import 'dart:async';
import 'dart:convert';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/group_call.dart';
import 'package:lan_messenger/src/groups.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

class FakeLanNode extends LanNode {
  FakeLanNode(super.identity);
  Map<String, FakeLanNode>? network;
  final List<Map<String, dynamic>> sent = [];
  @override
  Future<void> signal(Peer peer, Map<String, dynamic> data) async {
    sent.add({...data});
    final remote = network?[peer.id];
    if (remote == null) throw StateError('offline');
    final sender = remote.peers[this.identity.id]!;
    remote.onSignal?.call(sender, data);
  }
}
Future<Identity> identity(String name) async {
  final pair = await X25519().newKeyPair();
  return Identity(await pair.extract(), name);
}
Peer peer(Identity i) => Peer(id: i.id, name: i.displayName, key: i.publicKeyB64,
  host: '127.0.0.1', port: 39823, seen: DateTime.now());

void main() {
  test('reject malformed group records and replayed sender content', () {
    expect(GroupRoom.fromJson({'id': 'x', 'name': 'bad', 'owner': 'o',
      'members': ['other']}), isNull);
    final r = GroupRoom(id: 'room1', name: 'LAN', ownerId: 'owner',
        members: ['owner', 'a', 'b']);
    expect(GroupRoom.fromJson(jsonDecode(jsonEncode(r.toJson())))!.members,
        containsAll(['owner', 'a', 'b']));
    expect(GroupChatEntry.fromJson({
      'id': 'm', 'from': 'a', 'body': 'hey',
      'when': DateTime.now().toUtc().toIso8601String(),
    }), isNotNull);
    expect(GroupChatEntry.fromJson({
      'id': 'm', 'from': 'a', 'body': List.filled(4001, 'X').join(),
      'when': DateTime.now().toUtc().toIso8601String(),
    }), isNull);
  });

  test('encryptable group envelope is routed to members only and deduplicated', () async {
    final ids = await Future.wait([identity('A'), identity('B'), identity('C')]);
    final nodes = ids.map(FakeLanNode.new).toList();
    final network = {for (final n in nodes) n.identity.id: n};
    for (final n in nodes) {
      n.network = network;
      for (final other in nodes) {
        if (n != other) n.peers[other.identity.id] = peer(other.identity);
      }
    }
    final groups = nodes.map(GroupMessaging.new).toList();
    for (var i = 0; i < groups.length; i++) {
      final index = i;
      groups[i].onInvitation = (_, __, ___) async => true;
      nodes[i].onSignal = (sender, msg) {
        unawaited(groups[index].receive(sender, msg));
      };
    }
    final room = await groups[0].create('Study group',
        [peer(ids[1]), peer(ids[2])]);
    await Future<void>.delayed(const Duration(milliseconds: 100));
    expect(groups[1].rooms[room.id], isNotNull);
    expect(groups[2].rooms[room.id], isNotNull);
    await groups[0].send(room, 'Private group test');
    await Future<void>.delayed(const Duration(milliseconds: 100));
    expect(groups[1].rooms[room.id]!.messages.single.body,
        'Private group test');
    final envelope = nodes[0].sent.last;
    final recipient = groups[1];
    await recipient.receive(peer(ids[0]), envelope);
    expect(recipient.rooms[room.id]!.messages.length, 1);
    await recipient.receive(peer(ids[2]), {
      'type': 'group-chat', 'groupId': room.id,
      'messageId': 'spoof', 'text': 'ignored', 'when': DateTime.now().toIso8601String(),
    });
    // C is an authorized member, so its own message is allowed.
    expect(recipient.rooms[room.id]!.messages.length, 2);
    await recipient.receive(Peer(id: 'outsider', name: 'X', key: 'x',
        host: '127.0.0.1', port: 5, seen: DateTime.now()), {
      'type': 'group-chat', 'groupId': room.id,
      'messageId': 'bad', 'text': 'ignored', 'when': DateTime.now().toIso8601String(),
    });
    expect(recipient.rooms[room.id]!.messages.length, 2);
  });

  test('group-call guard refuses oversubscribed rooms and invalid joins', () async {
    final id = await identity('Host');
    final node = FakeLanNode(id);
    final manager = GroupMessaging(node);
    final room = GroupRoom(id: 'r', name: 'group', ownerId: id.id,
      members: [id.id, 'b', 'c', 'd', 'e']);
    expect(GroupCallMesh.canCall(room), isFalse);
    room.members.removeLast();
    expect(GroupCallMesh.canCall(room), isTrue);
    final mesh = GroupCallMesh(node, manager);
    expect(await mesh.handle(Peer(id:'stranger', name:'x', key:'k',
      host:'127.0.0.1', port:1, seen:DateTime.now()), {
      'type':'group-start','groupId':'unknown','sessionId':'spoof','video':true,
    }), isTrue);
    expect(mesh.active, isFalse);
  });

  test('group media join policy, mute and idempotent leave without capture', () async {
    final identities = await Future.wait([
      identity('Host'), identity('Member B'), identity('Member C'),
    ]);
    final node = FakeLanNode(identities[0]);
    final rooms = GroupMessaging(node);
    final room = GroupRoom(
      id: 'room-media-policy', name: 'Group video',
      ownerId: identities[0].id,
      members: identities.map((id) => id.id).toList(),
    );
    rooms.rooms[room.id] = room;
    final mesh = GroupCallMesh(node, rooms);
    await mesh.start(room, withVideo: true);
    expect(mesh.active, isTrue);
    expect(mesh.participants, 1);
    expect(mesh.localRenderer, isNull); // No camera until a peer joins.
    final sessionId = mesh.sessionId;
    await mesh.handle(peer(identities[1]), {
      'type': 'group-join', 'groupId': room.id,
      'sessionId': sessionId, 'video': false,
    });
    expect(mesh.links, isEmpty); // Video/audio mismatch is not joined.
    await mesh.handle(Peer(
      id: 'uninvited', name: 'Outsider', key: 'dummy',
      host: '127.0.0.1', port: 1234, seen: DateTime.now()), {
      'type': 'group-leave', 'groupId': room.id,
      'sessionId': sessionId,
    });
    expect(mesh.active, isTrue); // A stranger cannot end the room.
    await mesh.setMuted(true);
    expect(mesh.muted, isTrue);
    await mesh.leave();
    await mesh.leave();
    expect(mesh.active, isFalse);
    expect(mesh.muted, isFalse);
    expect(mesh.localRenderer, isNull);
  });

}
