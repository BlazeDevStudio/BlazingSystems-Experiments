#!/bin/sh
# BlazePwifi R281 Rental profile uninstaller
set -eu
PURGE=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --purge) PURGE=1 ;;
    --force) FORCE=1 ;;
    -h|--help) echo "Usage: $0 [--purge] [--force]"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
[ "$(id -u)" = 0 ] || { echo "ERROR: run as root" >&2; exit 1; }
[ -f /etc/blazepwifi/R281_RENTAL_PROFILE ] || { echo "ERROR: R281 rental profile marker not found." >&2; exit 1; }
if [ -x /etc/init.d/blazepwifi ] && [ "$FORCE" != 1 ]; then
  echo "ERROR: full BlazePwifi service now exists; refusing to remove shared libraries. Use --force only if intentional." >&2
  exit 1
fi
uci -q delete uhttpd.blazepwifi_rental_vendo >/dev/null 2>&1 || true
uci commit uhttpd >/dev/null 2>&1 || true
/etc/init.d/uhttpd restart >/dev/null 2>&1 || true
rm -rf /www/rental
for f in rental vendo rental-admin rental-login rental-session rental-logout; do rm -f "/www/cgi-bin/$f"; done
rm -rf /usr/lib/blazepwifi
rm -f /etc/blazepwifi/R281_RENTAL_PROFILE
if [ "$PURGE" -eq 1 ]; then
  rm -rf /etc/blazepwifi /tmp/blazepwifi
  uci -q delete blazepwifi >/dev/null 2>&1 || true
  rm -f /etc/config/blazepwifi
  echo "Rental state and BlazePwifi rental configuration purged."
else
  echo "Rental state preserved under /etc/blazepwifi/state."
  echo "Use --purge only if you also want enrolled-device state removed."
fi
echo "EasyMode, network, firewall, wireless and modem configuration were not changed."
