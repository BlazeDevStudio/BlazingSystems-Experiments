#!/bin/sh
# PAY-0740 / #31 #32: real installed v1 member+rental paid entrypoints,
# private disposable receipt corruption fixture only. No devices/customer data.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0740-XXXXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
BP_RENTAL_DEVICES="$BP_STATE/rental-devices.tsv"
BP_RENTAL_EVENTS="$BP_STATE/rental-events.tsv"
export BP_STATE BP_RUN BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION BP_RENTAL_DEVICES BP_RENTAL_EVENTS
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() {
  case "$1" in
    rental_seconds_per_pulse) printf '600';;
    member_event_history) printf '256';;
    *) printf '';;
  esac
}
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_member_init
bp_rental_init
printf 'alice\tAlice\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123456\tfixture\n' >"$BP_MEMBERS"
printf 'bob\tBob\t1\tsha256i\tsalt\thash\t4096\t200\t1\t123456\tfixture\n' >>"$BP_MEMBERS"
printf '1\n' >"$BP_MEMBER_REVISION"
printf 'dev01\tfake-secret\t0\tFixture Device\t0\n' >"$BP_RENTAL_DEVICES"
chmod 600 "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS"
files_snapshot() {
  sha256sum "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" \
    "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS"
}
refuse() {
  name="$1"; shift
  before="$(files_snapshot)"
  rc=0
  "$@" >"$T/out" 2>"$T/err" || rc=$?
  [ "$rc" -ne 0 ] && [ ! -s "$T/out" ] && [ "$before" = "$(files_snapshot)" ] &&
    [ ! -e "$BP_STATE/paid-state-uncertain" ] || {
    echo "PAY-0740 FAIL: $name accepted/mutated despite unrelated receipt corruption (rc=$rc)" >&2
    exit 1
  }
}
[ "$(bp_member_balance_change alice add 10 softtimer:fixture member-good)" = "$(printf '10\t2')" ]
[ "$(bp_member_balance_change alice add 10 softtimer:fixture member-good)" = "$(printf '10\t2')" ]
[ "$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)" = "$(printf 'credited\t124056')" ]
[ "$(bp_rental_apply_coin dev01 controller01 nonce01 target01 1)" = "$(printf 'duplicate\t124056')" ]
cp "$BP_MEMBER_EVENTS" "$T/member-ok"
cp "$BP_RENTAL_EVENTS" "$T/rental-ok"

# PAY-0742: the real Vendo CGI invokes these exact signed replay/snapshot
# helpers while holding bp_paid_replay_read_lock. Test both the healthy
# signed paths and unrelated corruption without HTTP/key mocks.
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
grep -Fq 'bp_member_replay_snapshot_ok "$event_id" "$user" add' "$VENDO"
grep -Fq 'bp_member_replay_snapshot_ok "$event_id" "$user" restore_all' "$VENDO"
grep -Fq 'bp_member_replay_snapshot_ok "$event_id" "$from" transfer' "$VENDO"
grep -Fq 'bp_member_signed_read_integrity' "$VENDO"
bp_paid_replay_read_lock
bp_member_replay_snapshot_ok member-good alice add softtimer:fixture 10 ""
bp_member_signed_read_integrity
bp_paid_replay_read_unlock
refuse_signed() {
  name="$1"; shift
  before="$(files_snapshot)"
  bp_paid_replay_read_lock || {
    echo "PAY-0742 FAIL: cannot get signed financial replay reader lock" >&2
    exit 1
  }
  rc=0
  "$@" >"$T/out" 2>"$T/err" || rc=$?
  bp_paid_replay_read_unlock
  [ "$rc" -ne 0 ] && [ ! -s "$T/out" ] &&
    [ "$before" = "$(files_snapshot)" ] &&
    [ ! -e "$BP_PAID_UNCERTAIN" ] || {
    echo "PAY-0742 FAIL: $name signed reply accepted/mutated corrupt member receipt (rc=$rc)" >&2
    exit 1
  }
}

