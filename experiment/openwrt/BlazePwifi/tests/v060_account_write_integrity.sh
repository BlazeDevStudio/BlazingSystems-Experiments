#!/bin/sh
# ACC-0642: real paid account writer exercised with disposable synthetic state.
# This is NOT an on-device power-cut test or permission to alter customer funds.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-account-integrity-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/state" "$T/run" "$T/bin"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
bp_init_dirs
A=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
B=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
MAC='aa:bb:cc:dd:ee:ff'
entry() { printf '%s\t%s\t0\t0\t0\t0\t%s\t10.1.1.1\t\n' "$1" "$2" "$MAC"; }
entry "$A" 100 > "$BP_ACCOUNTS"
entry "$B" 900 >> "$BP_ACCOUNTS"
chmod 600 "$BP_ACCOUNTS"
balance() { awk -F '\t' -v d="$1" '$1==d {print $2; exit}' "$BP_ACCOUNTS"; }
checksum() { sha256sum "$BP_ACCOUNTS" | cut -d' ' -f1; }
update() { bp_account_write "$A" 220 0 0 0 0 "$MAC" 10.1.1.1 ''; }
assert_refused() {
  original="$(checksum)"
  set +e
  update >"$T/failure.log" 2>&1
  status=$?
  set -e
  [ "$status" -eq 8 ] || { echo "unsafe account replacement returned $status at stage ${stage:-unknown}" >&2; exit 1; }
  [ "$(checksum)" = "$original" ] || { echo "failed account write changed a paid snapshot" >&2; exit 1; }
}
[ "$(balance "$B")" = 900 ]
update
[ "$(balance "$A")" = 220 ]
[ "$(balance "$B")" = 900 ]
[ "$(awk -F '\t' '$1!=""{n++} END{print n+0}' "$BP_ACCOUNTS")" -eq 2 ]

# A duplicate of an unrelated existing member is no less dangerous than
# a duplicated target account: either corrupts authoritative financial state.
cp -p "$BP_ACCOUNTS" "$T/pristine"
entry "$B" 900 >> "$BP_ACCOUNTS"
stage=duplicate-unrelated
assert_refused
cp -p "$T/pristine" "$BP_ACCOUNTS"
entry "$A" 220 >> "$BP_ACCOUNTS"
stage=duplicate-target
assert_refused
cp -p "$T/pristine" "$BP_ACCOUNTS"

printf 'not-a-real-account\t120\n' >> "$BP_ACCOUNTS"
stage=short-row
assert_refused
cp -p "$T/pristine" "$BP_ACCOUNTS"

# Full-width row with wrong bank digits must not be silently passed through.
printf '%s\tinvalid-credit\t0\t0\t0\t0\t%s\t10.1.1.1\t\n' "$B" "$MAC" >> "$BP_ACCOUNTS"
stage=invalid-bank
assert_refused
cp -p "$T/pristine" "$BP_ACCOUNTS"

# Inject a copy step that emits a plausible partial snapshot before EIO.
cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
if [ "${FAULT_AWK:-}" = partial ]; then
  printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\t1\t0\t0\t0\t0\t\t\t\n'
  exit 74
fi
exec /usr/bin/awk "$@"
AWK
chmod 700 "$T/bin/awk"
# POSIX shells cache command paths. We already invoked /usr/bin/awk for
# checks before installing the fault shim; flush the hash or this EIO
# injection would never be exercised and might falsely certify an unsafe
# successful write.
hash -r 2>/dev/null || true
[ "$(command -v awk)" = "$T/bin/awk" ] || {
  echo "fault-injection awk shim not active" >&2; exit 1
}
export FAULT_AWK=partial
stage=partial-awk
assert_refused
unset FAULT_AWK
[ "$(balance "$B")" = 900 ]

# Prevent replacing a referenced file through an attacker-controlled symlink.
mv "$BP_ACCOUNTS" "$T/account-original.tsv"
ln -s "$T/account-original.tsv" "$BP_ACCOUNTS"
set +e
update >"$T/failure.log" 2>&1
status=$?
set -e
[ "$status" -eq 8 ]
[ "$(awk -F '\t' -v d="$B" '$1==d{print $2}' "$T/account-original.tsv")" = 900 ]
rm "$BP_ACCOUNTS"
mv "$T/account-original.tsv" "$BP_ACCOUNTS"

# Invalid destination account identifier and TSV/newline pollution refused.
old="$(checksum)"
set +e
bp_account_write 'bogus/newline' 220 0 0 0 0 "$MAC" 10.1.1.1 '' >"$T/failure.log" 2>&1
status=$?
set -e
[ "$status" -eq 8 ]
injected="$(printf 'one\ntwo')"
set +e
bp_account_write "$A" 220 0 0 0 0 "$MAC" 10.1.1.1 "$injected" >"$T/failure.log" 2>&1
status=$?
set -e
[ "$status" -eq 8 ]
[ "$(checksum)" = "$old" ]
[ "$(balance "$A")" = 220 ]
[ "$(balance "$B")" = 900 ]

echo 'ACC-0642 PASS: account writer refuses duplicate/invalid/truncated source, symlink, injected fields and failing partial awk before replacing paid seconds'
echo 'LAB ONLY: shared v1 TSVs still lack authenticated crash-atomic fsync journal or hardware powercut acceptance'
