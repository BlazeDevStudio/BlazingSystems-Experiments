#!/bin/sh
# LEDGER-0636: actual HMAC-authorized synthetic POSIX journal bridge regression.
# Intentionally cannot point to customer/device directories.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
ENGINE="$ROOT/tools/v060_journal_auth_fixture.sh"
T="$(mktemp -d /tmp/blaze-v2-auth-fixture-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
command -v openssl >/dev/null 2>&1 || { echo "openssl required for fixture" >&2; exit 1; }
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$T/.blaze-v2-fixture-only"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' > "$T/ledger.tsv"
digest="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$digest" >> "$T/ledger.tsv"
key_one='1111111111111111111111111111111111111111111111111111111111111111'
key_two='2222222222222222222222222222222222222222222222222222222222222222'
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key_one" "$key_two" > "$T/controller-keys.tsv"
chmod 600 "$T/ledger.tsv" "$T/controller-keys.tsv" "$T/.blaze-v2-fixture-only"
ledger_sha() { sha256sum "$T/ledger.tsv" | cut -d' ' -f1; }
bank() { awk -F '\t' -v n="$1" '$1=="A"&&$2==n {print $3;exit}' "$T/ledger.tsv"; }
lease() { awk -F '\t' -v n="$1" '$1=="L"&&$2==n {print $3;exit}' "$T/ledger.tsv"; }
sign() {
  case "$1" in ctrlOne) k="$key_one";; ctrlTwo) k="$key_two";; *) k="$key_one";; esac
  printf 'BLAZE-V2-AUTH-FIXTURE/1\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$k" -r | awk '{print $1}'
}
signed() {
  ctl="$1"; seq="$2"; eid="$3"; action="$4"
  src="$5"; dst="$6"; units="$7"; now="$8"
  mac="$(sign "$ctl" "$seq" "$eid" "$action" "$src" "$dst" "$units" "$now")"
  BLAZE_TEST_FAULT="${BLAZE_TEST_FAULT:-}" sh "$ENGINE" "$T" \
    "$ctl" "$seq" "$eid" "$action" "$src" "$dst" "$units" "$now" "$mac"
}
refuse() {
  previous="$(ledger_sha)"
  if signed "$@" > "$T/denied.log" 2>&1; then
    echo "invalid signed fixture request accepted: $*" >&2
    exit 1
  fi
  [ "$(ledger_sha)" = "$previous" ] || {
    echo "rejected signed request altered balance/receipt" >&2; exit 1
  }
}
[ "$(signed ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'COMMIT\t140')" ]
[ "$(signed ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'REPLAY\t140')" ]
[ "$(bank alice)" = 140 ]
refuse ctrlOne 1 ctrlOne:1 AM alice - 41 1000
refuse ctrlOne 3 ctrlOne:3 AM alice - 20 1000
refuse ctrlOne 02 ctrlOne:02 AM alice - 10 1000
refuse ctrlOne 2 ctrlOne:9 AM alice - 10 1000

# A valid MAC for ctrlOne can never impersonate ctrlTwo, even when signed
# fields would otherwise pass input validation and use the same replay index.
before="$(ledger_sha)"
foreign="$(sign ctrlOne 2 ctrlOne:2 AM alice - 10 1000)"
if BLAZE_TEST_FAULT='' sh "$ENGINE" "$T" ctrlTwo 1 ctrlTwo:1 AM alice - 10 1000 "$foreign" >"$T/denied.log" 2>&1; then
    echo 'HMAC of other controller was accepted' >&2; exit 1
fi
[ "$(ledger_sha)" = "$before" ]
# Changing ANY authenticated field is not a replay; the signature must reject.
proof="$(sign ctrlOne 2 ctrlOne:2 TM alice bob 50 1000)"
for tampered in 'alice dev01 50 1000' 'alice bob 51 1000' 'alice bob 50 1001'; do
    set -- $tampered
    before="$(ledger_sha)"
    if BLAZE_TEST_FAULT='' sh "$ENGINE" "$T" ctrlOne 2 ctrlOne:2 TM "$1" "$2" "$3" "$4" "$proof" >"$T/denied.log" 2>&1; then
        echo "tampered HMAC contents accepted: $tampered" >&2; exit 1
    fi
    [ "$(ledger_sha)" = "$before" ]
done

