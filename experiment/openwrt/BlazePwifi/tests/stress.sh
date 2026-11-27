#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.lan_if') echo br-lan;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.pause_max_seconds') echo 0;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
exit 0
NFT
chmod +x "$T/bin/"*

export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$BP_LIB"
bp_init_dirs

# Kernel flock must be released automatically when a CGI exits without
# explicitly unlocking, so a crashed request cannot wedge accounting.
(
  . "$BP_LIB"
  bp_init_dirs
  bp_lock
  exit 0
)
bp_lock
bp_unlock
echo 'stress: crash-safe flock release ok'

# A read-only portal visit must not create a durable account row.
D0=eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
bp_bind_device "$D0" 02:00:00:00:00:ee 10.0.0.2 0
! grep -q "^$D0	" "$BP_ACCOUNTS"
echo 'stress: zero-account suppression ok'

D=cccccccccccccccccccccccccccccccc
MAC1=02:00:00:00:00:01
MAC2=02:00:00:00:00:02
NOW="$(date +%s)"
EXP=$((NOW+3600))
VOUCHER_EVENT="v:$(printf voucher-test | sha256sum | awk '{print $1}')"

bp_account_write "$D" 500 "$EXP" 0 0 0 "$MAC1" 10.0.0.10 "$VOUCHER_EVENT"

# Push far more coin replay IDs than the configured retention window.
i=1
while [ "$i" -le 50 ]; do
  line="$(bp_account_line "$D")"
  events="$(printf '%s' "$line" | cut -f9)"
  coin="c:$(printf 'coin-%s' "$i" | sha256sum | awk '{print $1}')"
  events="$(bp_events_push "$events" "$coin")"
  bp_account_write "$D" 500 "$EXP" 0 0 0 "$MAC1" 10.0.0.10 "$events"
  i=$((i+1))
done

events="$(bp_account_field "$D" 9)"
bp_events_has "$events" "$VOUCHER_EVENT"
COINS="$(printf '%s' "$events" | tr ',' '\n' | grep -c '^c:' || true)"
[ "$COINS" -le 8 ]
[ "$(printf '%s' "$events" | tr ',' '\n' | grep -c '^v:' || true)" -eq 1 ]
echo 'stress: replay history retention ok'

# Runtime loss/reboot must not erase paid account state.
rm -rf "$T/run"; mkdir -p "$T/run"; chmod 700 "$T/run"
BP_RUN="$T/run"; export BP_RUN
bp_init_dirs
[ "$(bp_get_credit "$D")" -eq 500 ]
[ "$(bp_remaining "$D")" -gt 3000 ]
echo 'stress: persistent account reload ok'

# Private-MAC rotation rebinds the same account instead of duplicating it.
bp_lock
bp_bind_device "$D" "$MAC2" 10.0.0.11
bp_unlock
[ "$(bp_account_field "$D" 7)" = "$MAC2" ]
[ "$(bp_get_credit "$D")" -eq 500 ]
[ "$(awk -F '\t' -v d="$D" '$1==d {n++} END{print n+0}' "$BP_ACCOUNTS")" -eq 1 ]
echo 'stress: MAC rebind ok'

# v0.1 MAC-keyed state is claimed exactly once during upgrade.
LEGACY_MAC=02:00:00:00:00:99
printf '%s\t700\n' "$LEGACY_MAC" > "$BP_LEGACY_CREDITS"
printf '%s\t%s\t10.0.0.99\n' "$LEGACY_MAC" "$EXP" > "$BP_LEGACY_SESSIONS"
D2=dddddddddddddddddddddddddddddddd
bp_lock
bp_bind_device "$D2" "$LEGACY_MAC" 10.0.0.99
bp_unlock
[ "$(bp_get_credit "$D2")" -eq 700 ]
[ "$(bp_remaining "$D2")" -gt 3000 ]
! grep -q "^$LEGACY_MAC	" "$BP_LEGACY_CREDITS"
! grep -q "^$LEGACY_MAC	" "$BP_LEGACY_SESSIONS"
echo 'stress: legacy migration ok'

# Simulate a crash after the new account reached disk but before old legacy
# files were cleaned; the same MAC must never be claimable twice.
printf '%s\t700\n' "$LEGACY_MAC" > "$BP_LEGACY_CREDITS"
printf '%s\t%s\t10.0.0.99\n' "$LEGACY_MAC" "$EXP" > "$BP_LEGACY_SESSIONS"
D3=ffffffffffffffffffffffffffffffff
bp_lock
bp_bind_device "$D3" "$LEGACY_MAC" 10.0.0.99 1
bp_unlock
[ "$(bp_get_credit "$D3")" -eq 0 ]
echo 'stress: migration replay blocked'
! grep -q "^$LEGACY_MAC	" "$BP_LEGACY_CREDITS"
! grep -q "^$LEGACY_MAC	" "$BP_LEGACY_SESSIONS"

# Concurrent writers must serialize without losing rows or sharing temp paths.
i=1
while [ "$i" -le 12 ]; do
  n="$i"
  (
    . "$BP_LIB"
    bp_init_dirs
    d="$(printf '%032x' "$n")"
    m="$(printf '02:00:00:00:01:%02x' "$n")"
    bp_lock || exit 1
    bp_account_write "$d" "$n" 0 0 0 0 "$m" "10.0.1.$n" ""
    bp_unlock
  ) &
  i=$((i+1))
done
wait

i=1
while [ "$i" -le 12 ]; do
  d="$(printf '%032x' "$i")"
  [ "$(bp_get_credit "$d")" -eq "$i" ]
  i=$((i+1))
done
echo 'stress: concurrent writers ok'

echo 'BlazePwifi persistence/replay stress checks passed'

