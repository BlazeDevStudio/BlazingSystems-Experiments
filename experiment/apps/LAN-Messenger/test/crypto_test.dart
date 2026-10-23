import 'dart:convert';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/identity.dart';

void main() {
  test('peer envelope decrypts cross-device and rejects modification', () async {
    final a = Identity(await (await X25519().newKeyPair()).extract(), 'A');
    final b = Identity(await (await X25519().newKeyPair()).extract(), 'B');
    final alice = PeerCipher(a);
    final bob = PeerCipher(b);
    final envelope = await alice.seal(b.publicKeyB64, utf8.encode('hello offline'));
    final plain = await bob.open(envelope);
    expect(utf8.decode(plain), 'hello offline');
    final corrupt = Map<String, dynamic>.from(envelope);
    corrupt['data'] = base64Encode(List<int>.filled(13, 255));
    expect(() => bob.open(corrupt), throwsA(isA<SecretBoxAuthenticationError>()));
  });
}