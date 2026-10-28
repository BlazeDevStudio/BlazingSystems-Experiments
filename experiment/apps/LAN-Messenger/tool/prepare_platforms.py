"""Patch only generated Flutter platform runners; never touches application source."""
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parents[1]
manifest = root / 'android/app/src/main/AndroidManifest.xml'
if manifest.exists():
    text = manifest.read_text(encoding='utf-8')
    permissions = [
        'android.permission.INTERNET',
        'android.permission.ACCESS_WIFI_STATE',
        'android.permission.ACCESS_NETWORK_STATE',
        'android.permission.CHANGE_WIFI_MULTICAST_STATE',
        'android.permission.RECORD_AUDIO',
        'android.permission.CAMERA',
        'android.permission.FOREGROUND_SERVICE',
        'android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE',
        'android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION',
        'android.permission.POST_NOTIFICATIONS',
    ]
    missing = ''.join(f'    <uses-permission android:name="{p}" />\n' for p in permissions
                      if f'android:name="{p}"' not in text)
    # Remove the obsolete overlay permission even if regenerating a prior manifest.
    text = re.sub(r'^\s*<uses-permission android:name="android\.permission\.SYSTEM_ALERT_WINDOW"\s*/>\s*$', '', text, flags=re.MULTILINE)
    text = text.replace('<application', missing + '    <application', 1)
    text = re.sub(r'android:label="[^"]*"', 'android:label="LAN Messenger"', text, count=1)
    text = text.replace('android:name=".MainActivity"',
        'android:name=".MainActivity" android:supportsPictureInPicture="true" '
        'android:resizeableActivity="true"', 1)
    text = text.replace('<application', '<application android:usesCleartextTraffic="true"', 1)
    service = ('        <service android:name="de.julianassmann.flutter_background.IsolateHolderService" '
               'android:exported="false" android:foregroundServiceType="connectedDevice" />\n')
    if 'de.julianassmann.flutter_background.IsolateHolderService' not in text:
        text = text.replace('</application>', service + '    </application>', 1)
    receiver = ('        <receiver android:name=".CallActionReceiver" android:exported="false" />\n')
    if 'android:name=".CallActionReceiver"' not in text:
        text = text.replace('</application>', receiver + '    </application>', 1)
    projection_service = ('        <service android:name=".ScreenProjectionService" '
                          'android:exported="false" '
                          'android:foregroundServiceType="mediaProjection" />\n')
    if 'android:name=".ScreenProjectionService"' not in text:
        text = text.replace('</application>', projection_service + '    </application>', 1)
    # Device owner must manually grant Accessibility access in Android settings.
    # Never exported, no hidden remote-control service or automatic enabling.
    accessibility = ('        <service android:name=".RemoteTouchService" '
                     'android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE" '
                     'android:exported="true">\n'
                     '            <intent-filter>\n'
                     '                <action android:name="android.accessibilityservice.AccessibilityService" />\n'
                     '            </intent-filter>\n'
                     '            <meta-data android:name="android.accessibilityservice" '
                     'android:resource="@xml/remote_touch_accessibility" />\n'
                     '        </service>\n')
    if 'android:name=".RemoteTouchService"' not in text:
        text = text.replace('</application>', accessibility + '    </application>', 1)
    manifest.write_text(text, encoding='utf-8')
    print(f'Patched {manifest}')

    main_activity = root / 'android/app/src/main/kotlin/com/example/lan_messenger/MainActivity.kt'
    main_activity.parent.mkdir(parents=True, exist_ok=True)
    # Native NotificationManager is intentionally used instead of a heavy plugin:
    # heads-up notifications need no network, account or background polling SDK.
    main_activity.write_text((root / 'tool/AndroidMainActivity.kt').read_text(encoding='utf-8'), encoding='utf-8')
    # System CallStyle and Android native PiP replace the legacy overlay.
    obsolete = main_activity.parent / 'AndroidCallOverlay.kt'
    if obsolete.exists():
        obsolete.unlink()
    projection_target = main_activity.parent / 'ScreenProjectionService.kt'
    projection_target.write_text((root / 'tool/ScreenProjectionService.kt').read_text(encoding='utf-8'), encoding='utf-8')
    touch_target = main_activity.parent / 'RemoteTouchService.kt'
    touch_target.write_text((root / 'tool/RemoteTouchService.kt').read_text(encoding='utf-8'), encoding='utf-8')
    accessibility_xml = root / 'android/app/src/main/res/xml/remote_touch_accessibility.xml'
    accessibility_xml.parent.mkdir(parents=True, exist_ok=True)
    accessibility_xml.write_text((root / 'tool/remote_touch_accessibility.xml').read_text(encoding='utf-8'), encoding='utf-8')
    strings_xml = root / 'android/app/src/main/res/values/strings.xml'
    strings_xml.parent.mkdir(parents=True, exist_ok=True)
    if not strings_xml.exists():
        strings_xml.write_text('<resources></resources>', encoding='utf-8')
    strings = strings_xml.read_text(encoding='utf-8')
    if 'lan_remote_touch_description' not in strings:
        strings = strings.replace('</resources>', '<string name="lan_remote_touch_description">Optional mouse-like taps during an approved LAN Messenger screen-sharing call. Enable only when you want remote control, and revoke it in the call or Accessibility settings.</string></resources>')
        strings_xml.write_text(strings, encoding='utf-8')

    # Audio tones are generated original assets; Android plays these through
    # high-priority notification channels even when Flutter is not foregrounded.
    raw = root / 'android/app/src/main/res/raw'
    raw.mkdir(parents=True, exist_ok=True)
    for key in ('call','video_call','message','file'):
        source = root / 'assets/sounds' / (key+'.wav')
        if source.exists():
            shutil.copy2(source, raw / (key+'.wav'))

