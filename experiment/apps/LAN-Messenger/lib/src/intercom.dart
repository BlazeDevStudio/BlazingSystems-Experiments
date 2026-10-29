import 'dart:async';
import 'dart:io';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:flutter/services.dart';
import 'identity.dart';
import 'node.dart';
import 'call_transport_gate.dart';
import 'windows_remote_input.dart';
import 'lan_reconnect_policy.dart';
import 'call_peer_watchdog.dart';
import 'serial_async_gate.dart';
import 'protocol.dart';

// Exactly one active call, shared for voice and video. No STUN/TURN or internet.
class Intercom {
  final LanNode node;
  Peer? talkingTo;
  String? callId;
  bool video = false;
  bool connecting = false;
  /// True while the previous call's native WebRTC tracks and peer connection
  /// are being torn down. A second dial during that interval can be rejected
  /// by either device before its incoming notification is posted.
  bool get closing => _closing;
  bool muted = false;
  bool sharingScreen = false;
  bool peerSharingScreen = false;
  bool remoteControlActive = false;
  String? _approvedControllerId;
  DateTime? _controlDeadline;
  DateTime? _lastMotionAt;
  DateTime? _lastClickAt;
  Timer? _controlTimer;
  bool get remoteControlApproved => _approvedControllerId == talkingTo?.id &&
      _controlDeadline != null &&
      DateTime.now().isBefore(_controlDeadline!);
  Future<bool> Function(Peer peer)? onRemoteControlRequest;
  void Function(String message)? onControlStatus;
  Future<DesktopCapturerSource?> Function(List<DesktopCapturerSource> sources)?
      onChooseDesktopSource;

  Future<void> requestRemoteControl() async {
    final peer = talkingTo;
    if (peer == null || callId == null || !peerSharingScreen) {
      throw StateError('No shared screen to control');
    }
    await node.signal(peer, {'type': 'control-request', 'callId': callId});
  }

  Future<void> revokeRemoteControl() async {
    final peer = talkingTo;
    final id = callId;
    _approvedControllerId = null;
    _controlDeadline = null;
    _controlTimer?.cancel();
    _controlTimer = null;
    remoteControlActive = false;
    if (Platform.isWindows) WindowsRemoteInput.releaseButtons();
    if (Platform.isAndroid && sharingScreen) {
      unawaited(const MethodChannel('lan_messenger/remote')
          .invokeMethod<void>('status', {'active': false}).catchError((_) {}));
    }
    onChanged?.call();
    if (peer != null && id != null) {
      try { await node.signal(peer, {
        'type': 'control-grant', 'callId': id, 'enabled': false,
      }); } catch (_) {}
    }
  }

  Future<void> sendRemoteClick(double x, double y) async {
    final peer = talkingTo;
    final id = callId;
    if (!remoteControlActive || !peerSharingScreen || peer == null ||
        id == null || !x.isFinite || !y.isFinite ||
        x < 0 || x > 1 || y < 0 || y > 1) return;
    try {
      // Keep the older control-click envelope for mixed preview versions.
      await node.signal(peer, {
        'type': 'control-click', 'callId': id, 'x': x, 'y': y,
      });
    } catch (e) {
      unawaited(_log('legacy remote click delivery failed: ${e.runtimeType}'));
    }
  }

  /// Allowed input events are session-bound and checked by the receiving host.
  DateTime? _lastOutgoingMove;
  bool _outgoingMovePending = false;

  Future<void> sendRemoteInput(String action, double x, double y, [int wheel = 0]) async {
    final peer = talkingTo;
    final id = callId;
    const allowed = {'move', 'down', 'up', 'click', 'right', 'middle', 'scroll'};
    if (!remoteControlActive || !peerSharingScreen || peer == null ||
        id == null || !allowed.contains(action) ||
        !x.isFinite || !y.isFinite || x < 0 || x > 1 || y < 0 || y > 1) return;
    // Pointer moves are high frequency. Avoid piling up HTTP requests when
    // the remote host is busy, but NEVER drop mouse-button releases.
    final motion = action == 'move' || action == 'scroll';
    final now = DateTime.now();
    if (motion && (_outgoingMovePending ||
        (_lastOutgoingMove != null &&
         now.difference(_lastOutgoingMove!) <
             const Duration(milliseconds: 45)))) return;
    if (motion) {
      _lastOutgoingMove = now;
      _outgoingMovePending = true;
    }
    try {
      await node.signal(peer, {
        'type': 'control-input', 'callId': id,
        'action': action, 'x': x, 'y': y,
        'wheel': wheel.clamp(-120, 120),
      });
    } catch (e) {
      // RemoteControlSurface invokes this from an unawaited pointer callback.
      // A refused/late network request must NEVER become an uncaught error
      // that terminates an active call or its Flutter process.
      unawaited(_log('remote input delivery failed: ${e.runtimeType}'));
    } finally {
      if (motion) _outgoingMovePending = false;
    }
  }