# Duplicate another valid member receipt ID must close fresh, replay and
# transfer paths (not just lookup of that particular duplicate ID).
cat "$T/member-ok" >>"$BP_MEMBER_EVENTS"
refuse_signed member-duplicate-signed-replay bp_member_replay_snapshot_ok member-good alice add softtimer:fixture 10 ""
refuse_signed member-duplicate-signed-snapshot bp_member_signed_read_integrity
refuse member-duplicate-other-new bp_member_balance_change bob add 1 softtimer:fixture member-new
refuse member-duplicate-other-old bp_member_balance_change alice add 10 softtimer:fixture member-good
refuse member-duplicate-other-transfer bp_member_transfer alice bob 1 softtimer:fixture member-transfer
cp "$T/member-ok" "$BP_MEMBER_EVENTS"
# A wrong-schema unrelated receipt must not permit new credit merely
# because its event ID is different from the requested one.
printf 'unrelated\t123\talice\tadd\t1\n' >>"$BP_MEMBER_EVENTS"
refuse_signed member-truncated-signed-replay bp_member_replay_snapshot_ok member-good alice add softtimer:fixture 10 ""
refuse_signed member-truncated-signed-snapshot bp_member_signed_read_integrity
refuse member-partial-row bp_member_balance_change bob add 1 softtimer:fixture member-new
cp "$T/member-ok" "$BP_MEMBER_EVENTS"
printf 'unrelated\t123\talice\tadd\tbad\t1\tsofttimer:fixture\t1\n' >>"$BP_MEMBER_EVENTS"
refuse_signed member-malformed-signed-replay bp_member_replay_snapshot_ok member-good alice add softtimer:fixture 10 ""
refuse_signed member-malformed-signed-snapshot bp_member_signed_read_integrity
refuse member-malformed-amount bp_member_balance_change bob add 1 softtimer:fixture member-new
cp "$T/member-ok" "$BP_MEMBER_EVENTS"

# A pulse-unbound old/altered r: receipt for another controller cannot be
# ignored while creating a fresh unrelated rental credit or replaying one.
unrelated="r:$(printf 'rental|%s|%s|%s' controller02 nonce02 target02 | bp_sha256)"
printf '%s\tdev01\t124656\t123456\tp:0\n' "$unrelated" >>"$BP_RENTAL_EVENTS"
refuse rental-unrelated-weak-receipt-new bp_rental_apply_coin dev01 controller03 nonce03 target03 1
refuse rental-unrelated-weak-receipt-old bp_rental_apply_coin dev01 controller01 nonce01 target01 1
cp "$T/rental-ok" "$BP_RENTAL_EVENTS"
# Two identical receipts elsewhere fail closed for a different event.
cat "$T/rental-ok" >>"$BP_RENTAL_EVENTS"
refuse rental-duplicate-corpus bp_rental_apply_coin dev01 controller03 nonce03 target03 1
cp "$T/rental-ok" "$BP_RENTAL_EVENTS"
printf 'legacy-other\tdev01\t100\t123456\n' >>"$BP_RENTAL_EVENTS"
refuse rental-partial-unrelated bp_rental_apply_coin dev01 controller03 nonce03 target03 1
cp "$T/rental-ok" "$BP_RENTAL_EVENTS"

# A sound, fully restored corpus must sign safe member reads/replays.
bp_paid_replay_read_lock
bp_member_replay_snapshot_ok member-good alice add softtimer:fixture 10 ""
bp_member_signed_read_integrity
bp_paid_replay_read_unlock
[ "$(bp_member_balance_change bob add 1 softtimer:fixture member-new)" = "$(printf '1\t3')" ]
[ "$(bp_rental_apply_coin dev01 controller03 nonce03 target03 1)" = "$(printf 'credited\t124656')" ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
echo 'PAY-0740/0742 PASS: unrelated corrupted/duplicate member+rental corpus blocks direct and PUBLIC signed replay/snapshot ACKs, with healthy signed reads intact.'
echo 'NOT ATOMIC: v1 still separates paid balance, receipt, revision/lease; no independent witness, hardware fsync or production v0.6 admission.'
