import 'dart:async';
import 'dart:io';
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
    try { await stream?.dispose().timeout(const Duration(seconds: 5)); }
    catch (e) { await _log('stream dispose error: $e'); }
    try { if (local != null) { local.srcObject = null; await local.dispose(); } }
    catch (e) { await _log('local renderer dispose error: $e'); }
    try { if (remote != null) { remote.srcObject = null; await remote.dispose(); } }
    catch (e) { await _log('remote renderer dispose error: $e'); }
    _closing = false;
  }
}