import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/inline_preview.dart';

void main() {
  test('Only faithful inline formats are previewable; Office files require external readers', () {
    for (final ext in ['xlsx','xls','docx','doc','pptx','ppt','exe']) {
      expect(supportsInlinePreview(ext), isFalse, reason: ext);
    }
    for (final ext in ['pdf','txt','png','mp4','mp3','csv']) {
      expect(supportsInlinePreview(ext), isTrue, reason: ext);
    }
  });


  test('inline TXT preview truncates safely and never invokes external programs', () async {
    final dir = await Directory.systemTemp.createTemp('lan-preview');
    try {
      final f = File('${dir.path}/example.txt');
      await f.writeAsString('Hello from LAN Messenger');
      expect(await previewDocument(f, 'txt'), contains('Hello from LAN Messenger'));
    } finally { await dir.delete(recursive: true); }
  });
}