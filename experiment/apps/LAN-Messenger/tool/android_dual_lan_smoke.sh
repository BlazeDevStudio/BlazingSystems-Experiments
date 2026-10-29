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
  -no-snapshot -no-boot-anim -camera-front emulated >"$OUT/emulator-peer2.log" 2>&1 &
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
  # Wait for netsim Wi-Fi DHCP; simultaneous cloud AVDs can boot before IPv4.
  for wifi_try in $(seq 1 25); do
    adb -s "$serial" shell ip -f inet addr show wlan0 >"$OUT/$serial-wifi.txt" 2>/dev/null || true
    if grep -Eq 'inet ([0-9]+\.){3}[0-9]+/' "$OUT/$serial-wifi.txt"; then break; fi
    if [[ "$wifi_try" == 5 ]]; then adb -s "$serial" shell svc wifi enable || true; fi
    sleep 2
  done
  cat "$OUT/$serial-wifi.txt"
  adb -s "$serial" install -r "$APK"
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.POST_NOTIFICATIONS || true
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.RECORD_AUDIO || true
  adb -s "$serial" shell pm grant com.example.lan_messenger android.permission.CAMERA || true
  adb -s "$serial" shell appops set com.example.lan_messenger PICTURE_IN_PICTURE allow || true
  # Exercise the duplicate-overlay bug with native draw-over-apps explicitly
  # granted on disposable test emulators (not the user's phone).
  adb -s "$serial" shell appops set com.example.lan_messenger SYSTEM_ALERT_WINDOW allow || true
  # The app requests opt-in background service battery exemption on startup.
  # First-run Android Settings can steal focus and hide the peer list entirely.
  # Grant the exemption in this disposable emulator, not in production builds.
  adb -s "$serial" shell cmd deviceidle whitelist +com.example.lan_messenger || true
  adb -s "$serial" shell am start -W -n com.example.lan_messenger/.MainActivity
  sleep 3
  resumed="$(adb -s "$serial" shell dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity' | head -2 || true)"
  echo "$serial resumed activities: $resumed"
  if echo "$resumed" | grep -q 'com.android.settings'; then
    echo "Dismissing temporary Android battery-optimization request on $serial"
    adb -s "$serial" shell input keyevent KEYCODE_BACK || true
    adb -s "$serial" shell am start -W -n com.example.lan_messenger/.MainActivity
  fi
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
    # A failed cloud runner previously trapped Pixel Launcher ANR *over* an
    # already-online Messenger peer row. BACK left the launcher dialog in place
    # for all ten polls. Close ONLY the named system launcher ANR by locating
    # its exact "Close app" button in UiAutomator's real XML coordinates.
    # No discovery acceptance is credited until the peer row is visible again.
    if grep -Fq "Pixel Launcher isn't responding" "$OUT/$serial-hierarchy.xml"; then
      coords="$(python3 "$ROOT/experiment/apps/LAN-Messenger/tool/emulator_launcher_anr.py" \
          "$OUT/$serial-hierarchy.xml" || true)"
      if [[ "$coords" =~ ^[0-9]+[[:space:]][0-9]+$ ]]; then
        read -r close_x close_y <<<"$coords"
        echo "$serial: closing obstructing Pixel Launcher ANR via system button"
        adb -s "$serial" shell input tap "$close_x" "$close_y" || true
        adb -s "$serial" shell am start -n com.example.lan_messenger/.MainActivity || true
      else
        echo "$serial: launcher dialog found but safe Close app target unavailable"
      fi
      both=0
      continue
    fi
    if [[ "$attempt" == 1 || "$attempt" == 10 ]]; then
      python3 - "$OUT/$serial-hierarchy.xml" "$serial" <<'PYINFO'
import sys, xml.etree.ElementTree as ET
try:
    root=ET.parse(sys.argv[1]).getroot()
    labels=[(node.attrib.get("text","") + " " + node.attrib.get("content-desc","")).strip()
            for node in root.iter("node")]
    print(sys.argv[2], "visible UI labels:", [x for x in labels if x][:25])
except Exception as error:
    print(sys.argv[2], "UI hierarchy unreadable:", error)
PYINFO
    fi
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
