#!/bin/sh
# V2NATIVE-0668 — compiled HMAC/fsync journal fixture, not real customer money.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/tools/v060_journal_authority_native.c"
cmp -s "$SRC" "$ROOT/openwrt/paid-authority/src/v060_journal_authority.c" || {
  echo 'paid authority package source diverges from tested journal source' >&2; exit 1;
}
T="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
RT="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
NUM="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
RENT="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
BOUND="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T" "$RT" "$NUM" "$RENT" "$BOUND"' EXIT HUP INT TERM
umask 077
chmod 700 "$T"
command -v cc >/dev/null || { echo 'C compiler missing';exit 1; }
command -v openssl >/dev/null || { echo 'OpenSSL test signer missing';exit 1; }
# An unguarded build must be rejected at compile time.
if cc -std=c11 -Wall -Wextra -Werror -O2 "$SRC" -lcrypto -o "$T/unguarded" 2>"$T/compile-error"; then
  echo 'native fixture compiled without LAB-ONLY guard' >&2; exit 1
fi
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_FIXTURE_ONLY "$SRC" \
  -lcrypto -o "$T/native"
# Build the production profile too. The test-only root override keeps this
# process confined to a marked disposable /tmp tree; production has no such
# override and is bound to /etc/blazepwifi/state.
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_RUNTIME_AUTHORITY \
  -DBLAZE_RUNTIME_TEST_ROOT_OVERRIDE "$SRC" -lcrypto -o "$T/runtime"
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$T/.blaze-v2-fixture-only"
key=3333333333333333333333333333333333333333333333333333333333333333
key2=4444444444444444444444444444444444444444444444444444444444444444
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key" "$key2" > "$T/controller-keys.tsv"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' >"$T/ledger.tsv"
base="$(sha256sum "$T/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$base" >>"$T/ledger.tsv"
chmod 600 "$T/.blaze-v2-fixture-only" "$T/controller-keys.tsv" "$T/ledger.tsv"
sign_domain() {
  domain="$1"; shift
  case "$1" in
    ctrlOne) controller_key="$key" ;;
    ctrlTwo) controller_key="$key2" ;;
    *) echo "unknown synthetic controller" >&2; return 1 ;;
  esac
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$domain" "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$controller_key" -r | awk '{print $1}'
}
sign() { sign_domain 'BLAZE-V2-AUTH-FIXTURE/1' "$@"; }
sign_runtime() { sign_domain 'BLAZE-V2-AUTH/1' "$@"; }
# PAY-0753: v1 permits numeric-leading member IDs and generated rental IDs
# are hexadecimal. A v2 authority must preserve those exact identities.
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$NUM/.blaze-v2-fixture-only"
printf 'ctrlOne\t%s\n' "$key" >"$NUM/controller-keys.tsv"
printf 'V\t2\nA\t7alice\t100\nA\t_bob\t20\nL\t3dev01\t0\n' >"$NUM/ledger.tsv"
num_base="$(sha256sum "$NUM/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$num_base" >>"$NUM/ledger.tsv"
chmod 600 "$NUM/.blaze-v2-fixture-only" "$NUM/controller-keys.tsv" "$NUM/ledger.tsv"
num_run() { num_signed="$(sign "$@")"; "$T/native" "$NUM" "$@" "$num_signed"; }
[ "$(num_run ctrlOne 1 ctrlOne:1 AM 7alice - 40 1000)" = "$(printf 'COMMIT\t140')" ] || {
  echo 'PAY-0753 numeric-leading member identity rejected' >&2; exit 1;
}
[ "$(num_run ctrlOne 1 ctrlOne:1 AM 7alice - 40 1000)" = "$(printf 'REPLAY\t140')" ]
[ "$(num_run ctrlOne 2 ctrlOne:2 TM 7alice _bob 10 1000)" = "$(printf 'COMMIT\t130')" ]
[ "$(num_run ctrlOne 3 ctrlOne:3 LR 3dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ]
num_digest="$(sha256sum "$NUM/ledger.tsv" | cut -d' ' -f1)"
num_signed="$(sign ctrlOne 4 ctrlOne:4 AM 7alice:bad - 1 1000)"
if "$T/native" "$NUM" ctrlOne 4 ctrlOne:4 AM 7alice:bad - 1 1000 "$num_signed" >"$NUM/bad-out" 2>"$NUM/bad-error"; then
  echo 'PAY-0753 delimiter-bearing subject accepted' >&2; exit 1;
fi
[ ! -s "$NUM/bad-out" ] &&
  [ "$(sha256sum "$NUM/ledger.tsv" | cut -d' ' -f1)" = "$num_digest" ]
# PAY-0754: installed rental IDs allow colon and up to 96 characters. A
# valid existing paid lease must survive the v2 parser and exact replay.
rental_id="3zone:$(printf '%090d' 0)"
[ "${#rental_id}" -eq 96 ]
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$RENT/.blaze-v2-fixture-only"
printf 'ctrlOne\t%s\n' "$key" >"$RENT/controller-keys.tsv"
printf 'V\t2\nL\t%s\t0\n' "$rental_id" >"$RENT/ledger.tsv"
rental_base="$(sha256sum "$RENT/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$rental_base" >>"$RENT/ledger.tsv"
chmod 600 "$RENT/.blaze-v2-fixture-only" "$RENT/controller-keys.tsv" "$RENT/ledger.tsv"
rent_run() { rent_signed="$(sign "$@")"; "$T/native" "$RENT" "$@" "$rent_signed"; }
[ "$(rent_run ctrlOne 1 ctrlOne:1 LR "$rental_id" - 600 1000)" = "$(printf 'COMMIT\t1600')" ] || {
  echo 'PAY-0754 valid long colon rental identity rejected' >&2; exit 1;
}
[ "$(rent_run ctrlOne 1 ctrlOne:1 LR "$rental_id" - 600 1000)" = "$(printf 'REPLAY\t1600')" ]
rental_digest="$(sha256sum "$RENT/ledger.tsv" | cut -d' ' -f1)"
overlong_id="${rental_id}0"
overlong_sig="$(sign ctrlOne 2 ctrlOne:2 LR "$overlong_id" - 1 1000)"
if "$T/native" "$RENT" ctrlOne 2 ctrlOne:2 LR "$overlong_id" - 1 1000 "$overlong_sig" >"$RENT/overlong-out" 2>"$RENT/overlong-error"; then
  echo 'PAY-0754 overlong rental identity accepted' >&2; exit 1;
fi
[ ! -s "$RENT/overlong-out" ] &&
  [ "$(sha256sum "$RENT/ledger.tsv" | cut -d' ' -f1)" = "$rental_digest" ]
# PAY-0756: imported v1 money/time may reach the signed-32 ceiling. The
# native parser, arithmetic, durable receipt and replay must agree there.
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' > "$BOUND/.blaze-v2-fixture-only"
printf 'ctrlOne\t%s\n' "$key" > "$BOUND/controller-keys.tsv"
printf 'V\t2\nA\talice\t2147483647\nA\tbob\t0\nL\tdev01\t2147483646\n' > "$BOUND/ledger.tsv"
bound_base="$(sha256sum "$BOUND/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$bound_base" >> "$BOUND/ledger.tsv"
chmod 600 "$BOUND/.blaze-v2-fixture-only" "$BOUND/controller-keys.tsv" "$BOUND/ledger.tsv"
bound_run() { bound_signed="$(sign "$@")"; "$T/native" "$BOUND" "$@" "$bound_signed"; }
[ "$(bound_run ctrlOne 1 ctrlOne:1 SM alice - 1 2147483645)" = "$(printf 'COMMIT\t2147483646')" ] || {
  echo 'PAY-0756 valid v1 maximum bank rejected' >&2; exit 1;
}
[ "$(bound_run ctrlOne 1 ctrlOne:1 SM alice - 1 2147483645)" = "$(printf 'REPLAY\t2147483646')" ]
[ "$(bound_run ctrlOne 2 ctrlOne:2 AM alice - 1 2147483645)" = "$(printf 'COMMIT\t2147483647')" ]
[ "$(bound_run ctrlOne 3 ctrlOne:3 LR dev01 - 1 2147483646)" = "$(printf 'COMMIT\t2147483647')" ]
[ "$(bound_run ctrlOne 3 ctrlOne:3 LR dev01 - 1 2147483646)" = "$(printf 'REPLAY\t2147483647')" ]
bound_digest="$(sha256sum "$BOUND/ledger.tsv" | cut -d' ' -f1)"
for spec in '4 ctrlOne:4 AM alice - 1 2147483647' \
            '4 ctrlOne:4 LR dev01 - 1 2147483647' \
            '4 ctrlOne:4 AM bob - 1 2147483648'; do
  # These requests exceed the bank/lease/time ceiling or carry invalid now.
  set -- $spec
  bound_signed="$(sign ctrlOne "$@")"
  if "$T/native" "$BOUND" ctrlOne "$@" "$bound_signed" > "$BOUND/refused-out" 2> "$BOUND/refused-error"; then
    echo 'PAY-0756 signed-32 overflow accepted' >&2; exit 1;
  fi
  [ ! -s "$BOUND/refused-out" ] &&
    [ "$(sha256sum "$BOUND/ledger.tsv" | cut -d' ' -f1)" = "$bound_digest" ] || exit 1
done
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$RT/.blaze-v2-fixture-only"
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key" "$key2" > "$RT/controller-keys.tsv"
printf 'V\t2\nA\talice\t100\nA\tbob\t200\nL\tdev01\t0\n' >"$RT/ledger.tsv"
base="$(sha256sum "$RT/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$base" >>"$RT/ledger.tsv"
chmod 600 "$RT/.blaze-v2-fixture-only" "$RT/controller-keys.tsv" "$RT/ledger.tsv"
runtime_run() {
  signed="$(sign_runtime "$@")"
  "$T/runtime" "$RT" "$@" "$signed"
}
runtime_digest() { sha256sum "$RT/ledger.tsv" | cut -d' ' -f1; }
runtime_before="$(runtime_digest)"
# CGI authentication is deliberately read only, even with a correct
# production-domain envelope. It creates no lock and never reads the ledger.
verify_sig="$(sign_runtime ctrlOne 1 ctrlOne:1 AM alice - 40 1000)"
verify_before="$(find "$RT" -maxdepth 1 -type f -printf '%f %s\n' | sort)"
[ -z "$("$T/runtime" "$RT" ctrlOne 1 ctrlOne:1 LR "$rental_id" - 600 1000 \
  "$(sign_runtime ctrlOne 1 ctrlOne:1 LR "$rental_id" - 600 1000)" \
  --verify-envelope-only)" ] || {
  echo 'PAY-0754 runtime envelope rejected valid long rental identity' >&2; exit 1;
}
[ -z "$("$T/runtime" "$RT" ctrlOne 1 ctrlOne:1 AM 7alice - 40 1000 \
  "$(sign_runtime ctrlOne 1 ctrlOne:1 AM 7alice - 40 1000)" \
  --verify-envelope-only)" ] || {
  echo 'PAY-0753 runtime envelope rejected numeric-leading member identity' >&2; exit 1;
}
[ -z "$("$T/runtime" "$RT" ctrlOne 1 ctrlOne:1 AM alice - 40 1000 \
  "$verify_sig" --verify-envelope-only)" ] || {
  echo 'runtime envelope verifier emitted an ACK' >&2; exit 1;
}
[ "$(find "$RT" -maxdepth 1 -type f -printf '%f %s\n' | sort)" = "$verify_before" ] &&
  [ "$(runtime_digest)" = "$runtime_before" ] || {
  echo 'runtime envelope verifier changed financial state' >&2; exit 1;
}
if "$T/runtime" "$RT" ctrlOne 1 ctrlOne:1 AM alice - 41 1000 \
  "$verify_sig" --verify-envelope-only >"$T/verify-tamper" 2>"$T/verify-tamper-error"; then
  echo 'runtime verifier accepted altered paid quantity' >&2; exit 1;
fi
[ ! -s "$T/verify-tamper" ] && [ "$(runtime_digest)" = "$runtime_before" ]
# A deployable profile without admitted independent freshness and a protected
# response signer must not ACK or mutate, including when a request is replayed.
runtime_refuse() {
  before="$(runtime_digest)"
  if runtime_run "$@" >"$T/runtime-refused" 2>"$T/runtime-refused-error"; then
    echo 'runtime authority committed without admitted trust adapters' >&2; exit 1
  fi
  [ ! -s "$T/runtime-refused" ] && [ "$(runtime_digest)" = "$before" ] || {
    echo 'runtime authority ACKed or mutated without admitted trust adapters' >&2; exit 1;
  }
}
runtime_refuse ctrlOne 1 ctrlOne:1 AM alice - 40 1000
runtime_refuse ctrlOne 1 ctrlOne:1 AM alice - 40 1000
[ "$(runtime_digest)" = "$runtime_before" ]
# Fixture-domain controller signatures must never enter the installed
# runtime request namespace, even when every other field is identical.
fixture_sig="$(sign ctrlOne 2 ctrlOne:2 AM alice - 7 1000)"
if "$T/runtime" "$RT" ctrlOne 2 ctrlOne:2 AM alice - 7 1000 "$fixture_sig" \
    >"$T/runtime-fixture-domain" 2>"$T/runtime-fixture-domain-error"; then
  echo 'runtime profile accepted fixture request domain' >&2; exit 1
fi
[ ! -s "$T/runtime-fixture-domain" ] &&
  [ "$(runtime_digest)" = "$runtime_before" ]
# Both unsigned mode and the software HMAC fixture mode remain unavailable in
# the deployable profile. Missing a response signer must fail before commit.
signed="$(sign ctrlOne 3 ctrlOne:3 AM alice - 10 1000)"
if "$T/runtime" "$RT" ctrlOne 3 ctrlOne:3 AM alice - 10 1000 "$signed" \
    --authenticated-ack >"$T/runtime-ack" 2>"$T/runtime-ack-error"; then
  echo 'runtime profile accepted fixture ACK mode' >&2; exit 1
fi
[ ! -s "$T/runtime-ack" ] && [ "$(runtime_digest)" = "$runtime_before" ]
signed="$(sign_runtime ctrlOne 2 ctrlOne:2 AM alice - 7 1000)"
if "$T/runtime" "$RT" ctrlOne 2 ctrlOne:2 AM alice - 7 1000 "$signed" \
    --server-ack-v2 >"$T/runtime-server-ack" 2>"$T/runtime-server-ack-error"; then
  echo 'runtime profile committed using an unprotected software ACK key' >&2; exit 1
fi
[ ! -s "$T/runtime-server-ack" ] && [ "$(runtime_digest)" = "$runtime_before" ]
# Production authority builds are path-bound and cannot target arbitrary data.
if "$T/runtime" /etc ctrlOne 3 ctrlOne:3 AM alice - 10 1000 "$signed" \
    >"$T/runtime-external" 2>&1; then
  echo 'runtime profile accepted a non-authority state path' >&2; exit 1
fi
[ ! -s "$T/runtime-external" ] && [ "$(runtime_digest)" = "$runtime_before" ]
# Corrupt financial state is never repaired or acknowledged by the runtime.
printf 'corrupt\n' >>"$RT/ledger.tsv"
corrupt_digest="$(runtime_digest)"
if runtime_run ctrlOne 3 ctrlOne:3 AM alice - 10 1000 >"$T/runtime-corrupt" 2>&1; then
  echo 'runtime profile accepted corrupted authority state' >&2; exit 1
fi
[ "$(runtime_digest)" = "$corrupt_digest" ]
run() {
  signed="$(sign "$@")"
  "$T/native" "$T" "$@" "$signed"
}
digest() { sha256sum "$T/ledger.tsv" | cut -d' ' -f1; }
bank() { awk -F '\t' -v u="$1" '$1=="A" && $2==u {print $3;exit}' "$T/ledger.tsv"; }
lease() { awk -F '\t' -v u="$1" '$1=="L" && $2==u {print $3;exit}' "$T/ledger.tsv"; }
refuse() {
  before="$(digest)"
  if run "$@" > "$T/out" 2>"$T/err"; then
    echo "unexpected signed transaction accepted: $*" >&2;exit 1
  fi
  [ ! -s "$T/out" ] || { echo 'refusal emitted ACK' >&2;exit 1; }
  [ "$(digest)" = "$before" ] || { echo 'refusal changed ledger' >&2;exit 1; }
}
[ "$(run ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'COMMIT\t140')" ]
[ "$(bank alice):$(bank bob)" = '140:200' ]
first="$(digest)"
[ "$(run ctrlOne 1 ctrlOne:1 AM alice - 40 1000)" = "$(printf 'REPLAY\t140')" ]
[ "$(digest)" = "$first" ]
# A real signed payload collision cannot reuse an old controller sequence.
refuse ctrlOne 1 ctrlOne:1 AM alice - 41 1000
refuse ctrlOne 3 ctrlOne:3 TM alice bob 30 1000
refuse ctrlOne 01 ctrlOne:01 TM alice bob 30 1000
refuse ctrlOne 2 ctrlOne:2 TM alice alice 30 1000
# HMAC must reject tampering before any journal state change.
wrong=0000000000000000000000000000000000000000000000000000000000000000
if "$T/native" "$T" ctrlOne 2 ctrlOne:2 TM alice bob 30 1000 "$wrong" >"$T/out" 2>"$T/err"; then
  echo 'unauthenticated paid event accepted' >&2;exit 1
fi
[ ! -s "$T/out" ] && [ "$(digest)" = "$first" ]
export BLAZE_V2_NATIVE_TEST_FAULT=before-source-fsync
refuse ctrlOne 2 ctrlOne:2 TM alice bob 30 1000
export BLAZE_V2_NATIVE_TEST_FAULT=before-rename
refuse ctrlOne 2 ctrlOne:2 TM alice bob 30 1000
unset BLAZE_V2_NATIVE_TEST_FAULT
# After-rename dirsync uncertainty is not a false success ACK. On recovery
# the committed receipt is available for exact retransmission.
export BLAZE_V2_NATIVE_TEST_FAULT=after-rename-before-dir-fsync
if run ctrlOne 2 ctrlOne:2 TM alice bob 30 1000 >"$T/out" 2>"$T/err"; then
  echo 'uncertain payment produced success ACK' >&2;exit 1
fi
[ ! -s "$T/out" ]
grep -Fq UNCERTAIN "$T/err"
unset BLAZE_V2_NATIVE_TEST_FAULT
[ "$(bank alice):$(bank bob)" = '110:230' ]
# PAY-0745: a previously visible rename may not be durable yet.
recovery_sha="$(digest)"
export BLAZE_V2_NATIVE_TEST_FAULT=before-replay-dir-fsync
if run ctrlOne 2 ctrlOne:2 TM alice bob 30 1000 >"$T/out" 2>"$T/err"; then
  echo "unsynced replay returned payment ACK" >&2; exit 1
fi
[ ! -s "$T/out" ] && [ "$(digest)" = "$recovery_sha" ]
grep -Fq "before-replay-dir-fsync fault" "$T/err"
unset BLAZE_V2_NATIVE_TEST_FAULT
[ "$(run ctrlOne 2 ctrlOne:2 TM alice bob 30 1000)" = "$(printf 'REPLAY\t110')" ]
[ "$(( $(bank alice) + $(bank bob) ))" -eq 340 ]
# Lease/receipt/highwater all share the same fsync'd snapshot.
[ "$(run ctrlOne 3 ctrlOne:3 LR dev01 - 600 1000)" = "$(printf 'COMMIT\t1600')" ]
[ "$(lease dev01)" = 1600 ]
[ "$(run ctrlOne 3 ctrlOne:3 LR dev01 - 600 1000)" = "$(printf 'REPLAY\t1600')" ]
[ "$(awk -F '\t' '$1=="C"&&$2=="ctrlOne"{print $3}' "$T/ledger.tsv")" = 3 ]
[ "$(awk -F '\t' '$1=="R"&&$2=="ctrlOne"{a++}END{print a+0}' "$T/ledger.tsv")" = 3 ]
# A real post-dir-fsync lost response cannot duplicate paid time.
export BLAZE_V2_NATIVE_TEST_FAULT=after-dir-fsync-before-ack
if run ctrlOne 4 ctrlOne:4 SM alice - 10 1000 >"$T/out" 2>"$T/err"; then
  echo 'simulated lost ACK returned success' >&2;exit 1
fi
unset BLAZE_V2_NATIVE_TEST_FAULT
[ ! -s "$T/out" ] && [ "$(bank alice)" = 100 ]
[ "$(run ctrlOne 4 ctrlOne:4 SM alice - 10 1000)" = "$(printf 'REPLAY\t100')" ]
base="$(digest)"
# The test must never operate on a real or non-synthetic financial directory.
if "$T/native" /etc ctrlOne 5 ctrlOne:5 AM alice - 10 1000 "$wrong" >"$T/out" 2>"$T/err"; then
  echo 'external root accepted' >&2;exit 1
fi
ln "$T/ledger.tsv" "$T/alias"
refuse ctrlOne 5 ctrlOne:5 AM alice - 10 1000
rm "$T/alias"
chmod 644 "$T/controller-keys.tsv"
refuse ctrlOne 5 ctrlOne:5 AM alice - 10 1000
chmod 600 "$T/controller-keys.tsv"
chmod 750 "$T"
refuse ctrlOne 5 ctrlOne:5 AM alice - 10 1000
chmod 700 "$T"
[ "$(digest)" = "$base" ]
# V2NATIVE-0669: signed rolling receipt window is bounded, but the durable
# controller sequence floor must never be rolled back or reused.
expected=100
for seq in 5 6 7 8 9 10 11 12 13 14 15; do
  expected=$((expected-1))
  [ "$(run ctrlOne "$seq" "ctrlOne:$seq" SM alice - 1 1000)" = "$(printf 'COMMIT\t%s' "$expected")" ]
done
[ "$expected" -eq 89 ]
[ "$(bank alice):$(bank bob)" = '89:230' ]
[ "$(awk -F '\t' '$1=="C"&&$2=="ctrlOne"{print $3}' "$T/ledger.tsv")" -eq 15 ]
[ "$(awk -F '\t' '$1=="R"&&$2=="ctrlOne"{c++}END{print c+0}' "$T/ledger.tsv")" -eq 8 ]
# Sequence 1 and sequence 5 have aged out; their authentic signed payloads
# must still be rejected as stale, not credited or replayed as new.
refuse ctrlOne 1 ctrlOne:1 AM alice - 40 1000
refuse ctrlOne 5 ctrlOne:5 SM alice - 1 1000
[ "$(run ctrlOne 15 ctrlOne:15 SM alice - 1 1000)" = "$(printf 'REPLAY\t89')" ]
[ "$(bank alice)" -eq 89 ]
# Another process holding the durable lock cannot race a new paid write.
(
  exec 9>"$T/.v2-native-lock"
  flock -x 9
  printf 'HELD\n' >"$T/.lockready"
  sleep 2
) &
locker=$!
while [ ! -e "$T/.lockready" ]; do sleep 0.1; done
refuse ctrlOne 16 ctrlOne:16 AM alice - 10 1000
wait "$locker"
[ "$(bank alice)" -eq 89 ]
# MULTICTL-0673: two authenticated controllers, two different private
# keys, independent monotonic sequence floors, ONE atomic member ledger.
[ "$(run ctrlTwo 1 ctrlTwo:1 AM alice - 3 1000)" = "$(printf 'COMMIT\t92')" ]
[ "$(bank alice):$(bank bob)" = '92:230' ]
two_digest="$(digest)"
[ "$(run ctrlTwo 1 ctrlTwo:1 AM alice - 3 1000)" = "$(printf 'REPLAY\t92')" ]
[ "$(digest)" = "$two_digest" ]
# A retained receipt returns the result at the ORIGINAL commit, not the
# current account balance; replay cannot undo another controller's credit.
[ "$(run ctrlOne 15 ctrlOne:15 SM alice - 1 1000)" = "$(printf 'REPLAY\t89')" ]
[ "$(digest)" = "$two_digest" ]
refuse ctrlTwo 1 ctrlTwo:1 AM alice - 4 1000
refuse ctrlTwo 3 ctrlTwo:3 SM bob - 5 1000
# A controller cannot impersonate the other by signing the exact other
# controller envelope with its own key. Rejection emits NO paid ACK.
forged="$(printf 'BLAZE-V2-AUTH-FIXTURE/1\tctrlTwo\t2\tctrlTwo:2\tSM\tbob\t-\t5\t1000\n' |
  openssl dgst -sha256 -mac HMAC -macopt "hexkey:$key" -r | awk '{print $1}')"
