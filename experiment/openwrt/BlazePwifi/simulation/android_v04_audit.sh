#!/bin/bash
set -euo pipefail

APK="${1:?usage: android_v04_audit.sh /path/to/BlazeRental-v0.4.0-ci.apk [output-dir]}"
OUT="${2:-android-v04-audit}"
PKG="com.blazesystems.blazerental.debug"
ADMIN="$PKG/com.blazesystems.blazerental.BlazeDeviceAdminReceiver"
LAUNCHER_COMPONENT="$PKG/com.google.android.apps.nexuslauncher.NexusLauncherActivity"

mkdir -p "$OUT"
ADB=(adb)

fail() {
  echo "ANDROID_V04_FAIL: $*" >&2
  adb logcat -d > "$OUT/logcat.txt" 2>/dev/null || true
  exit 1
}

dump_ui() {
  local name="$1" ok=0 attempt
  : > "$OUT/$name.xml"
  for attempt in 1 2 3 4 5; do
    if adb shell uiautomator dump --compressed /sdcard/blaze-window.xml >"$OUT/$name-uiautomator.txt" 2>&1; then
      adb exec-out cat /sdcard/blaze-window.xml > "$OUT/$name.xml" 2>/dev/null || true
      if grep -q '<?xml' "$OUT/$name.xml"; then
        ok=1
        break
      fi
    fi
    sleep 1
  done
  adb exec-out screencap -p > "$OUT/$name.png" 2>/dev/null || true
  [ "$ok" -eq 1 ] || fail "could not capture Android UI hierarchy for $name"
}

assert_ui() {
  local file="$1" needle="$2"
  grep -Fq "$needle" "$file" || fail "UI missing '$needle' in $file"
}

ui_has_exact() {
  local file="$1" needle="$2"
  python3 - "$file" "$needle" <<'PY'
import sys,xml.etree.ElementTree as ET
path, needle=sys.argv[1],sys.argv[2]
raw=open(path,'rb').read().decode('utf-8','ignore')
start=raw.find('<?xml')
if start > 0: raw=raw[start:]
root=ET.fromstring(raw)
if not any(node.attrib.get('text') == needle for node in root.iter('node')):
    raise SystemExit(1)
PY
}

assert_ui_exact() {
  ui_has_exact "$1" "$2" || fail "UI missing exact node '$2' in $1"
}

# Keep each hierarchy and screenshot so a missing/off-screen control remains
# diagnosable. Search is bounded and requires the real, exact runtime label.
scroll_to_exact() {
  local name="$1" needle="$2" attempt w h
  read -r w h <<<"$(screen_size)"
  for attempt in 0 1 2 3 4 5 6; do
    dump_ui "$name-$attempt"
    if ui_has_exact "$OUT/$name-$attempt.xml" "$needle"; then
      return 0
    fi
    if [ "$attempt" -lt 6 ]; then
      adb shell input swipe $((w/2)) $((h*4/5)) $((w/2)) $((h/3)) 420
      sleep 1
    fi
  done
  fail "UI missing exact node '$needle' after bounded scrolling ($name)"
}

screen_size() {
  adb shell wm size | sed -n 's/.*Physical size: \([0-9]*\)x\([0-9]*\).*/\1 \2/p' | tail -n1
}

swipe_page() {
  local xml="$1" heading="$2" direction="$3" w h y from to
  read -r w h <<<"$(screen_size)"
  # The headline is below the nav overlay and above the secret timer. Derive
  # its actual position rather than swiping through a navigation button.
  y="$(python3 - "$xml" "$heading" <<'PY'
import re,sys,xml.etree.ElementTree as ET
raw=open(sys.argv[1],encoding='utf-8').read()
root=ET.fromstring(raw[raw.find('<?xml'):])
for node in root.iter('node'):
    if node.get('text') == sys.argv[2]:
        bounds=list(map(int,re.findall(r'\d+',node.get('bounds',''))))
        if len(bounds) == 4 and bounds[3] > bounds[1]:
            print((bounds[1]+bounds[3])//2)
            raise SystemExit(0)
raise SystemExit(1)
PY
)" || fail "cannot locate swipe headline '$heading'"
  from=$((w*9/10)); to=$((w/10))
  if [ "$direction" = right ]; then from=$((w/10)); to=$((w*9/10)); fi
  adb shell input swipe "$from" "$y" "$to" "$y" 320
  sleep 1
}

swipe_drawer_up() {
  read -r w h <<<"$(screen_size)"
  adb shell input swipe $((w/2)) $((h*4/5)) $((w/2)) $((h/4)) 420
  sleep 1
}

