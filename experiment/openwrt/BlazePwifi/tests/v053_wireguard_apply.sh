#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export BP_STATE="$TMP/state"
export BP_RUN="$TMP/run"
export BP_REMOTE_NETWORK_CONFIG="$TMP/network"
export BP_REMOTE_FIREWALL_CONFIG="$TMP/firewall"
export UCI_LOG="$TMP/uci.log"
export OPS_LOG="$TMP/ops.log"
export ADMIN_STATE="$TMP/remote-admin.running"
mkdir -p "$BP_STATE" "$BP_RUN" "$TMP/bin"
printf 'BASE-NETWORK\n' > "$BP_REMOTE_NETWORK_CONFIG"
printf 'BASE-FIREWALL\n' > "$BP_REMOTE_FIREWALL_CONFIG"
: > "$UCI_LOG"; : > "$OPS_LOG"

cat > "$TMP/bin/uci" <<'UCI'
#!/bin/sh
printf '%s\n' "$*" >> "$UCI_LOG"
case "$*" in
  "commit network") printf 'uci-network-commit\n' >> "$BP_REMOTE_NETWORK_CONFIG" ;;
  "commit firewall") printf 'uci-firewall-commit\n' >> "$BP_REMOTE_FIREWALL_CONFIG" ;;
esac
exit 0
UCI

cat > "$TMP/bin/wg" <<'WG'
#!/bin/sh
case "$1" in
  genkey)
    printf '%s\n' 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
    ;;
  pubkey)
    cat >/dev/null
    printf '%s\n' 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC='
    ;;
  show)
    case "${2:-}" in
      interfaces) printf '%s\n' blazewg ;;
      blazewg)
        if [ "${3:-}" = latest-handshakes ]; then
          printf 'peer\t%s\n' "${WG_HANDSHAKE_TS:-2000000000}"
        fi
        ;;
      all)
        [ "${3:-}" = latest-handshakes ] && printf 'blazewg\t%s\n' "${WG_HANDSHAKE_TS:-2000000000}"
        ;;
    esac
    ;;
esac
exit 0
WG

for cmd in ifup ifdown ip; do
cat > "$TMP/bin/$cmd" <<'CMD'
#!/bin/sh
printf '%s %s\n' "$(basename "$0")" "$*" >> "$OPS_LOG"
exit 0
CMD
done
chmod +x "$TMP/bin/"*
export PATH="$TMP/bin:$PATH"

. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"

bp_cfg() {
  case "$1" in
    admin_port) printf '8443' ;;
    durable_sync) printf '0' ;;
    *) printf '' ;;
  esac
}

. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/remote_apply.sh"

export CONNECTED_ROUTES='192.168.1.0/24
172.16.0.0/16'
export ROUTE_SIG='via=192.168.1.1 dev=br-lan'
export DEFAULT_SIG='via=192.168.1.1 dev=eth0'
export HEALTH_OK=1
export BP_REMOTE_CONNECTED_ROUTES_HOOK='printf "%s\n" "$CONNECTED_ROUTES"'
export BP_REMOTE_ROUTE_GET_HOOK='printf "%s" "$ROUTE_SIG"'
export BP_REMOTE_DEFAULT_ROUTE_HOOK='printf "%s" "$DEFAULT_SIG"'
export BP_REMOTE_WG_HEALTH_HOOK='[ "$HEALTH_OK" = 1 ]'
export BP_REMOTE_GUARD_HOOK='printf "guard %s\n" "$BP_REMOTE_GUARD_ID" >> "$OPS_LOG"'
export BP_REMOTE_NETWORK_RELOAD_HOOK='printf "network-reload\n" >> "$OPS_LOG"'
export BP_REMOTE_IFUP_HOOK='printf "ifup-hook\n" >> "$OPS_LOG"'
export BP_REMOTE_IFDOWN_HOOK='printf "ifdown-hook\n" >> "$OPS_LOG"'
export BP_REMOTE_LINK_DELETE_HOOK='printf "link-delete\n" >> "$OPS_LOG"'
export BP_REMOTE_LINK_PRECREATE_HOOK='printf "link-precreate\n" >> "$OPS_LOG"'
export BP_REMOTE_FIREWALL_RELOAD_HOOK='printf "firewall-reload\n" >> "$OPS_LOG"'
export BP_REMOTE_ADMIN_START_HOOK='touch "$ADMIN_STATE"; printf "admin-start\n" >> "$OPS_LOG"'
export BP_REMOTE_ADMIN_STOP_HOOK='rm -f "$ADMIN_STATE"; printf "admin-stop\n" >> "$OPS_LOG"'
export BP_REMOTE_ADMIN_STATUS_HOOK='test -f "$ADMIN_STATE"'

