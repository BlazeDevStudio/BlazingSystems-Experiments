import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Windows compact viewer serializes opening and deferred restoration', () {
    final app = File('lib/main.dart').readAsStringSync();
    final start = app.indexOf('Future<void> _openCompactVideoWindow()');
    final end = app.indexOf('Future<void> _expandActiveCall()', start);
    expect(start, greaterThan(0));
    expect(end, greaterThan(start));
    final block = app.substring(start, end);
    expect(block, contains('_openingCompactWindow'));
    expect(block, contains('_deferredCompactRestore'));
    expect(block, contains('intercom?.callId != session'));
    expect(block, contains('intercom?.closing == true'));
    expect(block, contains('await _restoreCompactVideo()'));
    expect(block, isNot(contains('await wm.windowManager.setSkipTaskbar(true)')));
  });
  test('Windows compact call presentation rechecks live session after awaiting toast', () {
    final app = File('lib/main.dart').readAsStringSync();
    expect(app, contains('if (intercom?.callId == id && intercom?.closing != true)'));
  });
}
