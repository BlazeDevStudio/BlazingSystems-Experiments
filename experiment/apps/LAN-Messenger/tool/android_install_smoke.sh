#!/usr/bin/env bash
# Must run in ONE shell process. Android-emulator-runner runs separate script
# lines as individual sh -c commands, so stateful multiline snippets break.
set -euo pipefail
APK_DIR="$GITHUB_WORKSPACE/android-apk"
echo "Downloaded artifact contents:"
find "$APK_DIR" -maxdepth 8 -type f -print
APK="$(find "$APK_DIR" -type f -name 'app-x86_64-release.apk' -print -quit)"
if [[ -z "$APK" || ! -s "$APK" ]]; then
  echo "ERROR: app-x86_64-release.apk missing from downloaded artifact"
  exit 1
fi
echo "Installing $APK to Android emulator"
adb install -r "$APK"
echo "Installed package:"
adb shell pm list packages | grep -F 'com.example.lan_messenger'
adb logcat -c || true
echo "Starting the LAN Messenger launcher activity"
adb shell am start -W -n com.example.lan_messenger/.MainActivity
sleep 10
echo "Running process PID:"
adb shell pidof com.example.lan_messenger
# Exercise the Activity resume/Answer entrypoint without another device.
# A deliberately stale call ID must never crash or accidentally start capture.
echo "Testing background -> notification Answer Activity lifecycle (stale ID)"
adb shell input keyevent KEYCODE_HOME
sleep 2
adb shell am start -W -n com.example.lan_messenger/.MainActivity \
  --es action answer --es callId smoke-stale-answer-1
sleep 4
adb shell pidof com.example.lan_messenger
echo "Testing repeated Answer tap does not terminate Flutter"
adb shell am start -W -n com.example.lan_messenger/.MainActivity \
  --es action answer --es callId smoke-stale-answer-1
sleep 2
adb shell pidof com.example.lan_messenger
echo "Recent app-specific crash evidence (if any):"
if adb logcat -d -t 1600 | grep -E 'Process: com.example.lan_messenger|INSTALL_FAILED'; then
  echo "An installation or app crash was detected"
  exit 1
fi
echo "Android install and launch smoke passed"
