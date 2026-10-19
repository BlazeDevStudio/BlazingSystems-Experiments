#!/bin/sh
# V2TARGET-0670 — OpenWrt 25.12.5 SDK cross compiler for LAB-ONLY fixture.
# No router image, boot hook, payment endpoint, production key, or v1 migration.
set -eu
export LC_ALL=C
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
VERSION=25.12.5
GCC_VERSION=14.3.0
[ "$#" -eq 1 ] || { echo 'usage: ruijie|x86_64|orangepi_zero3' >&2; exit 2; }
TARGET="$1"
case "$TARGET" in
  ruijie)
    SUB="ramips/mt7621"; STEM="ramips-mt7621"; MACHINE="MIPS" ;;
  x86_64)
    SUB="x86/64"; STEM="x86-64"; MACHINE="X86-64" ;;
  orangepi_zero3)
    SUB="sunxi/cortexa53"; STEM="sunxi-cortexa53"; MACHINE="AArch64" ;;
  *)
    echo 'V2TARGET-0670 BLOCKED: use ruijie, x86_64 or orangepi_zero3' >&2; exit 2;;
esac
[ -n "$RUNNER_TEMP" ] || {
  echo 'V2TARGET-0670 BLOCKED: only supported in isolated GitHub Actions runner' >&2;exit 2;
}
command -v curl >/dev/null
command -v sha256sum >/dev/null
command -v zstd >/dev/null
command -v readelf >/dev/null
command -v make >/dev/null
# Never assume ImageBuilder provides a compiler; download the matching SDK.
BASE="https://downloads.openwrt.org/releases/$VERSION/targets/$SUB"
SDK_FILE="$(printf 'openwrt-sdk-%s-%s_gcc-%s_musl.Linux-x86_64.tar.zst' "$VERSION" "$STEM" "$GCC_VERSION")"
TMP="$(mktemp -d "$RUNNER_TEMP/blaze-v2target-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT HUP INT TERM
umask 077
cd "$TMP"
curl --http1.1 -fL --retry 5 --retry-all-errors --retry-delay 3 \
  --connect-timeout 30 --max-time 300 "$BASE/sha256sums" -o sha256sums
# sha256sums on OpenWrt may denote files with a leading "*" for binary.
DIGEST="$(awk -v requested="$SDK_FILE" '
  {
    file=$2; sub(/^\*/, "", file)
    if(file==requested && $1 ~ /^[a-fA-F0-9]+$/ && length($1)==64) {
      found++; hash=$1
    }
  }
  END {if(found==1) print hash}
' sha256sums)"
[ -n "$DIGEST" ] || { echo "V2TARGET-0670 BLOCKED: SDK checksum not in official index: $SDK_FILE" >&2;exit 9; }
curl --http1.1 -fL --retry 5 --retry-all-errors --retry-delay 3 \
  --connect-timeout 30 --max-time 1800 "$BASE/$SDK_FILE" -o sdk.tar.zst
