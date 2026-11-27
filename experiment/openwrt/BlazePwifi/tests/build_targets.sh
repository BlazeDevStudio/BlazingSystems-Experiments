#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
B="$ROOT/build/build-openwrt-image.sh"
for token in orangepi_zero3 orangepi_one orangepi_pc xunlong_orangepi-zero3 xunlong_orangepi-one xunlong_orangepi-pc gpiod-tools; do
  grep -q "$token" "$B" || { echo "missing required build target: $token" >&2; exit 1; }
done
grep -q 'target: \[ruijie, x86_64, orangepi_zero3, orangepi_one, orangepi_pc\]' "$ROOT/../../../.github/workflows/blazepwifi-build.yml" 2>/dev/null || true
echo "BlazePwifi hardware build matrix checks passed"
