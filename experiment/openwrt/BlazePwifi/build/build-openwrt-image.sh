#!/bin/sh
set -eu
VER="${OPENWRT_VERSION:-25.12.5}"
TARGET="${1:-ruijie}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
WORK="${WORKDIR:-/tmp/blazepwifi-imagebuilder}"

SUB=""
PROFILE=""
IB=""
KIND=""
case "$TARGET" in
  ruijie)
    SUB="ramips/mt7621"; PROFILE="ruijie_rg-ew1200g-pro-v1.1"; KIND="router"
    IB="openwrt-imagebuilder-$VER-ramips-mt7621.Linux-x86_64.tar.zst"
    ;;
  x86_64)
    SUB="x86/64"; PROFILE="generic"; KIND="x86"
    IB="openwrt-imagebuilder-$VER-x86-64.Linux-x86_64.tar.zst"
    ;;
  orangepi_zero3)
    SUB="sunxi/cortexa53"; PROFILE="xunlong_orangepi-zero3"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa53.Linux-x86_64.tar.zst"
    ;;
  orangepi_one)
    SUB="sunxi/cortexa7"; PROFILE="xunlong_orangepi-one"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa7.Linux-x86_64.tar.zst"
    ;;
  orangepi_pc)
    SUB="sunxi/cortexa7"; PROFILE="xunlong_orangepi-pc"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa7.Linux-x86_64.tar.zst"
    ;;
  orangepi_pc_plus)
    SUB="sunxi/cortexa7"; PROFILE="xunlong_orangepi-pc-plus"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa7.Linux-x86_64.tar.zst"
    ;;
  orangepi_pc2)
    SUB="sunxi/cortexa53"; PROFILE="xunlong_orangepi-pc2"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa53.Linux-x86_64.tar.zst"
    ;;
  orangepi_zero)
    SUB="sunxi/cortexa7"; PROFILE="xunlong_orangepi-zero"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa7.Linux-x86_64.tar.zst"
    ;;
  orangepi_zero2)
    SUB="sunxi/cortexa53"; PROFILE="xunlong_orangepi-zero2"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa53.Linux-x86_64.tar.zst"
    ;;
  orangepi_zero2w)
    SUB="sunxi/cortexa53"; PROFILE="xunlong_orangepi-zero2w"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa53.Linux-x86_64.tar.zst"
    ;;
  orangepi_one_plus)
    SUB="sunxi/cortexa53"; PROFILE="xunlong_orangepi-one-plus"; KIND="sbc"
    IB="openwrt-imagebuilder-$VER-sunxi-cortexa53.Linux-x86_64.tar.zst"
    ;;
  *)
    echo "usage: $0 {ruijie|x86_64|orangepi_zero3|orangepi_one|orangepi_pc|orangepi_pc_plus|orangepi_pc2|orangepi_zero|orangepi_zero2|orangepi_zero2w|orangepi_one_plus}" >&2
    exit 2
    ;;
esac

# PAY-0774: an SDK-compiled runtime may be installed only in a separately
# named, noncustomer x86 preview image. The ordinary firmware path is unchanged.
PAID_PREVIEW=0
if [ -n "${BLAZE_V2_PAID_PREVIEW:-}" ]; then
  [ "$BLAZE_V2_PAID_PREVIEW" = lab-only ] && [ "$TARGET" = x86_64 ] &&
    [ "${GITHUB_ACTIONS:-}" = true ] && [ -n "${RUNNER_TEMP:-}" ] || {
    echo 'PAY-0774 BLOCKED: paid authority preview requires x86_64 LAB-ONLY CI' >&2
    exit 9
  }
  SOURCE_SHA="$(git -C "$ROOT" rev-parse HEAD)"
  printf '%s' "$SOURCE_SHA" | grep -Eq '^[0-9a-f]{40}$' || {
    echo 'PAY-0774 BLOCKED: literal source commit is required' >&2
    exit 9
  }
  PAID_SDK_DIR="$ROOT/dist/v060-native-sdk-lab/x86_64"
  [ -d "$PAID_SDK_DIR" ] && [ ! -L "$PAID_SDK_DIR" ] &&
    [ -f "$PAID_SDK_DIR/MANIFEST.txt" ] &&
    [ -f "$PAID_SDK_DIR/SHA256SUMS" ] || {
    echo 'PAY-0774 BLOCKED: same-run SDK package evidence missing' >&2
    exit 9
  }
  for line in "target=x86_64" "commit=$SOURCE_SHA" \
    'pay0743_runtime_authority_package_crosscompiled=1' \
    'pay0743_runtime_authority_paid_cutover_enabled=0' \
    'production_released=0' 'customer_install_authorized=0'; do
    grep -Fxq "$line" "$PAID_SDK_DIR/MANIFEST.txt" || {
      echo "PAY-0774 BLOCKED: SDK provenance mismatch: $line" >&2
      exit 9
    }
  done
  (cd "$PAID_SDK_DIR" && sha256sum -c SHA256SUMS) || {
    echo 'PAY-0774 BLOCKED: SDK artifact checksum mismatch' >&2
    exit 9
  }
  PAID_ELF="$PAID_SDK_DIR/blazepwifi-paid-authority-x86_64"
  [ -f "$PAID_ELF" ] && [ ! -L "$PAID_ELF" ] &&
    readelf -h "$PAID_ELF" | grep -Fq 'X86-64' &&
    readelf -d "$PAID_ELF" | grep -Eq 'Shared library: \[libcrypto\.so\.' || {
    echo 'PAY-0774 BLOCKED: SDK authority ELF ABI or crypto dependency invalid' >&2
    exit 9
  }
  set -- "$PAID_SDK_DIR"/blazepwifi-paid-authority*.apk
  [ "$#" -eq 1 ] && [ -f "$1" ] && [ ! -L "$1" ] || {
    echo 'PAY-0774 BLOCKED: exactly one regular authority APK is required' >&2
    exit 9
  }
  PAID_APK="$1"
  PAID_PREVIEW=1
