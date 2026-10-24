import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_webrtc/flutter_webrtc.dart';

import 'identity.dart';
import 'node.dart';
import 'protocol.dart';

/// LAN group calls use a peer-to-peer WebRTC mesh, capped at four devices.
/// Each participant has a separate authenticated connection to every other
/// participant, but captures microphone/camera only once per local room.
const maxGroupMembers = 4;

class GroupText {
  final String id;
  final String senderId;
  final String text;
  final DateTime time;
  const GroupText(this.id, this.senderId, this.text, this.time);
  Map<String, dynamic> toJson() => {
    'id': id, 'sender': senderId, 'text': text, 'time': time.toIso8601String(),
  };
  static GroupText? fromJson(dynamic value) {
    if (value is! Map) return null;
    final id = value['id'], sender = value['sender'], text = value['text'];
    if (id is! String || sender is! String || text is! String ||
        id.length > 100 || sender.length != 64 || text.length > 4000) return null;
    return GroupText(id, sender, text,
        DateTime.tryParse(value['time']?.toString() ?? '') ?? DateTime.now());
  }
}

class GroupRoom {
  final String id;
  final String name;
  final String creatorId;
  final List<String> members;
  final List<GroupText> messages = [];
  final Set<String> seen = {};
  GroupRoom(this.id, this.name, this.creatorId, this.members);

  static GroupRoom? parse(Map data, String ownId, String fromId) {
    final id = data['roomId'], name = data['name'];
    final creator = data['creatorId'], roster = data['members'];
    if (id is! String || !RegExp(r'^[a-f0-9]{32}$').hasMatch(id) ||
        name is! String || name.trim().isEmpty || name.length > 60 ||
        creator is! String || creator.length != 64 ||
        roster is! List || roster.length < 3 || roster.length > maxGroupMembers ||
        roster.any((v) => v is! String || !RegExp(r'^[a-f0-9]{64}$').hasMatch(v)) ||
        roster.toSet().length != roster.length ||
        !roster.contains(ownId) || !roster.contains(fromId) ||
        creator != fromId) return null;
    return GroupRoom(id, name.trim(), creator, List<String>.from(roster));
  }

  bool accepts(String member) => members.contains(member);
  bool addMessage(GroupText msg) {
    if (!accepts(msg.senderId) || msg.text.trim().isEmpty ||
        msg.text.length > 4000 || !seen.add('${msg.senderId}/${msg.id}')) return false;
    messages.add(msg);
    if (messages.length > 300) {
      final removed = messages.removeAt(0);
      seen.remove('${removed.senderId}/${removed.id}');
    }
    return true;
  }

  Map<String, dynamic> toJson() => {
    'roomId': id, 'name': name, 'creatorId': creatorId,
    'members': members, 'messages': messages.map((m) => m.toJson()).toList(),
  };
}

/// Encrypted group text and a separate bounded mesh call manager. No cloud,
/// central relay, remote input or unattended group call acceptance.
class GroupCoordinator {
  GroupCoordinator(this.node);
  final LanNode node;
  final Map<String, GroupRoom> rooms = {};
  GroupMediaCall? activeCall;
  Future<bool> Function(GroupRoom room, Peer inviter, bool video)? onCallInvite;
  void Function()? onChanged;
  final Set<String> _handledInvites = {};
  Future<void> _saveQueue = Future.value();

  Future<Directory> _storage() async =>
      node.storageDirectory ?? Identity.appDirectory();

  Future<void> load() async {
    try {
      final dir = await _storage();
      final file = File('${dir.path}${Platform.pathSeparator}groups.json');
      if (!await file.exists()) return;
      final data = jsonDecode(await file.readAsString());
      if (data is! List) return;
      for (final entry in data) {
        if (entry is! Map) continue;
        final id = entry['roomId'], creator = entry['creatorId'];
        if (id is! String || creator is! String) continue;
        final room = GroupRoom.parse(entry, node.identity.id, creator);
        if (room == null) continue;
        rooms[room.id] = room;
        final texts = entry['messages'];
        if (texts is List) {
          for (final item in texts.take(300)) {
            final text = GroupText.fromJson(item);
            if (text != null) room.addMessage(text);
          }
        }
      }
      onChanged?.call();
    } catch (_) {/* Corrupt local group data cannot block app startup. */}
  }

