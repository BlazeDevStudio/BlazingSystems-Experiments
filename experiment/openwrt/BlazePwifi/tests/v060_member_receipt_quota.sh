#!/bin/sh
# MIG-0626: synthetic-only fail-closed prepaid receipt quota check.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$T/.blaze-fixture-only"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
bp_init_dirs() { :; }
bp_cfg() { case "$1" in member_event_history) printf '128';; *) printf ''; esac; }
bp_tmp_suffix() { printf 'synthetic-quota'; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
bp_member_init
printf 'alice\tFixture A\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123\tfixture\n' >"$BP_MEMBERS"
printf 'bob\tFixture B\t1\tsha256i\tsalt\thash\t4096\t200\t1\t123\tfixture\n' >>"$BP_MEMBERS"
printf '1\n' >"$BP_MEMBER_REVISION"
# Simulated existing receipts past the defensive size. All paths are in mktemp.
dd if=/dev/zero bs=1048576 count=5 2>/dev/null | tr '\000' 'R' > "$BP_MEMBER_EVENTS"
baseline="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
set +e
bp_member_balance_change alice add 10 softtimer:test quota-event-1 > "$T/output1" 2>"$T/error1"
rc1=$?
bp_member_transfer alice bob 50 softtimer:test quota-event-2 > "$T/output2" 2>"$T/error2"
rc2=$?
set -e
[ "$rc1" -eq 7 ] && [ "$rc2" -eq 7 ] ||
  { echo "P0 FAIL: receipt quota did not reject new money before write rc=$rc1/$rc2" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$baseline" ] ||
  { echo "P0 FAIL: quota refusal still mutated balances" >&2; exit 1; }
[ "$(wc -c < "$BP_MEMBER_EVENTS")" -eq 5242880 ] ||
  { echo "P0 FAIL: quota refusal truncated accepted receipt store" >&2; exit 1; }
echo 'PASS: paid member quota rejects credit and transfer before mutation, never deletes old receipts'
