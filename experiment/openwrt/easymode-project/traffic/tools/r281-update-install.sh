#!/bin/sh
# Deliberate administrator update; never flashes or changes router configuration.
set -eu
cd "$(dirname "$0")"
[ "$(cat /tmp/sysinfo/board_name)" = notion,r281 ] || { echo 'Requires verified notion,r281 board.';exit 1; }
[ "$(. /etc/openwrt_release; echo "$DISTRIB_RELEASE")" = 24.10.8 ] || { echo 'Requires OpenWrt 24.10.8.';exit 1; }
[ "$(tr -d '\r\n' </etc/blaze/easymode-version)" = 4.2.6 ] || { echo 'Requires existing EasyMode 4.2.6 management.';exit 1; }
[ -f /usr/share/blaze/common.uc ] && [ -x /usr/libexec/blaze-lock-claim ]
sha256sum -c SHA256SUMS
if [ "${1:-}" = --check ];then echo 'PASS: compatibility and checksums. No files changed.';exit 0;fi
[ "${1:-}" = --apply ] || { echo 'Use --check first, then --apply to install deliberately.';exit 1; }
/usr/libexec/blaze-lock-claim job "$$"
backup="/root/easymode-before-ssid-$(date +%Y%m%d-%H%M%S).tar.gz"
ok=0
finish() {
 if [ "$ok" != 1 ] && [ -s "$backup" ];then tar -xzf "$backup" -C /;echo "Update failed; previous files restored from $backup";fi
 rm -f /tmp/blaze-job.lock/pid /tmp/blaze-job.lock/id
 rmdir /tmp/blaze-job.lock 2>/dev/null || true
 /etc/init.d/rpcd restart
 /etc/init.d/blaze-health restart
}
trap finish EXIT
umask 077
tar -czf "$backup" -C / etc/config usr/share/blaze usr/share/rpcd/ucode/blaze usr/libexec/blaze-launch usr/libexec/blaze-job usr/libexec/blaze-health www/easy/app.js www/index.html
for path in $(find root -type f);do target="/${path#root/}";cp "$path" "$target.ssid-new";mv "$target.ssid-new" "$target";done
ucode -c -o /tmp/blaze-settings-check.ucb /usr/share/blaze/settings.uc
ucode -c -o /tmp/blaze-rpc-check.ucb /usr/share/rpcd/ucode/blaze
sh -n /usr/libexec/blaze-job
sh -n /usr/libexec/blaze-health
# Preserve installed navigation and appearance. Only refresh the asset version.
sed 's|/easy/app.js?v=[^" ]*|/easy/app.js?v=4.2.6-ssid1|' /www/index.html >/www/index.html.ssid-new
chmod 644 /www/index.html.ssid-new
mv /www/index.html.ssid-new /www/index.html
ok=1
echo "Installed. Backup: $backup. Sign in again if needed. No reboot or Wi-Fi reload performed."