tap_text() {
  local xml="$1" text="$2"
  local xy
  xy="$(python3 - "$xml" "$text" <<'PY'
import re,sys,xml.etree.ElementTree as ET
path, needle=sys.argv[1],sys.argv[2]
raw=open(path,'rb').read().decode('utf-8','ignore')
start=raw.find('<?xml')
if start > 0: raw=raw[start:]
root=ET.fromstring(raw)
for node in root.iter('node'):
    if node.attrib.get('text') == needle:
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            print((x1+x2)//2,(y1+y2)//2)
            raise SystemExit(0)
raise SystemExit(2)
PY
)" || fail "cannot locate UI node '$text'"
  read -r x y <<<"$xy"
  adb shell input tap "$x" "$y"
  sleep 1
}

long_press_text() {
  local xml="$1" text="$2" duration="${3:-4500}"
  local xy
  xy="$(python3 - "$xml" "$text" <<'PY'
import re,sys,xml.etree.ElementTree as ET
path, needle=sys.argv[1],sys.argv[2]
raw=open(path,'rb').read().decode('utf-8','ignore')
start=raw.find('<?xml')
if start > 0: raw=raw[start:]
root=ET.fromstring(raw)
for node in root.iter('node'):
    if node.attrib.get('text') == needle:
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',node.attrib.get('bounds',''))
        if m:
            x1,y1,x2,y2=map(int,m.groups())
            print((x1+x2)//2,(y1+y2)//2)
            raise SystemExit(0)
raise SystemExit(2)
PY
)" || fail "cannot locate UI node '$text'"
  read -r x y <<<"$xy"
  adb shell input swipe "$x" "$y" "$x" "$y" "$duration"
  sleep 1
}

echo "Installing candidate APK: $APK"
adb wait-for-device
adb install -r -t "$APK" >/dev/null
adb logcat -c || true

# A fresh emulator without accounts can promote the debug candidate to Device Owner.
if ! adb shell dpm set-device-owner "$ADMIN" >"$OUT/device-owner.txt" 2>&1; then
  cat "$OUT/device-owner.txt" >&2
  fail "could not set Device Owner on clean emulator"
fi
grep -Eqi 'Success|Active admin set' "$OUT/device-owner.txt" || fail "Device Owner command did not report success"

set +e
timeout 20 adb shell am start -n "$LAUNCHER_COMPONENT" >"$OUT/home-launch.txt" 2>&1
HOME_RC=$?
set -e
# Old Android launchers can leave `am start -W` waiting indefinitely even after
# HOME is visible. Treat timeout as acceptable only if the activity really becomes active.
if [ "$HOME_RC" -ne 0 ] && [ "$HOME_RC" -ne 124 ]; then
  cat "$OUT/home-launch.txt" >&2 || true
  fail "HOME launch command failed"
fi
sleep 4
adb shell dumpsys activity activities > "$OUT/activity-after-home.txt" 2>/dev/null || true
grep -Fq "$LAUNCHER_COMPONENT" "$OUT/activity-after-home.txt" \
  || grep -Fq "com.google.android.apps.nexuslauncher.NexusLauncherActivity" "$OUT/activity-after-home.txt" \
  || fail "Launcher3 HOME activity did not become active"

dump_ui "01-rental-page"
assert_ui_exact "$OUT/01-rental-page.xml" "BLAZERENTAL"
assert_ui "$OUT/01-rental-page.xml" "TIME FINISHED"
assert_ui "$OUT/01-rental-page.xml" "INSERT COIN"

# Unpaid drawer gesture must not transition into All Apps.
swipe_drawer_up
dump_ui "02-unpaid-drawer-block"
assert_ui "$OUT/02-unpaid-drawer-block.xml" "INSERT COIN"

# Exercise gestures independently of the button fallback, including both ends.
swipe_page "$OUT/02-unpaid-drawer-block.xml" "BLAZERENTAL" right
dump_ui "02a-rental-boundary"
assert_ui_exact "$OUT/02a-rental-boundary.xml" "BLAZERENTAL"
swipe_page "$OUT/02a-rental-boundary.xml" "BLAZERENTAL" left
dump_ui "02b-swipe-quick"
assert_ui_exact "$OUT/02b-swipe-quick.xml" "QUICK CONTROLS"
swipe_page "$OUT/02b-swipe-quick.xml" "QUICK CONTROLS" left
dump_ui "02c-swipe-notifications"
assert_ui_exact "$OUT/02c-swipe-notifications.xml" "NOTIFICATIONS"
swipe_page "$OUT/02c-swipe-notifications.xml" "NOTIFICATIONS" left
dump_ui "02d-notifications-boundary"
assert_ui_exact "$OUT/02d-notifications-boundary.xml" "NOTIFICATIONS"
swipe_page "$OUT/02d-notifications-boundary.xml" "NOTIFICATIONS" right
dump_ui "02e-swipe-quick-return"
assert_ui_exact "$OUT/02e-swipe-quick-return.xml" "QUICK CONTROLS"
swipe_page "$OUT/02e-swipe-quick-return.xml" "QUICK CONTROLS" right
dump_ui "02f-swipe-rental-return"
assert_ui_exact "$OUT/02f-swipe-rental-return.xml" "BLAZERENTAL"

