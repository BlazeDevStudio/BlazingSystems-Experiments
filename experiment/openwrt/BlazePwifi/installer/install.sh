#!/bin/sh
set -eu
BASE="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
[ -f /etc/openwrt_release ] || { echo "ERROR: OpenWrt required" >&2; exit 1; }
. /etc/openwrt_release
case "${DISTRIB_RELEASE:-}" in 25.12.*) ;; *) echo "ERROR: BlazePwifi 0.2 targets OpenWrt 25.12.x; detected ${DISTRIB_RELEASE:-unknown}." >&2; exit 1;; esac
command -v apk >/dev/null || { echo "ERROR: apk package manager not found." >&2; exit 1; }
[ "$(id -u)" = 0 ] || { echo "ERROR: run as root" >&2; exit 1; }

FREE_KB="$(df -k /overlay 2>/dev/null | awk 'NR==2{print $4}')"; [ -n "${FREE_KB:-}" ] || FREE_KB=99999
[ "$FREE_KB" -ge 900 ] || { echo "ERROR: need at least 900 KB free overlay space; found ${FREE_KB} KB." >&2; exit 1; }

echo "Installing runtime packages..."
apk -U add uhttpd nftables px5g-mbedtls flock ip-full kmod-wireguard wireguard-tools >/dev/null
if ! apk -U add zerotier >/dev/null 2>&1; then
  echo "WARNING: ZeroTier package unavailable on this target; WireGuard remote access remains available." >&2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="/root/blazepwifi-backup-$STAMP"
mkdir -p "$BACKUP"
cp -a /etc/config/uhttpd "$BACKUP/" 2>/dev/null || true
cp -a /etc/config/firewall "$BACKUP/" 2>/dev/null || true
EXISTING_CONFIG=0
if [ -f /etc/config/blazepwifi ]; then
  cp -a /etc/config/blazepwifi "$BACKUP/blazepwifi.config"
  EXISTING_CONFIG=1
fi
cp -a /etc/blazepwifi "$BACKUP/" 2>/dev/null || true
PRESERVED_PORTAL="$BACKUP/blazepwifi/portal/portal.json"

echo "Installing BlazePwifi files..."
cp -a "$BASE/openwrt/rootfs/." /
rm -f /etc/uci-defaults/99-blazepwifi
if [ "$EXISTING_CONFIG" = 1 ]; then
  cp -a "$BACKUP/blazepwifi.config" /etc/config/blazepwifi
fi
if [ -s "$PRESERVED_PORTAL" ]; then
  mkdir -p /etc/blazepwifi/portal
  cp -a "$PRESERVED_PORTAL" /etc/blazepwifi/portal/portal.json
