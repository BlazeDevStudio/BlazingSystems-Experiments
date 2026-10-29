import 'dart:convert';
import 'dart:io';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

class _RealSockets extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) =>
      super.createHttpClient(context);
}

Future<Identity> identity(String name) async =>
    Identity(await (await X25519().newKeyPair()).extract(), name);

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('one-way UDP discovery becomes two-sided via authenticated first-contact',
      () => HttpOverrides.runWithHttpOverrides(() async {
        final a = LanNode(await identity('Android A'));
        final b = LanNode(await identity('Android B'));
        await a.start();
        await b.start();
        try {
          final payload = jsonDecode(announcement(
            a.identity.id,
            a.identity.displayName,
            a.identity.publicKeyB64,
            a.listenPort,
          )) as Map<String, dynamic>;
          final pinned = Peer.fromDiscovery(payload, '127.0.0.1')!;
          // B sees A's valid announcement. A never receives B's reverse
          // UDP packet, as on the affected shared emulator virtual Wi-Fi.
          b.peers[a.identity.id] = pinned;
          a.peers.remove(b.identity.id);
          expect(a.peers.containsKey(b.identity.id), isFalse);
          expect(await b.introduceDiscoveredPeer(pinned), isTrue);
          final learned = a.peers[b.identity.id];
          expect(learned, isNotNull);
          expect(learned!.key, b.identity.publicKeyB64);
          expect(learned.name, 'Android B');
          expect(a.isOnline(learned), isTrue);
        } finally {
          await a.dispose();
          await b.dispose();
        }
      }, _RealSockets()));

  test('introduction refuses unknown and modified pinned destinations',
      () => HttpOverrides.runWithHttpOverrides(() async {
        final a = LanNode(await identity('A'));
        final b = LanNode(await identity('B'));
        await a.start();
        await b.start();
        try {
          final peer = Peer(
            id: a.identity.id,
            key: a.identity.publicKeyB64,
            host: '127.0.0.1',
            port: a.listenPort,
            name: 'A',
            seen: DateTime.now(),
          );
          expect(await b.introduceDiscoveredPeer(peer), isFalse,
              reason: 'Do not make unsolicited connections to unknown peers');
          b.peers[peer.id] = peer;
          final portSpoof = Peer(
            id: peer.id, key: peer.key, host: peer.host,
            port: peer.port == 65535 ? 65534 : peer.port + 1,
            name: peer.name, seen: peer.seen,
          );
          expect(await b.introduceDiscoveredPeer(portSpoof), isFalse,
              reason: 'Never probe an unpinned TCP port');
          final hostSpoof = Peer(
            id: peer.id, key: peer.key, host: '127.0.0.2',
            port: peer.port, name: peer.name, seen: peer.seen,
          );
          expect(await b.introduceDiscoveredPeer(hostSpoof), isFalse,
              reason: 'Never probe an unpinned host');
          expect(await b.introduceDiscoveredPeer(peer), isTrue);
        } finally {
          await a.dispose();
          await b.dispose();
        }
      }, _RealSockets()));

  test('newly announced valid peer triggers only bounded first-contact ping', () {
    final source = File('lib/src/node.dart').readAsStringSync();
    final start = source.indexOf('void _handleAnnouncement(Datagram packet)');
    final end = source.indexOf('Future<void> _serve(HttpRequest', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final handler = source.substring(start, end);
    expect(handler, contains('Peer.fromDiscovery(decoded, packet.address.address)'));
    expect(handler, contains('if (old == null && _udp != null)'));
    expect(handler, contains('unawaited(introduceDiscoveredPeer(peer));'));
    expect(source, contains('maxConcurrentPeerIntroductions = 4'));
    expect(source, contains('peers[peer.id]?.port != peer.port'));
    expect(source, contains("utf8.encode(jsonEncode({'kind': 'ping'}))"));
    expect(source, contains('timeout: const Duration(seconds: 3)'));
  });
}
