import 'dart:async';
import 'dart:io';
import 'identity.dart';
import 'recoverable_json_file.dart';
import 'node.dart';
import 'protocol.dart';

/// Group content stays locally persisted and is sent only through LanNode's
/// existing authenticated/encrypted peer channel. Max 8 participants per chat.
class GroupRoom {
  GroupRoom({required this.id, required this.name,
    required this.ownerId, required this.members,
    List<GroupChatEntry>? messages}) : messages = messages ?? [];
  final String id;
  String name;
  final String ownerId;
  final List<String> members;
  final List<GroupChatEntry> messages;
  bool includes(String peerId) => members.contains(peerId);
  Map<String, dynamic> toJson() => {
    'id': id, 'name': name, 'owner': ownerId, 'members': members,
    'messages': messages.map((m) => m.toJson()).toList(),
  };
  static GroupRoom? fromJson(dynamic data) {
    if (data is! Map || data['id'] is! String ||
        data['name'] is! String || data['owner'] is! String ||
        data['members'] is! List) return null;
    final ids = (data['members'] as List).whereType<String>().toSet().toList();
    if (ids.isEmpty || ids.length > 8 || !ids.contains(data['owner']) ||
        (data['id'] as String).length > 64 ||
        (data['name'] as String).length > 60) return null;
    final entries = (data['messages'] is List ? data['messages'] as List : [])
        .map(GroupChatEntry.fromJson).whereType<GroupChatEntry>().take(300).toList();
    return GroupRoom(id: data['id'], name: data['name'],
      ownerId: data['owner'], members: ids, messages: entries);
  }
}
class GroupChatEntry {
  const GroupChatEntry({required this.id, required this.sender,
    required this.body, required this.when});
  final String id, sender, body;
  final DateTime when;
  Map<String, dynamic> toJson() =>
      {'id': id, 'from': sender, 'body': body, 'when': when.toIso8601String()};
  static GroupChatEntry? fromJson(dynamic json) {
    if (json is! Map || json['id'] is! String ||
        json['from'] is! String || json['body'] is! String ||
        json['when'] is! String) return null;
    final when = DateTime.tryParse(json['when'] as String);
    if (when == null || (json['id'] as String).length > 64 ||
        (json['body'] as String).length > 4000) return null;
    return GroupChatEntry(id: json['id'], sender: json['from'],
      body: json['body'], when: when);
  }
}

class GroupMessaging {
  GroupMessaging(this.node);
  final LanNode node;
  final Map<String, GroupRoom> rooms = {};
  Future<bool> Function(Peer, String name, int participantCount)? onInvitation;
  void Function()? onChanged;
  Future<void> _pending = Future<void>.value();

