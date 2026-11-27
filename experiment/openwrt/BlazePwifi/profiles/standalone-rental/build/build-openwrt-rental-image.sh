#!/bin/sh
set -eu

VER="${OPENWRT_VERSION:-25.12.5}"
TARGET="${1:-ruijie}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)"
PROFILE_ROOT="$ROOT/profiles/standalone-rental"
WORK="${WORKDIR:-/tmp/blazepwifi-rental-imagebuilder}"

case "$TARGET" in
  ruijie)
    SUB="ramips/mt7621"; PROFILE="ruijie_rg-ew1200g-pro-v1.1"; KIND="router"; INSTALL_TARGET="ew1200g-pro"
    IB="openwrt-imagebuilder-$VER-ramips-mt7621.Linux-x86_64.tar.zst"
    ;;
  x86_64)
    SUB="x86/64"; PROFILE="generic"; KIND="x86"; INSTALL_TARGET="generic"
    IB="openwrt-imagebuilder-$VER-x86-64.Linux-x86_64.tar.zst"
    ;;
  *) echo "usage: $0 {ruijie|x86_64}" >&2; exit 2 ;;
esac

BASE="https://downloads.openwrt.org/releases/$VER/targets/$SUB"
rm -rf "$WORK"
mkdir -p "$WORK/rootfs"
FILES="$WORK/rootfs"
cp -a "$ROOT/openwrt/rootfs/." "$FILES/"

mkdir -p "$FILES/usr/share/blazepwifi" "$FILES/usr/share/blazepwifi-rental-installer" "$FILES/etc/uci-defaults"
if [ -f "$FILES/etc/uci-defaults/99-blazepwifi" ]; then
  mv "$FILES/etc/uci-defaults/99-blazepwifi" "$FILES/usr/share/blazepwifi/full-uci-defaults.sh"
  chmod 755 "$FILES/usr/share/blazepwifi/full-uci-defaults.sh"
fi

cp -p "$PROFILE_ROOT/openwrt/install.sh" "$FILES/usr/share/blazepwifi-rental-installer/install.sh"
cp -p "$PROFILE_ROOT/openwrt/upgrade-to-full.sh" "$FILES/usr/share/blazepwifi-rental-installer/upgrade-to-full.sh"
cp -p "$PROFILE_ROOT/openwrt/rental-profile" "$FILES/usr/share/blazepwifi-rental-installer/rental-profile"
cp -p "$PROFILE_ROOT/openwrt/rental-standalone.html" "$FILES/usr/share/blazepwifi-rental-installer/rental-standalone.html"
chmod 755 "$FILES/usr/share/blazepwifi-rental-installer/"*.sh "$FILES/usr/share/blazepwifi-rental-installer/rental-profile"

cat > "$FILES/etc/uci-defaults/98-blazepwifi-rental-standalone" <<EOF
#!/bin/sh
set -eu
cd /usr/share/blazepwifi-rental-installer
sh ./install.sh --preinstalled --target=$INSTALL_TARGET
exit 0
EOF
chmod 755 "$FILES/etc/uci-defaults/98-blazepwifi-rental-standalone"

PACKAGES="uhttpd px5g-mbedtls openssl-util flock"
cd "$WORK"
command -v curl >/dev/null || { echo "curl required" >&2; exit 1; }
command -v zstd >/dev/null || { echo "zstd required" >&2; exit 1; }

curl -fL "$BASE/$IB" -o "$IB"
curl -fsSL "$BASE/sha256sums" -o sha256sums
EXPECTED="$(awk -v f="$IB" '$2=="*"f || $2==f {print $1;exit}' sha256sums)"
[ -n "$EXPECTED" ] || { echo "checksum entry not found for $IB" >&2; exit 1; }
echo "$EXPECTED  $IB" | sha256sum -c -

tar --zstd -xf "$IB"
D="$(find . -maxdepth 1 -type d -name 'openwrt-imagebuilder-*' | head -n1)"
[ -n "$D" ] || { echo "ImageBuilder extraction failed" >&2; exit 1; }
mv "$D" imagebuilder
cd imagebuilder
make image PROFILE="$PROFILE" PACKAGES="$PACKAGES" FILES="$FILES"

OUT="$ROOT/dist/rental-$TARGET"
rm -rf "$OUT"; mkdir -p "$OUT"

case "$KIND" in
  router)
    IMG="$(find bin/targets -type f -name '*ruijie_rg-ew1200g-pro-v1.1-squashfs-sysupgrade.bin' -print -quit)"
    [ -n "$IMG" ] && [ -s "$IMG" ] || { echo "EW1200G Pro sysupgrade image missing" >&2; exit 1; }
    cp "$IMG" "$OUT/BlazePwifi-Rental-Standalone-EW1200G-Pro-v1.1-sysupgrade.bin"
    BOOTSTRAP="openwrt-$VER-ramips-mt7621-ruijie_rg-ew1200g-pro-v1.1-initramfs-kernel.bin"
    BOOTSTRAP_SHA="$(awk -v f="$BOOTSTRAP" '$2=="*"f || $2==f {print $1;exit}' "$WORK/sha256sums")"
    if [ -n "$BOOTSTRAP_SHA" ]; then
      curl -fL "$BASE/$BOOTSTRAP" -o "$OUT/OpenWrt-EW1200G-Pro-v1.1-recovery-initramfs.bin"
      echo "$BOOTSTRAP_SHA  $OUT/OpenWrt-EW1200G-Pro-v1.1-recovery-initramfs.bin" | sha256sum -c -
    fi
    cat > "$OUT/FLASH-NOTES.txt" <<EOF
BlazePwifi Rental Standalone - Ruijie RG-EW1200G Pro v1.1
The sysupgrade BIN contains OpenWrt $VER plus the complete BlazePwifi software payload in Rental Standalone mode.
The Rental first-boot installer does not write network, wireless or firewall UCI packages.
Flashing firmware itself can replace/preserve OpenWrt configuration according to the sysupgrade options used.
Confirm exact hardware revision and recovery access before flashing.
EOF
    ;;
  x86)
    BIOS="$(find bin/targets -type f -name '*generic-ext4-combined.img.gz' ! -name '*efi*' -print -quit)"
    EFI="$(find bin/targets -type f -name '*generic-ext4-combined-efi.img.gz' -print -quit)"
    [ -n "$BIOS" ] && [ -s "$BIOS" ] || { echo "x86 BIOS image missing" >&2; exit 1; }
    [ -n "$EFI" ] && [ -s "$EFI" ] || { echo "x86 UEFI image missing" >&2; exit 1; }
    cp "$BIOS" "$OUT/BlazePwifi-Rental-Standalone-x86_64-BIOS.img.gz"
    cp "$EFI" "$OUT/BlazePwifi-Rental-Standalone-x86_64-UEFI.img.gz"
    gzip -t "$OUT/"*.img.gz
    ;;
esac

cat > "$OUT/BUILD-MANIFEST.txt" <<EOF
Edition: BlazePwifi Rental Standalone
Edition version: 0.5.0-rental-rc.3
OpenWrt version: $VER
Target: $TARGET
OpenWrt target: $SUB
Profile: $PROFILE
Full BlazePwifi payload present: yes
Hotspot core activated by image first boot: no
Rental management route: /rental/
Android server base: http://LocalIP
Remote coin protocol port: 4455
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
(cd "$OUT" && sha256sum * | grep -v ' SHA256SUMS$' > SHA256SUMS)
echo "Rental Standalone image ready in $OUT"
