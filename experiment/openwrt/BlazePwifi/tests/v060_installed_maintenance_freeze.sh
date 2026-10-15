#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
FREEZE="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2_maintenance_freeze.sh"
COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
sh -n "$FREEZE"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN" "$T/bin"
: > "$BP_RUN/paid-financial.lock"
printf 'member-money\n' > "$BP_STATE/members.tsv"
before="$(sha256sum "$BP_STATE/members.tsv")"

reject() {
  if sh "$FREEZE" --freeze --operator-quiesced > "$T/out" 2>&1; then
    echo "FAIL: $1 admitted" >&2; exit 1
  fi
  grep -q 'paid_ack_authorized=0; migration_authorized=0' "$T/out"
  [ "$before" = "$(sha256sum "$BP_STATE/members.tsv")" ] || exit 1
}

if sh "$FREEZE" > "$T/out" 2>&1; then echo 'FAIL: implicit freeze' >&2; exit 1; fi
[ ! -e "$BP_STATE/paid-v2-cutover-intent" ] || exit 1
touch "$BP_STATE/paid-state-uncertain"
reject uncertain_paid_write
[ ! -e "$BP_STATE/paid-v2-cutover-intent" ] || exit 1
rm "$BP_STATE/paid-state-uncertain"
exec 9<>"$BP_RUN/paid-financial.lock"
flock -n 9
reject active_writer
[ ! -e "$BP_STATE/paid-v2-cutover-intent" ] || exit 1
flock -u 9
exec 9>&-
ln -s missing "$BP_STATE/paid-v2-cutover-intent"
reject dangling_marker
rm "$BP_STATE/paid-v2-cutover-intent"

# A failed sync must leave a marker that denies paid writes and replay ACKs.
printf '#!/bin/sh\nexit 1\n' > "$T/bin/sync"
chmod +x "$T/bin/sync"
PATH="$T/bin:$PATH" reject sync_failure
[ -f "$BP_STATE/paid-v2-cutover-intent" ] || exit 1
grep -q 'marker_sync_uncertain' "$T/out"

BP_POST_BODY=''
. "$COMMON"
if bp_paid_begin; then echo 'FAIL: paid write during freeze' >&2; exit 1; fi
if bp_paid_replay_read_lock; then echo 'FAIL: replay ACK during freeze' >&2; exit 1; fi
[ ! -e "$BP_STATE/paid-state-uncertain" ] || exit 1
[ "$before" = "$(sha256sum "$BP_STATE/members.tsv")" ] || exit 1
reject existing_marker

rm "$BP_STATE/paid-v2-cutover-intent"
sh "$FREEZE" --freeze --operator-quiesced > "$T/out"
grep -q 'FROZEN; paid_ack_authorized=0; migration_authorized=0' "$T/out"
reject idempotent_denial
[ "$before" = "$(sha256sum "$BP_STATE/members.tsv")" ] || exit 1
echo 'PAY-0758 installed maintenance freeze: active writer, uncertainty, sync failure, paid writes and replay denied'
