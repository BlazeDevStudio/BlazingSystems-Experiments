import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/inline_preview.dart';

void main() {
  test('inline TXT preview truncates safely and never invokes external programs', () async {
    final dir = await Directory.systemTemp.createTemp('lan-preview');
    try {
      final f = File('${dir.path}/example.txt');
      await f.writeAsString('Hello from LAN Messenger');
      expect(await previewDocument(f, 'txt'), contains('Hello from LAN Messenger'));
    } finally { await dir.delete(recursive: true); }
  });
}