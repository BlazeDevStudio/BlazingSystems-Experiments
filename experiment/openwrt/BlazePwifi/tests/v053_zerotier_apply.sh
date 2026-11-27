#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
STAGE=setup
cleanup_test() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "ZeroTier survival test FAILED at stage=$STAGE rc=$rc" >&2
    echo "--- ops.log ---" >&2
    cat "$OPS_LOG" >&2 2>/dev/null || true
    echo "--- zerotier config ---" >&2
    cat "$BP_REMOTE_ZT_CONFIG" >&2 2>/dev/null || true
    echo "--- remote runtime ---" >&2
    cat "$BP_REMOTE_RUNTIME" >&2 2>/dev/null || true
    echo "--- zerotier runtime ---" >&2
    cat "$BP_REMOTE_ZT_RUNTIME" >&2 2>/dev/null || true
  fi
  rm -rf "$TMP"
  exit "$rc"
}
trap cleanup_test EXIT

export BP_STATE="$TMP/state"
export BP_RUN="$TMP/run"
export BP_REMOTE_NETWORK_CONFIG="$TMP/network"
export BP_REMOTE_FIREWALL_CONFIG="$TMP/firewall"
export BP_REMOTE_ZT_CONFIG="$TMP/zerotier"
export OPS_LOG="$TMP/ops.log"
export UCI_LOG="$TMP/uci.log"
export ADMIN_STATE="$TMP/remote-admin.running"
mkdir -p "$BP_STATE" "$BP_RUN" "$TMP/bin"
printf 'BASE-NETWORK\n' > "$BP_REMOTE_NETWORK_CONFIG"
printf 'BASE-FIREWALL\n' > "$BP_REMOTE_FIREWALL_CONFIG"
cat > "$BP_REMOTE_ZT_CONFIG" <<'EOF'
zerotier.global=zerotier
zerotier.global.enabled=0
zerotier.global.secret=
zerotier.earth=network
zerotier.earth.id=8056c2e21c000001
zerotier.earth.allow_managed=1
zerotier.earth.allow_global=0
zerotier.earth.allow_default=0
zerotier.earth.allow_dns=0
EOF
chmod 600 "$BP_REMOTE_ZT_CONFIG"
: > "$OPS_LOG"; : > "$UCI_LOG"

cat > "$TMP/bin/uci" <<'UCI'
#!/bin/sh
set -eu
[ "${1:-}" != "-q" ] || shift
cmd="${1:-}"; shift || true
cfg_for() {
  case "$1" in
    zerotier*) printf '%s' "$BP_REMOTE_ZT_CONFIG" ;;
    firewall*) printf '%s' "$BP_REMOTE_FIREWALL_CONFIG" ;;
    network*) printf '%s' "$BP_REMOTE_NETWORK_CONFIG" ;;
    *) return 1 ;;
  esac
}
strip_quotes() {
  printf '%s' "$1" | sed "s/^'//;s/'$//"
}
case "$cmd" in
  get)
    key="${1:-}"; file="$(cfg_for "$key")" || exit 1
    line="$(grep -F "${key}=" "$file" 2>/dev/null | tail -n1 || true)"
    [ -n "$line" ] || exit 1
    strip_quotes "${line#*=}"
    ;;
  show)
    pkg="${1:-}"; file="$(cfg_for "$pkg.")" || exit 1
    grep -E "^${pkg}\." "$file" 2>/dev/null || true
    ;;
  set)
    kv="${1:-}"; key="${kv%%=*}"; val="${kv#*=}"; file="$(cfg_for "$key")" || exit 1
    tmp="${file}.tmp.$$"
    grep -Fv "${key}=" "$file" > "$tmp" 2>/dev/null || true
    printf '%s=%s\n' "$key" "$val" >> "$tmp"
    mv "$tmp" "$file"
    ;;
  add_list)
    kv="${1:-}"; key="${kv%%=*}"; val="${kv#*=}"; file="$(cfg_for "$key")" || exit 1
    printf '%s=%s\n' "$key" "$val" >> "$file"
    ;;
  delete)
    key="${1:-}"; file="$(cfg_for "$key")" || exit 1
    tmp="${file}.tmp.$$"
    awk -v k="$key" 'index($0,k"=")!=1 && index($0,k".")!=1 {print}' "$file" > "$tmp"
    mv "$tmp" "$file"
    ;;
  commit)
    pkg="${1:-}"
    printf 'commit %s\n' "$pkg" >> "$UCI_LOG"
    ;;
  *)
    exit 1
    ;;
