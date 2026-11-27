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
awk -v want="$ROOT" -v scratch="$SCRATCH" -v source="$SOURCE" \
  -f "$PARSER" /proc/self/mountinfo || fail 'scratch backing not proven by kernel mount table'
echo 'STORCHK-0674: operator must independently verify that source is dedicated, disposable physical storage.'
echo 'STORCHK-0674: no destructive action executed; paid_v1_migration_authorized=0'
