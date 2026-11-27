#!/bin/sh
# Protect live money/identity state through full OpenWrt sysupgrade.
# This audit uses synthetic filesystem paths and never reads customer data.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
KEEP="$ROOT/openwrt/rootfs/lib/upgrade/keep.d/blazepwifi"
UPDATE="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/update.sh"
BUILD="$ROOT/tools/build-update-bundle.sh"
[ -s "$KEEP" ] || { echo "BlazePwifi sysupgrade keep.d policy missing" >&2; exit 1; }
sh -n "$UPDATE" "$BUILD"

for required in /etc/config/blazepwifi /etc/blazepwifi/state \
    /etc/blazepwifi/portal /etc/uhttpd.crt /etc/uhttpd.key; do
    grep -Fxq "$required" "$KEEP" || {
        echo "sysupgrade preservation missing $required" >&2
        exit 1
    }
done

# Do not include the entire /etc/blazepwifi directory or massive rollback
# snapshots; keep the billing state and portal, not stale updater archives.
if grep -Eq '^/etc/blazepwifi/?$|^/etc/blazepwifi/update(/|$)' "$KEEP"; then
    echo "Unbounded sysupgrade backup path is forbidden" >&2
    exit 1
fi
if grep -E '^[^#[:space:]]' "$KEEP" | grep -v -E '^(/etc/config/blazepwifi|/etc/blazepwifi/state|/etc/blazepwifi/portal|/etc/uhttpd.crt|/etc/uhttpd.key)$'; then
    echo "Unexpected backup path needs review" >&2
    exit 1
fi

# Overlay update bundles must be able to carry the preservation policy,
# without opening the updater whitelist to arbitrary OpenWrt keep.d paths.
. "$UPDATE"
bp_update_path_allowed /lib/upgrade/keep.d/blazepwifi
if bp_update_path_allowed /lib/upgrade/keep.d/foreign-package; then
    echo "Unsafe generic sysupgrade keep.d write permission" >&2
    exit 1
fi
if bp_update_path_allowed /etc/sysupgrade.conf; then
    echo "Updater must not overwrite the operator's sysupgrade.conf" >&2
    exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
BUNDLE="$(sh "$BUILD" "$ROOT" "$TMP")"
[ -s "$BUNDLE" ]
tar -tzf "$BUNDLE" | grep -Fxq 'payload/lib/upgrade/keep.d/blazepwifi' || {
    echo "Overlay bundle omitted the sysupgrade state preservation policy" >&2
    exit 1
}

echo "v0.6 sysupgrade source preservation and exact updater allowlist verified; real OpenWrt sysupgrade -l and reboot still required"
