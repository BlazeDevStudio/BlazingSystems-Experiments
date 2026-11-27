#!/bin/sh
set -eu

PROFILE_VERSION="0.5.0-rental-rc.3"
TARGET="auto"
FORCE=0
PREINSTALLED=0
SELF="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

for arg in "$@"; do
  case "$arg" in
    --target=*) TARGET="${arg#*=}" ;;
    --force) FORCE=1 ;;
    --preinstalled) PREINSTALLED=1 ;;
    -h|--help)
      echo "Usage: $0 [--target=auto|r281|ew1200g-pro|generic] [--force] [--preinstalled]"
      exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

die(){ echo "ERROR: $*" >&2; exit 1; }
note(){ echo "==> $*"; }

[ "$(id -u)" = 0 ] || die "Run as root."
[ -f /etc/openwrt_release ] || die "OpenWrt is required."
. /etc/openwrt_release
case "${DISTRIB_RELEASE:-}" in
  24.10.*|25.12.*) ;;
  *) [ "$FORCE" = 1 ] || die "Validated for OpenWrt 24.10.x/25.12.x; detected ${DISTRIB_RELEASE:-unknown}." ;;
esac

ROOTFS=""
if [ "$PREINSTALLED" -eq 0 ]; then
  for p in "$SELF/rootfs" "$SELF/../../../openwrt/rootfs" "$SELF/../../../../openwrt/rootfs"; do
    [ -d "$p/usr/lib/blazepwifi" ] && { ROOTFS="$p"; break; }
  done
  [ -n "$ROOTFS" ] || die "Full BlazePwifi rootfs payload not found beside installer."
fi

BOARD="$(cat /tmp/sysinfo/board_name 2>/dev/null || true)"
MODEL="$(cat /tmp/sysinfo/model 2>/dev/null || true)"
detect_target(){
  case "$BOARD $MODEL" in
    *notion,r281*|*R281*) echo r281 ;;
    *ruijie*ew1200g*|*RG-EW1200G*) echo ew1200g-pro ;;
    *) echo generic ;;
  esac
}
DETECTED="$(detect_target)"
[ "$TARGET" = auto ] && TARGET="$DETECTED"
case "$TARGET" in r281|ew1200g-pro|generic) ;; *) die "Invalid target '$TARGET'.";; esac
if [ "$TARGET" != generic ] && [ "$TARGET" != "$DETECTED" ] && [ "$FORCE" != 1 ]; then
  die "Target '$TARGET' does not match detected '$DETECTED' ($BOARD / $MODEL)."
fi

command -v uci >/dev/null 2>&1 || die "UCI missing."
FREE_KB="$(df -Pk /overlay 2>/dev/null | awk 'NR==2{print $4+0}')"
[ "${FREE_KB:-0}" -ge 1800 ] || [ "$FORCE" = 1 ] || die "Need at least 1.8 MB free overlay; found ${FREE_KB:-0} KB."

if ! command -v uhttpd >/dev/null 2>&1 || ! command -v openssl >/dev/null 2>&1 || ! command -v flock >/dev/null 2>&1; then
  note "Installing required web/crypto/locking packages..."
  if command -v apk >/dev/null 2>&1; then
    apk -U add uhttpd px5g-mbedtls openssl-util flock >/dev/null || die "Dependency installation failed."
  elif command -v opkg >/dev/null 2>&1; then
    opkg update >/dev/null || die "Package index update failed."
    command -v uhttpd >/dev/null 2>&1 || opkg install uhttpd >/dev/null || die "uhttpd install failed."
    command -v openssl >/dev/null 2>&1 || opkg install openssl-util >/dev/null || die "openssl-util install failed."
    command -v flock >/dev/null 2>&1 || { opkg install flock >/dev/null 2>&1 || opkg install util-linux-flock >/dev/null 2>&1 || die "flock install failed."; }
    [ -s /etc/uhttpd.crt ] || { opkg install px5g-mbedtls >/dev/null 2>&1 || opkg install px5g-wolfssl >/dev/null 2>&1 || true; }
  else
    die "No supported package manager found."
  fi
fi

