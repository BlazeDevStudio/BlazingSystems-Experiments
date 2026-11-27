#!/bin/sh
# RENT-0687: signed rental coin receipt payload collision fixture.
# Runs only in a private disposable temp tree; never touches /etc or hardware.
set -u
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"; mkdir -p "$BP_STATE" "$BP_RUN"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { [ "$1" = rental_seconds_per_pulse ] && printf 600 || printf ''; }
bp_tmp_suffix() { printf 'rent0687'; }
bp_durable_sync() { :; }
bp_now() { printf 123456; }
bp_sha256() { sha256sum | cut -d' ' -f1; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_rental_init || exit 2
printf 'dev01\tfake-secret\t0\tSynthetic Device 1\t0\n' > "$BP_RENTAL_DEVICES"
printf 'dev02\tfake-secret\t0\tSynthetic Device 2\t0\n' >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
first="$(bp_rental_apply_coin dev01 controller01 aabbccdd 11223344 2)" || exit 1
[ "$first" = "$(printf 'credited\t124656')" ] || { echo "RENT-0687 FAIL: first paid credit" >&2; exit 1; }
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq 1 ] || exit 1
[ "$(cut -f5 "$BP_RENTAL_EVENTS")" = "p:2" ] || { echo "RENT-0687 FAIL: missing pulse metadata" >&2; exit 1; }
dupe="$(bp_rental_apply_coin dev01 controller01 aabbccdd 11223344 2)" || exit 1
[ "$dupe" = "$(printf 'duplicate\t124656')" ] || { echo "RENT-0687 FAIL: correct replay" >&2; exit 1; }
# Same signed event identity but different paid payload must NOT be confirmed
# as original payment. Cross-device duplicates must not be ACKed either.
reject() {
  set +e
  result="$(bp_rental_apply_coin "$@")"
  rc=$?
  set -e
  [ "$rc" -ne 0 ] && [ -z "$result" ] || {
    echo "RENT-0687 FAIL: false ACK or mutation for altered/legacy receipt" >&2
    exit 1
  }
}
reject dev01 controller01 aabbccdd 11223344 1
reject dev01 controller01 aabbccdd 11223344 3
reject dev02 controller01 aabbccdd 11223344 2
reject dev01 controller01 aabbccdd 11223344 0
reject dev01 controller01 aabbccdd 11223344 -1
reject dev01 controller01 aabbccdd 11223344 21
reject dev01 controller01 aabbccdd 11223344 '2x'
# Old 4-field v1 receipt MUST NOT silently become a successful ACK.
legacy_event="r:$(printf 'rental|%s|%s|%s' controller01 deadbeef 55667788 | sha256sum | cut -d' ' -f1)"
printf '%s\tdev01\t135000\t123456\n' "$legacy_event" >> "$BP_RENTAL_EVENTS"
reject dev01 controller01 deadbeef 55667788 1
reject dev01 controller01 deadbeef 55667788 2
[ "$(bp_rental_device_line dev01 | cut -f3)" -eq 124656 ] || {
  echo 'RENT-0687 FAIL: duplicate/legacy mutated paid lease' >&2; exit 1;
}
[ "$(bp_rental_device_line dev02 | cut -f3)" -eq 0 ] || exit 1
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq 2 ] || exit 1
[ ! -e "$BP_STATE/paid-state-uncertain" ] || exit 1
json="$(bp_rental_events_json)"
printf '%s' "$json" | grep -Fq '"kind":"r"' || {
  echo 'RENT-0687 FAIL: admin JSON kind changed' >&2; exit 1;
}
printf '%s' "$json" | grep -Fq '"kind":"p:' && {
  echo 'RENT-0687 FAIL: admin JSON leaks implementation kind' >&2; exit 1;
}
echo 'RENT-0687 PASS: exact signed receipt retry, changed pulse/device collision, legacy refusal, bounded numeric input and admin display'
