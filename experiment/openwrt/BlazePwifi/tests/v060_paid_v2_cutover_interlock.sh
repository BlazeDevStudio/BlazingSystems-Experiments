#!/bin/sh
# PAY-0730 / P0 #31/#32: exercise REAL installed v1 money entrypoints,
# but only within a disposable private /tmp synthetic state. No hardware.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0730-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf '%s\n' BLAZE-PAY-0730-SYNTHETIC-ONLY > "$T/.lab-only"
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
    rental_seconds_per_pulse) printf '600' ;;
    member_event_history) printf '256' ;;
    *) printf '' ;;
  esac
}
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
bp_member_init
bp_rental_init
printf 'alice\tAlice\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123456\tfixture\n' > "$BP_MEMBERS"
printf 'bob\tBob\t1\tsha256i\tsalt\thash\t4096\t200\t1\t123456\tfixture\n' >> "$BP_MEMBERS"
printf '1\n' > "$BP_MEMBER_REVISION"
printf 'dev01\tfixture-key\t0\tFixture Device\t0\n' > "$BP_RENTAL_DEVICES"
chmod 600 "$BP_MEMBERS" "$BP_MEMBER_REVISION" "$BP_RENTAL_DEVICES"

# The interlock is default-INACTIVE: healthy v1 behavior MUST remain usable
# until an actual operator-managed migration/cutover is safely engineered.
[ ! -e "$BP_PAID_V2_CUTOVER" ] && [ ! -L "$BP_PAID_V2_CUTOVER" ]
[ "$(bp_member_balance_change alice add 10 softtimer:fixture evt0730)" = "$(printf '10\t2')" ]
[ "$(bp_member_balance_change alice add 10 softtimer:fixture evt0730)" = "$(printf '10\t2')" ]
[ "$(bp_rental_apply_coin dev01 controller01 nonce0730 target01 1)" = "$(printf 'credited\t124056')" ]
[ "$(bp_rental_apply_coin dev01 controller01 nonce0730 target01 1)" = "$(printf 'duplicate\t124056')" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
digest_paid() {
  sha256sum "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_MEMBER_REVISION" \
    "$BP_RENTAL_DEVICES" "$BP_RENTAL_EVENTS" | awk '{print $1}'
}
deny() {
  label="$1"; shift
  before="$(digest_paid)"
  rc=0
  "$@" > "$T/stdout" 2> "$T/stderr" || rc=$?
  [ "$rc" -ne 0 ] && [ ! -s "$T/stdout" ] &&
    [ "$(digest_paid)" = "$before" ] || {
      echo "PAY-0730 unsafe success/mutation at $label (rc=$rc)" >&2
      exit 1
    }
}
deny_all() {
  label="$1"
  deny "$label begin" bp_paid_begin
  deny "$label replay lock" bp_paid_replay_read_lock
  deny "$label member fresh" bp_member_balance_change alice add 3 softtimer:fixture new0730
  deny "$label member old ACK" bp_member_balance_change alice add 10 softtimer:fixture evt0730
  deny "$label transfer" bp_member_transfer alice bob 3 softtimer:fixture move0730
  deny "$label rental fresh" bp_rental_apply_coin dev01 controller01 nonce-new target01 1
  deny "$label rental old ACK" bp_rental_apply_coin dev01 controller01 nonce0730 target01 1
  [ ! -e "$BP_PAID_UNCERTAIN" ] || {
    echo "PAY-0730 unexpected pending marker at $label" >&2; exit 1
  }
}
# Treat every on-disk marker type as HALT. In particular a dangling symlink
# must not become the same as 'no cutover' under a simple -e check.
printf 'CUTOVER-IN-PROGRESS\n' > "$BP_PAID_V2_CUTOVER"
deny_all regular-marker
rm "$BP_PAID_V2_CUTOVER"
mkdir "$BP_PAID_V2_CUTOVER"
deny_all directory-marker
rmdir "$BP_PAID_V2_CUTOVER"
ln -s "$T/does-not-exist" "$BP_PAID_V2_CUTOVER"
deny_all dangling-symlink-marker
rm "$BP_PAID_V2_CUTOVER"

# After a v1 writer acquired its paid lock and pending marker, the cutover
# may have been staged by a faulty external operator. No success commit ACK,
# and no automatic clearing of the uncertain financial marker is permitted.
bp_paid_begin
[ -f "$BP_PAID_UNCERTAIN" ]
printf 'CUTOVER-WHILE-WRITING\n' > "$BP_PAID_V2_CUTOVER"
deny 'mid-write cutover refuses final commit' bp_paid_commit
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$BP_PAID_V2_CUTOVER"
deny 'uncertainty remains after cutover marker removed' bp_paid_begin
[ -f "$BP_PAID_UNCERTAIN" ]
echo 'PAY-0730 PASS: real v1 paid member/rental new+replay deny on cutover marker; late marker keeps quarantine; default absent stays functional'
echo 'NOT A MIGRATION OR WITNESS: marker is same-domain, deletable/rollbackable; #31/#32/#34/#43 and v0.6 customer cutover remain BLOCKED'
