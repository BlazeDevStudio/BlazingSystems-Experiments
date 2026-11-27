#!/bin/sh
# RENT-0724: deterministic stale-admin-lease race at the shared paid lock.
# Synthetic /tmp only; no customer devices, credentials or paid state.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rental-admin-race-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
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
lease() { awk -F '\t' '$1=="dev01" {print $3}' "$BP_RENTAL_DEVICES"; }
countkind() { awk -F '\t' -v k="$1" '$5==k {n++} END {print n+0}' "$BP_RENTAL_EVENTS"; }
reject_rc() {
  want="$1"; shift
  set +e
  "$@" >"$T/out" 2>"$T/err"; got=$?
  set -e
  [ "$got" -eq "$want" ] && [ ! -s "$T/out" ] || {
    echo "RENT-0724 false financial ACK or wrong denial: expected $want got $got ($*)" >&2
    exit 1
  }
}
# A separate legitimate payment can finish after admin's read lock and
# before admin obtains the WRITER lock. Simulate only this exact gap.
bp_paid_begin() {
  bp_rental_device_write dev01 fake-secret "$competing_lease" 'Synthetic Device' 0 || return 8
  exec 6>"$BP_RUN/paid-financial.lock" || return 8
  flock -n 6 || return 8
  printf 'PENDING\t123456\n' >"$BP_PAID_UNCERTAIN" || return 8
}
competing_lease=130000
[ "$(bp_rental_lease_add dev01 600)" = 130600 ] || {
  echo 'RENT-0724 admin lease add lost newly paid time' >&2; exit 1;
}
[ "$(lease)" = 130600 ]
[ "$(countkind lease_add)" -eq 1 ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
# An ordinary expire click saw already-expired lease=120000, but a coin
# extended it to 130000 during lock handoff: reject without forfeiting it.
bp_rental_device_write dev01 fake-secret 120000 'Synthetic Device' 0
competing_lease=130000
before_events="$(sha256sum "$BP_RENTAL_EVENTS")"
reject_rc 6 bp_rental_lease_expire dev01
[ "$(lease)" = 130000 ]
[ "$before_events" = "$(sha256sum "$BP_RENTAL_EVENTS")" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
# Even explicit forfeiture was approved for the originally observed lease.
# If a new payment extends it during the writer handoff, the confirmation
# becomes stale and must not erase the later customer's credit.
bp_rental_device_write dev01 fake-secret 130000 'Synthetic Device' 0
competing_lease=130600
reject_rc 6 bp_rental_lease_expire dev01 CONFIRM_FORFEIT
[ "$(lease)" = 130600 ]
[ "$before_events" = "$(sha256sum "$BP_RENTAL_EVENTS")" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
# If the competing writer created a value too close to signed-32-bit max,
# reject AFTER lock but clear only our own unmodified pending marker.
bp_rental_device_write dev01 fake-secret 120000 'Synthetic Device' 0
competing_lease=2147483640
reject_rc 8 bp_rental_lease_add dev01 600
[ "$(lease)" = 2147483640 ]
[ "$before_events" = "$(sha256sum "$BP_RENTAL_EVENTS")" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
# Re-source the ordinary lock implementation for preflight, denial and
# successful explicitly confirmed forfeiture.
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf 123456; }
bp_rental_device_write dev01 fake-secret 130000 'Synthetic Device' 0
before_state="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
reject_rc 6 bp_rental_lease_expire dev01
[ "$before_state" = "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
[ "$(bp_rental_lease_expire dev01 CONFIRM_FORFEIT)" = 123456 ]
[ "$(lease)" = 123456 ]
[ "$(countkind expire)" -eq 1 ]
grep -Fq 'confirmed_forfeit_seconds:6544' "$BP_RENTAL_EVENTS"
# Invalid amount and overflow are blocked BEFORE placing a pending marker.
before_state="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
reject_rc 2 bp_rental_lease_add dev01 0008
bp_rental_device_write dev01 fake-secret 2147483640 'Synthetic Device' 0
reject_rc 8 bp_rental_lease_add dev01 600
[ ! -e "$BP_PAID_UNCERTAIN" ]
[ "$(countkind lease_add)" -eq 1 ]
# A writer owning the financial lock BEFORE it creates a pending marker
# must block both administrative changes without false success.
exec 7>"$BP_RUN/paid-financial.lock"
flock -n 7 || exit 1
reject_rc 8 bp_rental_lease_add dev01 600
reject_rc 8 bp_rental_lease_expire dev01 CONFIRM_FORFEIT
flock -u 7; exec 7>&-
[ ! -e "$BP_PAID_UNCERTAIN" ]
# A failure after actually replacing a lease retains quarantine; NEVER
# reuse the read-only-refusal marker cleanup for a partial money write.
bp_rental_device_write dev01 fake-secret 123456 'Synthetic Device' 0
bp_rental_event_log() { return 8; }
reject_rc 8 bp_rental_lease_add dev01 600
[ "$(lease)" = 124056 ]
[ -f "$BP_PAID_UNCERTAIN" ]
echo 'RENT-0724 PASS: admin add/expire revalidate under paid writer lock, preserve competing credit and forfeit intent, cleanup read-only reject, retain partial-write quarantine'
echo 'NOT CRASH ATOMIC: v1 rental lease and receipt still commit separately; P0 #32/#43/#34 customer migration denied'
