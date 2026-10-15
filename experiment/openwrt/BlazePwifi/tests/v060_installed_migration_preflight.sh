#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
PREFLIGHT="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2_migration_preflight.sh"
sh -n "$PREFLIGHT"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT INT TERM
export BP_STATE="$T/state" BP_RUN="$T/run"
mkdir -p "$BP_STATE" "$BP_RUN"
touch "$BP_RUN/paid-financial.lock" "$BP_STATE/paid-v2-cutover-intent"
printf 'a:b\t10\t1800000000\t0\t0\t0\t\t\t\n' > "$BP_STATE/accounts.tsv"
printf '1\n' > "$BP_STATE/member-revision"
printf '2member\tlabel\t1\tsha256i\tsalt\thash\t4096\t10\t1\t1700000000\tadmin\n' > "$BP_STATE/members.tsv"
: > "$BP_STATE/member-events.tsv"
printf 'a:b\tsecret\t1900000000\tlabel\t1700000000\n' > "$BP_STATE/rental-devices.tsv"
: > "$BP_STATE/rental-events.tsv"
printf 'Vendo1\t1\t1\t1\t1\t-1\t-1\t-1\t1\t1\t1\t40\t400\t6\t1\n' > "$BP_STATE/controllers.tsv"

pass() {
  sh "$PREFLIGHT" > "$T/output" 2>&1 || { cat "$T/output" >&2; exit 1; }
  grep -q 'READ_ONLY_PASS; paid_ack_authorized=0; migration_authorized=0' "$T/output"
}
reject() {
  immutable_before="$(sha256sum "$BP_STATE"/*.tsv "$BP_STATE/member-revision")"
  if sh "$PREFLIGHT" > "$T/output" 2>&1; then
    echo "FAIL: $1 admitted" >&2; exit 1
  fi
  grep -q 'paid_ack_authorized=0' "$T/output" || { cat "$T/output" >&2; exit 1; }
  [ ! -e "$BP_STATE/ledger.tsv" ] || { echo 'FAIL: preflight initialized v2 ledger' >&2; exit 1; }
  [ "$immutable_before" = "$(sha256sum "$BP_STATE"/*.tsv "$BP_STATE/member-revision")" ] || {
    echo "FAIL: $1 changed a financial store" >&2; exit 1;
  }
}
restore() {
  cp "$T/accounts" "$BP_STATE/accounts.tsv"
  cp "$T/members" "$BP_STATE/members.tsv"
  cp "$T/rental" "$BP_STATE/rental-devices.tsv"
  cp "$T/controllers" "$BP_STATE/controllers.tsv"
  : > "$BP_STATE/member-events.tsv"
  : > "$BP_STATE/rental-events.tsv"
  printf '1\n' > "$BP_STATE/member-revision"
}
cp "$BP_STATE/accounts.tsv" "$T/accounts"
cp "$BP_STATE/members.tsv" "$T/members"
cp "$BP_STATE/rental-devices.tsv" "$T/rental"
cp "$BP_STATE/controllers.tsv" "$T/controllers"
pass
before="$(sha256sum "$BP_STATE"/*.tsv "$BP_STATE/member-revision")"
pass
[ "$before" = "$(sha256sum "$BP_STATE"/*.tsv "$BP_STATE/member-revision")" ] || exit 1

rm "$BP_STATE/paid-v2-cutover-intent"; reject missing_quiescence; touch "$BP_STATE/paid-v2-cutover-intent"
rm "$BP_STATE/paid-v2-cutover-intent"; ln -s accounts.tsv "$BP_STATE/paid-v2-cutover-intent"; reject symlink_quiescence; rm "$BP_STATE/paid-v2-cutover-intent"; touch "$BP_STATE/paid-v2-cutover-intent"
touch "$BP_STATE/paid-state-uncertain"; reject unresolved_partial_write; rm "$BP_STATE/paid-state-uncertain"
rm "$BP_STATE/member-events.tsv"; reject partial_member_family; restore
printf 'bad\t10' >> "$BP_STATE/accounts.tsv"; reject partial_row; restore
cat "$T/accounts" >> "$BP_STATE/accounts.tsv"; reject duplicate_account; restore
sed 's/\t10\t/\t2147483648\t/' "$T/accounts" > "$BP_STATE/accounts.tsv"; reject high_account; restore
printf 'a:b\t10\t1800000000\t0\t0\t0\t\t\tv:old-receipt\n' > "$BP_STATE/accounts.tsv"; reject account_receipt; restore
sed 's/\t10\t1\t/\t2147483648\t1\t/' "$T/members" > "$BP_STATE/members.tsv"; reject high_member; restore
cat "$T/members" >> "$BP_STATE/members.tsv"; reject duplicate_member; restore
printf 'm:old\t1700000000\t2member\tadd\t10\t10\tcontroller\t10\n' > "$BP_STATE/member-events.tsv"; reject member_receipt; restore
sed 's/1900000000/2147483648/' "$T/rental" > "$BP_STATE/rental-devices.tsv"; reject high_rental_lease; restore
cat "$T/rental" >> "$BP_STATE/rental-devices.tsv"; reject duplicate_rental; restore
printf 'r:old\ta:b\t10\t1700000000\tp:1\n' > "$BP_STATE/rental-events.tsv"; reject rental_receipt; restore
sed 's/Vendo1/1Vendo/' "$T/controllers" > "$BP_STATE/controllers.tsv"; reject incompatible_controller; restore
printf '0\n' > "$BP_STATE/member-revision"; reject rolled_back_member_revision; restore
exec 9<"$BP_RUN/paid-financial.lock"
flock -n 9 || exit 1
reject writer_busy
flock -u 9
exec 9<&-
pass
printf 'a:b\t2147483647\t2147483647\t2147483647\t0\t2147483647\t\t\t\n' > "$BP_STATE/accounts.tsv"
printf '2member\tlabel\t1\tsha256i\tsalt\thash\t4096\t2147483647\t1\t2147483647\tadmin\n' > "$BP_STATE/members.tsv"
printf 'a:b\tsecret\t2147483647\tlabel\t2147483647\n' > "$BP_STATE/rental-devices.tsv"
pass || { echo 'PAY-0756 valid signed-32 v1 state rejected' >&2; exit 1; }
restore
echo 'PAY-0755 installed migration preflight: valid read-only scan; partial, replay, corrupt and incompatible state denied'