  void persist() {
    _saveQueue = _saveQueue.then((_) async {
      final dir = await _storage();
      final file = File('${dir.path}${Platform.pathSeparator}groups.json');
      await file.writeAsString(jsonEncode(
          rooms.values.map((r) => r.toJson()).toList()), flush: true);
    }).catchError((Object _) {});
  }

  Future<GroupRoom> create(String name, List<Peer> participants) async {
    final unique = <String, Peer>{for (final p in participants) p.id: p};
    if (name.trim().isEmpty || name.trim().length > 60 ||
        unique.length < 2 || unique.length >= maxGroupMembers ||
        unique.containsKey(node.identity.id)) {
      throw ArgumentError('Choose two or three other devices and a group name.');
    }
    final members = [node.identity.id, ...unique.keys]..sort();
    final room = GroupRoom(randomId(), name.trim(), node.identity.id, members);
    rooms[room.id] = room;
    persist();
    onChanged?.call();
    final invitation = {'type': 'group-room-invite', ...room.toJson()};
    for (final peer in unique.values) {
      unawaited(node.signal(peer, invitation).catchError((Object _) {}));
    }
    return room;
  }

  Future<void> sendText(GroupRoom room, String text) async {
    if (!rooms.containsKey(room.id) || text.trim().isEmpty || text.length > 4000) {
      throw ArgumentError('Invalid group message');
    }
    final msg = GroupText(randomId(), node.identity.id, text.trim(), DateTime.now());
    room.addMessage(msg);
    onChanged?.call();
    persist();
    for (final id in room.members) {
      if (id == node.identity.id) continue;
      final peer = node.peers[id];
      if (peer == null) continue;
      unawaited(node.signal(peer, {
        'type': 'group-text', 'roomId': room.id,
        'id': msg.id, 'text': msg.text,
      }).catchError((Object _) {}));
    }
  }

  Future<void> startCall(GroupRoom room, {required bool video}) async {
    if (activeCall != null || !rooms.containsKey(room.id)) {
      throw StateError('Already in a group call');
    }
    final call = GroupMediaCall(node, room, randomId(), video, onChanged: onChanged);
    activeCall = call;
    try {
      await call.join();
      for (final id in room.members) {
        if (id == node.identity.id) continue;
        final peer = node.peers[id];
        if (peer == null) continue;
        unawaited(node.signal(peer, {
          'type': 'group-call-invite', 'roomId': room.id,
          'sessionId': call.sessionId, 'video': video,
        }).catchError((Object _) {}));
      }
      onChanged?.call();
    } catch (_) {
      await call.leave();
      activeCall = null;
      rethrow;
    }
  }

  Future<void> endCall() async {
    final call = activeCall;
    if (call == null) return;
    activeCall = null;
    await call.leave();
    onChanged?.call();
  }

  Future<bool> incoming(Peer peer, Map<String, dynamic> data) async {
    final type = data['type'];
    if (type is! String || !type.startsWith('group-')) return false;
    if (type == 'group-room-invite') {
      final room = GroupRoom.parse(data, node.identity.id, peer.id);
      if (room != null && !rooms.containsKey(room.id)) {
        rooms[room.id] = room;
        persist();
        onChanged?.call();
      }
      return true;
    }
    final id = data['roomId'];
    final room = id is String ? rooms[id] : null;
    if (room == null || !room.accepts(peer.id)) return true;
    if (type == 'group-text') {
      final text = data['text'], messageId = data['id'];
      if (text is String && text.length <= 4000 &&
          messageId is String && messageId.length <= 100 &&
          messageId.isNotEmpty) {
        if (room.addMessage(GroupText(messageId, peer.id, text, DateTime.now()))) {
          persist();
          onChanged?.call();
        }
      }
      return true;
    }
    final sessionId = data['sessionId'];
    if (sessionId is! String ||
        !RegExp(r'^[a-f0-9]{32}$').hasMatch(sessionId)) return true;
    if (type == 'group-call-invite') {
      final unique = '${peer.id}/$sessionId';
      if (!_handledInvites.add(unique)) return true;
      if (_handledInvites.length > 100) _handledInvites.clear();
      if (activeCall != null) return true;
      final video = data['video'] == true;
      // The user must accept first; the microphone is never opened remotely.
      final accept = await (onCallInvite?.call(room, peer, video) ??
          Future<bool>.value(false));
      if (!accept || activeCall != null) return true;
      final call = GroupMediaCall(node, room, sessionId, video, onChanged: onChanged);
      activeCall = call;
      try {
        await call.join();
        onChanged?.call();
      } catch (_) {
        await call.leave();
        activeCall = null;
        onChanged?.call();
      }
      return true;
    }
    final call = activeCall;
    if (call != null && call.room.id == room.id && call.sessionId == sessionId) {
      await call.handle(peer, data);
    }
    return true;
  }
}

