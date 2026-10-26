#!/bin/sh
# Run only in an isolated test directory; substitutes the reboot command.
set -eu
ROOT=$(CDPATH= cd "$(dirname "$0")/.." && pwd)
TMP=$(mktemp /tmp/blaze-reboot-test-XXXXXX) || exit 1
STATE=/tmp/blaze-watchdog-reboots-test-$$
trap 'rm -f "$TMP" "$STATE" "$STATE.new"' EXIT
sed \
 -e "s@STATE=/etc/blaze/watchdog-reboots@STATE=$STATE@" \
 -e 's@NOW=$(date +%s)@NOW=${TEST_NOW}@' \
 -e 's@UP=$(cut -d. -f1 /proc/uptime)@UP=3600@' \
 -e 's@HEALTH=$(cat /tmp/blaze-health.json 2>/dev/null || true)@HEALTH=@' \
 -e 's@probe_link "$DEV"@false@' \
 -e 's@logger -t BlazeSystems@:@g' \
 -e 's@/sbin/reboot@/bin/true@' \
 "$ROOT/root/usr/libexec/blaze-watchdog-reboot" >"$TMP"

TEST_NOW=1793003000;export TEST_NOW
sh "$TMP" || exit 1
if sh "$TMP"; then echo 'FAIL: immediate second reboot was allowed' >&2;exit 1;fi
TEST_NOW=1793008401;export TEST_NOW
sh "$TMP" || exit 1
TEST_NOW=1793015000;export TEST_NOW
if sh "$TMP"; then echo 'FAIL: third reboot within 24 hours was allowed' >&2;exit 1;fi
[ "$(wc -l <"$STATE")" = 2 ] || exit 1
echo 'PASS: durable 90-minute spacing and two-per-24-hour reboot budget'
