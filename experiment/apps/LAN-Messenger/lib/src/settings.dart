import 'dart:io';
import 'package:flutter/material.dart';
import 'identity.dart';
import 'recoverable_json_file.dart';
import 'lan_reconnect_policy.dart';

/// Intentional defaults: auto-receive known LAN peers, never auto-open files.
/// Receiver quotas keep unsolicited files from consuming all device storage.
class AppSettings {
  bool autoReceiveFiles = true;
  int maximumFileMb = 512;
  int reconnectGraceSeconds = 60;
  final List<String> routedPeerAddresses = [];
  bool soundsEnabled = true;
  bool minimizeToTray = true;
  bool backgroundMode = true;
  bool startWithWindows = false;
  bool headsUpNotifications = true;
  bool useAppSounds = true;
  String avatarPath = '';
  int accentValue = 0xff1267d8;
  String fontFamily = 'Default';
  double fontScale = 1.0;
  final Map<String, int> threadAccents = {};
  final Map<String, String> soundPaths = {};
  Color get accent => Color(accentValue);
  Color threadAccent(String peerId) => Color(threadAccents[peerId] ?? accentValue);


  static Future<File> _file() async {
    final dir = await Identity.appDirectory();
    return File('${dir.path}${Platform.pathSeparator}settings.json');
  }

  static Future<AppSettings> load() async {
    final settings = AppSettings();
    try {
      final map = await RecoverableJsonFile.read(await _file(),
          isValid: (value) => value is Map<String, dynamic>);
      if (map is Map<String,dynamic>) {
        settings.autoReceiveFiles = map['autoReceiveFiles'] is bool ? map['autoReceiveFiles'] : true;
        settings.maximumFileMb = map['maximumFileMb'] is int ?
            (map['maximumFileMb'] as int).clamp(16,2048).toInt() : 512;
        settings.reconnectGraceSeconds =
            LanReconnectPolicy.clampSeconds(map['reconnectGraceSeconds']);
        if (map['routedPeerAddresses'] is List) {
          for (final entry in (map['routedPeerAddresses'] as List).take(8)) {
            if (entry is String) {
              final seed = LanReconnectPolicy.privateIpv4Seed(entry);
              if (seed != null && !settings.routedPeerAddresses.contains(seed)) {
                settings.routedPeerAddresses.add(seed);
              }
            }
          }
        }
        settings.soundsEnabled = map['soundsEnabled'] is bool ? map['soundsEnabled'] : true;
        settings.minimizeToTray = map['minimizeToTray'] is bool ? map['minimizeToTray'] : true;
        settings.backgroundMode = map['backgroundMode'] is bool ? map['backgroundMode'] : true;
        settings.startWithWindows = map['startWithWindows'] is bool ? map['startWithWindows'] : false;
        settings.headsUpNotifications = map['headsUpNotifications'] is bool ? map['headsUpNotifications'] : true;
        settings.useAppSounds = map['useAppSounds'] is bool ? map['useAppSounds'] : true;
        settings.avatarPath = map['avatarPath'] is String ? map['avatarPath'] : '';
        settings.accentValue = map['accentValue'] is int ? map['accentValue'] : 0xff1267d8;
        settings.fontFamily = ['Default','Serif','Monospace'].contains(map['fontFamily']) ? map['fontFamily'] : 'Default';
        settings.fontScale = map['fontScale'] is num ? (map['fontScale'] as num).toDouble().clamp(0.85, 1.4) : 1.0;
        if (map['threadAccents'] is Map) {
          (map['threadAccents'] as Map).forEach((key, value) {
            if (key is String && value is int && key.length < 100) settings.threadAccents[key] = value;
          });
        }
        if (map['soundPaths'] is Map) {
          (map['soundPaths'] as Map).forEach((key, value) {
            if (key is String && value is String && key.length < 40) settings.soundPaths[key] = value;
          });
        }
      }
    } catch (_) {}
    return settings;
  }

  Future<void> save() async {
    final file = await _file();
    await RecoverableJsonFile.write(file, {
      'autoReceiveFiles': autoReceiveFiles,
      'maximumFileMb': maximumFileMb,
      'reconnectGraceSeconds': reconnectGraceSeconds,
      'routedPeerAddresses': routedPeerAddresses,
      'soundsEnabled': soundsEnabled,
      'minimizeToTray': minimizeToTray,
      'backgroundMode': backgroundMode,
      'startWithWindows': startWithWindows,
      'headsUpNotifications': headsUpNotifications,
      'useAppSounds': useAppSounds,
      'avatarPath': avatarPath,
      'accentValue': accentValue,
      'fontFamily': fontFamily,
      'fontScale': fontScale,
      'threadAccents': threadAccents,
      'soundPaths': soundPaths,
    });
  }

  /// reg.exe uses the verb "add", not "/add"; this was the original Windows
  /// startup failure. Keep arguments unquoted here: Process.run handles them.
  static List<String> windowsStartupArgs(bool enabled, String executable) {
    const key = r'HKCU\Software\Microsoft\Windows\CurrentVersion\Run';
    return enabled
        ? ['add', key, '/v', 'LAN Messenger', '/t', 'REG_SZ', '/d', '"$executable"', '/f']
        : ['delete', key, '/v', 'LAN Messenger', '/f'];
  }

  Future<void> configureWindowsStartup(bool enabled) async {
    if (!Platform.isWindows) return;
    final args = windowsStartupArgs(enabled, Platform.resolvedExecutable);
    final result = await Process.run('reg.exe', args, runInShell: false);
    if (result.exitCode != 0) {
      throw StateError('Windows startup setting failed: ${result.stderr}');
    }
    startWithWindows = enabled;
    await save();
  }
}