fi

BASE="https://downloads.openwrt.org/releases/$VER/targets/$SUB"
mkdir -p "$WORK"
cd "$WORK"
command -v curl >/dev/null || { echo "curl required" >&2; exit 1; }
command -v zstd >/dev/null || { echo "zstd required" >&2; exit 1; }

FILES_DIR="$ROOT/openwrt/rootfs"
PACKAGES="uhttpd nftables px5g-mbedtls flock ip-full kmod-wireguard wireguard-tools"
if [ "$KIND" = x86 ] || [ "$KIND" = sbc ]; then
  FILES_DIR="$WORK/rootfs-$TARGET"
  rm -rf "$FILES_DIR"
  mkdir -p "$FILES_DIR"
  cp -a "$ROOT/openwrt/rootfs/." "$FILES_DIR/"
  sh "$ROOT/build/prepare-tabler.sh" "$FILES_DIR/www/blazepwifi/vendor/tabler"
  PACKAGES="$PACKAGES openssl-util zerotier"
fi
if [ "$KIND" = sbc ]; then
  mkdir -p "$FILES_DIR/usr/sbin" "$FILES_DIR/etc/init.d" "$FILES_DIR/usr/share/blazepwifi/orangepi"
  cp "$ROOT/linux-agent/blazepwifi-gpio-agent.sh" "$FILES_DIR/usr/sbin/blazepwifi-gpio-agent"
  cp "$ROOT/linux-agent/blazepwifi-gpio-agent.init" "$FILES_DIR/etc/init.d/blazepwifi-gpio-agent"
  cp "$ROOT/linux-agent/profiles/"*.conf "$FILES_DIR/usr/share/blazepwifi/orangepi/"
  chmod 0755 "$FILES_DIR/usr/sbin/blazepwifi-gpio-agent" "$FILES_DIR/etc/init.d/blazepwifi-gpio-agent"
  PACKAGES="$PACKAGES gpiod-tools"
fi

# OpenWrt mirrors can intermittently abort HTTP/2 transfers. Prefer HTTP/1.1
# with bounded retries and resumption, and never expose an incomplete archive
# as a validated ImageBuilder. SHA-256 is verified below before extraction.
bp_download_large() {
  url="$1"; target="$2"
  curl --http1.1 -fL --retry 5 --retry-all-errors --retry-delay 3 \
    --connect-timeout 30 --continue-at - --output "$target.part" "$url"
  mv -f "$target.part" "$target"
}
if [ ! -f "$IB" ]; then
  bp_download_large "$BASE/$IB" "$IB"
fi
curl --http1.1 -fsSL --retry 5 --retry-all-errors --retry-delay 3 \
  --connect-timeout 30 "$BASE/sha256sums" -o sha256sums.part
mv -f sha256sums.part sha256sums
EXPECTED="$(awk -v f="$IB" '$2=="*"f || $2==f {print $1;exit}' sha256sums)"
[ -n "$EXPECTED" ] || { echo "checksum entry not found for $IB" >&2; exit 1; }
echo "$EXPECTED  $IB" | sha256sum -c -

rm -rf imagebuilder
tar --zstd -xf "$IB"
D="$(find . -maxdepth 1 -type d -name 'openwrt-imagebuilder-*' | head -n1)"
[ -n "$D" ] || { echo "ImageBuilder extraction failed" >&2; exit 1; }
mv "$D" imagebuilder
cd imagebuilder

if [ "$PAID_PREVIEW" -eq 1 ]; then
  # OpenWrt 25.12.5 ImageBuilder rebuilds its local APK index on make image.
  cp "$PAID_APK" packages/
  PACKAGES="$PACKAGES blazepwifi-paid-authority"