WEB_ROOT="$(uci -q get uhttpd.main.home || true)"
CGI_PREFIX="$(uci -q get uhttpd.main.cgi_prefix || true)"
[ -n "$WEB_ROOT" ] || WEB_ROOT=/www
[ -n "$CGI_PREFIX" ] || CGI_PREFIX=/cgi-bin
case "$WEB_ROOT" in /*) ;; *) die "Unsupported uHTTPd document root '$WEB_ROOT'.";; esac
case "$CGI_PREFIX" in /*) ;; *) die "Unsupported CGI prefix '$CGI_PREFIX'.";; esac
CGI_DIR="$WEB_ROOT$CGI_PREFIX"

if [ -x /etc/init.d/blazepwifi ] && [ "$(uci -q get blazepwifi.main.edition || true)" = full ] && [ "$FORCE" != 1 ]; then
  die "Full BlazePwifi is already active. Rental Standalone is not an in-place downgrade."
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="/root/blazepwifi-rental-standalone-backups/$STAMP"
mkdir -p "$BACKUP/cgi"
for p in /etc/config/uhttpd /etc/config/blazepwifi; do [ -f "$p" ] && cp -p "$p" "$BACKUP/" || true; done
[ -d /etc/blazepwifi ] && cp -a /etc/blazepwifi "$BACKUP/etc-blazepwifi" || true
[ -d /usr/lib/blazepwifi ] && cp -a /usr/lib/blazepwifi "$BACKUP/usr-lib-blazepwifi" || true
[ -d "$WEB_ROOT/rental" ] && cp -a "$WEB_ROOT/rental" "$BACKUP/web-rental" || true
for f in rental blaze-rental-admin blaze-rental-login blaze-rental-session blaze-rental-logout blaze-rental-profile; do
  [ -f "$CGI_DIR/$f" ] && cp -p "$CGI_DIR/$f" "$BACKUP/cgi/$f" || true
done

if [ "$PREINSTALLED" -eq 0 ]; then
  note "Installing complete BlazePwifi v0.5 payload; hotspot core remains dormant..."
  EXISTING_CFG=0
  [ -f /etc/config/blazepwifi ] && { EXISTING_CFG=1; cp -p /etc/config/blazepwifi "$BACKUP/blazepwifi.original"; }
  cp -a "$ROOTFS/." /
  # Preserve the full-server defaults under a dormant, non-uci-defaults path.
  # Rental Standalone must never execute them automatically because they create
  # BlazePwifi firewall/listener ownership. The explicit --full conversion runs
  # this saved copy after operator confirmation.
  if [ -f /etc/uci-defaults/99-blazepwifi ]; then
    mkdir -p /usr/share/blazepwifi
    cp -p /etc/uci-defaults/99-blazepwifi /usr/share/blazepwifi/full-uci-defaults.sh
    chmod 755 /usr/share/blazepwifi/full-uci-defaults.sh
    rm -f /etc/uci-defaults/99-blazepwifi
  fi
  [ "$EXISTING_CFG" -eq 0 ] || cp -p "$BACKUP/blazepwifi.original" /etc/config/blazepwifi
fi

if [ -f /etc/uci-defaults/99-blazepwifi ]; then
  mkdir -p /usr/share/blazepwifi
  [ -f /usr/share/blazepwifi/full-uci-defaults.sh ] || cp -p /etc/uci-defaults/99-blazepwifi /usr/share/blazepwifi/full-uci-defaults.sh
  chmod 755 /usr/share/blazepwifi/full-uci-defaults.sh
  rm -f /etc/uci-defaults/99-blazepwifi
fi

chmod +x /etc/init.d/blazepwifi /usr/sbin/blazepwifi-core /usr/lib/blazepwifi/*.sh /www/blazepwifi/cgi-bin/* 2>/dev/null || true
/etc/init.d/blazepwifi stop >/dev/null 2>&1 || true
/etc/init.d/blazepwifi disable >/dev/null 2>&1 || true

mkdir -p /etc/blazepwifi/state /tmp/blazepwifi "$CGI_DIR" "$WEB_ROOT/rental/vendor"
chmod 700 /etc/blazepwifi /etc/blazepwifi/state /tmp/blazepwifi

cp -p /www/blazepwifi/cgi-bin/rental "$CGI_DIR/rental"
cp -p /www/blazepwifi/cgi-bin/admin "$CGI_DIR/blaze-rental-admin"
cp -p /www/blazepwifi/cgi-bin/admin-login "$CGI_DIR/blaze-rental-login"
cp -p /www/blazepwifi/cgi-bin/admin-session "$CGI_DIR/blaze-rental-session"
cp -p /www/blazepwifi/cgi-bin/admin-logout "$CGI_DIR/blaze-rental-logout"
cp -p "$SELF/rental-profile" "$CGI_DIR/blaze-rental-profile"
cp -p "$SELF/rental-standalone.html" "$WEB_ROOT/rental/index.html"
cp -p /www/blazepwifi/vendor/qrcode/qrcode.js "$WEB_ROOT/rental/vendor/qrcode.js"
cp -p /www/blazepwifi/vendor/qrcode/LICENSE "$WEB_ROOT/rental/vendor/qrcode-LICENSE"
chmod 755 "$CGI_DIR/rental" "$CGI_DIR"/blaze-rental-*
chmod 644 "$WEB_ROOT/rental/index.html" "$WEB_ROOT/rental/vendor/"*

ensure(){ k="$1"; v="$2"; uci -q get "blazepwifi.main.$k" >/dev/null 2>&1 || uci set "blazepwifi.main.$k=$v"; }
uci -q get blazepwifi.main >/dev/null 2>&1 || uci set blazepwifi.main='core'
uci set blazepwifi.main.edition='rental-standalone'
uci set blazepwifi.main.edition_version="$PROFILE_VERSION"
uci set blazepwifi.main.full_upgrade_available='1'
uci set blazepwifi.main.enabled='0'
ensure capability_tier auto
ensure rental_if br-lan
ensure controller_if br-lan
ensure rental_seconds_per_pulse 600
ensure coin_window 120
uci set blazepwifi.main.portal_port='8080'
uci set blazepwifi.main.admin_port='443'
uci set blazepwifi.main.vendo_port='4455'
ensure durable_sync 1
ensure auth_max_attempts 5
ensure auth_global_max_attempts 30
ensure auth_window_seconds 300
ensure auth_lock_seconds 900
ensure auth_idle_seconds 900
ensure auth_absolute_seconds 28800
ensure auth_kdf_rounds 2048
ensure auth_bind_ip 1

randhex(){
  n="${1:-18}"
  x="$(hexdump -n "$n" -e '1/1 "%02x"' /dev/urandom 2>/dev/null || true)"
  [ "${#x}" -ge $((n*2)) ] || x="$(od -An -N "$n" -tx1 /dev/urandom 2>/dev/null | tr -d ' \n' || true)"
  [ "${#x}" -ge $((n*2)) ] || x="$(printf '%s|%s' "$(date +%s)" "$$" | sha256sum | awk '{print $1}')"
  printf '%s' "$x" | cut -c1-$((n*2))
}
KEY="$(uci -q get blazepwifi.main.vendo_key || true)"
[ -n "$KEY" ] && [ "$KEY" != CHANGE_ME ] || uci set "blazepwifi.main.vendo_key=$(randhex 18)"
uci commit blazepwifi

BP_LIB=/usr/lib/blazepwifi/common.sh BP_AUTH_LIB=/usr/lib/blazepwifi/auth.sh BP_RENTAL_LIB=/usr/lib/blazepwifi/rental.sh BP_RENTAL_POLICY_LIB=/usr/lib/blazepwifi/rental_policy.sh \
  sh -c '. "$BP_LIB"; . "$BP_AUTH_LIB"; . "$BP_RENTAL_LIB"; . "$BP_RENTAL_POLICY_LIB"; bp_init_dirs; bp_auth_init; bp_rental_init; bp_rental_policy_v2_init' \
  || die "Unable to initialize rental state."

BOOT=""
if ! grep -q "^admin$(printf '\t')" /etc/blazepwifi/state/admin-users.tsv 2>/dev/null; then
  BOOT="$(randhex 12)"
  BP_LIB=/usr/lib/blazepwifi/common.sh /usr/lib/blazepwifi/auth.sh --set-bootstrap admin admin "$BOOT" || die "Unable to create administrator."
  printf '%s\n' "$BOOT" > /etc/blazepwifi/INITIAL_ADMIN_PASSWORD
  chmod 600 /etc/blazepwifi/INITIAL_ADMIN_PASSWORD
fi

LAN_IP="$(uci -q get network.lan.ipaddr || true)"
[ -n "$LAN_IP" ] || LAN_IP="$(ip -4 addr show 2>/dev/null | awk '/inet / && $2 !~ /^127\./ {sub(/\/.*/,"",$2);print $2;exit}')"
[ -n "$LAN_IP" ] || LAN_IP=192.168.1.1

