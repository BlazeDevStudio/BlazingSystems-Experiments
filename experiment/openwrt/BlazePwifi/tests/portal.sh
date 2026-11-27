#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/portal"

LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/portal.sh"
DEFAULT="$ROOT/openwrt/rootfs/etc/blazepwifi/portal/portal.json"
INDEX="$ROOT/openwrt/rootfs/www/blazepwifi/index.html"
EDITOR="$ROOT/openwrt/rootfs/www/blazepwifi/portal-editor.html"
API="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/api"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"

[ -x "$LIB" ] || { echo "missing portal.sh" >&2; exit 1; }
[ -f "$DEFAULT" ] || { echo "missing portal.json" >&2; exit 1; }
[ -f "$EDITOR" ] || { echo "missing portal editor" >&2; exit 1; }

cp "$DEFAULT" "$T/portal/portal.json"
export BP_PORTAL_DIR="$T/portal" BP_PORTAL_FILE="$T/portal/portal.json"
. "$LIB"

[ "$(bp_portal_get brand)" = "BlazePwifi" ]
bp_portal_validate accent '#7c5cff'
bp_portal_validate show_details 1
bp_portal_validate brand 'Family Hotspot'
! bp_portal_validate accent red
! bp_portal_validate show_details yes
! bp_portal_validate brand '<script>alert(1)</script>'
! bp_portal_validate brand 'bad"quote'

bp_portal_set brand 'Family Hotspot'
[ "$(bp_portal_get brand)" = "Family Hotspot" ]
grep -q '"brand": "Family Hotspot"' "$BP_PORTAL_FILE"

grep -q "action.*portal_config\|portal_config)" "$API"
grep -q 'portal_get)' "$ADMIN"
grep -q 'portal_set)' "$ADMIN"

grep -q 'Insert Coin' "$INDEX"
grep -q 'Buy Time' "$INDEX"
grep -q 'Voucher' "$INDEX"
grep -q 'id="network-details"' "$INDEX"
grep -q 'blazePreview' "$INDEX"
grep -q 'portal-editor' "$ROOT/openwrt/rootfs/www/blazepwifi/admin.html"

hero_line="$(grep -n 'id="hero-actions"' "$INDEX" | head -n1 | cut -d: -f1)"
details_line="$(grep -n 'id="network-details"' "$INDEX" | head -n1 | cut -d: -f1)"
[ -n "$hero_line" ] && [ -n "$details_line" ] && [ "$hero_line" -lt "$details_line" ]

# Public portal configuration must be available before device identity checks.
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.lan_if') echo br-lan;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/ip" <<'IP'
#!/bin/sh
exit 0
IP
chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_PORTAL_LIB="$LIB"
export REQUEST_METHOD=POST REMOTE_ADDR=10.0.0.2
OUT="$(printf 'action=portal_config' | sh "$API")"
echo "$OUT" | grep -q '"brand":"Family Hotspot"'
! echo "$OUT" | grep -q 'missing or invalid device token'

echo "BlazePwifi v0.3 portal checks passed"
