#!/bin/sh
# v0.3 foundation compatibility gate retained for v0.4+
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

case "$(cat "$ROOT/VERSION")" in
  0.3.0|0.4.0|0.5.0|0.5.1|0.5.2|0.5.3-dev.1|0.5.3-dev.2|0.5.3-dev.3|0.5.3-dev.4|0.5.3-dev.5|0.5.3) ;;
  *)
    echo "unexpected BlazePwifi VERSION" >&2
    exit 1
    ;;
esac
test -d "$ROOT/releases/0.3.0" || {
  echo "v0.3.0 release history must remain preserved" >&2
  exit 1
}

vendor_pat="$(printf '%s%s' 'Wi' 'Fi5')"
host_pat="$(printf '%s%s' 'wifi' '5-soft\\.com')"
if grep -RniE "${vendor_pat}|${host_pat}" "$ROOT" --exclude-dir=.git >/tmp/blaze-prohibited.$$ 2>/dev/null; then
  cat /tmp/blaze-prohibited.$$ >&2
  rm -f /tmp/blaze-prohibited.$$
  echo "prohibited commercial reference remains in public BlazePwifi tree" >&2
  exit 1
fi
rm -f /tmp/blaze-prohibited.$$

CFG="$ROOT/openwrt/rootfs/etc/config/blazepwifi"
grep -q "option capability_tier 'auto'" "$CFG"
! grep -q "option admin_key 'CHANGE_ME'" "$CFG"
! grep -q "option vendo_key 'CHANGE_ME'" "$CFG"

CAP="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/capabilities.sh"
[ -f "$CAP" ] || {
  echo "missing capabilities.sh" >&2
  exit 1
}

BP_CAP_TIER=auto BP_CAP_ARCH=mips BP_CAP_MEM_KB=131072 BP_CAP_OVERLAY_KB=8192 sh "$CAP" --detect | grep -qx lite
BP_CAP_TIER=auto BP_CAP_ARCH=aarch64 BP_CAP_MEM_KB=524288 BP_CAP_OVERLAY_KB=1048576 sh "$CAP" --detect | grep -qx standard
BP_CAP_TIER=auto BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=2097152 BP_CAP_OVERLAY_KB=2097152 sh "$CAP" --detect | grep -qx full
BP_CAP_TIER=lite BP_CAP_ARCH=x86_64 BP_CAP_MEM_KB=2097152 BP_CAP_OVERLAY_KB=2097152 sh "$CAP" --detect | grep -qx lite

echo "BlazePwifi v0.3 foundation compatibility checks passed"