fi
chmod +x /etc/init.d/blazepwifi* /usr/sbin/blazepwifi-* /usr/sbin/blazepwifi-core /usr/lib/blazepwifi/*.sh /www/blazepwifi/cgi-bin/*
mkdir -p /etc/blazepwifi/state /etc/blazepwifi/portal /tmp/blazepwifi
chmod 700 /etc/blazepwifi /etc/blazepwifi/state /etc/blazepwifi/portal /tmp/blazepwifi
[ ! -f /etc/blazepwifi/portal/portal.json ] || chmod 600 /etc/blazepwifi/portal/portal.json

ensure_opt(){ key="$1"; value="$2"; uci -q get "blazepwifi.main.$key" >/dev/null 2>&1 || uci set "blazepwifi.main.$key=$value"; }
ensure_opt portal_port 8080
ensure_opt vendo_port 4455
ensure_opt admin_port 8443
ensure_opt coin_window 120
ensure_opt pulse_value_centavos 100
ensure_opt event_history 64
ensure_opt pause_max_seconds 0
ensure_opt walled_refresh_seconds 120
ensure_opt durable_sync 1
ensure_opt firewall_zone lan
ensure_opt capability_tier auto
ensure_opt management_if br-lan
ensure_opt hotspot_if br-lan
ensure_opt controller_if br-lan
ensure_opt rental_if br-lan
ensure_opt management_vlan 0
ensure_opt hotspot_vlan 0
ensure_opt controller_vlan 0
ensure_opt rental_vlan 0
ensure_opt gpio_chip gpiochip0
ensure_opt coin_line 0
ensure_opt relay_line 0
ensure_opt led_line 0
ensure_opt coin_active_low 1
ensure_opt relay_active_low 0
ensure_opt led_active_low 0
ensure_opt coin_debounce_ms 40
ensure_opt pulse_group_ms 400
ensure_opt auth_max_attempts 5
ensure_opt auth_global_max_attempts 30
ensure_opt auth_window_seconds 300
ensure_opt auth_lock_seconds 900
ensure_opt auth_idle_seconds 900
ensure_opt auth_absolute_seconds 28800
ensure_opt auth_kdf_rounds 2048
ensure_opt auth_bind_ip 1

randhex(){
  bytes="${1:-18}"
  out="$(hexdump -n "$bytes" -e '1/1 "%02x"' /dev/urandom 2>/dev/null || true)"
  [ "${#out}" -ge $((bytes*2)) ] || out="$(od -An -N "$bytes" -tx1 /dev/urandom 2>/dev/null | tr -d ' \n' || true)"
  [ "${#out}" -ge $((bytes*2)) ] || out="$(printf '%s|%s' "$(date +%s)" "$$" | sha256sum | awk '{print $1}')"
  printf '%s' "$out" | cut -c1-$((bytes*2))
}
OLD_ADMIN="$(uci -q get blazepwifi.main.admin_key || true)"
VENDO="$(uci -q get blazepwifi.main.vendo_key || true)"
[ "$VENDO" != CHANGE_ME ] && [ -n "$VENDO" ] || { VENDO="$(randhex 18)"; uci set blazepwifi.main.vendo_key="$VENDO"; }

BOOTSTRAP=""
if ! grep -q '^admin	' /etc/blazepwifi/state/admin-users.tsv 2>/dev/null; then
  if [ -n "$OLD_ADMIN" ] && [ "$OLD_ADMIN" != CHANGE_ME ]; then BOOTSTRAP="$OLD_ADMIN"; else BOOTSTRAP="$(randhex 12)"; fi
  BP_LIB=/usr/lib/blazepwifi/common.sh /usr/lib/blazepwifi/auth.sh --set-bootstrap admin admin "$BOOTSTRAP"
fi
uci -q delete blazepwifi.main.admin_key || true
uci commit blazepwifi

LAN_IP="$(uci -q get network.lan.ipaddr || true)"
[ -n "$LAN_IP" ] || LAN_IP=192.168.1.1
PORTAL="$(uci -q get blazepwifi.main.portal_port || echo 8080)"
VENDO_PORT="$(uci -q get blazepwifi.main.vendo_port || echo 4455)"
ADMIN_PORT="$(uci -q get blazepwifi.main.admin_port || echo 8443)"

for s in blazepwifi blazepwifi_vendo blazepwifi_admin; do uci -q delete "uhttpd.$s" || true; done

uci set uhttpd.blazepwifi='uhttpd'
uci add_list uhttpd.blazepwifi.listen_http="$LAN_IP:$PORTAL"
uci set uhttpd.blazepwifi.home='/www/blazepwifi'
uci set uhttpd.blazepwifi.cgi_prefix='/cgi-bin'
uci set uhttpd.blazepwifi.rfc1918_filter='0'
uci set uhttpd.blazepwifi.max_requests='32'
uci set uhttpd.blazepwifi.max_connections='128'

uci set uhttpd.blazepwifi_vendo='uhttpd'
uci add_list uhttpd.blazepwifi_vendo.listen_http="$LAN_IP:$VENDO_PORT"
uci set uhttpd.blazepwifi_vendo.home='/www/blazepwifi'
uci set uhttpd.blazepwifi_vendo.cgi_prefix='/cgi-bin'
uci set uhttpd.blazepwifi_vendo.rfc1918_filter='0'
uci set uhttpd.blazepwifi_vendo.max_requests='32'
uci set uhttpd.blazepwifi_vendo.max_connections='64'

uci set uhttpd.blazepwifi_admin='uhttpd'
uci add_list uhttpd.blazepwifi_admin.listen_https="$LAN_IP:$ADMIN_PORT"
uci set uhttpd.blazepwifi_admin.home='/www/blazepwifi'
uci set uhttpd.blazepwifi_admin.cgi_prefix='/cgi-bin'
uci set uhttpd.blazepwifi_admin.rfc1918_filter='0'
uci set uhttpd.blazepwifi_admin.cert='/etc/uhttpd.crt'
uci set uhttpd.blazepwifi_admin.key='/etc/uhttpd.key'
uci set uhttpd.blazepwifi_admin.max_requests='16'
uci set uhttpd.blazepwifi_admin.max_connections='32'

uci -q get uhttpd.defaults >/dev/null 2>&1 || uci set uhttpd.defaults='cert'
uci set uhttpd.defaults.days='1825'
uci set uhttpd.defaults.bits='2048'
uci set uhttpd.defaults.country='PH'
uci set uhttpd.defaults.commonname="$LAN_IP"
uci set uhttpd.defaults.organization='BlazePwifi'
uci commit uhttpd

FIREWALL_ZONE="$(uci -q get blazepwifi.main.firewall_zone || echo lan)"
for r in blazepwifi_portal blazepwifi_vendo blazepwifi_admin; do uci -q delete "firewall.$r" || true; done

uci set firewall.blazepwifi_portal='rule'
uci set firewall.blazepwifi_portal.name='Allow-BlazePwifi-Portal'
uci set firewall.blazepwifi_portal.src="$FIREWALL_ZONE"
uci set firewall.blazepwifi_portal.proto='tcp'
uci set firewall.blazepwifi_portal.dest_port="$PORTAL"
uci set firewall.blazepwifi_portal.target='ACCEPT'

uci set firewall.blazepwifi_vendo='rule'
uci set firewall.blazepwifi_vendo.name='Allow-BlazePwifi-Vendo'
uci set firewall.blazepwifi_vendo.src="$FIREWALL_ZONE"
uci set firewall.blazepwifi_vendo.proto='tcp'
uci set firewall.blazepwifi_vendo.dest_port="$VENDO_PORT"
uci set firewall.blazepwifi_vendo.target='ACCEPT'

uci set firewall.blazepwifi_admin='rule'
uci set firewall.blazepwifi_admin.name='Allow-BlazePwifi-Admin'
uci set firewall.blazepwifi_admin.src="$FIREWALL_ZONE"
uci set firewall.blazepwifi_admin.proto='tcp'
uci set firewall.blazepwifi_admin.dest_port="$ADMIN_PORT"
uci set firewall.blazepwifi_admin.target='ACCEPT'
uci commit firewall

/etc/init.d/firewall reload 2>/dev/null || true
/etc/init.d/uhttpd restart
/etc/init.d/blazepwifi enable
/etc/init.d/blazepwifi-remote-guard enable 2>/dev/null || true
/etc/init.d/blazepwifi-remote-admin enable 2>/dev/null || true
/etc/init.d/blazepwifi restart
sleep 2

nft list table inet blazepwifi >/dev/null || { echo "ERROR: nftables gate did not start. Restore from $BACKUP" >&2; exit 1; }
[ -s /etc/uhttpd.crt ] && [ -s /etc/uhttpd.key ] || { echo "ERROR: HTTPS certificate was not generated. Restore from $BACKUP" >&2; exit 1; }

echo
echo "BlazePwifi installed."
echo "Portal:   http://$LAN_IP:$PORTAL/"
echo "Admin:    https://$LAN_IP:$ADMIN_PORT/admin.html"
echo "ESP API:  http://$LAN_IP:$VENDO_PORT/cgi-bin/vendo"
echo "Admin username: admin"
if [ -n "$BOOTSTRAP" ]; then
  echo "Bootstrap admin password: $BOOTSTRAP"
  echo "IMPORTANT: sign in and replace this bootstrap password immediately."
else
  echo "Admin credentials: preserved from existing v0.3 authentication state."
fi
echo "Vendo key: $VENDO"
echo "Backup: $BACKUP"
echo "A browser warning for the local self-signed admin certificate is expected."
echo "Existing Vendo credentials are preserved during upgrades."
