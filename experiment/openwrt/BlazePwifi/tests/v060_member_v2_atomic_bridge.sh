#!/bin/sh
# PAY-0713 isolated synthetic authority test through real member.sh functions.
# Checks balance+receipt one-rename, lost ACK, crash before rename, torn TSV
# read-model reconstruction, transfer conservation, collision, corruption.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-v2-member-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
mkdir -m 700 "$T/state" "$T/run"
printf 'BLAZE-V2-MEMBER-SYNTHETIC-ONLY\n' >"$T/.blaze-v2-member-synthetic-only"
chmod 600 "$T/.blaze-v2-member-synthetic-only"
BP_STATE="$T/state"; BP_RUN="$T/run"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
BP_MEMBER_V2_LAB=1
BP_MEMBER_V2_LAB_HELPER="$ROOT/tests/fixtures/member-v2-atomic-lab.sh"
export BP_STATE BP_RUN BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION
export BP_MEMBER_V2_LAB BP_MEMBER_V2_LAB_HELPER
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { printf ''; }
bp_now() { printf 123456; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
bp_member_init
printf 'alice\tAlice\t1\tsha256i\tsalt\thash\t4096\t140\t1\t100\tfixture\n' >"$BP_MEMBERS"
printf 'bob\tBob\t1\tsha256i\tsalt\thash\t4096\t200\t1\t100\tfixture\n' >>"$BP_MEMBERS"
printf '1\n' > "$BP_MEMBER_REVISION"
. "$BP_MEMBER_V2_LAB_HELPER"
bp_member_v2_lab_seed
ledger="$BP_STATE/member-v2-atomic.tsv"
[ -f "$ledger" ]
account() { awk -F '\t' -v u="$1" '$1==u {print $8}' "$BP_MEMBERS"; }
receipt_count() { awk -F '\t' -v id="$1" '$1==id {n++} END {print n+0}' "$BP_MEMBER_EVENTS"; }
reject() {
  set +e
  "$@" >"$T/reject.log" 2>&1
  rc=$?
  set -e
  [ "$rc" -ne 0 ] || { echo "unexpected paid ACK: $*" >&2;exit 1; }
}
[ "$(bp_member_balance_change alice add 40 softtimer:fixture evt1)" = "$(printf '40\t2')" ]
[ "$(account alice):$(account bob)" = 180:200 ]
[ "$(receipt_count evt1)" -eq 1 ]
baseline="$(sha256sum "$ledger")"
[ "$(bp_member_balance_change alice add 40 softtimer:fixture evt1)" = "$(printf '40\t2')" ]
[ "$baseline" = "$(sha256sum "$ledger")" ]
reject bp_member_balance_change alice add 41 softtimer:fixture evt1
reject bp_member_balance_change bob add 40 softtimer:fixture evt1
reject bp_member_balance_change alice add 40 softtimer:other evt1
[ "$baseline" = "$(sha256sum "$ledger")" ]
# Before the one authority rename: no money and no receipt committed.
reject env BP_MEMBER_V2_LAB_FAULT=before-authority-rename sh -c '
  . "$1/common.sh"; . "$1/member.sh"
  bp_cfg() { printf ""; }; bp_now() { printf 123456; }
  bp_member_balance_change alice add 9 softtimer:fixture evt2
' sh "$ROOT/openwrt/rootfs/usr/lib/blazepwifi"
[ "$(sha256sum "$ledger")" = "$baseline" ]
[ "$(account alice)" = 180 ]
[ "$(receipt_count evt2)" -eq 0 ]
[ "$(bp_member_balance_change alice add 9 softtimer:fixture evt2)" = "$(printf '9\t3')" ]
[ "$(account alice)" = 189 ]
# Transfer crash AFTER the single authority rename and BEFORE the ACK.
set +e
BP_MEMBER_V2_LAB_FAULT=after-authority-rename bp_member_transfer alice bob 50 softtimer:fixture evt3 >"$T/lostack" 2>&1
rc=$?
set -e
[ "$rc" -eq 86 ] || { echo "wrong after-rename fault result $rc" >&2;exit 1; }
[ "$(account alice):$(account bob)" = 189:200 ]
# Same request must reconstruct both projected balances + exactly one receipt.
[ "$(bp_member_transfer alice bob 50 softtimer:fixture evt3)" = "$(printf '50\t4')" ]
[ "$(account alice):$(account bob)" = 139:250 ]
[ "$(( $(account alice) + $(account bob) ))" -eq 389 ]
[ "$(receipt_count evt3)" -eq 1 ]
reject bp_member_transfer alice bob 51 softtimer:fixture evt3
reject bp_member_transfer alice carol 50 softtimer:fixture evt3
# Projection failure happens after authority commit: do NOT ACK; retry repairs.
set +e
BP_MEMBER_V2_LAB_FAULT=projection-eio bp_member_balance_change alice add 11 softtimer:fixture evt4 >"$T/failedview" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "wrong projection EIO result $rc" >&2;exit 1; }
[ "$(account alice)" = 139 ]
[ "$(bp_member_balance_change alice add 11 softtimer:fixture evt4)" = "$(printf '11\t5')" ]
[ "$(account alice):$(account bob)" = 150:250 ]
[ "$(receipt_count evt4)" -eq 1 ]
# V1 admin mutations are barred from forking the lab authority.
reject bp_member_delete alice fixture
reject bp_member_patch alice changed 1 fixture
reject bp_member_create carol Carol password12 fixture
snapshot="$(sha256sum "$ledger")"
# Broken projection is automatically rebuilt from source of truth, not imported.
printf 'alice\tcorrupted\n' >"$BP_MEMBERS"
[ "$(bp_member_balance_change alice add 11 softtimer:fixture evt4)" = "$(printf '11\t5')" ]
[ "$(account alice)" = 150 ]
[ "$snapshot" = "$(sha256sum "$ledger")" ]
# A tampered ledger checksum fails closed rather than rewriting paid data.
cp "$ledger" "$T/ledger.good"
sed 's/alice/AliceTampered/' "$T/ledger.good" >"$ledger"
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
[ "$(account alice)" = 150 ]
cp "$T/ledger.good" "$ledger"; chmod 600 "$ledger"
# A global quarantine marker always wins over synthetic authority.
printf 'PENDING\n' >"$BP_STATE/paid-state-uncertain"
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
rm "$BP_STATE/paid-state-uncertain"
# PAY-0714: Fixture-only financial code may not ship in OpenWrt rootfs.
[ ! -e "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member-v2-atomic-lab.sh" ] || {
  echo "PAY-0714 rejected bundled lab authority in customer rootfs" >&2; exit 1;
}
# Missing, relative, and nonexistent explicit test helper all fail closed.
expected_lab_helper="$BP_MEMBER_V2_LAB_HELPER"
unset BP_MEMBER_V2_LAB_HELPER
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
BP_MEMBER_V2_LAB_HELPER=tests/fixtures/member-v2-atomic-lab.sh
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
BP_MEMBER_V2_LAB_HELPER="$T/missing-helper.sh"
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
BP_MEMBER_V2_LAB_HELPER="$expected_lab_helper"
[ "$snapshot" = "$(sha256sum "$ledger")" ]
# All derived paid paths must remain in the SAME isolated fixture state.
# Use a disposable sentinel outside state; never aim the test at live /etc.
printf 'OUTSIDE-SENTINEL\n' > "$T/escape-sentinel"
for name in BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION; do
  original="$(eval "printf '%s' \"\$$name\"")"
  eval "$name=\"$T/escape-sentinel\""
  reject bp_member_balance_change alice add 1 softtimer:fixture evt5
  eval "$name=\"$original\""
  [ "$(cat "$T/escape-sentinel")" = OUTSIDE-SENTINEL ] || {
    echo "PAY-0713 synthetic derived-state path escape" >&2;exit 1;
  }
done
[ "$snapshot" = "$(sha256sum "$ledger")" ]
# Even an environment override cannot route fixture code into real paid paths.
old_state="$BP_STATE"
BP_STATE=/etc/blazepwifi/state
reject bp_member_balance_change alice add 1 softtimer:fixture evt5
BP_STATE="$old_state"
[ "$snapshot" = "$(sha256sum "$ledger")" ]
echo 'PAY-0713 PASS: real member entrypoints route synthetic-only single-authority member+receipt commits, EIO, lost-ACK, replay, recovery, transfer and corruption'
echo 'NOT PRODUCTION: v1 migration, independent antirollback, target fsync/powercut, admin/CGI v2 protocol, physical acceptance remain BLOCKED'
