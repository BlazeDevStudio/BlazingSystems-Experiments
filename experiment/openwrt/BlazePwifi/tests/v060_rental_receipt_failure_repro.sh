#!/bin/sh
# MIG-0622: synthetic expected RED, no real device/network/customer record.
# Shows a changed prepaid lease when receipt append cannot be written.
set -u
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)" || exit 1
trap 'chmod 700 "$BP_RENTAL_EVENTS" 2>/dev/null || true; rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"; mkdir -p "$BP_STATE" "$BP_RUN"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$T/.blaze-fixture-only"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf '600' || printf ''; }
bp_tmp_suffix() { printf 'rental-fixture'; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
bp_sha256() { sha256sum | awk '{print $1}'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
# This private directory intentionally rejects the append operation. NEVER use
# /dev/full, /etc, another user's account file, or live router directories.
mkdir "$BP_RENTAL_EVENTS"
out="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1 2>"$T/receipt-error.log")"
rc=$?
lease="$(bp_rental_device_line dev01 | cut -f3)"
if [ "$rc" -eq 0 ] && [ "$lease" -eq 124056 ] &&
    [ "$out" = "$(printf 'credited\t124056')" ] && [ -d "$BP_RENTAL_EVENTS" ]; then
  echo 'P0 RED: rental lease credited and ACK succeeded despite unwritable receipt' >&2
  exit 1
fi
if [ "$rc" -ne 0 ] && [ "$lease" -eq 0 ]; then
  echo 'PASS: rejected rental receipt failure without changing lease'
  exit 0
fi
echo "REPRO SETUP FAILURE: unexpected rental receipt result rc=$rc lease=$lease" >&2
exit 2
