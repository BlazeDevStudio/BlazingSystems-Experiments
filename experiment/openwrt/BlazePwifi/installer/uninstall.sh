#!/bin/sh
set -eu
[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
/etc/init.d/blazepwifi stop 2>/dev/null || true
/etc/init.d/blazepwifi disable 2>/dev/null || true
nft delete table inet blazepwifi 2>/dev/null || true
for s in blazepwifi blazepwifi_vendo blazepwifi_admin; do uci -q delete "uhttpd.$s" || true; done
for r in blazepwifi_portal blazepwifi_vendo blazepwifi_admin; do uci -q delete "firewall.$r" || true; done
uci commit uhttpd
uci commit firewall
/etc/init.d/firewall reload 2>/dev/null || true
/etc/init.d/uhttpd restart 2>/dev/null || true
rm -rf /www/blazepwifi /usr/lib/blazepwifi /usr/sbin/blazepwifi-core /etc/init.d/blazepwifi
printf 'BlazePwifi runtime removed. Persistent state, keys, and /etc/config/blazepwifi were retained.\n'
