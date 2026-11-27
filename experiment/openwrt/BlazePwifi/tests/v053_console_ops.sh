#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export BP_STATE="$TMP/state"
export BP_RUN="$TMP/run"
export REMOTE_ADDR="192.0.2.10"
mkdir -p "$BP_STATE" "$BP_RUN" "$TMP/bin"

# Match constrained OpenWrt targets where the optional openssl CLI may be absent.
cat > "$TMP/bin/openssl" <<'OPENSSL'
#!/bin/sh
exit 1
OPENSSL
chmod +x "$TMP/bin/openssl"
export PATH="$TMP/bin:$PATH"

. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"

TEST_TERMINAL_ENABLED=1
bp_cfg() {
  case "$1" in
    advanced_terminal_enabled) printf '%s' "$TEST_TERMINAL_ENABLED" ;;
    terminal_ttl_seconds) printf '300' ;;
    terminal_idle_seconds) printf '60' ;;
    terminal_command_timeout_seconds) printf '5' ;;
    terminal_output_max_bytes) printf '4096' ;;
    auth_kdf_rounds) printf '2' ;;
    auth_max_attempts) printf '5' ;;
    auth_global_max_attempts) printf '30' ;;
    auth_window_seconds) printf '300' ;;
    auth_lock_seconds) printf '900' ;;
    auth_idle_seconds) printf '900' ;;
    auth_absolute_seconds) printf '28800' ;;
    auth_bind_ip) printf '1' ;;
    durable_sync) printf '0' ;;
    *) printf '' ;;
  esac
}

. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh"

bp_auth_init
PASS='CorrectHorseBattery1!'
bp_auth_set_password admin admin "$PASS" 0

export BP_AUTH_USER=admin
export BP_AUTH_ROLE=admin
export BP_AUTH_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
export BP_AUTH_MUST_CHANGE=0

# Correct password opens one session.
TOKEN="$(bp_terminal_open "$PASS")"
[ "$(printf '%s' "$TOKEN" | wc -c)" -eq 48 ]
bp_terminal_validate "$TOKEN"
[ "$(bp_terminal_active_count)" -eq 1 ]

# The terminal token is bound to the current authenticated web session.
OLD_AUTH="$BP_AUTH_TOKEN"
export BP_AUTH_TOKEN=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
if bp_terminal_validate "$TOKEN"; then
  echo "terminal token survived admin-session change" >&2
  exit 1
fi
export BP_AUTH_TOKEN="$OLD_AUTH"
bp_terminal_validate "$TOKEN"

# Bounded command runner works and reports exact exit/output.
bp_terminal_exec "$TOKEN" 'printf terminal-ok'
[ "$BP_TERMINAL_RC" -eq 0 ]
[ "$BP_TERMINAL_OUTPUT" = "terminal-ok" ]

# Only one Advanced Terminal command may execute at a time.
(
  exec 5>"$BP_RUN/terminal-exec.lock"
  flock 5
  sleep 2
) &
LOCK_PID=$!
sleep 1
if bp_terminal_exec "$TOKEN" 'printf should-not-run'; then
  echo "concurrent terminal command was not blocked" >&2
  kill "$LOCK_PID" 2>/dev/null || true
  wait "$LOCK_PID" 2>/dev/null || true
  exit 1
else
  [ "$?" -eq 5 ]
fi
wait "$LOCK_PID"

# Detached/background and lifecycle commands are blocked before execution.
if bp_terminal_exec "$TOKEN" 'sleep 1 &'; then
  echo "background terminal command was not blocked" >&2
  exit 1
else
  [ "$?" -eq 2 ]
fi
if bp_terminal_exec "$TOKEN" 'echo $(reboot)'; then
  echo "nested lifecycle command was not blocked" >&2
  exit 1
else
  [ "$?" -eq 2 ]
fi

# Closing invalidates immediately.
bp_terminal_close "$TOKEN"
if bp_terminal_validate "$TOKEN"; then
  echo "closed terminal token remained valid" >&2
  exit 1
fi
[ "$(bp_terminal_active_count)" -eq 0 ]

# Wrong password is audited and cannot open a terminal.
if bp_terminal_open 'WrongPassword123!'; then
  echo "wrong password opened terminal" >&2
  exit 1
fi
grep -q 'console_reauth_failure' "$BP_AUDIT"

# Disabled state blocks opening even with the correct password.
TEST_TERMINAL_ENABLED=0
if bp_terminal_open "$PASS"; then
  echo "disabled terminal opened" >&2
  exit 1
else
  [ "$?" -eq 10 ]
fi
TEST_TERMINAL_ENABLED=1

# Remote profile defaults are disabled and contain no private key field.
bp_remote_init
[ "$(bp_remote_get mode)" = disabled ]
BASE_JSON="$(bp_remote_config_json)"
printf '%s' "$BASE_JSON" | grep -q '"mode":"disabled"'
! printf '%s' "$BASE_JSON" | grep -qi 'private_key'

# Incomplete active modes are rejected.
if bp_remote_save wireguard 1 1 0 BlazePwifi Shop '' 30 120 '' 51820 '' '' '' 25 '' 1420 ''; then
  echo "incomplete WireGuard profile was accepted" >&2
  exit 1
else
  [ "$?" -eq 3 ]
fi
if bp_remote_save zerotier 1 1 0 BlazePwifi Shop '' 30 120 '' 51820 '' '' '' 25 '' 1420 deadbeef; then
  echo "short ZeroTier network id was accepted" >&2
  exit 1
fi

WG_KEY='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
bp_remote_save wireguard 1 1 0 'BlazePwifi-01' 'Shop A' '10.20.0.0/24' 30 120   'vpn.example.com' 51820 '10.20.0.2/32' "$WG_KEY" '10.20.0.0/24' 25 '10.20.0.1' 1420 ''
[ "$(bp_remote_get mode)" = wireguard ]
[ "$(bp_remote_get wg_endpoint)" = vpn.example.com ]
[ "$(bp_remote_get management)" = 1 ]
bp_remote_ready
WG_JSON="$(bp_remote_config_json)"
printf '%s' "$WG_JSON" | grep -q '"wg_peer_public_key"'
! printf '%s' "$WG_JSON" | grep -qi 'private_key'

# Remote Terminal permission cannot be enabled without Remote Management.
if bp_remote_save disabled 1 0 1 BlazePwifi Shop '' 30 120 '' 51820 '' '' '' 25 '' 1420 ''; then
  echo "remote terminal permission bypassed management dependency" >&2
  exit 1
fi

bp_remote_save zerotier 1 1 0 BlazePwifi 'Mesh site' '' 30 120   '' 51820 '' '' '' 25 '' 1420 '0123456789abcdef'
[ "$(bp_remote_get mode)" = zerotier ]
[ "$(bp_remote_get zt_network_id)" = 0123456789abcdef ]
bp_remote_ready

echo "v0.5.3 console operations security tests passed"
