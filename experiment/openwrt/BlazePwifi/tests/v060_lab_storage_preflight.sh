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
1 0 8:1 / / rw,relatime - ext4 /dev/sda1 rw
2 1 8:2 / /overlay rw,relatime - ext4 /dev/sda2 rw
3 1 31:0 / /rom ro,relatime - squashfs /dev/mtdblock0 ro
4 1 8:3 / /boot rw,relatime - vfat /dev/sda3 rw
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
sed 's/8:17/8:1/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'scratch reuses root filesystem block device'
sed 's/8:17/8:2/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'scratch reuses /overlay block device'
sed 's/8:17/31:0/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'scratch reuses /rom block device'
sed 's/8:17/8:3/g' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'scratch reuses /boot block device'
awk '$5 != "/"' "$TEMP/good" > "$TEMP/bad"
check_bad "$TEMP/bad" 'missing root mount identity'
sed '1s/ - ext4 / - overlay /' "$TEMP/good" | awk '$5 != "/overlay"' > "$TEMP/bad"
check_bad "$TEMP/bad" 'overlay root without separately identified upper storage'
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
sed '/\/tmp\/blaze-v2-native-test01/s/rw,relatime/ro,relatime/' "$TEMP/good" > "$TEMP/bad"
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
echo 'STORCHK-0674 PASS: mountinfo parser rejects root/overlay/rom/boot device reuse plus tmpfs/system/loop/ambiguous/wrong-device/restricted path; no mounts or paid writes'
echo 'LAB ONLY: software preflight is NOT physical power-loss durability'

# STORCHK-0674 follow-up: partitions on the same physical parent are not isolated.
PARENT_GUARD="$BASE/tools/v060_lab_block_parent_guard.sh"
SYSFS="$TEMP/sys"
mkdir -p "$SYSFS/dev/block" "$SYSFS/devices/pci/block/sda" "$SYSFS/devices/pci/block/sdb" "$SYSFS/devices/virtual/block/dm-0/slaves"
make_disk() {
  disk="$1"; mm="$2"
  mkdir -p "$SYSFS/devices/pci/block/$disk"
  printf '%s\\n' "$mm" > "$SYSFS/devices/pci/block/$disk/dev"
  ln -s "../../devices/pci/block/$disk" "$SYSFS/dev/block/$mm"
}
make_partition() {
  disk="$1"; part="$2"; mm="$3"
  mkdir -p "$SYSFS/devices/pci/block/$disk/$part"
  printf '%s\\n' "$mm" > "$SYSFS/devices/pci/block/$disk/$part/dev"
  printf '1\\n' > "$SYSFS/devices/pci/block/$disk/$part/partition"
  ln -s "../../devices/pci/block/$disk/$part" "$SYSFS/dev/block/$mm"
}
make_disk sda 8:0
make_disk sdb 8:16
make_partition sda sda1 8:1
make_partition sda sda2 8:2
make_partition sda sda3 8:3
make_partition sda sda4 8:4
make_partition sdb sdb1 8:17
printf '253:0\\n' > "$SYSFS/devices/virtual/block/dm-0/dev"
ln -s ../../../../pci/block/sda/sda2 "$SYSFS/devices/virtual/block/dm-0/slaves/sda2"
ln -s ../../devices/virtual/block/dm-0 "$SYSFS/dev/block/253:0"
[ -s "$PARENT_GUARD" ] || { echo 'missing STORCHK-0674 physical-parent guard' >&2; exit 1; }
sh -n "$PARENT_GUARD"
check_parent_ok() {
  scratch_mm="$1"; root_mm="$2"; overlay_mm="$3"; boot_mm="$4"; root_fs="$5"; label="$6"
  sh "$PARENT_GUARD" "$SYSFS" "$scratch_mm" "$root_mm" "$overlay_mm" "$boot_mm" "$root_fs" > "$TEMP/parent-out" 2> "$TEMP/parent-err" || {
    cat "$TEMP/parent-err" >&2; echo "unexpected physical-parent rejection: $label" >&2; exit 1;
  }
  grep -Fqx 'physical_parent_separation_verified=1' "$TEMP/parent-out"
}
check_parent_bad() {
  scratch_mm="$1"; root_mm="$2"; overlay_mm="$3"; boot_mm="$4"; root_fs="$5"; label="$6"
  if sh "$PARENT_GUARD" "$SYSFS" "$scratch_mm" "$root_mm" "$overlay_mm" "$boot_mm" "$root_fs" > "$TEMP/parent-out" 2> "$TEMP/parent-err"; then
    echo "unsafe physical-parent layout accepted: $label" >&2
    exit 1
  fi
  grep -Fq 'STORCHK-0674 BLOCKED' "$TEMP/parent-err" || {
    echo "physical-parent failure lacked explicit fail-closed status: $label" >&2; exit 1;
  }
  [ ! -s "$TEMP/parent-out" ] || { echo "unsafe physical-parent layout emitted success: $label" >&2; exit 1; }
}
check_parent_ok 8:17 8:1 8:2 8:3 ext4 'separate physical scratch disk'
check_parent_bad 8:4 8:1 8:2 8:3 ext4 'scratch sibling partition shares root physical disk'
check_parent_bad 8:0 8:1 8:2 8:3 ext4 'scratch is the same whole disk as protected mounts'
check_parent_bad 253:0 8:1 8:2 8:3 ext4 'device-mapper topology is unsupported'
check_parent_bad 8:99 8:1 8:2 8:3 ext4 'scratch sysfs identity is missing'
check_parent_ok 8:17 0:42 8:2 8:3 overlay 'overlay root is checked through its upper storage'
check_parent_bad 8:4 0:42 8:2 8:3 overlay 'scratch shares overlay upper physical disk'
echo 'STORCHK-0674 PHYSICAL-PARENT RED/GREEN MATRIX PASS: sibling partitions, whole-disk reuse, mapper ambiguity and missing sysfs identity fail closed'
