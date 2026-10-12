#!/bin/sh
# RENT-0723: synthetic concurrency at exact global financial lock boundaries.
# Never touches real devices, live leases, controllers, or customer databases.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rental-race-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf 123456; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t124000\tSynthetic Device\t0\n' >"$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
getlease() { awk -F '\t' '$1=="dev01" {print $3}' "$BP_RENTAL_DEVICES"; }
receiptcount() { awk -F '\t' -v e="$1" '$1==e {n++} END {print n+0}' "$BP_RENTAL_EVENTS"; }
assert_reject() {
  set +e
  "$@" >"$T/rejected" 2>&1; code=$?
  set -e
  [ "$code" -ne 0 ] || { echo "RENT-0723 false ACK: $*" >&2;exit 1; }
  [ ! -s "$T/rejected" ] || { echo "RENT-0723 unexpected success output" >&2;exit 1; }
}
first="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)"
[ "$first" = "$(printf 'credited\t124600')" ]
event1="r:$(printf 'rental|%s|%s|%s' controller01 nonce01 target01 | bp_sha256)"
[ "$(receiptcount "$event1")" -eq 1 ]
snapshot="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
[ "$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)" = "$(printf 'duplicate\t124600')" ]
[ "$snapshot" = "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ]
# An independent financial writer already owns the lock but might not
# have created its uncertainty marker yet. Do not ACK an old receipt.
exec 7>"$BP_RUN/paid-financial.lock"
flock -n 7 || exit 1
assert_reject bp_rental_apply_coin dev01 controller01 nonce01 target01 1
assert_reject bp_rental_apply_coin dev01 controller02 nonce02 target01 1
[ "$snapshot" = "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
flock -u 7
exec 7>&-
# A separate admin/consumer can win the gap between releasing the replay
# read lock and acquiring writer lock. Simulate a committed independent
# lease increase at that boundary and verify the current lease is RE-READ.
bp_paid_begin() {
  # In this deterministic race, another already-authorized operation
  # finished immediately before our normal paid writer acquisition.
  bp_rental_device_write dev01 fake-secret 130000 'Synthetic Device' 0 || return 8
  exec 6>"$BP_RUN/paid-financial.lock" || return 8
  flock -n 6 || return 8
  printf 'PENDING\t123456\n' >"$BP_PAID_UNCERTAIN" || return 8
}
second="$(bp_rental_apply_coin dev01 controller02 nonce02 target01 1)"
[ "$second" = "$(printf 'credited\t130600')" ] || {
  echo "RENT-0723 stale lease replaced independent paid time: $second" >&2;exit 1;
}
[ "$(getlease)" = 130600 ]
event2="r:$(printf 'rental|%s|%s|%s' controller02 nonce02 target01 | bp_sha256)"
[ "$(receiptcount "$event2")" -eq 1 ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
# Simulate the *same* receipt committed by another writer in the gap. The
# just-created pending marker is cleared only after checking exact identity.
bp_paid_begin() {
  event3="r:$(printf 'rental|%s|%s|%s' controller03 nonce03 target01 | bp_sha256)"
  bp_rental_device_write dev01 fake-secret 131200 'Synthetic Device' 0 || return 8
  bp_rental_append_paid_receipt "$event3" dev01 131200 123456 1 || return 8
  exec 6>"$BP_RUN/paid-financial.lock" || return 8
  flock -n 6 || return 8
  printf 'PENDING\t123456\n' >"$BP_PAID_UNCERTAIN" || return 8
}
third="$(bp_rental_apply_coin dev01 controller03 nonce03 target01 1)"
[ "$third" = "$(printf 'duplicate\t131200')" ] || {
  echo "RENT-0723 second ACK should reuse the concurrent receipt: $third" >&2;exit 1;
}
[ "$(getlease)" = 131200 ]
event3="r:$(printf 'rental|%s|%s|%s' controller03 nonce03 target01 | bp_sha256)"
[ "$(receiptcount "$event3")" -eq 1 ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
# Re-source original shared lock implementation before standard negative tests.
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf 123456; }
# Duplicate paid member row is an untrusted snapshot; no ACK.
cp "$BP_RENTAL_DEVICES" "$T/healthy-devices"
cat "$T/healthy-devices" >>"$BP_RENTAL_DEVICES"
assert_reject bp_rental_apply_coin dev01 controller01 nonce01 target01 1
cp "$T/healthy-devices" "$BP_RENTAL_DEVICES"
# Corrupt/duplicate receipt cannot justify a paid replay.
cp "$BP_RENTAL_EVENTS" "$T/healthy-events"
cat "$T/healthy-events" >>"$BP_RENTAL_EVENTS"
assert_reject bp_rental_apply_coin dev01 controller01 nonce01 target01 1
cp "$T/healthy-events" "$BP_RENTAL_EVENTS"
# A pending marker remains authoritative despite an older valid receipt.
printf 'PENDING\t123456\n' >"$BP_STATE/paid-state-uncertain"
assert_reject bp_rental_apply_coin dev01 controller01 nonce01 target01 1
rm -f "$BP_STATE/paid-state-uncertain"
echo 'RENT-0723 PASS: locked replay ACK, no lost updates across lock handoff, exact duplicate on concurrent commit, fail-closed corrupt/uncertain paid files'
echo 'NOT ATOMIC: v1 rental lease TSV and receipt still commit separately; target powercut and #32 production migration blocked'