class GroupMediaCall {
  GroupMediaCall(this.node, this.room, this.sessionId, this.video, {this.onChanged});
  final LanNode node;
  final GroupRoom room;
  final String sessionId;
  final bool video;
  final void Function()? onChanged;
  final Map<String, RTCPeerConnection> _pcs = {};
  final Map<String, RTCVideoRenderer> remoteVideos = {};
  final Map<String, List<RTCIceCandidate>> _pendingIce = {};
  final Set<String> _joined = {};
  MediaStream? _local;
  RTCVideoRenderer? localVideo;
  bool muted = false;
  bool _closed = false;

  bool get joined => _local != null && !_closed;
  int get participantCount => _joined.length + (joined ? 1 : 0);

  Future<void> join() async {
    if (_closed || _local != null) return;
    final stream = await navigator.mediaDevices.getUserMedia({
      'audio': {
        'echoCancellation': true,
        'noiseSuppression': true,
        'autoGainControl': true,
      },
      'video': video ? {
        'facingMode': 'user', 'width': {'ideal': 320},
        'height': {'ideal': 240}, 'frameRate': {'ideal': 12},
      } : false,
    });
    if (_closed) {
      await stream.dispose();
      return;
    }
    _local = stream;
    if (video) {
      localVideo = RTCVideoRenderer();
      await localVideo!.initialize();
      localVideo!.srcObject = stream;
    }
    onChanged?.call();
    for (final id in room.members) {
      if (id == node.identity.id) continue;
      final peer = node.peers[id];
      if (peer == null) continue;
      unawaited(node.signal(peer, {
        'type': 'group-call-join', 'roomId': room.id,
        'sessionId': sessionId,
      }).catchError((Object _) {}));
    }
  }

  Future<RTCPeerConnection> _connection(Peer peer) async {
    final existing = _pcs[peer.id];
    if (existing != null) return existing;
    final stream = _local;
    if (_closed || stream == null) throw StateError('Group call not joined');
    final pc = await createPeerConnection({
      'iceServers': <Map<String, dynamic>>[],
      'iceTransportPolicy': 'all', 'sdpSemantics': 'unified-plan',
    });
    if (_closed) { await pc.dispose(); throw StateError('Call ended'); }
    _pcs[peer.id] = pc;
    pc.onIceCandidate = (candidate) {
      if (_closed || candidate.candidate == null) return;
      unawaited(node.signal(peer, {
        'type': 'group-call-ice', 'roomId': room.id, 'sessionId': sessionId,
        'candidate': candidate.candidate,
        'mid': candidate.sdpMid, 'mLine': candidate.sdpMLineIndex,
      }).catchError((Object _) {}));
    };
    pc.onTrack = (event) {
      if (_closed || !video || event.track.kind != 'video' ||
          event.streams.isEmpty) return;
      final renderer = remoteVideos[peer.id];
      if (renderer != null) {
        renderer.srcObject = event.streams.first;
        onChanged?.call();
      }
    };
    pc.onConnectionState = (state) {
      if (_closed) return;
      if (state == RTCPeerConnectionState.RTCPeerConnectionStateFailed ||
          state == RTCPeerConnectionState.RTCPeerConnectionStateClosed) {
        _joined.remove(peer.id);
        onChanged?.call();
      }
    };
    if (video) {
      final renderer = RTCVideoRenderer();
      await renderer.initialize();
      remoteVideos[peer.id] = renderer;
    }
    for (final track in stream.getTracks()) {
      await pc.addTrack(track, stream);
    }
    onChanged?.call();
    return pc;
  }

  Future<void> _flush(Peer peer) async {
    final pc = _pcs[peer.id];
    if (pc == null) return;
    final list = _pendingIce.remove(peer.id) ?? [];
    for (final candidate in list) {
      try { await pc.addCandidate(candidate); } catch (_) {}
    }
  }

  Future<void> _offer(Peer peer) async {
    if (_closed || _pcs.containsKey(peer.id) || !joined) return;
    final pc = await _connection(peer);
    final sdp = await pc.createOffer({
      'offerToReceiveAudio': true, 'offerToReceiveVideo': video,
    });
    await pc.setLocalDescription(sdp);
    await node.signal(peer, {
      'type': 'group-call-offer', 'roomId': room.id,
      'sessionId': sessionId, 'sdp': sdp.sdp,
    });
  }

