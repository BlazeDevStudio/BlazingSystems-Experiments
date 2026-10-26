#!/bin/sh
set -eu
cd "$(dirname "$0")"
[ "$(id -u)" = 0 ] || { echo 'Run as the router administrator.'; exit 1; }
if command -v apk >/dev/null 2>&1 && ! command -v opkg >/dev/null 2>&1; then
 echo 'This release contains opkg IPKs, not signed OpenWrt APKs. Installation stopped without changes.'; exit 1
fi
command -v opkg >/dev/null || { echo 'A supported OpenWrt opkg runtime is required.'; exit 1; }
command -v sha256sum >/dev/null || { echo 'SHA-256 verification is required.'; exit 1; }
[ -f PACKAGE-SHA256SUMS ] || { echo 'Package checksums are missing.'; exit 1; }
sha256sum -c PACKAGE-SHA256SUMS
[ -f ./EasyMode-v7.0.2-Core-all.ipk ] || { echo 'Core package is missing.'; exit 1; }
set -- ./EasyMode-v7.0.2-*-all.ipk
[ "$#" -eq 2 ] || { echo 'Expected one Core package and one edition package in this bundle.'; exit 1; }
edition=
for pkg in "$@"; do case "$pkg" in *-Core-*) ;; *) edition=$pkg;; esac; done
[ -n "$edition" ] || { echo 'Edition package is missing.'; exit 1; }
. /etc/openwrt_release
case "$DISTRIB_RELEASE" in 24.10.*) ;; *) echo 'Validated runtime family: OpenWrt 24.10. Installation stopped.'; exit 1 ;; esac
for pkg in ucode ucode-mod-fs ucode-mod-uci ucode-mod-ubus rpcd rpcd-mod-ucode uhttpd-mod-ubus nftables-json; do
 opkg status "$pkg" | grep -q '^Status:.* installed' || { echo "Missing runtime dependency: $pkg. Install from your matching OpenWrt feed, then retry."; exit 1; }
done
umask 077
mkdir -p /etc/easymode-traffic
sysupgrade -b /etc/easymode-traffic/pre-v7-settings.tar.gz
opkg install ./EasyMode-v7.0.2-Core-all.ipk
opkg install "$edition"
echo 'EasyMode Traffic Intelligence installed. Open /traffic/?v=7.0.2 on your router. Existing management and network settings are preserved.'
