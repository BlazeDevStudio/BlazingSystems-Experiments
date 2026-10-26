#!/bin/sh
set -eu
cd "$(dirname "$0")"
[ "$(cat /tmp/sysinfo/board_name 2>/dev/null)" = notion,r281 ] || { echo 'Requires verified board notion,r281.'; exit 1; }
[ "$(. /etc/openwrt_release; echo "$DISTRIB_RELEASE")" = 24.10.8 ] || { echo 'Requires OpenWrt 24.10.8.'; exit 1; }
v=$(tr -d '\r\n' </etc/blaze/easymode-version 2>/dev/null || true)
[ "$v" = 4.2.6 ] || [ "$v" = 10.0.0 ] || [ "$v" = 10.1.0 ] || [ "$v" = 10.2.0 ] || { echo 'Requires the R281 EasyMode 4.2.6, 10.0.0, 10.1.0, or 10.2.0 baseline.'; exit 1; }
for x in tar sha256sum ucode rpcd; do command -v "$x" >/dev/null 2>&1 || { echo "Missing dependency: $x"; exit 1; }; done
sha256sum -c SHA256SUMS
for f in root/usr/libexec/* root/etc/init.d/* root/etc/uci-defaults/*; do
 [ -f "$f" ] || continue
 first=$(head -n1 "$f")
 case "$first" in '#!/bin/sh'|'#!/bin/ash') sh -n "$f";; '#!/usr/bin/ucode') ucode -c -o /tmp/blaze-v10.2-check.ucb "$f";; esac
done
module_check=/tmp/blaze-v10.2-module-check.uc
: >"$module_check"; n=0
for f in root/usr/share/blaze/*.uc; do
 [ -f "$f" ] || continue
 if grep -q '^[[:space:]]*export[[:space:]]' "$f"; then
  n=$((n+1));printf "import * as m%s from '%s/%s';\n" "$n" "$(pwd)" "$f" >>"$module_check"
 else
  ucode -c -o /tmp/blaze-v10.2-check.ucb "$f"
 fi
done
[ ! -s "$module_check" ] || ucode "$module_check"
ucode -c -o /tmp/blaze-v10.2-check.ucb root/usr/share/rpcd/ucode/blaze
rm -f /tmp/blaze-v10.2-check.ucb "$module_check"
[ "${1:-}" != --check ] || { echo 'PASS: exact board/release, baseline, dependencies, checksums; no changes.'; exit 0; }
[ "${1:-}" = --apply ] || { echo 'Use --check, then --apply.'; exit 1; }
[ -d root/etc/blaze ] && [ -d root/usr/share/blaze ] && [ -x root/usr/libexec/blaze-health ]
/usr/libexec/blaze-lock-claim job "$$"
umask 077
backup="/root/easymode-before-v10.2-$(date +%Y%m%d-%H%M%S).tar.gz"
list="/tmp/blaze-v10.2-files.$$"; missing="/tmp/blaze-v10.2-missing.$$"
maintenance=/tmp/blaze-maintenance.lock
pending=/etc/blaze/easymode-install.pending
: >"$list"; : >"$missing"
for path in $(find root -type f); do target="${path#root/}"; if [ -f "/$target" ]; then echo "$target" >>"$list"; else echo "$target" >>"$missing"; fi; done
ok=0
finish() {
 if [ "$ok" != 1 ]; then
  /etc/init.d/blaze-quality stop >/dev/null 2>&1 || true
  while IFS= read -r target; do rm -f "/$target"; done <"$missing"
  [ ! -s "$backup" ] || tar -xzf "$backup" -C /
  /etc/init.d/rpcd restart >/dev/null 2>&1 || true
  /etc/init.d/blaze-health restart >/dev/null 2>&1 || true
  [ ! -x /etc/init.d/blaze-quality ] || /etc/init.d/blaze-quality restart >/dev/null 2>&1 || true
  /etc/init.d/blaze-sms-archive restart >/dev/null 2>&1 || true
 fi
 rm -f "$maintenance" "$pending"
 rm -f "$list" "$missing" /tmp/blaze-job.lock/pid /tmp/blaze-job.lock/id
 rmdir /tmp/blaze-job.lock 2>/dev/null || true
}
trap finish EXIT HUP INT TERM
tar -czf "$backup" -C / -T "$list"
tar -tzf "$backup" >/dev/null
printf '10.2.0 %s\n' "$(date +%s)" >"$pending"
touch "$maintenance"
/etc/init.d/blaze-health stop
# Copy only packaged application files. Runtime UCI and /etc/blaze histories
# are not replaced; this update never writes network/Wi-Fi configuration.
for path in $(find root -type f); do
 target="/${path#root/}";mkdir -p "$(dirname "$target")"
 cp "$path" "$target.v10.2-new";case "$path" in root/usr/libexec/*|root/etc/init.d/*|root/etc/uci-defaults/*|*.sh) chmod 755 "$target.v10.2-new";;*) chmod 644 "$target.v10.2-new";;esac
 mv "$target.v10.2-new" "$target"
 [ "$(sha256sum "$path" | cut -d' ' -f1)" = "$(sha256sum "$target" | cut -d' ' -f1)" ]
done
for f in /usr/libexec/blaze-health /usr/libexec/blaze-watchdog-reboot /usr/libexec/blaze-quality /usr/libexec/blaze-job /etc/init.d/blaze-health /etc/init.d/blaze-quality /etc/init.d/blaze-sms-archive; do [ ! -f "$f" ] || sh -n "$f"; done
module_check=/tmp/blaze-v10.2-module-check.uc
: >"$module_check"; n=0
for f in /usr/share/blaze/*.uc; do
 if grep -q '^[[:space:]]*export[[:space:]]' "$f"; then
  n=$((n+1));printf "import * as m%s from '%s';\n" "$n" "$f" >>"$module_check"
 else
  ucode -c -o /tmp/blaze-v10.2-check.ucb "$f"
 fi
done
[ ! -s "$module_check" ] || ucode "$module_check"
ucode -c -o /tmp/blaze-v10.2-check.ucb /usr/share/rpcd/ucode/blaze
rm -f "$module_check" /tmp/blaze-v10.2-check.ucb
chmod 644 /www/index.html /www/easy/app.js /www/easy/core.js /www/easy/style.css /www/easy/refined.css
/etc/init.d/rpcd restart
/etc/init.d/blaze-health restart
/etc/init.d/blaze-quality enable >/dev/null 2>&1 || true
/etc/init.d/blaze-quality restart
/etc/init.d/blaze-sms-archive enable >/dev/null 2>&1 || true
/etc/init.d/blaze-sms-archive restart >/dev/null 2>&1 || true
ok=1
echo "Installed EasyMode v10.2.0 application. Backup: $backup. No network reload or reboot."
