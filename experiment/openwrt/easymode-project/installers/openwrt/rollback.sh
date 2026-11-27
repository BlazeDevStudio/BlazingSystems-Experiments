#!/bin/sh
set -eu
B=${1:-}
[ -n "$B" ] && [ -d "$B" ] || { echo "usage: $0 /tmp/easymode-backup-TIMESTAMP" >&2; exit 2; }
rm -rf /usr/lib/easymode
[ -d "$B/easymode" ] && cp -a "$B/easymode" /usr/lib/easymode
[ -d "$B/state" ] && { rm -rf /etc/easymode; cp -a "$B/state" /etc/easymode; }
echo "EasyMode files restored from $B. UCI exports remain in the backup for deliberate/manual restoration."
