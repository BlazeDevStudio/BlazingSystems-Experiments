#!/bin/sh
# PAY-0637. Synthetic audit of live library member_delete money preservation.
# No real members/devices/API credentials, all changes inside mktemp.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-member-delete-XXXXXX)"
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

member_row() {
  # username, fictional banked seconds. Eleven valid TSV fields.
  printf '%s\t%s\t1\tsha256i\tsalt\thash\t4096\t%s\t1\t123\tsynthetic\n' "$1" "$1" "$2"
}
member_row alice 350 > "$BP_MEMBERS"
member_row bob 0 >> "$BP_MEMBERS"
member_row invalid abc >> "$BP_MEMBERS"
member_row carol 0 >> "$BP_MEMBERS"
member_row dan 0 >> "$BP_MEMBERS"
chmod 600 "$BP_MEMBERS"
# PAY-0729: seeded member rows have revision 1; global must match.
# The old fixture's global=0 was inconsistent with its own paid records.
printf '1\n' > "$BP_MEMBER_REVISION"
pre="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
revision_before="$(cat "$BP_MEMBER_REVISION")"
set +e
bp_member_delete alice 'admin:synthetic' > "$T/response" 2>&1
rc=$?
set -e
[ "$rc" -eq 6 ] || { echo "nonzero bank deletion error $rc, wanted 6" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$pre" ]
[ "$(cat "$BP_MEMBER_REVISION")" = "$revision_before" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" = 350 ]

set +e
bp_member_delete invalid 'admin:synthetic' > "$T/response" 2>&1
rc=$?
set -e
[ "$rc" -eq 7 ]
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$pre" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]

result="$(bp_member_delete bob 'admin:synthetic')"
[ "$result" = 2 ] || { echo "valid empty account deletion failed" >&2; exit 1; }
[ -z "$(bp_member_line bob)" ]
[ "$(cat "$BP_MEMBER_REVISION")" = 2 ]
grep -Fq "$(printf 'admin:2:bob\t')" "$BP_MEMBER_EVENTS"
[ ! -e "$BP_PAID_UNCERTAIN" ]

# Inject a failure of the actual member-row atomic replacement after
# successful pending-financial marker. Must not return success or forget user.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */members.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
before="$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)"
set +e
bp_member_delete carol 'admin:synthetic' > "$T/response" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "rename failure returned $rc" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$before" ]
[ -n "$(bp_member_line carol)" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv"
set +e
bp_member_delete carol 'admin:synthetic' > "$T/response" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "ambiguous paid state must block retry (got $rc)" >&2; exit 1; }
[ "$(sha256sum "$BP_MEMBERS" | cut -d' ' -f1)" = "$before" ]

# This only clears a marker within the synthetic fixture to exercise a second
# EIO boundary. Never clear paid uncertainty this way on a real system.
rm "$BP_PAID_UNCERTAIN"
set +e
(
  bp_member_event_record() { return 8; }
  bp_member_delete dan 'admin:synthetic' > "$T/response" 2>&1
)
rc=$?
set -e
[ "$rc" -eq 8 ] || { echo "failed delete audit receipt acknowledged" >&2; exit 1; }
[ -f "$BP_PAID_UNCERTAIN" ]
[ "$(printf '%s' "$(bp_member_line alice)" | cut -f8)" = 350 ]
[ -n "$(bp_member_line carol)" ]
# After a partial delete, the only safe response is operator reconciliation:
# a replay must never produce a new success response.
set +e
bp_member_delete dan 'admin:synthetic' > "$T/response" 2>&1
rc=$?
set -e
[ "$rc" -eq 9 ] || { echo "ambiguous audit receipt not quarantined" >&2; exit 1; }

# Member deletion UI is the real authenticated admin CGI, not a fake API:
# enforce actionable error-code translation and no silent forfeiture escape.
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
grep -Fq 'member has paid time remaining; bank or transfer it before deleting' "$ADMIN"
grep -Fq 'invalid member balance; operator reconciliation required' "$ADMIN"
grep -Fq 'member deletion storage failed; reconcile the account before retrying' "$ADMIN"
echo 'PAY-0637 synthetic live member delete PASS: paid balance preserved, empty member removed, failed rename and receipt quarantined, admin explains nonzero bank'
echo 'NOT PRODUCTION: v1 deletion+receipt is still separate files, powercut/fsync+v1 migration testing outstanding'
