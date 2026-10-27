import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

class _LoopbackHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) =>
      super.createHttpClient(context);
}

Future<void> _exerciseLostAck({required bool finalChunk}) async {
  final directory = await Directory.systemTemp.createTemp('lan-ack-resume-');
  final alice = LanNode(Identity(
      await (await X25519().newKeyPair()).extract(), 'Sender'));
  final bob = LanNode(Identity(
      await (await X25519().newKeyPair()).extract(), 'Receiver'),
      storageDirectory: directory);
  HttpServer? proxy;
  try {
    await alice.start();
    await bob.start();
    final original = Uint8List.fromList(
        List<int>.generate(chunkSize * 3, (i) => i % 251));
    final source = File('${directory.path}/source.bin');
    await source.writeAsBytes(original);
    bob.peers[alice.identity.id] = Peer(
        id: alice.identity.id, key: alice.identity.publicKeyB64,
        name: 'Sender', host: '127.0.0.1', port: alice.listenPort,
        seen: DateTime.now());

    proxy = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    var chunkNumber = 0;
    var lostAcknowledgements = 0;
    final receiver = bob;
    proxy.listen((request) async {
      final client = HttpClient();
      try {
        final data = await utf8.decoder.bind(request).join();
        final upstream = await client.postUrl(Uri(
            scheme: 'http', host: '127.0.0.1', port: receiver.listenPort,
            path: request.uri.path));
        upstream.headers.contentType = ContentType.json;
        upstream.write(data);
        final response = await upstream.close();
        final body = await utf8.decoder.bind(response).join();
        if (request.uri.path == '/v1/chunk') {
          chunkNumber++;
          if (lostAcknowledgements == 0 &&
              (finalChunk ? chunkNumber == 3 : chunkNumber == 1)) {
            // The authenticated receiver has finished processing/committing
            // this chunk, but the sender gets an empty HTTP response.
            // It must query file-status.next rather than blindly append.
            lostAcknowledgements++;
            await request.response.close();
            return;
          }
        }
        request.response.statusCode = response.statusCode;
        request.response.headers.contentType = ContentType.json;
        request.response.write(body);
        await request.response.close();
      } catch (e) {
        request.response.statusCode = HttpStatus.badGateway;
        await request.response.close();
      } finally {
        client.close(force: true);
      }
    });
    final interceptedBob = Peer(
        id: bob.identity.id, key: bob.identity.publicKeyB64,
        name: 'Receiver', host: '127.0.0.1', port: proxy.port,
        seen: DateTime.now());
    await alice.sendFile(interceptedBob, source);
    final files = await bob.receivedFiles();
    expect(files.length, 1);
    expect(await files.single.readAsBytes(), original);
    expect(lostAcknowledgements, 1);
    // For the first-chunk ACK loss, the receiver processes exactly 3 sends;
    // the receiver's receipt makes the final-chunk lost ACK recoverable too.
    expect(chunkNumber, 3);
  } finally {
    await proxy?.close(force: true);
    await alice.dispose();
    await bob.dispose();
    await directory.delete(recursive: true);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('routed ingress advertises its real TCP port if preferred port is occupied',
      () => HttpOverrides.runWithHttpOverrides(() async {
        final identity1 = Identity(
            await (await X25519().newKeyPair()).extract(), 'Ingress A');
        final identity2 = Identity(
            await (await X25519().newKeyPair()).extract(), 'Ingress B');
        final first = LanNode(identity1);
        final second = LanNode(identity2);
        try {
          await first.start();
          await second.start();
          expect(LanNode.preferredListenPort, 39824);
          expect(first.listenPort, greaterThan(0));
          expect(second.listenPort, greaterThan(0));
          expect(second.listenPort, isNot(first.listenPort));
          expect(first.usingPreferredListenPort,
              first.listenPort == LanNode.preferredListenPort);
          expect(second.usingPreferredListenPort,
              second.listenPort == LanNode.preferredListenPort);
          // Both servers must report the actual bound port, not assume a
          // fixed route if another local application already owns it.
        } finally {
          await first.dispose();
          await second.dispose();
        }
      }, _LoopbackHttpOverrides()));

  test('resume large file after lost first-chunk acknowledgement', () =>
      HttpOverrides.runWithHttpOverrides(
          () => _exerciseLostAck(finalChunk: false),
          _LoopbackHttpOverrides()));
  test('do not duplicate file after lost final-chunk acknowledgement', () =>
      HttpOverrides.runWithHttpOverrides(
          () => _exerciseLostAck(finalChunk: true),
          _LoopbackHttpOverrides()));
}
