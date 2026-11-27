#!/bin/sh
set -eu
ROOT="${1:-experiment/openwrt/BlazePwifi}"
OUT="${2:-dist/update}"
VERSION="$(cat "$ROOT/VERSION")"
BASE_MIN="${BASE_MIN:-0.5.0}"
GRACE="${STABILITY_GRACE_SECONDS:-600}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT INT TERM
mkdir -p "$WORK/payload" "$OUT"
: > "$WORK/manifest.tsv"

# Configuration/state are intentionally not replaced by feature updates.
# New defaults are migrated idempotently by update-migrate.sh.
find "$ROOT/openwrt/rootfs" -type f | sort | while IFS= read -r src; do
  rel="${src#"$ROOT/openwrt/rootfs"}"
  case "$rel" in
    /etc/config/blazepwifi|/etc/blazepwifi/*) continue ;;
  esac
  dest="$WORK/payload$rel"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  mode="$(stat -c '%a' "$src" 2>/dev/null || stat -f '%Lp' "$src")"
  case "$rel" in
    /usr/sbin/*|/etc/init.d/*|/www/blazepwifi/cgi-bin/*|/usr/lib/blazepwifi/*.sh)
      mode=755 ;;
  esac
  sha="$(sha256sum "$dest" | awk '{print $1}')"
  printf '%s\t%s\t%s\n' "$sha" "$mode" "$rel" >> "$WORK/manifest.tsv"
done

cat > "$WORK/release.env" <<EOF
VERSION=$VERSION
BASE_MIN=$BASE_MIN
STABILITY_GRACE_SECONDS=$GRACE
REQUIRES_REBOOT=0
FORMAT=blazepwifi-overlay-v1
EOF

BUNDLE="$OUT/BlazePwifi-v$VERSION-update.tar.gz"
tar -czf "$BUNDLE" -C "$WORK" release.env manifest.tsv payload
sha256sum "$BUNDLE" > "$BUNDLE.sha256"
printf '%s\n' "$BUNDLE"