# First candidate interrupted before atomic rename: neither member changes.
before="$(ledger_sha)"
if BLAZE_TEST_FAULT=before-rename sh "$ENGINE" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 50 1000 "$proof" >"$T/denied.log" 2>&1; then
    echo 'precommit failure got ACK' >&2; exit 1
fi
[ "$(ledger_sha)" = "$before" ]
[ "$(bank alice):$(bank bob)" = '140:200' ]
# Same signed transaction with lost ACK: write+receipt committed together,
# process failed, next signed request REPLAYS it without repeating deduction.
if BLAZE_TEST_FAULT=after-rename-before-ack sh "$ENGINE" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 50 1000 "$proof" >"$T/denied.log" 2>&1; then
    echo 'lost ACK was reported as successful reply' >&2; exit 1
fi
[ "$(bank alice):$(bank bob)" = '90:250' ]
[ "$(signed ctrlOne 2 ctrlOne:2 TM alice bob 50 1000)" = "$(printf 'REPLAY\t90')" ]
[ "$(( $(bank alice) + $(bank bob) ))" -eq 340 ]
[ "$(signed ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ]
[ "$(signed ctrlTwo 1 ctrlTwo:1 LR dev01 - 600 1000)" = "$(printf 'REPLAY\t1600')" ]
[ "$(lease dev01)" -eq 1600 ]

# Keys MUST be well-formed, private, single-link and uniquely scoped.
cp "$T/controller-keys.tsv" "$T/keys-pristine"
chmod 644 "$T/controller-keys.tsv"
refuse ctrlOne 3 ctrlOne:3 AM alice - 1 1000
chmod 600 "$T/controller-keys.tsv"
cat "$T/keys-pristine" >> "$T/controller-keys.tsv"
refuse ctrlOne 3 ctrlOne:3 AM alice - 1 1000
cp "$T/keys-pristine" "$T/controller-keys.tsv"
chmod 600 "$T/controller-keys.tsv"
mv "$T/controller-keys.tsv" "$T/keys-saved"
ln -s "$T/keys-saved" "$T/controller-keys.tsv"
refuse ctrlOne 3 ctrlOne:3 AM alice - 1 1000
rm "$T/controller-keys.tsv"
mv "$T/keys-saved" "$T/controller-keys.tsv"
chmod 600 "$T/controller-keys.tsv"

# Verify receipt pruning never reopens old transaction sequence.
q=3
while [ "$q" -le 15 ]; do
  signed ctrlOne "$q" "ctrlOne:$q" AM alice - 1 1000 > "$T/accepted.log"
  q=$((q+1))
done
[ "$(bank alice)" -eq 103 ]
refuse ctrlOne 1 ctrlOne:1 AM alice - 40 1000
refuse ctrlOne 14 ctrlOne:14 AM alice - 50 1000
[ "$(bank alice)" -eq 103 ]
[ "$(lease dev01)" -eq 1600 ]
[ "$(awk -F '\t' '$1=="R"&&$2=="ctrlOne"{n++} END{print n+0}' "$T/ledger.tsv")" -le 8 ]

# Corrupt the stored journal, then use a VALID authenticated MAC: it must
# refuse an otherwise fresh operation without resetting or altering state.
cp "$T/ledger.tsv" "$T/healthy-ledger"
sed 's/A\talice\t103/A\talice\t1003/' "$T/healthy-ledger" > "$T/ledger.tsv"
before="$(ledger_sha)"
refuse ctrlOne 16 ctrlOne:16 AM alice - 1 1000
[ "$(ledger_sha)" = "$before" ]
grep -q 'SHA-256 mismatch' "$T/denied.log"
cp "$T/healthy-ledger" "$T/ledger.tsv"
# An attempt outside a protected synthetic root never invokes a mutation.
if BLAZE_TEST_FAULT='' sh "$ENGINE" /etc ctrlOne 16 ctrlOne:16 AM alice - 1 1000 "$(sign ctrlOne 16 ctrlOne:16 AM alice - 1 1000)" >/dev/null 2>&1; then
  echo 'non-fixture real device path accepted' >&2; exit 1
fi
echo 'LEDGER-0636 HMAC synthetic journal PASS: per-controller auth, immutable transfer, replay/collision, stale sequence, private keys, precommit and lost ACK, tamper fail-closed'
echo 'NOT PRODUCTION: OpenSSL argv and shell compare not hardened, missing real v1 migration, OpenWrt fsync/dirsync and hardware powercut tests'
