#!/bin/sh
# P0-0710 synthetic-only: real legacy source code, no customer state or HW.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-p0-0710-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf '%s\n' BLAZE-SYNTHETIC-FIXTURE-ONLY > "$T/.blaze-fixture-only"
BP_STATE="$T/state"; BP_RUN="$T/run"; mkdir -p "$BP_STATE" "$BP_RUN"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { case "$1" in member_event_history) printf '128';; rental_seconds_per_pulse) printf '%s' "$fixture_per";; *) :;; esac; }
bp_tmp_suffix() { printf 'p0-0710'; }
bp_durable_sync() { :; }
bp_now() { printf '%s' "$fixture_now"; }
bp_sha256() { sha256sum | awk '{print $1}'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_member_init
fixture_per=600
fixture_now=123456
: > "$BP_RENTAL_EVENTS"
chmod 600 "$BP_RENTAL_EVENTS"
printf '1\n' > "$BP_MEMBER_REVISION"
# Refuse entry to the financial mutation boundary for invalid numbers.
# For valid numeric inputs the sentinel must be reached (public rc=9), proving
# we are exercising the production code rather than a dead test path.
bp_paid_begin() { printf 'entered\n' > "$T/begin"; return 99; }

member_fixture() {
  printf 'alice\tFixture A\t1\tsha256i\tsalt\thash\t4096\t%s\t1\t123\tfixture\n' "$1" > "$BP_MEMBERS"
  printf 'bob\tFixture B\t1\tsha256i\tsalt\thash\t4096\t%s\t1\t123\tfixture\n' "$2" >> "$BP_MEMBERS"
  : > "$BP_MEMBER_EVENTS"
  rm -f "$T/begin"
}
rental_fixture() {
  printf 'dev01\tfake-secret\t%s\tSynthetic Device\t0\n' "$1" > "$BP_RENTAL_DEVICES"
  : > "$BP_RENTAL_EVENTS"
  rm -f "$T/begin"
}
must_reject_member_add() {
  numeric_case_label="$1"; balance="$2"; amount="$3"
  member_fixture "$balance" 200
  before="$(cat "$BP_MEMBERS")"
  rc=0
  bp_member_balance_change alice add "$amount" fixture "evt-$numeric_case_label" >"$T/out" 2>"$T/err" || rc=$?
  if [ "$rc" -eq 0 ] || [ "$rc" -eq 99 ] || [ -e "$T/begin" ] ||
     [ -s "$T/out" ] || [ "$(cat "$BP_MEMBERS")" != "$before" ]; then
    echo "P0-0710 RED: member add accepted unsafe $numeric_case_label (rc=$rc)" >&2; exit 1
  fi
}
must_reject_transfer() {
  numeric_case_label="$1"; src="$2"; dst="$3"; amount="$4"
  member_fixture "$src" "$dst"
  before="$(cat "$BP_MEMBERS")"
  rc=0
  bp_member_transfer alice bob "$amount" fixture "evt-$label" >"$T/out" 2>"$T/err" || rc=$?
  if [ "$rc" -eq 0 ] || [ "$rc" -eq 99 ] || [ -e "$T/begin" ] ||
     [ -s "$T/out" ] || [ "$(cat "$BP_MEMBERS")" != "$before" ]; then
    echo "P0-0710 RED: member transfer accepted unsafe $label (rc=$rc)" >&2; exit 1
  fi
}
must_reject_rental() {
  numeric_case_label="$1"; lease="$2"; pulses="$3"; seconds="$4"
  rental_fixture "$lease"; fixture_per="$seconds"
  before="$(cat "$BP_RENTAL_DEVICES")"
  rc=0
  bp_rental_apply_coin dev01 controller01 "nonce-$numeric_case_label" target01 "$pulses" >"$T/out" 2>"$T/err" || rc=$?
  if [ "$rc" -eq 0 ] || [ "$rc" -eq 99 ] || [ -e "$T/begin" ] ||
     [ -s "$T/out" ] || [ "$(cat "$BP_RENTAL_DEVICES")" != "$before" ]; then
    echo "P0-0710 RED: rental accepted unsafe $label (rc=$rc)" >&2; exit 1
  fi
}
assert_valid_reaches_boundary() {
  scope="$1"; shift
  rm -f "$T/begin"
  rc=0
  "$@" >"$T/out" 2>"$T/err" || rc=$?
  [ "$rc" -eq 9 ] && [ -f "$T/begin" ] || {
    echo "P0-0710 setup error: healthy $scope did not reach transaction boundary (rc=$rc)" >&2
    exit 2
  }
}
# Numbers must be canonical nonnegative decimal, bounded for portable 32-bit
# shells (MAX 2147483647) before any arithmetic or ACK.
must_reject_member_add malformed-bank not-a-number 10
must_reject_member_add padded-bank 000100 10
must_reject_member_add over-max-bank 2147483648 10
must_reject_member_add addition-overflow 2147483640 10
must_reject_member_add padded-amount 100 08
must_reject_transfer malformed-source not-a-number 200 10
must_reject_transfer malformed-target 100 bad 10
must_reject_transfer padded-target 100 000200 10
must_reject_transfer target-overflow 100 2147483640 10
must_reject_transfer padded-amount 100 200 08
must_reject_rental malformed-lease not-a-number 1 600
must_reject_rental padded-lease 000100 1 600
must_reject_rental over-max-lease 2147483648 1 600
must_reject_rental lease-overflow 2147483640 1 600
must_reject_rental padded-pulses 0 08 600
must_reject_rental padded-rate 0 1 0600
must_reject_rental invalid-rate 0 1 nonsense

member_fixture 100 200
assert_valid_reaches_boundary member-add bp_member_balance_change alice add 10 fixture positive-add
member_fixture 100 200
assert_valid_reaches_boundary member-transfer bp_member_transfer alice bob 10 fixture positive-transfer
fixture_per=600; rental_fixture 0
assert_valid_reaches_boundary rental-coin bp_rental_apply_coin dev01 controller01 nonce-positive target01 1
echo 'P0-0710 PASS: malformed/octal/overflow paid inputs rejected BEFORE financial boundary; healthy ones still reach it'
echo 'CUSTOMER_INSTALL_AUTHORIZED=0 PHYSICAL_POWER_CUT_VERIFIED=0'
