#!/bin/sh
# PAY-0721: host-run ephemeral P-256 cross-target ABI feasibility gate.
# Official target SDK compile is separately required; this host pass does NOT
# prove OpenWrt runtime installation, HSM/TPM key custody or paid ACK issuance.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/tools/v060_p256_target_capability_probe.c"
T="$(mktemp -d /tmp/blaze-v2-p256-capability-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
umask 077
command -v cc >/dev/null
command -v openssl >/dev/null
# No accidentally unguarded production-capable build.
if cc -std=c11 -Wall -Wextra -Werror -O2 "$SRC" -lcrypto \
    -o "$T/unguarded" >"$T/unguarded-out" 2>"$T/unguarded-err"; then
  echo 'PAY-0721 unguarded production build unexpectedly compiled' >&2; exit 1
fi
grep -Fq 'LAB-ONLY compile guard' "$T/unguarded-err" || {
  echo 'PAY-0721 missing explicit fixture compile guard' >&2; exit 1;
}
cc -std=c11 -Wall -Wextra -Werror -O2 \
  -DBLAZE_V2_P256_CAPABILITY_LAB_ONLY "$SRC" -lcrypto -o "$T/probe"
"$T/probe" >"$T/out" 2>"$T/err" || {
  echo 'PAY-0721 host libcrypto P-256 primitive test failed' >&2
  sed -n '1,8p' "$T/err" >&2; exit 1;
}
grep -Fxq 'PAY-0721 EPHEMERAL_SIGN_VERIFY_TEST=PASS' "$T/out"
grep -Fxq 'ALGORITHM=ECDSA-P256-SHA256' "$T/out"
grep -Fxq 'PUBLIC_VERIFY=SPKI-DER' "$T/out"
grep -Fxq 'PRIVATE_KEY_PERSISTED=0' "$T/out"
grep -Fxq 'PRODUCTION_SIGNER_AVAILABLE=0' "$T/out"
grep -Fxq 'PHYSICAL_TARGET_TESTED=0' "$T/out"
grep -Fxq 'CUSTOMER_PAID_ACK_AUTHORIZED=0' "$T/out"
[ ! -s "$T/err" ]
[ ! -e "$ROOT/openwrt/rootfs/usr/libexec/blazepwifi-lab/p256-capability" ]
[ ! -e "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/v2-server-private.pem" ]
# No persisted key generation APIs or private key text even in lab output.
! grep -Eq 'BEGIN (EC )?PRIVATE KEY|secret-key|private.pem' "$T/out"
echo 'PAY-0721 PASS: host compiled guarded ephemeral P-256 sign + public-only verify and tamper denial'
echo 'LAB ONLY: cross-SDK compile and physical target runtime signer evidence still required; no production ACK'
