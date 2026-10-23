import 'dart:convert';
import 'dart:io';
import 'identity.dart';

/// Intentional defaults: auto-receive known LAN peers, never auto-open files.
/// Receiver quotas keep unsolicited files from consuming all device storage.
class AppSettings {
  bool autoReceiveFiles = true;
  int maximumFileMb = 512;
  bool soundsEnabled = true;
  bool minimizeToTray = true;
  bool backgroundMode = true;
  bool startWithWindows = false;

  static Future<File> _file() async {
    final dir = await Identity.appDirectory();
    return File('${dir.path}${Platform.pathSeparator}settings.json');
  }

  static Future<AppSettings> load() async {
    final settings = AppSettings();
    try {
      final map = jsonDecode(await (await _file()).readAsString());
      if (map is Map<String,dynamic>) {
        settings.autoReceiveFiles = map['autoReceiveFiles'] is bool ? map['autoReceiveFiles'] : true;
        settings.maximumFileMb = map['maximumFileMb'] is int ?
            (map['maximumFileMb'] as int).clamp(16,2048).toInt() : 512;
        settings.soundsEnabled = map['soundsEnabled'] is bool ? map['soundsEnabled'] : true;
        settings.minimizeToTray = map['minimizeToTray'] is bool ? map['minimizeToTray'] : true;
        settings.backgroundMode = map['backgroundMode'] is bool ? map['backgroundMode'] : true;
        settings.startWithWindows = map['startWithWindows'] is bool ? map['startWithWindows'] : false;
      }
    } catch (_) {}
    return settings;
  }

  Future<void> save() async {
    final file = await _file();
    await file.writeAsString(jsonEncode({
      'autoReceiveFiles': autoReceiveFiles,
      'maximumFileMb': maximumFileMb,
      'soundsEnabled': soundsEnabled,
      'minimizeToTray': minimizeToTray,
      'backgroundMode': backgroundMode,
      'startWithWindows': startWithWindows,
    }), flush:true);
  }

  /// Optional per-user autorun, never modified without user toggling it.
  Future<void> configureWindowsStartup(bool enabled) async {
    if (!Platform.isWindows) return;
    const key = r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run';
    final args = enabled ? ['/add', key, '/v', 'LAN Messenger', '/t', 'REG_SZ',
      '/d', '"${Platform.resolvedExecutable}"', '/f'] :
      ['/delete', key, '/v', 'LAN Messenger', '/f'];
    final result = await Process.run('reg', args);
    if (result.exitCode != 0) {
      throw StateError('Unable to update Windows startup: ${result.stderr}');
    }
    startWithWindows=enabled;
    await save();
  }
}