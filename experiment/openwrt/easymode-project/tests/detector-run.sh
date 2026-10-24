#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
mkdir -p "$tmp/core" "$tmp/modules/hardware" "$tmp/installers/openwrt"
cp "$ROOT/core/detect.sh" "$tmp/core/detect.sh"
cp "$ROOT/modules/hardware/capabilities.sh" "$tmp/modules/hardware/capabilities.sh"
cp "$ROOT/installers/openwrt/install.sh" "$tmp/installers/openwrt/install.sh"
chmod a-x "$tmp/core/detect.sh" "$tmp/modules/hardware/capabilities.sh" "$tmp/installers/openwrt/install.sh"
cap=$(sh "$tmp/modules/hardware/capabilities.sh")
det=$(sh "$tmp/installers/openwrt/install.sh" --check-detector)
python3 -c 'import json,sys
for raw in sys.argv[1:]:
    data=json.loads(raw)
    assert "recommended" in data, data
' "$cap" "$det"
rm -rf "$tmp"
echo "detector run passed"
