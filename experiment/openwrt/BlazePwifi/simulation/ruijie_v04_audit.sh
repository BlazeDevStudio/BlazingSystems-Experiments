#!/bin/bash
set -euo pipefail
DIR="${1:?usage: ruijie_v04_audit.sh ARTIFACT_DIR [OUT]}"
OUT="${2:-ruijie-v04-audit}"
mkdir -p "$OUT"

MAN="$(find "$DIR" -type f -name BUILD-MANIFEST.txt -print -quit)"
SUMS="$(find "$DIR" -type f -name SHA256SUMS -print -quit)"
IMG="$(find "$DIR" -type f -name '*ruijie_rg-ew1200g-pro-v1.1-squashfs-sysupgrade.bin' -print -quit)"
test -n "$MAN" -a -n "$SUMS" -a -n "$IMG" -a -s "$IMG"
grep -Fq 'Target: ruijie' "$MAN"
grep -Fq 'Profile: ruijie_rg-ew1200g-pro-v1.1' "$MAN"
(cd "$(dirname "$SUMS")" && sha256sum -c "$(basename "$SUMS")") | tee "$OUT/checksums.txt"
file "$IMG" | tee "$OUT/file.txt"
grep -Fq 'u-boot legacy uImage' "$OUT/file.txt"

ROOTIMG="$OUT/root.squashfs"
OFFSET_FILE="$OUT/squashfs-offset.txt"
python3 - "$IMG" "$ROOTIMG" "$OFFSET_FILE" <<'PY'
import struct,sys
src,out,offset_file=sys.argv[1:]
data=open(src,'rb').read()
if len(data) < 64 or data[:4] != bytes.fromhex('27051956'):
    raise SystemExit('unexpected Ruijie sysupgrade uImage header')
kernel_size=struct.unpack('>I',data[12:16])[0]
search_from=64+kernel_size
offset=data.find(b'hsqs',search_from)
if offset < 0:
    raise SystemExit('squashfs rootfs magic not found after uImage payload')
open(out,'wb').write(data[offset:])
open(offset_file,'w').write(str(offset)+'\n')
print('kernel_payload_bytes='+str(kernel_size))
print('squashfs_offset='+str(offset))
PY

test -s "$ROOTIMG"
file "$ROOTIMG" | tee "$OUT/root-file.txt"
grep -qi 'Squashfs filesystem' "$OUT/root-file.txt"

mkdir -p "$OUT/rootfs"
sudo unsquashfs -f -d "$OUT/rootfs" "$ROOTIMG" > "$OUT/unsquashfs.txt"
sudo chmod -R a+rX "$OUT/rootfs"
test -x "$OUT/rootfs/etc/init.d/blazepwifi"
test -f "$OUT/rootfs/www/blazepwifi/admin.html"
test -x "$OUT/rootfs/www/blazepwifi/cgi-bin/rental"
test -f "$OUT/rootfs/www/blazepwifi/vendor/tailadmin/blaze-tailadmin.css"

python3 - "$OUT/audit.json" "$IMG" "$OFFSET_FILE" <<'PY'
import hashlib,json,sys,os
out,path,offset_file=sys.argv[1:]
offset=int(open(offset_file).read().strip())
json.dump({
 "target":"ruijie_rg-ew1200g-pro-v1.1",
 "release":"0.4.0",
 "validation_level":"uimage-plus-squashfs-rootfs-extraction",
 "firmware":os.path.basename(path),
 "sha256":hashlib.sha256(open(path,'rb').read()).hexdigest(),
 "squashfs_offset":offset,
 "checks":{
   "target_manifest":True,
   "checksums":True,
   "uimage_header":True,
   "squashfs_found_after_kernel":True,
   "squashfs_extract":True,
   "blazepwifi_service":True,
   "admin_ui":True,
   "rental_api":True
 }
},open(out,'w'),indent=2)
PY
echo "Ruijie v0.4 structural audit passed (not a physical MT7621 boot claim)"
