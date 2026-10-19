#!/bin/sh
# Test the actual health functions; all route-writing calls below are mocked.
set -eu
health=${1:-/usr/libexec/blaze-health}
tmp=$(mktemp /tmp/blaze-health-functions.XXXXXX)
trap 'rm -f "$tmp"' EXIT
sed '/^while :; do/,$d' "$health" >"$tmp"
. "$tmp"
uci() { case "$*" in *internet_mode*) echo failover;; *source_order*) echo 'sim wired';; *backup_enabled*) echo 1;; esac; }
SOURCE_AVAILABLE=1
source_info() { [ "$SOURCE_AVAILABLE" = 1 ] || return 1;SRC_DEV=test0;SRC_GW=192.0.2.1;return 0; }
route_one() { source_info "$1" || return 1;CHOSEN="$1";return 0; }
ip() {
 [ "$*" = 'route del unreachable default proto 99 metric 5' ] && { REMOVED_BLACKHOLE=1;return 0; }
 echo "Unexpected route command: $*" >&2;return 1
}
SIM_OK=0;WIRED_OK=0;WIFI_OK=0;set_routes
[ "$CHOSEN" = sim ] && [ "$EFFECTIVE" = degraded ] || exit 1
echo 'PASS: failed probes retain an addressed uplink'
SIM_OK=0;WIRED_OK=1;set_routes
[ "$CHOSEN" = wired ] && [ "$EFFECTIVE" = failover ] || exit 1
echo 'PASS: verified backup still takes priority'
SOURCE_AVAILABLE=0;SIM_OK=0;WIRED_OK=0;WIFI_OK=0;REMOVED_BLACKHOLE=0;set_routes
[ "$REMOVED_BLACKHOLE" = 1 ] && [ "$ACTIVE" = none ] || exit 1
echo 'PASS: no-source state removes a stale high-priority blackhole route'
[ "$(recovery_kind sim)" = reconnect ] && [ "$(recovery_kind wifi)" = reconnect-wifi ] && [ "$(recovery_kind wired)" = reconnect-wired ] || exit 1
echo 'PASS: automatic SIM recovery reconnects the data session without cycling the radio'
