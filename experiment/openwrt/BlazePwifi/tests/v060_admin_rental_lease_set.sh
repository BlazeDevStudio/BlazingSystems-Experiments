#!/bin/sh
# RENT-0649: execute real authenticated admin CGI against synthetic paid devices.
# Isolated /tmp records, no customer account, phone or production credentials.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-admin-set-XXXXXX)"
trap 'rc=$?; if [ "$rc" -ne 0 ]; then
  printf "RENT-0649 authenticated CGI failed at stage=%s rc=%s\\n" "${stage:-bootstrap}" "$rc" >&2
  printf "Synthetic response: %s\\n" "${last_response:-empty}" >&2
fi
rm -rf "$T"' EXIT
trap 'exit 1' HUP INT TERM
stage=bootstrap
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *'get blazepwifi.main.admin_port') echo 8443;;
 *'get blazepwifi.main.durable_sync') echo 0;;
 *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh"
export BP_CONFIG_LIB="$LIB/config.sh" BP_RENTAL_LIB="$LIB/rental.sh"
export BP_RENTAL_POLICY_LIB="$LIB/rental_policy.sh"
export BP_CONTROLLER_LIB="$LIB/controller.sh" BP_MEMBER_LIB="$LIB/member.sh"
export BP_MEMBER_MIGRATION_LIB="$LIB/member_migration.sh"
export BP_CONSOLE_OPS_LIB="$LIB/console_ops.sh"
export BP_REMOTE_APPLY_LIB="$LIB/remote_apply.sh"
export BP_RENTAL_POLICY_V2="$T/state/rental-policy-v2.tsv"
# Source the libraries outside CGI mode; common.sh consumes stdin for
# POST bodies during sourcing, which under set -e exits when no body exists.
# Only the actual child CGI request uses REQUEST_METHOD=POST.
export SERVER_PORT=8443 REMOTE_ADDR=10.0.0.8
export HTTP_X_BLAZE_SESSION=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
export HTTP_X_BLAZE_CSRF=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
bp_rental_init
bp_auth_init
clock="$(bp_now)"
printf '%s\tshopoperator\toperator\t%s\t%s\t%s\t%s\t10.0.0.8\t0\n' \
  "$HTTP_X_BLAZE_SESSION" "$HTTP_X_BLAZE_CSRF" "$clock" "$clock" "$((clock+3600))" \
  > "$BP_ADMIN_SESSIONS"
chmod 600 "$BP_ADMIN_SESSIONS"
printf 'dev01\tfiction-secret-1\t%s\tPhone One\t%s\n' "$((clock+800))" "$clock" > "$BP_RENTAL_DEVICES"
printf 'dev02\tfiction-secret-2\t%s\tPhone Two\t%s\n' "$((clock+2400))" "$clock" >> "$BP_RENTAL_DEVICES"
chmod 600 "$BP_RENTAL_DEVICES"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
lease() { awk -F '\t' -v d="$1" '$1==d{print $3;exit}' "$BP_RENTAL_DEVICES"; }
send() {
  confirm="${2:-}"
  printf 'action=rental_lease_set&device_id=dev01&seconds=%s&confirm_forfeit=%s' "$1" "$confirm" | REQUEST_METHOD=POST sh "$ADMIN"
}
initial="$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)"
stage=refuse-active-paid-shortening
denied="$(send 100)"; last_response="$denied"
printf '%s' "$denied" | grep -q '"ok":false'
printf '%s' "$denied" | grep -q 'shortening paid rental time requires explicit CONFIRM_FORFEIT authorization'
[ "$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)" = "$initial" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]

stage=normal-increase
increase="$(send 1800)"; last_response="$increase"
printf '%s' "$increase" | grep -q '"ok":true'
[ "$(lease dev01)" -gt "$((clock+1700))" ]
[ "$(lease dev02)" -eq "$((clock+2400))" ]
grep -q 'forfeit_seconds:0' "$BP_RENTAL_EVENTS"
[ ! -e "$BP_PAID_UNCERTAIN" ]

# Failed rename of the exact money file; authentic operator/session and CSRF
# still work but no success response or balance changes are permitted.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
pre="$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)"
stage=failed-rename
failed="$(send 2500)"; last_response="$failed"
printf '%s' "$failed" | grep -q '"ok":false'
printf '%s' "$failed" | grep -q 'rental lease storage or audit failed'
[ "$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)" = "$pre" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv";hash -r 2>/dev/null || true
stage=quarantined-retry
retry="$(send 2500)"; last_response="$retry"
printf '%s' "$retry" | grep -q 'paid state uncertain'
[ "$(sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1)" = "$pre" ]

# Remove a synthetic-only marker to test late audit EIO after balance change.
rm "$BP_PAID_UNCERTAIN"
cat > "$T/bin/chmod" <<'CHMOD'
#!/bin/sh
case "${2:-}" in */rental-events.tsv) exit 74;; esac
exec /bin/chmod "$@"
CHMOD
chmod 700 "$T/bin/chmod";hash -r 2>/dev/null || true
stage=failed-audit
failed_audit="$(send 2400)"; last_response="$failed_audit"
printf '%s' "$failed_audit" | grep -q '"ok":false'
printf '%s' "$failed_audit" | grep -q 'rental lease storage or audit failed'
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/chmod";hash -r 2>/dev/null || true
[ "$(lease dev02)" -eq "$((clock+2400))" ]

# Clear only fictional /tmp marker. Confirmed intentional cancellation is
# recorded with both previous and new expiry, never silently called a refund.
rm "$BP_PAID_UNCERTAIN"
stage=explicit-forfeit
shortened="$(send 30 CONFIRM_FORFEIT)"; last_response="$shortened"
printf '%s' "$shortened" | grep -q '"ok":true'
[ "$(lease dev01)" -le "$((clock+60))" ]
[ "$(lease dev02)" -eq "$((clock+2400))" ]
grep -q 'forfeit_seconds:[1-9][0-9]*' "$BP_RENTAL_EVENTS"
grep -q 'lease_set' "$BP_RENTAL_EVENTS"
[ ! -e "$BP_PAID_UNCERTAIN" ]

echo 'RENT-0649 real operator CGI PASS: CSRF/session, no implicit lease shortening, money+audit failure quarantine, explicit paid forfeiture logged with old/new expiry'
echo 'LAB ONLY: real authenticated crash-atomic journal/rollbackable migration and hardware power cut acceptance missing'
