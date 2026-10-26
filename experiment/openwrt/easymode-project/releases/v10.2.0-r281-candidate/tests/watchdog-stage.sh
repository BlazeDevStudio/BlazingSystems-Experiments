#!/bin/sh
# Exercises the actual recovery function with all disruptive commands mocked.
set -eu
ROOT=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp /tmp/blaze-watchdog-test-XXXXXX) || exit 1
trap 'rm -f "$TMP"' EXIT
sed -e '/^while :; do/,$d' \
 -e 's@/usr/libexec/blaze-outage-snapshot@:@g' \
 -e 's@/usr/libexec/blaze-launch@mock_launch@g' \
 -e 's@/usr/libexec/blaze-watchdog-reboot@mock_reboot@g' \
 "$ROOT/root/usr/libexec/blaze-health" >"$TMP"
. "$TMP"
uci() { case "$*" in *watchdog_enabled*) echo 1;; *watchdog_failures*) echo 3;; esac; }
probe_source() { return 1; }
logger() { :; }
record_event() { :; }
save_sim_stage() { :; }
mock_launch() { STARTED=$1; return 0; }
mock_reboot() { REBOOTS=$((REBOOTS+1)); return 0; }

SIM_FAIL=3;SIM_ATTEMPTS=0;SIM_LAST_REC=-1200;WIRED_OK=0;WIFI_OK=0;STARTED='';REBOOTS=0
recover_source sim 3600
[ "$STARTED" = reconnect ] && [ "$SIM_ATTEMPTS" = 1 ] || exit 1
SIM_FAIL=3;STARTED='';recover_source sim 3901
[ "$STARTED" = radio-reconnect ] && [ "$SIM_ATTEMPTS" = 2 ] || exit 1
SIM_FAIL=3;WIRED_OK=1;recover_source sim 4502
[ "$REBOOTS" = 0 ] || exit 1
WIRED_OK=0;recover_source sim 4502
[ "$REBOOTS" = 1 ] || exit 1
echo 'PASS: reconnect, radio, backup guard, and last-resort reboot stages'