fi

make image PROFILE="$PROFILE" PACKAGES="$PACKAGES" FILES="$FILES_DIR"

if [ "$PAID_PREVIEW" -eq 1 ]; then
  INSTALLED_ELF="$(find build_dir -type f -path '*/root-*/usr/sbin/blazepwifi-paid-authority' -print -quit)"
  [ -n "$INSTALLED_ELF" ] && [ -s "$INSTALLED_ELF" ] &&
    readelf -h "$INSTALLED_ELF" | grep -Fq 'X86-64' || {
    echo 'PAY-0774 BLOCKED: built x86 rootfs lacks target-native authority' >&2
    exit 9
  }
fi

OUT="$ROOT/dist/$TARGET"
if [ "$PAID_PREVIEW" -eq 1 ]; then
  OUT="$ROOT/dist/v060-paid-installed-preview/$TARGET"
fi
rm -rf "$OUT"
mkdir -p "$OUT"

case "$KIND" in
  router)
    find bin/targets -type f -name '*ruijie_rg-ew1200g-pro-v1.1-squashfs-sysupgrade.bin' -exec cp -v {} "$OUT/" \;
    ls "$OUT/"*squashfs-sysupgrade.bin >/dev/null 2>&1 || { echo "Ruijie BlazePwifi sysupgrade image missing" >&2; exit 1; }
    BOOTSTRAP="openwrt-$VER-ramips-mt7621-ruijie_rg-ew1200g-pro-v1.1-initramfs-kernel.bin"
    BOOTSTRAP_SHA="$(awk -v f="$BOOTSTRAP" '$2=="*"f || $2==f {print $1;exit}' "$WORK/sha256sums")"
    [ -n "$BOOTSTRAP_SHA" ] || { echo "Official Ruijie bootstrap checksum entry missing" >&2; exit 1; }
    bp_download_large "$BASE/$BOOTSTRAP" "$OUT/$BOOTSTRAP"
    echo "$BOOTSTRAP_SHA  $OUT/$BOOTSTRAP" | sha256sum -c -
    cat > "$OUT/RUIJIE-FLASH-NOTES.txt" <<EOF
BlazePwifi Ruijie RG-EW1200G Pro v1.1 release set
The initramfs file is the checksum-verified official OpenWrt bootstrap and does not contain BlazePwifi.
The squashfs sysupgrade is the BlazePwifi persistent image from this CI build.
Never flash to a different hardware revision; confirm recovery access first.
EOF
    ;;
  x86)
    find bin/targets -type f \( -name '*combined.img.gz' -o -name '*combined-efi.img.gz' \) -exec cp -v {} "$OUT/" \;
    ls "$OUT/"*combined.img.gz >/dev/null 2>&1 || { echo "x86 BIOS combined image missing" >&2; exit 1; }
    ls "$OUT/"*combined-efi.img.gz >/dev/null 2>&1 || { echo "x86 UEFI combined image missing" >&2; exit 1; }
    for image in "$OUT/"*.img.gz; do gzip -t "$image"; done
    ;;
  sbc)
    find bin/targets -type f -name "*$PROFILE*-sdcard.img.gz" -exec cp -v {} "$OUT/" \;
    count="$(find "$OUT" -type f -name '*.img.gz' | wc -l)"
    [ "$count" -gt 0 ] || { echo "Orange Pi image missing for profile $PROFILE" >&2; exit 1; }
    for image in "$OUT/"*.img.gz; do gzip -t "$image"; done
    cp "$ROOT/linux-agent/profiles/$(printf '%s' "$TARGET" | tr '_' '-').conf" "$OUT/HARDWARE-PROFILE.conf" 2>/dev/null || true
    ;;
esac

cat > "$OUT/BUILD-MANIFEST.txt" <<EOF
BlazePwifi version: $(cat "$ROOT/VERSION")
OpenWrt version: $VER
Target: $TARGET
OpenWrt target: $SUB
Profile: $PROFILE
Capability: $( [ "$KIND" = router ] && echo lite || { [ "$KIND" = x86 ] && echo full || echo standard; } )
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Paid authority installed preview: $PAID_PREVIEW
Paid v2 commit/replay authorized: 0
Customer install authorized: 0
EOF
if [ "$PAID_PREVIEW" -eq 1 ]; then
  printf 'Source commit: %s\nSDK package SHA256: %s\n' "$SOURCE_SHA" "$(sha256sum "$PAID_APK" | cut -d ' ' -f 1)" >> "$OUT/BUILD-MANIFEST.txt"
fi
(cd "$OUT" && sha256sum * | grep -v ' SHA256SUMS$' > SHA256SUMS)
echo "BlazePwifi $TARGET images ready in $OUT"
