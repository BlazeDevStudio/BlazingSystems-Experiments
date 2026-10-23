import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/protocol.dart';

void main() {
  attachmentHistoryTests();
  test('file names never escape receive directory', () {
    expect(safeFileName('../../boot.ini'), 'boot.ini');
    expect(safeFileName(r'..\..\Users\file.txt'), 'file.txt');
    expect(safeFileName(''), 'received-file');
    expect(safeFileName('a<b>.jpg'), 'a_b_.jpg');
  });
  test('reject malformed or forged discovery records', () {
    final key = base64Encode(List<int>.filled(32, 1));
    final bad = jsonDecode(announcement(''.padRight(64, '0'), 'Stranger', key, 9999))
        as Map<String, dynamic>;
    expect(Peer.fromDiscovery(bad, '192.168.1.10'), isNull);
    bad['id'] = fingerprint(List<int>.filled(32, 1));
    expect(Peer.fromDiscovery(bad, '192.168.1.10'), isNotNull);
    bad['port'] = 65536;
    expect(Peer.fromDiscovery(bad, '192.168.1.10'), isNull);
  });
}

// The attachment metadata must survive app restart: the same thread shows
// photos and files, not a separate transfer-only screen.
void attachmentHistoryTests() {
  test('file messages retain attachment references in conversation history', () {
    final now = DateTime.utc(2026, 10, 23);
    final message = ChatMessage(id: 'file-id', peerId: 'peer-id',
      text: 'holiday-photo.jpg', outgoing: false, time: now,
      kind: 'file', filePath: '/downloads/holiday-photo.jpg', fileSize: 1024);
    final copy = ChatMessage.fromJson(jsonDecode(jsonEncode(message.toJson())));
    expect(copy, isNotNull);
    expect(copy!.kind, 'file');
    expect(copy.peerId, 'peer-id');
    expect(copy.text, 'holiday-photo.jpg');
    expect(copy.filePath, '/downloads/holiday-photo.jpg');
    expect(copy.fileSize, 1024);
    expect(copy.time, now);
  });
}