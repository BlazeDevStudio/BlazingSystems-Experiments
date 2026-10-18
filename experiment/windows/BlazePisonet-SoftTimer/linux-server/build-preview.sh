#!/bin/sh
# Produce a deterministic source bundle for an approved Linux lab host.
set -eu
[ "$#" -eq 1 ] || { echo 'Usage: build-preview.sh ABSOLUTE_OUTPUT_DIR' >&2; exit 2; }
case "$1" in /*) ;; *) echo 'Output directory must be absolute.' >&2; exit 2;; esac
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
OUT="$1"
VERSION='0.1.0-preview.2'
NAME="BlazePisonet-LIO-v$VERSION-linux"
TMP="$(mktemp -d)"
trap 'rm -r -- "$TMP"' EXIT HUP INT TERM
BUNDLE="$TMP/$NAME"
mkdir "$BUNDLE"
FILES='README.md install-preview.sh uninstall-preview.sh blaze_lio_prepare.py blaze_lio_activate.py blaze_lio_status.py blaze_lio_ssh_status.py'
for file in $FILES; do
  [ -f "$ROOT/$file" ] && [ ! -L "$ROOT/$file" ] || {
    echo "Missing or unsafe package source: $file" >&2; exit 1;
  }
  cp "$ROOT/$file" "$BUNDLE/$file"
done
(cd "$BUNDLE" && sha256sum $FILES) > "$BUNDLE/MANIFEST.sha256"
tar --format=ustar --sort=name --mtime='@0' --owner=0 --group=0 \
  --numeric-owner -cf "$TMP/bundle.tar" -C "$TMP" "$NAME"
mkdir -p "$OUT"
gzip -n -9 -c "$TMP/bundle.tar" > "$OUT/$NAME.tar.gz.tmp"
mv -f -- "$OUT/$NAME.tar.gz.tmp" "$OUT/$NAME.tar.gz"
(cd "$OUT" && sha256sum "$NAME.tar.gz") > "$OUT/$NAME.SHA256SUMS"
printf '%s\n' "$OUT/$NAME.tar.gz"
