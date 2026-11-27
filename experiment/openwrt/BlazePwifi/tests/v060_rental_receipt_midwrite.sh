#!/bin/sh
# MIG-0627 sandbox: a failed lease receipt after the lease rename must NOT ACK
# or permit a blind retry; it remains UNCERTAIN (not crash-atomic yet).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf '600' || printf ''; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
bp_tmp_suffix() { printf 'test-lease-error'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init
printf 'dev01\tfake-secret\t0\tSynthetic Device\t0\n' > "$BP_RENTAL_DEVICES"
# A real I/O failure can happen AFTER preflight; test that exact boundary.
bp_rental_append_paid_receipt() { return 74; }
set +e
out="$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)"
rc=$?
set -e
lease="$(bp_rental_device_line dev01 | cut -f3)"
[ "$rc" -ne 0 ] && [ "$lease" -eq 124056 ] && [ -z "$out" ] ||
 { echo "P0 FAIL: unexpected late receipt outcome rc=$rc lease=$lease out=$out" >&2; exit 1; }
[ -f "$BP_STATE/paid-state-uncertain" ] ||
 { echo "P0 FAIL: failed paid lease missing persistent halt marker" >&2; exit 1; }
set +e
bp_rental_apply_coin dev01 controller01 nonce01 target01 1 >"$T/retry" 2>&1
retry=$?
set -e
[ "$retry" -ne 0 ] && [ "$(bp_rental_device_line dev01 | cut -f3)" -eq "$lease" ] ||
 { echo "P0 FAIL: retry could re-credit uncertain paid lease" >&2; exit 1; }
echo 'PASS: rental late receipt EIO rejects ACK and quarantines further paid mutations'
echo 'NOT ATOMIC: initial lease changed; operator must reconcile against controller evidence'
