#!/bin/sh
# AUTH-0661: safeguard *real* full+R281 admin verifier writers.
# Synthetic passwords/state are confined to mktemp, never production admin.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-admin-verifier-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
for profile in full r281; do
(
  T="$T/$profile"
  mkdir -p "$T/state" "$T/run" "$T/bin"
  export BP_STATE="$T/state" BP_RUN="$T/run"
  case "$profile" in
    full) LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh";;
    r281) LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi/auth.sh";;
  esac
  sh -n "$LIB"
  . "$LIB"
  bp_tmp_suffix() { printf 'fixture-%s' "$$"; }
  bp_durable_sync() { return 0; }
  bp_auth_now() { printf '1000'; }
  bp_auth_cfg() { printf '%s' "$2"; }
  bp_auth_random_hex() { printf '0011223344556677'; }
  bp_auth_sha256i() { printf 'fixture-not-a-production-verifier'; }
  # Fictional original hashes, enough to check registry snapshot preservation.
  printf 'alice\tadmin\tsha256i\tsaltold\thashold\t2048\t0\n' > "$BP_ADMIN_USERS"
  printf 'bob\toperator\tsha256i\tsaltold\thashbob\t2048\t0\n' >> "$BP_ADMIN_USERS"
  chmod 600 "$BP_ADMIN_USERS"
  : > "$BP_AUDIT"
  chmod 600 "$BP_AUDIT"
  sha() { sha256sum "$BP_ADMIN_USERS" | cut -d' ' -f1; }
  bob() { awk -F '\t' '$1=="bob" {print $5}' "$BP_ADMIN_USERS"; }
  assert_refused() {
    previous="$(sha)"
    set +e
    bp_auth_set_password alice admin synthetic-long-password 0 > "$T/output" 2>&1
    rc=$?
    set -e
    [ "$rc" -eq 8 ] || { echo "password writer $profile accepted unsafe $stage rc=$rc" >&2; exit 1; }
    [ "$(sha)" = "$previous" ] || { echo "$profile $stage overwrote existing admin hashes" >&2; exit 1; }
  }
  original="$(sha)"
  # Do not turn malformed or duplicated old operators into successful resets.
  printf 'damaged\trow\n' >> "$BP_ADMIN_USERS"
  stage=malformed
  assert_refused
  printf 'alice\tadmin\tsha256i\tsaltold\thashold\t2048\t0\nbob\toperator\tsha256i\tsaltold\thashbob\t2048\t0\n' > "$BP_ADMIN_USERS"
  printf 'bob\toperator\tsha256i\tsaltold\thashbob\t2048\t0\n' >> "$BP_ADMIN_USERS"
  stage=duplicate-operator
  assert_refused
  printf 'alice\tadmin\tsha256i\tsaltold\thashold\t2048\t0\nbob\toperator\tsha256i\tsaltold\thashbob\t2048\t0\n' > "$BP_ADMIN_USERS"
  [ "$(sha)" = "$original" ]

  # Return a plausible partial output, then exit with I/O error.
  cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
if [ "${AUTH_FAULT_AWK:-}" = partial ]; then
  printf 'bob\toperator\tsha256i\tsaltold\thashbob\t2048\t0\n'
  exit 74
fi
exec /usr/bin/awk "$@"
AWK
  chmod 700 "$T/bin/awk"
  PATH="$T/bin:$PATH"; export PATH
  hash -r 2>/dev/null || true
  [ "$(command -v awk)" = "$T/bin/awk" ]
  AUTH_FAULT_AWK=partial; export AUTH_FAULT_AWK
  stage=partial-awk-copy
  assert_refused
  unset AUTH_FAULT_AWK
  [ "$(bob)" = hashbob ]

  # If atomic replace itself fails, do not issue a false success response.
  cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */admin-users.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
  chmod 700 "$T/bin/mv"
  hash -r 2>/dev/null || true
  [ "$(command -v mv)" = "$T/bin/mv" ]
  stage=failed-rename
  assert_refused
  rm "$T/bin/mv"
  hash -r 2>/dev/null || true

  # A symlink pointing to administrator credentials is never an allowed
  # baseline for privileged password update.
  mv "$BP_ADMIN_USERS" "$T/original-users.tsv"
  ln -s "$T/original-users.tsv" "$BP_ADMIN_USERS"
  set +e
  bp_auth_set_password alice admin synthetic-long-password 0 >"$T/output" 2>&1
  rc=$?
  set -e
  [ "$rc" -eq 8 ] && [ "$(sha256sum "$T/original-users.tsv" | cut -d' ' -f1)" = "$original" ]
  rm "$BP_ADMIN_USERS"
  mv "$T/original-users.tsv" "$BP_ADMIN_USERS"

  # Healthy credential reset must retain bob and actually audit the change.
  bp_auth_set_password alice admin synthetic-long-password 0 > "$T/success"
  [ ! -s "$T/success" ]
  [ "$(bob)" = hashbob ]
  [ "$(awk -F '\t' '$1=="alice"{print $4}' "$BP_ADMIN_USERS")" = 0011223344556677 ]
  grep -Fq "$(printf '1000\tpassword_set\talice')" "$BP_AUDIT"
  [ "$(awk 'END{print NR}' "$BP_ADMIN_USERS")" -eq 2 ]

  # Audit fails AFTER new verifier commit. Do not falsely ACK or revert
  # potentially durable credential state; operator must reconcile on device.
  set +e
  (
    bp_auth_audit() { return 8; }
    bp_auth_set_password alice admin synthetic-different-password 0 >"$T/output" 2>&1
  )
  rc=$?
  set -e
  [ "$rc" -eq 8 ] || { echo "$profile false ACK after audit EIO" >&2; exit 1; }
  [ "$(bob)" = hashbob ]
  echo "AUTH-0661 PASS $profile: malformed/duplicate/symlink/partial-copy/rename reject; healthy password+audit persists; failed postcommit audit refuses ACK"
)
done
echo 'NOT PRODUCTION fsync proof: password and audit remain separate v1 files, no actual credentials imported or changed'