esac
UCI

cat > "$TMP/bin/zerotier-idtool" <<'ZTID'
#!/bin/sh
[ "${1:-}" = generate ] || exit 1
printf '%s\n' 'abcdef1234:0:00112233445566778899aabbccddeeff'
ZTID

cat > "$TMP/bin/zerotier-cli" <<'ZTCLI'
#!/bin/sh
case "${1:-}" in
  info)
    printf '200 info abcdef1234 1.14.2 %s\n' "${ZT_NODE_STATE:-ONLINE}"
    ;;
  get)
    case "${3:-}" in
      status) printf '%s\n' "${ZT_STATUS:-OK}" ;;
      portDeviceName) printf '%s\n' "${ZT_IF:-ztblaze123}" ;;
      ip4) printf '%s\n' "${ZT_IP:-10.77.0.2/24}" ;;
      *) exit 1 ;;
    esac
    ;;
  *)
    exit 1
    ;;
esac
ZTCLI

cat > "$TMP/bin/wg" <<'WG'
#!/bin/sh
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

export ROUTE_SIG='via=192.168.1.1 dev=br-lan'
export DEFAULT_SIG='via=192.168.1.1 dev=eth0'
export ZT_ROUTES='10.77.0.0/24'
export ZT_OTHER_ROUTES='192.168.1.0/24
172.16.0.0/16'
export ZT_STATUS=OK
export ZT_NODE_STATE=ONLINE
export ZT_IF=ztblaze123
export ZT_IP=10.77.0.2/24
export BP_REMOTE_ZT_HEALTH_SECONDS=0
export BP_REMOTE_ROUTE_GET_HOOK='printf "%s" "$ROUTE_SIG"'
export BP_REMOTE_DEFAULT_ROUTE_HOOK='printf "%s" "$DEFAULT_SIG"'
export BP_REMOTE_ZT_ROUTES_HOOK='printf "%s\n" "$ZT_ROUTES"'
export BP_REMOTE_ZT_CONNECTED_ROUTES_HOOK='printf "%s\n" "$ZT_OTHER_ROUTES"'
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
export BP_REMOTE_ZT_SERVICE_HOOK='printf "zerotier-%s\n" "$BP_REMOTE_ZT_SERVICE_ACTION" >> "$OPS_LOG"'

save_zt() {
  nwid="$1"
  bp_remote_save zerotier 1 1 1 BlazePwifi-Test Lab 10.77.0.0/24 30 120     '' 51820 '' '' '' 25 '' 1420 "$nwid"
}

STAGE=identity-preparation
NODE="$(bp_remote_zt_identity_prepare)"
[ "$NODE" = abcdef1234 ]
! grep -q '^zerotier.earth' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.global.secret=abcdef1234:' "$BP_REMOTE_ZT_CONFIG"
[ "$(stat -c '%a' "$BP_REMOTE_ZT_CONFIG")" = 600 ]
RUNTIME_JSON="$(bp_remote_runtime_status_json)"
printf '%s' "$RUNTIME_JSON" | grep -q '"node_id":"abcdef1234"'
! printf '%s' "$RUNTIME_JSON" | grep -q '00112233445566778899aabbccddeeff'

STAGE=config-ownership-guards
printf 'zerotier.global.join=0123456789abcdef\n' >> "$BP_REMOTE_ZT_CONFIG"
set +e; bp_remote_zt_config_compatible; RC=$?; set -e
[ "$RC" -eq 2 ]
sed -i '/^zerotier.global.join=/d' "$BP_REMOTE_ZT_CONFIG"
printf 'zerotier.foreign=network\nzerotier.foreign.id=fedcba9876543210\n' >> "$BP_REMOTE_ZT_CONFIG"
set +e; bp_remote_zt_config_compatible; RC=$?; set -e
[ "$RC" -eq 3 ]
sed -i '/^zerotier.foreign/d' "$BP_REMOTE_ZT_CONFIG"

STAGE=initial-profile-validation
save_zt 0123456789abcdef
bp_remote_zt_live_validate 192.168.1.10