  MediaStream? _displayStream;
  MediaStream? _remoteFallbackStream;
  // Native track callbacks and teardown must never mutate a fallback stream
  // concurrently; Flutter's WebRTC callbacks may arrive back-to-back.
  final SerialAsyncGate _remoteVideoTrackGate = SerialAsyncGate();
  bool _remoteHasNativeStream = false;
  bool _remoteVideoFrameObserved = false;
  List<MediaDeviceInfo> availableCameras = <MediaDeviceInfo>[];
  int activeCameraIndex = 0;
  bool get canSwitchCamera => video && !sharingScreen &&
      availableCameras.length > 1 && _localStream != null;

  Future<void> refreshCameras() async {
    try {
      availableCameras = (await navigator.mediaDevices.enumerateDevices())
          .where((device) => device.kind == 'videoinput').toList();
      if (activeCameraIndex >= availableCameras.length) activeCameraIndex = 0;
    } catch (e) {
      availableCameras = <MediaDeviceInfo>[];
      unawaited(_log('camera enumeration error: $e'));
    }
    onChanged?.call();
  }

  Future<void> switchCamera() async {
    if (!canSwitchCamera || _closing) return;
    final track = _localStream!.getVideoTracks().first;
    final next = (activeCameraIndex + 1) % availableCameras.length;
    final success = await Helper.switchCamera(
        track, availableCameras[next].deviceId, _localStream);
    if (!success) throw StateError('Camera switch is unsupported');
    activeCameraIndex = next;
    onChanged?.call();
  }

  Future<void> startScreenShare() async {
    if (!video || _connection == null || _closing) {
      throw StateError('Screen sharing requires an active video call');
    }
    if (sharingScreen) return;
    // Request Android's system screen capture permission for every session.
    if (Platform.isAndroid) {
      final granted = await Helper.requestCapturePermission(fullScreenOnly: true);
      if (!granted) throw StateError('Screen sharing was declined');
      await const MethodChannel('lan_messenger/projection')
          .invokeMethod<void>('start');
      // Allow the foreground service to enter mediaProjection state before
      // WebRTC acquires the projection token on Android 14+.
      await Future<void>.delayed(const Duration(milliseconds: 350));
    }
    MediaStream? display;
    try {
      Map<String, dynamic> videoOptions = {'frameRate': 12};
      if (Platform.isWindows) {
        // Desktop Flutter WebRTC does not provide a native source picker.
        // A source ID is required for predictable Windows capture.
        final sources = await desktopCapturer.getSources(
          types: [SourceType.Screen],
        );
        if (sources.isEmpty) throw StateError('Windows has no capturable displays');
        final source = await onChooseDesktopSource?.call(sources);
        if (source == null) throw StateError('No screen selected');
        videoOptions = {
          'deviceId': {'exact': source.id},
          'mandatory': {'frameRate': 12.0},
        };
        await _log('selected capture source ${source.type}: ${source.name}');
      }
      display = await navigator.mediaDevices.getDisplayMedia({
        'audio': false, 'video': videoOptions,
      });
      if (_closing || _connection == null || talkingTo == null) {
        throw StateError('The call ended while selecting a screen');
      }
      if (display.getVideoTracks().isEmpty) {
        throw StateError('No screen video track available');
      }
      // Flutter WebRTC may return an enabled but dead screen-capture track.
      // Confirm an actual decoded desktop frame BEFORE replacing the camera
      // sender; otherwise both local preview and peer can go permanently blank.
      if (Platform.isWindows || Platform.isAndroid) {
        final probe = RTCVideoRenderer();
        await probe.initialize();
        try {
          probe.srcObject = display;
          var frameReady = false;
          for (var attempt = 0; attempt < 50; attempt++) {
            if (_closing || _connection == null) break;
            if (probe.videoWidth > 0 && probe.videoHeight > 0) {
              frameReady = true;
              break;
            }
            await Future<void>.delayed(const Duration(milliseconds: 120));
          }
          if (!frameReady) {
            throw StateError('Selected desktop capture produced no frames. '
                'Keep the display active and select a different screen.');
          }
        } finally {
          probe.srcObject = null;
          await probe.dispose();
        }
      }
      final senders = await _connection!.getSenders();
      final videoSenders = senders.where((s) => s.track?.kind == 'video').toList();
      if (videoSenders.isEmpty) throw StateError('Video sender unavailable');
      await videoSenders.first.replaceTrack(display.getVideoTracks().first);
      _displayStream = display;
      sharingScreen = true;
      // If Android stops MediaProjection or the desktop capturer ends,
      // restore the camera instead of leaving the peer on a dead screen track.
      display.getVideoTracks().first.onEnded = () {
        if (!_closing && sharingScreen && identical(_displayStream, display)) {
          unawaited(stopScreenShare().catchError((Object e) async {
            await _log('automatic screen-share recovery error: $e');
          }));
        }
      };
      localRenderer?.srcObject = display;
      onChanged?.call();
      await node.signal(talkingTo!, {
        'type': 'share-state', 'callId': callId, 'active': true,
      }).catchError((_) {});
      await _log('screen share started');
    } catch (e) {
      if (display != null) {
        for (final track in display.getTracks()) { track.stop(); }
        await display.dispose();
      }
      if (Platform.isAndroid) {
        try { await const MethodChannel('lan_messenger/projection')
            .invokeMethod<void>('stop'); } catch (_) {}
      }
      rethrow;
    }
  }

