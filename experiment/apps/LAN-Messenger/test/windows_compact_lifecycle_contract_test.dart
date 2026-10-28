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
    expect(block, contains('_deferredCompactForceOpen'));
    expect(block, contains('intercom?.callId != session'));
    expect(block, contains('intercom?.closing == true'));
    expect(block, contains('await _restoreCompactVideo(forceOpen: forceOpen)'));
    expect(block, isNot(contains('await wm.windowManager.setSkipTaskbar(true)')));
  });
  test('Windows compact call presentation rechecks live session after awaiting toast', () {
    final app = File('lib/main.dart').readAsStringSync();
    expect(app, contains('if (intercom?.callId == id && intercom?.closing != true)'));
  });
  test('Windows compact texture frame completes before native window mutations', () {
    final app = File('lib/main.dart').readAsStringSync();
    final start = app.indexOf('Future<void> _openCompactVideoWindow()');
    final restore = app.indexOf('Future<void> _restoreCompactVideo(', start);
    final end = app.indexOf('Future<void> _expandActiveCall()', restore);
    expect(start, greaterThan(0));
    expect(restore, greaterThan(start));
    expect(end, greaterThan(restore));
    final opening = app.substring(start, restore);
    final restoring = app.substring(restore, end);
    final openFrame = opening.indexOf('await WidgetsBinding.instance.endOfFrame');
    final openNative = opening.indexOf('await wm.windowManager.setMinimumSize(');
    expect(openFrame, greaterThan(0));
    expect(openNative, greaterThan(openFrame));
    final restoreFrame = restoring.indexOf('await WidgetsBinding.instance.endOfFrame');
    final restoreNative = restoring.indexOf('await wm.windowManager.setAlwaysOnTop(false)');
    expect(restoreFrame, greaterThan(0));
    expect(restoreNative, greaterThan(restoreFrame));
    expect(opening, contains('intercom?.callId != session'));
    expect(opening, contains('intercom?.closing == true'));
    expect(restoring, contains('if (!mounted) return'));
    expect(opening, contains('const Duration(seconds: 3)'));
    expect(restoring, contains('const Duration(seconds: 3)'));
  });

}
