#!/bin/sh
# MIG-0623 POSIX-shell ledger transaction sandbox assertions. NO LIVE RECORDS.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TOOL="$BASE/tools/v060_journal_fixture.sh"
T="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' > "$T/ledger.tsv"
# Integrity footer belongs in the same source snapshot.
body_hash="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$body_hash" >> "$T/ledger.tsv"
chmod 600 "$T/ledger.tsv" "$T/.blaze-v2-fixture-only"
run() { BLAZE_TEST_FAULT="" sh "$TOOL" "$T" "$@"; }
account() { awk -F '\t' -v u="$1" '$1=="A"&&$2==u {print $3;exit}' "$T/ledger.tsv"; }
lease() { awk -F '\t' -v u="$1" '$1=="L"&&$2==u {print $3;exit}' "$T/ledger.tsv"; }
reject() { if run "$@" >"$T/reject.log" 2>&1; then echo "unexpected accepted command" >&2; exit 1; fi; }

# Exact sequence replay must not add prepaid time again.
[ "$(run ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'COMMIT\t140')" ]
[ "$(run ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'REPLAY\t140')" ]
[ "$(account alice)" = 140 ]
# The event name must use the same canonical decimal sequence as its receipt.
# A legacy 02 spelling must fail before write, not corrupt the next read.
before_noncanonical="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
reject ctrlOne 02 ctrlOne:02 TM alice bob 50 1000
[ "$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)" = "$before_noncanonical" ]
reject ctrlOne 1 ctrlOne:1 AM alice - 60 1000
reject ctrlOne 3 ctrlOne:3 AM alice - 10 1000
reject ctrlOne 2 ctrlOne:9 AM alice - 10 1000
[ "$(account alice)" = 140 ]

# Simulate ENOSPC before rename. Both account balances and ID floor unchanged.
if BLAZE_TEST_FAULT=before-rename sh "$TOOL" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 50 1000 >"$T/fault.log" 2>&1; then
  echo "before-rename failure acknowledged" >&2; exit 1
fi
[ "$(account alice):$(account bob)" = 140:200 ]
# Simulate process crash *after* rename and before response; retry must replay.
if BLAZE_TEST_FAULT=after-rename-before-ack sh "$TOOL" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 50 1000 >"$T/fault.log" 2>&1; then
  echo "lost ACK was misreported as a successful direct reply" >&2; exit 1
fi
[ "$(account alice):$(account bob)" = 90:250 ]
[ "$(run ctrlOne 2 ctrlOne:2 TM alice bob 50 1000)" = "$(printf 'REPLAY\t90')" ]
[ "$(( $(account alice) + $(account bob) ))" -eq 340 ]
# Simulated receipt EIO cannot commit new money and must not consume sequence.
if BLAZE_TEST_FAULT=receipt-eio sh "$TOOL" "$T" ctrlOne 3 ctrlOne:3 AM alice - 30 1000 >"$T/fault.log" 2>&1; then
  echo "receipt EIO acknowledged" >&2; exit 1
fi
[ "$(account alice)" = 90 ]
[ "$(run ctrlOne 3 ctrlOne:3 AM alice - 30 1000)" = "$(printf 'COMMIT\t120')" ]

# A rental lease lives in the *same* money+receipt snapshot, not a second TSV.
[ "$(run ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ]
[ "$(run ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" = "$(printf 'REPLAY\t1600')" ]
[ "$(lease dev01)" = 1600 ]
reject ctrlTwo 1 ctrlTwo:1 LR dev01 - 900 1000
reject ctrlThree 1 ctrlTwo:1 AM alice - 50 1000

# Reclaim bounded old receipts without reopening credit for stale sequence.
s=4
while [ "$s" -le 24 ]; do
  run ctrlOne "$s" "ctrlOne:$s" AM alice - 1 1000 > "$T/run.log"
  s=$((s+1))
done
[ "$(account alice)" -eq 141 ]
[ "$(awk -F '\t' '$1=="R"&&$2=="ctrlOne" {n++} END {print n+0}' "$T/ledger.tsv")" -le 8 ]
reject ctrlOne 1 ctrlOne:1 AM alice - 40 1000
[ "$(account alice)" -eq 141 ]
# Two independent clients race for the same sequence. The lock may reject one
# with BUSY, but a retry of that exact request must replay without new credit.
(set +e; BLAZE_TEST_FAULT="" sh "$TOOL" "$T" ctrlRace 1 ctrlRace:1 AM alice - 9 1000 >"$T/parallel1" 2>&1; rc="$?"; printf '%s\n' "$rc" >"$T/parallel1.rc"; exit 0) &
p1=$!
(set +e; BLAZE_TEST_FAULT="" sh "$TOOL" "$T" ctrlRace 1 ctrlRace:1 AM alice - 9 1000 >"$T/parallel2" 2>&1; rc="$?"; printf '%s\n' "$rc" >"$T/parallel2.rc"; exit 0) &
p2=$!
wait "$p1" "$p2"
[ "$(account alice)" -eq 150 ]
grep -Eq '^COMMIT[[:space:]]150$' "$T/parallel1" "$T/parallel2"
[ "$(run ctrlRace 1 ctrlRace:1 AM alice - 9 1000)" = "$(printf 'REPLAY\t150')" ]
[ "$(account alice)" -eq 150 ]

# An otherwise valid numeric record with a stale checksum is corruption.
cp "$T/ledger.tsv" "$T/intact-snapshot"
awk -F '\t' 'BEGIN {OFS="\t"} $1=="A" && $2=="alice" {$3+=5} {print}' "$T/intact-snapshot" >"$T/modified"
mv "$T/modified" "$T/ledger.tsv"
reject ctrlOne 25 ctrlOne:25 AM alice - 1 1000
grep -Fq 'SHA-256 mismatch' "$T/reject.log"
[ "$(account alice)" -eq 155 ]
cp "$T/intact-snapshot" "$T/ledger.tsv"
[ "$(account alice)" -eq 150 ]

# Additional trailing record must be rejected (not partially applied).
cp "$T/ledger.tsv" "$T/pristine"
printf 'INVALID\tRECORD\n' >> "$T/ledger.tsv"
reject ctrlOne 25 ctrlOne:25 AM alice - 1 1000
[ "$(account alice)" -eq 150 ]
cmp -s "$T/ledger.tsv" "$T/pristine" && { echo "corruption setup failed" >&2; exit 1; }
# Unsafe roots must not be accepted even with a valid-looking command.
if BLAZE_TEST_FAULT="" sh "$TOOL" /etc ctrlOne 25 ctrlOne:25 AM alice - 1 1000 >/dev/null 2>&1; then
  echo "system path accepted by fixture" >&2; exit 1
fi
echo 'MIG-0624 synthetic POSIX journal PASS: checksum, concurrent retry, member/rental+receipt snapshot, stale-window refusal, EIO/lost-ACK and corruption negative cases'
echo 'NOT PRODUCTION: no real authentication, fsync durability, historical v1 migration, or hardware flash/power-loss validation'
