#!/bin/sh
# V2TARGET-0670: cheap fail-closed source gate; never compiles native package.
set -eu
BASE="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
PKG="$BASE/openwrt/lab-native/Makefile"
BUILDER="$BASE/tools/v060_cross_compile_native_lab.sh"
SOURCE="$BASE/tools/v060_journal_authority_native.c"
WORKFLOW="$BASE/../../../.github/workflows/blazepwifi-v060-sdk-lab.yml"
[ -s "$PKG" ] && [ -s "$BUILDER" ] && [ -s "$SOURCE" ] && [ -s "$WORKFLOW" ]
sh -n "$BUILDER"
grep -Fq -- '-DBLAZE_FIXTURE_ONLY' "$PKG"
grep -Fq 'DEFAULT:=n' "$PKG"
grep -Fq 'DEPENDS:=+libopenssl' "$PKG"
grep -Fq '#if !defined(BLAZE_FIXTURE_ONLY) && !defined(BLAZE_RUNTIME_AUTHORITY)' "$SOURCE"
grep -Fq '#if defined(BLAZE_FIXTURE_ONLY) && defined(BLAZE_RUNTIME_AUTHORITY)' "$SOURCE"
grep -Fq '#define V2_REQUEST_DOMAIN "BLAZE-V2-AUTH/1"' "$SOURCE"
grep -Fq '#define V2_REQUEST_DOMAIN "BLAZE-V2-AUTH-FIXTURE/1"' "$SOURCE"
grep -Fq '"/etc/blazepwifi/state"' "$SOURCE"
grep -Fq 'ROOT_PREFIX "/tmp/blaze-v2-native-"' "$SOURCE"
grep -Fq 'sha256sum -c -' "$BUILDER"
# SDK libcrypto needs only SHA/HMAC; its optional /dev/crypto engine must
# remain disabled and is not a security requirement for the fixture.
grep -Fq '[ -e "$SDK/.config" ] || : > "$SDK/.config"' "$BUILDER"
grep -Fq 'OPENSSL_ENGINE_BUILTIN_DEVCRYPTO PACKAGE_libopenssl-devcrypto' "$BUILDER"
grep -Fq 'optional cryptodev engine remained enabled' "$BUILDER"
grep -Fq 'package/openssl/compile' "$BUILDER"
grep -Fq 'crypto.h' "$BUILDER"
grep -Fq 'readelf -h' "$BUILDER"
grep -Fq 'MACHINE="MIPS"' "$BUILDER"
grep -Fq 'MACHINE="X86-64"' "$BUILDER"
grep -Fq 'MACHINE="AArch64"' "$BUILDER"
grep -Fq 'retention-days: 3' "$WORKFLOW"
grep -Fq 'if-no-files-found: error' "$WORKFLOW"
grep -Fq 'permissions:' "$WORKFLOW"
# Never silently ship a lab package in normal firmware or direct installers.
! grep -Fq 'blazepwifi-v2-native-lab' "$BASE/build/build-openwrt-image.sh"
! grep -R -Fq 'v2-native-fixture' "$BASE/openwrt/rootfs" 
[ ! -e "$BASE/openwrt/rootfs/usr/libexec/blazepwifi-lab" ]
# Mandatory disabled independent state inspection (not migration).
grep -Fq "option v2_shadow_diagnostics '0'" "$BASE/openwrt/rootfs/etc/config/blazepwifi"
printf '%s\n' 'V2TARGET-0670 STATIC PASS: synthetic-only SDK package remains opt-in, checksum-required, non-production and not installed in normal firmware'
