#!/usr/bin/env bash
set -euo pipefail
PKG=com.blazesystems.blazenetmonitor
APK=expiremental/BlazeNetMonitorAndroid/app/build/outputs/apk/debug/app-debug.apk
finish() {
  adb logcat -d -v threadtime > /tmp/blaze-android-logcat.txt || true
  adb shell dumpsys notification --noredact > /tmp/blaze-android-notification.txt || true
  adb shell dumpsys activity services > /tmp/blaze-android-services.txt || true
  echo '===== app exception evidence ====='
  grep -A 22 -B 2 -E 'FATAL EXCEPTION|Process: com.blazesystems.blazenetmonitor|Bad notification|RemoteServiceException' /tmp/blaze-android-logcat.txt | tail -95 || true
}
trap finish EXIT

adb install -r "$APK"
adb shell pm grant "$PKG" android.permission.POST_NOTIFICATIONS
adb logcat -c || true
adb shell am start -W -n "$PKG/.MainActivity"
sleep 5
# A first-run donation dialog can cover the control. BACK closes it.
adb shell input keyevent KEYCODE_BACK
sleep 1

# Never tap a guessed percentage of the display; scrolling, density and
# notification/status-bar heights vary. Locate the actual Android view ID.
dump_ui() {
  timeout 25s adb shell uiautomator dump /sdcard/blazenetmonitor-window.xml > /tmp/blaze-ui-dump-command.txt 2>&1 &&
    timeout 15s adb pull /sdcard/blazenetmonitor-window.xml /tmp/blaze-ui.xml >/dev/null 2>&1
}
if ! dump_ui; then
  echo 'INCONCLUSIVE: Android UI hierarchy could not be collected'
  cat /tmp/blaze-ui-dump-command.txt || true
  exit 3
fi
coords="$(python3 - <<'PY'
import re
import sys
import xml.etree.ElementTree as ET
root = ET.parse('/tmp/blaze-ui.xml').getroot()
matches = []
for node in root.iter('node'):
    if node.attrib.get('resource-id') != 'com.blazesystems.blazenetmonitor:id/monitor_toggle_button':
        continue
    if node.attrib.get('text') != 'Start monitoring' or node.attrib.get('clickable') != 'true':
        continue
    match = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.attrib.get('bounds', ''))
    if match:
        x1,y1,x2,y2 = map(int, match.groups())
        if x2 > x1 and y2 > y1:
            matches.append(((x1+x2)//2, (y1+y2)//2))
if len(matches) != 1:
    print('INCONCLUSIVE: expected one visible, clickable Start monitoring button, found', len(matches), file=sys.stderr)
    sys.exit(3)
print(*matches[0])
PY
)" || { echo 'INCONCLUSIVE: test did not identify the real Start monitoring button'; exit 3; }
read -r X Y <<< "$coords"
echo "Tapping actual Start monitoring view at ($X,$Y)"
adb shell input tap "$X" "$Y"
sleep 12

pid="$(adb shell pidof "$PKG" | tr -d '\r')"
test -n "$pid" || { echo 'FAIL app process terminated after Start monitoring'; exit 3; }
adb shell dumpsys activity services > /tmp/blaze-android-services-after.txt
if ! grep -F "$PKG/.MonitorService" /tmp/blaze-android-services-after.txt; then
  echo 'FAIL foreground monitor service missing after real button click'
  exit 3
fi
adb shell dumpsys notification --noredact > /tmp/blaze-android-notification-after.txt
if ! grep -F "$PKG" /tmp/blaze-android-notification-after.txt; then
  echo 'FAIL no app notification after Start monitoring'
  exit 3
fi
if grep -E 'FATAL EXCEPTION|RemoteServiceException|Bad notification' /tmp/blaze-android-logcat.txt 2>/dev/null | grep -q "$PKG"; then
  echo 'FAIL app exception detected'
  exit 3
fi
echo "PASS actual Start monitoring view, app PID $pid, service and notification survive 12 seconds"
