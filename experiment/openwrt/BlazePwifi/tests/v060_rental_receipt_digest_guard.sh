#!/bin/sh
# RENT-20261022-HASH / P0 #32.
# Reject an unavailable, malformed or truncated receipt hash BEFORE modifying
# prepaid rental time or emitting ACK. Disposable state only; no hardware.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-renthash-XXXXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf '600' || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
bp_tmp_suffix() { printf 'renthash'; }
BP_TEST_HASH_MODE=valid
bp_sha256() {
  case "$BP_TEST_HASH_MODE" in
    missing) cat >/dev/null; return 73;;
    empty) cat >/dev/null; return 0;;
    short) cat >/dev/null; printf abc; return 0;;
    nonhex) cat >/dev/null; printf '%064d' 0 | tr 0 g; return 0;;
    valid) sha256sum | cut -d' ' -f1;;
    *) return 99;;
  esac
}
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
before="$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")"
for mode in missing empty short nonhex; do
  BP_TEST_HASH_MODE="$mode"
  rc=0
  bp_rental_apply_coin dev01 controller01 deadbeef abcdef12 1 > "$T/$mode.out" 2>"$T/$mode.err" || rc=$?
  if [ "$rc" -eq 0 ] || [ -s "$T/$mode.out" ] ||
     [ "$before" != "$(sha256sum "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS")" ] ||
     [ -e "$BP_STATE/paid-state-uncertain" ]; then
    echo "RENT-20261022-HASH FAIL: $mode digest changed state or emitted paid ACK (rc=$rc)" >&2
    exit 1
  fi
done
BP_TEST_HASH_MODE=valid
first="$(bp_rental_apply_coin dev01 controller01 deadbeef abcdef12 1)"
[ "$first" = "$(printf 'credited\t124056')" ] || exit 1
retry="$(bp_rental_apply_coin dev01 controller01 deadbeef abcdef12 1)"
[ "$retry" = "$(printf 'duplicate\t124056')" ] || exit 1
[ "$(bp_rental_device_line dev01 | cut -f3)" -eq 124056 ] || exit 1
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq 1 ] || exit 1
echo 'RENT-20261022-HASH PASS: empty/broken receipt digest never credits or ACKs; valid credit and exact replay preserved'
echo 'NOT ATOMIC: v1 rental time and receipt are still separate writes; no independent rollback witness or paid-production authority.'
