#!/bin/sh
# v0.6.0 money/state migration must not run on the v0.5 overlay updater.
# This test never touches live UCI, router state, customer money or hardware.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/update.sh"
sh -n "$LIB"

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT INT TERM
TARGET="$T/router/usr/lib/blazepwifi/installed.txt"
CUSTOMER="$T/ledger/accounts.tsv"
mkdir -p "$(dirname "$TARGET")" "$(dirname "$CUSTOMER")" "$T/pkg/payload$(dirname "$TARGET")"
printf 'previous-code\n' > "$TARGET"
printf 'paid-customer\t3600\n' > "$CUSTOMER"
printf 'unapproved-060-code\n' > "$T/pkg/payload$TARGET"
DIGEST="$(sha256sum "$T/pkg/payload$TARGET" | awk '{print $1}')"
printf '%s\t644\t%s\n' "$DIGEST" "$TARGET" > "$T/pkg/manifest.tsv"

export BP_UPDATE_ROOT="$T/state"
export BP_UPDATE_RUN="$T/run"
export BP_UPDATE_TEST_PREFIX="$T/router"
export BP_UPDATE_HEALTH_HOOK=true
. "$LIB"

make_release() {
  printf 'VERSION=%s\nBASE_MIN=0.5.0\nSTABILITY_GRACE_SECONDS=600\nFORMAT=blazepwifi-overlay-v1\n' "$1" > "$T/pkg/release.env"
  tar -czf "$T/new.tar.gz" -C "$T/pkg" release.env manifest.tsv payload
  sha256sum "$T/new.tar.gz" | awk '{print $1}'
}

# The test must prove rejection before any persistent state/snapshot mutation.
for release in 0.6.0 0.6.1 0.6.0-rc1 0.6; do
  sum="$(make_release "$release")"
  if bp_update_apply "$T/new.tar.gz" "$sum" > "$T/output" 2>&1; then
    echo "FAIL: unapproved $release upgrade was accepted" >&2
    exit 1
  fi
  grep -q 'transactional config and financial-state rollback has not been approved' "$T/output" || {
    cat "$T/output" >&2
    echo "FAIL: $release rejected for wrong reason" >&2
    exit 1
  }
  [ "$(cat "$TARGET")" = previous-code ] || exit 1
  [ "$(cat "$CUSTOMER")" = "$(printf 'paid-customer\t3600')" ] || exit 1
  [ ! -e "$BP_UPDATE_PENDING" ] || exit 1
  [ ! -e "$BP_UPDATE_STABLE" ] || exit 1
  [ "$(find "$BP_UPDATE_ROOT/snapshots" -mindepth 1 -maxdepth 1 | wc -l)" -eq 0 ] || exit 1
done

# Backward compatibility: 0.5.x overlay application and manual rollback
# remain functional. This is not authorization to release the new code.
sum="$(make_release 0.5.3)"
bp_update_apply "$T/new.tar.gz" "$sum"
[ "$(cat "$TARGET")" = unapproved-060-code ] || exit 1
[ "$(bp_update_env_get "$BP_UPDATE_PENDING" VERSION)" = 0.5.3 ] || exit 1
bp_update_manual_rollback
[ "$(cat "$TARGET")" = previous-code ] || exit 1
[ ! -e "$BP_UPDATE_PENDING" ] || exit 1
[ "$(cat "$CUSTOMER")" = "$(printf 'paid-customer\t3600')" ] || exit 1

echo "v0.6.0 migration release preflight: blocked before mutation; v0.5.x apply/rollback preserved"
