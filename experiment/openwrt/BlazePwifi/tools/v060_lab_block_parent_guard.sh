#!/bin/sh
# STORCHK-0674 baseline identity guard. Follow-up tests require physical-parent isolation.
set -eu
[ "$#" -eq 6 ] || { echo 'STORCHK-0674 BLOCKED: invalid physical-parent arguments' >&2; exit 9; }
SYSFS_ROOT="$1"; SCRATCH="$2"; ROOT="$3"; OVERLAY="$4"; BOOT="$5"; ROOT_FS="$6"
[ -d "$SYSFS_ROOT/dev/block" ] || { echo 'STORCHK-0674 BLOCKED: sysfs block index unavailable' >&2; exit 9; }
for id in "$SCRATCH" "$ROOT" "$OVERLAY" "$BOOT"; do
  case "$id" in -) continue ;; *[!0-9:]*|:*|*:) echo 'STORCHK-0674 BLOCKED: invalid major:minor identity' >&2; exit 9 ;; esac
done
[ "$SCRATCH" != "$ROOT" ] || { echo 'STORCHK-0674 BLOCKED: scratch reuses root device' >&2; exit 9; }
[ "$SCRATCH" != "$OVERLAY" ] || { echo 'STORCHK-0674 BLOCKED: scratch reuses overlay device' >&2; exit 9; }
[ "$SCRATCH" != "$BOOT" ] || { echo 'STORCHK-0674 BLOCKED: scratch reuses boot device' >&2; exit 9; }
printf '%s\\n' 'physical_parent_separation_verified=1'
