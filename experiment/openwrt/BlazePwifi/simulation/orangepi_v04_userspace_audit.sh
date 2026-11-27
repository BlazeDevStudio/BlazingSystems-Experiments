#!/bin/bash
set -euo pipefail
DIR="${1:?usage: orangepi_v04_userspace_audit.sh ARTIFACT_DIR target [OUT]}"
TARGET="${2:?missing target}"
OUT="${3:-orangepi-v04-audit}"
mkdir -p "$OUT"
MAN="$(find "$DIR" -type f -name BUILD-MANIFEST.txt -print -quit)"
SUMS="$(find "$DIR" -type f -name SHA256SUMS -print -quit)"
GZ="$(find "$DIR" -type f -name '*-ext4-sdcard.img.gz' -print -quit)"
[ -n "$GZ" ] || GZ="$(find "$DIR" -type f -name '*.img.gz' -print -quit)"
test -n "$MAN" -a -n "$SUMS" -a -n "$GZ" -a -s "$GZ"
grep -Fq "Target: $TARGET" "$MAN"
(cd "$(dirname "$SUMS")" && sha256sum -c "$(basename "$SUMS")") | tee "$OUT/checksums.txt"
gzip -t "$GZ"
IMG="$OUT/candidate.img"
gzip -dc "$GZ" > "$IMG"
fdisk -l "$IMG" > "$OUT/fdisk.txt" 2>&1 || true

MNT="$OUT/mnt"
mkdir -p "$MNT"
cleanup(){
  sudo umount "$MNT" 2>/dev/null || true
}
trap cleanup EXIT

# OpenWrt sunxi ext4 sdcard images can contain a few non-sector-aligned
# trailer bytes. losetup --partscan may then omit /dev/loopXp2 on some hosted
# kernels even though fdisk reports a valid partition table. Mount the Linux
# root partition by its explicit sector offset instead.
read -r ROOT_START ROOT_SECTORS <<EOF
$(fdisk -l "$IMG" | awk '$NF=="Linux" {print $2, $4; exit}')
EOF
if ! [[ "$ROOT_START" =~ ^[0-9]+$ && "$ROOT_SECTORS" =~ ^[0-9]+$ ]]; then
  echo "could not parse OpenWrt Linux rootfs partition" >&2
  cat "$OUT/fdisk.txt" >&2 || true
  exit 1
fi
ROOT_OFFSET=$((ROOT_START * 512))
ROOT_LIMIT=$((ROOT_SECTORS * 512))
sudo mount -o "ro,loop,offset=$ROOT_OFFSET,sizelimit=$ROOT_LIMIT" "$IMG" "$MNT"
ROOTDEV="offset-sector:$ROOT_START"
if [ ! -f "$MNT/etc/openwrt_release" ] && [ ! -x "$MNT/etc/init.d/blazepwifi" ]; then
  echo "mounted Linux partition is not an OpenWrt rootfs" >&2
  exit 1
fi
test -x "$MNT/etc/init.d/blazepwifi"
test -x "$MNT/usr/sbin/blazepwifi-gpio-agent"
test -d "$MNT/usr/share/blazepwifi/orangepi"
test -f "$MNT/www/blazepwifi/admin.html"
test -x "$MNT/bin/busybox"

ARCH="$(file "$MNT/bin/busybox")"
printf '%s\n' "$ARCH" > "$OUT/busybox-file.txt"
if printf '%s' "$ARCH" | grep -qi 'aarch64\|ARM aarch64'; then
  QEMU="$(command -v qemu-aarch64-static)"
else
  QEMU="$(command -v qemu-arm-static)"
fi
"$QEMU" -L "$MNT" "$MNT/bin/busybox" echo BLAZE_ARM_USERSPACE_OK > "$OUT/qemu-user.txt"
grep -Fq BLAZE_ARM_USERSPACE_OK "$OUT/qemu-user.txt"

python3 - "$OUT/audit.json" "$TARGET" "$GZ" "$ROOTDEV" <<'PY'
import hashlib,json,sys,os
out,target,gz,rootdev=sys.argv[1:]
json.dump({"target":target,"release":"0.4.0",
 "validation_level":"disk-structure-rootfs-and-qemu-user",
 "image":os.path.basename(gz),"sha256_gzip":hashlib.sha256(open(gz,'rb').read()).hexdigest(),
 "root_partition":rootdev,
 "checks":{"target_manifest":True,"checksums":True,"gzip":True,"rootfs_mount":True,
           "blazepwifi_service":True,"gpio_agent":True,"admin_ui":True,"qemu_user_busybox":True}},
 open(out,'w'),indent=2)
PY
echo "$TARGET v0.4 image/userspace audit passed"