if "$T/native" "$T" ctrlTwo 2 ctrlTwo:2 SM bob - 5 1000 "$forged" >"$T/out" 2>"$T/err"; then
  echo 'cross-controller key forgery accepted' >&2;exit 1
fi
[ ! -s "$T/out" ] && [ "$(digest)" = "$two_digest" ]
[ "$(run ctrlTwo 2 ctrlTwo:2 SM bob - 5 1000)" = "$(printf 'COMMIT\t225')" ]
[ "$(bank alice):$(bank bob)" = '92:225' ]
[ "$(awk -F '\t' '$1=="C"&&$2=="ctrlOne"{print $3}' "$T/ledger.tsv")" = 15 ]
[ "$(awk -F '\t' '$1=="C"&&$2=="ctrlTwo"{print $3}' "$T/ledger.tsv")" = 2 ]
[ "$(run ctrlTwo 2 ctrlTwo:2 SM bob - 5 1000)" = "$(printf 'REPLAY\t225')" ]
refuse ctrlOne 5 ctrlOne:5 SM alice - 1 1000
# MULTICTL-0681: an operator-side registry misconfiguration must not
# let distinct controllers impersonate one another by sharing an HMAC key.
# ALL registry entries are validated, even if the requested ID is ctrlOne.
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key" "$key" > "$T/controller-keys.tsv"
refuse ctrlOne 16 ctrlOne:16 AM alice - 1 1000
grep -Fq 'duplicate controller secret' "$T/err"
# Duplicate identity in unrelated rows must invalidate the entire registry.
key3=5555555555555555555555555555555555555555555555555555555555555555
key4=6666666666666666666666666666666666666666666666666666666666666666
printf 'ctrlOne\t%s\nctrlTwo\t%s\nctrlThird\t%s\nctrlThird\t%s\n' \
  "$key" "$key2" "$key3" "$key4" > "$T/controller-keys.tsv"
