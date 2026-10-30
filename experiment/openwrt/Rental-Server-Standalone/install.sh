#!/bin/sh
# Rental Server Standalone installer v0.1.3 preview
# BLAZE_R281_RENTAL_HUB
set -eu
VERSION='0.1.3-preview.1'
MARKER='BLAZE_R281_RENTAL_HUB'
REPO_RAW='https://raw.githubusercontent.com/BlazingSystems/BlazingSystems-Experiments/main/experiment/openwrt/Rental-Server-Standalone'
MODE=install
PURGE=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --uninstall) MODE=uninstall ;;
    --purge) PURGE=1 ;;
    --force) FORCE=1 ;;
    -h|--help) echo "Usage: $0 [--force] | --uninstall [--purge]"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
[ "$(id -u)" = 0 ] || { echo 'ERROR: run as root.' >&2; exit 1; }

safe_remove(){
  f="$1"; [ -e "$f" ] || return 0
  if [ -f "$f" ] && grep -q "$MARKER" "$f" 2>/dev/null; then rm -f "$f"; else echo "KEEP: $f is not recognized as a Rental Server Standalone file."; fi
}
if [ "$MODE" = uninstall ]; then
  safe_remove /www/cgi-bin/rental
  safe_remove /www/cgi-bin/rental-admin
  if [ -f /www/rental/index.html ] && grep -q 'BlazeRental · R281 Test Hub' /www/rental/index.html 2>/dev/null; then rm -rf /www/rental; fi
  if [ "$PURGE" = 1 ]; then rm -rf /etc/blazepwifi-rental; else echo 'Rental state preserved at /etc/blazepwifi-rental.'; fi
  echo 'Uninstall complete. EasyMode/LuCI/OpenWrt configuration was not changed.'
  exit 0
fi

[ -f /etc/openwrt_release ] || { echo 'ERROR: OpenWrt not detected.' >&2; exit 1; }
. /etc/openwrt_release
BOARD="$(cat /tmp/sysinfo/board_name 2>/dev/null || true)"
case "$BOARD" in notion,r281) ;; *) [ "$FORCE" = 1 ] || { echo "ERROR: expected notion,r281; detected '${BOARD:-unknown}'." >&2; exit 1; };; esac
case "${DISTRIB_RELEASE:-}" in 24.10.*) ;; *) [ "$FORCE" = 1 ] || { echo "ERROR: intended for OpenWrt 24.10.x; detected '${DISTRIB_RELEASE:-unknown}'." >&2; exit 1; };; esac
command -v uci >/dev/null || { echo 'ERROR: uci missing.' >&2; exit 1; }
command -v sha256sum >/dev/null || { echo 'ERROR: sha256sum missing.' >&2; exit 1; }
HOME_DIR="$(uci -q get uhttpd.main.home || true)"
CGI_PREFIX="$(uci -q get uhttpd.main.cgi_prefix || true)"
[ "$HOME_DIR" = '/www' ] || { echo "ERROR: uHTTPd home is '$HOME_DIR'; refusing to modify it." >&2; exit 1; }
[ "$CGI_PREFIX" = '/cgi-bin' ] || { echo "ERROR: uHTTPd CGI prefix is '$CGI_PREFIX'; refusing to modify it." >&2; exit 1; }

if ! command -v openssl >/dev/null 2>&1; then
  [ "${BLAZE_NO_PACKAGE_INSTALL:-0}" != 1 ] || { echo 'ERROR: openssl required.' >&2; exit 1; }
  command -v opkg >/dev/null || { echo 'ERROR: openssl missing and opkg unavailable.' >&2; exit 1; }
  echo 'Installing only openssl-util for BlazeRental HMAC authentication.'
  opkg update >/dev/null && opkg install openssl-util >/dev/null
fi

for f in /www/cgi-bin/rental /www/cgi-bin/rental-admin; do
  if [ -e "$f" ] && ! grep -q "$MARKER" "$f" 2>/dev/null; then [ "$FORCE" = 1 ] || { echo "ERROR: $f belongs to another application." >&2; exit 1; }; fi
done
if [ -e /www/rental/index.html ] && ! grep -q 'BlazeRental · R281 Test Hub' /www/rental/index.html 2>/dev/null; then
  [ "$FORCE" = 1 ] || { echo 'ERROR: /www/rental belongs to another application.' >&2; exit 1; }
fi

admin_token_hex(){
  x="$(openssl rand -hex 24 2>/dev/null)" || x=''
  case "$x" in *[!0-9a-f]*) x='';; esac
  [ "${#x}" -eq 48 ] || x="$(hexdump -n 24 -e '1/1 "%02x"' /dev/urandom 2>/dev/null)" || x=''
  case "$x" in *[!0-9a-f]*) x='';; esac
  [ "${#x}" -eq 48 ] || x="$(od -An -N 24 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n')" || x=''
  case "$x" in *[!0-9a-f]* ) return 1;; esac
  [ "${#x}" -eq 48 ] || return 1
  printf '%s' "$x"
}
RENTAL_BASE=/etc/blazepwifi-rental
FRESH_STATE=1
if [ -e "$RENTAL_BASE" ] || [ -L "$RENTAL_BASE" ]; then
  FRESH_STATE=0
  [ -d "$RENTAL_BASE" ] && [ ! -L "$RENTAL_BASE" ] &&
    [ -d "$RENTAL_BASE/state" ] && [ ! -L "$RENTAL_BASE/state" ] || {
      echo 'ERROR: existing rental authority is incomplete or unsafe.' >&2; exit 1;
    }
  for f in devices.tsv enroll.tsv policy.tsv events.tsv; do
    [ -f "$RENTAL_BASE/state/$f" ] && [ ! -L "$RENTAL_BASE/state/$f" ] || {
      echo "ERROR: existing rental authority file $f missing or unsafe." >&2; exit 1;
    }
  done
