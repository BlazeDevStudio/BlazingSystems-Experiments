#!/bin/sh
# RENT-0646: real rental lease writer under disposable faulted filesystem.
# No customers, enrollments, actual rental phone, secret or payment gateway.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rental-db-XXXXXX)"
# Stage-aware failure is essential for silent set -e assertion failures;
# this contains only fictional /tmp test secrets, never production keys.
trap 'rc=$?; if [ "$rc" -ne 0 ]; then
  printf "RENT-0646 failure at stage=%s rc=%s\\n" "${stage:-bootstrap}" "$rc" >&2
  [ ! -f "$T/failure" ] || cat "$T/failure" >&2
fi
rm -rf "$T"' EXIT
trap 'exit 1' HUP INT TERM
stage=bootstrap
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
entry() { printf '%s\t%s\t%s\tSynthetic Phone\t1000\n' "$1" "$2" "$3"; }
entry dev01 fixture-private-token-A 123456 > "$BP_RENTAL_DEVICES"
entry dev02 fixture-private-token-B 654321 >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
checksum() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }
lease() { awk -F '\t' -v d="$1" '$1==d {print $3;exit}' "$BP_RENTAL_DEVICES"; }
update() { bp_rental_device_write dev01 fixture-private-token-A 124056 "Synthetic Phone" 1010; }
reject() {
  before="$(checksum)"
  set +e
  update > "$T/failure" 2>&1
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "rental unsafe write accepted at stage $stage rc=$rc" >&2; exit 1; }
  [ "$(checksum)" = "$before" ] || {
    echo "failed lease write lost another paid device" >&2;exit 1;
  }
}
update
[ "$(lease dev01)" = 124056 ] && [ "$(lease dev02)" = 654321 ]
cp -p "$BP_RENTAL_DEVICES" "$T/good"
stage=duplicate-unrelated
entry dev02 fixture-private-token-B 654321 >> "$BP_RENTAL_DEVICES"
reject
cp -p "$T/good" "$BP_RENTAL_DEVICES"
stage=duplicate-target
entry dev01 fixture-private-token-A 124056 >> "$BP_RENTAL_DEVICES"
reject
cp -p "$T/good" "$BP_RENTAL_DEVICES"
stage=malformed-record
printf 'broken\tlease\n' >> "$BP_RENTAL_DEVICES"
reject
cp -p "$T/good" "$BP_RENTAL_DEVICES"
stage=non-numeric-lease
entry dev03 fixture-private-token-C incorrect >> "$BP_RENTAL_DEVICES"
reject
cp -p "$T/good" "$BP_RENTAL_DEVICES"

# Fault shim must be active: clear the POSIX shell command lookup cache.
cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
if [ "${FAULT_AWK:-}" = partial ]; then
  printf 'dev01\ttruncated\t5\tSynthetic Phone\t1000\n'
  exit 74
fi
exec /usr/bin/awk "$@"
AWK
chmod 700 "$T/bin/awk"
hash -r 2>/dev/null || true
[ "$(command -v awk)" = "$T/bin/awk" ]
export FAULT_AWK=partial
stage=failed-partial-copy
reject
unset FAULT_AWK
[ "$(lease dev02)" = 654321 ]

cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
stage=rename-I-O-failure
reject
[ "$(lease dev02)" = 654321 ]
# Simulate an authenticated operator lease mutation under the real financial
# quarantine lock. A late failed device rename must never ACK or clear marker.
bp_paid_begin
set +e
update >"$T/failure" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ]
bp_paid_abort
[ -f "$BP_PAID_UNCERTAIN" ]
set +e
bp_paid_begin > "$T/failure" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] && [ "$(lease dev02)" = 654321 ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true
# Synthetic-only reset of an invented uncertainty marker for more tests.
rm "$BP_PAID_UNCERTAIN"

stage=symlink-source
mv "$BP_RENTAL_DEVICES" "$T/privately-saved"
ln -s "$T/privately-saved" "$BP_RENTAL_DEVICES"
set +e
update > "$T/failure" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ]
[ "$(awk -F '\t' '$1=="dev02" {print $3;exit}' "$T/privately-saved")" = 654321 ]
rm "$BP_RENTAL_DEVICES"
mv "$T/privately-saved" "$BP_RENTAL_DEVICES"

stage=secret-pollution
before="$(checksum)"
polluted="$(printf 'SECRET\nOTHER')"
set +e
bp_rental_device_write dev01 "$polluted" 124056 "Synthetic" 1010 > "$T/failure" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] && [ "$(checksum)" = "$before" ]
# Real authenticated/admin and rented-client CGI call sites must not suppress
# a failed write. The admin path must acquire paid-state quarantine.
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
CLIENT="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
stage=admin-source-contract
# The admin lease-set now locks account state before reading the previous
# balance and uses an explicit paid-begin/checked audit/paid-commit block.
# Do NOT require obsolete single-line syntax from the weaker implementation.
grep -Fq 'bp_lock || bp_fail "accounting busy"' "$ADMIN"
grep -Fq 'bp_paid_begin || {' "$ADMIN"
grep -Fq 'if ! bp_paid_commit; then' "$ADMIN"
grep -Fq 'rental lease sync uncertain; operator reconciliation required' "$ADMIN"
grep -Fq 'bp_rental_event_log lease_set "$did"' "$ADMIN"
# Phone heartbeat is only presence data now: the status CGI must NEVER
# re-write the authoritative paid lease row from an old snapshot.
grep -Fq 'bp_rental_seen_update "$did" "$now"' "$CLIENT"
grep -Fq 'rental presence update failed; retry status' "$CLIENT"
! grep -Fq 'bp_rental_device_write "$did" "$secret" "${lease:-0}" "$label" "$now"' "$CLIENT"

echo 'RENT-0646 PASS: paid rental leases survive duplicate/corrupt/partial copy, failed rename, source symlink and secret pollution; quarantined operator lease never false-ACKs'
echo 'NOT PRODUCTION: real source lease/receipt still separate TSV files; v2 signed journal, source migration, Android owner signing and physical powercut remain P0'
