#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
L="$ROOT/android/BlazeRentalLauncher"
GRADLE="$L/build.gradle"
MANIFEST="$L/AndroidManifest.xml"
SRC="$L/src/com/blazesystems/blazerental"
ADMIN="$SRC/BlazeAdminActivity.java"
ALARM="$SRC/RentalAlarmConfig.java"
PLAYER="$SRC/BlazeAlarmPlayer.java"
RECEIVER="$SRC/RentalAlarmReceiver.java"
LCM_PNG="$L/res/drawable-nodpi/blaze_lcm_brand.png"

case "$(cat "$ROOT/VERSION")" in
  0.5.2)
    grep -Fq 'versionCode 50200' "$GRADLE"
    grep -Fq 'versionName "0.5.2"' "$GRADLE"
    ;;
  0.5.3-dev.1)
    grep -Fq 'versionCode 50290' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.1"' "$GRADLE"
    ;;
  0.5.3-dev.2)
    grep -Fq 'versionCode 50291' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.2"' "$GRADLE"
    ;;
  0.5.3-dev.3)
    grep -Fq 'versionCode 50292' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.3"' "$GRADLE"
    ;;
  0.5.3-dev.4)
    grep -Fq 'versionCode 50293' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.4"' "$GRADLE"
    ;;
  0.5.3-dev.5)
    grep -Fq 'versionCode 50294' "$GRADLE"
    grep -Fq 'versionName "0.5.3-dev.5"' "$GRADLE"
    ;;
  *) exit 1 ;;
esac
grep -Fq 'android:icon="@drawable/blaze_lcm_brand"' "$MANIFEST"
grep -Fq 'android.permission.MODIFY_AUDIO_SETTINGS' "$MANIFEST"
grep -Fq 'android.permission.ACCESS_NOTIFICATION_POLICY' "$MANIFEST"
grep -Fq 'android.permission.WAKE_LOCK' "$MANIFEST"
test -s "$LCM_PNG"
python3 - "$LCM_PNG" <<'PY'
import struct, sys, zlib
p=sys.argv[1]
data=open(p,'rb').read()
assert data[:8] == b'\x89PNG\r\n\x1a\n'
off=8
seen_iend=False
while off < len(data):
    assert off + 12 <= len(data)
    n=struct.unpack('>I', data[off:off+4])[0]
    typ=data[off+4:off+8]
    end=off+12+n
    assert end <= len(data)
    body=data[off+4:off+8+n]
    crc=struct.unpack('>I', data[off+8+n:end])[0]
    assert (zlib.crc32(body) & 0xffffffff) == crc
    off=end
    if typ == b'IEND':
        seen_iend=True
        break
assert seen_iend and off == len(data)
PY
test -s "$ALARM"
test -s "$PLAYER"
grep -Fq 'def = kind == KIND_URGENT ? 180L : 600L' "$ALARM"
grep -Fq 'kind == KIND_URGENT ? 10L : kind == KIND_TIME_UP ? 15L : 5L' "$ALARM"
grep -Fq 'Math.max(25, Math.min(100, value))' "$ALARM"
grep -Fq 'STREAM_ALARM' "$PLAYER"
grep -Fq 'startVolumeGuard' "$PLAYER"
grep -Fq 'setInterruptionFilter' "$PLAYER"
grep -Fq 'KIND_TIME_UP' "$RECEIVER"
grep -Fq 'wasTriggered' "$RECEIVER"
grep -Fq 'leaseUntilMs' "$RECEIVER"
grep -Fq 'Rental time alarms' "$ADMIN"
grep -Fq 'GRANT DND ALARM OVERRIDE' "$ADMIN"
grep -Fq 'RingtoneManager.ACTION_RINGTONE_PICKER' "$ADMIN"
grep -Fq 'RingtoneManager.EXTRA_RINGTONE_SHOW_SILENT, false' "$ADMIN"
grep -Fq 'Intent.ACTION_OPEN_DOCUMENT' "$ADMIN"
grep -Fq 'appVersionName()' "$ADMIN"
echo "v0.5.2 inherited BlazeRental branding/alarm contracts passed"
