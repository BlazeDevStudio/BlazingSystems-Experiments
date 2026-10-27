import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Windows call popup Open restores a live call, not its chat thread', () {
    final source = File('lib/main.dart').readAsStringSync();
    final begin = source.indexOf('Future<dynamic> _handleDesktopCallAction(');
    final end = source.indexOf('void _resolveIncomingDialog(', begin);
    expect(begin, greaterThanOrEqualTo(0));
    expect(end, greaterThan(begin));
    final handler = source.substring(begin, end);

    // The native popup must not silently minimize a connected video call.
    expect(handler, contains("action == 'open'"));
    expect(handler, contains('unawaited(_expandActiveCall());'));
    expect(handler, isNot(contains('_openCallThread()')));

    // Opening a still-ringing call must not auto-answer or skip its prompt.
    expect(handler, contains('if (_incomingDialogOpen)'));
    expect(handler, contains('_openWindow();'));
  });
}
