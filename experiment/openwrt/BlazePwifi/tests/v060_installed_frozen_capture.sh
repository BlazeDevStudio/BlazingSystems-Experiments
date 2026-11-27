#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
CAPTURE="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2_frozen_capture.sh"
[ -f "$CAPTURE" ] || { echo 'FAIL: installed frozen capture command missing' >&2; exit 1; }
sh -n "$CAPTURE"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run" BP_SNAPSHOT_ROOT="$T/captures"
mkdir -p "$BP_STATE/targets" "$BP_RUN" "$BP_SNAPSHOT_ROOT" "$T/bin"
: > "$BP_RUN/paid-financial.lock"
printf 'FROZEN\t1700000000\n' > "$BP_STATE/paid-v2-cutover-intent"
printf 'a:b\t20\t1800000000\t0\t0\t0\t\t\tp:old-receipt\n' > "$BP_STATE/accounts.tsv"
printf 'm:old\t1700000000\tmember1\tadd\t20\t20\tVendo1\t1\n' > "$BP_STATE/member-events.tsv"
printf 'r:old\ta:b\t20\t1700000000\tp:1\n' > "$BP_STATE/rental-events.tsv"
printf 'PENDING\t2\n' > "$BP_STATE/targets/Vendo1.progress"
chmod 0600 "$BP_STATE/accounts.tsv"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"

reject() {
  if sh "$CAPTURE" --capture --operator-quiesced > "$T/out" 2>&1; then
    echo "FAIL: $1 admitted" >&2; exit 1
  fi
  grep -q 'paid_ack_authorized=0; migration_authorized=0' "$T/out" || { cat "$T/out" >&2; exit 1; }
  [ "$before" = "$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)" ] || {
    echo "FAIL: $1 changed v1 financial source" >&2; exit 1;
  }
}

if sh "$CAPTURE" > "$T/out" 2>&1; then echo 'FAIL: implicit capture' >&2; exit 1; fi
rm "$BP_STATE/paid-v2-cutover-intent"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject missing_freeze
printf 'FROZEN\t1700000000\n' > "$BP_STATE/paid-v2-cutover-intent"
touch "$BP_STATE/paid-state-uncertain"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject uncertain_money
rm "$BP_STATE/paid-state-uncertain"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
exec 9<>"$BP_RUN/paid-financial.lock"
flock -n 9
reject active_writer
flock -u 9
exec 9>&-
ln -s accounts.tsv "$BP_STATE/linked-money"
reject symlink_source
rm "$BP_STATE/linked-money"
BP_SNAPSHOT_ROOT="$BP_STATE/captures" reject recursive_destination
ln -s "$BP_SNAPSHOT_ROOT" "$T/link-captures"
BP_SNAPSHOT_ROOT="$T/link-captures" reject symlink_destination
rm "$T/link-captures"

# A tar process can exit zero despite omitting a financial file. The
# archive itself may checksum correctly, but it is not a complete recovery.
real_tar="$(command -v tar)"
printf '#!/bin/sh\nif [ "$1" = "-cf" ]; then\n  exec "%s" --exclude=./accounts.tsv -cf "$2" -C "$4" .\nfi\nexec "%s" "$@"\n' "$real_tar" "$real_tar" > "$T/bin/tar"
chmod +x "$T/bin/tar"
PATH="$T/bin:$PATH" reject silently_missing_account
grep -q 'archive_file_mismatch' "$T/out" || { cat "$T/out" >&2; exit 1; }
[ -d "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp" ] || exit 1
[ ! -e "$BP_SNAPSHOT_ROOT/v1-frozen-snapshot" ] || exit 1
rm -rf "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp"
rm "$T/bin/tar"

