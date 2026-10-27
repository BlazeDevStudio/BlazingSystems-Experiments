import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Windows restores its regular window before slow WebRTC teardown', () {
    final code = File('lib/main.dart').readAsStringSync();
    final begin = code.indexOf('Future<void> _finalizeEndedCallPresentation(');
    final end = code.indexOf('Future<void> _showActiveTrayMenu(', begin);
    expect(begin, greaterThanOrEqualTo(0));
    expect(end, greaterThan(begin));
    final body = code.substring(begin, end);
    final windows = body.indexOf('if (Platform.isWindows)');
    final teardownWait = body.indexOf('for (var i = 0; i < 80');
    expect(windows, greaterThanOrEqualTo(0));
    expect(teardownWait, greaterThan(windows));
    expect(body.substring(windows, teardownWait),
        contains('await _endCallPresentation();'));
    expect(body.substring(windows, teardownWait), contains('return;'));
    // Still don't dismiss Android PiP mid-RTC engine cleanup.
    expect(body.substring(teardownWait), contains('await _endCallPresentation();'));
    expect(body, contains('call.callId == null && mounted'));
  });
}
