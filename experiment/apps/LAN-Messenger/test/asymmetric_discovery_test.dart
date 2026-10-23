import 'dart:convert';
import 'dart:io';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('encrypted first-contact message works with one-way peer discovery', () async {
    final a = LanNode(Identity(await (await X25519().newKeyPair()).extract(), 'Android'));
    final b = LanNode(Identity(await (await X25519().newKeyPair()).extract(), 'PC-03'));
    await a.start();
    await b.start();
    try {
      final data = jsonDecode(announcement(b.identity.id, b.identity.displayName,
          b.identity.publicKeyB64, b.listenPort)) as Map<String, dynamic>;
      a.peers[b.identity.id] = Peer.fromDiscovery(data, '127.0.0.1')!;
      // Simulate asymmetric Wi-Fi multicast: PC did not hear Android.
      b.peers.remove(a.identity.id);
      String? message;
      b.onChat = (_, m) => message = m.text;
      await a.sendMessage(a.peers[b.identity.id]!, 'Hi from phone');
      expect(message, 'Hi from phone');
      expect(b.peers[a.identity.id]?.name, 'Android');
      expect(b.isOnline(b.peers[a.identity.id]!), isTrue);
    } finally {
      await a.dispose();
      await b.dispose();
    }
  });
}