STAGE=first-live-apply
# Successful apply requires ONLINE/TUNNELED + network OK + interface + assigned IPv4.
bp_remote_zerotier_apply 192.168.1.10
[ "$(bp_remote_runtime_get state)" = active ]
[ "$(bp_remote_activation_state)" = active ]
[ "$(bp_remote_zt_runtime_get active)" = 1 ]
[ "$(bp_remote_zt_runtime_get network_id)" = 0123456789abcdef ]
[ "$(bp_remote_zt_runtime_get node_id)" = abcdef1234 ]
[ "$(bp_remote_zt_runtime_get interface)" = ztblaze123 ]
[ "$(bp_remote_zt_runtime_get address)" = 10.77.0.2/24 ]
[ "$(bp_remote_runtime_get wg_listener)" = 10.77.0.2:8443 ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ ! -d "$BP_REMOTE_APPLY_ROOT/snapshots/$(bp_remote_runtime_get apply_id)" ]
[ -e "$ADMIN_STATE" ]
grep -q '^zerotier.blazepwifi=network' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.blazepwifi.allow_managed=1' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.blazepwifi.allow_global=0' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.blazepwifi.allow_default=0' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.blazepwifi.allow_dns=0' "$BP_REMOTE_ZT_CONFIG"
grep -q 'firewall.blazezt' "$BP_REMOTE_FIREWALL_CONFIG"
grep -q 'firewall.blazezt_admin' "$BP_REMOTE_FIREWALL_CONFIG"
ACTIVE_ZT="$(cat "$BP_REMOTE_ZT_CONFIG")"
ACTIVE_FW="$(cat "$BP_REMOTE_FIREWALL_CONFIG")"
ACTIVE_PROFILE="$(bp_remote_runtime_get profile_sha)"
ACTIVE_LISTENER="$(bp_remote_runtime_get wg_listener)"

STAGE=staged-profile-change
# Changing network ID is staged until the next successful transaction.
save_zt fedcba9876543210
[ "$(bp_remote_activation_state)" = active_staged_changes ]

STAGE=access-denied-rollback
# ACCESS_DENIED must restore the previously active ZeroTier config/runtime/listener.
ZT_STATUS=ACCESS_DENIED
set +e; bp_remote_zerotier_apply 192.168.1.10; APPLY_RC=$?; set -e
check_eq() {
  name="$1"; got="$2"; want="$3"
  if [ "$got" != "$want" ]; then
    printf 'ASSERT %s FAILED\n  got:  <%s>\n  want: <%s>\n' "$name" "$got" "$want" >&2
    return 1
  fi
  printf 'ASSERT %s OK\n' "$name" >&2
}
check_true() {
  name="$1"; shift
  if ! "$@"; then
    printf 'ASSERT %s FAILED\n' "$name" >&2
    return 1
  fi
  printf 'ASSERT %s OK\n' "$name" >&2
}

check_eq access_denied_rc "$APPLY_RC" 46
check_eq restored_zerotier_config "$(cat "$BP_REMOTE_ZT_CONFIG")" "$ACTIVE_ZT"
check_eq restored_firewall_config "$(cat "$BP_REMOTE_FIREWALL_CONFIG")" "$ACTIVE_FW"
check_eq restored_runtime_state "$(bp_remote_runtime_get state)" active
check_eq restored_profile_sha "$(bp_remote_runtime_get profile_sha)" "$ACTIVE_PROFILE"
check_eq restored_listener "$(bp_remote_runtime_get wg_listener)" "$ACTIVE_LISTENER"
check_eq rollback_reason "$(bp_remote_runtime_get last_error)" zerotier-ACCESS_DENIED
check_eq restored_zerotier_active "$(bp_remote_zt_runtime_get active)" 1
check_eq staged_change_state "$(bp_remote_activation_state)" active_staged_changes
check_true restored_admin_listener test -e "$ADMIN_STATE"
check_true pending_cleared test ! -e "$BP_REMOTE_PENDING"
check_eq snapshots_cleared "$(find "$BP_REMOTE_APPLY_ROOT/snapshots" -mindepth 1 -maxdepth 1 -type d -print -quit)" ""
ZT_STATUS=OK

STAGE=unsafe-route-rollback
# Unsafe managed default route must be rejected and rolled back.
ZT_ROUTES=default
set +e; bp_remote_zerotier_apply 192.168.1.10; APPLY_RC=$?; set -e
[ "$APPLY_RC" -eq 47 ]
[ "$(cat "$BP_REMOTE_ZT_CONFIG")" = "$ACTIVE_ZT" ]
[ "$(bp_remote_zt_runtime_get active)" = 1 ]
[ -e "$ADMIN_STATE" ]
ZT_ROUTES=10.77.0.0/24

