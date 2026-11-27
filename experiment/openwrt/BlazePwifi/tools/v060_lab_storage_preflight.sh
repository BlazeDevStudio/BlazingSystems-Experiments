#!/bin/sh
# STORCHK-0674 LAB-only, read-only fixture/persistent scratch mount preflight.
# Does NOT execute a payment, mount a device, power-cycle, or prove durability.
set -eu
[ "$#" -eq 3 ] || {
  echo 'Usage: v060_lab_storage_preflight.sh /tmp/blaze-v2-native-ID /dev/DEDICATED_SCRATCH_PARTITION /mnt/blaze-v2-lab-media-ID' >&2
  exit 2
}
ROOT="$1"; SOURCE="$2"; SCRATCH="$3"
SELF="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
PARSER="$SELF/v060_lab_mountinfo_guard.awk"
fail() { echo "STORCHK-0674 BLOCKED: $1; no power-cut authorization" >&2; exit 9; }
[ -r "$PARSER" ] || fail 'parser unavailable'
# Must be a real, private, non-symlink synthetic fixture owned by this user.
[ -d "$ROOT" ] && [ ! -L "$ROOT" ] || fail 'missing/symlink fixture directory'
[ "$(stat -c '%a' "$ROOT")" = 700 ] || fail 'fixture directory is not 0700'
[ "$(stat -c '%u' "$ROOT")" = "$(id -u)" ] || fail 'fixture has unexpected owner'
MARKER="$ROOT/.blaze-v2-fixture-only"
[ -f "$MARKER" ] && [ ! -L "$MARKER" ] || fail 'private synthetic marker missing'
[ "$(stat -c '%a' "$MARKER")" = 600 ] || fail 'synthetic marker is not 0600'
[ "$(stat -c '%h' "$MARKER")" = 1 ] || fail 'synthetic marker hardlinked'
[ "$(stat -c '%u' "$MARKER")" = "$(id -u)" ] || fail 'synthetic marker owner mismatch'
[ "$(cat "$MARKER")" = 'BLAZE-V2-SYNTHETIC-ONLY' ] || fail 'synthetic marker invalid'
# The REAL kernel mount table is the only source; no user-supplied override.
[ -r /proc/self/mountinfo ] || fail 'mountinfo unavailable'
PARENT_GUARD="$SELF/v060_lab_block_parent_guard.sh"
[ -r "$PARENT_GUARD" ] || fail 'physical-parent guard unavailable'
if ! MOUNT_GATE="$(awk -v want="$ROOT" -v scratch="$SCRATCH" -v source="$SOURCE" -f "$PARSER" /proc/self/mountinfo)"; then
  fail 'scratch backing not proven by kernel mount table'
fi
field() { printf '%s\n' "$MOUNT_GATE" | sed -n "s/^$1=//p" | sed -n '1p'; }
ROOT_DEVICE="$(field root_device)"
ROOT_FS="$(field root_fs)"
OVERLAY_DEVICE="$(field overlay_device)"
ROM_DEVICE="$(field rom_device)"
BOOT_DEVICE="$(field boot_device)"
SCRATCH_DEVICE="$(field scratch_device)"
[ -n "$ROOT_DEVICE" ] && [ -n "$ROOT_FS" ] && [ -n "$SCRATCH_DEVICE" ] || fail 'mountinfo identity fields incomplete'
[ -n "$OVERLAY_DEVICE" ] || OVERLAY_DEVICE=-
[ -n "$ROM_DEVICE" ] || ROM_DEVICE=-
[ -n "$BOOT_DEVICE" ] || BOOT_DEVICE=-
if ! PARENT_GATE="$(sh "$PARENT_GUARD" /sys "$SCRATCH_DEVICE" "$ROOT_DEVICE" "$OVERLAY_DEVICE" "$ROM_DEVICE" "$BOOT_DEVICE" "$ROOT_FS")"; then
  fail 'scratch physical-parent separation could not be proven'
fi
printf '%s\n' "$MOUNT_GATE" | sed -e '/^root_device=/d' -e '/^root_fs=/d' -e '/^overlay_device=/d' -e '/^rom_device=/d' -e '/^boot_device=/d' -e '/^scratch_device=/d'
printf '%s\n' "$PARENT_GATE"
echo 'STORCHK-0674: operator must independently verify that source is dedicated, disposable physical storage.'
echo 'STORCHK-0674: no destructive action executed; paid_v1_migration_authorized=0'
