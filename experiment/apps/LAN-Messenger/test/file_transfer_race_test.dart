import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:crypto/crypto.dart' as crypto;
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/foundation.dart';
import 'package:lan_messenger/src/identity.dart';
import 'package:lan_messenger/src/node.dart';
import 'package:lan_messenger/src/protocol.dart';

Future<Identity> newPeerIdentity(String name) async {
  final pair = await X25519().newKeyPair();
  return Identity(await pair.extract(), name);
}

/// Send a real authenticated/encrypted LAN HTTP request, not a mock of the
/// file-receiver implementation under test.
Future<Map<String, dynamic>> postEncrypted(
    LanNode from, LanNode to, String route, Map<String, dynamic> event) async {
  final packet = await from.cipher.seal(
      to.identity.publicKeyB64, utf8.encode(jsonEncode(event)));
  packet['replyPort'] = from.listenPort;
  packet['replyName'] = from.identity.displayName;
  final client = HttpClient()..connectionTimeout = const Duration(seconds: 5);
  try {
    final request = await client
        .postUrl(Uri(scheme: 'http', host: '127.0.0.1',
            port: to.listenPort, path: route))
        .timeout(const Duration(seconds: 8));
    request.headers.contentType = ContentType.json;
    request.add(utf8.encode(jsonEncode(packet)));
    final response = await request.close().timeout(const Duration(seconds: 12));
    final raw = await utf8.decoder.bind(response).join()
        .timeout(const Duration(seconds: 12));
    expect(response.statusCode, HttpStatus.ok);
    final opened = await from.cipher.open(
        jsonDecode(raw) as Map<String, dynamic>);
    return jsonDecode(utf8.decode(opened)) as Map<String, dynamic>;
  } finally {
    client.close(force: true);
  }
}

class _LoopbackHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) =>
      super.createHttpClient(context);
}

Future<void> withLanNodes(
    Future<void> Function(LanNode sender, LanNode receiver, Directory dir)
        testBody) => HttpOverrides.runWithHttpOverrides(
            () => _withLanNodes(testBody), _LoopbackHttpOverrides());

