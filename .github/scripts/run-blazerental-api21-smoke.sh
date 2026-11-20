#!/usr/bin/env bash
# Disposable Android 5.0 (API 21) launch smoke test; NO Device Owner provisioning.
set -euo pipefail

test -n "$TARGET" && test -n "$ANDROID_HOME"
mkdir -p rental-api21-evidence
sdk="$(timeout 20s adb shell getprop ro.build.version.sdk | tr -d '\r')"
printf '%s\n' "$sdk" | tee rental-api21-evidence/device-api.txt
test "$sdk" = "21"

mapfile -t apks < <(find "$TARGET/build/outputs/apk" -type f -name '*aosp*debug*.apk' | sort)
if [[ "${#apks[@]}" -ne 1 ]]; then
  printf 'Expected exactly one AOSP debug APK; found %s\n' "${#apks[@]}" >&2
  exit 1
fi
apk="${apks[0]}"
sha256sum "$apk" | tee rental-api21-evidence/apk.sha256
"$ANDROID_HOME/build-tools/27.0.3/aapt" dump badging "$apk" > rental-api21-evidence/aapt-badging.txt
"$ANDROID_HOME/build-tools/27.0.3/apksigner" verify --verbose --print-certs \
  --min-sdk-version 21 "$apk" > rental-api21-evidence/apksigner-verify.txt
python3 "$TARGET/tools/verify_apk_contract.py" "$apk" --mode debug \
  --min-api 21 --minimum-version-code 50300 \
  --aapt "$ANDROID_HOME/build-tools/27.0.3/aapt" \
  --apksigner "$ANDROID_HOME/build-tools/27.0.3/apksigner" \
  > rental-api21-evidence/apk-contract.json

timeout 90s adb install -r "$apk" | tee rental-api21-evidence/install.txt
grep -Eq '^Success$' rental-api21-evidence/install.txt
timeout 20s adb shell pm path com.blazesystems.blazerental.debug \
  | tee rental-api21-evidence/installed-package.txt
grep -q '^package:' rental-api21-evidence/installed-package.txt

# The main Activity is declared in the existing Launcher3 manifest.
timeout 40s adb shell am start -W \
  -n com.blazesystems.blazerental.debug/com.google.android.apps.nexuslauncher.NexusLauncherActivity \
  | tee rental-api21-evidence/activity-start.txt
grep -q 'Status: ok' rental-api21-evidence/activity-start.txt

sleep 5
timeout 15s adb logcat -d -t 2500 > rental-api21-evidence/logcat-tail.txt
python3 - <<'PY'
from pathlib import Path
import sys

text = Path("rental-api21-evidence/logcat-tail.txt").read_text(errors="replace")
lines = text.splitlines()
for idx, line in enumerate(lines):
    if "FATAL EXCEPTION" not in line:
        continue
    block = "\n".join(lines[idx:idx + 24])
    if ("Process: com.blazesystems.blazerental.debug" in block or
            "com.google.android.apps.nexuslauncher.NexusLauncherActivity" in block):
        sys.exit("FAIL: rental launcher fatal exception in AndroidRuntime logcat")
print("No observed rental launcher FATAL EXCEPTION in collected logcat tail")
PY

printf 'PASS: API21 APK signed/installed and launcher Activity started; Device Owner NOT EXECUTED\n' \
  | tee rental-api21-evidence/result.txt
