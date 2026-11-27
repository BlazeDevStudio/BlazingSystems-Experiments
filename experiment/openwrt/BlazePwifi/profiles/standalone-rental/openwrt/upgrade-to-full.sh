#!/bin/sh
set -eu

[ "${1:-}" = "--full" ] || { echo "Usage: $0 --full" >&2; exit 2; }
[ "$(id -u)" = 0 ] || { echo "ERROR: run as root" >&2; exit 1; }

MARK=/etc/blazepwifi/RENTAL_STANDALONE
[ -f "$MARK" ] || { echo "ERROR: Rental Standalone marker not found." >&2; exit 1; }
FULL_DEFAULTS=/usr/share/blazepwifi/full-uci-defaults.sh
[ -x "$FULL_DEFAULTS" ] || { echo "ERROR: dormant full BlazePwifi defaults are missing; refusing partial conversion." >&2; exit 1; }

STAMP="$(date +%Y%m%d-%H%M%S)"
B="/root/blazepwifi-rental-standalone-backups/full-upgrade-$STAMP"
mkdir -p "$B"
for p in /etc/config/uhttpd /etc/config/firewall /etc/config/blazepwifi /etc/config/network /etc/config/wireless; do
  [ -f "$p" ] && cp -p "$p" "$B/" || true
done
cp -a /etc/blazepwifi/state "$B/state" 2>/dev/null || true

LAN_IP="$(uci -q get network.lan.ipaddr || true)"
[ -n "$LAN_IP" ] || LAN_IP=192.168.1.1

echo "WARNING: this converts Rental Standalone into FULL BlazePwifi."
echo
echo "Rental Standalone intentionally left your existing Internet/network interfaces alone."
echo "Full BlazePwifi will now activate its hotspot/captive-portal firewall ownership."
echo "Your current network, wireless and firewall configuration has been backed up to:"
echo "  $B"
echo
printf "Type UPGRADE to continue: "
read -r answer
[ "$answer" = UPGRADE ] || { echo "Cancelled."; exit 1; }

command -v nft >/dev/null 2>&1 || {
  if command -v apk >/dev/null 2>&1; then
    apk -U add nftables >/dev/null
  elif command -v opkg >/dev/null 2>&1; then
    opkg update >/dev/null
    opkg install nftables >/dev/null
  else
    echo "ERROR: cannot install nftables" >&2
    exit 1
  fi
}

# Choose the normal full-server listener defaults before running the preserved
# full first-boot logic. Existing rental accounts, device secrets and policies
# remain in /etc/blazepwifi/state.
uci set blazepwifi.main.edition='full'
uci set blazepwifi.main.enabled='1'
uci set blazepwifi.main.portal_port='8080'
uci set blazepwifi.main.admin_port='8443'
uci set blazepwifi.main.vendo_port='4455'
uci commit blazepwifi

# Remove only the Rental Standalone dedicated controller listener. The preserved
# full defaults will create the normal portal/admin/vendo listeners and firewall
# rules after this explicit confirmation.
uci -q delete uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1 || true
uci commit uhttpd >/dev/null 2>&1 || true

sh "$FULL_DEFAULTS"

# Preserve Android clients enrolled to http://LocalIP by keeping the lightweight
# /cgi-bin/rental compatibility alias on the router's existing web server.
WEB_ROOT="$(sed -n 's/^web_root=//p' "$MARK" | head -n1)"
CGI_DIR="$(sed -n 's/^cgi_dir=//p' "$MARK" | head -n1)"
[ -n "$WEB_ROOT" ] || WEB_ROOT="$(uci -q get uhttpd.main.home || echo /www)"
[ -n "$CGI_DIR" ] || CGI_DIR="$WEB_ROOT$(uci -q get uhttpd.main.cgi_prefix || echo /cgi-bin)"
mkdir -p "$CGI_DIR"
cp -p /www/blazepwifi/cgi-bin/rental "$CGI_DIR/rental"
chmod 755 "$CGI_DIR/rental"

# Standalone-only management aliases use admin_port=443, while the full admin is
# intentionally on 8443. Remove those stale aliases and turn /rental into a
# small compatibility redirect rather than leaving a broken console behind.
for f in blaze-rental-admin blaze-rental-login blaze-rental-session blaze-rental-logout blaze-rental-profile; do
  rm -f "$CGI_DIR/$f"
done
mkdir -p "$WEB_ROOT/rental"
cat > "$WEB_ROOT/rental/index.html" <<EOF
<!doctype html><meta charset="utf-8"><title>BlazePwifi</title>
<meta http-equiv="refresh" content="0;url=https://$LAN_IP:8443/admin.html">
<p>Rental Standalone was converted to full BlazePwifi.
<a href="https://$LAN_IP:8443/admin.html">Open full administration</a>.</p>
EOF

mv "$MARK" /etc/blazepwifi/RENTAL_STANDALONE.upgraded
cat > /etc/blazepwifi/FULL_CONVERSION_INFO <<EOF
converted_at=$(date +%s)
backup=$B
from=rental-standalone
EOF
chmod 600 /etc/blazepwifi/FULL_CONVERSION_INFO

/etc/init.d/uhttpd restart >/dev/null 2>&1 || true
/etc/init.d/blazepwifi enable
/etc/init.d/blazepwifi restart
sleep 2

if command -v nft >/dev/null 2>&1; then
  nft list table inet blazepwifi >/dev/null 2>&1 || {
    echo "ERROR: full hotspot gate did not start. Backup is at $B" >&2
    exit 1
  }
fi

echo
echo "Full BlazePwifi activated."
echo "Portal:             http://$LAN_IP:8080/"
echo "Full administration:https://$LAN_IP:8443/admin.html"
echo "Rental app alias:   http://$LAN_IP/cgi-bin/rental"
echo "Backup:             $B"
