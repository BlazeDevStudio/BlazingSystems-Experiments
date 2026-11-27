#!/usr/bin/env bash
set -euo pipefail

REPO="${BLAZE_REPO:-BlazingSystems/BlazingSystems-Experiments}"
BRANCH="${BLAZE_BRANCH:-blazepwifi-v0.4.0-implementation}"
TAG="${BLAZE_TAG:-v0.4.0}"
PRIVATE_KEY="${1:-}"

if [ -z "$PRIVATE_KEY" ] || [ ! -s "$PRIVATE_KEY" ]; then
  echo "usage: $0 /path/to/blazerental-transfer-private.pem" >&2
  exit 2
fi

for cmd in gh openssl jq keytool base64 tar; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "missing required command: $cmd" >&2; exit 2; }
done
gh auth status >/dev/null

umask 077
WORK="$(mktemp -d)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

echo "Downloading locked v0.4 recovery handoff..."
mkdir -p "$WORK/assets" "$WORK/plain"
gh release download "$TAG" --repo "$REPO" \
  --pattern 'BlazeRental-v0.4-signing-backup.enc' \
  --pattern 'BlazeRental-v0.4-signing-aes-key.enc' \
  --pattern 'BlazeRental-v0.4-signing-aes-iv.bin' \
  --dir "$WORK/assets"

for f in BlazeRental-v0.4-signing-backup.enc BlazeRental-v0.4-signing-aes-key.enc BlazeRental-v0.4-signing-aes-iv.bin; do
  test -s "$WORK/assets/$f" || { echo "release recovery asset missing: $f" >&2; exit 1; }
done

gh api "repos/$REPO/contents/.github/blazerental-v04-production-identity.json?ref=$BRANCH" \
  --jq .content | tr -d '\n' | base64 -d > "$WORK/identity.json"
EXPECTED="$(jq -r .sha256_fingerprint "$WORK/identity.json" | tr -d ':' | tr 'A-F' 'a-f')"
test "$(jq -r .locked "$WORK/identity.json")" = true
test -n "$EXPECTED"

openssl pkey -in "$PRIVATE_KEY" -noout
openssl pkeyutl -decrypt -inkey "$PRIVATE_KEY" \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 \
  -in "$WORK/assets/BlazeRental-v0.4-signing-aes-key.enc" \
  -out "$WORK/aes.key"

KEYHEX="$(xxd -p -c 256 "$WORK/aes.key")"
IVHEX="$(xxd -p -c 256 "$WORK/assets/BlazeRental-v0.4-signing-aes-iv.bin")"
openssl enc -d -aes-256-cbc -K "$KEYHEX" -iv "$IVHEX" \
  -in "$WORK/assets/BlazeRental-v0.4-signing-backup.enc" \
  -out "$WORK/backup.tar.gz"
tar -xzf "$WORK/backup.tar.gz" -C "$WORK/plain"

P12="$(find "$WORK/plain" -type f -name 'BlazeRental-v0.4-production.p12' -print -quit)"
PASSFILE="$(find "$WORK/plain" -type f -name 'keystore-password.txt' -print -quit)"
test -n "$P12" -a -s "$P12"
test -n "$PASSFILE" -a -s "$PASSFILE"
PASS="$(tr -d '\r\n' < "$PASSFILE")"
test -n "$PASS"

ACTUAL="$(keytool -list -v -keystore "$P12" -storetype PKCS12 -storepass "$PASS" -alias blazerental \
  | sed -n 's/^[[:space:]]*SHA256: //p' | head -n1 | tr -d ':' | tr 'A-F' 'a-f')"
if [ -z "$ACTUAL" ] || [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "Recovered keystore does not match the locked v0.4 production identity." >&2
  exit 1
fi

echo "Locked signer verified. Storing it as GitHub Actions secrets..."
base64 < "$P12" | tr -d '\n' | gh secret set BLAZERENTAL_KEYSTORE_B64 --repo "$REPO"
printf '%s' "$PASS" | gh secret set BLAZERENTAL_KEYSTORE_PASSWORD --repo "$REPO"
printf '%s' blazerental | gh secret set BLAZERENTAL_KEY_ALIAS --repo "$REPO"
gh secret set BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM --repo "$REPO" < "$PRIVATE_KEY"

LATEST="$(gh run list --repo "$REPO" --workflow blazerental-v04-locked-resign.yml \
  --branch "$BRANCH" --limit 1 --json databaseId,conclusion --jq '.[0] | select(.conclusion=="failure") | .databaseId' || true)"
if [ -n "$LATEST" ]; then
  echo "Re-running locked production signing gate: $LATEST"
  gh run rerun "$LATEST" --repo "$REPO" --failed
else
  echo "Signer secrets stored. No failed locked-sign run was found to re-run."
fi

echo "Done. No private key, keystore, or password was printed or committed."
