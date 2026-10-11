#!/bin/sh
# RENT-0723: deterministic synthetic race through the REAL rental payment API.
# Tests held money lock on duplicate and an intervening real rival payment
# between original lease read and writer lock. No customer/hardware records.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rent-0723-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_now() { printf '123456'; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf 'rent0723-%s' "$$"; }
bp_sha256() { sha256sum | cut -d' ' -f1; }
race_trigger=0
bp_cfg() {
  [ "$1" = rental_seconds_per_pulse ] || { printf ''; return 0; }
  if [ "$race_trigger" = 1 ]; then
    # This runs in the outer bp_cfg command-substitution subprocess, with
    # fresh outer event absent and BEFORE the outer writer lock is acquired.
    # The rival uses the actual bp_rental_apply_coin money mutation.
    race_trigger=0 bp_rental_apply_coin dev01 rivalCtrl rivalNonce rivalTarget 2 > /dev/null || return 74
  fi
  printf 600
}
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t0\tFixture Rental\t0\n' > "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
[ -f "$BP_RENTAL_EVENTS" ] || { echo 'RENT-0723 missing fixture receipt store' >&2; exit 1; }
lease_of() { bp_rental_device_line dev01 | cut -f3; }
rival_event="r:$(printf 'rental|%s|%s|%s' rivalCtrl rivalNonce rivalTarget | bp_sha256)"
outer_event="r:$(printf 'rental|%s|%s|%s' firstCtrl firstNonce firstTarget | bp_sha256)"
receipt_count() { awk -F '\t' -v e="$1" '$1==e {n++} END {print n+0}' "$BP_RENTAL_EVENTS"; }
# Before the RENT-0723 change the outer operation used the stale 0 lease and
# could overwrite a legitimate rival 2-pulse credit with only 1 pulse.
race_trigger=1
set +e
output="$(bp_rental_apply_coin dev01 firstCtrl firstNonce firstTarget 1)"
rc=$?
set -e
race_trigger=0
[ "$rc" -ne 0 ] && [ -z "$output" ] || {
  echo 'RENT-0723 P0 FAIL: stale outer rental request acknowledged' >&2;exit 1;
}
[ "$(lease_of)" = 124656 ] &&
[ "$(receipt_count "$rival_event")" -eq 1 ] &&
[ "$(receipt_count "$outer_event")" -eq 0 ] || {
  echo 'RENT-0723 P0 FAIL: lost rival seconds or duplicated outer receipt' >&2;exit 1;
}
[ ! -e "$BP_STATE/paid-state-uncertain" ] || {
  echo 'RENT-0723 FAIL: safe unmodified race was improperly quarantined' >&2; exit 1;
}
# The global paid writer lock must also block an existing receipt's ACK.
exec 7>"$BP_RUN/paid-financial.lock"
flock -n 7
set +e
blocked="$(bp_rental_apply_coin dev01 rivalCtrl rivalNonce rivalTarget 2)"
blocked_rc=$?
set -e
[ "$blocked_rc" -ne 0 ] && [ -z "$blocked" ] || {
  echo 'RENT-0723 P0 FAIL: replay ACK leaked while paid transaction lock held' >&2;exit 1;
}
flock -u 7
exec 7>&-
[ "$(receipt_count "$rival_event")" -eq 1 ] || exit 1
[ "$(lease_of)" = 124656 ] || exit 1
# Replaying an actually committed receipt succeeds once writer lock is free.
dupe="$(bp_rental_apply_coin dev01 rivalCtrl rivalNonce rivalTarget 2)"
[ "$dupe" = "$(printf 'duplicate\t124656')" ] || exit 1
[ "$(receipt_count "$rival_event")" -eq 1 ] || exit 1
# The outer call can now retry and add on top of the rival's actual lease.
fresh="$(bp_rental_apply_coin dev01 firstCtrl firstNonce firstTarget 1)"
[ "$fresh" = "$(printf 'credited\t125256')" ] || exit 1
[ "$(lease_of)" = 125256 ] &&
[ "$(receipt_count "$rival_event")" -eq 1 ] &&
[ "$(receipt_count "$outer_event")" -eq 1 ] || {
  echo 'RENT-0723 P0 FAIL: paid time conservation or unique receipt' >&2;exit 1;
}
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq 2 ] || exit 1
[ ! -e "$BP_STATE/paid-state-uncertain" ] || exit 1
echo 'RENT-0723 PASS: real rental writer rejects stale lease and no signed replay ACK while global paid lock held'
echo 'NOT ATOMIC: lease and receipt still separately written; issue #32 and physical powercut acceptance OPEN'
