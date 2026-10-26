import 'dart:convert';
import 'dart:io';
import 'package:cryptography/cryptography.dart';
import 'package:path_provider/path_provider.dart';
import 'protocol.dart';
import 'recoverable_json_file.dart';

class Identity {
  final SimpleKeyPairData keyPair;
  String displayName;
  final String id;
  final String publicKeyB64;
  Identity(this.keyPair, this.displayName)
      : id = fingerprint(keyPair.publicKey.bytes),
        publicKeyB64 = base64Encode(keyPair.publicKey.bytes);

  static Future<Directory> appDirectory() async {
    final base = await getApplicationSupportDirectory();
    final dir = Directory('${base.path}${Platform.pathSeparator}LAN Messenger');
    await dir.create(recursive: true);
    return dir;
  }

  static Future<Identity> load() async {
    final dir = await appDirectory();
    final file = File('${dir.path}${Platform.pathSeparator}identity.json');
    if (await RecoverableJsonFile.hasSavedState(file)) {
      // A corrupt or interrupted rename must never silently regenerate a
      // device identity: existing peers would lose their pinned trust.
      final obj = await RecoverableJsonFile.read(file, isValid: (value) {
        if (value is! Map<String, dynamic> ||
            value['private'] is! String || value['public'] is! String ||
            value['name'] is! String) return false;
        try {
          return base64Decode(value['private'] as String).length == 32 &&
              base64Decode(value['public'] as String).length == 32 &&
              (value['name'] as String).isNotEmpty;
        } catch (_) { return false; }
      }) as Map<String, dynamic>;
      final keyPair = SimpleKeyPairData(
        base64Decode(obj['private'] as String),
        publicKey: SimplePublicKey(base64Decode(obj['public'] as String),
          type: KeyPairType.x25519), type: KeyPairType.x25519);
      return Identity(keyPair, obj['name'] as String);
    }
    final newPair = (await X25519().newKeyPair()).extract();
    final keyPair = await newPair;
    final id = fingerprint(keyPair.publicKey.bytes);
    // Prefer a recognizable machine name without asking the user to configure it.
    final hostname = Platform.localHostname.trim();
    final name = hostname.isNotEmpty && hostname.toLowerCase() != 'localhost'
        ? hostname.substring(0, hostname.length > 40 ? 40 : hostname.length)
        : 'Device ${id.substring(0, 4).toUpperCase()}';
    await RecoverableJsonFile.write(file, {
      'private': base64Encode(keyPair.bytes),
      'public': base64Encode(keyPair.publicKey.bytes), 'name': name,
    });
    return Identity(keyPair, name);
  }

  Future<void> rename(String value) async {
    final newName = value.trim();
    if (newName.isEmpty || newName.length > 40) {
      throw ArgumentError('Device name must contain 1–40 characters');
    }
    final dir = await appDirectory();
    final file = File('${dir.path}${Platform.pathSeparator}identity.json');
    // Preserve our long-lived identity so conversations do not break on rename.
    await RecoverableJsonFile.write(file, {
      'private': base64Encode(keyPair.bytes),
      'public': base64Encode(keyPair.publicKey.bytes),
      'name': newName,
    });
    displayName = newName;
  }
}


class PeerCipher {
  final Identity identity;
  final AesGcm _cipher = AesGcm.with256bits();
  PeerCipher(this.identity);

  Future<SecretKey> _derive(String remotePublicKey) async {
    final remoteBytes = base64Decode(remotePublicKey);
    if (remoteBytes.length != 32) throw const FormatException('Bad public key');
    final shared = await X25519().sharedSecretKey(
      keyPair: identity.keyPair,
      remotePublicKey: SimplePublicKey(remoteBytes, type: KeyPairType.x25519));
    final ordered = [identity.id, fingerprint(remoteBytes)]..sort();
    return Hkdf(hmac: Hmac.sha256(), outputLength: 32).deriveKey(
      secretKey: shared, nonce: utf8.encode('LAN Messenger v1'),
      info: utf8.encode(ordered.join(':')));
  }

  Future<Map<String, dynamic>> seal(String remoteKey, List<int> plain) async {
    final box = await _cipher.encrypt(plain, secretKey: await _derive(remoteKey));
    return {'from': identity.publicKeyB64, 'nonce': base64Encode(box.nonce),
      'data': base64Encode(box.cipherText), 'mac': base64Encode(box.mac.bytes)};
  }

  Future<List<int>> open(Map<String, dynamic> envelope) async {
    final remoteKey = envelope['from'] as String;
    final box = SecretBox(base64Decode(envelope['data'] as String),
      nonce: base64Decode(envelope['nonce'] as String),
      mac: Mac(base64Decode(envelope['mac'] as String)));
    return _cipher.decrypt(box, secretKey: await _derive(remoteKey));
  }

  static String senderId(Map<String, dynamic> envelope) =>
      fingerprint(base64Decode(envelope['from'] as String));
}