# Empty financial-state directories must also be captured; a checksum of
# the incomplete tar and an unchanged file-only manifest are insufficient.
mkdir "$BP_STATE/targets/empty-state"
printf '#!/bin/sh\nif [ "$1" = "-cf" ]; then\n  exec "%s" --exclude=./targets/empty-state -cf "$2" -C "$4" .\nfi\nexec "%s" "$@"\n' "$real_tar" "$real_tar" > "$T/bin/tar"
chmod +x "$T/bin/tar"
PATH="$T/bin:$PATH" reject silently_missing_empty_directory
grep -q 'archive_directory_mismatch' "$T/out" || { cat "$T/out" >&2; exit 1; }
[ -d "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp" ] || exit 1
[ ! -e "$BP_SNAPSHOT_ROOT/v1-frozen-snapshot" ] || exit 1
rm -rf "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp"
rm "$T/bin/tar"
rmdir "$BP_STATE/targets/empty-state"

# A checksum-perfect archive can still have unsafe recovery metadata:
# a successful tar may change an account to world-readable. Reject it even
# when all original file bytes and directory names are present.
printf '#!/bin/sh\nif [ "$1" = "-cf" ]; then\n  stage="$(mktemp -d)" || exit 1\n  "%s" -cf "$2" -C "$4" . || exit 1\n  "%s" -xf "$2" -C "$stage" || exit 1\n  chmod 0777 "$stage/accounts.tsv" || exit 1\n  "%s" -cf "$2" -C "$stage" . || exit 1\n  rm -rf "$stage" || exit 1\n  exit 0\nfi\nexec "%s" "$@"\n' "$real_tar" "$real_tar" "$real_tar" "$real_tar" > "$T/bin/tar"
chmod +x "$T/bin/tar"
PATH="$T/bin:$PATH" reject silently_weakened_account_permissions
grep -q 'archive_metadata_mismatch' "$T/out" || { cat "$T/out" >&2; exit 1; }
[ "$(stat -c '%a' "$BP_STATE/accounts.tsv")" = 600 ] || exit 1
[ -d "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp" ] || exit 1
[ ! -e "$BP_SNAPSHOT_ROOT/v1-frozen-snapshot" ] || exit 1
rm -rf "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp"
rm "$T/bin/tar"

# A short write or sync failure leaves an incomplete capture and no success.
printf '#!/bin/sh\nprintf partial > "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp/state.tar"\nexit 1\n' > "$T/bin/tar"
chmod +x "$T/bin/tar"
PATH="$T/bin:$PATH" reject partial_archive
[ -d "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp" ] || exit 1
[ ! -e "$BP_SNAPSHOT_ROOT/v1-frozen-snapshot" ] || exit 1
rm -rf "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp"
rm "$T/bin/tar"
printf '#!/bin/sh\nexit 1\n' > "$T/bin/sync"
chmod +x "$T/bin/sync"
PATH="$T/bin:$PATH" reject sync_failure
[ -d "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp" ] || exit 1
[ ! -e "$BP_SNAPSHOT_ROOT/v1-frozen-snapshot" ] || exit 1
rm -rf "$BP_SNAPSHOT_ROOT/.v1-frozen-capture.tmp"
rm "$T/bin/sync"

# Simulate a lost response: the committed capture must remain and a retry
# must never overwrite it or acknowledge a new migration.
sh "$CAPTURE" --capture --operator-quiesced > /dev/null
final="$BP_SNAPSHOT_ROOT/v1-frozen-snapshot"
[ -d "$final" ] && [ ! -L "$final" ] || exit 1
(cd "$final" && sha256sum -c SHA256SUMS) > "$T/verify"
tar -xOf "$final/state.tar" ./accounts.tsv | cmp - "$BP_STATE/accounts.tsv"
tar -xOf "$final/state.tar" ./member-events.tsv | cmp - "$BP_STATE/member-events.tsv"
tar -xOf "$final/state.tar" ./rental-events.tsv | cmp - "$BP_STATE/rental-events.tsv"
tar -xOf "$final/state.tar" ./targets/Vendo1.progress | cmp - "$BP_STATE/targets/Vendo1.progress"
reject lost_response_retry
printf 'corrupt' >> "$final/state.tar"
if (cd "$final" && sha256sum -c SHA256SUMS) > "$T/verify" 2>&1; then
  echo 'FAIL: corrupted archive verified' >&2; exit 1
fi
reject corrupt_existing_capture
[ "$before" = "$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)" ] || exit 1
echo 'PAY-0760 installed frozen capture: source receipts preserved, partial/replay/corrupt state denied'
