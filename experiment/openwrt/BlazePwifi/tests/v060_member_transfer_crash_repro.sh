#!/bin/sh
# MIG-0617 expected-RED, synthetic ONLY. Simulate power-loss after first bank write.
# It deliberately exits 1 if a partially committed transfer is observed.
set -u
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
BP_STATE="$T/state"; BP_RUN="$T/run"; mkdir -p "$BP_STATE" "$BP_RUN"
printf 'BLAZE-SYNTHETIC-FIXTURE-ONLY\n' > "$T/.blaze-fixture-only"
BP_MEMBERS="$BP_STATE/members.tsv"
BP_MEMBER_EVENTS="$BP_STATE/member-events.tsv"
BP_MEMBER_REVISION="$BP_STATE/member-revision"
export BP_STATE BP_RUN BP_MEMBERS BP_MEMBER_EVENTS BP_MEMBER_REVISION
# Use exact production member code, with only machine dependencies stubbed.
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { printf ''; }
bp_tmp_suffix() { printf 'transfer-repro'; }
bp_durable_sync() { :; }
bp_now() { printf '123456'; }
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
bp_member_init
printf 'alice\tFixture A\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123\tfixture\n' > "$BP_MEMBERS"
printf 'bob\tFixture B\t1\tsha256i\tsalt\thash\t4096\t200\t1\t123\tfixture\n' >> "$BP_MEMBERS"
printf '1\n' > "$BP_MEMBER_REVISION"
cat > "$T/crash-worker.sh" <<'WORKER'
#!/bin/sh
set -u
ROOT="$1"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs() { :; }
bp_cfg() { printf ''; }
bp_tmp_suffix() { printf 'transfer-crash'; }
bp_now() { printf '123457'; }
bp_durable_sync() {
  # Called by real bp_member_write after atomic rename of the FIRST record.
  # SIGKILL models power loss before the second member write and event log.
  kill -KILL "$$"
}
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
bp_member_transfer alice bob 40 fixture transfer-event-0001 >/dev/null
WORKER
# Run worker in separate process; never kill the test harness itself.
sh "$T/crash-worker.sh" "$ROOT" >"$T/crash-stdout" 2>"$T/crash-stderr"
worker_rc=$?
if [ "$worker_rc" -eq 0 ]; then
  echo 'REPRO SETUP FAILURE: injected power loss did not terminate transfer' >&2
  exit 2
fi
a="$(bp_member_line alice | cut -f8)"
b="$(bp_member_line bob | cut -f8)"
case "$a:$b" in
  '100:200'|'60:240') echo 'PASS: transfer outcome atomic at tested interruption boundary' ;;
  '60:200') echo 'P0 RED: power loss leaves 40 paid seconds missing from synthetic member balances' >&2; exit 1 ;;
  *) echo "REPRO SETUP FAILURE: unexpected balances a=$a b=$b" >&2; exit 2 ;;
esac
