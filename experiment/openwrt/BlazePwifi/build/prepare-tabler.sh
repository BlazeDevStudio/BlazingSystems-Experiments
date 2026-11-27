#!/bin/sh
set -eu
DEST="${1:?destination directory required}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VERSION=1.6.1
PKG="@tabler/core@1.6.1"
command -v npm >/dev/null || { echo "npm is required to prepare Tabler core CSS" >&2; exit 1; }
command -v tar >/dev/null || { echo "tar is required" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
cd "$TMP"
ARCHIVE="$(npm pack "$PKG" --silent | tail -n1)"
[ -n "$ARCHIVE" ] && [ -s "$ARCHIVE" ] || { echo "Tabler package download failed" >&2; exit 1; }
tar -xzf "$ARCHIVE" package/dist/css/tabler.min.css
[ -s package/dist/css/tabler.min.css ] || { echo "Tabler core CSS missing from package" >&2; exit 1; }
mkdir -p "$DEST"
cp package/dist/css/tabler.min.css "$DEST/tabler.min.css"
cp "$ROOT/ui/vendor/tabler/LICENSE" "$DEST/LICENSE"
printf '%s\n' "$VERSION" > "$DEST/VERSION"
[ "$(wc -c < "$DEST/tabler.min.css")" -gt 10000 ] || { echo "Tabler core CSS unexpectedly small" >&2; exit 1; }
echo "Prepared Tabler core CSS $VERSION in $DEST"