if ! uci show uhttpd.main 2>/dev/null | grep -q "listen_https.*:443"; then
  uci add_list uhttpd.main.listen_https='0.0.0.0:443'
fi
uci set uhttpd.main.cert='/etc/uhttpd.crt'
uci set uhttpd.main.key='/etc/uhttpd.key'

uci -q delete uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1 || true
uci set uhttpd.blazepwifi_rental_vendo='uhttpd'
uci add_list "uhttpd.blazepwifi_rental_vendo.listen_http=$LAN_IP:4455"
uci set uhttpd.blazepwifi_rental_vendo.home='/www/blazepwifi'
uci set uhttpd.blazepwifi_rental_vendo.cgi_prefix='/cgi-bin'
uci set uhttpd.blazepwifi_rental_vendo.rfc1918_filter='0'
uci set uhttpd.blazepwifi_rental_vendo.max_requests='24'
uci set uhttpd.blazepwifi_rental_vendo.max_connections='64'

uci -q get uhttpd.defaults >/dev/null 2>&1 || uci set uhttpd.defaults='cert'
uci set uhttpd.defaults.days='1825'
uci set uhttpd.defaults.bits='2048'
uci set uhttpd.defaults.country='PH'
uci set uhttpd.defaults.commonname="$LAN_IP"
uci set uhttpd.defaults.organization='BlazePwifi Rental'
uci commit uhttpd