STAGE=watchdog-rollback
# Watchdog owns a ZeroTier transaction and restores the active snapshot exactly.
WATCH_ID=zt-watchdog
bp_remote_snapshot_create "$WATCH_ID"
bp_remote_pending_write "$WATCH_ID" "$(bp_remote_profile_hash)" 192.168.1.10 "$ROUTE_SIG" "$DEFAULT_SIG" zerotier
printf 'BROKEN-ZT\n' > "$BP_REMOTE_ZT_CONFIG"
printf 'BROKEN-FW\n' > "$BP_REMOTE_FIREWALL_CONFIG"
bp_remote_runtime_write applying "$WATCH_ID" broken 0 "" 10.88.0.2:8443 "" 0
bp_remote_zt_runtime_write 0 broken broken broken broken broken
bp_remote_guard "$WATCH_ID"
[ "$(cat "$BP_REMOTE_ZT_CONFIG")" = "$ACTIVE_ZT" ]
[ "$(cat "$BP_REMOTE_FIREWALL_CONFIG")" = "$ACTIVE_FW" ]
[ "$(bp_remote_zt_runtime_get active)" = 1 ]
[ "$(bp_remote_runtime_get last_error)" = watchdog-timeout ]
[ -e "$ADMIN_STATE" ]
[ ! -e "$BP_REMOTE_PENDING" ]
[ -z "$(find "$BP_REMOTE_APPLY_ROOT/snapshots" -mindepth 1 -maxdepth 1 -type d -print -quit)" ]

STAGE=wireguard-conflict
# WireGuard cannot be applied over an active ZeroTier transport.
bp_remote_save wireguard 1 1 1 BlazePwifi-Test Lab 10.20.0.0/24 30 120   198.51.100.8 51820 10.20.0.2/32 BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB= 10.20.0.0/24 25 10.20.0.1 1420 ''
set +e; bp_remote_wg_live_validate 192.168.1.10; WG_RC=$?; set -e
[ "$WG_RC" -eq 32 ]

# Restore staged ZeroTier profile before disabling the active prior tunnel.
save_zt fedcba9876543210

STAGE=remote-path-disable-rejection
# Disable cannot be initiated over the ZeroTier path being removed.
ROUTE_SIG='via= dev=ztblaze123'
set +e; bp_remote_zerotier_disable 10.77.0.10; DISABLE_RC=$?; set -e
[ "$DISABLE_RC" -eq 31 ]
[ "$(bp_remote_zt_runtime_get active)" = 1 ]
ROUTE_SIG='via=192.168.1.1 dev=br-lan'

STAGE=local-disable
# Local disable is transactional and preserves stable identity for reuse.
bp_remote_zerotier_disable 192.168.1.10
[ "$(bp_remote_runtime_get state)" = staged ]
[ "$(bp_remote_zt_runtime_get active)" = 0 ]
[ "$(bp_remote_zt_runtime_get node_id)" = abcdef1234 ]
grep -q '^zerotier.global.secret=abcdef1234:' "$BP_REMOTE_ZT_CONFIG"
grep -q '^zerotier.global.enabled=0' "$BP_REMOTE_ZT_CONFIG"
! grep -q '^zerotier.blazepwifi=' "$BP_REMOTE_ZT_CONFIG"
[ ! -e "$ADMIN_STATE" ]
[ ! -e "$BP_REMOTE_PENDING" ]

STAGE=orphan-snapshot-cleanup
# Boot guard removes completed/orphaned historical snapshots when no transaction is pending.
mkdir -p "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old"
printf 'secret-old\n' > "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old/zerotier"
bp_remote_guard_boot
[ ! -d "$BP_REMOTE_APPLY_ROOT/snapshots/orphan-old" ]

STAGE=zerotier-conflict
# A staged ZeroTier apply is refused while an active non-ZeroTier transport exists.
bp_remote_runtime_write active fake-wireguard "$(bp_remote_profile_hash)" "$(bp_now)" "" 10.20.0.2:8443 "" 123
bp_remote_zt_runtime_write 0 fedcba9876543210 abcdef1234 "" "" staged
set +e; bp_remote_zt_live_validate 192.168.1.10; ZT_RC=$?; set -e
[ "$ZT_RC" -eq 43 ]

STAGE=complete
echo "v0.5.3-dev.5 ZeroTier apply/rollback survival tests passed"