echo "$DIGEST  sdk.tar.zst" | sha256sum -c -
mkdir extracted
tar -I zstd -xf sdk.tar.zst -C extracted
SDK="$(find "$TMP/extracted" -mindepth 1 -maxdepth 1 -type d -name 'openwrt-sdk-*' | head -n 1)"
[ -n "$SDK" ] && [ -f "$SDK/rules.mk" ] || {
  echo 'V2TARGET-0670 BLOCKED: verified SDK archive invalid' >&2;exit 9;
}
DEST="$SDK/package/blazepwifi-v2-native-lab"
mkdir -p "$DEST/src"
cp "$ROOT/openwrt/lab-native/Makefile" "$DEST/Makefile"
cp "$ROOT/tools/v060_journal_authority_native.c" "$DEST/src/"
cp "$ROOT/tools/v060_p256_target_capability_probe.c" "$DEST/src/"
# PAY-0743: cross-compile the separately packaged installed authority profile
# for the same target. This proves target ABI/package construction only; the
# package remains excluded from customer images pending admission gates.
PAID_DEST="$SDK/package/blazepwifi-paid-authority"
mkdir -p "$PAID_DEST/src"
cp "$ROOT/openwrt/paid-authority/Makefile" "$PAID_DEST/Makefile"
cp "$ROOT/openwrt/paid-authority/src/v060_journal_authority.c" "$PAID_DEST/src/"
cmp -s "$ROOT/tools/v060_journal_authority_native.c" \
  "$PAID_DEST/src/v060_journal_authority.c" || {
  echo 'PAY-0743 BLOCKED: runtime package source diverged from canonical journal' >&2; exit 9;
}
# PAY-0721: use actual target libcrypto EVP EC APIs; no server key material.
grep -Fq '#ifndef BLAZE_V2_P256_CAPABILITY_LAB_ONLY' "$DEST/src/v060_p256_target_capability_probe.c"
grep -Fq -- '-DBLAZE_V2_P256_CAPABILITY_LAB_ONLY' "$DEST/Makefile"
# Assert the test-only macro is compile time mandatory and source never gets
# installed into production rootfs/images by this workflow.
grep -Fq '#if !defined(BLAZE_FIXTURE_ONLY) && !defined(BLAZE_RUNTIME_AUTHORITY)' "$DEST/src/v060_journal_authority_native.c"
grep -Fq -- '-DBLAZE_FIXTURE_ONLY' "$DEST/Makefile"
! grep -R -Fq 'blazepwifi-v2-native-lab' "$ROOT/build/build-openwrt-image.sh"
! grep -R -Fq 'blazepwifi-paid-authority' "$ROOT/build/build-openwrt-image.sh"
grep -Fq -- '-DBLAZE_RUNTIME_AUTHORITY' "$PAID_DEST/Makefile"
# OpenWrt's SDK prerequisite contract REQUIRES umask 022 for compiled
# packages; restricted 077 is used only while staging private downloads above.
# Do not use FORCE=1 to bypass its build safety checks.
umask 022
[ "$(umask)" = 0022 ] || { echo 'OpenWrt SDK umask prerequisite failed' >&2; exit 9; }
# The published SDK provides the cross toolchain but not necessarily
# staged OpenSSL development headers. Build the authentic matching OpenWrt
# 25.12.5 openssl package first; NEVER use host openssl headers/libraries.
# Pin the upstream source commit from its verified annotated v25.12.5 tag.
OPENWRT_SRC_SHA=f0a60eee2fe051741c643ea6118718aae1ef17fb
SOURCE="$TMP/openwrt-source"
git clone --quiet --filter=blob:none --depth=1 --sparse \
  --branch v25.12.5 https://github.com/openwrt/openwrt.git "$SOURCE"
[ "$(git -C "$SOURCE" rev-parse HEAD)" = "$OPENWRT_SRC_SHA" ] || {
  echo 'V2TARGET-0670 BLOCKED: OpenWrt release source tag changed' >&2;exit 9;
}
# Cone-pattern sparse checkout takes real directories, including OpenSSL
# sources and the matching OpenWrt build include macros. A non-cone trailing
# slash alone did not materialize these sources on GitHub's runner.
git -C "$SOURCE" sparse-checkout set package/libs/openssl include
git -C "$SOURCE" checkout --quiet --detach "$OPENWRT_SRC_SHA"
[ -s "$SOURCE/package/libs/openssl/Makefile" ] &&
[ -s "$SOURCE/include/openssl-module.mk" ] || {
  echo 'V2TARGET-0670 BLOCKED: matching OpenSSL build source missing' >&2;exit 9;
}
mkdir -p "$SDK/package/libs"
cp -a "$SOURCE/package/libs/openssl" "$SDK/package/libs/openssl"
cp "$SOURCE/include/openssl-module.mk" "$SDK/include/openssl-module.mk"
# Build only standard libcrypto algorithms required by SHA-256/HMAC.
# The SDK's imported configuration can enable the optional devcrypto engine.
# That engine needs kernel cryptodev.h, which is neither bundled with SDK nor
# required by this fixture. Disable only optional engines in the LAB SDK;
# preserve target-native OpenSSL and all core cryptographic algorithms.
# Avoid conflicting duplicate Kconfig assignments from the imported SDK.
# Official OpenWrt SDK archives may not contain a .config until first setup.
# Create only this disposable SDK configuration, never customer/device files.
[ -e "$SDK/.config" ] || : > "$SDK/.config"
for opt in OPENSSL_ENGINE OPENSSL_ENGINE_BUILTIN \
  OPENSSL_ENGINE_BUILTIN_DEVCRYPTO PACKAGE_libopenssl-devcrypto; do
  sed -i "/^CONFIG_$opt=/d; /^# CONFIG_$opt is not set$/d" "$SDK/.config"
  printf '# CONFIG_%s is not set\n' "$opt" >> "$SDK/.config"
