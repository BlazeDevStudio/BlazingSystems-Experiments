#!/bin/sh
# PAY-0722: OFF-DEVICE operator-delivered, READ-ONLY OpenWrt test-target
# ABI/ephemeral signing primitive probe. NEVER an unattended installer,
# production ACK issuer, key provisioning tool or customer migration.
# It runs the existing PAY-0721 in-memory-only ELF supplied by the operator
# in a private isolated LAB /tmp path after matching an explicit SHA256.
# The checksum verifies selected bytes, NOT a signed artifact provenance.
# No root required; do not inspect customer config, financial state or keys.
set -eu
export LC_ALL=C
usage() {
  echo "usage: sh v060_p256_physical_runtime_probe.sh --operator-isolated-target --candidate /tmp/blaze-v2-p256-probe-NAME --sha256 64lowercasehex" >&2
  exit 2
}
operator=0
candidate=''
digest=''
while [ "$#" -gt 0 ]; do
  case "$1" in
    --operator-isolated-target)
      [ "$operator" -eq 0 ] || usage
      operator=1; shift ;;
    --candidate)
      [ -z "$candidate" ] && [ "$#" -ge 2 ] || usage
      candidate="$2"; shift 2 ;;
    --sha256)
      [ -z "$digest" ] && [ "$#" -ge 2 ] || usage
      digest="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[ "$operator" -eq 1 ] || usage
# Do not accept a host PC, guessed OS, unknown version, or a live system
# silently. Operators must separately attest real test-device isolation.
if [ ! -r /etc/openwrt_release ] ||
   ! grep -Eq "^DISTRIB_RELEASE='25[.]12[.][0-9]+'$" /etc/openwrt_release; then
  echo 'PAY-0722 BLOCKED: OpenWrt 25.12 isolated target is not proven'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'
  exit 4
fi
arch="$(uname -m 2>/dev/null || printf unknown)"
case "$arch" in
  mips*|x86_64|aarch64) ;;
  *) echo 'PAY-0722 BLOCKED: unsupported/unidentified target architecture'
     echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4 ;;
esac
printf 'PAY-0722 OPENWRT_RUNTIME_ARCH=%s\n' "$arch"
if command -v openssl >/dev/null 2>&1; then
  echo 'OPENSSL_CLI_PRESENT=1'
else
  echo 'OPENSSL_CLI_PRESENT=0'
fi
# Always require explicit artifact identity. Merely finding openssl/libcrypto
# does not demonstrate that the SDK ELF actually runs on the target.
case "$candidate" in
  /tmp/blaze-v2-p256-probe-*) ;;
  *) echo 'PAY-0722 BLOCKED: missing isolated test candidate'
     echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4 ;;
esac
suffix="${candidate#/tmp/blaze-v2-p256-probe-}"
case "$suffix" in ''|*/*|*..*|*[!A-Za-z0-9._-]*)
  echo 'PAY-0722 BLOCKED: unsafe candidate path'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;; esac
[ "${#digest}" -eq 64 ] || {
  echo 'PAY-0722 BLOCKED: expected SHA256 missing'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
printf '%s\n' "$digest" | grep -Eq '^[0-9a-f]{64}$' || {
  echo 'PAY-0722 BLOCKED: invalid expected SHA256'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
[ -f "$candidate" ] && [ ! -L "$candidate" ] && [ -x "$candidate" ] || {
  echo 'PAY-0722 BLOCKED: candidate missing/nonregular/not executable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
command -v timeout >/dev/null 2>&1 || {
  echo 'PAY-0722 BLOCKED: bounded timeout unavailable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
command -v sha256sum >/dev/null 2>&1 || {
  echo 'PAY-0722 BLOCKED: SHA256 unavailable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
command -v stat >/dev/null 2>&1 || {
  echo 'PAY-0722 BLOCKED: private-file metadata validation unavailable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
owner="$(id -u)" || exit 4
mode_owner="$(stat -c '%a:%h:%u' "$candidate" 2>/dev/null)" || {
  echo 'PAY-0722 BLOCKED: candidate metadata unreadable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
[ "$mode_owner" = "500:1:$owner" ] || {
  echo 'PAY-0722 BLOCKED: candidate must be owner-only 0500, single-link, same uid'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
observed="$(sha256sum "$candidate" | cut -d' ' -f1)" || {
  echo 'PAY-0722 BLOCKED: candidate hash unreadable'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
[ "$observed" = "$digest" ] || {
  echo 'PAY-0722 BLOCKED: target binary checksum mismatch'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4;
}
# Never expose candidate output unless it matches the fixed 7-line harmless
# ephemeral capability contract; stderr is suppressed. No key serialization.
expected="$(printf '%s\n' \
  'PAY-0721 EPHEMERAL_SIGN_VERIFY_TEST=PASS' \
  'ALGORITHM=ECDSA-P256-SHA256' \
  'PUBLIC_VERIFY=SPKI-DER' \
  'PRIVATE_KEY_PERSISTED=0' \
  'PRODUCTION_SIGNER_AVAILABLE=0' \
  'PHYSICAL_TARGET_TESTED=0' \
  'CUSTOMER_PAID_ACK_AUTHORIZED=0')"
if ! output="$(timeout 15 "$candidate" 2>/dev/null)" ||
   [ "$output" != "$expected" ]; then
  echo 'PAY-0722 BLOCKED: target in-memory P256 primitive failed / output mismatched'
  echo 'PRODUCTION_SIGNER_AVAILABLE=0'; exit 4
fi
echo 'PAY-0722 PHYSICAL_EPHEMERAL_P256_RUNTIME=PASS'
echo 'PAY-0722 TARGET_SIGNING_KEY_CUSTODY=UNVERIFIED'
echo 'PAY-0722 INDEPENDENT_ROLLBACK_WITNESS=UNVERIFIED'
echo 'PAY-0722 TARGET_POWER_CUT=UNVERIFIED'
echo 'PAY-0722 ARTIFACT_PROVENANCE_AUTHENTICATED=0'
echo 'PRODUCTION_SIGNER_AVAILABLE=0'
echo 'CUSTOMER_PAID_ACK_AUTHORIZED=0'
echo 'PRODUCTION_v0.6.0_RELEASED=0'
