#!/bin/sh
# PAY-0775: missing installed pieces must refuse a candidate image.
set -eu
SOURCE="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d "${TMPDIR:-/tmp}/blaze-paid-rootfs-XXXXXX")"
trap 'rm -rf "$T"' EXIT HUP INT TERM
R="$T/root-x86"
mkdir -p "$R/usr/sbin" "$R/lib/apk/packages" \
  "$R/usr/lib/blazepwifi" "$R/usr/lib" "$R/www/blazepwifi/cgi-bin"
readelf() {
case "$*" in
  *blazepwifi-paid-authority)
    grep -Fq AUTHORITY_ELF "$R/usr/sbin/blazepwifi-paid-authority" || return 1
    printf 'Machine: Advanced Micro Devices X86-64\n'
    ;;
  *libcrypto.so.3)
    grep -Fq CRYPTO_ELF "$R/usr/lib/libcrypto.so.3" || return 1
    printf 'Machine: Advanced Micro Devices X86-64\nLibrary soname: [libcrypto.so.3]\n'
    ;;
  *) return 1 ;;
esac
}
printf 'AUTHORITY_ELF fixture\n' >"$R/usr/sbin/blazepwifi-paid-authority"
printf 'usr/sbin/blazepwifi-paid-authority\n' \
  >"$R/lib/apk/packages/blazepwifi-paid-authority.list"
printf 'CRYPTO_ELF fixture\n' >"$R/usr/lib/libcrypto.so.3"
printf '/usr/sbin/blazepwifi-paid-authority "$@" --verify-envelope-only\n' \
  >"$R/usr/lib/blazepwifi/common.sh"
printf 'bp_v2_verify_envelope "$id"\n' >"$R/www/blazepwifi/cgi-bin/vendo"
VERIFY="$SOURCE/build/verify-paid-preview-rootfs.sh"
run_verify() ( set -- "$R"; . "$VERIFY" )
run_verify >"$T/stdout"
reject() {
  expected="$1"
  if run_verify >"$T/stdout" 2>"$T/stderr"; then
    echo "PAY-0775 negative unexpectedly passed: $expected" >&2
    exit 1
  fi
  grep -Fq "$expected" "$T/stderr" || {
    echo "PAY-0775 wrong refusal: $expected" >&2
    cat "$T/stderr" >&2
    exit 1
  }
}
mv "$R/usr/sbin/blazepwifi-paid-authority" "$T/authority"
reject 'installed x86 authority missing'
mv "$T/authority" "$R/usr/sbin/blazepwifi-paid-authority"
mv "$R/lib/apk/packages/blazepwifi-paid-authority.list" "$T/package"
reject 'installed authority package record missing'
mv "$T/package" "$R/lib/apk/packages/blazepwifi-paid-authority.list"
printf 'usr/sbin/unrelated\n' >"$R/lib/apk/packages/blazepwifi-paid-authority.list"
reject 'installed authority package record missing'
printf 'usr/sbin/blazepwifi-paid-authority\n' >"$R/lib/apk/packages/blazepwifi-paid-authority.list"
mv "$R/usr/lib/libcrypto.so.3" "$T/crypto"
reject 'installed crypto library missing'
mv "$T/crypto" "$R/usr/lib/libcrypto.so.3"
printf 'non-ELF crypto fixture\n' >"$R/usr/lib/libcrypto.so.3"
reject 'installed crypto library missing'
printf 'CRYPTO_ELF fixture\n' >"$R/usr/lib/libcrypto.so.3"
mv "$R/usr/lib/blazepwifi/common.sh" "$T/common"
reject 'installed native envelope helper missing'
cp "$T/common" "$R/usr/lib/blazepwifi/common.sh"
printf 'helper without native call\n' >"$R/usr/lib/blazepwifi/common.sh"
reject 'installed native envelope helper missing'
cp "$T/common" "$R/usr/lib/blazepwifi/common.sh"
mv "$R/www/blazepwifi/cgi-bin/vendo" "$T/vendo"
reject 'installed Vendo envelope route missing'
mv "$T/vendo" "$R/www/blazepwifi/cgi-bin/vendo"
printf 'no v2 verifier route\n' >"$R/www/blazepwifi/cgi-bin/vendo"
reject 'installed Vendo envelope route missing'
printf 'PAY-0775 missing verifier route/crypto/package refusals PASS\n'
