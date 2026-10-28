import 'dart:async';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'intercom.dart';
import 'groups.dart';
import 'node.dart';
import 'protocol.dart';

/// Opt-in peer-to-peer mesh, not a centralized server or a hidden relay.
/// Every pair negotiates a separate encrypted LAN signaling/WebRTC connection.
/// A hard cap of four participants bounds microphone, codec and bandwidth use.
class GroupCallMesh {
  GroupCallMesh(this.node, this.messaging);
  final LanNode node;
  final GroupMessaging messaging;
  GroupRoom? activeRoom;
  String? sessionId;
  bool video = false;
  final Map<String, Intercom> links = {};
  final Set<String> _announcedTo = {};
  // Share one OS capture across every pair in a 3–4 person mesh. Reopening the
  // same camera for each peer fails on devices with exclusive camera access.
  Future<MediaStream>? _captureFuture;
  MediaStream? _capture;
  RTCVideoRenderer? localRenderer;
  bool _leaving = false;
  bool _muted = false;
  String? mediaError;
  Future<bool> Function(Peer, GroupRoom, bool)? onInvitation;
  void Function()? onChanged;

  bool get active => activeRoom != null && sessionId != null;
  // A pending WebRTC offer is not yet a joined participant.
  int get participants => 1 + links.values
      .where((link) => link.talkingTo != null && !link.connecting).length;

  /// Distinct call IDs are owned by individual encrypted WebRTC mesh links.
  /// Never compare a probe against the room's sessionId: that is a shared
  /// coordination ID, NOT the per-peer media call identity.
  /// The link is valid while ICE/SDP negotiation is still in progress.
  bool hasLiveLinkSession(Peer peer, String callSessionId) {
    if (!active || _leaving || activeRoom?.includes(peer.id) != true) {
      return false;
    }
    final link = links[peer.id];
    return link != null && link.callId == callSessionId &&
        link.talkingTo?.id == peer.id && !link.closing;
  }

  static bool canCall(GroupRoom room) => room.members.length >= 3 &&
      room.members.length <= 4;

  Future<MediaStream> _sharedMedia() {
    if (!active || _leaving) {
      return Future<MediaStream>.error(StateError('Group session ended'));
    }
    return _captureFuture ??= _acquireMedia();
  }

