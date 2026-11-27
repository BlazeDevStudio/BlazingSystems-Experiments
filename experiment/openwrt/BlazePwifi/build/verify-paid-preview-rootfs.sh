#!/bin/sh
# PAY-0775: accept only a complete, installed LAB x86 verifier route.
set -eu
ROOTFS="${1:-}"
[ -n "$ROOTFS" ] && [ -d "$ROOTFS" ] && [ ! -L "$ROOTFS" ] || {
  echo 'PAY-0775 BLOCKED: installed rootfs missing or unsafe' >&2
  exit 9
}

ELF="$ROOTFS/usr/sbin/blazepwifi-paid-authority"
[ -f "$ELF" ] && [ ! -L "$ELF" ] && [ -s "$ELF" ] &&
  readelf -h "$ELF" | grep -Fq 'X86-64' || {
  echo 'PAY-0775 BLOCKED: installed x86 authority missing or wrong ABI' >&2
  exit 9
}
PACKAGE_RECORD="$ROOTFS/lib/apk/packages/blazepwifi-paid-authority.list"
[ -f "$PACKAGE_RECORD" ] && [ ! -L "$PACKAGE_RECORD" ] &&
  grep -Eq '^/?usr/sbin/blazepwifi-paid-authority$' "$PACKAGE_RECORD" || {
  echo 'PAY-0775 BLOCKED: installed authority package record missing' >&2
  exit 9
}
CRYPTO="$ROOTFS/usr/lib/libcrypto.so.3"
[ -s "$CRYPTO" ] &&
  readelf -h "$CRYPTO" | grep -Fq 'X86-64' &&
  readelf -d "$CRYPTO" | grep -Fq 'Library soname: [libcrypto.so.3]' || {
  echo 'PAY-0775 BLOCKED: installed crypto library missing' >&2
  exit 9
}

COMMON="$ROOTFS/usr/lib/blazepwifi/common.sh"
CGI="$ROOTFS/www/blazepwifi/cgi-bin/vendo"
[ -f "$COMMON" ] && [ ! -L "$COMMON" ] &&
  grep -Fq '/usr/sbin/blazepwifi-paid-authority' "$COMMON" &&
  grep -Fq -- '--verify-envelope-only' "$COMMON" || {
  echo 'PAY-0775 BLOCKED: installed native envelope helper missing' >&2
  exit 9
}
[ -f "$CGI" ] && [ ! -L "$CGI" ] &&
  grep -Fq 'bp_v2_verify_envelope "' "$CGI" || {
  echo 'PAY-0775 BLOCKED: installed Vendo envelope route missing' >&2
  exit 9
}
printf 'PAY-0775 installed x86 verifier route PASS (paid ACK still denied)\n'
