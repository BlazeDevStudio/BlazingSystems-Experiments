#!/bin/bash
set -euo pipefail
DIR="${1:?usage: x86_v04_qemu_audit.sh ARTIFACT_DIR [OUT]}"
OUT="${2:-x86-v04-audit}"
mkdir -p "$OUT"
MAN="$(find "$DIR" -type f -name BUILD-MANIFEST.txt -print -quit)"
SUMS="$(find "$DIR" -type f -name SHA256SUMS -print -quit)"
test -n "$MAN" -a -n "$SUMS"
grep -Fq 'Target: x86_64' "$MAN"
grep -Fq 'Profile: generic' "$MAN"
(cd "$(dirname "$SUMS")" && sha256sum -c "$(basename "$SUMS")") | tee "$OUT/checksums.txt"

BIOSGZ="$(find "$DIR" -type f -name '*ext4-combined.img.gz' ! -name '*efi*' -print -quit)"
[ -n "$BIOSGZ" ] || BIOSGZ="$(find "$DIR" -type f -name '*combined.img.gz' ! -name '*efi*' -print -quit)"
EFIGZ="$(find "$DIR" -type f -name '*ext4-combined-efi.img.gz' -print -quit)"
[ -n "$EFIGZ" ] || EFIGZ="$(find "$DIR" -type f -name '*combined-efi.img.gz' -print -quit)"
test -n "$BIOSGZ" -a -n "$EFIGZ"
gzip -t "$BIOSGZ"; gzip -t "$EFIGZ"
gzip -dc "$BIOSGZ" > "$OUT/bios.img"
gzip -dc "$EFIGZ" > "$OUT/uefi.img"

boot_one(){
  local mode="$1" img="$2" log="$3"
  local extra=()
  if [ "$mode" = uefi ]; then
    local code vars
    code="$(find /usr/share/OVMF /usr/share/ovmf -type f \( -name 'OVMF_CODE.fd' -o -name 'OVMF_CODE_4M.fd' \) 2>/dev/null | head -n1)"
    test -n "$code"
    case "$(basename "$code")" in
      *4M*) vars="$(dirname "$code")/OVMF_VARS_4M.fd" ;;
      *) vars="$(dirname "$code")/OVMF_VARS.fd" ;;
    esac
    test -f "$vars"
    cp "$vars" "$OUT/ovmf-vars.fd"
    extra=(-drive "if=pflash,format=raw,readonly=on,file=$code" -drive "if=pflash,format=raw,file=$OUT/ovmf-vars.fd")
  fi
  set +e
  timeout 45 qemu-system-x86_64 -m 512 -smp 1     -drive "file=$img,format=raw,if=ide"     -nic user,model=e1000     -serial "file:$log" -display none -monitor none -no-reboot "${extra[@]}"
  rc=$?
  set -e
  [ "$rc" -eq 0 ] || [ "$rc" -eq 124 ] || return "$rc"
  grep -Eqi 'OpenWrt|procd|Please press Enter|urngd|br-lan' "$log"
}
boot_one bios "$OUT/bios.img" "$OUT/bios-serial.log"
boot_one uefi "$OUT/uefi.img" "$OUT/uefi-serial.log"

# Mount the exact BIOS candidate and verify BlazePwifi is in its rootfs.
LOOP="$(sudo losetup --show -Pf "$OUT/bios.img")"
MNT="$OUT/mnt"; mkdir -p "$MNT"
cleanup(){ sudo umount "$MNT" 2>/dev/null || true; sudo losetup -d "$LOOP" 2>/dev/null || true; }
trap cleanup EXIT
ROOTDEV=""
for p in "${LOOP}"p*; do
  [ -b "$p" ] || continue
  if sudo mount -o ro "$p" "$MNT" 2>/dev/null; then
    if [ -x "$MNT/etc/init.d/blazepwifi" ]; then ROOTDEV="$p"; break; fi
    sudo umount "$MNT"
  fi
done
test -n "$ROOTDEV"
test -x "$MNT/etc/init.d/blazepwifi"
test -f "$MNT/www/blazepwifi/admin.html"
test -x "$MNT/www/blazepwifi/cgi-bin/rental"

python3 - "$OUT/audit.json" "$BIOSGZ" "$EFIGZ" <<'PY'
import hashlib,json,sys,os
out,bios,efi=sys.argv[1:]
json.dump({"target":"x86_64","release":"0.4.0","validation_level":"qemu-bios-uefi-plus-rootfs",
 "bios_image":os.path.basename(bios),"uefi_image":os.path.basename(efi),
 "bios_sha256":hashlib.sha256(open(bios,'rb').read()).hexdigest(),
 "uefi_sha256":hashlib.sha256(open(efi,'rb').read()).hexdigest(),
 "checks":{"checksums":True,"bios_qemu_boot":True,"uefi_qemu_boot":True,
           "rootfs_mount":True,"blazepwifi_service":True,"admin_ui":True,"rental_api":True}},
 open(out,'w'),indent=2)
PY
echo "x86_64 BIOS/UEFI v0.4 QEMU audit passed"
