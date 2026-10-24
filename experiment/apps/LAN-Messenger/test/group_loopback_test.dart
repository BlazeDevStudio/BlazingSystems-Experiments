import 'dart:io';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/group_rooms.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

Future<Identity> newIdentity(String name) async {
  final data = await (await X25519().newKeyPair()).extract();
  return Identity(data, name);
}

Future<void> eventually(bool Function() ready) async {
  for (var i = 0; i < 100; i++) {
    if (ready()) return;
    await Future<void>.delayed(const Duration(milliseconds: 30));
  }
  fail('Timed out waiting for authenticated LAN peer event');
}

void main() {
  test('three independent localhost nodes exchange authenticated group texts',
      () async {
    final base = await Directory.systemTemp.createTemp('lan-group-test-');
    final nodes = <LanNode>[];
    try {
      for (final name in ['Windows', 'Android-A', 'Android-B']) {
        final dir = Directory('${base.path}/$name')..createSync(recursive: true);
        final node = LanNode(await newIdentity(name), storageDirectory: dir);
        nodes.add(node);
        await node.start();
      }
      for (final a in nodes) {
        for (final b in nodes) {
          if (identical(a, b)) continue;
          a.peers[b.identity.id] = Peer(
            id: b.identity.id, name: b.identity.displayName,
            key: b.identity.publicKeyB64, host: '127.0.0.1',
            port: b.listenPort, seen: DateTime.now());
        }
      }
      final groups = [for (final n in nodes) GroupCoordinator(n)];
      for (var i = 0; i < nodes.length; i++) {
        final group = groups[i];
        nodes[i].onSignal = (peer, data) {
          group.incoming(peer, data);
        };
      }
      final owner = nodes.first;
      final room = await groups.first.create('Technicians', [
        owner.peers[nodes[1].identity.id]!,
        owner.peers[nodes[2].identity.id]!,
      ]);
      await eventually(() => groups[1].rooms.containsKey(room.id) &&
          groups[2].rooms.containsKey(room.id));
      await groups[1].sendText(groups[1].rooms[room.id]!, 'Message from Android');
      await eventually(() => groups[0].rooms[room.id]!.messages.any(
          (m) => m.text == 'Message from Android') &&
          groups[2].rooms[room.id]!.messages.any(
          (m) => m.text == 'Message from Android'));
      expect(groups.first.rooms[room.id]!.messages.where(
          (m) => m.text == 'Message from Android').length, 1);
      expect(groups.last.rooms[room.id]!.members.length, 3);
      // Source peer IDs are authenticated by pairwise X25519/AES-GCM.
      final forged = GroupText('forged', 'd' * 64, 'fake', DateTime.now());
      expect(groups.last.rooms[room.id]!.addMessage(forged), isFalse);
    } finally {
      for (final node in nodes) {
        await node.dispose();
      }
      await base.delete(recursive: true);
    }
  }, timeout: const Timeout(Duration(seconds: 25)));
}
