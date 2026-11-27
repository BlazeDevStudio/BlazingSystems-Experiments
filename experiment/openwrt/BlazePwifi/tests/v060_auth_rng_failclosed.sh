#!/bin/sh
# RNG-0660: test actual auth caller behavior when all CSPRNG sources fail.
# Only fictional /tmp data, no owner/admin credentials or live devices.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-auth-csrf-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
for profile in full r281; do
(
  ROOT_TMP="$T/$profile"
  mkdir -p "$ROOT_TMP/state" "$ROOT_TMP/run"
  export BP_STATE="$ROOT_TMP/state" BP_RUN="$ROOT_TMP/run"
  case "$profile" in
    full) LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh";;
    r281) LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi/auth.sh";;
  esac
  sh -n "$LIB" || { echo "auth shell syntax failure $profile" >&2; exit 1; }
  # The shell library must have exactly one of each sensitive function.
  [ "$(grep -c '^bp_auth_random_hex()' "$LIB")" -eq 1 ]
  [ "$(grep -c '^bp_auth_login()' "$LIB")" -eq 1 ]
  [ "$(grep -c '^bp_auth_set_password()' "$LIB")" -eq 1 ]
  . "$LIB"
  # Isolated fixture; do NOT touch existing system data.
  printf 'admin\tadmin\tsha256i\tsalt-old\thash-old\t1000\t0\n' > "$BP_ADMIN_USERS"
  : > "$BP_ADMIN_SESSIONS"
  : > "$BP_AUTH_FAILURES"
  : > "$BP_AUDIT"
  chmod 600 "$BP_ADMIN_USERS" "$BP_ADMIN_SESSIONS" "$BP_AUTH_FAILURES" "$BP_AUDIT"
  original="$(sha256sum "$BP_ADMIN_USERS" | cut -d' ' -f1)"
  # Stubs isolate success/failure propagation, NOT actual cryptographic strength.
  bp_auth_now() { printf '1000'; }
  bp_auth_cfg() { printf '%s' "$2"; }
  bp_auth_init() { :; }
  bp_auth_lock() { :; }
  bp_auth_unlock() { :; }
  bp_auth_is_locked() { return 1; }
  bp_auth_verify_password() { return 0; }
  bp_auth_user_line() { printf 'admin\tadmin\tsha256i\tsalt-old\thash-old\t1000\t0\n'; }
  bp_auth_clear_failures() { :; }
  bp_auth_audit() { printf '%s\n' "$1" >> "$BP_AUDIT"; }
  bp_auth_sha256i() { printf '%s' "fixture-hash"; }

  # No CSPRNG => no password salt, no session token/CSRF and NO login ACK.
  bp_auth_random_hex() { return 8; }
  set +e
  bp_auth_set_password admin admin synthetic-long-password 0 > "$ROOT_TMP/password.out" 2>&1
  passrc=$?
  bp_auth_session_create_unlocked admin admin 127.0.0.1 > "$ROOT_TMP/session.out" 2>&1
  sessionrc=$?
  bp_auth_login admin synthetic-long-password 127.0.0.1 > "$ROOT_TMP/login.out" 2>&1
  loginrc=$?
  set -e
  [ "$passrc" -eq 8 ] && [ "$sessionrc" -eq 8 ] && [ "$loginrc" -eq 8 ] || {
    echo "$profile rejected entropy statuses wrong: pass=$passrc session=$sessionrc login=$loginrc" >&2
    exit 1
  }
  [ "$(sha256sum "$BP_ADMIN_USERS" | cut -d' ' -f1)" = "$original" ]
  [ ! -s "$BP_ADMIN_SESSIONS" ]
  [ ! -s "$ROOT_TMP/login.out" ] && [ ! -s "$ROOT_TMP/session.out" ]
  ! grep -q '^login_success$' "$BP_AUDIT"
  grep -q '^session_create_failed$' "$BP_AUDIT"

  # A backend can also return success with truncated output. Shape check.
  bp_auth_random_hex() { printf 'f'; }
  set +e
  bp_auth_set_password admin admin synthetic-long-password 0 >/dev/null 2>&1
  passrc=$?
  bp_auth_session_create_unlocked admin admin 127.0.0.1 >"$ROOT_TMP/session.out" 2>&1
  sessionrc=$?
  set -e
  [ "$passrc" -eq 8 ] && [ "$sessionrc" -eq 8 ]
  [ "$(sha256sum "$BP_ADMIN_USERS" | cut -d' ' -f1)" = "$original" ]
  [ ! -s "$BP_ADMIN_SESSIONS" ]

  # Positive control: test-only canonical fake strings (NEVER production).
  bp_auth_random_hex() {
    case "$1" in
      8) printf '0011223344556677';;
      24) printf '%048d' 0;;
      32) printf '%064d' 0;;
      *) return 8;;
    esac
  }
  token="$(bp_auth_session_create_unlocked admin admin 127.0.0.1)"
  [ -n "$token" ]
  [ "$(printf '%s' "$token" | awk -F '\t' '{print length($1)}')" -eq 64 ]
  [ "$(printf '%s' "$token" | awk -F '\t' '{print length($2)}')" -eq 48 ]
  [ "$(awk 'END{print NR}' "$BP_ADMIN_SESSIONS")" -eq 1 ]
  echo "RNG-0660 PASS $profile: failed/truncated entropy no password or session ACK; checked positive fixture generated session"
)
done
echo 'RNG-0660 verified full+standalone auth caller fail-closed propagation; NO real private keys and NO on-device signing proof'
