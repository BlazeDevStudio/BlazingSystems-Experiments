#!/bin/sh
# BlazePwifi 0.3.0 - full R281 rental deployment profile installer
set -eu

PROFILE_VERSION='0.3.0-r281.1'
CORE_VERSION='0.3.0'
PAYLOAD_REF='31c85b357280f40c507efe29612555c43776122a'
RAW_BASE="https://raw.githubusercontent.com/BlazingSystems/BlazingSystems-Experiments/$PAYLOAD_REF/experiment/openwrt/BlazePwifi/profiles/r281-rental"
FORCE=0
NO_PKGS="${BLAZE_NO_PACKAGE_INSTALL:-0}"

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    -h|--help)
      echo "Usage: $0 [--force]"
      echo "Environment: BLAZE_NO_PACKAGE_INSTALL=1 to refuse dependency installation."
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

die(){ echo "ERROR: $*" >&2; exit 1; }
note(){ echo "==> $*"; }
randhex(){
  bytes="${1:-18}"
  out="$(hexdump -n "$bytes" -e '1/1 "%02x"' /dev/urandom 2>/dev/null || true)"
  [ "${#out}" -ge $((bytes*2)) ] || out="$(od -An -N "$bytes" -tx1 /dev/urandom 2>/dev/null | tr -d ' \n' || true)"
  [ "${#out}" -ge $((bytes*2)) ] || out="$(printf '%s|%s' "$(date +%s)" "$$" | sha256sum | awk '{print $1}')"
  printf '%s' "$out" | cut -c1-$((bytes*2))
}
ensure_uci(){
  key="$1"; value="$2"
  uci -q get "blazepwifi.main.$key" >/dev/null 2>&1 || uci set "blazepwifi.main.$key=$value"
}
install_dependencies(){
  need=0
  command -v openssl >/dev/null 2>&1 || need=1
  command -v flock >/dev/null 2>&1 || need=1
  [ "$need" -eq 0 ] && return 0
  [ "$NO_PKGS" != 1 ] || die "Required dependency missing (openssl/flock) and package installation is disabled."
  command -v opkg >/dev/null 2>&1 || die "opkg unavailable."
  avail="$(df -Pk /overlay 2>/dev/null | awk 'NR==2{print $4+0}')"
  [ "${avail:-0}" -ge 2048 ] || die "Less than 2 MB free overlay space; refusing package installation."
  note "Updating package index for required rental dependencies..."
  opkg update >/dev/null || die "opkg update failed."
  if ! command -v openssl >/dev/null 2>&1; then
    note "Installing openssl-util for BlazeRental HMAC authentication..."
    opkg install openssl-util >/dev/null || die "Unable to install openssl-util."
  fi
  if ! command -v flock >/dev/null 2>&1; then
    note "Installing flock for BlazePwifi session/accounting locks..."
    opkg install flock >/dev/null 2>&1 || opkg install util-linux-flock >/dev/null 2>&1 || die "Unable to install flock."
  fi
}

[ "$(id -u)" = 0 ] || die "Run as root."
[ -f /etc/openwrt_release ] || die "OpenWrt not detected."
. /etc/openwrt_release
BOARD="$(cat /tmp/sysinfo/board_name 2>/dev/null || true)"
case "$BOARD" in notion,r281) ;; *) [ "$FORCE" = 1 ] || die "Expected notion,r281; detected '${BOARD:-unknown}'.";; esac
case "${DISTRIB_RELEASE:-}" in 24.10.*) ;; *) [ "$FORCE" = 1 ] || die "Profile is validated for OpenWrt 24.10.x; detected '${DISTRIB_RELEASE:-unknown}'.";; esac
command -v uci >/dev/null 2>&1 || die "uci missing."
command -v wget >/dev/null 2>&1 || die "wget missing."
command -v sha256sum >/dev/null 2>&1 || die "sha256sum missing."
command -v hexdump >/dev/null 2>&1 || die "hexdump missing."

HOME_DIR="$(uci -q get uhttpd.main.home || true)"
CGI_PREFIX="$(uci -q get uhttpd.main.cgi_prefix || true)"
[ "$HOME_DIR" = /www ] || die "Existing uHTTPd main home is '$HOME_DIR', expected /www."
[ "$CGI_PREFIX" = /cgi-bin ] || die "Existing uHTTPd main CGI prefix is '$CGI_PREFIX', expected /cgi-bin."
uci show uhttpd.main 2>/dev/null | grep -q "listen_https.*:443" || die "Existing R281 uHTTPd main instance does not expose HTTPS :443; refusing insecure admin installation."

