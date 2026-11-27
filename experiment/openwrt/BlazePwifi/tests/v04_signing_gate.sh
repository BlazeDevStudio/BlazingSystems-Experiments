#!/bin/bash
set -euo pipefail
APK="${1:?usage: v04_signing_gate.sh signed.apk expected-fingerprint-file}"
FPFILE="${2:?missing expected fingerprint file}"
APKSIGNER="${APKSIGNER:-apksigner}"
AAPT="${AAPT:-aapt}"

test -s "$APK"
test -s "$FPFILE"

VERIFY="$(mktemp)"; trap 'rm -f "$VERIFY"' EXIT
"$APKSIGNER" verify --verbose --print-certs "$APK" > "$VERIFY"

# minSdk 21 requires JAR/v1 for Android 5/6; newer Androids also get v2/v3.
grep -Fq 'Verified using v1 scheme (JAR signing): true' "$VERIFY"
grep -Fq 'Verified using v2 scheme (APK Signature Scheme v2): true' "$VERIFY"
grep -Fq 'Verified using v3 scheme (APK Signature Scheme v3): true' "$VERIFY"

EXPECTED="$(sed -n 's/^[[:space:]]*SHA256:[[:space:]]*//p' "$FPFILE" | head -n1 | tr -d ':' | tr 'A-F' 'a-f')"
if [ -z "$EXPECTED" ]; then
  EXPECTED="$(grep -Eo '([A-Fa-f0-9]{2}:){31}[A-Fa-f0-9]{2}' "$FPFILE" | head -n1 | tr -d ':' | tr 'A-F' 'a-f' || true)"
fi
if [ -z "$EXPECTED" ]; then
  EXPECTED="$(grep -Eo '(^|[^A-Fa-f0-9])([A-Fa-f0-9]{64})([^A-Fa-f0-9]|$)' "$FPFILE" | head -n1 | tr -cd 'A-Fa-f0-9' | tail -c 65 | tr 'A-F' 'a-f' || true)"
fi
ACTUAL="$(sed -n 's/^Signer #1 certificate SHA-256 digest: //p' "$VERIFY" | tr 'A-F' 'a-f' | head -n1)"
[ -n "$EXPECTED" -a -n "$ACTUAL" ]
[ "$ACTUAL" = "$EXPECTED" ] || {
  echo "signing lineage mismatch" >&2
  echo "expected: $EXPECTED" >&2
  echo "actual:   $ACTUAL" >&2
  exit 1
}

BADGING="$("$AAPT" dump badging "$APK")"
printf '%s\n' "$BADGING" | grep -q "package: name='com.blazesystems.blazerental'"
printf '%s\n' "$BADGING" | grep -q "versionName='0.4.0'"
printf '%s\n' "$BADGING" | grep -q "sdkVersion:'21'"

echo "BlazeRental v0.4 signing lineage gate passed"