PEER='BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB='
save_wg() {
  endpoint="$1"; allowed="$2"; sources="$3"
  bp_remote_save wireguard 1 1 1 BlazePwifi-Test Lab "$sources" 30 120 \
    "$endpoint" 51820 10.20.0.2/32 "$PEER" "$allowed" 25 10.20.0.1 1420 ''
}
expect_validate_rc() {
  want="$1"; source="$2"
  set +e
  bp_remote_wg_live_validate "$source"
  got=$?
  set -e
  [ "$got" -eq "$want" ] || { echo "expected validate rc $want, got $got" >&2; exit 1; }
}

# IPv4 helper must recognize real hosts before route-safety checks rely on it.
bp_remote_ipv4_host 192.168.1.10
! bp_remote_ipv4_host 192.168.1
! bp_remote_ipv4_host 999.168.1.10
cidr='10.20.0.0/24'
bp_remote_ipv4_cidr_valid 192.168.1.0/24
[ "$cidr" = '10.20.0.0/24' ] || { echo "IPv4 helper leaked caller cidr state" >&2; exit 1; }

# Unsafe route contracts.
save_wg 198.51.100.8 0.0.0.0/0 10.20.0.0/24
expect_validate_rc 13 192.168.1.10

save_wg 198.51.100.8 192.168.1.0/24 192.168.1.0/24
expect_validate_rc 14 192.168.1.10

CONNECTED_ROUTES=''
save_wg 198.51.100.8 192.168.1.0/24 192.168.1.0/24
expect_validate_rc 15 192.168.1.10

CONNECTED_ROUTES='192.168.1.0/24
172.16.0.0/16'
save_wg 198.51.100.8 10.20.0.0/24 ''
expect_validate_rc 17 192.168.1.10

save_wg 10.20.0.1 10.20.0.0/24 10.20.0.0/24
expect_validate_rc 18 192.168.1.10

save_wg 198.51.100.8 10.20.0.0/24 10.20.0.0/24
ROUTE_SIG='via= dev=blazewg'
expect_validate_rc 16 192.168.1.10
ROUTE_SIG='via=192.168.1.1 dev=br-lan'
bp_remote_wg_live_validate 192.168.1.10

# Local key is generated on-device and never enters the staged profile JSON.
PUB="$(bp_remote_wg_public_key)"
[ "$PUB" = 'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=' ]
[ "$(stat -c '%a' "$BP_REMOTE_WG_KEY")" = 600 ]
CFG_JSON="$(bp_remote_config_json)"
! printf '%s' "$CFG_JSON" | grep -q 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
! printf '%s' "$CFG_JSON" | grep -qi 'private_key'

# Successful transactional apply.
bp_remote_wireguard_apply 192.168.1.10
[ "$(bp_remote_runtime_get state)" = active ]
[ "$(bp_remote_activation_state)" = active ]
[ "$(bp_remote_runtime_get wg_listener)" = '10.20.0.2:8443' ]
[ "$(bp_remote_runtime_get public_key)" = "$PUB" ]
[ "$(bp_remote_runtime_get last_handshake)" -gt 0 ]
[ "$(stat -c '%a' "$BP_REMOTE_NETWORK_CONFIG")" = 600 ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ -z "$(find "$BP_REMOTE_APPLY_ROOT/snapshots" -mindepth 1 -maxdepth 1 -type d -print -quit)" ]
[ -e "$ADMIN_STATE" ]
grep -q 'network.blazewg' "$UCI_LOG"
grep -q 'network.blazewg_peer' "$UCI_LOG"
grep -q 'firewall.blazewg' "$UCI_LOG"
grep -q 'firewall.blazewg_admin' "$UCI_LOG"
! grep -Eq 'network\.(lan|wan)(=|\.)' "$UCI_LOG"
! grep -Eq 'firewall\.(lan|wan)(=|\.)' "$UCI_LOG"
! grep -q 'uhttpd\.' "$UCI_LOG"

ACTIVE_NET="$(cat "$BP_REMOTE_NETWORK_CONFIG")"
ACTIVE_FW="$(cat "$BP_REMOTE_FIREWALL_CONFIG")"
ACTIVE_PROFILE="$(bp_remote_runtime_get profile_sha)"
ACTIVE_LISTENER="$(bp_remote_runtime_get wg_listener)"

# A staged profile edit leaves the old tunnel active until a new transaction succeeds.
save_wg 203.0.113.9 10.20.0.0/24 10.20.0.0/24
[ "$(bp_remote_activation_state)" = active_staged_changes ]

# Failed re-apply must restore prior network/firewall/runtime, not strand the router.
HEALTH_OK=0
set +e
bp_remote_wireguard_apply 192.168.1.10
APPLY_RC=$?
set -e
[ "$APPLY_RC" -eq 27 ]
[ "$(cat "$BP_REMOTE_NETWORK_CONFIG")" = "$ACTIVE_NET" ]
[ "$(cat "$BP_REMOTE_FIREWALL_CONFIG")" = "$ACTIVE_FW" ]
[ "$(bp_remote_runtime_get state)" = active ]
[ "$(bp_remote_runtime_get profile_sha)" = "$ACTIVE_PROFILE" ]
[ "$(bp_remote_runtime_get wg_listener)" = "$ACTIVE_LISTENER" ]
[ "$(bp_remote_runtime_get last_error)" = handshake-timeout ]
[ "$(bp_remote_activation_state)" = active_staged_changes ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ -e "$ADMIN_STATE" ]
HEALTH_OK=1

