#!/bin/sh
# PAY-0720: real OpenWrt source no-production-signer boundary.
# The Windows product may parse PUBLIC signatures, but target Vendo currently
# has no durable signed v2 receipt issuer. Verify we NEVER accidentally ship
# a v2 money ACK or credit path while server capability remains unaccepted.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
BUILD="$ROOT/build/build-openwrt-image.sh"
[ -f "$CGI" ] && [ -f "$BUILD" ] || exit 1
# Signed-vendo check still occurs BEFORE the unavailable-v2 rejection.
signature_line="$(grep -nF 'bp_check_vendo_sig "$action"' "$CGI" | head -n1 | cut -d: -f1)"
denial_line="$(grep -nF 'member_v2_*) bp_fail "member v2 authority unavailable; no v1 fallback"' "$CGI" | head -n1 | cut -d: -f1)"
heartbeat_line="$(grep -nF 'heartbeat() {' "$CGI" | head -n1 | cut -d: -f1)"
for line in "$signature_line" "$denial_line" "$heartbeat_line"; do
  case "$line" in ''|*[!0-9]*)
    echo 'PAY-0720 source trust gate missing' >&2; exit 1;;
  esac
done
[ "$signature_line" -lt "$denial_line" ] &&
  [ "$denial_line" -lt "$heartbeat_line" ] || {
  echo 'PAY-0720 v2 signed denial moved after paid heartbeat or before signature' >&2
  exit 1
}
# No successful public-acknowledged v2 membership path has been authorized,
# no generated/embedded private signing keys or fake ACKP1 in customer rootfs.
if grep -Fq ACKP1 "$CGI"; then
  echo 'PAY-0720: Vendo appears to emit unapproved ACKP1 responses' >&2
  exit 1
fi
test ! -e "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member-v2-server-ack-sign.sh"
test ! -e "$ROOT/openwrt/rootfs/etc/blazepwifi/v2-server-private.pem"
# The ImageBuilder manifests must not be misreported as universal OpenSSL
# target support: only x86/SBC requests openssl-util, not small Ruijie.
grep -Fq 'PACKAGES="$PACKAGES openssl-util zerotier"' "$BUILD"
grep -Fq 'if [ "$KIND" = x86 ] || [ "$KIND" = sbc ]; then' "$BUILD"
echo 'PAY-0720 PASS: signed Vendo v2 denial remains ahead of mutation; no production ACKP1/signing key'
echo 'BLOCKED: OpenWrt target private-key signer and physical durability not validated; Ruijie crypto package unavailable in requested package list'
