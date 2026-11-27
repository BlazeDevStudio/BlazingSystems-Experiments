#!/bin/sh
# WITNESS-0734: real native P-256 crypto parser, private synthetic fixture.
# Verifies only a signed challenge+ledger digest statement. NEVER a real
# monotonic witness, production signer, controller ACK or physical trial.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-witness0734-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
umask 077
SRC="$ROOT/tools/v060_witness_proof_verify_native.c"
if cc -std=c11 -O2 -Wall -Wextra -Werror -DBLAZE_PAID_RUNTIME_ENABLED \
     "$SRC" -lcrypto -o "$T/unsafe" 2>"$T/compile-denial"; then
  echo 'WITNESS-0734 FAIL: crypto-only verifier compiled as paid runtime' >&2; exit 1
fi
grep -Fq 'MUST NOT enable' "$T/compile-denial"
cc -std=c11 -O2 -Wall -Wextra -Werror "$SRC" -lcrypto -o "$T/verify"
openssl ecparam -name prime256v1 -genkey -noout -out "$T/private.pem"
openssl pkey -in "$T/private.pem" -pubout -out "$T/public.pem" >/dev/null 2>&1
openssl ecparam -name secp256k1 -genkey -noout -out "$T/othercurve.pem"
openssl pkey -in "$T/othercurve.pem" -pubout -out "$T/othercurve-public.pem" >/dev/null 2>&1
openssl ecparam -name prime256v1 -genkey -noout -out "$T/wrong.pem"
openssl pkey -in "$T/wrong.pem" -pubout -out "$T/wrong-public.pem" >/dev/null 2>&1
printf 'V\t2\nA\tfixture\t125\nL\tdevice\t900\n' >"$T/snapshot"
nonce=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
othernonce=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
create_statement() {
  digest="$(sha256sum "$T/snapshot" | cut -d ' ' -f1)"
  printf 'BLAZE-V2-WITNESS-CHALLENGE/1\tdevice01\t12\t7\t%s\t%s\n' \
    "$digest" "$nonce" >"$T/proof"
  openssl dgst -sha256 -sign "$T/private.pem" -out "$T/signature" "$T/proof"
}
verify() {
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
      device01 12 7 "$nonce"
}
reject() {
  label="$1"; shift
  before="$(sha256sum "$T/snapshot" "$T/proof" "$T/signature" | cut -d ' ' -f1)"
  rc=0
  "$@" >"$T/out" 2>"$T/err" || rc=$?
  [ "$rc" -ne 0 ] && [ ! -s "$T/out" ] &&
    [ "$before" = "$(sha256sum "$T/snapshot" "$T/proof" "$T/signature" | cut -d ' ' -f1)" ] || {
    echo "WITNESS-0734 FAIL: $label accepted bad proof/changed finance" >&2
    exit 1
  }
  grep -Fq 'NO PAID ACK' "$T/err"
}
create_statement
verify >"$T/valid"
grep -Fqx 'WITNESS_STATEMENT_CRYPTO_VALID=1' "$T/valid"
for flag in INDEPENDENT_MONOTONIC_WITNESS_VERIFIED PAID_ACK_AUTHORIZED \
    FINANCIAL_MIGRATION_AUTHORIZED CUSTOMER_INSTALL_AUTHORIZED; do
  grep -Fqx "$flag=0" "$T/valid"
done
reject 'new challenge refuses replayed proof' \
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 12 7 "$othernonce"
reject 'changed witness epoch' \
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 13 7 "$nonce"
reject 'changed witness revision' \
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 12 8 "$nonce"
reject 'wrong device id' \
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device02 12 7 "$nonce"
reject 'wrong signing public key' \
  "$T/verify" "$T/wrong-public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 12 7 "$nonce"
reject 'wrong EC curve despite matching bit length' \
  "$T/verify" "$T/othercurve-public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 12 7 "$nonce"
# Prove the same signed statement NEVER survives a ledger snapshot change.
printf 'A\tnew-funds\t100\n' >>"$T/snapshot"
reject 'restored or altered local snapshot' verify
sed -i '$d' "$T/snapshot"
# Recreate fresh canonical proof + signature for corruption/unsafe source tests.
create_statement
printf '\000' >> "$T/signature"
reject 'corrupt detached signature' verify
create_statement
printf 'garbage\n' >> "$T/proof"
reject 'noncanonical extra proof bytes' verify
create_statement
ln -s "$T/snapshot" "$T/linked-snapshot"
reject 'symlink local snapshot' \
  "$T/verify" "$T/public.pem" "$T/linked-snapshot" "$T/proof" "$T/signature" \
  device01 12 7 "$nonce"
ln -s "$T/public.pem" "$T/linked-public.pem"
reject 'symlink pubkey' \
  "$T/verify" "$T/linked-public.pem" "$T/snapshot" "$T/proof" "$T/signature" \
  device01 12 7 "$nonce"
ln -s "$T/signature" "$T/linked-signature"
reject 'symlink detached signature' \
  "$T/verify" "$T/public.pem" "$T/snapshot" "$T/proof" "$T/linked-signature" \
  device01 12 7 "$nonce"
echo 'WITNESS-0734 PASS: native pinned-caller P-256 proof binds ledger digest, epoch, revision, device and caller challenge; invalid input denied without ACK'
echo 'NOT ATTESTED: caller must pin key, generate/never reuse secure challenges and prove independent physically monotonic external witness. No real paid ACK or v0.6 release.'
