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
# On first install a donation dialog appears. BACK dismisses it.
adb shell input keyevent KEYCODE_BACK
sleep 1
adb shell uiautomator dump /sdcard/window.xml
adb exec-out cat /sdcard/window.xml > /tmp/blaze-android-ui.xml
python3 - <<'PY'
import xml.etree.ElementTree as E,re,subprocess
root=E.parse('/tmp/blaze-android-ui.xml').getroot()
nodes=[n for n in root.iter('node') if n.attrib.get('text','')=='Start monitoring']
if not nodes: raise SystemExit('Start monitoring control absent after dismissing intro; cannot claim test')
coords=list(map(int,re.findall(r'\d+',nodes[0].attrib['bounds'])))
subprocess.run(['adb','shell','input','tap',str((coords[0]+coords[2])//2),str((coords[1]+coords[3])//2)],check=True)
PY
sleep 12
pid=$(adb shell pidof "$PKG" | tr -d '\r')
test -n "$pid" || { echo 'FAIL app process terminated after Start Monitoring'; exit 3; }
adb shell dumpsys activity services | grep -F "$PKG/.MonitorService" || {
  echo 'FAIL foreground monitor service missing'; exit 3;
}
adb logcat -d -v brief | grep -E 'FATAL EXCEPTION|RemoteServiceException|Process: com.blazesystems.blazenetmonitor' && {
  echo 'FAIL unhandled Android service/UI exception';exit 3;
} || true
echo 'PASS tap Start Monitoring, app process survives 12 seconds, service exists'
