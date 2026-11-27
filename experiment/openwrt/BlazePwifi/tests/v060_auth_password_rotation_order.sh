#!/bin/sh
# AUTH-0663: old privileged sessions are removed BEFORE password commit.
# Execute both real auth.sh CLI paths using ONLY fictional /tmp credentials.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-admin-rotate-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
for profile in full r281; do
(
  T="$T/$profile"; mkdir -p "$T/bin" "$T/state" "$T/run"
  export BP_STATE="$T/state" BP_RUN="$T/run"
  case "$profile" in
    full)
      LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
      ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin" ;;
    r281)
      LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi/auth.sh"
      ADMIN="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental-admin" ;;
  esac
  sh -n "$LIB"; sh -n "$ADMIN"
  # Real password-change CGI must revoke before credential update; a false
  # ACK after post-write failed revoke leaves previous attacker token valid.
  python3 - "$ADMIN" <<'PY'
import sys,pathlib
text=pathlib.Path(sys.argv[1]).read_text()
section=text.split("  password_change)",1)[1]
a=section.find('if ! bp_auth_invalidate_user_sessions "$BP_AUTH_USER"')
b=section.find('if bp_auth_set_password "$BP_AUTH_USER"')
assert a>=0 and b>a, "password was committed before server sessions revoked"
assert 'password was not changed' in section[a:b]
PY

  # Common shim supplies the local fixture's state primitives; all auth
  # login/password/session code is sourced from the real library under test.
  cat > "$T/common.sh" <<'SH'
#!/bin/sh
bp_init_dirs() { mkdir -p "$BP_STATE" "$BP_RUN"; }
bp_now() { date +%s; }
bp_cfg() { return 1; }
bp_tmp_suffix() { printf 'fixture-%s' "$$"; }
bp_durable_sync() { return 0; }
bp_sha256() { sha256sum | cut -d' ' -f1; }
SH
  export BP_LIB="$T/common.sh"
  : > "$T/mv.log"
  export AUTH_MV_LOG="$T/mv.log"
  cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "$2" in
  */admin-sessions.tsv)
    printf 'sessions\n' >> "$AUTH_MV_LOG"
    [ "$AUTH_MV_FAIL" = sessions ] && exit 74;;
  */admin-users.tsv)
    printf 'users\n' >> "$AUTH_MV_LOG"
    [ "$AUTH_MV_FAIL" = users ] && exit 74;;
esac
exec /bin/mv "$@"
MV
  chmod 700 "$T/bin/mv"
  PATH="$T/bin:$PATH"; export PATH

  printf 'alice\tadmin\tsha256i\tsaltold\thashold\t2048\t0\n' > "$BP_STATE/admin-users.tsv"
  printf 'bob\toperator\tsha256i\tsaltbob\thashbob\t2048\t0\n' >> "$BP_STATE/admin-users.tsv"
  chmod 600 "$BP_STATE/admin-users.tsv"
  TOKEN="$(printf '%064d' 7)"
  BOBTOKEN="$(printf '%064d' 8)"
  CSRF="$(printf '%048d' 1)"
  make_sessions() {
    printf '%s\talice\tadmin\t%s\t1\t1\t2000000000\t10.1.1.1\t0\n' "$TOKEN" "$CSRF" > "$BP_RUN/admin-sessions.tsv"
    printf '%s\tbob\toperator\t%s\t1\t1\t2000000000\t10.1.1.2\t0\n' "$BOBTOKEN" "$CSRF" >> "$BP_RUN/admin-sessions.tsv"
    chmod 600 "$BP_RUN/admin-sessions.tsv"
  }
  make_sessions
  sha_users() { sha256sum "$BP_STATE/admin-users.tsv" | cut -d' ' -f1; }
  count_session() { awk -F '\t' -v t="$1" '$1==t{n++}END{print n+0}' "$BP_RUN/admin-sessions.tsv"; }
  original="$(sha_users)"

  # Session rename fault must prevent password write and leave both tokens
  # in place; no successful admin reset may be reported.
  export AUTH_MV_FAIL=sessions
  set +e
  sh "$LIB" --set-password alice admin fictional-long-password >"$T/failed" 2>&1
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "$profile falsely committed password with failed revoke: $rc" >&2;exit 1; }
  [ "$(sha_users)" = "$original" ]
  [ "$(count_session "$TOKEN")" = 1 ]
  [ "$(count_session "$BOBTOKEN")" = 1 ]
  grep -q 'password was not changed' "$T/failed"
  ! grep -qx users "$AUTH_MV_LOG"

  # Healthy operation: auth lock ensures session removal happens before
  # replacement of privileged credential verifier; bob remains active.
  export AUTH_MV_FAIL=none
  : > "$AUTH_MV_LOG"
  sh "$LIB" --set-password alice admin fictional-long-password >"$T/success" 2>&1
  [ "$(count_session "$TOKEN")" = 0 ]
  [ "$(count_session "$BOBTOKEN")" = 1 ]
  [ "$(awk -F '\t' '$1=="bob"{print $5}' "$BP_STATE/admin-users.tsv")" = hashbob ]
  [ "$(awk 'END{print NR}' "$BP_STATE/admin-users.tsv")" -eq 2 ]
  [ "$(sed -n '1p' "$AUTH_MV_LOG")" = sessions ]
  [ "$(sed -n '2p' "$AUTH_MV_LOG")" = users ]
  revised="$(sha_users)"
  [ "$revised" != "$original" ]

  # Password-database failure after successful logout must leave the OLD
  # password verifier available for fresh login, but all prior sessions dead.
  make_sessions
  export AUTH_MV_FAIL=users
  : > "$AUTH_MV_LOG"
  set +e
  sh "$LIB" --set-password alice admin fictional-different-password >"$T/failed" 2>&1
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "$profile falsely ACKed password write EIO: $rc" >&2;exit 1; }
  [ "$(sha_users)" = "$revised" ]
  [ "$(count_session "$TOKEN")" = 0 ]
  [ "$(count_session "$BOBTOKEN")" = 1 ]
  [ "$(sed -n '1p' "$AUTH_MV_LOG")" = sessions ]
  [ "$(sed -n '2p' "$AUTH_MV_LOG")" = users ]

  echo "AUTH-0663 PASS $profile: failed pre-revoke preserves old password; healthy session-before-verifier ordering; failed verifier write leaves old sessions dead and existing password usable"
)
done
echo 'AUTH-0663 lab only: synthetic /tmp CLI and static real-CGI ordering, not device-powercut or production owner recovery certification'