fi
TOKEN_FILE=$RENTAL_BASE/admin.token
[ ! -L "$TOKEN_FILE" ] && { [ ! -e "$TOKEN_FILE" ] || [ -f "$TOKEN_FILE" ]; } || {
  echo 'ERROR: unsafe admin token path.' >&2; exit 1;
}
NEW_ADMIN_TOKEN=''
if [ "$FRESH_STATE" = 0 ] && [ ! -s "$TOKEN_FILE" ]; then
  echo 'ERROR: existing rental admin identity missing or empty.' >&2; exit 1;
fi
if [ "$FRESH_STATE" = 1 ]; then
  NEW_ADMIN_TOKEN="$(admin_token_hex)" || { echo 'ERROR: secure random bytes unavailable.' >&2; exit 1; }
fi

SELF_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || pwd)"
TMP="/tmp/rental-server-standalone.$$"
mkdir -p "$TMP/root/www/cgi-bin" "$TMP/root/www/rental"
fetch_or_copy(){
  rel="$1"; dst="$2"
  if [ -f "$SELF_DIR/$rel" ]; then cp "$SELF_DIR/$rel" "$dst"; return; fi
  command -v wget >/dev/null || { echo "ERROR: $rel not beside installer and wget unavailable." >&2; exit 1; }
  wget -qO "$dst" "$REPO_RAW/$rel" || { echo "ERROR: failed to download $rel" >&2; exit 1; }
}
fetch_or_copy root/www/cgi-bin/rental "$TMP/root/www/cgi-bin/rental"
fetch_or_copy root/www/cgi-bin/rental-admin "$TMP/root/www/cgi-bin/rental-admin"
fetch_or_copy root/www/rental/index.html "$TMP/root/www/rental/index.html"
echo '5e338fa1bc20bb8ec287d1e25e9bac65ee6d23ea45eebc79a7a6410d9e4e227a  root/www/cgi-bin/rental' > "$TMP/SHA256SUMS"
echo 'c95ceee486634e61d972bff6f60ab32851d48df652a90440ff5c3a53044fe3a3  root/www/cgi-bin/rental-admin' >> "$TMP/SHA256SUMS"
echo '64ec53a877845409efd03441de059f4a7e43d7a800c443b46593786c6e947d7b  root/www/rental/index.html' >> "$TMP/SHA256SUMS"
(cd "$TMP" && sha256sum -c SHA256SUMS >/dev/null) || { rm -rf "$TMP"; echo 'ERROR: payload checksum verification failed.' >&2; exit 1; }

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="/root/blazepwifi-rental-backups/$STAMP"
mkdir -p "$BACKUP" /www/rental /www/cgi-bin /etc/blazepwifi-rental/state
for f in /www/cgi-bin/rental /www/cgi-bin/rental-admin /www/rental/index.html; do [ -e "$f" ] && cp -p "$f" "$BACKUP/$(basename "$f")" || true; done
cp "$TMP/root/www/cgi-bin/rental" /www/cgi-bin/rental
cp "$TMP/root/www/cgi-bin/rental-admin" /www/cgi-bin/rental-admin
cp "$TMP/root/www/rental/index.html" /www/rental/index.html
chmod 755 /www/cgi-bin/rental /www/cgi-bin/rental-admin
chmod 644 /www/rental/index.html
chmod 700 /etc/blazepwifi-rental /etc/blazepwifi-rental/state
for f in devices.tsv enroll.tsv policy.tsv events.tsv; do
  if [ "$FRESH_STATE" = 1 ]; then : > "/etc/blazepwifi-rental/state/$f"; fi
  chmod 600 "/etc/blazepwifi-rental/state/$f"
done
if [ -n "$NEW_ADMIN_TOKEN" ]; then
  printf '%s\n' "$NEW_ADMIN_TOKEN" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
fi
rm -rf "$TMP"

TOKEN="$(cat /etc/blazepwifi-rental/admin.token)"
OUT="$(printf 'action=health' | REQUEST_METHOD=POST REMOTE_ADDR=127.0.0.1 HTTP_X_BLAZE_RENTAL_ADMIN="$TOKEN" /www/cgi-bin/rental-admin 2>/dev/null || true)"
printf '%s' "$OUT" | grep -q '"ok":true' || { echo 'ERROR: local API health test failed.' >&2; exit 1; }
LAN_IP="$(uci -q get network.lan.ipaddr || true)"; [ -n "$LAN_IP" ] || LAN_IP=192.168.1.1
cat > /etc/blazepwifi-rental/INSTALL-INFO <<EOF
Rental Server Standalone $VERSION
Dashboard: http://$LAN_IP/rental/
APK base URL: http://$LAN_IP
APK endpoint: http://$LAN_IP/cgi-bin/rental
EasyMode and LuCI/OpenWrt configuration were not changed.
EOF
chmod 600 /etc/blazepwifi-rental/INSTALL-INFO

echo
echo "Rental Server Standalone $VERSION installed."
echo "EasyMode:   http://$LAN_IP/"
echo "Admin/LuCI: http://$LAN_IP/admin"
echo "Rental:     http://$LAN_IP/rental/"
echo "APK URL:    http://$LAN_IP"
echo
echo 'Rental admin token:'
cat /etc/blazepwifi-rental/admin.token
echo
echo 'No network/firewall/wireless/uHTTPd/EasyMode/LuCI configuration was modified.'