# Disable cannot be initiated over the tunnel being removed.
ROUTE_SIG='via= dev=blazewg'
set +e
bp_remote_wireguard_disable 10.20.0.10
DISABLE_RC=$?
set -e
[ "$DISABLE_RC" -eq 31 ]
[ "$(bp_remote_runtime_get state)" = active ]
ROUTE_SIG='via=192.168.1.1 dev=br-lan'

# Local disable is transactional and leaves key/profile staged for reuse.
bp_remote_wireguard_disable 192.168.1.10
[ "$(bp_remote_runtime_get state)" = staged ]
[ "$(bp_remote_activation_state)" = staged ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ ! -e "$ADMIN_STATE" ]
[ -r "$BP_REMOTE_WG_KEY" ]

# Watchdog timeout restores the exact pre-change snapshot and clears ownership.
PRE_WATCH_NET="$(cat "$BP_REMOTE_NETWORK_CONFIG")"
PRE_WATCH_FW="$(cat "$BP_REMOTE_FIREWALL_CONFIG")"
PRE_WATCH_STATE="$(bp_remote_runtime_get state)"
WATCH_ID=watchdog-recovery-test
bp_remote_snapshot_create "$WATCH_ID"
bp_remote_pending_write "$WATCH_ID" "$(bp_remote_profile_hash)" 192.168.1.10 "$ROUTE_SIG" "$DEFAULT_SIG"
printf 'BROKEN-WATCHDOG-NETWORK\n' > "$BP_REMOTE_NETWORK_CONFIG"
printf 'BROKEN-WATCHDOG-FIREWALL\n' > "$BP_REMOTE_FIREWALL_CONFIG"
bp_remote_runtime_write applying "$WATCH_ID" bad 0 "" '10.20.0.2:8443' "$PUB" 0
touch "$ADMIN_STATE"
bp_remote_guard "$WATCH_ID"
[ "$(cat "$BP_REMOTE_NETWORK_CONFIG")" = "$PRE_WATCH_NET" ]
[ "$(cat "$BP_REMOTE_FIREWALL_CONFIG")" = "$PRE_WATCH_FW" ]
[ "$(bp_remote_runtime_get state)" = "$PRE_WATCH_STATE" ]
[ "$(bp_remote_runtime_get last_error)" = watchdog-timeout ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ ! -e "$ADMIN_STATE" ]
! bp_remote_pending_owned "$WATCH_ID"

# Reboot during a pending change restores the exact pre-change snapshot.
PRE_BOOT_NET="$(cat "$BP_REMOTE_NETWORK_CONFIG")"
PRE_BOOT_FW="$(cat "$BP_REMOTE_FIREWALL_CONFIG")"
PRE_BOOT_STATE="$(bp_remote_runtime_get state)"
BOOT_ID=boot-recovery-test
bp_remote_snapshot_create "$BOOT_ID"
bp_remote_pending_write "$BOOT_ID" "$(bp_remote_profile_hash)" 192.168.1.10 "$ROUTE_SIG" "$DEFAULT_SIG"
printf 'BROKEN-NETWORK\n' > "$BP_REMOTE_NETWORK_CONFIG"
printf 'BROKEN-FIREWALL\n' > "$BP_REMOTE_FIREWALL_CONFIG"
bp_remote_runtime_write applying "$BOOT_ID" bad 0 "" '10.20.0.2:8443' "$PUB" 0
touch "$ADMIN_STATE"
bp_remote_guard_boot
[ "$(cat "$BP_REMOTE_NETWORK_CONFIG")" = "$PRE_BOOT_NET" ]
[ "$(cat "$BP_REMOTE_FIREWALL_CONFIG")" = "$PRE_BOOT_FW" ]
[ "$(bp_remote_runtime_get state)" = "$PRE_BOOT_STATE" ]
[ "$(bp_remote_runtime_get last_error)" = reboot-during-apply ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ ! -e "$ADMIN_STATE" ]

# This WireGuard-only fixture intentionally lacks ZeroTier binaries; the
# dedicated dev.5 ZeroTier fixture owns that transport's survival coverage.
bp_remote_save zerotier 1 1 0 BlazePwifi-Test Lab '' 30 120 '' 51820 '' '' '' 25 '' 1420 0123456789abcdef
if bp_remote_zt_live_supported; then
  echo "ZeroTier unexpectedly available in WireGuard-only fixture" >&2
  exit 1
fi

mkdir -p "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old"
printf 'secret-old\n' > "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old/network"
bp_remote_guard_boot
[ ! -d "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old" ]

echo "v0.5.3 WireGuard apply/rollback survival tests passed"