if [ -x /etc/init.d/blazepwifi ] && [ "$FORCE" != 1 ]; then
  die "A full BlazePwifi service is already installed. Use its native installer or rerun with --force only if you intentionally want the R281 rental profile."
fi

# Avoid stealing the controller port from an unrelated service.
if uci show uhttpd 2>/dev/null | grep "listen_http" | grep -q ":4455" && ! uci -q get uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1; then
  [ "$FORCE" = 1 ] || die "TCP 4455 is already configured by another uHTTPd instance."
fi

install_dependencies

TMP="/tmp/blazepwifi-r281-rental.$$"
rm -rf "$TMP"
mkdir -p "$TMP"
cat > "$TMP/SHA256SUMS" <<'SUMS'
f256635b44d4a63cc8a65586274d95c71f0fdcc6b5c304ea337dc58a8eca3400  root/usr/lib/blazepwifi/common.sh
9b4ae8bd253bb761dcf1f8e642d2419a1d5400dbbb8a2c70a9079c0ebae49c0f  root/usr/lib/blazepwifi/auth.sh
fa82cc621cca3195a4f64a3ac995565eff60bbf8ad93428f17a8616f4e5d46f3  root/usr/lib/blazepwifi/config.sh
07e02b266adb5bcb6871af6f230cd780b610ca087330fbfc5563355f728a8ff6  root/usr/lib/blazepwifi/rental.sh
5f6b64aa02335578c2cf7ffc568e12e6415df9f34d9599c7ff14b77326e6912d  root/usr/lib/blazepwifi/controller.sh
db192d00dada4c342fbe341002e4775324427c444ac312c2dd23cbf1d57124ff  root/www/cgi-bin/rental
6f5d448aa9da465c1ff53561aaad2954d03cba2bfb9c8fa2f7f8afa18003af57  root/www/cgi-bin/vendo
d95b8e28b5ed9657e94e558ccc28138a33063510fdf42775fe728da594a9e4a0  root/www/cgi-bin/rental-admin
aa5fe4aca10e0e81d33259fe566d11363984ae2d5557a13fc1a77e51702902aa  root/www/cgi-bin/rental-login
bf9819491093e97bf6f6f4fd5d1ea394ef8c6b2504625bc8f346f4ce1130aca6  root/www/cgi-bin/rental-session
7b9a6a3be75be9cb375e02121fa8f8adfd73ea9325e1d049cd1e371341bc33c4  root/www/cgi-bin/rental-logout
562d33d1acccc0c7a7416cb2fd4aff116406c8ce3ff569a031e8da8b9b732b75  root/www/rental/index.html
79ec86f82856005b1c887905cfccfcfbec3821ca61c7fd5a952faa5f778f791c  root/www/rental/vendor/qrcode.js
3a850fa5f08101db6f40676c2786e10bd2cd5fff7b12ffdf1e0c434d4e49d90c  root/www/rental/vendor/qrcode-LICENSE
SUMS

note "Downloading immutable BlazePwifi rental payload $PAYLOAD_REF..."
while read -r hash rel; do
  [ -n "$hash" ] || continue
  mkdir -p "$TMP/$(dirname "$rel")"
  wget -qO "$TMP/$rel" "$RAW_BASE/$rel" || { rm -rf "$TMP"; die "Failed to download $rel"; }
done < "$TMP/SHA256SUMS"

(cd "$TMP" && sha256sum -c SHA256SUMS) || { rm -rf "$TMP"; die "Payload checksum verification failed. Nothing was installed."; }

for f in   root/usr/lib/blazepwifi/common.sh   root/usr/lib/blazepwifi/auth.sh   root/usr/lib/blazepwifi/config.sh   root/usr/lib/blazepwifi/rental.sh   root/usr/lib/blazepwifi/controller.sh   root/www/cgi-bin/rental root/www/cgi-bin/vendo root/www/cgi-bin/rental-admin   root/www/cgi-bin/rental-login root/www/cgi-bin/rental-session root/www/cgi-bin/rental-logout
do
  sh -n "$TMP/$f" || { rm -rf "$TMP"; die "Shell syntax validation failed: $f"; }
