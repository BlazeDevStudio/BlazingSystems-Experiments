import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

void main() {
  test('stale peer remains authenticated while UI shows offline', () async {
    final id = Identity(await (await X25519().newKeyPair()).extract(), 'Local');
    final node = LanNode(id);
    final remote = Identity(await (await X25519().newKeyPair()).extract(), 'Remote');
    final sample = jsonDecode(announcement(remote.id, 'PC-03',
        remote.publicKeyB64, 50000)) as Map<String, dynamic>;
    final peer = Peer.fromDiscovery(sample, '127.0.0.1')!;
    final oldPeer = Peer(id: peer.id, key: peer.key, name: peer.name,
      host: peer.host, port: peer.port,
      seen: DateTime.now().subtract(const Duration(minutes: 2)));
    node.peers[oldPeer.id] = oldPeer;
    expect(node.isOnline(oldPeer), isFalse);
    expect(node.peers[oldPeer.id]?.key, remote.publicKeyB64);
  });
}