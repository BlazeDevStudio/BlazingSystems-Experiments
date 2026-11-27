#!/bin/sh
# STORCHK-0674 negative-first synthetic /proc/self/mountinfo contract test.
# Never mounts/disks or creates a fixture for real power-cut use.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
AWK="$BASE/tools/v060_lab_mountinfo_guard.awk"
WRAP="$BASE/tools/v060_lab_storage_preflight.sh"
[ -s "$AWK" ] && [ -s "$WRAP" ] || exit 1
sh -n "$WRAP"
TEMP="$(mktemp -d /tmp/blaze-v2-storage-preflight-XXXXXX)"
trap 'rm -rf "$TEMP"' EXIT HUP INT TERM
WANT=/tmp/blaze-v2-native-test01
SCRATCH=/mnt/blaze-v2-lab-media-test01
SOURCE=/dev/sdb1
cat > "$TEMP/good" <<'MOUNTINFO'
20 1 8:17 / /mnt/blaze-v2-lab-media-test01 rw,relatime - ext4 /dev/sdb1 rw
21 1 8:17 /fixture /tmp/blaze-v2-native-test01 rw,relatime - ext4 /dev/sdb1 rw
MOUNTINFO
check_ok() {
  awk -v want="$WANT" -v scratch="$SCRATCH" -v source="$SOURCE" -f "$AWK" "$1" > "$TEMP/out" 2>"$TEMP/err" || {
    cat "$TEMP/err" >&2; echo "unexpected safe fixture rejection: $2" >&2; exit 1;
  }
  grep -Fqx 'physical_powercut_verified=0' "$TEMP/out"
  grep -Fqx 'customer_install_authorized=0' "$TEMP/out"
}
check_bad() {
  if awk -v want="$WANT" -v scratch="$SCRATCH" -v source="$SOURCE" -f "$AWK" "$1" > "$TEMP/out" 2>"$TEMP/err"; then
    echo "unsafe synthetic mount accepted: $2" >&2
    exit 1
  fi
  grep -Fq 'STORCHK-0674 BLOCKED' "$TEMP/err" || {
    echo "unsafe case lacked clear block status: $2" >&2; exit 1;
  }
  [ ! -s "$TEMP/out" ] || {
    echo "unsafe case printed success fields: $2" >&2; exit 1;
  }
}
check_ok "$TEMP/good" 'explicit persistent scratch bind'
# All negative cases must fail CLOSED. Inputs are plain-text synthetic mount
# tables and have no actual mount privileges or storage effects.
sed 's/ - ext4 / - tmpfs /g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'tmpfs'
sed 's/\/dev\/sdb1/\/dev\/loop0/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'loop source'
sed 's/\/dev\/sdb1/\/dev\/root/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'system root source'
sed 's/\/dev\/sdb1/\/dev\/sdc1/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'wrong expected physical source'
sed 's#/fixture /tmp/blaze#/ /tmp/blaze#' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'bound entire storage volume instead of isolated directory'
sed 's# /mnt/blaze-v2-lab-media-test01 # /overlay #g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'missing approved scratch root'
sed 's# /mnt/blaze-v2-lab-media-test01 # / #g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'customer filesystem root'
sed '2s/rw,relatime/ro,relatime/' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'read-only target mount'
sed 's# /fixture /tmp/blaze-v2-native-test01 # /fixture /tmp/blaze-v2-native-OTHER #g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'unmounted generic tmp path'
cat "$TEMP/good" "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'stacked / duplicate mount points'
sed 's/ - ext4 / - overlay /g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'overlay is not dedicated scratch'
# Input validation: invalid operator paths and devices are rejected.
if awk -v want=/etc -v scratch="$SCRATCH" -v source="$SOURCE" -f "$AWK" "$TEMP/good" > "$TEMP/out" 2>"$TEMP/err"; then
  echo 'unsafe /etc fixture requested and accepted' >&2; exit 1
fi
if awk -v want="$WANT" -v scratch="$SCRATCH" -v source=/dev/loop0 -f "$AWK" "$TEMP/good" > "$TEMP/out" 2>"$TEMP/err"; then
  echo 'loopback source accepted' >&2; exit 1
fi
# Wrapper itself must never accept a missing marker or arbitrary live path.
if sh "$WRAP" /etc /dev/sdb1 "$SCRATCH" > "$TEMP/out" 2>"$TEMP/err"; then
  echo 'wrapper accepted /etc as paid scratch fixture' >&2; exit 1
fi
[ ! -s "$TEMP/out" ] || { echo 'unsafe wrapper emitted success' >&2; exit 1; }
echo 'STORCHK-0674 PASS: mountinfo parser rejects tmpfs/system/root/overlay/loop/ambiguous/wrong-device/restricted path; no mounts or paid writes'
echo 'LAB ONLY: software preflight is NOT physical power-loss durability'
