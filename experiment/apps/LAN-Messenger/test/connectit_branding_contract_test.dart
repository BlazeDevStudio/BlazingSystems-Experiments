import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('ConnectIT originals are immutable and byte-identical to source', () {
    const originals = <String, String>{
      'connectit-logo-master.svg': 'aae32e59151cf4b83eed3225c053c4a9f6817768691c3849c5ec2e9d0f5d2c44',
      'connectit-app-icon.svg': '8f541a7c6f6b9f94f6a1c1ce18e7a4db0cfbaee696d35a8bc6a281cbf617fa52',
      'connectit-icon-48.png': 'bac11bb77cb47c99abe19b14e6adb38d34d4de3d2813f1cf008e1349adba0e0e',
      'connectit-icon-256.png': '3440f6ba8bd3eb9abf957e7e22091e921f346016c174b24cf07191bfd6c2a6bc',
      'connectit.ico': 'e7b6d8e8926651f59038b5def2e5a52bfab20e1b6d636548ab1d95ce18eb8101',
      'android-adaptive-foreground.png': '29f3107d4e303b82f708744d7003bc5133da6989141edd03186bb314cae0f957',
      'android-adaptive-background.png': '4e53a94e5d8a3f21ab9f143f75a50cfbfab3788aca03ea3b83910ff7cd3001e9',
    };
    for (final item in originals.entries) {
      final original = File('assets/branding/connectit/${item.key}');
      expect(original.existsSync(), isTrue, reason: 'Missing ${item.key}');
      expect(sha256.convert(original.readAsBytesSync()).toString(), item.value,
          reason: 'ConnectIT artwork differs from owner-provided source');
    }
  });

  test('ConnectIT is used for UI, Windows and Android icons only', () {
    final main = File('lib/main.dart').readAsStringSync();
    final pubspec = File('pubspec.yaml').readAsStringSync();
    final generator = File('tool/generate_assets.py').readAsStringSync();
    final platform = File('tool/prepare_platforms.py').readAsStringSync();
    expect(main, contains('assets/branding/connectit/connectit-icon-48.png'));
    expect(main, contains("rootBundle.load('assets/icons/lan_messenger.ico')"));
    expect(pubspec, contains('assets/branding/connectit/'));
    expect(generator, contains("root/'assets/branding/connectit/connectit.ico'"));
    expect(platform, contains("root / 'windows/runner/resources/app_icon.ico'"));
    expect(platform, contains("res / 'mipmap-anydpi-v26/ic_launcher.xml'"));
    expect(platform, contains('android-adaptive-foreground.png'));
    expect(platform, contains('android-adaptive-background.png'));
  });
}
