#!/bin/sh
set -eu
PURGE=0
[ "${1:-}" = "--purge" ] && PURGE=1
[ "$(id -u)" = 0 ] || { echo "ERROR: run as root" >&2; exit 1; }

MARK=/etc/blazepwifi/RENTAL_STANDALONE
[ -f "$MARK" ] || { echo "ERROR: Rental Standalone marker not found." >&2; exit 1; }
WEB_ROOT="$(sed -n 's/^web_root=//p' "$MARK" | head -n1)"
CGI_DIR="$(sed -n 's/^cgi_dir=//p' "$MARK" | head -n1)"
[ -n "$WEB_ROOT" ] || WEB_ROOT="$(uci -q get uhttpd.main.home || echo /www)"
[ -n "$CGI_DIR" ] || CGI_DIR="$WEB_ROOT$(uci -q get uhttpd.main.cgi_prefix || echo /cgi-bin)"

uci -q delete uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1 || true
uci commit uhttpd >/dev/null 2>&1 || true

rm -rf "$WEB_ROOT/rental"
for f in rental blaze-rental-admin blaze-rental-login blaze-rental-session blaze-rental-logout blaze-rental-profile; do
  rm -f "$CGI_DIR/$f"
done
rm -f /usr/sbin/blazepwifi-rental-upgrade "$MARK"

/etc/init.d/uhttpd restart >/dev/null 2>&1 || true

if [ "$PURGE" -eq 1 ]; then
  /etc/init.d/blazepwifi stop >/dev/null 2>&1 || true
  /etc/init.d/blazepwifi disable >/dev/null 2>&1 || true
  rm -rf /usr/lib/blazepwifi /usr/sbin/blazepwifi-core /www/blazepwifi /etc/blazepwifi
  rm -f /etc/init.d/blazepwifi /etc/config/blazepwifi
  echo "Rental Standalone software and state purged."
else
  echo "Rental routes removed. Full BlazePwifi payload/state was preserved."
fi

echo "Network, wireless and firewall UCI packages were not modified."
