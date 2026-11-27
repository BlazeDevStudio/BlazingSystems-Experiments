#!/bin/sh
# PAY-0729 / P0 #31: exercise the real legacy member money entrypoints.
# Entirely private /tmp synthetic fixture. NO production funds or keys.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay-0729-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$T/.fixture-only"
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -m 700 "$BP_STATE" "$BP_RUN"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
export BP_STATE BP_RUN BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { :; }
bp_durable_sync() { :; }
bp_tmp_suffix() { printf 'pay0729'; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"

member_row() {
  printf '%s\t%s\t1\tsha256i\tsalt\thash\t4096\t%s\t%s\t123456\tfixture\n' "$1" "$1" "$2" "$3"
}
reset_fixture() {
  rm -f "$BP_MEMBER_REVISION" "$BP_MEMBERS" "$BP_MEMBER_EVENTS" "$BP_PAID_UNCERTAIN"
  bp_member_init
  member_row alice 100 1 > "$BP_MEMBERS"
  member_row bob 200 1 >> "$BP_MEMBERS"
  printf '1\n' > "$BP_MEMBER_REVISION"
  chmod 600 "$BP_MEMBERS" "$BP_MEMBER_REVISION" "$BP_MEMBER_EVENTS"
}
bank() { awk -F '\t' -v u="$1" '$1==u {print $8}' "$BP_MEMBERS"; }
file_hashes() {
  sha256sum "$BP_MEMBERS" "$BP_MEMBER_EVENTS" | awk '{print $1}'
}
refuse() {
  label="$1"; shift
  before="$(file_hashes)"
  rc=0
  "$@" > "$T/out" 2> "$T/err" || rc=$?
  [ "$rc" -ne 0 ] && [ ! -s "$T/out" ] && [ "$(file_hashes)" = "$before" ] || {
    echo "PAY-0729 FAIL: $label emitted ACK or modified member/receipt (rc=$rc)" >&2
    exit 1
  }
}
reset_fixture
[ "$(bp_member_balance_change alice add 10 fixture evt-valid-add)" = "$(printf '10\t2')" ]
[ "$(bank alice)" = 110 ]
[ "$(bp_member_transfer alice bob 5 fixture evt-valid-transfer)" = "$(printf '5\t3')" ]
[ "$(bank alice):$(bank bob)" = '105:205' ]
[ "$(bp_member_balance_change alice add 10 fixture evt-valid-add)" = "$(printf '10\t3')" ]

# Corrupt, padded, missing, overflowing or rolled-back global revisions must
# refuse BOTH fresh operations and a previously recorded success replay.
for bad in corrupt 0003 '' 2147483647 0; do
  printf '%s\n' "$bad" > "$BP_MEMBER_REVISION"
  refuse 'corrupt revision fresh add' bp_member_balance_change alice add 10 fixture evt-bad
  refuse 'corrupt revision old ACK' bp_member_balance_change alice add 10 fixture evt-valid-add
  refuse 'corrupt revision transfer' bp_member_transfer alice bob 10 fixture evt-bad-transfer
done

rm -f "$BP_MEMBER_REVISION"
refuse 'missing revision' bp_member_balance_change alice add 10 fixture evt-missing
[ ! -e "$BP_MEMBER_REVISION" ]
if bp_member_init >"$T/out" 2>"$T/err"; then
  echo 'PAY-0729 FAIL: reinitialization silently reset paid revision' >&2; exit 1
fi
[ ! -e "$BP_MEMBER_REVISION" ]
# A symlink must not be used as an authoritative revision.
printf '3\n' > "$T/foreign-revision"
ln -s "$T/foreign-revision" "$BP_MEMBER_REVISION"
refuse 'linked revision' bp_member_balance_change alice add 10 fixture evt-linked
[ "$(cat "$T/foreign-revision")" = 3 ]
rm "$BP_MEMBER_REVISION"

# A duplicated member row or a member revision ahead of the global value
# prevents both paid writes and receipt ACKs.
printf '3\n' > "$BP_MEMBER_REVISION"
member_row extra 0 4 >> "$BP_MEMBERS"
refuse 'member ahead of global' bp_member_balance_change alice add 10 fixture evt-ahead
refuse 'member ahead of global replay' bp_member_balance_change alice add 10 fixture evt-valid-add
reset_fixture
member_row alice 100 1 >> "$BP_MEMBERS"
refuse 'duplicate member revision read model' bp_member_transfer alice bob 5 fixture evt-duplicate

# Fault injection: a revision write failure AFTER entering the financial
# boundary must not proceed to member/receipt writes using an empty revision.
# Stub ONLY transaction boundary in the disposable fixture, not money logic.
reset_fixture
bp_paid_begin() { : > "$T/begin"; return 0; }
bp_paid_abort() { : > "$T/abort"; return 0; }
bp_member_next_revision() { return 8; }
refuse 'failed allocation after paid begin add' bp_member_balance_change alice add 7 fixture evt-late-add
[ -e "$T/begin" ] && [ -e "$T/abort" ]
rm "$T/begin" "$T/abort"
refuse 'failed allocation after paid begin transfer' bp_member_transfer alice bob 7 fixture evt-late-transfer
[ -e "$T/begin" ] && [ -e "$T/abort" ]
rm "$T/begin" "$T/abort"
refuse 'failed allocation admin patch' bp_member_patch alice '@keep' '@keep' fixture
[ -e "$T/begin" ] && [ -e "$T/abort" ]
echo 'PAY-0729 PASS: valid credit/transfer and replay; corrupt/missing/linked/rolled-back/duplicate revision and failed allocation refuse ACK with no paid data change'
echo 'NOT ATOMIC: v1 balance, revision and receipt still separate; P0 #31/#32/#34/#43 and customer v0.6 remain blocked'
