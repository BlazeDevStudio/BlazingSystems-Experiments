#!/usr/bin/env bash
set -euo pipefail

# The Android emulator runner executes every workflow script line separately.
# Shell loops and traps must live within this one bash file.
capture_evidence() {
  adb logcat -d -v time >> threadharbor-logcat.txt 2>/dev/null || true
  adb exec-out screencap -p > threadharbor-smoke.png 2>/dev/null || true
}
trap capture_evidence EXIT

adb install preview/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -W -n com.blazesystems.threadharbor/.MainActivity
ready=0
for attempt in $(seq 1 12); do
  if adb shell pidof com.blazesystems.threadharbor 2>/dev/null | grep -Eq '[0-9]+'; then
    ready=1
    break
  fi
  sleep 2
done
if [ "$ready" -ne 1 ]; then
  echo "FAIL: Android app process did not remain alive after launch" >&2
  exit 1
fi
echo "PASS: Installed APK launched and process is alive"
python3 expiremental/Blaze-ThreadHarbor-Utility/ci/emulator_bidirectional.py
adb shell pidof com.blazesystems.threadharbor | grep -Eq '[0-9]+'
echo "PASS: Native app process survived emulator UI regressions"
