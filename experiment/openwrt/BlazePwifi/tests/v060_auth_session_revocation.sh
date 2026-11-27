#!/bin/sh
# AUTH-0662: exercise BOTH real auth libraries against synthetic sessions.
# No customer authentication, cookies, tokens or live accounts.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-auth-revoke-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM

for profile in full r281; do
(
  T="$T/$profile"; mkdir -p "$T/bin" "$T/state" "$T/run"
  export BP_STATE="$T/state" BP_RUN="$T/run"
  case "$profile" in
    full)
      LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
      LOGOUT="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-logout"
      ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin" ;;
    r281)
      LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi/auth.sh"
      LOGOUT="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental-logout"
      ADMIN="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental-admin" ;;
  esac
  sh -n "$LIB"; sh -n "$LOGOUT"; sh -n "$ADMIN"
  grep -Fq 'if ! bp_auth_logout "$BP_AUTH_TOKEN"' "$LOGOUT"
  grep -Fq 'if ! bp_auth_invalidate_user_sessions "$BP_AUTH_USER"' "$ADMIN"

  . "$LIB"
  bp_auth_now() { printf '1000'; }
  bp_auth_cfg() { printf '%s' "$2"; }
  bp_tmp_suffix() { printf 'fixture-%s' "$$"; }
  A="$(printf '%064d' 1)"
  B="$(printf '%064d' 2)"
  CSRF="$(printf '%048d' 3)"
  printf '%s\talice\tadmin\t%s\t500\t900\t10000\t10.1.1.2\t0\n' "$A" "$CSRF" > "$BP_ADMIN_SESSIONS"
  printf '%s\tbob\tviewer\t%s\t500\t900\t10000\t10.1.1.3\t0\n' "$B" "$CSRF" >> "$BP_ADMIN_SESSIONS"
  chmod 600 "$BP_ADMIN_SESSIONS"
  : > "$BP_AUDIT"
  chmod 600 "$BP_AUDIT"
  sha() { sha256sum "$BP_ADMIN_SESSIONS" | cut -d' ' -f1; }
  count_token() { awk -F '\t' -v t="$1" '$1==t {count++} END{print count+0}' "$BP_ADMIN_SESSIONS"; }
  initial="$(sha)"

  # Failure in the session refresh copy step is a refused authentication,
  # not a valid session line with an unchanged/partial stale access timestamp.
  cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
if [ "${AUTH_FAULT_AWK:-}" = partial ]; then
  printf 'partial-fixture-session\n'
  exit 74
fi
exec /usr/bin/awk "$@"
AWK
  chmod 700 "$T/bin/awk"
  PATH="$T/bin:$PATH"; export PATH
  hash -r 2>/dev/null || true
  [ "$(command -v awk)" = "$T/bin/awk" ]
  AUTH_FAULT_AWK=partial; export AUTH_FAULT_AWK
  set +e
  bp_auth_session_lookup "$A" 10.1.1.2 > "$T/lookup" 2>&1
  lrc=$?
  bp_auth_logout "$A" alice 10.1.1.2 > "$T/logout" 2>&1
  orc=$?
  bp_auth_invalidate_user_sessions alice > "$T/invalidate" 2>&1
  irc=$?
  set -e
  [ "$lrc" -eq 8 ] && [ "$orc" -eq 8 ] && [ "$irc" -eq 8 ] || {
    echo "$profile ignored injected failing awk: lookup=$lrc logout=$orc invalidate=$irc" >&2; exit 1;
  }
  [ ! -s "$T/lookup" ]
  [ "$(sha)" = "$initial" ]
  [ ! -s "$BP_AUDIT" ]
  unset AUTH_FAULT_AWK

  # Reject failed rename before session removal; no logout ACK or audit.
  cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */admin-sessions.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
  chmod 700 "$T/bin/mv"
  hash -r 2>/dev/null || true
  [ "$(command -v mv)" = "$T/bin/mv" ]
  set +e
  bp_auth_session_lookup "$A" 10.1.1.2 > "$T/lookup" 2>&1
  lrc=$?
  bp_auth_logout "$A" alice 10.1.1.2 > "$T/logout" 2>&1
  orc=$?
  bp_auth_invalidate_user_sessions alice > "$T/invalidate" 2>&1
  irc=$?
  set -e
  [ "$lrc" -eq 8 ] && [ "$orc" -eq 8 ] && [ "$irc" -eq 8 ]
  [ ! -s "$T/lookup" ]
  [ "$(sha)" = "$initial" ]
  [ ! -s "$BP_AUDIT" ]
  rm "$T/bin/mv"
  hash -r 2>/dev/null || true

  # Reject session storage that redirects to another file via a symlink.
  mv "$BP_ADMIN_SESSIONS" "$T/session-original.tsv"
  ln -s "$T/session-original.tsv" "$BP_ADMIN_SESSIONS"
  set +e
  bp_auth_session_lookup "$A" 10.1.1.2 >"$T/lookup" 2>&1; lrc=$?
  bp_auth_logout "$A" alice 10.1.1.2 >"$T/logout" 2>&1; orc=$?
  bp_auth_invalidate_user_sessions alice >"$T/invalidate" 2>&1; irc=$?
  set -e
  [ "$lrc" -eq 8 ] && [ "$orc" -eq 8 ] && [ "$irc" -eq 8 ]
  [ "$(sha256sum "$T/session-original.tsv" | cut -d' ' -f1)" = "$initial" ]
  rm "$BP_ADMIN_SESSIONS"
  mv "$T/session-original.tsv" "$BP_ADMIN_SESSIONS"

  # Positive control: lookup refresh, logout/revocation, other user remains.
  found="$(bp_auth_session_lookup "$A" 10.1.1.2)"
  [ -n "$found" ]
  [ "$(count_token "$A")" = 1 ]
  [ "$(awk -F '\t' -v t="$A" '$1==t{print $6}' "$BP_ADMIN_SESSIONS")" = 1000 ]
  bp_auth_logout "$A" alice 10.1.1.2
  [ "$(count_token "$A")" = 0 ]
  [ "$(count_token "$B")" = 1 ]
  grep -Fq "$(printf '1000\tlogout\talice')" "$BP_AUDIT"
  bp_auth_invalidate_user_sessions bob
  [ ! -s "$BP_ADMIN_SESSIONS" ]
  echo "AUTH-0662 PASS $profile: failed awk/rename/symlink never ACK logout or password-revoke; successful refresh, logout and user-wide revoke"
)
done
echo 'AUTH-0662 source test proof is synthetic; no owner login, hardware TLS, or installed recovery validated'
