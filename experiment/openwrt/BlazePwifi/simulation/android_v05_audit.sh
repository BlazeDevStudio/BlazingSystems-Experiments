#!/bin/bash
set -euo pipefail

APK="${1:?usage: android_v05_audit.sh /path/to/BlazeRental-current-ci.apk [output-dir]}"
OUT="${2:-android-v05-audit}"
PKG="com.blazesystems.blazerental.debug"
ADMIN="$PKG/com.blazesystems.blazerental.BlazeDeviceAdminReceiver"
HOME_COMPONENT="$PKG/com.google.android.apps.nexuslauncher.NexusLauncherActivity"
mkdir -p "$OUT"

fail(){ echo "ANDROID_V05_FAIL: $*" >&2; adb logcat -d >"$OUT/logcat.txt" 2>/dev/null||true; exit 1; }
screen_size(){ adb shell wm size | sed -n 's/.*Physical size: \([0-9]*\)x\([0-9]*\).*/\1 \2/p' | tail -n1; }
dump_ui(){
 local n="$1" ok=0
 for i in 1 2 3 4 5; do
  adb shell uiautomator dump --compressed /sdcard/blaze.xml >"$OUT/$n-uiautomator.txt" 2>&1 || true
  adb exec-out cat /sdcard/blaze.xml >"$OUT/$n.xml" 2>/dev/null || true
  grep -q '<?xml' "$OUT/$n.xml" && { ok=1; break; }
  sleep 1
 done
 adb exec-out screencap -p >"$OUT/$n.png" 2>/dev/null||true
 [ "$ok" = 1 ] || fail "UI dump failed: $n"
}
has(){ grep -Fq "$2" "$1"; }
assert_has(){ has "$1" "$2" || fail "UI missing '$2' in $1"; }
assert_not(){ ! has "$1" "$2" || fail "UI unexpectedly contains '$2' in $1"; }
xy_text(){
 python3 - "$1" "$2" <<'PY'
import re,sys,xml.etree.ElementTree as ET
raw=open(sys.argv[1],encoding='utf-8',errors='ignore').read(); raw=raw[raw.find('<?xml'):]
root=ET.fromstring(raw); needle=sys.argv[2]
for n in root.iter('node'):
    if n.get('text')==needle or needle in (n.get('text') or ''):
        m=re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]',n.get('bounds',''))
        if m:
            a,b,c,d=map(int,m.groups()); print((a+c)//2,(b+d)//2); raise SystemExit
raise SystemExit(2)
PY
}
tap_text(){ local xy; xy="$(xy_text "$1" "$2")"||fail "cannot locate '$2'"; adb shell input tap $xy; sleep 1; }
long_text(){ local xy; xy="$(xy_text "$1" "$2")"||fail "cannot locate '$2'"; adb shell input swipe $xy $xy "${3:-4500}"; sleep 1; }
scroll_find(){
 local base="$1" text="$2"; read -r w h <<<"$(screen_size)"
 for i in 0 1 2 3 4 5 6; do
  dump_ui "$base-$i"
  if has "$OUT/$base-$i.xml" "$text"; then echo "$OUT/$base-$i.xml"; return 0; fi
  adb shell input swipe $((w/2)) $((h*4/5)) $((w/2)) $((h/3)) 350; sleep .5
 done
 return 1
}

adb wait-for-device
adb install -r -t "$APK" >/dev/null
EXPECTED_VERSION="$(cat "$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)/VERSION")"
INSTALLED_VERSION="$(adb shell dumpsys package "$PKG" | sed -n 's/.*versionName=//p' | head -n1 | tr -d '\r')"
[ "$INSTALLED_VERSION" = "$EXPECTED_VERSION" ] || fail "installed version $INSTALLED_VERSION does not match VERSION $EXPECTED_VERSION"
adb logcat -c || true

adb shell dpm set-device-owner "$ADMIN" >"$OUT/device-owner.txt" 2>&1 || { cat "$OUT/device-owner.txt"; fail "Device Owner provisioning failed"; }
grep -Eqi 'Success|Active admin set' "$OUT/device-owner.txt" || fail "Device Owner not confirmed"

timeout 20 adb shell am start -n "$HOME_COMPONENT" >"$OUT/home-start.txt" 2>&1 || true
sleep 4
dump_ui 01-locked
assert_has "$OUT/01-locked.xml" "BLAZERENTAL"
assert_has "$OUT/01-locked.xml" "00:00:00"
assert_has "$OUT/01-locked.xml" "INSERT COIN"

