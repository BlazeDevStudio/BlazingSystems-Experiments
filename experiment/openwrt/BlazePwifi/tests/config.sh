#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/uci.db" <<'DB'
blazepwifi.main.admin_port=8443
blazepwifi.main.portal_port=8080
blazepwifi.main.vendo_port=4455
blazepwifi.main.capability_tier=auto
blazepwifi.main.lan_if=br-lan
blazepwifi.main.management_if=br-lan
blazepwifi.main.hotspot_if=br-lan
blazepwifi.main.controller_if=br-lan
blazepwifi.main.rental_if=br-lan
blazepwifi.main.hotspot_vlan=0
blazepwifi.main.management_vlan=0
blazepwifi.main.controller_vlan=0
blazepwifi.main.rental_vlan=0
blazepwifi.main.firewall_zone=lan
blazepwifi.main.auth_idle_seconds=900
blazepwifi.main.auth_absolute_seconds=28800
blazepwifi.main.auth_bind_ip=1
blazepwifi.main.auth_kdf_rounds=8
blazepwifi.main.durable_sync=0
DB

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
DB="${TEST_UCI_DB:?}"
[ "$1" = "-q" ] && shift
cmd="$1"; shift
case "$cmd" in
 get)
   key="$1"
   sed -n "s#^$key=##p" "$DB" | tail -n1
   ;;
 set)
   kv="$1"; key="${kv%%=*}"; val="${kv#*=}"
   tmp="$DB.tmp"
   awk -F= -v k="$key" '$1!=k {print}' "$DB" > "$tmp"
   printf '%s=%s\n' "$key" "$val" >> "$tmp"
   mv "$tmp" "$DB"
   ;;
 delete)
   key="$1"; tmp="$DB.tmp"; awk -F= -v k="$key" '$1!=k {print}' "$DB" > "$tmp"; mv "$tmp" "$DB"
   ;;
 commit) exit 0 ;;
 *) exit 1 ;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" TEST_UCI_DB="$T/uci.db"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_CONFIG_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export BP_MEMBER_MIGRATION_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member_migration.sh"
export BP_CONSOLE_OPS_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh"
export BP_REMOTE_APPLY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/remote_apply.sh"
export BP_AUTH_NOW=2000000000 SERVER_PORT=8443 REMOTE_ADDR=10.0.0.9

CONFIG="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
LOGIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-login"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
[ -x "$CONFIG" ] || { echo "missing executable config.sh" >&2; exit 1; }

. "$BP_LIB"
. "$CONFIG"
bp_config_validate admin_port 9443
! bp_config_validate admin_port 70000
bp_config_validate capability_tier full
! bp_config_validate capability_tier giant
bp_config_validate hotspot_vlan 13
bp_config_validate hotspot_vlan 0
! bp_config_validate hotspot_vlan 4095
bp_config_validate management_if br-mgmt.13
! bp_config_validate management_if 'bad interface!'

bp_config_set admin_port 9443
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]

export BP_CONFIG_APPLY_HOOK=false
! bp_config_set admin_port 9555
[ "$(uci -q get blazepwifi.main.admin_port)" = 9443 ]
unset BP_CONFIG_APPLY_HOOK
export SERVER_PORT=9443

. "$BP_AUTH_LIB"
bp_auth_init
sh "$BP_AUTH_LIB" --set-password admin admin 'Config-Admin-123!'
sh "$BP_AUTH_LIB" --set-password viewer viewer 'Config-Viewer-123!'

AOUT="$(printf 'username=admin&password=Config-Admin-123!' | REQUEST_METHOD=POST sh "$LOGIN")"
ACOOKIE="$(printf '%s\n' "$AOUT" | sed -n 's/^Set-Cookie: \(blaze_admin=[^;]*\).*/\1/p' | tr -d '\r')"
ACSRF="$(printf '%s' "$AOUT" | sed -n 's/.*"csrf":"\([^"]*\)".*/\1/p')"
VOUT="$(printf 'username=viewer&password=Config-Viewer-123!' | REQUEST_METHOD=POST sh "$LOGIN")"
VCOOKIE="$(printf '%s\n' "$VOUT" | sed -n 's/^Set-Cookie: \(blaze_admin=[^;]*\).*/\1/p' | tr -d '\r')"

OUT="$(printf 'action=config_get&key=admin_port' | HTTP_COOKIE="$VCOOKIE" REQUEST_METHOD=POST sh "$ADMIN")"
echo "$OUT" | grep -q '"key":"admin_port"'
echo "$OUT" | grep -q '"value":"9443"'

OUT="$(printf 'action=config_set&key=admin_port&value=9555' | HTTP_COOKIE="$VCOOKIE" HTTP_X_BLAZE_CSRF=x REQUEST_METHOD=POST sh "$ADMIN")"
echo "$OUT" | grep -q 'insufficient role'

OUT="$(printf 'action=config_set&key=admin_port&value=9555' | HTTP_COOKIE="$ACOOKIE" HTTP_X_BLAZE_CSRF=wrong REQUEST_METHOD=POST sh "$ADMIN")"
echo "$OUT" | grep -q 'csrf'

OUT="$(printf 'action=config_set&key=admin_port&value=9555' | HTTP_COOKIE="$ACOOKIE" HTTP_X_BLAZE_CSRF="$ACSRF" REQUEST_METHOD=POST sh "$ADMIN")"
echo "$OUT" | grep -q '"ok":true'
[ "$(uci -q get blazepwifi.main.admin_port)" = 9555 ]
grep -q 'config_change' "$T/state/audit.tsv"

echo "BlazePwifi v0.3 config checks passed"