cp -p "$SELF/upgrade-to-full.sh" /usr/sbin/blazepwifi-rental-upgrade
chmod 755 /usr/sbin/blazepwifi-rental-upgrade
cat > /etc/blazepwifi/RENTAL_STANDALONE <<EOF
profile=$PROFILE_VERSION
target=$TARGET
board=$BOARD
model=$MODEL
web_root=$WEB_ROOT
cgi_dir=$CGI_DIR
backup=$BACKUP
installed_at=$(date +%s)
EOF
chmod 600 /etc/blazepwifi/RENTAL_STANDALONE

/etc/init.d/uhttpd restart >/dev/null 2>&1 || {
  [ -f "$BACKUP/uhttpd" ] && cp -p "$BACKUP/uhttpd" /etc/config/uhttpd || true
  /etc/init.d/uhttpd restart >/dev/null 2>&1 || true
  die "uHTTPd failed; configuration rolled back where possible."
}

OUT="$(printf 'action=status' | REQUEST_METHOD=POST SERVER_PORT=80 REMOTE_ADDR=127.0.0.1 sh "$CGI_DIR/rental" 2>/dev/null || true)"
printf '%s' "$OUT" | grep -q '"error":"missing authentication"' || die "BlazeRental API smoke test failed."

echo
echo "BlazePwifi Rental Standalone $PROFILE_VERSION installed."
echo "Target:            $TARGET ($BOARD / $MODEL)"
echo "Rental console:    https://$LAN_IP/rental/"
echo "Android server:    http://$LAN_IP"
echo "Android API:       http://$LAN_IP/cgi-bin/rental"
echo "Remote coin API:   http://$LAN_IP:4455/cgi-bin/vendo"
echo "Full server core:  installed but DISABLED"
echo "Full conversion:   /usr/sbin/blazepwifi-rental-upgrade --full"
echo "Backup:            $BACKUP"
echo "Admin username:    admin"
[ -n "$BOOT" ] && echo "Bootstrap password: $BOOT"
echo
echo "Existing root/admin UI preserved."
echo "No network, wireless or firewall UCI package was modified."