refuse ctrlOne 16 ctrlOne:16 AM alice - 1 1000
grep -Fq 'duplicate controller identity' "$T/err"
# Reject the trivially forgeable all-zero secret on ANY listed controller.
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key" "$wrong" > "$T/controller-keys.tsv"
refuse ctrlOne 16 ctrlOne:16 AM alice - 1 1000
grep -Fq 'zero controller secret rejected' "$T/err"
# Restore the unique, private, nonzero registry. Earlier real receipts
# must still replay without changing balances or emitting a new COMMIT.
printf 'ctrlOne\t%s\nctrlTwo\t%s\n' "$key" "$key2" > "$T/controller-keys.tsv"
pre_registry_digest="$(digest)"
[ "$(run ctrlOne 15 ctrlOne:15 SM alice - 1 1000)" = "$(printf 'REPLAY\t89')" ]
[ "$(run ctrlTwo 2 ctrlTwo:2 SM bob - 5 1000)" = "$(printf 'REPLAY\t225')" ]
[ "$(digest)" = "$pre_registry_digest" ]
echo 'MULTICTL-0681 PASS: global duplicate IDs, reused HMAC secrets and zero keys rejected without ACK or ledger mutation'
# Data corruption must not be treated as a zero-balance fallback.
sed 's/A\talice\t92/A\talice\t93/' "$T/ledger.tsv" > "$T/bad"
mv "$T/bad" "$T/ledger.tsv"
refuse ctrlOne 5 ctrlOne:5 AM alice - 10 1000
grep -Fq 'SHA-256 integrity footer mismatch' "$T/err"
echo 'MULTICTL-0673 PASS: independent controller keys, cross-key forgery refusal, shared prepaid balances, replay floor, lock and crash no-ACK'
echo 'LAB ONLY: this host test is not hardware power-loss, v1 migration or a production release gate'
