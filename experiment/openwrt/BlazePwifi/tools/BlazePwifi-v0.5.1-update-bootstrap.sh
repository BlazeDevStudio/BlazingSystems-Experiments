#!/bin/sh
# One-time bootstrap for BlazePwifi releases that predate the transactional updater.
# Usage: sh BlazePwifi-v0.5.1-update-bootstrap.sh BUNDLE.tar.gz SHA256
set -eu
[ "$(id -u)" = 0 ] || { echo "Run as root." >&2; exit 1; }
BUNDLE="${1:-}"
EXPECTED="${2:-}"
[ -f "$BUNDLE" ] || { echo "Update bundle not found." >&2; exit 1; }
printf '%s' "$EXPECTED" | grep -Eq '^[0-9a-fA-F]{64}$' || {
  echo "Exact SHA-256 from the GitHub release is required." >&2; exit 1;
}
ACTUAL="$(sha256sum "$BUNDLE" | awk '{print $1}')"
[ "$(printf '%s' "$ACTUAL" | tr A-F a-f)" = "$(printf '%s' "$EXPECTED" | tr A-F a-f)" ] || {
  echo "Bundle SHA-256 mismatch." >&2; exit 1;
}
tar -tzf "$BUNDLE" | awk '/^\// || /(^|\/)\.\.($|\/)/ {bad=1} END{exit bad?1:0}' || {
  echo "Unsafe update archive." >&2; exit 1;
}
TMP="/tmp/blazepwifi-bootstrap-update.$$"
trap 'rm -rf "$TMP"' EXIT INT TERM
mkdir -p "$TMP"
tar -xzf "$BUNDLE" -C "$TMP"   payload/usr/lib/blazepwifi/update.sh   payload/usr/sbin/blazepwifi-update
chmod +x "$TMP/payload/usr/sbin/blazepwifi-update"
BP_UPDATE_LIB="$TMP/payload/usr/lib/blazepwifi/update.sh"   "$TMP/payload/usr/sbin/blazepwifi-update" apply "$BUNDLE" "$EXPECTED"
echo "BlazePwifi update staged successfully. The previous stable version is retained for rollback."
