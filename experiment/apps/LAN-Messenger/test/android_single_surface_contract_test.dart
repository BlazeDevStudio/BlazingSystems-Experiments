import 'dart:io';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android APK must not package the old application-owned call overlay', () {
    final native = File('tool/AndroidMainActivity.kt').readAsStringSync();
    final generator = File('tool/prepare_platforms.py').readAsStringSync();
    final app = File('lib/main.dart').readAsStringSync();

    expect(native.contains('AndroidCallOverlay'), isFalse);
    expect(native.contains('overlay().show('), isFalse);
    expect(generator.contains("'android.permission.SYSTEM_ALERT_WINDOW',"), isFalse);
    expect(generator.contains("obsolete.unlink()"), isTrue);
    expect(app.contains("Floating call window permission"), isFalse);
    expect(app.contains("Video picture-in-picture settings"), isTrue);
  });

  test('every call alert has its own explicit group, unlike background service', () {
    // On Android 35 the incoming call was auto-grouped with FlutterBackground
    // and the real Answer action was hidden in an inaccessible summary.
    final native = File('tool/AndroidMainActivity.kt').readAsStringSync();
    expect(native.split('.setCategory(Notification.CATEGORY_CALL)').length - 1, 3);
    expect(native.split('.setGroup(callNotificationGroup)').length - 1, 3);
    expect(native.contains('private val callNotificationGroup = "lan-messenger-call-actions"'), isTrue);
    // No full-screen intent is introduced; system notification remains the UI.
    // Native tests still must click the REAL notification Answer action.
  });

  test('video PiP state cannot depend on incoming notification access', () {
    final native = File('tool/AndroidMainActivity.kt').readAsStringSync();
    final start = native.indexOf('private fun showOngoingCall(');
    final end = native.indexOf('private fun pictureActions(', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final ongoing = native.substring(start, end);
    expect(ongoing.indexOf('pipEnabledForCall = video'), greaterThanOrEqualTo(0));
    expect(ongoing.indexOf('if (!canNotify()) return false'),
        greaterThan(ongoing.indexOf('pipEnabledForCall = video')));
    expect(native.contains('AndroidCallOverlay'), isFalse);
  });
  test('Android PiP uses OS expansion, not a nonexpanding custom Open action', () {
    final native = File('tool/AndroidMainActivity.kt').readAsStringSync();
    final start = native.indexOf('private fun pictureActions(');
    final end = native.indexOf('private fun pipFailureReason()', start);
    expect(start, greaterThanOrEqualTo(0));
    expect(end, greaterThan(start));
    final pipActions = native.substring(start, end);
    expect(pipActions, contains('control("mute"'));
    expect(pipActions, contains('control("end"'));
    expect(pipActions, isNot(contains('control("open"')));
    expect(native, contains('"Return to live call"'));
    expect(native, isNot(contains('"Open thread"')));
  });

}
