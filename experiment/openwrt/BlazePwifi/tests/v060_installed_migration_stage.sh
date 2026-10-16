#!/bin/sh
# PAY-0765: exercise the real installed candidate command on disposable state.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2_migration_stage.sh"
NATIVE="$ROOT/tools/v060_journal_authority_native.c"
cmp -s "$NATIVE" "$ROOT/openwrt/paid-authority/src/v060_journal_authority.c"
sh -n "$STAGE"
T="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
export BP_STATE="$T/state" BP_RUN="$T/run" BP_SNAPSHOT_ROOT="$T/captures"
mkdir -m 700 "$BP_STATE" "$BP_RUN" "$BP_SNAPSHOT_ROOT" "$BP_STATE/targets" "$T/bin"
: > "$BP_RUN/paid-financial.lock"
printf 'FROZEN\t1700000000\n' > "$BP_STATE/paid-v2-cutover-intent"
printf 'wifi01\t0\t0\t0\t0\t0\t\t\t\n' > "$BP_STATE/accounts.tsv"
: > "$BP_STATE/vouchers.tsv"
printf 'alice\tAlice\t1\tsha256i\tSalt\tHash\t4096\t120\t1\t100\tfixture\n' > "$BP_STATE/members.tsv"
printf 'bob\tBob\t1\tsha256i\tSalt2\tHash2\t4096\t0\t1\t100\tfixture\n' >> "$BP_STATE/members.tsv"
printf 'm:1\t100\talice\tadd\t20\t20\tVendo1\t\n' > "$BP_STATE/member-events.tsv"
printf '1\n' > "$BP_STATE/member-revision"
printf 'dev01\tSecret\t1800000000\tTerminal1\t100\n' > "$BP_STATE/rental-devices.tsv"
paid_rental='r:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
printf '%s\tdev01\t1800000000\t100\tp:2\n' "$paid_rental" > "$BP_STATE/rental-events.tsv"
chmod 600 "$BP_STATE"/*.tsv "$BP_STATE/member-revision"
archive_dir="$BP_SNAPSHOT_ROOT/v1-frozen-snapshot"
mkdir -m 700 "$archive_dir"
refresh_archive() {
  tar -cf "$archive_dir/state.tar" -C "$BP_STATE" .
  (cd "$archive_dir" && sha256sum state.tar > SHA256SUMS)
}
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
stage() { sh "$STAGE" --stage --operator-quiesced; }
reject() {
  if stage > "$T/out" 2> "$T/err"; then echo "FAIL: $1 admitted" >&2; exit 1; fi
  [ ! -s "$T/out" ] || { echo "FAIL: $1 emitted success" >&2; exit 1; }
  grep -q 'paid_ack_authorized=0; migration_authorized=0' "$T/err"
  case "$1" in
    unsupported_wifi_money) expected=unsupported_or_corrupt_wifi_money;;
    unsupported_voucher_money|unresolved_coin_window) expected="$1";;
    missing_freeze) expected=frozen_marker_required;;
    malformed_frozen_marker|incomplete_frozen_marker) expected=frozen_marker_invalid;;
    hardlinked_frozen_marker) expected=frozen_marker_metadata;;
    changed_frozen_archive_marker) expected=frozen_archive_marker_mismatch;;
    overflowing_member_receipt|orphan_member_source|orphan_transfer_recipient|same_transfer_recipient|bad_transfer_balance|bad_add_amount|bad_subtract_amount|bad_set_origin|bad_transfer_amount|bad_transfer_target_underflow|bad_transfer_sender_overflow|recreated_member_epoch|trimmed_delete_recreated_member|recreated_transfer_recipient) expected=member_receipt_corrupt;;
    malformed_rental_receipt) expected=rental_receipt_corrupt;;
    corrupt_archive) expected=archive_digest_mismatch;;
    concurrent_writer) expected=writer_busy;;
    partial_archive_copy) expected=stage_archive_copy;;
    sync_failure) expected=stage_sync_uncertain;;
    *) expected="$1";;
  esac
  grep -q "$expected" "$T/err" || { cat "$T/err" >&2; exit 1; }
  [ "$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)" = "$before" ] || {
    echo "FAIL: $1 changed live money" >&2; exit 1;
  }
  [ ! -e "$BP_SNAPSHOT_ROOT/v1-v2-candidate" ]
  case "$1" in partial_archive_copy|sync_failure) ;;
    *) rm -rf "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp";;
  esac
}
if sh "$STAGE" > "$T/out" 2> "$T/err"; then echo 'implicit stage admitted' >&2; exit 1; fi

# PAY-0769: producer writes a private, canonical FROZEN<TAB>epoch marker.
# A valid money snapshot is not admissible with a fabricated freeze marker.
marker="$BP_STATE/paid-v2-cutover-intent"
printf 'PENDING\t1700000000\n' > "$marker"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject malformed_frozen_marker
printf 'FROZEN\t1700000000' > "$marker"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject incomplete_frozen_marker
printf 'FROZEN\t1700000000\n' > "$marker"
refresh_archive
ln "$marker" "$T/hardlinked-marker"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject hardlinked_frozen_marker
rm "$T/hardlinked-marker"
# Fresh syntactically valid freeze marker, but state.tar was captured under
# another freeze epoch. Reject rather than pair old archived receipts with
# a different current cutover proof.
printf 'FROZEN\t1700000001\n' > "$marker"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject changed_frozen_archive_marker
printf 'FROZEN\t1700000000\n' > "$marker"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"

printf 'wifi01\t1\t0\t0\t0\t0\t\t\t\n' > "$BP_STATE/accounts.tsv"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject unsupported_wifi_money
printf 'wifi01\t0\t0\t0\t0\t0\t\t\t\n' > "$BP_STATE/accounts.tsv"
printf 'voucher\n' > "$BP_STATE/vouchers.tsv"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject unsupported_voucher_money
: > "$BP_STATE/vouchers.tsv"
printf 'm:2\t100\talice\tadd\t2147483648\t2147483648\tVendo1\t\n' >> "$BP_STATE/member-events.tsv"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject overflowing_member_receipt
sed -i '$d' "$BP_STATE/member-events.tsv"

# PAY-0766: operator-only staging must refuse orphan or recycled paid
# identity history, even when the frozen archive digest matches. All inputs
# are disposable, and the helper rejects ANY candidate or money write.
cp -p "$BP_STATE/member-events.tsv" "$T/member-events.provenance.good"
stage_member_refuse() {
  why="$1"
  refresh_archive
  before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
  reject "$why"
  cp -p "$T/member-events.provenance.good" "$BP_STATE/member-events.tsv"
}
printf 'm:orphan:2\t100\tghost\tadd\t10\t10\tVendo1\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse orphan_member_source
printf 'm:missing:2\t100\talice\ttransfer\t-4\t116\tVendo1\t116:ghost:4\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse orphan_transfer_recipient
printf 'm:self:2\t100\talice\ttransfer\t-4\t116\tVendo1\t116:alice:4\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse same_transfer_recipient
printf 'm:bad:2\t100\talice\ttransfer\t-4\t116\tVendo1\t116:bob:2147483648\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_transfer_balance
# PAY-0767: a well-formed receipt can still contradict the actual v1
# writer's kind/delta/result contract. Such history must never become a
# staged A-opening without an explicit owner reconciliation.
printf 'm:add:broken\t100\talice\tadd\t5\t4\tVendo1\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_add_amount
printf 'm:sub:broken\t100\talice\tsubtract\t5\t5\tVendo1\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_subtract_amount
printf 'm:set:broken\t100\talice\tset\t1\t0\tVendo1\t0\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_set_origin
printf 'm:transfer:wrong\t100\talice\ttransfer\t-4\t116\tVendo1\t116:bob:4\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_transfer_amount
printf 'm:transfer:dest\t100\talice\ttransfer\t-4\t4\tVendo1\t116:bob:3\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_transfer_target_underflow
printf 'm:transfer:sender\t100\talice\ttransfer\t-4\t4\tVendo1\t2147483647:bob:4\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse bad_transfer_sender_overflow
printf 'admin:2:alice\t101\talice\tdelete\t0\t0\tfixture\t\n' >> "$BP_STATE/member-events.tsv"
printf 'admin:3:alice\t102\talice\tcreate\t0\t0\tfixture\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse recreated_member_epoch
printf 'admin:3:alice\t102\talice\tcreate\t0\t0\tfixture\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse trimmed_delete_recreated_member
printf 'm:transfer:2\t100\talice\ttransfer\t-4\t116\tVendo1\t116:bob:4\n' >> "$BP_STATE/member-events.tsv"
printf 'admin:3:bob\t101\tbob\tdelete\t0\t0\tfixture\t\n' >> "$BP_STATE/member-events.tsv"
printf 'admin:4:bob\t102\tbob\tcreate\t0\t0\tfixture\t\n' >> "$BP_STATE/member-events.tsv"
stage_member_refuse recreated_transfer_recipient

printf 'r:short\tdev01\t1800000000\t100\tp:2\n' >> "$BP_STATE/rental-events.tsv"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject malformed_rental_receipt
sed -i '$d' "$BP_STATE/rental-events.tsv"
printf 'PENDING\n' > "$BP_STATE/targets/Vendo1.progress"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject unresolved_coin_window
rm "$BP_STATE/targets/Vendo1.progress"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
printf 'corrupt' >> "$archive_dir/state.tar"
reject corrupt_archive
refresh_archive
rm "$BP_STATE/paid-v2-cutover-intent"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
reject missing_freeze
printf 'FROZEN\t1700000000\n' > "$BP_STATE/paid-v2-cutover-intent"
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
(
  exec 9< "$BP_RUN/paid-financial.lock"
  flock -x 9
  : > "$T/writer-held"
  while [ ! -e "$T/release-writer" ]; do sleep 0.05; done
) &
writer=$!
tries=0
while [ ! -e "$T/writer-held" ] && [ "$tries" -lt 100 ]; do sleep 0.05; tries=$((tries+1)); done
[ -e "$T/writer-held" ]
reject concurrent_writer
: > "$T/release-writer"
wait "$writer"
rm "$T/writer-held" "$T/release-writer"
printf '#!/bin/sh\nprintf partial > "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp/state.tar"\nexit 1\n' > "$T/bin/cp"
chmod +x "$T/bin/cp"
PATH="$T/bin:$PATH" reject partial_archive_copy
[ -d "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp" ]
rm -rf "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp"
rm "$T/bin/cp"
printf '#!/bin/sh\nexit 1\n' > "$T/bin/sync"
chmod +x "$T/bin/sync"
PATH="$T/bin:$PATH" reject sync_failure
[ -d "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp" ]
rm -rf "$BP_SNAPSHOT_ROOT/.v1-v2-candidate.tmp"
rm "$T/bin/sync"

# Healthy distinct source/recipient transfer receipts remain acceptable.
printf 'm:healthy:2\t100\talice\ttransfer\t-4\t4\tVendo1\t116:bob:4\n' >> "$BP_STATE/member-events.tsv"
refresh_archive
before="$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)"
result="$(stage)"
printf '%s\n' "$result" | grep -q 'CANDIDATE.*paid_ack_authorized=0; migration_authorized=0'
candidate="$BP_SNAPSHOT_ROOT/v1-v2-candidate"
[ -d "$candidate" ] && [ ! -L "$candidate" ]
(cd "$candidate" && sha256sum -c SHA256SUMS >/dev/null)
tar -xOf "$candidate/state.tar" ./member-events.tsv | cmp - "$BP_STATE/member-events.tsv"
tar -xOf "$candidate/state.tar" ./rental-events.tsv | cmp - "$BP_STATE/rental-events.tsv"
archive_hash="$(sha256sum "$candidate/state.tar" | awk '{print $1}')"
grep -Fx "$(printf 'P\t%s\t1' "$archive_hash")" "$candidate/ledger.tsv"
grep -Fx "$(printf 'A\talice\t120')" "$candidate/ledger.tsv"
grep -Fx "$(printf 'L\tdev01\t1800000000')" "$candidate/ledger.tsv"
if stage > "$T/out" 2> "$T/err"; then echo 'lost-response retry overwrote candidate' >&2; exit 1; fi
grep -q prior_candidate_present "$T/err"
[ "$(find "$BP_STATE" -type f -exec sha256sum {} + | LC_ALL=C sort)" = "$before" ]

# The same provenance record is parsed and retained by the actual native
# journal engine. This marked fixture cannot authorize installed payments.
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY "$NATIVE" -lcrypto -o "$T/native"
native_root="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T" "$native_root"' EXIT HUP INT TERM
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$native_root/.blaze-v2-fixture-only"
key=3333333333333333333333333333333333333333333333333333333333333333
printf 'ctrlOne\t%s\n' "$key" > "$native_root/controller-keys.tsv"
cp "$candidate/ledger.tsv" "$native_root/ledger.tsv"
chmod 700 "$native_root"
chmod 600 "$native_root"/* "$native_root/.blaze-v2-fixture-only"
signed="$(printf 'BLAZE-V2-AUTH-FIXTURE/1\tctrlOne\t1\tctrlOne:1\tAM\talice\t-\t1\t1000\n' |
  openssl dgst -sha256 -mac HMAC -macopt "hexkey:$key" -r | awk '{print $1}')"
[ "$("$T/native" "$native_root" ctrlOne 1 ctrlOne:1 AM alice - 1 1000 "$signed")" = "$(printf 'COMMIT\t121')" ]
grep -Fx "$(printf 'P\t%s\t1' "$archive_hash")" "$native_root/ledger.tsv"
native_digest="$(sha256sum "$native_root/ledger.tsv" | awk '{print $1}')"
if "$T/native" "$native_root" ctrlOne 1 ctrlOne:1 AM alice - 1 1000 "$signed" > "$T/replay"; then
  grep -Fx "$(printf 'REPLAY\t121')" "$T/replay"
else echo 'native replay failed' >&2; exit 1; fi
[ "$(sha256sum "$native_root/ledger.tsv" | awk '{print $1}')" = "$native_digest" ]
sed -i 's/^P\t/P\tinvalid\t/' "$native_root/ledger.tsv"
sed -i '$d' "$native_root/ledger.tsv"
printf 'H\t%s\n' "$(sha256sum "$native_root/ledger.tsv" | awk '{print $1}')" >> "$native_root/ledger.tsv"
tampered="$(sha256sum "$native_root/ledger.tsv" | awk '{print $1}')"
if "$T/native" "$native_root" ctrlOne 1 ctrlOne:1 AM alice - 1 1000 "$signed" > "$T/out" 2> "$T/err"; then
  echo 'malformed provenance admitted' >&2; exit 1
fi
[ ! -s "$T/out" ] && [ "$(sha256sum "$native_root/ledger.tsv" | awk '{print $1}')" = "$tampered" ]
echo 'PAY-0765/0766/0767/0769 installed inactive candidate: freeze marker provenance, member identities and transfer arithmetic checked; frozen receipts preserved; partial/replay/corrupt states denied'