# Use the owner's ConnectIT logo on native launchers without changing
# the existing LAN protocol, package identity or account functionality.
brand = root / 'assets/branding/connectit'
res = root / 'android/app/src/main/res'
if manifest.exists():
    for folder, name in {
        'mipmap-mdpi': 'connectit-icon-48.png',
        'mipmap-hdpi': 'connectit-icon-64.png',
        'mipmap-xhdpi': 'connectit-icon-128.png',
        'mipmap-xxhdpi': 'connectit-icon-128.png',
        'mipmap-xxxhdpi': 'connectit-icon-192.png'
    }.items():
        dest = res / folder
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(brand / name, dest / 'ic_launcher.png')
        assert (dest / 'ic_launcher.png').read_bytes() == (brand / name).read_bytes()

    adaptive = res / 'mipmap-nodpi'
    adaptive.mkdir(parents=True, exist_ok=True)
    for source_name, target_name in (
        ('android-adaptive-foreground.png', 'connectit_foreground.png'),
        ('android-adaptive-background.png', 'connectit_background.png')
    ):
        shutil.copyfile(brand / source_name, adaptive / target_name)
        assert (adaptive / target_name).read_bytes() == (brand / source_name).read_bytes()

    xml = res / 'mipmap-anydpi-v26/ic_launcher.xml'
    xml.parent.mkdir(parents=True, exist_ok=True)
    xml.write_text('''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@mipmap/connectit_background" />
    <foreground android:drawable="@mipmap/connectit_foreground" />
</adaptive-icon>
''', encoding='utf-8')

windows_icon = root / 'windows/runner/resources/app_icon.ico'
if windows_icon.parent.exists():
    shutil.copyfile(brand / 'connectit.ico', windows_icon)
    assert windows_icon.read_bytes() == (brand / 'connectit.ico').read_bytes()

window = root / 'windows/runner/main.cpp'
if window.exists():
    text = window.read_text(encoding='utf-8')
    text = text.replace('L"lan_messenger"', 'L"LAN Messenger"')
    window.write_text(text, encoding='utf-8')
    print(f'Patched {window}')

# A second native popup HWND runs on the Flutter runner's existing Windows
# message loop. Its independent lifecycle allows calls to be offered while
# the main Flutter window is hidden without activating/restoring that window.
runner = root / 'windows/runner'
if runner.exists():
    header = runner / 'windows_call_toast.h'
    source = runner / 'windows_call_toast.cpp'
    header.write_text((root / 'tool/windows_call_toast.h').read_text(encoding='utf-8'),
                      encoding='utf-8')
    source.write_text((root / 'tool/windows_call_toast.cpp').read_text(encoding='utf-8'),
                      encoding='utf-8')
    flutter_window = runner / 'flutter_window.cpp'
    if flutter_window.exists():
        code = flutter_window.read_text(encoding='utf-8')
        if '#include "windows_call_toast.h"' not in code:
            code = '#include "windows_call_toast.h"\n' + code
        if 'g_call_toast' not in code:
            code = code.replace(
                'FlutterWindow::FlutterWindow(',
                'namespace {\nstd::unique_ptr<WindowsCallToast> g_call_toast;\n}\n\n'
                'FlutterWindow::FlutterWindow(', 1)
            marker = 'SetChildContent(flutter_controller_->view()->GetNativeWindow());'
            if marker not in code:
                raise RuntimeError('Flutter runner has no window child anchor')
            code = code.replace(marker, marker + '\n  g_call_toast = '
                                'std::make_unique<WindowsCallToast>('
                                'flutter_controller_->engine()->messenger(), '
                                'GetAncestor(flutter_controller_->view()->GetNativeWindow(), GA_ROOT));', 1)
            on_destroy = 'void FlutterWindow::OnDestroy() {'
            if on_destroy not in code:
                raise RuntimeError('Flutter runner has no OnDestroy anchor')
            code = code.replace(on_destroy,
                                on_destroy + '\n  g_call_toast.reset();', 1)
        flutter_window.write_text(code, encoding='utf-8')
    cmake = runner / 'CMakeLists.txt'
    if cmake.exists():
        code = cmake.read_text(encoding='utf-8')
        if 'windows_call_toast.cpp' not in code:
            code += ('\n# Native, non-activating draggable call HUD.\n'
                     'target_sources(${BINARY_NAME} PRIVATE "windows_call_toast.cpp")\n')
        cmake.write_text(code, encoding='utf-8')

# Flutter create may scaffold a demo widget_test referencing MyApp. This is
# not our application and must not replace the real protocol/crypto tests.
demo = root / 'test/widget_test.dart'
if demo.exists() and 'pumpWidget(const MyApp())' in demo.read_text(encoding='utf-8'):
    demo.unlink()
    print(f'Removed default template test {demo}')