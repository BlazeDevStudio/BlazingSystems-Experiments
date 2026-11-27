#!/bin/sh
# FSYNC-0644 — integrated synthetic signed v2 journal + durable syscalls.
# No payment device/customer storage; root must be disposable /tmp.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-v2-atomic-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
cc -std=c11 -Wall -Wextra -Werror -O2 -D_GNU_SOURCE -DBLAZE_FIXTURE_ONLY \
  "$BASE/tools/v060_durable_replace.c" -o "$T/native-fixture"
chmod 700 "$T/native-fixture"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' > "$T/ledger.tsv"
sha="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$sha" >> "$T/ledger.tsv"
secret='3333333333333333333333333333333333333333333333333333333333333333'
printf 'ctrlOne\t%s\n' "$secret" > "$T/controller-keys.tsv"
chmod 600 "$T/.blaze-v2-fixture-only" "$T/ledger.tsv" "$T/controller-keys.tsv"
export BLAZE_V2_ATOMIC_BIN="$T/native-fixture"
AUTH="$BASE/tools/v060_journal_auth_fixture.sh"
hash() { sha256sum "$T/ledger.tsv" | cut -d' ' -f1; }
bank() { awk -F '\t' -v u="$1" '$1=="A"&&$2==u {print $3;exit}' "$T/ledger.tsv"; }
rent() { awk -F '\t' -v u="$1" '$1=="L"&&$2==u {print $3;exit}' "$T/ledger.tsv"; }
sign() {
  printf 'BLAZE-V2-AUTH-FIXTURE/1\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$secret" -r | awk '{print $1}'
}
signed() {
  mac="$(sign "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8")"
  sh "$AUTH" "$T" "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$mac"
}
expect_failure() {
  previous="$(hash)"
  set +e
  signed "$@" > "$T/refused" 2>"$T/failure"
  rc=$?
  set -e
  [ "$rc" -ne 0 ] || { echo "faulted native signed transfer reported success" >&2;exit 1; }
  ! grep -Fq COMMIT "$T/refused" || { echo "ambiguous durable commit produced ACK" >&2;exit 1; }
  [ "$(hash)" = "$previous" ] || { echo "precommit error changed balances" >&2;exit 1; }
}
# Correctly signed, fsync-backed committed member topup, receipt and floor.
result="$(signed ctrlOne 1 ctrlOne:1 AM alice - 40 1000)"
[ "$result" = "$(printf 'COMMIT\t140')" ]
[ "$(bank alice):$(bank bob)" = '140:200' ]
[ "$(signed ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'REPLAY\t140')" ]
[ "$(bank alice)" -eq 140 ]
# Authenticating a different amount with the original MAC must fail, without
# even reaching the native fsync commit helper.
old="$(hash)"
original_mac="$(sign ctrlOne 2 ctrlOne:2 TM alice bob 30 1000)"
wrong='0000000000000000000000000000000000000000000000000000000000000000'
set +e
sh "$AUTH" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 30 1000 "$wrong" >"$T/refused" 2>"$T/failure"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash)" = "$old" ]

# Flush failure and rename failure both leave authoritative bank+receipt intact.
export BLAZE_DURABLE_TEST_FAULT=before-source-fsync
expect_failure ctrlOne 2 ctrlOne:2 TM alice bob 30 1000
export BLAZE_DURABLE_TEST_FAULT=before-rename
expect_failure ctrlOne 2 ctrlOne:2 TM alice bob 30 1000
unset BLAZE_DURABLE_TEST_FAULT
# Failure AFTER rename may have committed balances + receipt on host, but
# no ACK can be issued before parent dir durability is established.
export BLAZE_DURABLE_TEST_FAULT=after-rename-before-dir-fsync
set +e
sh "$AUTH" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 30 1000 "$original_mac" >"$T/refused" 2>"$T/failure"
rc=$?
set -e
[ "$rc" -ne 0 ]
! grep -Fq COMMIT "$T/refused"
grep -Fq UNCERTAIN "$T/failure"
unset BLAZE_DURABLE_TEST_FAULT
[ "$(bank alice):$(bank bob)" = '110:230' ]
[ "$(signed ctrlOne 2 ctrlOne:2 TM alice bob 30 1000)" = "$(printf 'REPLAY\t110')" ]
[ "$(( $(bank alice) + $(bank bob) ))" -eq 340 ]
# Rental paid extension uses same single replay+balance/floor store.
[ "$(signed ctrlOne 3 ctrlOne:3 LR dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ]
[ "$(signed ctrlOne 3 ctrlOne:3 LR dev01 - 600 1000)" = "$(printf 'REPLAY\t1600')" ]
[ "$(rent dev01)" -eq 1600 ]
[ "$(awk -F '\t' '$1=="C"&&$2=="ctrlOne"{print $3}' "$T/ledger.tsv")" -eq 3 ]
[ "$(awk -F '\t' '$1=="R"&&$2=="ctrlOne"{n++} END{print n+0}' "$T/ledger.tsv")" -eq 3 ]

# An arbitrary nonfixture helper cannot be substituted into the signed flow.
old="$(hash)"
BLAZE_V2_ATOMIC_BIN=/bin/true
set +e
signed ctrlOne 4 ctrlOne:4 AM alice - 1 1000 >"$T/refused" 2>"$T/failure"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash)" = "$old" ]
BLAZE_V2_ATOMIC_BIN="$T/native-fixture"
export BLAZE_V2_ATOMIC_BIN

# Data corruption must block even a signed transaction, not ACK with
# balances guessed from a partially damaged TSV.
sed 's/A\talice\t110/A\talice\t111/' "$T/ledger.tsv" > "$T/corrupt"
mv "$T/corrupt" "$T/ledger.tsv"
old="$(hash)"
set +e
signed ctrlOne 4 ctrlOne:4 AM alice - 1 1000 >"$T/refused" 2>"$T/failure"
rc=$?
set -e
[ "$rc" -ne 0 ] && [ "$(hash)" = "$old" ]
grep -Fq 'SHA-256 mismatch' "$T/failure"
echo 'FSYNC-0644 PASS: live synthetic HMAC controller -> balances+receipt+highwater -> source fsync/renameat/dir fsync, pre/post fault no false ACK, replay and tamper fail closed'
echo 'NOT PRODUCTION: Linux /tmp binary fixture, no verified OpenWrt NAND/overlay, no durable v1 migration or real paid endpoint'
