#!/bin/sh
# MIG-0619 synthetic-only expected RED: failed event receipt must not acknowledge credit.
set -u
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"; mkdir -p "$BP_STATE" "$BP_RUN"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$T/.blaze-fixture-only"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { printf ''; }
bp_tmp_suffix() { printf 'receipt-repro'; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
bp_member_init
printf 'alice\tFixture\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123\tfixture\n' > "$BP_MEMBERS"
printf '1\n' > "$BP_MEMBER_REVISION"
# Model EIO/ENOSPC at the receipt durability boundary. Production money mutation
# function is not stubbed; only the downstream filesystem receipt append is failed.
bp_member_event_record() { return 74; }
before="$(bp_member_line alice | cut -f8)"
result="$(bp_member_balance_change alice add 40 softtimer:fixture event-receipt-error-0001)"
rc=$?
after="$(bp_member_line alice | cut -f8)"
if [ "$rc" -eq 0 ]; then
  echo 'P0 FAIL: false member success ACK despite failed event receipt' >&2
  exit 1
fi
if [ "$before" -eq 100 ] && [ "$after" -eq 140 ] && [ -f "$BP_STATE/paid-state-uncertain" ]; then
  # Ambiguous first write remains visible: reject EVERY new paid mutation.
  set +e
  bp_member_balance_change alice add 40 softtimer:fixture event-receipt-error-0001 > "$T/retry" 2>&1
  retry_rc=$?
  set -e
  retry_balance="$(bp_member_line alice | cut -f8)"
  if [ "$retry_rc" -ne 0 ] && [ "$retry_balance" -eq "$after" ]; then
    echo 'PASS: member receipt EIO rejects ACK and quarantines all further paid changes'
    echo 'NOT ATOMIC: first balance mutation still visible pending operator reconciliation'
    exit 0
  fi
fi
echo "P0 FAIL: missing quarantine or unexpected receipt outcome rc=$rc before=$before after=$after" >&2
exit 1