  Future<void> stopScreenShare() async {
    final stream = _displayStream;
    if (!sharingScreen && stream == null) return;
    sharingScreen = false;
    _displayStream = null;
    await revokeRemoteControl();
    if (talkingTo != null && callId != null) {
      await node.signal(talkingTo!, {
        'type': 'share-state', 'callId': callId, 'active': false,
      }).catchError((_) {});
    }
    try {
      if (_connection != null && _localStream != null &&
          _localStream!.getVideoTracks().isNotEmpty) {
        final senders = await _connection!.getSenders();
        final videoSenders = senders.where((s) => s.track?.kind == 'video').toList();
        if (videoSenders.isNotEmpty) {
          await videoSenders.first.replaceTrack(_localStream!.getVideoTracks().first);
        }
      }
      localRenderer?.srcObject = _localStream;
    } finally {
      if (stream != null) {
        for (final track in stream.getTracks()) { track.stop(); }
        await stream.dispose();
      }
      if (Platform.isAndroid) {
        try { await const MethodChannel('lan_messenger/projection')
            .invokeMethod<void>('stop'); } catch (_) {}
      }
      onChanged?.call();
    }
  }
  bool _closing = false;
  int reconnectGraceSeconds = 60;
  bool reconnecting = false;
  DateTime? _reconnectUntil;
  Timer? _reconnectUiPulse;
  Timer? _peerProbeTimer;
  bool _peerProbeBusy = false;
  int _peerProbeGeneration = 0;
  bool _iceDisconnected = false;
  final CallPeerWatchdog _peerWatchdog = CallPeerWatchdog();

