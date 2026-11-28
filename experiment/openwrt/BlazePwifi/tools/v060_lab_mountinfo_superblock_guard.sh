#!/bin/sh
# STORCHK-0674 regression: both mount and superblock options must be rw.
# Synthetic mountinfo only; never mounts, writes, power-cycles or certifies.
set -eu
HERE="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
AWK="$HERE/v060_lab_mountinfo_guard.awk"
[ -s "$AWK" ] || { echo 'missing mountinfo guard' >&2; exit 1; }
TEMP="$(mktemp -d /tmp/blaze-v2-superblock-guard-XXXXXX)"
trap 'rm -rf "$TEMP"' EXIT HUP INT TERM
WANT=/tmp/blaze-v2-native-test01
SCRATCH=/mnt/blaze-v2-lab-media-test01
SOURCE=/dev/sdb1
cat > "$TEMP/good" <<'MOUNTINFO'
1 0 8:1 / / rw,relatime - ext4 /dev/sda1 rw,data=ordered
2 1 8:2 / /overlay rw,relatime - ext4 /dev/sda2 rw,data=ordered
3 1 31:0 / /rom ro,relatime - squashfs /dev/mtdblock0 ro
4 1 8:3 / /boot rw,relatime - vfat /dev/sda3 rw,fmask=0022
20 1 8:17 / /mnt/blaze-v2-lab-media-test01 rw,relatime - ext4 /dev/sdb1 rw,data=ordered
21 1 8:17 /fixture /tmp/blaze-v2-native-test01 rw,relatime - ext4 /dev/sdb1 rw,data=ordered
MOUNTINFO
check_ok() {
  awk -v want="$WANT" -v scratch="$SCRATCH" -v source="$SOURCE" -f "$AWK" "$1" > "$TEMP/out" 2> "$TEMP/err" || {
    cat "$TEMP/err" >&2; echo "unexpected safe fixture rejection: $2" >&2; exit 1;
  }
  grep -Fqx 'superblock_rw_verified=1' "$TEMP/out"
  grep -Fqx 'physical_powercut_verified=0' "$TEMP/out"
  grep -Fqx 'customer_install_authorized=0' "$TEMP/out"
}
check_bad() {
  if awk -v want="$WANT" -v scratch="$SCRATCH" -v source="$SOURCE" -f "$AWK" "$1" > "$TEMP/out" 2> "$TEMP/err"; then
    echo "unsafe synthetic mount accepted: $2" >&2
    exit 1
  fi
  grep -Fq 'STORCHK-0674 BLOCKED' "$TEMP/err" || {
    echo "unsafe case lacked explicit refusal: $2" >&2; exit 1;
  }
  [ ! -s "$TEMP/out" ] || {
    echo "unsafe case emitted success fields: $2" >&2; exit 1;
  }
}
check_ok "$TEMP/good" 'writable mount and superblock options'
# RED baseline: these keep per-mount flags rw while the actual backing
# superblock is ro. The previous parser accepted both cases.
sed '/\/mnt\/blaze-v2-lab-media-test01/s# /dev/sdb1 rw,data=ordered$# /dev/sdb1 ro,data=ordered#' "$TEMP/good" > "$TEMP/ro-scratch-super"
check_bad "$TEMP/ro-scratch-super" 'read-only scratch superblock under rw mount flags'
sed '/\/tmp\/blaze-v2-native-test01/s# /dev/sdb1 rw,data=ordered$# /dev/sdb1 ro,data=ordered#' "$TEMP/good" > "$TEMP/ro-target-super"
check_bad "$TEMP/ro-target-super" 'read-only fixture superblock under rw mount flags'
# Existing per-mount read-only defense remains active.
sed '/\/tmp\/blaze-v2-native-test01/s/rw,relatime/ro,relatime/' "$TEMP/good" > "$TEMP/ro-target-mount"
check_bad "$TEMP/ro-target-mount" 'read-only target mount options'
sed '/\/mnt\/blaze-v2-lab-media-test01/s/rw,relatime/ro,relatime/' "$TEMP/good" > "$TEMP/ro-scratch-mount"
check_bad "$TEMP/ro-scratch-mount" 'read-only scratch mount options'
echo 'STORCHK-0674 SUPERBLOCK GUARD PASS: writable positive control accepted; read-only target/scratch superblocks and mount options rejected'
echo 'SIMULATED_ONLY=1; PHYSICAL_POWER_CUT_VERIFIED=0; CUSTOMER_INSTALL_AUTHORIZED=0'