  Future<void> handle(Peer peer, Map<String, dynamic> data) async {
    if (_closed || !joined || !room.accepts(peer.id)) return;
    final type = data['type'];
    if (type == 'group-call-join') {
      if (_joined.add(peer.id)) {
        // A single acknowledgement makes both earlier and later joiners see
        // each other, without an endless JOIN/JOIN ping-pong.
        unawaited(node.signal(peer, {
          'type': 'group-call-join', 'roomId': room.id,
          'sessionId': sessionId,
        }).catchError((Object _) {}));
      }
      if (node.identity.id.compareTo(peer.id) < 0) {
        try { await _offer(peer); } catch (_) {}
      }
      onChanged?.call();
    } else if (type == 'group-call-offer' && data['sdp'] is String) {
      if (node.identity.id.compareTo(peer.id) < 0) return;
      try {
        final pc = await _connection(peer);
        await pc.setRemoteDescription(RTCSessionDescription(data['sdp'] as String, 'offer'));
        await _flush(peer);
        final answer = await pc.createAnswer({
          'offerToReceiveAudio': true, 'offerToReceiveVideo': video,
        });
        await pc.setLocalDescription(answer);
        await node.signal(peer, {
          'type': 'group-call-answer', 'roomId': room.id,
          'sessionId': sessionId, 'sdp': answer.sdp,
        });
      } catch (_) { /* Isolate this peer; keep other group participants live. */ }
    } else if (type == 'group-call-answer' && data['sdp'] is String) {
      final pc = _pcs[peer.id];
      if (pc == null) return;
      try {
        await pc.setRemoteDescription(RTCSessionDescription(data['sdp'] as String, 'answer'));
        await _flush(peer);
      } catch (_) {}
    } else if (type == 'group-call-ice' && data['candidate'] is String) {
      final candidate = RTCIceCandidate(data['candidate'] as String,
          data['mid'] as String?, data['mLine'] as int?);
      final pc = _pcs[peer.id];
      if (pc == null || await pc.getRemoteDescription() == null) {
        _pendingIce.putIfAbsent(peer.id, () => []).add(candidate);
      } else {
        try { await pc.addCandidate(candidate); } catch (_) {}
      }
    } else if (type == 'group-call-leave') {
      _joined.remove(peer.id);
      final pc = _pcs.remove(peer.id);
      if (pc != null) {
        try { await pc.close(); await pc.dispose(); } catch (_) {}
      }
      final renderer = remoteVideos.remove(peer.id);
      if (renderer != null) {
        try { await renderer.dispose(); } catch (_) {}
      }
      onChanged?.call();
    }
  }

  Future<void> setMuted(bool value) async {
    muted = value;
    for (final track in _local?.getAudioTracks() ?? <MediaStreamTrack>[]) {
      track.enabled = !value;
    }
    onChanged?.call();
  }

  Future<void> leave() async {
    if (_closed) return;
    _closed = true;
    for (final id in room.members) {
      if (id == node.identity.id) continue;
      final peer = node.peers[id];
      if (peer == null) continue;
      unawaited(node.signal(peer, {
        'type': 'group-call-leave', 'roomId': room.id,
        'sessionId': sessionId,
      }).catchError((Object _) {}));
    }
    final pcs = _pcs.values.toList();
    _pcs.clear();
    for (final pc in pcs) {
      try {
        pc.onIceCandidate = null;
        pc.onTrack = null;
        pc.onConnectionState = null;
        await pc.close().timeout(const Duration(seconds: 4));
        await pc.dispose().timeout(const Duration(seconds: 4));
      } catch (_) {}
    }
    for (final renderer in remoteVideos.values) {
      try { renderer.srcObject = null; await renderer.dispose(); } catch (_) {}
    }
    remoteVideos.clear();
    if (localVideo != null) {
      try { localVideo!.srcObject = null; await localVideo!.dispose(); } catch (_) {}
    }
    localVideo = null;
    final local = _local;
    _local = null;
    if (local != null) {
      for (final track in local.getTracks()) {
        try { await track.stop(); } catch (_) {}
      }
      try { await local.dispose(); } catch (_) {}
    }
    _joined.clear();
    onChanged?.call();
  }
}
