import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

Peer localPeer(Identity identity, int port, {bool stale = false}) {
  final payload = jsonDecode(announcement(identity.id, identity.displayName,
    identity.publicKeyB64, port)) as Map<String, dynamic>;
  final current = Peer.fromDiscovery(payload, '127.0.0.1')!;
  if (!stale) return current;
  return Peer(id: current.id, name: current.name, key: current.key,
      host: current.host, port: current.port,
      seen: DateTime.now().subtract(const Duration(minutes: 2)));
}

class _LoopbackHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) =>
      super.createHttpClient(context);
}

Future<void> realSockets(Future<void> Function() testBody) =>
    HttpOverrides.runWithHttpOverrides(testBody, _LoopbackHttpOverrides());

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('authenticated text and keepalive work after discovery goes stale', () => realSockets(() async {
    final alice = LanNode(Identity(
        await (await X25519().newKeyPair()).extract(), 'Android'));
    final bob = LanNode(Identity(
        await (await X25519().newKeyPair()).extract(), 'PC-03'));
    await alice.start();
    await bob.start();
    try {
      final peerBob = localPeer(bob.identity, bob.listenPort, stale: true);
      final peerAlice = localPeer(alice.identity, alice.listenPort, stale: true);
      alice.peers[bob.identity.id] = peerBob;
      bob.peers[alice.identity.id] = peerAlice;
      expect(alice.isOnline(peerBob), isFalse);
      ChatMessage? received;
      bob.onChat = (_, message) => received = message;
      await alice.sendMessage(peerBob, 'hello after 2 minutes');
      expect(received?.text, 'hello after 2 minutes');
      // A successful authenticated request also restores presence.
      expect(alice.isOnline(peerBob), isTrue);
      expect(bob.isOnline(peerAlice), isTrue);
      expect(bob.peers[alice.identity.id], isNotNull);
    } finally {
      await alice.dispose();
      await bob.dispose();
    }
  }));

  test('file arrives automatically with matching content after stale discovery', () => realSockets(() async {
    final folder = await Directory.systemTemp.createTemp('lan-messenger-tests-');
    final alice = LanNode(Identity(
        await (await X25519().newKeyPair()).extract(), 'Phone'), storageDirectory: folder);
    final bob = LanNode(Identity(
        await (await X25519().newKeyPair()).extract(), 'Windows'), storageDirectory: folder);
    await alice.start();
    await bob.start();
    try {
      final peerBob = localPeer(bob.identity, bob.listenPort, stale: true);
      final peerAlice = localPeer(alice.identity, alice.listenPort, stale: true);
      alice.peers[bob.identity.id] = peerBob;
      bob.peers[alice.identity.id] = peerAlice;
      // No file-offer callback: receiver never prompts. This MUST still work.
      expect(bob.autoReceiveFiles, isTrue);
      final original = Uint8List.fromList(List<int>.generate(138777, (i) => i % 251));
      final input = File('${folder.path}/preview-picture.png');
      await input.writeAsBytes(original);
      ChatMessage? received;
      bob.onChat = (_, message) => received = message;
      await alice.sendFile(peerBob, input);
      expect(received?.kind, 'file');
      expect(received?.outgoing, isFalse);
      expect(await File(received!.filePath!).readAsBytes(), original);
    } finally {
      await alice.dispose();
      await bob.dispose();
      await folder.delete(recursive: true);
    }
  }));
}