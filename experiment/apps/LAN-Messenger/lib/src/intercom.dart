import 'dart:async';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'node.dart';
import 'protocol.dart';

class Intercom {
  final LanNode node;
  Peer? talkingTo;
  String? callId;
  RTCPeerConnection? _connection;
  MediaStream? _mic;
  final Map<String, List<RTCIceCandidate>> _pendingIce = {};
  bool connecting = false;
  bool _remoteDescriptionReady = false;
  Timer? _answerTimeout;
  void Function()? onChanged;
  Future<bool> Function(Peer)? onIncoming;
  Intercom(this.node);

  Future<RTCPeerConnection> _prepare(Peer peer, String id) async {
    _mic = await navigator.mediaDevices.getUserMedia({'audio': true, 'video': false});
    // Deliberately no STUN, TURN, relay, or internet-dependent infrastructure.
    final pc = await createPeerConnection({
      'iceServers': <Map<String, dynamic>>[],
      'iceTransportPolicy': 'all',
    });
    _connection = pc;
    pc.onIceCandidate = (candidate) {
      if (candidate.candidate != null) {
        unawaited(node.signal(peer, {'type': 'ice', 'callId': id,
          'candidate': candidate.candidate, 'mid': candidate.sdpMid,
          'mLine': candidate.sdpMLineIndex}).catchError((_) {}));
      }
    };
    pc.onConnectionState = (state) {
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
          state == RTCPeerConnectionState.RTCPeerConnectionStateClosed) {
        unawaited(hangUp(notify: false));
      }
      onChanged?.call();
    };
    for (final track in _mic!.getAudioTracks()) {
      await pc.addTrack(track, _mic!);
    }
    return pc;
  }

  Future<void> call(Peer peer) async {
    if (talkingTo != null) throw StateError('Already in a call');
    final id = randomId();
    talkingTo = peer;
    callId = id;
    connecting = true;
    onChanged?.call();
    try {
      final pc = await _prepare(peer, id);
      final offer = await pc.createOffer({'offerToReceiveAudio': true});
      await pc.setLocalDescription(offer);
      await node.signal(peer, {'type': 'offer', 'callId': id, 'sdp': offer.sdp});
      // A missed call must not leave the microphone and call UI active forever.
      _answerTimeout = Timer(const Duration(seconds: 45), () {
        if (callId == id && connecting) unawaited(hangUp());
      });
    } catch (_) {
      await hangUp(notify: false);
      rethrow;
    }
  }

  Future<void> incomingSignal(Peer peer, Map<String, dynamic> data) async {
    final type = data['type'];
    final id = data['callId'];
    if (id is! String || id.length > 64 || type is! String) return;
    if (type == 'offer') {
      if (talkingTo != null || data['sdp'] is! String) {
        unawaited(node.signal(peer, {'type': 'hangup', 'callId': id}).catchError((_) {}));
        return;
      }
      talkingTo = peer;
      callId = id;
      connecting = true;
      onChanged?.call();
      try {
        final accepted = await (onIncoming?.call(peer) ?? Future.value(false));
        if (!accepted) {
          await hangUp();
          return;
        }
        final pc = await _prepare(peer, id);
        await pc.setRemoteDescription(RTCSessionDescription(data['sdp'] as String, 'offer'));
        _remoteDescriptionReady = true;
        await _flushIce(id);
        final answer = await pc.createAnswer({'offerToReceiveAudio': true});
        await pc.setLocalDescription(answer);
        await node.signal(peer, {'type': 'answer', 'callId': id, 'sdp': answer.sdp});
        connecting = false;
        onChanged?.call();
      } catch (_) { await hangUp(); }
      return;
    }
    if (type == 'ice' && data['candidate'] is String) {
      if (id != callId || peer.id != talkingTo?.id) return;
      final candidate = RTCIceCandidate(data['candidate'] as String,
          data['mid'] as String?, data['mLine'] as int?);
      if (_connection == null || !_remoteDescriptionReady) {
        _pendingIce.putIfAbsent(id, () => []).add(candidate);
      } else {
        try { await _connection!.addCandidate(candidate); } catch (_) {}
      }
    } else if (type == 'answer' && data['sdp'] is String &&
        id == callId && peer.id == talkingTo?.id) {
      await _connection?.setRemoteDescription(
          RTCSessionDescription(data['sdp'] as String, 'answer'));
      _remoteDescriptionReady = true;
      await _flushIce(id);
      connecting = false;
      _answerTimeout?.cancel();
      _answerTimeout = null;
      onChanged?.call();
    } else if (type == 'hangup' && id == callId && peer.id == talkingTo?.id) {
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

  Future<void> hangUp({bool notify = true}) async {
    _answerTimeout?.cancel();
    _answerTimeout = null;
    final peer = talkingTo;
    final id = callId;
    talkingTo = null;
    callId = null;
    connecting = false;
    _remoteDescriptionReady = false;
    _pendingIce.clear();
    final pc = _connection;
    final stream = _mic;
    _connection = null;
    _mic = null;
    onChanged?.call();
    if (notify && peer != null && id != null) {
      unawaited(node.signal(peer, {'type': 'hangup', 'callId': id}).catchError((_) {}));
    }
    if (stream != null) {
      for (final track in stream.getTracks()) { track.stop(); }
      await stream.dispose();
    }
    await pc?.close();
  }
}