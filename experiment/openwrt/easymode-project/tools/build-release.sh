#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
V=$(cat "$ROOT/VERSION"); OUT="$ROOT/releases/v$V"
mkdir -p "$OUT/openwrt" "$OUT/windows" "$OUT/offline-html"
cp "$ROOT/installers/offline-html/EasyMode-Installer.html" "$OUT/offline-html/"
cp "$ROOT/installers/windows/Install-EasyMode.ps1" "$OUT/windows/"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
cp -a "$ROOT/core" "$ROOT/modules" "$ROOT/editions" "$ROOT/installers" "$ROOT/VERSION" "$TMP/"
( cd "$TMP" && tar -czf "$OUT/openwrt/EasyMode-$V-all-editions.tar.gz" . )
cp "$OUT/openwrt/EasyMode-$V-all-editions.tar.gz" "$OUT/windows/easymode-upload.tar.gz"
( cd "$OUT" && find . -type f ! -name SHA256SUMS -exec sha256sum {} \; | sort > SHA256SUMS )
echo "release built at $OUT"