done

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="/root/blazepwifi-r281-rental-backups/$STAMP"
mkdir -p "$BACKUP"
[ -f /etc/config/uhttpd ] && cp -p /etc/config/uhttpd "$BACKUP/uhttpd.before"
[ -f /etc/config/blazepwifi ] && cp -p /etc/config/blazepwifi "$BACKUP/blazepwifi.before"
[ -d /www/rental ] && cp -a /www/rental "$BACKUP/www-rental.before"
for f in rental vendo rental-admin rental-login rental-session rental-logout; do
  [ -f "/www/cgi-bin/$f" ] && cp -p "/www/cgi-bin/$f" "$BACKUP/cgi-$f.before"
done
[ -d /etc/blazepwifi ] && cp -a /etc/blazepwifi "$BACKUP/etc-blazepwifi.before"
[ -d /usr/lib/blazepwifi ] && cp -a /usr/lib/blazepwifi "$BACKUP/usr-lib-blazepwifi.before"

note "Installing shared BlazePwifi rental core..."
mkdir -p /usr/lib/blazepwifi /www/cgi-bin /www/rental/vendor /etc/blazepwifi/state /tmp/blazepwifi
chmod 700 /etc/blazepwifi /etc/blazepwifi/state /tmp/blazepwifi
cp "$TMP/root/usr/lib/blazepwifi/"*.sh /usr/lib/blazepwifi/
cp "$TMP/root/www/cgi-bin/"* /www/cgi-bin/
cp "$TMP/root/www/rental/index.html" /www/rental/index.html
cp "$TMP/root/www/rental/vendor/"* /www/rental/vendor/
chmod 755 /usr/lib/blazepwifi/*.sh /www/cgi-bin/rental /www/cgi-bin/vendo /www/cgi-bin/rental-admin /www/cgi-bin/rental-login /www/cgi-bin/rental-session /www/cgi-bin/rental-logout
chmod 644 /www/rental/index.html /www/rental/vendor/*

# Create only BlazePwifi's own rental configuration package. Do not modify
# network/firewall/wireless/blaze/EasyMode configuration.
uci -q get blazepwifi.main >/dev/null 2>&1 || uci set blazepwifi.main='blazepwifi'
ensure_uci enabled 1
ensure_uci capability_tier lite
ensure_uci rental_if br-lan
ensure_uci controller_if br-lan
ensure_uci rental_vlan 0
ensure_uci controller_vlan 0
ensure_uci rental_seconds_per_pulse 600
ensure_uci coin_window 120
ensure_uci vendo_port 4455
ensure_uci durable_sync 1
ensure_uci auth_max_attempts 5
ensure_uci auth_global_max_attempts 30
ensure_uci auth_window_seconds 300
ensure_uci auth_lock_seconds 900
ensure_uci auth_idle_seconds 900
ensure_uci auth_absolute_seconds 28800
ensure_uci auth_kdf_rounds 2048
ensure_uci auth_bind_ip 1
VKEY="$(uci -q get blazepwifi.main.vendo_key || true)"
[ -n "$VKEY" ] && [ "$VKEY" != CHANGE_ME ] || uci set "blazepwifi.main.vendo_key=$(randhex 18)"
uci commit blazepwifi || die "Failed to commit BlazePwifi rental configuration."

# Initialize real BlazePwifi state.
BP_STATE=/etc/blazepwifi/state BP_RUN=/tmp/blazepwifi BP_LIB=/usr/lib/blazepwifi/common.sh BP_AUTH_LIB=/usr/lib/blazepwifi/auth.sh BP_RENTAL_LIB=/usr/lib/blazepwifi/rental.sh   sh -c '. "$BP_LIB"; . "$BP_AUTH_LIB"; . "$BP_RENTAL_LIB"; bp_init_dirs; bp_auth_init; bp_rental_init' || die "Unable to initialize BlazePwifi rental state."

# Migrate the earlier standalone test hub only when the real state is empty.
OLD=/etc/blazepwifi-rental/state
NEW=/etc/blazepwifi/state
if [ -d "$OLD" ] && [ ! -s "$NEW/rental-devices.tsv" ] && [ -s "$OLD/devices.tsv" ]; then
  note "Migrating enrolled devices from the earlier R281 test hub..."
  cp "$OLD/devices.tsv" "$NEW/rental-devices.tsv"
  [ ! -f "$OLD/enroll.tsv" ] || cp "$OLD/enroll.tsv" "$NEW/rental-enroll.tsv"
  if [ -f "$OLD/policy.tsv" ]; then
    awk -F '\t' -v OFS='\t' '{if(NF==5) print $1,$2,$3,$4,$5,"-"; else print}' "$OLD/policy.tsv" > "$NEW/rental-policy.tsv"
  fi
  chmod 600 "$NEW"/rental-*.tsv 2>/dev/null || true
fi

# Create the real BlazePwifi bootstrap admin only if one does not exist.
BOOTSTRAP_CREATED=0
if ! grep -q "^admin$(printf '\t')" /etc/blazepwifi/state/admin-users.tsv 2>/dev/null; then
  BOOTSTRAP="$(randhex 12)"
  BP_LIB=/usr/lib/blazepwifi/common.sh /usr/lib/blazepwifi/auth.sh --set-bootstrap admin admin "$BOOTSTRAP" || die "Unable to create BlazePwifi rental administrator."
  printf '%s\n' "$BOOTSTRAP" > /etc/blazepwifi/INITIAL_ADMIN_PASSWORD
  chmod 600 /etc/blazepwifi/INITIAL_ADMIN_PASSWORD
  BOOTSTRAP_CREATED=1
fi

LAN_IP="$(uci -q get network.lan.ipaddr || true)"
[ -n "$LAN_IP" ] || LAN_IP=192.168.1.1

# Related rental feature only: dedicated ESP controller listener.
uci -q delete uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1 || true
uci set uhttpd.blazepwifi_rental_vendo='uhttpd'
uci add_list "uhttpd.blazepwifi_rental_vendo.listen_http=$LAN_IP:4455"
uci set uhttpd.blazepwifi_rental_vendo.home='/www'
uci set uhttpd.blazepwifi_rental_vendo.cgi_prefix='/cgi-bin'
uci set uhttpd.blazepwifi_rental_vendo.rfc1918_filter='0'
uci commit uhttpd || die "Failed to add rental controller listener."

if ! /etc/init.d/uhttpd restart >/dev/null 2>&1; then
  note "uHTTPd restart failed; rolling back its configuration."
  [ -f "$BACKUP/uhttpd.before" ] && cp "$BACKUP/uhttpd.before" /etc/config/uhttpd
  /etc/init.d/uhttpd restart >/dev/null 2>&1 || true
  die "uHTTPd could not start. Rental files remain backed up at $BACKUP."
fi

# Local execution smoke tests.
OUT="$(printf 'action=status' | REQUEST_METHOD=POST SERVER_PORT=80 REMOTE_ADDR=127.0.0.1 sh /www/cgi-bin/rental 2>/dev/null || true)"
printf '%s' "$OUT" | grep -q '"error":"missing authentication"' || die "BlazeRental app API smoke test failed."
OUT="$(printf 'action=status' | REQUEST_METHOD=POST SERVER_PORT=443 HTTPS=on REMOTE_ADDR=127.0.0.1 sh /www/cgi-bin/rental-admin 2>/dev/null || true)"
printf '%s' "$OUT" | grep -q '"error":"unauthorized"' || die "Rental admin API smoke test failed."

cat > /etc/blazepwifi/R281_RENTAL_PROFILE <<EOF
profile_version=$PROFILE_VERSION
core_version=$CORE_VERSION
payload_ref=$PAYLOAD_REF
installed_at=$(date +%s)
backup=$BACKUP
EOF
chmod 600 /etc/blazepwifi/R281_RENTAL_PROFILE
rm -rf "$TMP"

echo
echo "BlazePwifi full R281 Rental profile $PROFILE_VERSION installed successfully."
echo
echo "Existing services:"
echo "  EasyMode:       http://$LAN_IP/"
echo "  R281 Admin:     http://$LAN_IP/admin"
echo
echo "BlazePwifi Rental:"
echo "  Management:     https://$LAN_IP/rental/"
echo "  Android server: http://$LAN_IP"
echo "  Android API:    http://$LAN_IP/cgi-bin/rental"
echo "  Coin controller:http://$LAN_IP:4455/cgi-bin/vendo"
echo
echo "Username: admin"
if [ "$BOOTSTRAP_CREATED" -eq 1 ]; then
  echo "Initial password: $BOOTSTRAP"
  echo "You will be required to replace this bootstrap password after login."
else
  echo "Existing BlazePwifi administrator password preserved."
fi
echo
echo "Backup: $BACKUP"
echo "No network, firewall, Wi-Fi, modem or EasyMode configuration was modified."
