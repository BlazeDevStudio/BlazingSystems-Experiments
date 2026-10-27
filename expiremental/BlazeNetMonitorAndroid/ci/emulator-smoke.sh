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
# Instrument the service under the APP UID (the service is deliberately
# exported=false). A plain "adb shell am" runs under the shell UID and is
# rejected by Android even if the app itself is functioning.
# UIAutomator on this runner timed out independently of the tested app.
adb shell run-as "$PKG" /system/bin/am start-foreground-service \
  -n "$PKG/.MonitorService" -a "$PKG.START"
sleep 12
pid=$(adb shell pidof "$PKG" | tr -d '\r')
test -n "$pid" || { echo 'FAIL app process terminated after Start Monitoring'; exit 3; }
adb shell dumpsys activity services | grep -F "$PKG/.MonitorService" || {
  echo 'FAIL foreground monitor service missing'; exit 3;
}
adb logcat -d -v brief | grep -E 'E AndroidRuntime:.*(FATAL EXCEPTION|Process: com.blazesystems.blazenetmonitor)' && {
  echo 'FAIL unhandled Android service/UI exception';exit 3;
} || true
echo 'PASS foreground monitor service survived 12 seconds and app process remains alive'
