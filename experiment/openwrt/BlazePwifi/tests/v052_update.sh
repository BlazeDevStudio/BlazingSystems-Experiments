#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/update.sh"
BOOT="$ROOT/tools/BlazePwifi-v0.5.2-update-bootstrap.sh"
BUILD="$ROOT/tools/build-update-bundle.sh"

sh -n "$LIB"
sh -n "$BOOT"
sh -n "$BUILD"
grep -Fq 'Exact SHA-256' "$BOOT"
grep -Fq 'previous stable version is retained for rollback' "$BOOT"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT INT TERM
TARGET="$TMP/root/usr/lib/blazepwifi/demo.txt"
mkdir -p "$(dirname "$TARGET")" "$TMP/bundle/payload$(dirname "$TARGET")"
printf 'stable\n' > "$TARGET"
printf 'candidate-052\n' > "$TMP/bundle/payload$TARGET"
SHA="$(sha256sum "$TMP/bundle/payload$TARGET" | awk '{print $1}')"
printf '%s\t644\t%s\n' "$SHA" "$TARGET" > "$TMP/bundle/manifest.tsv"
printf 'VERSION=0.5.2-test\nBASE_MIN=0.5.0\nSTABILITY_GRACE_SECONDS=600\nFORMAT=blazepwifi-overlay-v1\n' > "$TMP/bundle/release.env"
tar -czf "$TMP/update.tar.gz" -C "$TMP/bundle" release.env manifest.tsv payload
BUNDLE_SHA="$(sha256sum "$TMP/update.tar.gz" | awk '{print $1}')"

export BP_UPDATE_ROOT="$TMP/state"
export BP_UPDATE_RUN="$TMP/run"
export BP_UPDATE_TEST_PREFIX="$TMP/root"
export BP_UPDATE_HEALTH_HOOK=true
. "$LIB"
bp_update_apply "$TMP/update.tar.gz" "$BUNDLE_SHA"
[ "$(cat "$TARGET")" = candidate-052 ]
[ "$(bp_update_env_get "$BP_UPDATE_PENDING" VERSION)" = 0.5.2-test ]
bp_update_manual_rollback
[ "$(cat "$TARGET")" = stable ]
[ ! -e "$BP_UPDATE_PENDING" ]
echo "v0.5.2 transactional update/rollback compatibility tests passed"