Future<void> _withLanNodes(
    Future<void> Function(LanNode sender, LanNode receiver, Directory dir)
        testBody) async {
  final dir = await Directory.systemTemp.createTemp('lan-file-race-');
  final alice = LanNode(await newPeerIdentity('sender'), storageDirectory: dir);
  final bob = LanNode(await newPeerIdentity('receiver'), storageDirectory: dir);
  try {
    await alice.start();
    await bob.start();
    await testBody(alice, bob, dir);
  } finally {
    await alice.dispose();
    await bob.dispose();
    await dir.delete(recursive: true);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('duplicate authenticated chunk requests do not append twice',
      () => withLanNodes((sender, receiver, dir) async {
    final original = Uint8List.fromList(
        List<int>.generate(chunkSize * 2, (i) => i % 251));
    final id = randomId();
    final offer = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'file-offer', 'id': id, 'name': 'probe.bin',
      'size': original.length,
      'sha256': crypto.sha256.convert(original).toString(),
    });
    expect(offer['ok'], isTrue);

    Map<String, dynamic> chunk(int index) => {
      'id': id, 'index': index, 'bytes': base64Encode(original.sublist(
          index * chunkSize, (index + 1) * chunkSize)),
    };
    final duplicate = await Future.wait([
      postEncrypted(sender, receiver, '/v1/chunk', chunk(0)),
      postEncrypted(sender, receiver, '/v1/chunk', chunk(0)),
    ]);
    expect(duplicate.every((r) => r['ok'] == true), isTrue);
    final finalChunk = await postEncrypted(sender, receiver, '/v1/chunk', chunk(1));
    expect(finalChunk['ok'], isTrue);
    final files = await receiver.receivedFiles();
    expect(files.length, 1);
    expect(await files.single.readAsBytes(), original);
  }));

  test('concurrent same-ID file offers reserve before permission is resolved',
      () => withLanNodes((sender, receiver, dir) async {
    final entered = Completer<void>();
    final allow = Completer<bool>();
    var prompts = 0;
    receiver.autoReceiveFiles = false;
    receiver.onFileOffer = (_, __, ___) async {
      prompts++;
      if (!entered.isCompleted) entered.complete();
      return allow.future;
    };
    final id = randomId();
    final offer = {
      'kind': 'file-offer', 'id': id, 'name': 'same-name.bin',
      'size': 16,
      'sha256': crypto.sha256.convert(List<int>.filled(16, 1)).toString(),
    };
    final first = postEncrypted(sender, receiver, '/v1/event', offer);
    await entered.future.timeout(const Duration(seconds: 10));
    final repeat = await postEncrypted(sender, receiver, '/v1/event', offer);
    expect(repeat['ok'], isFalse);
    expect(repeat['reason'], 'pending');
    expect(prompts, 1);
    allow.complete(true);
    expect((await first)['ok'], isTrue);
    expect(prompts, 1);
  }));
  test('active offer rejects same transfer ID with different file identity',
      () => withLanNodes((sender, receiver, dir) async {
    final id = randomId();
    final initial = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'file-offer', 'id': id, 'name': 'genuine.bin',
      'size': 4,
      'sha256': crypto.sha256.convert([1, 2, 3, 4]).toString(),
    });
    expect(initial['ok'], true);
    final conflict = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'file-offer', 'id': id, 'name': 'replacement.bin',
      'size': 4,
      'sha256': crypto.sha256.convert([9, 8, 7, 6]).toString(),
    });
    expect(conflict['ok'], false);
    expect(conflict['reason'], 'conflicting transfer identity');
    final valid = await postEncrypted(sender, receiver, '/v1/chunk', {
      'id': id, 'index': 0, 'bytes': base64Encode([1, 2, 3, 4]),
    });
    expect(valid['ok'], true);
    expect((await receiver.receivedFiles()).length, 1);
  }));

  test('two simultaneous same-name transfers retain both contents',
      () => withLanNodes((sender, receiver, dir) async {
    final ids = [randomId(), randomId()];
    final contents = [List<int>.filled(19, 41), List<int>.filled(19, 87)];
    final offers = await Future.wait(List.generate(2, (i) => postEncrypted(
        sender, receiver, '/v1/event', {
          'kind': 'file-offer', 'id': ids[i], 'name': 'same-name.bin',
          'size': contents[i].length,
          'sha256': crypto.sha256.convert(contents[i]).toString(),
        })));
    expect(offers.every((r) => r['ok'] == true), true);
    final results = await Future.wait(List.generate(2, (i) => postEncrypted(
        sender, receiver, '/v1/chunk', {
          'id': ids[i], 'index': 0,
          'bytes': base64Encode(contents[i]),
        })));
    expect(results.every((r) => r['ok'] == true), true);
    final received = await receiver.receivedFiles();
    expect(received.length, 2);
    final data = await Future.wait(received.map((f) => f.readAsBytes()));
    expect(data.any((v) => listEquals(v, contents[0])), true);
    expect(data.any((v) => listEquals(v, contents[1])), true);
  }));

  test('session-specific probe refuses an absent call and wrong call ID',
      () => withLanNodes((sender, receiver, dir) async {
    receiver.onCallProbe = (peer, id) =>
        peer.id == sender.identity.id && id == 'valid-call-session';
    final bad = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'call-probe', 'callId': 'wrong-session',
    });
    expect(bad['ok'], true);
    expect(bad['active'], false);
    final good = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'call-probe', 'callId': 'valid-call-session',
    });
    expect(good['active'], true);
    receiver.onCallProbe = null; // Simulate ending the matching call.
    final ended = await postEncrypted(sender, receiver, '/v1/event', {
      'kind': 'call-probe', 'callId': 'valid-call-session',
    });
    expect(ended['active'], false);
  }));

}
