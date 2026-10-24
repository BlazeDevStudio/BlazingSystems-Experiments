import 'dart:async';
import 'dart:io';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/groups.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

Future<Identity> newIdentity(String label) async {
  final pair = await (await X25519().newKeyPair()).extract();
  return Identity(pair, label);
}

Future<void> eventually(bool Function() condition) async {
  for (var i = 0; i < 150; i++) {
    if (condition()) return;
    await Future<void>.delayed(const Duration(milliseconds: 25));
  }
  fail('Three-peer encrypted group transport did not deliver in time');
}

void main() {
  test('real three-node localhost group messages use authenticated encrypted HTTP',
      () async {
    final temp = await Directory.systemTemp.createTemp('lan_group_e2e_');
    final nodes = <LanNode>[];
    try {
      for (final label in ['Host', 'Android One', 'Android Two']) {
        final folder = await Directory('${temp.path}/${nodes.length}').create();
        final n = LanNode(await newIdentity(label), storageDirectory: folder);
        nodes.add(n);
        await n.start();
      }
      // Real TCP sockets bound by LanNode.start() on distinct ports; no fake
      // transport, no raw unencrypted calls, no external internet services.
      for (final n in nodes) {
        for (final other in nodes) {
          if (identical(n, other)) continue;
          n.peers[other.identity.id] = Peer(
            id: other.identity.id, name: other.identity.displayName,
            key: other.identity.publicKeyB64, host: '127.0.0.1',
            port: other.listenPort, seen: DateTime.now());
        }
      }
      final coordinators = nodes.map(GroupMessaging.new).toList();
      for (var i = 0; i < nodes.length; i++) {
        final coordinator = coordinators[i];
        coordinator.onInvitation = (_, __, ___) async => true;
        nodes[i].onSignal = (sender, message) =>
            unawaited(coordinator.receive(sender, message));
      }
      final room = await coordinators.first.create('LAN test team', [
        nodes[0].peers[nodes[1].identity.id]!,
        nodes[0].peers[nodes[2].identity.id]!,
      ]);
      await eventually(() =>
          coordinators[1].rooms.containsKey(room.id) &&
          coordinators[2].rooms.containsKey(room.id));
      await coordinators[1].send(coordinators[1].rooms[room.id]!, 'Hello over LAN');
      await eventually(() =>
          coordinators[0].rooms[room.id]!.messages.any(
              (m) => m.body == 'Hello over LAN') &&
          coordinators[2].rooms[room.id]!.messages.any(
              (m) => m.body == 'Hello over LAN'));
      // Replayed content must not add another group message.
      final author = nodes[0].peers[nodes[1].identity.id]!;
      final message = coordinators[0].rooms[room.id]!.messages.single;
      await coordinators[0].receive(author, {
        'type': 'group-chat', 'groupId': room.id,
        'messageId': message.id, 'text': message.body,
        'when': message.when.toIso8601String(),
      });
      expect(coordinators[0].rooms[room.id]!.messages.length, 1);
      expect(coordinators[2].rooms[room.id]!.messages.single.body, 'Hello over LAN');
    } finally {
      for (final n in nodes) { await n.dispose(); }
      await temp.delete(recursive: true);
    }
  }, timeout: const Timeout(Duration(seconds: 28)));
}
