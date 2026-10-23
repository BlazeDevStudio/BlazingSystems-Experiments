"""Patch only generated Flutter platform runners; never touches application source."""
from pathlib import Path
import re

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
    text = text.replace('<application', missing + '    <application', 1)
    text = re.sub(r'android:label="[^"]*"', 'android:label="LAN Messenger"', text, count=1)
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
    manifest.write_text(text, encoding='utf-8')
    print(f'Patched {manifest}')

    main_activity = root / 'android/app/src/main/kotlin/com/example/lan_messenger/MainActivity.kt'
    main_activity.parent.mkdir(parents=True, exist_ok=True)
    # Native NotificationManager is intentionally used instead of a heavy plugin:
    # heads-up notifications need no network, account or background polling SDK.
    main_activity.write_text((root / 'tool/AndroidMainActivity.kt').read_text(encoding='utf-8'), encoding='utf-8')
    projection_target = main_activity.parent / 'ScreenProjectionService.kt'
    projection_target.write_text((root / 'tool/ScreenProjectionService.kt').read_text(encoding='utf-8'), encoding='utf-8')

    # Audio tones are generated original assets; Android plays these through
    # high-priority notification channels even when Flutter is not foregrounded.
    import shutil
    raw = root / 'android/app/src/main/res/raw'
    raw.mkdir(parents=True, exist_ok=True)
    for key in ('call','video_call','message','file'):
        source = root / 'assets/sounds' / (key+'.wav')
        if source.exists():
            shutil.copy2(source, raw / (key+'.wav'))

window = root / 'windows/runner/main.cpp'
if window.exists():
    text = window.read_text(encoding='utf-8')
    text = text.replace('L"lan_messenger"', 'L"LAN Messenger"')
    window.write_text(text, encoding='utf-8')
    print(f'Patched {window}')

# Flutter create may scaffold a demo widget_test referencing MyApp. This is
# not our application and must not replace the real protocol/crypto tests.
demo = root / 'test/widget_test.dart'
if demo.exists() and 'pumpWidget(const MyApp())' in demo.read_text(encoding='utf-8'):
    demo.unlink()
    print(f'Removed default template test {demo}')