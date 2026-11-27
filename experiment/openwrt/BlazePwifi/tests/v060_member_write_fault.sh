#!/bin/sh
# DATA-0640: synthetic real member.sh negative storage tests. No real account.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-member-write-fault-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.member_event_history') echo 256;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
. "$BP_LIB"
. "$BP_MEMBER_LIB"
bp_member_init
row() { printf '%s\t%s\t1\tsha256i\tsalt\thash\t4096\t%s\t1\t123\tfiction\n' "$1" "$1" "$2"; }
row alice 100 > "$BP_MEMBERS"
row bob 900 >> "$BP_MEMBERS"
chmod 600 "$BP_MEMBERS"
# PAY-0729: the existing accounts carry revision 1. Seed matching global
# revision; global 0 with rows at 1 is an invalid paid snapshot.
printf '1\n' > "$BP_MEMBER_REVISION"
baseline="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
bob_bank() { awk -F '\t' '$1=="bob" {print $8;exit}' "$BP_MEMBERS"; }
test_write() {
  bp_member_write alice "Alice Edits" 1 sha256i salt hash 4096 100 2 200 synthetic
}
[ "$(bob_bank)" = 900 ]

# Inject malformed/truncated awk COPY of the other paid members. A rogue
# half-snapshot is a real danger if the subsequent append/rename succeeds.
cat > "$T/bin/awk" <<'AWK'
#!/bin/sh
if [ "${FAULT_AWK:-}" = partial ]; then
  printf 'alice\tcorrupt\t1\tsha256i\tsalt\thash\t4096\t100\t1\t123\tfiction\n'
  exit 73
fi
exec /usr/bin/awk "$@"
AWK
chmod 700 "$T/bin/awk"
export FAULT_AWK=partial
set +e
test_write > "$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "partial awk copy was acknowledged ($rc)" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$baseline" ]
unset FAULT_AWK
[ "$(bob_bank)" = 900 ]

# Existing malformed accounts must be quarantined, not copied into a
# success-looking new ledger. Refuse duplicate rows for same username too.
cp -p "$BP_MEMBERS" "$T/pristine"
printf 'broken\trow\n' >> "$BP_MEMBERS"
corrupt="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
set +e
test_write > "$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] && [ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$corrupt" ]
cp -p "$T/pristine" "$BP_MEMBERS"
row alice 100 >> "$BP_MEMBERS"
duplicate="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
set +e
test_write > "$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] && [ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$duplicate" ]
cp -p "$T/pristine" "$BP_MEMBERS"

# Real member caller must NOT print success on failure of accounts replacement.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */members.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
set +e
bp_member_patch alice "Attempted Rename" @keep admin:synthetic >"$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "member patch falsely succeeded ($rc)" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$baseline" ]
[ -f "$BP_PAID_UNCERTAIN" ]
[ "$(bob_bank)" = 900 ]
rm "$T/bin/mv"
set +e
bp_member_patch alice "Second Attempt" @keep admin:synthetic >"$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "reconciliation marker did not block member mutation" >&2; exit 1; }

# SYNTHETIC operator reconciliation only. No live marker may be cleared.
rm "$BP_PAID_UNCERTAIN"
# Stub password verifier generation so the test isolates account-persistence
# failure; this is not a credential hash test or production auth bypass.
bp_member_hash_password() {
  [ "${#1}" -ge 8 ] || return 2
  printf 'sha256i\tsalt-new\thash-new\t4096\n'
}
# Fail audit append AFTER account write. No false ACK and persistent marker.
set +e
(
  bp_member_event_record() { return 8; }
  bp_member_set_password alice 'sample-long-password' admin:synthetic >"$T/fault.log" 2>&1
)
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "password mutation after audit EIO returned success ($rc)" >&2; exit 1; }
[ -f "$BP_PAID_UNCERTAIN" ]
[ "$(bob_bank)" = 900 ]
set +e
bp_member_set_password alice 'sample-another-password' admin:synthetic >"$T/fault.log" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "post-audit uncertain password retry not blocked" >&2; exit 1; }

# In clean synthetic state, real code may write a new account and event.
rm "$BP_PAID_UNCERTAIN"
result="$(bp_member_create carol "Carol" 'synthetic-8character' admin:synthetic)"
case "$result" in ''|*[!0-9]*) echo 'member create did not return a revision' >&2;exit 1;; esac
[ -n "$(bp_member_line carol)" ]
[ "$(bob_bank)" = 900 ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
echo 'DATA-0640 member-store PASS: partial copy/malformed/duplicate records never replace balances; admin update/password EIO no false ACK and persistent quarantine; clean create works'
echo 'PRODUCTION blocked: separate TSV audit and member changes still lack integrated v2 fsync journal'
