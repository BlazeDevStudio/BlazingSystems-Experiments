#!/bin/sh
set -eu
base=$(pwd)
url=https://downloads.openwrt.org/releases/24.10.8/targets/x86/64
builder=openwrt-imagebuilder-24.10.8-x86-64.Linux-x86_64
mkdir -p /tmp/easymode-image
cd /tmp/easymode-image
curl --fail --location --retry 2 "$url/$builder.tar.zst" -o builder.tar.zst
echo '1b0511a92126ed97550d91295459f8869962f9b7c31dd3d0c7cda75c75825741  builder.tar.zst' | sha256sum -c -
tar --zstd -xf builder.tar.zst
cd "$builder"
mkdir -p files
cp -a "$base/traffic/root/." files/
chmod 755 files/etc/init.d/* files/etc/uci-defaults/* files/usr/libexec/*
sed -i "s/option edition 'generic'/option edition 'pc'/" files/etc/config/easymode_traffic
make image PROFILE=generic PACKAGES='luci uhttpd-mod-ubus rpcd-mod-ucode ucode-mod-fs ucode-mod-ubus ucode-mod-uci nftables-json' FILES="$PWD/files" ROOTFS_PARTSIZE=128
out="$base/dist-v7"
cp bin/targets/x86/64/openwrt-24.10.8-x86-64-generic-squashfs-combined.img.gz "$out/EasyMode-v7.0.2-PC-x86_64-BIOS.img.gz"
cp bin/targets/x86/64/openwrt-24.10.8-x86-64-generic-squashfs-combined-efi.img.gz "$out/EasyMode-v7.0.2-PC-x86_64-UEFI.img.gz"
cp bin/targets/x86/64/profiles.json "$out/OpenWrt-24.10.8-x86_64-profiles.json"
# Official x86 generic clears SUPPORTED_DEVICES: its trailer contains a signature,
# not the device-metadata record emitted by board-specific router targets.
staging_dir/host/bin/fwtool -s "$out/BIOS-IMAGE-SIGNATURE.ucert" "$out/EasyMode-v7.0.2-PC-x86_64-BIOS.img.gz"
staging_dir/host/bin/fwtool -s "$out/UEFI-IMAGE-SIGNATURE.ucert" "$out/EasyMode-v7.0.2-PC-x86_64-UEFI.img.gz"
cp bin/targets/x86/64/*.manifest "$out/" 2>/dev/null || true
cd "$base"
python3 traffic/tools/build.py
