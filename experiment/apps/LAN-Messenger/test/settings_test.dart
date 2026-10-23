import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/settings.dart';

void main() {
  test('Windows autostart uses the proper reg.exe verbs and quotes paths', () {
    final args = AppSettings.windowsStartupArgs(true, r'C:\Program Files\LAN Messenger\lan_messenger.exe');
    expect(args.first, 'add');
    expect(args, contains('/f'));
    expect(args[args.indexOf('/d') + 1], startsWith('"C:'));
    expect(args[args.indexOf('/d') + 1], endsWith('lan_messenger.exe"'));
    expect(args, isNot(contains('/add')));
    expect(AppSettings.windowsStartupArgs(false, r'C:\app.exe').first, 'delete');
  });
}
