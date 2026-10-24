#!/usr/bin/env bash
# Two *real* Android emulator instances on the same hosted Linux runner.
# Emulator >=36.5 provides shared virtual Wi-Fi; older versions isolate peers.
# This validates process launch, Wi-Fi addresses and LAN discovery UI,
# NOT audio/video quality or a physical Windows <-> Android call.
set -euo pipefail
ROOT="$GITHUB_WORKSPACE"
OUT="$ROOT/android-lan-evidence"
mkdir -p "$OUT"
APK="$(find "$ROOT/android-apk" -type f -name app-x86_64-release.apk -print -quit)"
test -n "$APK" && test -s "$APK" || { echo "Missing x86_64 APK"; exit 1; }
EMULATOR="${ANDROID_HOME:-$ANDROID_SDK_ROOT}/emulator/emulator"
AVD_MANAGER="${ANDROID_HOME:-$ANDROID_SDK_ROOT}/cmdline-tools/latest/bin/avdmanager"
"$EMULATOR" -version 2>&1 | head -n 4 | tee "$OUT/emulator-version.txt"
if [[ ! -x "$AVD_MANAGER" ]]; then AVD_MANAGER="$(command -v avdmanager)"; fi
if [[ ! -x "$AVD_MANAGER" ]]; then echo "avdmanager unavailable"; exit 1; fi
echo no | "$AVD_MANAGER" create avd -n lan_peer2 -k 'system-images;android-35;google_apis;x86_64' --device pixel_2 --force
"$EMULATOR" -avd lan_peer2 -port 5556 -no-window -gpu swiftshader_indirect \
  -no-snapshot -noaudio -no-boot-anim >"$OUT/emulator-peer2.log" 2>&1 &
SECOND_PID=$!
cleanup() {
  kill "$SECOND_PID" 2>/dev/null || true
}
trap cleanup EXIT
for attempt in $(seq 1 90); do
  completed="$(adb -s emulator-5556 shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)"
  [[ "$completed" == "1" ]] && break
  sleep 3
done
if [[ "$completed" != "1" ]]; then
  echo "Second emulator did not boot" >&2
  tail -n 100 "$OUT/emulator-peer2.log" >&2
  exit 1
fi
adb devices | tee "$OUT/adb-devices.txt"
for serial in emulator-5554 emulator-5556; do
  adb -s "$serial" shell ip -f inet addr show wlan0 | tee "$OUT/$serial-wifi.txt" || true
  adb -s "$serial" install -r "$APK"
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.POST_NOTIFICATIONS || true
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.RECORD_AUDIO || true
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.CAMERA || true
  adb -s "$serial" shell am start -W -n com.example.lan_messenger/.MainActivity
done
echo "Shared virtual Wi-Fi addresses:"
python3 - "$OUT" <<'PY'
import ipaddress, pathlib, re, sys
folder = pathlib.Path(sys.argv[1])
ips=[]
for serial in ["emulator-5554", "emulator-5556"]:
    text=(folder / (serial+"-wifi.txt")).read_text()
    found=re.search(r'\binet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)', text)
    if not found: raise SystemExit(f"{serial} has no active wlan0 IPv4 address")
    ips.append(ipaddress.ip_address(found.group(1)))
print("Cloud virtual network IPv4s:", *(str(i) for i in ips))
if ips[0] == ips[1]:
    raise SystemExit("Emulators do not have unique virtual Wi-Fi IPs")
PY
# Do not invent a successful discovery result: poll Flutter's real on-device
# accessibility hierarchy for a peer row. Preserve the XML + screenshots.
success=0
for attempt in $(seq 1 10); do
  sleep 8
  both=1
  for serial in emulator-5554 emulator-5556; do
    if ! adb -s "$serial" shell pidof com.example.lan_messenger >/dev/null; then
      echo "$serial app process exited unexpectedly"
      exit 1
    fi
    adb -s "$serial" shell uiautomator dump /sdcard/lan_smoke.xml >/dev/null 2>&1 || true
    adb -s "$serial" exec-out cat /sdcard/lan_smoke.xml >"$OUT/$serial-hierarchy.xml" 2>/dev/null || true
    adb -s "$serial" exec-out screencap -p >"$OUT/$serial-screen.png" 2>/dev/null || true
    if ! python3 - "$OUT/$serial-hierarchy.xml" <<'PY'
import pathlib, sys, xml.etree.ElementTree as ET
try:
    root=ET.parse(sys.argv[1]).getroot()
    displayed=" ".join((n.attrib.get("text","")+" "+n.attrib.get("content-desc",""))
        for n in root.iter("node"))
    assert "Online" in displayed and "Looking for nearby devices" not in displayed
except Exception:
    sys.exit(1)
PY
    then both=0; fi
  done
  if [[ "$both" == "1" ]]; then success=1; break; fi
done
for serial in emulator-5554 emulator-5556; do
  adb -s "$serial" logcat -d -t 3000 >"$OUT/$serial-logcat.txt" 2>/dev/null || true
done
if [[ "$success" == 1 ]]; then
  echo "PASS: both Android apps discovered a reachable online peer on shared cloud Wi-Fi."
  echo "Android two-emulator LAN discovery: PASS. This is not a live call test." >>"$GITHUB_STEP_SUMMARY"
else
  echo "FAIL: both Android apps did not confirm a peer row in accessible UI."
  echo "Review saved hierarchy XML, screenshots, and logcat evidence for discovery or UI/accessibility limitations."
  echo "Android two-emulator LAN discovery: NOT CONFIRMED." >>"$GITHUB_STEP_SUMMARY"
  exit 1
fi
