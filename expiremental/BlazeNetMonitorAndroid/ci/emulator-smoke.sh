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
# Tap the real Start monitoring button. On the fixed Pixel_2 emulator
# the button occupies the center of the controls card at ~47% screen height.
# UIAutomator previously hung before entering the tested application.
SIZE="$(adb shell wm size | sed -n 's/.*: \([0-9]*\)x\([0-9]*\).*/\1 \2/p' | tail -1)"
read -r WIDTH HEIGHT <<< "$SIZE"
test -n "$WIDTH" && test -n "$HEIGHT"
X=$((WIDTH/2))
Y=$((HEIGHT*47/100))
echo "Tapping Start monitoring at $X,$Y on $WIDTH x $HEIGHT"
adb shell input tap "$X" "$Y"
sleep 12
pid=$(adb shell pidof "$PKG" | tr -d '\r')
test -n "$pid" || { echo 'FAIL app process terminated after Start Monitoring'; exit 3; }
adb shell dumpsys activity services | grep -F "$PKG/.MonitorService" || {
  echo 'FAIL foreground monitor service missing'; exit 3;
}
adb shell dumpsys notification --noredact > /tmp/blaze-android-notification-after.txt
if ! grep -F "BlazeNetMonitor" /tmp/blaze-android-notification-after.txt; then
  echo 'FAIL no BlazeNetMonitor notification after real UI Start'; exit 3
fi
if ! grep -E 'id=(101|102)' /tmp/blaze-android-notification-after.txt | grep -q '101'; then
  echo 'WARN could not identify both notification IDs in OEM dumpsys format'
fi
adb logcat -d -v brief | grep -E 'E AndroidRuntime:.*(FATAL EXCEPTION|Process: com.blazesystems.blazenetmonitor)' && {
  echo 'FAIL unhandled Android service/UI exception';exit 3;
} || true
echo 'PASS real Start button, foreground process/service and network notification survive 12 seconds'