  Future<void> load() async {
    try {
      final folder = await Identity.appDirectory();
      final file = File('${folder.path}${Platform.pathSeparator}groups.json');
      if (!await RecoverableJsonFile.hasSavedState(file)) return;
      final raw = await RecoverableJsonFile.read(file, isValid: (value) => value is List);
      if (raw is! List) return;
      for (final item in raw) {
        final room = GroupRoom.fromJson(item);
        if (room != null && room.includes(node.identity.id)) rooms[room.id] = room;
      }
    } catch (_) { /* Broken local cache must not prevent device discovery. */ }
    onChanged?.call();
  }
  void _save() {
    _pending = _pending.then((_) async {
      final folder = await Identity.appDirectory();
      final file = File('${folder.path}${Platform.pathSeparator}groups.json');
      await RecoverableJsonFile.write(
          file, rooms.values.map((r) => r.toJson()).toList());
    }).catchError((Object _) {});
  }
  Future<GroupRoom> create(String name, List<Peer> members) async {
    final cleanName = name.trim();
    final ids = {node.identity.id, ...members.map((m) => m.id)}.toList();
    if (cleanName.isEmpty || cleanName.length > 60 ||
        ids.length < 3 || ids.length > 8 ||
        members.any((m) => node.peers[m.id]?.key != m.key)) {
      throw StateError('Choose a group name and 2–7 trusted LAN peers');
    }
    final room = GroupRoom(id: randomId(), name: cleanName,
      ownerId: node.identity.id, members: ids);
    rooms[room.id] = room; _save(); onChanged?.call();
    await invite(room);
    return room;
  }
  Future<void> invite(GroupRoom room) async {
    if (room.ownerId != node.identity.id) return;
    await Future.wait(room.members.where((id) => id != node.identity.id)
        .map((id) async {
      final peer = node.peers[id];
      if (peer == null || !node.isOnline(peer)) return;
      try {
        await node.signal(peer, {
          'type': 'group-invite', 'groupId': room.id,
          'owner': node.identity.id, 'name': room.name,
          'members': room.members,
        });
      } catch (_) { /* Offline invite can be re-sent manually. */ }
    }));
  }
  Future<void> send(GroupRoom room, String text) async {
    if (rooms[room.id] != room || !room.includes(node.identity.id)) {
      throw StateError('Not in this group');
    }
    final body = text.trim();
    if (body.isEmpty || body.length > 4000) throw StateError('Invalid message length');
    final entry = GroupChatEntry(id: randomId(), sender: node.identity.id,
      body: body, when: DateTime.now().toUtc());
    room.messages.add(entry);
    if (room.messages.length > 300) room.messages.removeAt(0);
    _save(); onChanged?.call();
    await Future.wait(room.members.where((id) => id != node.identity.id)
        .map((id) async {
      final peer = node.peers[id];
      if (peer == null || !node.isOnline(peer)) return;
      try {
        await node.signal(peer, {
          'type': 'group-chat', 'groupId': room.id,
          'messageId': entry.id, 'text': body,
          'when': entry.when.toIso8601String(),
        });
      } catch (_) { /* Delivery is best effort on offline LAN. */ }
    }));
  }
  Future<bool> receive(Peer sender, Map<String, dynamic> data) async {
    final type = data['type'];
    final id = data['groupId'];
    if (id is! String || id.length > 64) return false;
    if (type == 'group-invite') {
      final owner = data['owner'], name = data['name'], raw = data['members'];
      if (owner != sender.id || name is! String || name.isEmpty ||
          name.length > 60 || raw is! List) return true;
      final memberIds = raw.whereType<String>().toSet().toList();
      if (memberIds.length < 3 || memberIds.length > 8 ||
          !memberIds.contains(node.identity.id) || !memberIds.contains(sender.id) ||
          memberIds.any((m) => m != node.identity.id && !node.peers.containsKey(m))) {
        return true;
      }
      final existing = rooms[id];
      if (existing != null) {
        // Group authority cannot be silently reassigned by forged invites.
        if (existing.ownerId != sender.id) return true;
        return true;
      }
      final approved = await (onInvitation?.call(sender, name, memberIds.length) ??
          Future<bool>.value(false));
      if (approved != true) return true;
      rooms[id] = GroupRoom(id: id, name: name,
          ownerId: sender.id, members: memberIds);
      _save(); onChanged?.call();
      return true;
    }
    if (type != 'group-chat') return false;
    final room = rooms[id];
    if (room == null || !room.includes(sender.id)) return true;
    final msgId = data['messageId'], body = data['text'], at = data['when'];
    if (msgId is! String || msgId.length > 64 ||
        body is! String || body.isEmpty || body.length > 4000 ||
        at is! String) return true;
    if (room.messages.any((m) => m.id == msgId && m.sender == sender.id)) return true;
    final time = DateTime.tryParse(at);
    if (time == null) return true;
    room.messages.add(GroupChatEntry(id: msgId, sender: sender.id,
        body: body, when: time));
    if (room.messages.length > 300) room.messages.removeAt(0);
    _save(); onChanged?.call();
    return true;
  }
}
