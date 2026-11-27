#!/bin/sh
# v0.3 security/bootstrap verification retrigger
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if grep -Fq '"$" | sha256sum' "$ROOT/openwrt/rootfs/etc/uci-defaults/99-blazepwifi"; then
  echo 'uci-default entropy fallback must mix the process id' >&2
  exit 1
fi

for f in $(find "$ROOT" -type f \( -name '*.sh' -o -path '*/etc/init.d/*' -o -name 'api' -o -name 'admin' -o -name 'admin-login' -o -name 'admin-session' -o -name 'admin-logout' -o -name 'vendo' -o -name 'blazepwifi-core' \)); do
  first="$(head -n1 "$f" 2>/dev/null || true)"
  case "$first" in
    *bash*) bash -n "$f" ;;
    *) sh -n "$f" ;;
  esac
done

grep -q 'table inet blazepwifi' "$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
grep -q 'priority 10' "$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
grep -q 'walled_v4' "$ROOT/openwrt/rootfs/usr/sbin/blazepwifi-core"
grep -q 'bp_device_norm' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
grep -q 'flock -w 10 9' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
grep -q 'flock' "$ROOT/build/build-openwrt-image.sh"
grep -q 'flock' "$ROOT/installer/install.sh"
grep -q 'bp_tmp_suffix' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
grep -q 'tmp="$BP_STATE/.accounts.$(bp_tmp_suffix)"' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
grep -q "option durable_sync '1'" "$ROOT/openwrt/rootfs/etc/config/blazepwifi"
grep -q "option firewall_zone 'lan'" "$ROOT/openwrt/rootfs/etc/config/blazepwifi"
grep -q "Allow-BlazePwifi-Portal" "$ROOT/installer/install.sh"
grep -q 'coin target mismatch' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
grep -q 'vendo API requires dedicated port' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
grep -q 'admin API requires HTTPS' "$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -q 'listen_https' "$ROOT/installer/install.sh"
grep -q 'px5g-mbedtls' "$ROOT/build/build-openwrt-image.sh"
grep -q 'WiFi.softAP(setupApName.c_str(),cfg.apPass)' "$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
grep -q 'verifyWifi' "$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
grep -q 'verifyWifi' "$ROOT/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
grep -q 'bp_controller_json' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
grep -q 'bp_rental_apply_coin' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
grep -q '#include <LittleFS.h>' "$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
grep -q 'Recovered unacknowledged coin event from flash' "$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
grep -q 'BP_TARGET_DIR="$BP_STATE/targets"' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
grep -q '25.12' "$ROOT/installer/install.sh"

for x in \
  openwrt/rootfs/etc/init.d/blazepwifi \
  openwrt/rootfs/etc/init.d/blazepwifi-remote-admin \
  openwrt/rootfs/etc/init.d/blazepwifi-remote-guard \
  openwrt/rootfs/etc/uci-defaults/99-blazepwifi \
  openwrt/rootfs/usr/sbin/blazepwifi-core \
  openwrt/rootfs/usr/sbin/blazepwifi-remote-guard \
  openwrt/rootfs/usr/lib/blazepwifi/auth.sh \
  openwrt/rootfs/usr/lib/blazepwifi/controller.sh \
  openwrt/rootfs/usr/lib/blazepwifi/rental.sh \
  openwrt/rootfs/www/blazepwifi/cgi-bin/api \
  openwrt/rootfs/www/blazepwifi/cgi-bin/admin-login \
  openwrt/rootfs/www/blazepwifi/cgi-bin/admin-session \
  openwrt/rootfs/www/blazepwifi/cgi-bin/admin-logout \
  openwrt/rootfs/www/blazepwifi/cgi-bin/admin \
  openwrt/rootfs/www/blazepwifi/cgi-bin/vendo
do
  [ -x "$ROOT/$x" ] || { echo "required executable bit missing: $x" >&2; exit 1; }
done

if grep -q 'tmp="$BP_RUN/accounts' "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"; then
  echo 'persistent account temp files must stay on the state filesystem' >&2
  exit 1
fi

if grep -Rqs 'HTTP_X_BLAZE_ADMIN' "$ROOT/openwrt/rootfs"; then
  echo 'legacy admin-key header must not remain in v0.3 runtime' >&2
  exit 1
fi

if grep -Fq '"$" | sha256sum' "$ROOT/installer/install.sh"; then
  echo 'installer entropy fallback must mix the process id, not a literal dollar sign' >&2
  exit 1
fi

if grep -q '0.0.0.0:8443' "$ROOT/installer/install.sh"; then
  echo 'admin listener must not bind WAN wildcard' >&2
  exit 1
fi

echo 'BlazePwifi static checks passed'
