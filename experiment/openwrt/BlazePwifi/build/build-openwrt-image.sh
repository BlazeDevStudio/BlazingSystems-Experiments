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

[ -f "$IB" ] || curl -fL "$BASE/$IB" -o "$IB"
curl -fsSL "$BASE/sha256sums" -o sha256sums
EXPECTED="$(awk -v f="$IB" '$2=="*"f || $2==f {print $1;exit}' sha256sums)"
[ -n "$EXPECTED" ] || { echo "checksum entry not found for $IB" >&2; exit 1; }
echo "$EXPECTED  $IB" | sha256sum -c -

rm -rf imagebuilder
tar --zstd -xf "$IB"
D="$(find . -maxdepth 1 -type d -name 'openwrt-imagebuilder-*' | head -n1)"
[ -n "$D" ] || { echo "ImageBuilder extraction failed" >&2; exit 1; }
mv "$D" imagebuilder
cd imagebuilder

make image PROFILE="$PROFILE" PACKAGES="$PACKAGES" FILES="$FILES_DIR"

OUT="$ROOT/dist/$TARGET"
rm -rf "$OUT"
mkdir -p "$OUT"

case "$KIND" in
  router)
    find bin/targets -type f -name '*ruijie_rg-ew1200g-pro-v1.1-squashfs-sysupgrade.bin' -exec cp -v {} "$OUT/" \;
    ls "$OUT/"*squashfs-sysupgrade.bin >/dev/null 2>&1 || { echo "Ruijie BlazePwifi sysupgrade image missing" >&2; exit 1; }
    BOOTSTRAP="openwrt-$VER-ramips-mt7621-ruijie_rg-ew1200g-pro-v1.1-initramfs-kernel.bin"
    BOOTSTRAP_SHA="$(awk -v f="$BOOTSTRAP" '$2=="*"f || $2==f {print $1;exit}' "$WORK/sha256sums")"
    [ -n "$BOOTSTRAP_SHA" ] || { echo "Official Ruijie bootstrap checksum entry missing" >&2; exit 1; }
    curl -fL "$BASE/$BOOTSTRAP" -o "$OUT/$BOOTSTRAP"
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
EOF
(cd "$OUT" && sha256sum * | grep -v ' SHA256SUMS$' > SHA256SUMS)
echo "BlazePwifi $TARGET images ready in $OUT"
