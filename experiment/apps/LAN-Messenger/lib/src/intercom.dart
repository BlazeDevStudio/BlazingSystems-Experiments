import 'dart:async';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'identity.dart';
import 'node.dart';
import 'protocol.dart';

// Exactly one active call, shared for voice and video. No STUN/TURN or internet.
class Intercom {
  final LanNode node;
  Peer? talkingTo;
  String? callId;
  bool video = false;
  bool connecting = false;
  bool muted = false;
  bool sharingScreen = false;
  bool peerSharingScreen = false;
  bool controllingPeer = false;
  bool remoteControlGranted = false;
  bool remoteControlRequested = false;
  Future<bool> Function(Peer)? onRemoteControlRequest;
  DateTime? _lastRemoteInput;
  bool changingVideoSource = false;
  int cameraCount = 0;
  String? cameraId;
  MediaStream? _screenStream;
  MediaStreamTrack? _cameraTrack;
  bool _closing = false;
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
  Intercom(this.node);

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
    final stream = await navigator.mediaDevices.getUserMedia({
      'audio': {
        'echoCancellation': true,
        'noiseSuppression': true,
        'autoGainControl': true,
      },
      'video': video ? {
        'facingMode': 'user',
        'width': {'ideal': 640},
        'height': {'ideal': 480},
        'frameRate': {'ideal': 15},
      } : false,
    });
    if (callId != id || _closing) {
      for (final track in stream.getTracks()) { track.stop(); }
      await stream.dispose();
      return;
    }
    _localStream = stream;
    _cameraTrack = stream.getVideoTracks().isEmpty ? null : stream.getVideoTracks().first;
    if (video) {
      try {
        final cameras = await Helper.cameras;
        cameraCount = cameras.length;
        cameraId = cameras.isNotEmpty ? cameras.first.deviceId : null;
      } catch (e) {
        cameraCount = 1;
        await _log('camera enumeration unavailable: $e');
      }
    } else {
      cameraCount = 0;
      cameraId = null;
    }
    await _log('media acquired');
    if (video) {
      localRenderer = RTCVideoRenderer();
      remoteRenderer = RTCVideoRenderer();
      await localRenderer!.initialize();
      await remoteRenderer!.initialize();
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
    pc.onTrack = (event) {
      if (callId != id || _closing || !video) return;
      if (event.track.kind == 'video' && event.streams.isNotEmpty) {
        remoteRenderer?.srcObject = event.streams.first;
        onChanged?.call();
      }
    };
    pc.onConnectionState = (state) {
      if (callId != id || _closing) return;
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
          state == RTCPeerConnectionState.RTCPeerConnectionStateClosed) {
        unawaited(_log('unexpected connection state $state'));
        unawaited(hangUp(notify: false));
      } else if (state ==
          RTCPeerConnectionState.RTCPeerConnectionStateConnected) {
        connecting = false;
        _answerTimeout?.cancel();
        _answerTimeout = null;
      }
      onChanged?.call();
    };
    for (final track in stream.getTracks()) {
      await pc.addTrack(track, stream);
    }
    onChanged?.call();
    await _log('peer connection prepared');
  }

  Future<void> call(Peer peer, {bool withVideo = false}) async {
    if (talkingTo != null || _closing) throw StateError('Already in a call');
    final id = randomId();
    talkingTo = peer;
    callId = id;
    video = withVideo;
    muted = false;
    connecting = true;
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
        connecting = false;
        onChanged?.call();
      } catch (e) {
        await _log('incoming call error: $e');
        await hangUp();
      }
      return;
    }
    if (id != callId || peer.id != talkingTo?.id || _closing) return;
    // Commands are authenticated through the existing encrypted peer channel
    // and additionally bound to the currently active call ID.
    if (type == 'screen_state') {
      peerSharingScreen = data['active'] == true;
      if (!peerSharingScreen) {
        controllingPeer = false;
        remoteControlRequested = false;
      }
      onChanged?.call();
      return;
    }
    if (type == 'control_request') {
      // Android OS accessibility/input injection is deliberately unsupported.
      // Only a visible Windows sharer may grant session-bound remote assistance.
      final granted = Platform.isWindows && sharingScreen && !remoteControlGranted
          && (await (onRemoteControlRequest?.call(peer) ?? Future.value(false)));
      remoteControlGranted = granted;
      if (granted) onChanged?.call();
      await node.signal(peer, {'type': 'control_permission',
          'callId': id, 'granted': granted}).catchError((_) {});
      return;
    }
    if (type == 'control_permission') {
      controllingPeer = data['granted'] == true && peerSharingScreen;
      remoteControlRequested = false;
      onChanged?.call();
      return;
    }
    if (type == 'control_revoke') {
      remoteControlGranted = false;
      controllingPeer = false;
      remoteControlRequested = false;
      onChanged?.call();
      return;
    }
    if (type == 'control_input') {
      if (!Platform.isWindows || !sharingScreen || !remoteControlGranted) return;
      final action = data['action'];
      if (action != 'move' && action != 'tap' && action != 'text') return;
      try {
        await const MethodChannel('lan_messenger/windows_control')
            .invokeMethod<void>('input', {
              'action': action,
              'x': data['x'],
              'y': data['y'],
              'text': data['text'],
            });
      } catch (e) { await _log('remote input rejected: $e'); }
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
        _remoteDescriptionReady = true;
        await _flushIce(id);
        connecting = false;
        _answerTimeout?.cancel();
        _answerTimeout = null;
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

  /// Switch only between actual detected cameras. A switching failure leaves
  /// the existing outgoing video track intact.
  Future<bool> switchCamera() async {
    if (!video || sharingScreen || _closing || _localStream == null) return false;
    final tracks = _localStream!.getVideoTracks();
    if (tracks.isEmpty || changingVideoSource) return false;
    changingVideoSource = true;
    onChanged?.call();
    try {
      final devices = await Helper.cameras;
      cameraCount = devices.length;
      if (devices.length < 2) return false;
      final currentIndex = devices.indexWhere((x) => x.deviceId == cameraId);
      final next = devices[(currentIndex + 1) % devices.length];
      final ok = await Helper.switchCamera(tracks.first, next.deviceId, _localStream);
      if (ok) {
        cameraId = next.deviceId;
        await _log('switched camera device');
        onChanged?.call();
      }
      return ok;
    } catch (e) {
      await _log('camera switch unavailable: $e');
      return false;
    } finally {
      changingVideoSource = false;
      onChanged?.call();
    }
  }

  /// Local WebRTC screen-share replaces the video sender without starting
  /// another peer connection, and keeps the original audio call uninterrupted.
  /// Only supported for VIDEO calls with an existing sender.
  Future<bool> startScreenShare() async {
    if (!video || talkingTo == null || _connection == null ||
        sharingScreen || changingVideoSource || _closing) return false;
    changingVideoSource = true;
    onChanged?.call();
    MediaStream? acquired;
    try {
      // Android shows the standard OS screen-capture consent sheet.
      if (Platform.isAndroid) {
        final permission = await Helper.requestCapturePermission(fullScreenOnly: true);
        if (!permission) return false;
        await const MethodChannel('lan_messenger/screen_capture')
            .invokeMethod<void>('start');
      }
      acquired = await navigator.mediaDevices.getDisplayMedia({
        'audio': false,
        'video': {'frameRate': 12},
      });
      if (acquired.getVideoTracks().isEmpty) {
        await acquired.dispose();
        return false;
      }
      if (_connection == null || callId == null || _closing) {
        for (final t in acquired.getTracks()) { t.stop(); }
        await acquired.dispose();
        return false;
      }
      final senders = await _connection!.getSenders();
      final videoSenders = senders.where((x) => x.track?.kind == 'video').toList();
      if (videoSenders.isEmpty) throw StateError('No video sender in this call');
      await videoSenders.first.replaceTrack(acquired.getVideoTracks().first);
      _screenStream = acquired;
      sharingScreen = true;
      await node.signal(talkingTo!, {
        'type': 'screen_state', 'callId': callId, 'active': true,
      }).catchError((_) {});
      // The local preview shows exactly what the other side receives.
      localRenderer?.srcObject = acquired;
      for (final camera in _localStream?.getVideoTracks() ?? <MediaStreamTrack>[]) {
        camera.enabled = false;
      }
      onChanged?.call();
      await _log('screen sharing enabled');
      return true;
    } catch (e) {
      await _log('screen sharing declined/unavailable: $e');
      if (acquired != null) {
        for (final track in acquired.getTracks()) { track.stop(); }
        await acquired.dispose();
      }
      if (Platform.isAndroid) {
        try { await const MethodChannel('lan_messenger/screen_capture')
            .invokeMethod<void>('stop'); } catch (_) {}
      }
      return false;
    } finally {
      changingVideoSource = false;
      onChanged?.call();
    }
  }

  Future<void> stopScreenShare() async {
    if (_screenStream == null) return;
    final stream = _screenStream!;
    _screenStream = null;
    sharingScreen = false;
    await revokeRemoteControl();
    if (talkingTo != null && callId != null) {
      await node.signal(talkingTo!, {
        'type': 'screen_state', 'callId': callId, 'active': false,
      }).catchError((_) {});
    }
    try {
      final cameraTrack = _cameraTrack;
      if (cameraTrack != null && _connection != null && !_closing) {
        final senders = await _connection!.getSenders();
        for (final sender in senders) {
          if (sender.track?.kind == 'video') {
            await sender.replaceTrack(cameraTrack);
            break;
          }
        }
        cameraTrack.enabled = true;
        localRenderer?.srcObject = _localStream;
      }
    } catch (e) {
      await _log('screen share camera restore error: $e');
    } finally {
      for (final track in stream.getTracks()) { track.stop(); }
      try { await stream.dispose(); } catch (_) {}
      if (Platform.isAndroid) {
        try { await const MethodChannel('lan_messenger/screen_capture')
            .invokeMethod<void>('stop'); } catch (_) {}
      }
      onChanged?.call();
    }
  }

  Future<void> requestRemoteControl() async {
    if (talkingTo == null || callId == null || !peerSharingScreen ||
        controllingPeer || remoteControlRequested || _closing) return;
    remoteControlRequested = true;
    onChanged?.call();
    try {
      await node.signal(talkingTo!, {'type': 'control_request', 'callId': callId});
    } catch (_) {
      remoteControlRequested = false;
      onChanged?.call();
    }
  }

  Future<void> revokeRemoteControl() async {
    remoteControlGranted = false;
    controllingPeer = false;
    remoteControlRequested = false;
    onChanged?.call();
    if (talkingTo != null && callId != null) {
      await node.signal(talkingTo!, {'type': 'control_revoke',
          'callId': callId}).catchError((_) {});
    }
  }

  /// Rate-limited, call-scoped input; no file execution, shell or shortcuts.
  Future<void> sendRemoteInput(String action, {double? x, double? y,
      String? text}) async {
    if (!controllingPeer || !peerSharingScreen || talkingTo == null ||
        callId == null || _closing) return;
    if (action != 'tap' && action != 'move' && action != 'text') return;
    if (action == 'move') {
      final now = DateTime.now();
      if (_lastRemoteInput != null &&
          now.difference(_lastRemoteInput!).inMilliseconds < 40) return;
      _lastRemoteInput = now;
    }
    if (action == 'text' && (text == null || text.length > 120)) return;
    if (action != 'text' && (x == null || y == null ||
        x < 0 || x > 1 || y < 0 || y > 1)) return;
    await node.signal(talkingTo!, {'type': 'control_input', 'callId': callId,
      'action': action, 'x': x, 'y': y, 'text': text}).catchError((_) {});
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
    final screen = _screenStream;
    _screenStream = null;
    sharingScreen = false;
    peerSharingScreen = false;
    controllingPeer = false;
    remoteControlGranted = false;
    remoteControlRequested = false;
    changingVideoSource = false;
    cameraCount = 0;
    cameraId = null;
    _cameraTrack = null;
    final stream = _localStream;
    final local = localRenderer;
    final remote = remoteRenderer;
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
    if (screen != null) {
      for (final track in screen.getTracks()) { try { track.stop(); } catch (_) {} }
    }
    if (stream != null) {
      for (final track in stream.getTracks()) {
        try { track.enabled = false; track.stop(); }
        catch (e) { unawaited(_log('media track stop error: $e')); }
      }
    }
    try {
      if (pc != null) {
        // Disconnect callbacks first; don't allow an onConnectionState recursion.
        pc.onIceCandidate = null;
        pc.onConnectionState = null;
        pc.onTrack = null;
        await pc.close().timeout(const Duration(seconds: 5));
        await pc.dispose().timeout(const Duration(seconds: 5));
      }
    } catch (e) { await _log('peer teardown error: $e'); }
    // Each resource is released independently; one native plugin failure must
    // not skip the remaining stream or video renderer cleanup.
    if (screen != null && Platform.isAndroid) {
      try { await const MethodChannel('lan_messenger/screen_capture')
          .invokeMethod<void>('stop'); } catch (_) {}
    }
    try { await screen?.dispose().timeout(const Duration(seconds: 5)); }
    catch (e) { await _log('screen share dispose error: $e'); }
    try { await stream?.dispose().timeout(const Duration(seconds: 5)); }
    catch (e) { await _log('stream dispose error: $e'); }
    try { if (local != null) { local.srcObject = null; await local.dispose(); } }
    catch (e) { await _log('local renderer dispose error: $e'); }
    try { if (remote != null) { remote.srcObject = null; await remote.dispose(); } }
    catch (e) { await _log('remote renderer dispose error: $e'); }
    _closing = false;
  }
}