done
printf '\nCONFIG_PACKAGE_libopenssl=m\nCONFIG_PACKAGE_blazepwifi-v2-native-lab=m\nCONFIG_PACKAGE_blazepwifi-paid-authority=m\n' >> "$SDK/.config"
make -C "$SDK" defconfig
# Fail closed if defconfig re-enables the engine; do NOT paper over a missing
# kernel header by copying a host header or using FORCE=1.
for opt in OPENSSL_ENGINE OPENSSL_ENGINE_BUILTIN \
  OPENSSL_ENGINE_BUILTIN_DEVCRYPTO PACKAGE_libopenssl-devcrypto; do
  if grep -Eq "^CONFIG_$opt=[ym]" "$SDK/.config"; then
    echo "V2TARGET-0670 BLOCKED: optional cryptodev engine remained enabled: $opt" >&2
    exit 9
  fi
done
make -C "$SDK" -j2 package/openssl/compile V=s
OPENSSL_HDR="$(find "$SDK/staging_dir" -path '*/usr/include/openssl/crypto.h' -print -quit)"
[ -n "$OPENSSL_HDR" ] || {
  echo 'V2TARGET-0670 BLOCKED: SDK target libcrypto headers not staged' >&2;exit 9;
}
make -C "$SDK" -j2 package/blazepwifi-v2-native-lab/compile V=s
make -C "$SDK" -j2 package/blazepwifi-paid-authority/compile V=s
ELF="$(find "$SDK/build_dir" -type f -name v2-native-fixture -print -quit)"
[ -n "$ELF" ] && [ -s "$ELF" ] || {
  echo 'V2TARGET-0670 BLOCKED: SDK produced no native ELF' >&2;exit 9;
}
readelf -h "$ELF" > elf-header.txt
grep -Fq 'ELF' elf-header.txt
grep -Fq "$MACHINE" elf-header.txt || {
  echo "V2TARGET-0670 BLOCKED: wrong ELF machine, expected $MACHINE" >&2
  cat elf-header.txt >&2
  exit 9
}
# PAY-0721 SDK evidence: independently compiled P-256 EVP sign and
# public-only verify calls are linked for THIS target architecture. We do
# NOT run the target ELF here or claim physical runtime/secure key custody.
P256_ELF="$(find "$SDK/build_dir" -type f -name p256-primitive-probe -print -quit)"
[ -n "$P256_ELF" ] && [ -s "$P256_ELF" ] || {
  echo 'PAY-0721 BLOCKED: target SDK did not build P-256 primitive probe' >&2; exit 9;
}
PAID_ELF="$(find "$SDK/build_dir" -type f -name blazepwifi-paid-authority -print -quit)"
[ -n "$PAID_ELF" ] && [ -s "$PAID_ELF" ] || {
  echo 'PAY-0743 BLOCKED: OpenWrt SDK produced no installed authority ELF' >&2; exit 9;
}
readelf -h "$PAID_ELF" > paid-elf-header.txt
grep -Fq "$MACHINE" paid-elf-header.txt || {
  echo "PAY-0743 BLOCKED: wrong authority ELF architecture ($TARGET)" >&2; exit 9;
}
readelf -h "$P256_ELF" > p256-elf-header.txt
grep -Fq "$MACHINE" p256-elf-header.txt || {
  echo "PAY-0721 BLOCKED: wrong target ELF architecture ($TARGET)" >&2; exit 9;
}
readelf -d "$P256_ELF" | grep -Eq 'Shared library: \[libcrypto\.so\.' || {
  echo 'PAY-0721 BLOCKED: crosscompiled ELF lacks target libcrypto dependency' >&2; exit 9;
}
# Require actual OpenWrt SDK package; no fake artifact or host binary.
APK="$(find "$SDK/bin" -type f -name 'blazepwifi-v2-native-lab*.apk' -print -quit)"
[ -n "$APK" ] && [ -s "$APK" ] || {
  echo 'V2TARGET-0670 BLOCKED: no compiled OpenWrt .apk package' >&2;exit 9;
}
PAID_APK="$(find "$SDK/bin" -type f -name 'blazepwifi-paid-authority*.apk' -print -quit)"
[ -n "$PAID_APK" ] && [ -s "$PAID_APK" ] || {
  echo 'PAY-0743 BLOCKED: no installed authority OpenWrt package' >&2; exit 9;
}
OUT="$ROOT/dist/v060-native-sdk-lab/$TARGET"
mkdir -p "$OUT"
cp "$ELF" "$OUT/v2-native-fixture-$TARGET"
cp "$P256_ELF" "$OUT/p256-primitive-probe-$TARGET"
cp "$PAID_ELF" "$OUT/blazepwifi-paid-authority-$TARGET"
cp p256-elf-header.txt "$OUT/P256-ELF-HEADER.txt"
cp "$APK" "$OUT/"
cp "$PAID_APK" "$OUT/"
cp elf-header.txt "$OUT/ELF-HEADER.txt"
{
  printf 'V2TARGET-0670 LAB ONLY — NO CUSTOMER PAYMENTS\n'
  printf 'version=%s\nsdk=%s\n' "$VERSION" "$SDK_FILE"
  printf 'sdk_sha256=%s\n' "$DIGEST"
  printf 'target=%s\nmachine=%s\n' "$TARGET" "$MACHINE"
  printf 'commit=%s\n' "$GITHUB_SHA"
  printf 'source=tools/v060_journal_authority_native.c\n'
  printf 'macro=BLAZE_FIXTURE_ONLY\n'
  printf 'production_released=0\ncustomer_install_authorized=0\n'
  printf 'openwrt_rootfs_integration=0\npaid_migration_authorized=0\n'
  printf 'hardware_powercut_verified=0\n'
  printf 'p256_sdk_evpec_crosscompiled=1\n'
  printf 'p256_sdk_linked_target_libcrypto=1\n'
  printf 'p256_target_hardware_executed=0\n'
  printf 'p256_server_private_key_custody_verified=0\n'
  printf 'p256_production_ack_issuer_available=0\n'
  printf 'pay0743_runtime_authority_package_crosscompiled=1\n'
  printf 'pay0743_runtime_authority_in_customer_image=0\n'
  printf 'pay0743_runtime_authority_paid_cutover_enabled=0\n'
  # Requested package closure is NOT an installed/signing capability.
  case "$TARGET" in
    ruijie) printf 'customer_image_openssl_util_requested=0\n' ;;
    *) printf 'customer_image_openssl_util_requested=1\n' ;;
  esac
} >"$OUT/MANIFEST.txt"
(cd "$OUT" && sha256sum v2-native-fixture-* p256-primitive-probe-* blazepwifi-paid-authority-* ./*.apk > SHA256SUMS)
printf 'V2TARGET-0670 SDK COMPILE PASS: %s (%s) — LAB ONLY\n' "$TARGET" "$MACHINE"
printf 'PAY-0743 OpenWrt package cross-compile PASS: %s (%s) — installed package, NOT image-enabled\n' "$TARGET" "$MACHINE"
printf 'PAY-0721 P256 SDK LINK PASS: %s — target crypto primitive only, NO live signer or paid ACK\n' "$TARGET"