# Page 2: safe controls only. Rental Mode supports swipe paging, plus
# explicit compact navigation buttons for old launchers/touch stacks where a
# full-page child consumes synthetic or edge-case gestures.
tap_text "$OUT/02f-swipe-rental-return.xml" "QUICK CONTROLS >"
dump_ui "03-quick-controls"
assert_ui_exact "$OUT/03-quick-controls.xml" "QUICK CONTROLS"
assert_ui "$OUT/03-quick-controls.xml" "BLUETOOTH"
assert_ui "$OUT/03-quick-controls.xml" "FLASHLIGHT"

# UIAutomator only exposes currently visible ScrollView descendants on this
# old API level. Verify the below-the-fold floating timer control at source
# level, while keeping the emulator flow on stable visible controls.
PAGE_SOURCE="experiment/openwrt/BlazePwifi/android/BlazeRentalLauncher/src/com/blazesystems/blazerental/RentalSystemPages.java"
grep -Fq '"FLOATING TIMER: ON"' "$PAGE_SOURCE" || fail "floating timer ON control missing from RentalSystemPages"
grep -Fq '"FLOATING TIMER: OFF"' "$PAGE_SOURCE" || fail "floating timer OFF control missing from RentalSystemPages"

# Page 3: notification mirror replaces notification shade.
tap_text "$OUT/03-quick-controls.xml" "NOTIFICATIONS >"
dump_ui "04-notifications"
assert_ui_exact "$OUT/04-notifications.xml" "NOTIFICATIONS"

# Return to Page 1 through the same guaranteed navigation fallback and open
# the secret native admin via the timer long-press.
tap_text "$OUT/04-notifications.xml" "< QUICK CONTROLS"
dump_ui "04b-quick-controls-return"
tap_text "$OUT/04b-quick-controls-return.xml" "< RENTAL"
dump_ui "05-before-admin"
assert_ui "$OUT/05-before-admin.xml" "00:00:00"
long_press_text "$OUT/05-before-admin.xml" "00:00:00" 4500
dump_ui "06-initial-admin"
assert_ui "$OUT/06-initial-admin.xml" "BlazeRental Initial Setup"
scroll_to_exact "06a-enrollment-qr" "SCAN BLAZEPWIFI ENROLLMENT QR"
scroll_to_exact "06b-uninstall-defence" "3 · Uninstall defence"

# Device Owner must protect the production package from ordinary uninstall.
set +e
UNINSTALL="$(adb uninstall "$PKG" 2>&1)"
UNINSTALL_RC=$?
set -e
printf '%s\n' "$UNINSTALL" > "$OUT/uninstall-defense.txt"
if [ "$UNINSTALL_RC" -eq 0 ] && printf '%s' "$UNINSTALL" | grep -q '^Success'; then
  fail "Device Owner package was unexpectedly uninstallable"
fi
printf '%s' "$UNINSTALL" | grep -Eqi 'Failure|DELETE_FAILED|device policy|owner'   || fail "uninstall defense did not return a protected failure"

adb shell dumpsys device_policy > "$OUT/device-policy.txt" || true
grep -Fq "$PKG" "$OUT/device-policy.txt" || fail "Device Owner absent from dumpsys"

adb logcat -d > "$OUT/logcat.txt"
if grep -E 'FATAL EXCEPTION|AndroidRuntime.*Process: com\.blazesystems\.blazerental' "$OUT/logcat.txt"; then
  fail "BlazeRental crashed during emulator flow"
fi

python3 - "$OUT/audit.json" <<'PY'
import json,sys
json.dump({
  "target":"android-emulator",
  "release":"0.4.0",
  "validation_level":"emulator-device-owner-ui",
  "checks":{
    "launcher3_home":True,
    "fixed_rental_page":True,
    "unpaid_drawer_blocked":True,
    "quick_controls_page":True,
    "notifications_page":True,
    "swipe_navigation_both_directions":True,
    "swipe_endpoints_clamped":True,
    "secret_timer_admin":True,
    "initial_setup":True,
    "device_owner":True,
    "ordinary_uninstall_blocked":True,
    "no_fatal_crash":True
  }
},open(sys.argv[1],"w"),indent=2)
PY

echo "Android v0.4 emulator audit passed"
