#!/bin/sh
# Application update only; preserves settings and never flashes/reboots.
set -eu
cd "$(dirname "$0")"
[ "$(cat /tmp/sysinfo/board_name)" = notion,r281 ] || { echo 'Requires notion,r281.';exit 1; }
[ "$(. /etc/openwrt_release; echo "$DISTRIB_RELEASE")" = 24.10.8 ] || { echo 'Requires OpenWrt 24.10.8.';exit 1; }
[ "$(tr -d '\r\n' </etc/blaze/easymode-version)" = 4.2.6 ] || { echo 'Requires EasyMode 4.2.6.';exit 1; }
[ -f /usr/share/blaze/common.uc ] && [ -x /usr/libexec/blaze-lock-claim ]
ucode -e "import * as socket from 'socket';" || { echo 'Install matching official ucode-mod-socket first.';exit 1; }
opkg status kmod-nft-bridge | grep -q 'Status:.* installed' || { echo 'Install exact-kernel kmod-nft-bridge first.';exit 1; }
sha256sum -c SHA256SUMS
[ "${1:-}" != --check ] || { echo 'PASS: compatibility, dependencies and checksums; no changes.';exit 0; }
[ "${1:-}" = --apply ] || { echo 'Use --check, then --apply.';exit 1; }
/usr/libexec/blaze-lock-claim job "$$"
umask 077
backup="/root/easymode-before-sites-$(date +%Y%m%d-%H%M%S).tar.gz"
list="/tmp/blaze-update-files.$$"
missing="/tmp/blaze-update-missing.$$"
: >"$list"; : >"$missing"
for path in $(find root -type f);do
 target="${path#root/}"
 if [ -f "/$target" ];then echo "$target" >>"$list";else echo "$target" >>"$missing";fi
done
for target in www/index.html etc/blaze/sites.json;do
 if [ -f "/$target" ];then echo "$target" >>"$list";else echo "$target" >>"$missing";fi
done
ok=0
finish() {
 if [ "$ok" != 1 ] && [ -s "$backup" ];then
  /etc/init.d/blaze-sites stop 2>/dev/null || true
  while IFS= read -r target;do rm -f "/$target";done <"$missing"
  tar -xzf "$backup" -C /
  echo "Update failed; restored $backup"
 fi
 rm -f "$list" "$missing" /tmp/blaze-job.lock/pid /tmp/blaze-job.lock/id
 rmdir /tmp/blaze-job.lock 2>/dev/null || true
 /etc/init.d/rpcd restart
 /etc/init.d/blaze-health restart
 [ ! -x /etc/init.d/blaze-sites ] || /etc/init.d/blaze-sites restart
}
trap finish EXIT
tar -czf "$backup" -C / -T "$list"
umask 022
for path in $(find root -type f);do
 target="/${path#root/}";mkdir -p "$(dirname "$target")"
 cp "$path" "$target.sites-new";mv "$target.sites-new" "$target"
done
[ -f /etc/blaze/sites.json ] || printf '%s\n' '{"enabled":false,"mode":"off","domains":[],"devices":[]}' >/etc/blaze/sites.json
for module in settings sites-daemon sites-firewall sites-apply;do ucode -c -o /tmp/blaze-module-check.ucb "/usr/share/blaze/$module.uc";done
ucode -c -o /tmp/blaze-rpc-check.ucb /usr/share/rpcd/ucode/blaze
sh -n /usr/libexec/blaze-job
sh -n /usr/libexec/blaze-health
fw4 check
/etc/init.d/firewall reload
/etc/init.d/blaze-sites enable
/etc/init.d/blaze-sites restart
sed 's|/easy/app.js?v=[^" ]*|/easy/app.js?v=4.2.6-mgmt1|' /www/index.html >/www/index.html.sites-new
chmod 644 /www/index.html.sites-new
mv /www/index.html.sites-new /www/index.html
chmod 644 /www/easy/app.js /www/index.html
ok=1
echo "Installed. Backup: $backup. No reboot or Wi-Fi reload."
