#!/bin/sh
# Application update only; preserves settings and never flashes/reboots.
set -eu
cd "$(dirname "$0")"
[ "$(cat /tmp/sysinfo/board_name)" = notion,r281 ] || { echo 'Requires notion,r281.';exit 1; }
[ "$(. /etc/openwrt_release; echo "$DISTRIB_RELEASE")" = 24.10.8 ] || { echo 'Requires OpenWrt 24.10.8.';exit 1; }
[ "$(tr -d '\r\n' </etc/blaze/easymode-version)" = 4.2.6 ] || { echo 'Requires EasyMode 4.2.6.';exit 1; }
[ -f /usr/share/blaze/common.uc ] && [ -x /usr/bin/ucode ] && [ -x /usr/bin/flock ]
sha256sum -c SHA256SUMS
[ "${1:-}" != --check ] || { echo 'PASS: compatibility, dependencies and checksums; no changes.';exit 0; }
[ "${1:-}" = --apply ] || { echo 'Use --check, then --apply.';exit 1; }
/usr/libexec/blaze-lock-claim job "$$"
umask 077
backup="/root/easymode-before-sms-archive-$(date +%Y%m%d-%H%M%S).tar.gz"
list="/tmp/blaze-update-files.$$"
missing="/tmp/blaze-update-missing.$$"
: >"$list"; : >"$missing"
for path in $(find root -type f);do
 target="${path#root/}"
 if [ -f "/$target" ];then echo "$target" >>"$list";else echo "$target" >>"$missing";fi
done
ok=0
finish() {
 if [ "$ok" != 1 ];then
  /etc/init.d/blaze-sms-archive stop 2>/dev/null || true
  /etc/init.d/blaze-sms-archive disable 2>/dev/null || true
 fi
 if [ "$ok" != 1 ] && [ -s "$backup" ];then
  while IFS= read -r target;do rm -f "/$target";done <"$missing"
  tar -xzf "$backup" -C /
  echo "Update failed; restored $backup"
 fi
 rm -f "$list" "$missing" /tmp/blaze-job.lock/pid /tmp/blaze-job.lock/id
 rmdir /tmp/blaze-job.lock 2>/dev/null || true
 if [ "$ok" != 1 ];then /etc/init.d/rpcd restart;fi
}
trap finish EXIT
tar -czf "$backup" -C / -T "$list"
umask 022
for path in $(find root -type f);do
 target="/${path#root/}";mkdir -p "$(dirname "$target")"
 cp "$path" "$target.sites-new";mv "$target.sites-new" "$target"
done
for module in sms-inbox-archive message;do ucode -c -o /tmp/blaze-module-check.ucb "/usr/share/blaze/$module.uc";done
ucode -c -o /tmp/blaze-rpc-check.ucb /usr/share/rpcd/ucode/blaze
sh -n /usr/libexec/blaze-job
sh -n /usr/libexec/blaze-health
sed -e 's|/easy/app.js?v=[^" ]*|/easy/app.js?v=4.2.6-sms2|' -e 's|/easy/style.css?v=[^" ]*|/easy/style.css?v=4.2.6-sms2|' /www/index.html >/www/index.html.sites-new
chmod 644 /www/index.html.sites-new
mv /www/index.html.sites-new /www/index.html
chmod 644 /www/easy/app.js /www/index.html
/etc/init.d/rpcd restart
/etc/init.d/blaze-sms-archive enable
if /etc/init.d/blaze-sms-archive status >/dev/null 2>&1;then /etc/init.d/blaze-sms-archive restart;else /etc/init.d/blaze-sms-archive start;fi
ok=1
echo "Installed. Backup: $backup. No reboot or Wi-Fi reload."