  /// Call-scoped HTTP liveness supplements ICE: a crashed Windows process
  /// cannot send 'hangup', and the surviving peer may otherwise appear live.
  void _startPeerProbes(Peer peer, String id) {
    if (_peerProbeTimer != null) return;
    _peerWatchdog.reset();
    final generation = ++_peerProbeGeneration;
    _peerProbeTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (_peerProbeBusy || _closing || callId != id) return;
      unawaited(_checkPeerProbe(peer, id, generation));
    });
  }

  Future<void> _checkPeerProbe(Peer peer, String id, int generation) async {
    if (_peerProbeBusy || callId != id || _closing) return;
    _peerProbeBusy = true;
    try {
      final status = await node.probeCall(peer, id);
      if (generation != _peerProbeGeneration ||
          callId != id || _closing) return;
      final change = _peerWatchdog.report(status);
      if (change == CallWatchdogChange.ended) {
        // The remote process answered our encrypted probe but reports no
        // matching live session. End now; no point waiting for ICE timeouts.
        unawaited(_log('remote peer reports call session already ended'));
        unawaited(hangUp(notify: false));
      } else if (change == CallWatchdogChange.suspect) {
        node.markPeerUnreachable(peer);
        _beginReconnectAt(_peerWatchdog.firstUnavailableAt!);
        unawaited(_log('peer heartbeat unavailable; bounded reconnect'));
      } else if (change == CallWatchdogChange.recovered) {
        // A recovered signaling socket does not prove media recovery after
        // ICE has actually disconnected. Preserve grace until media resumes.
        if (!_iceDisconnected) _resetReconnectState();
        onChanged?.call();
      }
    } finally {
      if (generation == _peerProbeGeneration) _peerProbeBusy = false;
    }
  }

  void _stopPeerProbes() {
    _peerProbeTimer?.cancel();
    _peerProbeTimer = null;
    _peerProbeGeneration++;
    _peerProbeBusy = false;
    _iceDisconnected = false;
    _peerWatchdog.reset();
  }

  void _beginReconnectAt(DateTime firstFailure) {
    final deadline = firstFailure.add(Duration(seconds: reconnectGraceSeconds));
    if (!reconnecting) {
      reconnecting = true;
      _reconnectUiPulse?.cancel();
      _reconnectUiPulse = Timer.periodic(
          const Duration(seconds: 1), (_) => onChanged?.call());
    }
    if (_reconnectUntil == null || deadline.isBefore(_reconnectUntil!)) {
      _reconnectUntil = deadline;
      _disconnectGrace.dispose();
    }
    final remaining = _reconnectUntil!.difference(DateTime.now());
    _disconnectGrace.disconnected(remaining.isNegative
        ? Duration.zero : remaining);
    onChanged?.call();
  }

  int get reconnectRemainingSeconds {
    if (!reconnecting || _reconnectUntil == null) return 0;
    final ms = _reconnectUntil!.difference(DateTime.now()).inMilliseconds;
    return ms <= 0 ? 0 : (ms / 1000).ceil();
  }

  void _resetReconnectState() {
    reconnecting = false;
    _disconnectGrace.dispose();
    _reconnectUiPulse?.cancel();
    _reconnectUiPulse = null;
    _reconnectUntil = null;
  }
  late final LanDisconnectGrace _disconnectGrace = LanDisconnectGrace(() {
    if (callId != null && !_closing && reconnecting) {
      unawaited(_log('media reconnect grace expired; closing orphaned call'));
      unawaited(hangUp(notify: false));
    }
  });
  bool _remoteDescriptionReady = false;
  Future<void>? _shutdown;
  RTCPeerConnection? _connection;
  MediaStream? _localStream;
  RTCVideoRenderer? localRenderer;
  RTCVideoRenderer? remoteRenderer;
  final Map<String, List<RTCIceCandidate>> _pendingIce = {};
  Timer? _answerTimeout;
  void Function()? onChanged;
  Future<bool> Function(Peer, bool video)? onIncoming;
  /// Group calls may reuse one audio/video capture across several RTCPeerConnections.
  /// A link does not own streams obtained from this provider: the room owns
  /// their lifetime, so one departing peer cannot stop everyone's camera.
  final Future<MediaStream> Function()? sharedMediaProvider;
  Intercom(this.node, {this.sharedMediaProvider});

  Future<void> _log(String message) async {
    try {
      final dir = await Identity.appDirectory();
      final file = File('${dir.path}${Platform.pathSeparator}call-diagnostics.log');
      await file.writeAsString('${DateTime.now().toUtc().toIso8601String()} '
          '$message\n', mode: FileMode.append, flush: true);
    } catch (_) {}
  }

  Future<void> _prepare(Peer peer, String id) async {
    await _log('start media platform=${Platform.operatingSystem} video=$video');
    final stream = sharedMediaProvider != null
        ? await sharedMediaProvider!()
        : await navigator.mediaDevices.getUserMedia({
            'audio': {
              'echoCancellation': true,
              'noiseSuppression': true,
              'autoGainControl': true,
            },
            'video': video
                ? {
                    'facingMode': 'user',
                    'width': {'ideal': 640},
                    'height': {'ideal': 480},
                    'frameRate': {'ideal': 15},
                  }
                : false,
          });
    if (callId != id || _closing) {
      if (sharedMediaProvider == null) {
        for (final track in stream.getTracks()) { await track.stop(); }
        await stream.dispose();
      }
      return;
    }
    _localStream = stream;
    if (video) unawaited(refreshCameras());
    await _log('media acquired');
    if (video) {
      localRenderer = RTCVideoRenderer();
      remoteRenderer = RTCVideoRenderer();
      await localRenderer!.initialize();
      await remoteRenderer!.initialize();
      // Frame sizes change when the remote phone rotates or shares a screen.
      // Rebuild the AspectRatio on actual decoded-frame resize, not just
      // the local device OrientationBuilder callback.
      _remoteVideoFrameObserved = false;
      remoteRenderer!.onResize = () {
        if (callId != id || _closing) return;
        if (!_remoteVideoFrameObserved &&
            (remoteRenderer?.videoWidth ?? 0) > 0 &&
            (remoteRenderer?.videoHeight ?? 0) > 0) {
          _remoteVideoFrameObserved = true;
          print('LAN_CALL_TRACE remote_video_frame_decoded');
          unawaited(_log('decoded first remote video frame'));
        }
        onChanged?.call();
      };
      localRenderer!.srcObject = stream;
    }
    final pc = await createPeerConnection({
      'iceServers': <Map<String, dynamic>>[],
      'iceTransportPolicy': 'all',
      'sdpSemantics': 'unified-plan',
    });
    if (callId != id || _closing) {
      await pc.close();
      await pc.dispose();
      return;
    }
    _connection = pc;
    pc.onIceCandidate = (candidate) {
      if (callId != id || _closing || candidate.candidate == null) return;
      unawaited(node.signal(peer, {'type': 'ice', 'callId': id,
          'candidate': candidate.candidate, 'mid': candidate.sdpMid,
          'mLine': candidate.sdpMLineIndex}).catchError((_) {}));
    };
    _remoteHasNativeStream = false;
    pc.onAddStream = (remote) {
      if (callId != id || _closing || !video ||
          remote.getVideoTracks().isEmpty) return;
      _remoteHasNativeStream = true;
      remoteRenderer?.srcObject = remote;
      unawaited(_log('remote video attached via onAddStream'));
      onChanged?.call();
    };
    pc.onTrack = (event) {
      if (callId != id || _closing || !video ||
          event.track.kind != 'video') return;
      // Some Windows Unified Plan callbacks include an empty stream while
      // delivering the video track separately. Do not bind an empty stream
      // to RTCVideoRenderer: it produces a black window despite Connected.
      if (event.streams.isNotEmpty &&
          event.streams.first.getVideoTracks().isNotEmpty) {
        _remoteHasNativeStream = true;
        remoteRenderer?.srcObject = event.streams.first;
        unawaited(_log('remote video attached via onTrack'));
        onChanged?.call();
        return;
      }
      // Streamless or empty-stream track: attach its video track to a local
      // fallback MediaStream, with explicit ownership across native awaits.
      unawaited(_remoteVideoTrackGate.run<void>(() async {
        MediaStream? createdFallback;
        var rendererAttached = false;
        try {
          // A prior callback may be waiting on native stream creation.
          // Recheck ownership when the serialized operation actually starts.
          if (callId != id || _closing || _remoteHasNativeStream) return;
          final existing = _remoteFallbackStream;
          final fallback = existing ??
              await createLocalMediaStream('lan-received-video-$id');
          if (existing == null) createdFallback = fallback;
          if (callId != id || _closing || _remoteHasNativeStream) {
            if (existing == null) await fallback.dispose();
            return;
          }
          if (existing == null) _remoteFallbackStream = fallback;
          // Some Windows WebRTC builds deliver the same onTrack event twice.
          // Adding the identical native track repeatedly is not safe.
          if (!fallback.getVideoTracks().any(
              (track) => track.id == event.track.id)) {
            await fallback.addTrack(event.track);
          }
          if (callId != id || _closing || _remoteHasNativeStream) {
            if (existing == null &&
                identical(_remoteFallbackStream, fallback)) {
              _remoteFallbackStream = null;
              await fallback.dispose();
            }
            return;
          }
          // Never dispose a stream after handing it to the native renderer,
          // even if a later callback/log operation throws.
          rendererAttached = true;
          remoteRenderer?.srcObject = fallback;
          unawaited(_log('remote streamless video track attached'));
          onChanged?.call();
        } catch (e) {
          final abandoned = createdFallback;
          if (!rendererAttached && abandoned != null &&
              identical(_remoteFallbackStream, abandoned)) {
            _remoteFallbackStream = null;
            try { await abandoned.dispose(); } catch (_) {}
          }
          unawaited(_log('remote video attachment failed: ${e.runtimeType}'));
        }
      }));
    };
    pc.onConnectionState = (state) {
      if (callId != id || _closing) return;
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateDisconnected) {
        // WebRTC lost media: keep the existing tracks for bounded recovery.
        // A concurrent heartbeat may already have started an EARLIER deadline.
        _iceDisconnected = true;
        _beginReconnectAt(DateTime.now());
        unawaited(_log('media disconnected; grace=${reconnectGraceSeconds}s'));
      } else if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
          state == RTCPeerConnectionState.RTCPeerConnectionStateClosed) {
        // ICE failure/close is terminal without a new negotiation.
        _disconnectGrace.dispose();
        unawaited(_log('terminal connection state $state'));
        unawaited(hangUp(notify: false));
      } else if (CallTransportGate.mediaReady(state)) {
        _iceDisconnected = false;
        if (!_peerWatchdog.suspect) _resetReconnectState();
        // An SDP answer is not proof of a usable media path. Only the actual
        // WebRTC peer transport reaching Connected clears the call's
        // negotiating state and unlocks connected-call UI/PiP.
        connecting = false;
        _startPeerProbes(peer, id);
        _answerTimeout?.cancel();
        _answerTimeout = null;
        // Distinct, privacy-safe native log marker for both endpoints.
        // E2E acceptance checks this on the caller AND receiver: a ringing
        // notification or one endpoint's live UI does not prove two-way
        // WebRTC transport establishment.
        print('LAN_CALL_TRACE webrtc_transport_connected');
        unawaited(_log('webrtc_transport_connected callId=$id'));
      }
      onChanged?.call();
    };
    for (final track in stream.getTracks()) {
      await pc.addTrack(track, stream);
    }
    onChanged?.call();
    await _log('peer connection prepared');
  }

  Future<void> call(Peer peer, {bool withVideo = false,
      String? groupId, String? groupSessionId}) async {
    if (talkingTo != null || _closing) throw StateError('Already in a call');
    final id = randomId();
    talkingTo = peer;
    callId = id;
    video = withVideo;
    muted = false;
    sharingScreen = false;
    connecting = true;
    _resetReconnectState();
    _remoteDescriptionReady = false;
    onChanged?.call();
    try {
      await _prepare(peer, id);
      if (callId != id || _closing) return;
      final pc = _connection!;
      final offer = await pc.createOffer({
        'offerToReceiveAudio': true, 'offerToReceiveVideo': withVideo,
      });
      await pc.setLocalDescription(offer);
      await node.signal(peer, {
        'type': 'offer', 'callId': id, 'sdp': offer.sdp, 'video': withVideo,
        if (groupId != null && groupSessionId != null) ...{
          'groupId': groupId, 'groupSessionId': groupSessionId,
        },
      });
      _answerTimeout = Timer(const Duration(seconds: 45), () {
        if (callId == id && connecting) unawaited(hangUp());
      });
    } catch (e) {
      await _log('outgoing call error: $e');
      await hangUp(notify: false);
      rethrow;
    }
  }

  Future<void> incomingSignal(Peer peer, Map<String, dynamic> data) async {
    final type = data['type'];
    final id = data['callId'];
    if (id is! String || id.length > 64 || type is! String) return;
    if (type == 'offer') {
      if (talkingTo != null || _closing || data['sdp'] is! String) {
        unawaited(node.signal(peer, {'type': 'hangup', 'callId': id})
            .catchError((_) {}));
        return;
      }
      talkingTo = peer;
      callId = id;
      video = data['video'] == true;
      connecting = true;
      muted = false;
      sharingScreen = false;
      _remoteDescriptionReady = false;
      onChanged?.call();
      try {
        final accepted = await (onIncoming?.call(peer, video) ?? Future.value(false));
        if (callId != id || _closing) return;
        if (!accepted) { await hangUp(); return; }
        await _prepare(peer, id);
        if (callId != id || _closing) return;
        final pc = _connection!;
        await pc.setRemoteDescription(RTCSessionDescription(data['sdp'] as String, 'offer'));
        _remoteDescriptionReady = true;
        await _flushIce(id);
        final answer = await pc.createAnswer({
          'offerToReceiveAudio': true, 'offerToReceiveVideo': video,
        });
        await pc.setLocalDescription(answer);
        await node.signal(peer, {'type': 'answer', 'callId': id, 'sdp': answer.sdp});
        // SDP exchange completed, but ICE/DTLS may still be disconnected.
        // Keep "Connecting" until the peer connection callback fires.
        if (callId == id && connecting && !_closing) {
          _answerTimeout?.cancel();
          _answerTimeout = Timer(const Duration(seconds: 45), () {
            if (callId == id && connecting) unawaited(hangUp());
          });
        }
        onChanged?.call();
      } catch (e) {
        await _log('incoming call error: $e');
        await hangUp();
      }
      return;
    }
    if (id != callId || peer.id != talkingTo?.id || _closing) return;
    if (type == 'share-state') {
      peerSharingScreen = data['active'] == true;
      if (!peerSharingScreen) remoteControlActive = false;
      onChanged?.call();
      return;
    }
    if (type == 'control-request') {
      if (!sharingScreen ||
          !(Platform.isWindows || Platform.isAndroid)) return;
      // Existing authenticated peer + same live call ID; approval is never
      // automatic, lasts five minutes, and can be revoked locally.
      var accepted = await (onRemoteControlRequest?.call(peer) ??
          Future<bool>.value(false));
      if (accepted && Platform.isAndroid) {
        final ready = await const MethodChannel('lan_messenger/remote')
            .invokeMethod<bool>('available').catchError((_) => false);
        if (ready != true) accepted = false;
      }
      if (callId != id || talkingTo?.id != peer.id || !sharingScreen) return;
      _approvedControllerId = accepted ? peer.id : null;
      if (Platform.isAndroid) {
        unawaited(const MethodChannel('lan_messenger/remote')
            .invokeMethod<void>('status', {'active': accepted}).catchError((_) {}));
      }
      _controlDeadline = accepted
          ? DateTime.now().add(const Duration(minutes: 5)) : null;
      _controlTimer?.cancel();
      if (accepted) {
        _controlTimer = Timer(const Duration(minutes: 5), () {
          unawaited(revokeRemoteControl());
        });
      }
      await node.signal(peer, {
        'type': 'control-grant', 'callId': id, 'enabled': accepted,
        if (!accepted) 'reason': Platform.isAndroid
            ? 'Remote touch permission disabled or request declined' :
              'Remote-control request declined',
      }).catchError((_) {});
      onChanged?.call();
      return;
    }
    if (type == 'control-grant') {
      remoteControlActive = data['enabled'] == true && peerSharingScreen;
      if (!remoteControlActive && data['reason'] is String) {
        onControlStatus?.call(data['reason'] as String);
      }
      onChanged?.call();
      return;
    }
    if (type == 'control-click' || type == 'control-input') {
      if (!(Platform.isWindows || Platform.isAndroid) ||
          !sharingScreen || !remoteControlApproved ||
          _approvedControllerId != peer.id) return;
      final x = data['x'];
      final y = data['y'];
      final action = type == 'control-click' ? 'click' : data['action'];
      const allowed = {'move', 'down', 'up', 'click', 'right', 'middle', 'scroll'};
      if (x is! num || y is! num || action is! String ||
          !allowed.contains(action) ||
          !x.isFinite || !y.isFinite ||
          x < 0 || x > 1 || y < 0 || y > 1) return;
      final wheel = data['wheel'];
      if (action == 'scroll' &&
          (wheel is! int || wheel < -120 || wheel > 120)) return;
      final now = DateTime.now();
      // Throttle motion without dropping an essential mouse-button release.
      final gap = switch (action) {
        'move' || 'scroll' => const Duration(milliseconds: 25),
        'click' || 'right' || 'middle' => const Duration(milliseconds: 85),
        _ => Duration.zero,
      };
      final previous = (action == 'move' || action == 'scroll')
          ? _lastMotionAt : _lastClickAt;
      if (gap > Duration.zero && previous != null &&
          now.difference(previous) < gap) return;
      if (action == 'move' || action == 'scroll') {
        _lastMotionAt = now;
      } else if (gap > Duration.zero) {
        _lastClickAt = now;
      }
      if (Platform.isWindows) {
        WindowsRemoteInput.perform(action, x.toDouble(), y.toDouble(),
            action == 'scroll' ? wheel as int : 0);
      } else if (Platform.isAndroid && action == 'click') {
        await const MethodChannel('lan_messenger/remote').invokeMethod<bool>(
          'tap', {'x': x.toDouble(), 'y': y.toDouble()},
        ).catchError((_) => false);
      }
      return;
    }
    if (type == 'ice' && data['candidate'] is String) {
      final candidate = RTCIceCandidate(data['candidate'] as String,
          data['mid'] as String?, data['mLine'] as int?);
      if (_connection == null || !_remoteDescriptionReady) {
        _pendingIce.putIfAbsent(id, () => []).add(candidate);
      } else {
        try { await _connection!.addCandidate(candidate); } catch (_) {}
      }
    } else if (type == 'answer' && data['sdp'] is String) {
      try {
        await _connection?.setRemoteDescription(
            RTCSessionDescription(data['sdp'] as String, 'answer'));
        if (callId != id || _closing) return;
        _remoteDescriptionReady = true;
        await _flushIce(id);
        if (callId != id || _closing) return;
        // The remote SDP is now accepted, not the media connection.
        // The 45-second outgoing timeout remains armed until WebRTC Connected.
        onChanged?.call();
      } catch (e) {
        await _log('answer error: $e');
        await hangUp();
      }
    } else if (type == 'hangup') {
      await hangUp(notify: false);
    }
  }

  Future<void> _flushIce(String id) async {
    final pc = _connection;
    if (pc == null) return;
    for (final ice in _pendingIce.remove(id) ?? []) {
      try { await pc.addCandidate(ice); } catch (_) {}
    }
  }

  Future<void> setMuted(bool value) async {
    muted = value;
    for (final track in _localStream?.getAudioTracks() ?? <MediaStreamTrack>[]) {
      track.enabled = !value;
    }
    onChanged?.call();
  }

  Future<void> hangUp({bool notify = true}) {
    if (_shutdown != null) return _shutdown!;
    final pending = _hangUpOnce(notify: notify);
    _shutdown = pending;
    return pending.whenComplete(() => _shutdown = null);
  }

  Future<void> _hangUpOnce({required bool notify}) async {
    if (_closing) return;
    _closing = true;
    _stopPeerProbes();
    _resetReconnectState();
    _answerTimeout?.cancel();
    _answerTimeout = null;
    final peer = talkingTo;
    final id = callId;
    talkingTo = null;
    callId = null;
    connecting = false;
    video = false;
    _remoteDescriptionReady = false;
    _pendingIce.clear();
    final pc = _connection;
    final stream = _localStream;
    final display = _displayStream;
    _displayStream = null;
    sharingScreen = false;
    peerSharingScreen = false;
    remoteControlActive = false;
    if (Platform.isWindows) WindowsRemoteInput.releaseButtons();
    _approvedControllerId = null;
    _controlDeadline = null;
    _controlTimer?.cancel();
    _controlTimer = null;
    _lastMotionAt = null;
    _lastClickAt = null;
    availableCameras = <MediaDeviceInfo>[];
    final local = localRenderer;
    final remote = remoteRenderer;
    _remoteHasNativeStream = false;
    _remoteVideoFrameObserved = false;
    _lastOutgoingMove = null;
    _outgoingMovePending = false;
    _connection = null;
    _localStream = null;
    localRenderer = null;
    remoteRenderer = null;
    onChanged?.call();
    if (notify && peer != null && id != null) {
      unawaited(node.signal(peer, {'type': 'hangup', 'callId': id})
          .catchError((_) {}));
    }
    // Stop live capture synchronously before any native peer disposal await.
    // Otherwise a slow Windows WebRTC close() can hold the microphone open.
    if (stream != null && sharedMediaProvider == null) {
      for (final track in stream.getTracks()) {
        try {
          track.enabled = false;
          // stop() is asynchronous on Windows. Await it before proceeding.
          await track.stop().timeout(const Duration(seconds: 3));
        } catch (e) { await _log('media track stop error: $e'); }
      }
    }
    // Terminate screen capture immediately as well: a slow native peer close
    // must not keep the OS screen-sharing indicator active.
    if (display != null) {
      for (final track in display.getTracks()) {
        try { await track.stop().timeout(const Duration(seconds: 3)); }
        catch (e) { await _log('display track stop error: $e'); }
      }
    }
    // A callback that began before callId was invalidated can still be inside
    // native addTrack(). Drain that queue BEFORE closing the peer or disposing
    // the fallback stream. New callbacks are rejected by _closing/callId.
    await _remoteVideoTrackGate.run<void>(() async {});
    final fallback = _remoteFallbackStream;
    _remoteFallbackStream = null;
    try {
      if (pc != null) {
        // Disconnect callbacks first; don't allow an onConnectionState recursion.
        pc.onIceCandidate = null;
        pc.onConnectionState = null;
        pc.onTrack = null;
        pc.onAddStream = null;
        try { await pc.close().timeout(const Duration(seconds: 5)); }
        catch (e) { await _log('peer close error: $e'); }
        try { await pc.dispose().timeout(const Duration(seconds: 5)); }
        catch (e) { await _log('peer dispose error: $e'); }
      }
    } catch (e) { await _log('peer teardown error: $e'); }
    // Each resource is released independently; one native plugin failure must
    // not skip the remaining stream or video renderer cleanup.
    if (display != null) {
      // Tracks were already stopped above. Do not fire duplicate unawaited
      // native stop() Futures during shutdown.
      try { await display.dispose().timeout(const Duration(seconds: 5)); }
      catch (e) { await _log('display stream dispose error: $e'); }
    }
    if (Platform.isAndroid) {
      try { await const MethodChannel('lan_messenger/projection')
          .invokeMethod<void>('stop'); } catch (_) {}
    }
    if (stream != null && sharedMediaProvider == null) {
      for (final track in stream.getTracks()) {
        try { await track.dispose().timeout(const Duration(seconds: 3)); }
        catch (e) { await _log('track dispose error: $e'); }
      }
      try { await stream.dispose().timeout(const Duration(seconds: 5)); }
      catch (e) { await _log('stream dispose error: $e'); }
    }
    try {
      if (local != null) {
        local.srcObject = null;
        await local.dispose().timeout(const Duration(seconds: 4));
      }
    } catch (e) { await _log('local renderer dispose error: $e'); }
    try {
      if (remote != null) {
        remote.srcObject = null;
        await remote.dispose().timeout(const Duration(seconds: 4));
      }
    } catch (e) { await _log('remote renderer dispose error: $e'); }
    if (fallback != null) {
      try { await fallback.dispose().timeout(const Duration(seconds: 4)); }
      catch (e) { await _log('streamless remote media cleanup error: $e'); }
    }
    _closing = false;
    // The UI previously re-enabled Call as soon as talkingTo became null,
    // despite pending asynchronous native WebRTC disposal. Repaint only after
    // the previous session is actually safe to redial.
    onChanged?.call();
  }
}