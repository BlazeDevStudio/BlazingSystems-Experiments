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
  test('native Windows popup labels open action as call, not thread', () {
    final native = File('tool/windows_call_toast.cpp').readAsStringSync();
    final begin = native.indexOf('void WindowsCallToast::ResizeButtons()');
    final end = native.indexOf('void WindowsCallToast::Show(', begin);
    expect(begin, greaterThanOrEqualTo(0));
    expect(end, greaterThan(begin));
    final labels = native.substring(begin, end);
    expect(labels, contains('captions[2] = L"Open call";'));
    expect(labels, isNot(contains('L"Open thread"')));

    // The toast is copied into the generated Windows runner before compiling.
    final platformSetup = File('tool/prepare_platforms.py').readAsStringSync();
    expect(platformSetup, contains("root / 'tool/windows_call_toast.cpp'"));
    // Button 103 remains the call-opening action, not a conversation shortcut.
    final handler = native.substring(native.indexOf('case WM_COMMAND:'));
    expect(handler, contains('else if (id == 103) Emit("open");'));
  });

}
