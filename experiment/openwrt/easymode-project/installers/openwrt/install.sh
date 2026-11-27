#!/bin/sh
set -eu
VERSION=5.0.0-alpha.1
EDITION=${1:-auto}
PREFIX=/usr/lib/easymode
STATE=/etc/easymode
STAMP=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo unknown)
BACKUP=/tmp/easymode-backup-$STAMP
log(){ printf '[EasyMode] %s\n' "$*"; }
fail(){ log "ERROR: $*"; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"; }
[ "$(id -u)" = 0 ] || fail "Run as root on OpenWrt"
need sh; need uci; need ubus
PM=none; command -v apk >/dev/null 2>&1 && PM=apk; command -v opkg >/dev/null 2>&1 && [ "$PM" = none ] && PM=opkg
[ "$PM" != none ] || fail "Neither apk nor opkg found"
FREE=$(df -k /overlay 2>/dev/null | awk 'NR==2{print $4}'); [ -n "${FREE:-}" ] || FREE=0
[ "$FREE" -ge 256 ] || fail "Less than 256 KiB free overlay space"
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
DETECT=$HERE/core/detect.sh
[ -x "$DETECT" ] || fail "Missing detector"
INFO=$($DETECT); log "Device: $INFO"
if [ "$EDITION" = auto ]; then EDITION=$(printf '%s' "$INFO" | sed -n 's/.*"recommended":"\([^"]*\)".*/\1/p'); fi
case "$EDITION" in cellular|ap|router|switch|pc|generic) :;; *) fail "Unknown edition: $EDITION";; esac
mkdir -p "$BACKUP" "$STATE"
[ -d "$PREFIX" ] && cp -a "$PREFIX" "$BACKUP/" || true
[ -d "$STATE" ] && cp -a "$STATE" "$BACKUP/state" || true
uci export network > "$BACKUP/network.uci" 2>/dev/null || true
uci export wireless > "$BACKUP/wireless.uci" 2>/dev/null || true
uci export dhcp > "$BACKUP/dhcp.uci" 2>/dev/null || true
for s in "$HERE"/core/*.sh "$HERE"/modules/hardware/*.sh; do sh -n "$s" || fail "Shell syntax failed: $s"; done
STAGE=/tmp/easymode-stage-$STAMP
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -a "$HERE/core" "$HERE/modules" "$HERE/editions" "$STAGE/"
printf '%s\n' "$VERSION" > "$STAGE/VERSION"
printf '%s\n' "$EDITION" > "$STAGE/ACTIVE_EDITION"
OLD=/tmp/easymode-old-$STAMP
[ -d "$PREFIX" ] && mv "$PREFIX" "$OLD" || true
mkdir -p "$(dirname "$PREFIX")"
if mv "$STAGE" "$PREFIX"; then
  printf '%s\n' "$EDITION" > "$STATE/profile"
  if "$PREFIX/core/detect.sh" >/dev/null 2>&1; then
    rm -rf "$OLD"; log "Installed EasyMode $VERSION ($EDITION)"; log "Backup: $BACKUP"; exit 0
  fi
fi
log "Verification failed; rolling back"
rm -rf "$PREFIX"
[ -d "$OLD" ] && mv "$OLD" "$PREFIX" || true
[ -d "$BACKUP/state" ] && { rm -rf "$STATE"; cp -a "$BACKUP/state" "$STATE"; } || true
exit 1
