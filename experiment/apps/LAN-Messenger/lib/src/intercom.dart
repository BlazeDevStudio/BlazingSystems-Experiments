import 'dart:async';
import 'dart:io';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:flutter/services.dart';
import 'identity.dart';
import 'node.dart';
import 'windows_remote_input.dart';
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
  bool remoteControlActive = false;
  String? _approvedControllerId;
  DateTime? _controlDeadline;
  DateTime? _lastInputAt;
  bool get remoteControlApproved => _approvedControllerId == talkingTo?.id &&
      _controlDeadline != null &&
      DateTime.now().isBefore(_controlDeadline!);
  Future<bool> Function(Peer peer)? onRemoteControlRequest;

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
    remoteControlActive = false;
    onChanged?.call();
    if (peer != null && id != null) {
      try { await node.signal(peer, {
        'type': 'control-grant', 'callId': id, 'enabled': false,
      }); } catch (_) {}
    }
  }

  Future<void> sendRemoteClick(double x, double y) async {
    final peer = talkingTo;
    if (!remoteControlActive || !peerSharingScreen ||
        peer == null || callId == null ||
        !x.isFinite || !y.isFinite || x < 0 || x > 1 || y < 0 || y > 1) return;
    await node.signal(peer, {
      'type': 'control-click', 'callId': callId, 'x': x, 'y': y,
    });
  }

  MediaStream? _displayStream;
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
      final granted = await Helper.requestCapturePermission();
      if (!granted) throw StateError('Screen sharing was declined');
      await const MethodChannel('lan_messenger/projection')
          .invokeMethod<void>('start');
    }
    MediaStream? display;
    try {
      display = await navigator.mediaDevices.getDisplayMedia({
        'audio': false, 'video': {'frameRate': 12},
      });
      if (_closing || _connection == null || talkingTo == null) {
        throw StateError('The call ended while selecting a screen');
      }
      if (display.getVideoTracks().isEmpty) {
        throw StateError('No screen video track available');
      }
      final senders = await _connection!.getSenders();
      final videoSenders = senders.where((s) => s.track?.kind == 'video').toList();
      if (videoSenders.isEmpty) throw StateError('Video sender unavailable');
      await videoSenders.first.replaceTrack(display.getVideoTracks().first);
      _displayStream = display;
      sharingScreen = true;
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
    if (video) unawaited(refreshCameras());
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
    sharingScreen = false;
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
        connecting = false;
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
      if (!sharingScreen || !Platform.isWindows) return;
      // Existing authenticated peer + same live call ID; approval is never
      // automatic, lasts five minutes, and can be revoked locally.
      final accepted = await (onRemoteControlRequest?.call(peer) ??
          Future<bool>.value(false));
      if (callId != id || talkingTo?.id != peer.id || !sharingScreen) return;
      _approvedControllerId = accepted ? peer.id : null;
      _controlDeadline = accepted
          ? DateTime.now().add(const Duration(minutes: 5)) : null;
      await node.signal(peer, {
        'type': 'control-grant', 'callId': id, 'enabled': accepted,
      }).catchError((_) {});
      onChanged?.call();
      return;
    }
    if (type == 'control-grant') {
      remoteControlActive = data['enabled'] == true && peerSharingScreen;
      onChanged?.call();
      return;
    }
    if (type == 'control-click') {
      if (!Platform.isWindows || !sharingScreen || !remoteControlApproved ||
          _approvedControllerId != peer.id) return;
      final x = data['x'];
      final y = data['y'];
      if (x is! num || y is! num ||
          !x.isFinite || !y.isFinite ||
          x < 0 || x > 1 || y < 0 || y > 1) return;
      final now = DateTime.now();
      // Rate-limit remote input to at most ten clicks per second.
      if (_lastInputAt != null &&
          now.difference(_lastInputAt!) < const Duration(milliseconds: 100)) return;
      _lastInputAt = now;
      WindowsRemoteInput.clickNormalized(x.toDouble(), y.toDouble());
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
    final stream = _localStream;
    final display = _displayStream;
    _displayStream = null;
    sharingScreen = false;
    peerSharingScreen = false;
    remoteControlActive = false;
    _approvedControllerId = null;
    _controlDeadline = null;
    _lastInputAt = null;
    availableCameras = <MediaDeviceInfo>[];
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
    if (display != null) {
      for (final track in display.getTracks()) { track.stop(); }
      try { await display.dispose().timeout(const Duration(seconds: 5)); }
      catch (e) { await _log('display stream dispose error: $e'); }
    }
    if (Platform.isAndroid) {
      try { await const MethodChannel('lan_messenger/projection')
          .invokeMethod<void>('stop'); } catch (_) {}
    }
    try { await stream?.dispose().timeout(const Duration(seconds: 5)); }
    catch (e) { await _log('stream dispose error: $e'); }
    try { if (local != null) { local.srcObject = null; await local.dispose(); } }
    catch (e) { await _log('local renderer dispose error: $e'); }
    try { if (remote != null) { remote.srcObject = null; await remote.dispose(); } }
    catch (e) { await _log('remote renderer dispose error: $e'); }
    _closing = false;
  }
}