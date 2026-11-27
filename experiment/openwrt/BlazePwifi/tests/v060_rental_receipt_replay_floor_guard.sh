#!/bin/sh
# RENT-20261022-FLOOR / P0 #32: source-only v1 replay lease-floor guard.
# A retained signed receipt cannot justify an ACK after its paid lease
# disappears from the authoritative device snapshot. Synthetic files ONLY.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rentfloor-XXXXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf 123456; }
bp_tmp_suffix() { printf rentfloor; }
bp_sha256() { sha256sum | cut -d' ' -f1; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
first="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)"
[ "$first" = "$(printf 'credited\t124056')" ] || exit 1
retry="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)"
[ "$retry" = "$(printf 'duplicate\t124056')" ] || exit 1
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq 1 ] || exit 1
receipt_before="$(sha256sum "$BP_RENTAL_EVENTS")"
# Deliberately simulate a stale lease write with the later receipt retained.
# This is a file-only fault injection, NOT an actual device rollback.
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
set +e
out="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1 2>"$T/replay.err")"
rc=$?
set -e
if [ "$rc" -eq 0 ] || [ -n "$out" ] ||
   [ "$(cut -f3 "$BP_RENTAL_DEVICES")" != 0 ] ||
   [ "$(sha256sum "$BP_RENTAL_EVENTS")" != "$receipt_before" ] ||
   [ -e "$BP_STATE/paid-state-uncertain" ]; then
  echo "RENT-20261022-FLOOR FAIL: stale lease received duplicate paid ACK or mutated state (rc=$rc)" >&2
  exit 1
fi
# Exercise the second receipt lookup as though another writer committed
# between our initial read lock and the paid writer lock. Only this fixture
# overrides snapshot visibility; production receipt validation stays intact.
bp_rental_paid_receipt_snapshot() {
  if [ ! -e "$T/writer-read" ]; then
    : > "$T/writer-read"
    return 0
  fi
  awk -F '\t' -v e="$1" '$1==e {print; exit}' "$BP_RENTAL_EVENTS"
}
set +e
out="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1 2>"$T/writer.err")"
rc=$?
set -e
if [ "$rc" -eq 0 ] || [ -n "$out" ] ||
   [ "$(cut -f3 "$BP_RENTAL_DEVICES")" != 0 ] ||
   [ "$(sha256sum "$BP_RENTAL_EVENTS")" != "$receipt_before" ] ||
   [ ! -f "$BP_STATE/paid-state-uncertain" ]; then
  echo "RENT-20261022-FLOOR FAIL: writer-lock replay ACKed regressed lease or cleared uncertainty (rc=$rc)" >&2
  exit 1
fi
echo 'RENT-20261022-FLOOR PASS: stale-lease paid ACK refused under read and writer locks; normal purchase/replay preserved'
echo 'NOT ATOMIC: v1 separate lease/receipt writes, independent monotonic witness, migration, hardware proof remain blocked.'
