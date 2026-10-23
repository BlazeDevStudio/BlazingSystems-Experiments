import 'dart:convert';
import 'dart:math';
import 'package:crypto/crypto.dart' as digest;

const int discoveryPort = 39823;
const String multicastIp = '239.42.61.77';
const int chunkSize = 65536;
const int protocolVersion = 1;

String randomId() {
  final bytes = List<int>.generate(16, (_) => Random.secure().nextInt(256));
  return bytes.map((n) => n.toRadixString(16).padLeft(2, '0')).join();
}

String fingerprint(List<int> publicKey) =>
    digest.sha256.convert(publicKey).toString();

String safeFileName(String input) {
  final last = input.replaceAll('\\', '/').split('/').last;
  var cleaned = last.replaceAll(RegExp(r'[<>:"/\\|?*\x00-\x1f]'), '_').trim();
  cleaned = cleaned.replaceAll(RegExp(r'[. ]+$'), '');
  if (RegExp(r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$', caseSensitive: false).hasMatch(cleaned)) {
    cleaned = '_$cleaned';
  }
  if (cleaned.isEmpty || cleaned == '.' || cleaned == '..') return 'received-file';
  return cleaned.length > 180 ? cleaned.substring(cleaned.length - 180) : cleaned;
}

class Peer {
  final String id;
  final String name;
  final String key;
  final String host;
  final int port;
  final DateTime seen;

  const Peer({required this.id, required this.name, required this.key,
    required this.host, required this.port, required this.seen});

  String get shortCode => id.substring(0, min(8, id.length)).toUpperCase();
  Uri uri(String path) => Uri(scheme: 'http', host: host, port: port, path: path);

  Map<String, dynamic> toJson() => {
    'id': id, 'name': name, 'key': key, 'host': host, 'port': port,
  };

  static Peer? fromDiscovery(Map<String, dynamic> json, String host) {
    if (json['v'] != protocolVersion) return null;
    final id = json['id'];
    final name = json['name'];
    final key = json['key'];
    final port = json['port'];
    if (id is! String || !RegExp(r'^[a-f0-9]{64}$').hasMatch(id)) return null;
    if (name is! String || name.trim().isEmpty || name.length > 80) return null;
    if (key is! String || port is! int || port < 1 || port > 65535) return null;
    try {
      final publicKey = base64Decode(key);
      if (publicKey.length != 32 || fingerprint(publicKey) != id) return null;
    } catch (_) { return null; }
    return Peer(id: id, name: name, key: key, host: host,
      port: port, seen: DateTime.now());
  }
}

class ChatMessage {
  final String id;
  final String peerId;
  final String text;
  final bool outgoing;
  final DateTime time;
  final String kind;
  final String? filePath;
  final int? fileSize;
  ChatMessage({required this.id, required this.peerId, required this.text,
      required this.outgoing, required this.time, this.kind = 'text',
      this.filePath, this.fileSize});

  Map<String, dynamic> toJson() => {
    'id': id, 'peer': peerId, 'text': text,
    'outgoing': outgoing, 'time': time.toIso8601String(), 'kind': kind,
    if (filePath != null) 'filePath': filePath,
    if (fileSize != null) 'fileSize': fileSize,
  };

  static ChatMessage? fromJson(dynamic value) {
    if (value is! Map<String, dynamic>) return null;
    try {
      return ChatMessage(id: value['id'] as String, peerId: value['peer'] as String,
        text: value['text'] as String, outgoing: value['outgoing'] as bool,
        time: DateTime.parse(value['time'] as String),
        kind: value['kind'] as String? ?? 'text',
        filePath: value['filePath'] as String?,
        fileSize: value['fileSize'] is int ? value['fileSize'] as int : null);
    } catch (_) { return null; }
  }
}

String announcement(String id, String name, String publicKey, int port) => jsonEncode({
  'app': 'lan-messenger', 'v': protocolVersion,
  'id': id, 'name': name, 'key': publicKey, 'port': port,
});