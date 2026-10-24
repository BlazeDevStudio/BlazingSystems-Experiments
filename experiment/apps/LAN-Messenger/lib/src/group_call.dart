import 'dart:async';
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
  Future<bool> Function(Peer, GroupRoom, bool)? onInvitation;
  void Function()? onChanged;

  bool get active => activeRoom != null && sessionId != null;
  // A pending WebRTC offer is not yet a joined participant.
  int get participants => 1 + links.values
      .where((link) => link.talkingTo != null && !link.connecting).length;
  static bool canCall(GroupRoom room) => room.members.length >= 3 &&
      room.members.length <= 4;

  Future<void> start(GroupRoom room, {required bool withVideo}) async {
    if (active || !canCall(room) ||
        messaging.rooms[room.id] != room ||
        !room.includes(node.identity.id)) {
      throw StateError('Group calls support one active room with 3–4 members');
    }
    _announcedTo.clear();
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
      final call = Intercom(node);
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
      if (active || room == null || !room.includes(sender.id) ||
          !canCall(room)) return true;
      final requestedVideo = data['video'] == true;
      final accepted = await (onInvitation?.call(sender, room, requestedVideo) ??
          Future<bool>.value(false));
      if (!accepted || active) return true;
      _announcedTo.clear();
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

  Future<void> setMuted(bool muted) async {
    await Future.wait(links.values.map((link) => link.setMuted(muted)));
    onChanged?.call();
  }
  bool get muted => links.isNotEmpty &&
      links.values.every((link) => link.muted);
  Future<void> leave() async {
    if (!active) return;
    await _broadcast('group-leave');
    final old = links.values.toList();
    links.clear();
    _announcedTo.clear();
    activeRoom = null; sessionId = null; video = false;
    onChanged?.call();
    await Future.wait(old.map((link) => link.hangUp(notify: false)));
  }
}