# Unpaid: vertical All Apps gesture and horizontal escape must remain contained.
read -r w h <<<"$(screen_size)"
adb shell input swipe $((w/2)) $((h*4/5)) $((w/2)) $((h/4)) 400; sleep 1
dump_ui 02-unpaid-drawer
assert_has "$OUT/02-unpaid-drawer.xml" "BLAZERENTAL"
assert_not "$OUT/02-unpaid-drawer.xml" "Search apps"

adb shell input swipe $((w*4/5)) $((h/2)) $((w/5)) $((h/2)) 400; sleep 1
dump_ui 03-unpaid-horizontal
assert_has "$OUT/03-unpaid-horizontal.xml" "BLAZERENTAL"

# Secret timer opens native setup.
long_text "$OUT/03-unpaid-horizontal.xml" "00:00:00" 4500
dump_ui 04-admin
assert_has "$OUT/04-admin.xml" "BlazeRental Initial Setup"

# Establish local administrator password. The initial-setup layout keeps
# this field above the fold; verify and tap the exact visible EditText instead
# of scrolling the page away from it.
PFILE="$OUT/04-admin.xml"
assert_has "$PFILE" "Create local admin password"
tap_text "$PFILE" "Create local admin password"
adb shell input text 'BlazeTest123'
adb shell input keyevent 4
sleep .5
dump_ui 05b-password-ready
PFILE="$OUT/05b-password-ready.xml"
if ! has "$PFILE" "SET ADMIN PASSWORD"; then PFILE="$(scroll_find 05c-password-button 'SET ADMIN PASSWORD')" || fail "password button missing"; fi
tap_text "$PFILE" "SET ADMIN PASSWORD"
sleep 1

# v0.5 must allow daily-driver setup without BlazePwifi enrollment.
# showInitialSetup() returns to the top after saving the local password, so the
# daily-driver control is intentionally above the fold. Verify it in place
# instead of scrolling away from a visible button.
dump_ui 06-daily-driver
DFILE="$OUT/06-daily-driver.xml"
assert_has "$DFILE" "USE DEVICE AS IS"
tap_text "$DFILE" "USE DEVICE AS IS"
sleep 4
adb shell input keyevent 3
sleep 2
dump_ui 07-normal-home
assert_not "$OUT/07-normal-home.xml" "TIME FINISHED"

# Normal All Apps must work in unrestricted mode.
adb shell input swipe $((w/2)) $((h*4/5)) $((w/2)) $((h/4)) 420; sleep 1
dump_ui 08-app-drawer
assert_has "$OUT/08-app-drawer.xml" "Search apps"

# Return Home, then swipe right into the custom-left Blaze area.
adb shell input keyevent 3; sleep 1
adb shell input swipe $((w/6)) $((h/2)) $((w*5/6)) $((h/2)) 420; sleep 1
dump_ui 09-notifications
assert_has "$OUT/09-notifications.xml" "NOTIFICATIONS"
assert_has "$OUT/09-notifications.xml" "CLEAR ALL"

# One more right swipe reaches far-left BlazeRental page.
adb shell input swipe $((w/6)) $((h/2)) $((w*5/6)) $((h/2)) 420; sleep 1
dump_ui 10-rental-left
assert_has "$OUT/10-rental-left.xml" "BLAZERENTAL"

# Device Owner uninstall defense remains active.
set +e
UNINSTALL="$(adb uninstall "$PKG" 2>&1)"; RC=$?
set -e
printf '%s\n' "$UNINSTALL" >"$OUT/uninstall-defense.txt"
if [ "$RC" -eq 0 ] && printf '%s' "$UNINSTALL" | grep -q '^Success'; then fail "Device Owner unexpectedly uninstallable"; fi

adb shell dumpsys device_policy >"$OUT/device-policy.txt" || true
grep -Fq "$PKG" "$OUT/device-policy.txt" || fail "Device Owner missing"
adb logcat -d >"$OUT/logcat.txt"
! grep -E 'FATAL EXCEPTION|AndroidRuntime.*Process: com\.blazesystems\.blazerental' "$OUT/logcat.txt" || fail "BlazeRental crashed"

python3 - "$OUT/audit.json" "$EXPECTED_VERSION" <<'PY'
import json,sys
json.dump({"target":"android-emulator","release":sys.argv[2],"validation_level":"emulator-device-owner-ui","checks":{
"blaze_gate_locked":True,"unpaid_drawer_blocked":True,"unpaid_home_escape_blocked":True,
"secret_admin":True,"daily_driver_without_enrollment":True,"normal_home_preserved":True,
"all_apps_unrestricted":True,"notifications_adjacent":True,"clear_all_notifications":True,
"far_left_rental_page":True,"device_owner":True,"ordinary_uninstall_blocked":True,"no_fatal_crash":True}},open(sys.argv[1],"w"),indent=2)
PY
echo "Android $EXPECTED_VERSION emulator audit passed"
