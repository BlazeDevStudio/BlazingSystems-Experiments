#!/bin/sh
# PAY-0722: CI proves fail-closed operator/target boundary, not physical runtime.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
PROBE="$ROOT/tools/v060_p256_physical_runtime_probe.sh"
TEST="$(mktemp -d /tmp/blaze-p256-admission-XXXXXX)" || exit 1
trap 'rm -rf "$TEST"' EXIT HUP INT TERM
sh -n "$PROBE"
[ -f "$PROBE" ] && [ ! -e "$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-v2-signer" ]
# No operator consent: no automatic hardware probing, payment or key I/O.
if sh "$PROBE" >"$TEST/stdout" 2>"$TEST/stderr"; then
  echo 'PAY-0722 P0 FAIL: hardware probe accepted unattended invocation' >&2
  exit 1
fi
[ ! -s "$TEST/stdout" ] || {
  echo 'PAY-0722 FAIL: unauthenticated probe disclosed target information' >&2
  exit 1
}
grep -Fq 'usage:' "$TEST/stderr"
# Unrecognized flags never enable the probe.
if sh "$PROBE" --operator-isolated-target --enable-production >"$TEST/stdout" 2>"$TEST/stderr"; then
  echo 'PAY-0722 P0 FAIL: arbitrary production flag accepted' >&2; exit 1
fi
[ ! -s "$TEST/stdout" ]
# CI hosts are NOT OpenWrt physical test devices. A caller-provided hash and
# candidate must not trick a host into claiming signing/runtime admission.
if [ ! -e /etc/openwrt_release ]; then
  if sh "$PROBE" --operator-isolated-target \
    --candidate /tmp/blaze-v2-p256-probe-test --sha256 \
    0000000000000000000000000000000000000000000000000000000000000000 \
    >"$TEST/stdout" 2>"$TEST/stderr"; then
    echo 'PAY-0722 P0 FAIL: non-OpenWrt CI host accepted as target' >&2; exit 1
  fi
  grep -Fq 'BLOCKED: OpenWrt 25.12 isolated target is not proven' "$TEST/stdout"
  grep -Fq 'PRODUCTION_SIGNER_AVAILABLE=0' "$TEST/stdout"
  [ ! -s "$TEST/stderr" ]
fi
# The script is off-device, not an installer or a private-key template. It
# explicitly keeps each production-critical acceptance item unavailable.
grep -Fq 'stat -c' "$PROBE"
grep -Fq '500:1:$owner' "$PROBE"
grep -Fq 'TARGET_SIGNING_KEY_CUSTODY=UNVERIFIED' "$PROBE"
grep -Fq 'INDEPENDENT_ROLLBACK_WITNESS=UNVERIFIED' "$PROBE"
grep -Fq 'TARGET_POWER_CUT=UNVERIFIED' "$PROBE"
grep -Fq 'PRODUCTION_SIGNER_AVAILABLE=0' "$PROBE"
grep -Fq 'CUSTOMER_PAID_ACK_AUTHORIZED=0' "$PROBE"
grep -Fq 'PRODUCTION_v0.6.0_RELEASED=0' "$PROBE"
[ ! -e "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member-v2-server-ack-sign.sh" ]
# The actual authenticated Vendo v2 deny-before-money gate remains in place.
sh "$ROOT/tests/v060_v2_public_ack_runtime_boundary.sh" >/dev/null
echo 'PAY-0722 PASS: no unattended/hypothetical physical crypto signer admission, no prod signer installed'
echo 'NOT PHYSICAL TEST: owner must run an isolated target ELF; #31/#34/#43 remain OPEN'