  Future<MediaStream> _acquireMedia() async {
    MediaStream? captured;
    RTCVideoRenderer? preview;
    try {
      captured = await navigator.mediaDevices.getUserMedia({
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
      if (!active || _leaving) throw StateError('Group ended during capture');
      if (_muted) {
        for (final track in captured.getAudioTracks()) {
          track.enabled = false;
        }
      }
      if (video) {
        preview = RTCVideoRenderer();
        await preview.initialize();
        if (!active || _leaving) throw StateError('Group ended during preview');
        preview.srcObject = captured;
      }
      _capture = captured;
      localRenderer = preview;
      mediaError = null;
      onChanged?.call();
      return captured;
    } catch (e) {
      if (preview != null) {
        try { preview.srcObject = null; await preview.dispose(); } catch (_) {}
      }
      if (captured != null) {
        for (final track in captured.getTracks()) {
          try { await track.stop(); } catch (_) {}
        }
        try { await captured.dispose(); } catch (_) {}
      }
      _captureFuture = null; // Allow retry after camera-permission failures.
      mediaError = 'Microphone/camera unavailable: $e';
      onChanged?.call();
      rethrow;
    }
  }

  Future<void> start(GroupRoom room, {required bool withVideo}) async {
    if (active || _leaving || !canCall(room) ||
        messaging.rooms[room.id] != room ||
        !room.includes(node.identity.id)) {
      throw StateError('Group calls support one active room with 3–4 members');
    }
    _announcedTo.clear();
    _muted = false;
    mediaError = null;
    activeRoom = room;
    sessionId = randomId();
    video = withVideo;
    onChanged?.call();
    await _broadcast('group-start');
    await _broadcast('group-join');
  }

  Future<void> _broadcast(String type) async {
    final room = activeRoom, id = sessionId;
    if (room == null || id == null) return;
    await Future.wait(room.members.where((m) => m != node.identity.id)
        .map((member) async {
      final peer = node.peers[member];
      if (peer == null || !node.isOnline(peer)) return;
      try {
        await node.signal(peer, {'type': type, 'groupId': room.id,
          'sessionId': id, 'video': video});
      } catch (_) { /* Peer may have gone offline. */ }
    }));
  }

  Intercom _link(Peer peer) {
    return links.putIfAbsent(peer.id, () {
      final call = Intercom(node, sharedMediaProvider: _sharedMedia);
      call.onIncoming = (caller, requestedVideo) async =>
          active && activeRoom?.includes(caller.id) == true &&
          caller.id == peer.id && requestedVideo == video;
      call.onChanged = () {
        onChanged?.call();
        // A peer leaving must never end other group participants' calls.
      };
      return call;
    });
  }

  Future<bool> handle(Peer sender, Map<String, dynamic> data) async {
    final type = data['type'];
    final roomId = data['groupId'], id = data['sessionId'];
    if (type == 'group-start') {
      if (roomId is! String || id is! String || id.isEmpty || id.length > 64) return true;
      final room = messaging.rooms[roomId];
      if (active || _leaving || room == null || !room.includes(sender.id) ||
          !canCall(room)) return true;
      final requestedVideo = data['video'] == true;
      final accepted = await (onInvitation?.call(sender, room, requestedVideo) ??
          Future<bool>.value(false));
      if (!accepted || active) return true;
      _announcedTo.clear();
      _muted = false;
      mediaError = null;
      activeRoom = room;
      sessionId = id;
      video = requestedVideo;
      onChanged?.call();
      await _broadcast('group-join');
      return true;
    }
    if (type == 'group-join') {
      if (!active || id != sessionId || roomId != activeRoom?.id ||
          activeRoom?.includes(sender.id) != true ||
          sender.id == node.identity.id || data['video'] != video) return true;
      // Confirm our presence once to each new joiner. This prevents
      // deadlock if an earlier join broadcast arrived before they accepted.
      if (_announcedTo.add(sender.id)) {
        unawaited(node.signal(sender, {
          'type': 'group-join', 'groupId': activeRoom!.id,
          'sessionId': sessionId, 'video': video,
        }).catchError((Object _) {}));
      }
      final link = _link(sender);
      // Deterministic caller order prevents simultaneous-offer glare.
      if (node.identity.id.compareTo(sender.id) < 0 &&
          link.talkingTo == null) {
        unawaited(link.call(sender, withVideo: video,
          groupId: activeRoom!.id, groupSessionId: sessionId)
            .catchError((Object _) {}));
      }
      onChanged?.call();
      return true;
    }
    if (type == 'group-leave') {
      if (active && id == sessionId && roomId == activeRoom?.id &&
          activeRoom?.includes(sender.id) == true) {
        _announcedTo.remove(sender.id);
        final peer = links.remove(sender.id);
        if (peer != null) await peer.hangUp(notify: false);
        onChanged?.call();
      }
      return true;
    }
    // Group SDP offers identify the authorized existing room and live session.
    // Answers and ICE must match a previously created per-peer callId.
    if (type == 'offer' && data['groupId'] is String) {
      if (!active || data['groupId'] != activeRoom?.id ||
          data['groupSessionId'] != sessionId ||
          activeRoom?.includes(sender.id) != true) return true;
      final link = _link(sender);
      if (link.talkingTo != null) return true;
      await link.incomingSignal(sender, data);
      return true;
    }
    final existing = links[sender.id];
    if (existing != null && data['callId'] == existing.callId) {
      await existing.incomingSignal(sender, data);
      return true;
    }
    return false;
  }

  bool get muted => _muted;

  Future<void> setMuted(bool muted) async {
    _muted = muted;
    final stream = _capture;
    if (stream != null) {
      for (final track in stream.getAudioTracks()) {
        track.enabled = !muted;
      }
    }
    await Future.wait(links.values.map((link) => link.setMuted(muted)));
    onChanged?.call();
  }

  Future<void> leave() async {
    if (!active || _leaving) return;
    _leaving = true;
    try {
      await _broadcast('group-leave');
      final old = links.values.toList();
      links.clear();
      _announcedTo.clear();
      activeRoom = null;
      sessionId = null;
      video = false;
      _muted = false;
      onChanged?.call();
      // Each link owns only its PeerConnection and renderers, not the capture.
      await Future.wait(old.map((link) async {
        try { await link.hangUp(notify: false); } catch (_) {}
      }));
    } finally {
      // A capture can still be resolving while the room is shutting down.
      final pending = _captureFuture;
      if (pending != null) {
        try { await pending; } catch (_) {}
      }
      _captureFuture = null;
      final preview = localRenderer;
      localRenderer = null;
      if (preview != null) {
        try { preview.srcObject = null; await preview.dispose(); } catch (_) {}
      }
      final stream = _capture;
      _capture = null;
      if (stream != null) {
        for (final track in stream.getTracks()) {
          try { await track.stop(); } catch (_) {}
          try { await track.dispose(); } catch (_) {}
        }
        try { await stream.dispose(); } catch (_) {}
      }
      _leaving = false;
      mediaError = null;
      onChanged?.call();
    }
  }
}
