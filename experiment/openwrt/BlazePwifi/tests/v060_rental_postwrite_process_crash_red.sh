#!/bin/sh
# RENT-20261022-ATOMIC/P0 #32. EXPECTED RED: v1 rental lease and paid receipt
# are separate files. Synthetic process death after lease rename, BEFORE receipt.
# This script NEVER reaches a router/coin acceptor/customer state.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if [ "${1:-}" = "--crash" ]; then
  T="${BP_RENT_ATOMIC_FIXTURE_ROOT:-}"
  case "$T" in /tmp/blaze-rent-postwrite-*) :;; *) echo "unsafe fixture root" >&2; exit 64;; esac
  [ -d "$T" ] && [ ! -L "$T" ] &&
    [ "$(cat "$T/.blaze-synthetic-only" 2>/dev/null)" = "BLAZE-SYNTHETIC-ONLY" ] || exit 64
else
  umask 077
  T="$(mktemp -d /tmp/blaze-rent-postwrite-XXXXXXXX)" || exit 1
  trap 'rm -rf "$T"' EXIT HUP INT TERM
  printf 'BLAZE-SYNTHETIC-ONLY\n' > "$T/.blaze-synthetic-only"
fi
BP_STATE="$T/state"; BP_RUN="$T/run"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_RENTAL_DEVICES BP_RENTAL_EVENTS
mkdir -p "$BP_STATE" "$BP_RUN"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf '600' || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
bp_tmp_suffix() { printf 'rent-process-crash'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
if [ "${1:-}" = "--crash" ]; then
  # Terminate writer mid-operation, like SIGKILL/process death
  # (NOT a physical power cut), before writing authoritative receipt.
  bp_rental_append_paid_receipt() { exit 78; }
  bp_rental_apply_coin dev01 controller01 deadbeef abcdef12 1
  echo 'BUG: crash injection failed to terminate writer' >&2
  exit 71
fi
bp_rental_init
printf 'dev01\tfixture-only\t0\tSynthetic phone\t0\n' > "$BP_RENTAL_DEVICES"
printf 'dev02\tfixture-only\t0\tSynthetic spare\t0\n' >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
initial="$(sha256sum "$BP_RENTAL_EVENTS" | cut -d' ' -f1)"
rc=0
BP_RENT_ATOMIC_FIXTURE_ROOT="$T" sh "$0" --crash >"$T/child.stdout" 2>"$T/child.stderr" || rc=$?
[ "$rc" -eq 78 ] || {
  echo "REPRO INVALID: process exit was $rc, expected synthetic abort 78" >&2; exit 2;
}
[ ! -s "$T/child.stdout" ] || {
  echo "P0 FAILURE: coin success ACK emitted before receipt append" >&2; exit 2;
}
lease="$(bp_rental_device_line dev01 | cut -f3)"
receipts="$(wc -l < "$BP_RENTAL_EVENTS")"
receipt_sha="$(sha256sum "$BP_RENTAL_EVENTS" | cut -d' ' -f1)"
[ "$receipts" -eq 0 ] && [ "$initial" = "$receipt_sha" ] || {
  echo 'REPRO INVALID: receipt was already present before injected crash' >&2; exit 2;
}
[ -f "$BP_STATE/paid-state-uncertain" ] || {
  echo 'P0 FAILURE: interrupted paid operation did not preserve quarantine' >&2; exit 2;
}
retry_rc=0
bp_rental_apply_coin dev01 controller01 deadbeef abcdef12 1 >"$T/retry.stdout" 2>"$T/retry.stderr" || retry_rc=$?
[ "$retry_rc" -ne 0 ] && [ ! -s "$T/retry.stdout" ] || {
  echo "P0 FAILURE: blind retry acknowledged ambiguous coin time rc=$retry_rc" >&2; exit 2;
}
other_rc=0
bp_rental_apply_coin dev02 controller02 feedface 1234abcd 1 >"$T/other.stdout" 2>"$T/other.stderr" || other_rc=$?
[ "$other_rc" -ne 0 ] && [ ! -s "$T/other.stdout" ] || {
  echo "P0 FAILURE: different device accepted coin while state uncertain rc=$other_rc" >&2; exit 2;
}
if [ "$lease" -eq 0 ]; then
  echo 'PASS: process termination before receipt did not persist an unpaid lease'
  exit 0
fi
if [ "$lease" -eq 124056 ]; then
  echo 'RENT-20261022-ATOMIC RED: process died after rental lease rename; lease=124056, receipt absent, no ACK, quarantine persists'
  echo 'NOT PRODUCTION SAFE: this is a synthetic process-death boundary, not physical power-loss acceptance'
  exit 1
fi
echo "REPRO INVALID: unexpected lease after crash: $lease" >&2
exit 2
