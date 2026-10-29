import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final python = Platform.isWindows ? 'python' : 'python3';

  ProcessResult inspect(String xml) {
    final directory = Directory.systemTemp.createTempSync('lan-launcher-anr-');
    try {
      final file = File('${directory.path}${Platform.pathSeparator}ui.xml')
        ..writeAsStringSync(xml);
      return Process.runSync(
        python,
        ['tool/emulator_launcher_anr.py', file.path],
      );
    } finally {
      directory.deleteSync(recursive: true);
    }
  }

  const launcherAnr = '''
<hierarchy>
  <node text="Pixel Launcher isn't responding" package="android"
        resource-id="android:id/alertTitle"/>
  <node text="Close app" package="android" enabled="true"
        resource-id="android:id/aerr_close"
        bounds="[70,898][1010,1024]"/>
</hierarchy>
''';

  test('recovery clicks only Pixel Launcher Close app by actual bounds', () {
    final result = inspect(launcherAnr);
    expect(result.exitCode, 0, reason: result.stderr.toString());
    expect(result.stdout.toString().trim(), '540 961');
  });

  test('another app ANR is never clicked', () {
    final other = launcherAnr.replaceFirst(
      "Pixel Launcher isn't responding", "LAN Messenger isn't responding");
    expect(inspect(other).exitCode, isNot(0));
  });

  test('missing or spoofed system close button is refused', () {
    expect(inspect(launcherAnr.replaceFirst('android:id/aerr_close',
        'android:id/aerr_wait')).exitCode, isNot(0));
    expect(inspect(launcherAnr.replaceFirst('enabled="true"',
        'enabled="false"')).exitCode, isNot(0));
    expect(inspect(launcherAnr.replaceFirst('[70,898][1010,1024]',
        '[100,200][20,80]')).exitCode, isNot(0));
  });

  test('malformed accessibility XML fails closed', () {
    expect(inspect('<hierarchy><node').exitCode, isNot(0));
  });

  test('recovery does not weaken two-sided online UI assertion', () {
    final script = File('tool/android_dual_lan_smoke.sh').readAsStringSync();
    expect(script, contains('emulator_launcher_anr.py'));
    expect(script, contains('adb -s "$serial" shell input tap "$close_x" "$close_y"'));
    expect(script, contains('both=0'));
    expect(script, contains('if [[ "$both" == "1" ]]; then success=1; break; fi'));
    expect(script, contains('assert "Online" in displayed'));
    expect(script, contains('exit 1'));
  });
}
