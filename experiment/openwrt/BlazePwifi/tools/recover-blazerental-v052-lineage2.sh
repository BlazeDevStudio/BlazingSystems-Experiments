#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
REPO="BlazingSystems/BlazingSystems-Experiments"
TAG="v0.5.2"
IDENTITY="$ROOT/../../../.github/blazerental-v052-production-identity.json"
UNSEAL="$ROOT/tools/unseal-blazerental-lineage2.py"

PRIVATE_KEY="${1:-}"
SLOT="${2:-A}"
OUT="${3:-./blazerental-v052-lineage2-recovered}"
MODE="${4:-}"

[ -n "$PRIVATE_KEY" ] || {
  echo "usage: $0 /secure/path/recovery-private.pem [A|B] [output-dir] [--install-github-secrets]" >&2
  exit 2
}
[ -s "$PRIVATE_KEY" ] || { echo "private recovery key not found" >&2; exit 2; }
case "$SLOT" in A|B) ;; *) echo "recovery slot must be A or B" >&2; exit 2;; esac

command -v gh >/dev/null
command -v python3 >/dev/null
command -v keytool >/dev/null
command -v jq >/dev/null
python3 -c 'import cryptography' >/dev/null 2>&1 || {
  echo "Python cryptography is required: python3 -m pip install cryptography" >&2
  exit 2
}

EXPECTED="$(jq -r .sha256_fingerprint "$IDENTITY")"
[ -n "$EXPECTED" ] && [ "$EXPECTED" != null ]

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
mkdir -p "$TMP/assets" "$TMP/plain"

gh release download "$TAG" --repo "$REPO"   --pattern 'BlazeRental-v0.5.2-lineage2-signing-backup.enc'   --pattern 'BlazeRental-v0.5.2-lineage2-signing-nonce.bin'   --pattern "BlazeRental-v0.5.2-lineage2-key-recovery-$SLOT.enc"   --pattern 'BlazeRental-RECOVERY-MANIFEST.json'   --dir "$TMP/assets"

python3 "$UNSEAL"   --private-key "$PRIVATE_KEY"   --wrapped-key "$TMP/assets/BlazeRental-v0.5.2-lineage2-key-recovery-$SLOT.enc"   --encrypted-backup "$TMP/assets/BlazeRental-v0.5.2-lineage2-signing-backup.enc"   --nonce "$TMP/assets/BlazeRental-v0.5.2-lineage2-signing-nonce.bin"   --manifest "$TMP/assets/BlazeRental-RECOVERY-MANIFEST.json"   --out "$TMP/backup.tar.gz"

tar -xzf "$TMP/backup.tar.gz" -C "$TMP/plain"
P12="$TMP/plain/BlazeRental-v0.5.2-production-lineage2.p12"
PASSFILE="$TMP/plain/keystore-password.txt"
[ -s "$P12" ] && [ -s "$PASSFILE" ]
PASS="$(tr -d '\r\n' < "$PASSFILE")"
ACTUAL="$(keytool -list -v -alias blazerental -keystore "$P12" -storetype PKCS12   -storepass "$PASS" | sed -n 's/^[[:space:]]*SHA256: //p' | head -n1)"
[ "$ACTUAL" = "$EXPECTED" ] || {
  echo "recovered signer fingerprint mismatch; refusing output" >&2
  exit 1
}

umask 077
mkdir -p "$OUT"
cp "$P12" "$OUT/BlazeRental-production-lineage2.p12"
cp "$PASSFILE" "$OUT/keystore-password.txt"
printf '%s\n' "$EXPECTED" > "$OUT/signing-fingerprint.txt"

if [ "$MODE" = "--install-github-secrets" ]; then
  base64 < "$OUT/BlazeRental-production-lineage2.p12" | tr -d '\n' |     gh secret set BLAZERENTAL_LINEAGE2_KEYSTORE_B64 --repo "$REPO"
  gh secret set BLAZERENTAL_LINEAGE2_KEYSTORE_PASSWORD --repo "$REPO" < "$OUT/keystore-password.txt"
  gh secret set BLAZERENTAL_LINEAGE2_KEY_ALIAS --repo "$REPO" --body blazerental
  echo "Verified Lineage-2 signer installed into GitHub Actions secrets."
else
  echo "Recovered and verified Lineage-2 signer into: $OUT"
  echo "Fingerprint: $EXPECTED"
fi
