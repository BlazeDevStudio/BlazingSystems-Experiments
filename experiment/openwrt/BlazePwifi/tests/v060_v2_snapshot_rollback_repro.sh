#!/bin/sh
# ROLLBACK-0691 / EXPECTED UNSAFE REPRO ONLY.
# Show that an older, checksum-valid v2 fixture snapshot can erase already-
# acknowledged member and rental credits and reaccept their signed events.
# A successful test is NOT a fixed anti-rollback protocol or hardware proof.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
chmod 700 "$T"
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY \
  "$BASE/tools/v060_journal_authority_native.c" -lcrypto -o "$T/native"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
KEY1=3333333333333333333333333333333333333333333333333333333333333333
KEY2=4444444444444444444444444444444444444444444444444444444444444444
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$KEY1" "$KEY2" > "$T/controller-keys.tsv"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' > "$T/ledger.tsv"
sha256sum "$T/ledger.tsv" | awk '{printf "H\t%s\n",$1}' >> "$T/ledger.tsv"
chmod 600 "$T/.blaze-v2-fixture-only" "$T/controller-keys.tsv" "$T/ledger.tsv"
sign() {
  case "$1" in
    ctrlOne) key="$KEY1" ;;
    ctrlTwo) key="$KEY2" ;;
    *) echo 'unexpected mock controller' >&2; return 9 ;;
  esac
  printf 'BLAZE-V2-AUTH-FIXTURE/1\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$key" -r | awk '{print $1}'
}
run() {
  mac="$(sign "$@")" || exit 9
  "$T/native" "$T" "$@" "$mac"
}
bank() { awk -F '\t' '$1=="A"&&$2=="alice"{print $3;exit}' "$T/ledger.tsv"; }
lease() { awk -F '\t' '$1=="L"&&$2=="dev01"{print $3;exit}' "$T/ledger.tsv"; }
floor() { awk -F '\t' -v ctl="$1" '$1=="C"&&$2==ctl{print $3;exit}' "$T/ledger.tsv"; }
valid_footer() {
  actual="$(sed '$d' "$T/ledger.tsv" | sha256sum | awk '{print $1}')"
  recorded="$(tail -n 1 "$T/ledger.tsv" | cut -f2)"
  [ "$actual" = "$recorded" ] && [ "${#actual}" -eq 64 ]
}
valid_footer || { echo 'failed synthetic initial checksum' >&2;exit 1; }

[ "$(run ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'COMMIT\t140')" ] || exit 1
[ "$(bank)" = 140 ] && [ "$(floor ctrlOne)" = 1 ] || exit 1
# This snapshot is internally well formed, but will become STALE.
cp "$T/ledger.tsv" "$T/older-valid.snapshot"
chmod 600 "$T/older-valid.snapshot"
older_digest="$(sha256sum "$T/older-valid.snapshot" | cut -d' ' -f1)"
[ "$(run ctrlOne 2 ctrlOne:2 AM alice - 30 1000)" = "$(printf 'COMMIT\t170')" ] || exit 1
[ "$(run ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ] || exit 1
[ "$(bank):$(lease):$(floor ctrlOne):$(floor ctrlTwo)" = '170:1600:2:1' ] || exit 1
valid_footer || exit 1

# Simulate an UNAUTHORIZED manually restored old ledger file, not a power cut.
# Both the bank and the retained signed receipt/floor disappear together.
# The snapshot's original checksum is still valid: freshness is UNATTESTED.
cp "$T/older-valid.snapshot" "$T/ledger.tsv"
[ "$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)" = "$older_digest" ] || exit 1
valid_footer || { echo 'the stale snapshot was corrupt; not a valid repro' >&2;exit 1; }
[ "$(bank):$(lease):$(floor ctrlOne)" = '140:0:1' ] || exit 1
[ -z "$(floor ctrlTwo)" ] || exit 1

# The exact previously ACKed signed messages are now issued a NEW COMMIT,
# not REPLAY. This is unsafe even if repeating them reconstructs balances:
# the system has LOST knowledge of ACKs and could miss other paid operations.
after_member="$(run ctrlOne 2 ctrlOne:2 AM alice - 30 1000)" || exit 1
after_rental="$(run ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" || exit 1
if [ "$after_member" != "$(printf 'COMMIT\t170')" ] ||
   [ "$after_rental" != "$(printf 'COMMIT\t1600')" ]; then
  echo 'ROLLBACK-0691 REPRO NOT OBSERVED: inspect changed behavior, do not claim fixed without stronger safety tests' >&2
  exit 1
fi
[ "$(bank):$(lease)" = '170:1600' ] || exit 1
valid_footer || exit 1
echo 'ROLLBACK-0691 EXPECTED UNSAFE REPRO: older valid snapshot erased ACKed credits and sequence floors; originally signed member+rental events were reaccepted as NEW COMMIT.'
echo 'P0 STILL OPEN: this proves a lab-only anti-rollback hole; v0.6 live migration/update MUST REMAIN BLOCKED. NO REAL POWER-CUT TEST.'
