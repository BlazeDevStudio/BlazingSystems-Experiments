#!/bin/sh
# RENT-20261022-ATOMIC: fixture-only expected RED. No customer/device state.
# Proves current v1 can durably change a rental lease before receipt commit.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rent-atomic-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
chmod 700 "$T" "$T/state" "$T/run"
printf 'BLAZE-RENT-ATOMIC-SYNTHETIC-ONLY\n' > "$T/.blaze-fixture-only"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *'get blazepwifi.main.durable_sync') echo 0;;
 *'get blazepwifi.main.rental_seconds_per_pulse') echo 600;;
 *'get blazepwifi.main.pulse_value_centavos') echo 100;;
 *'get blazepwifi.main.vendo_port') echo 4455;;
 *'get blazepwifi.main.vendo_key') echo rent-atomic-fixture-secret;;
 *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"

export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
export BP_RENTAL_UPDATE_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_update.sh"

. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
. "$BP_RENTAL_POLICY_LIB"
bp_rental_init

DID=0123456789abcdef01234567
DSEC=0123456789abcdef0123456789abcdef0123456789abcdef
BEFORE=2000003600
NOW=2000000000
PULSES=2
CONTROLLER=vendo-atomic
NONCE=aabbccdd
TARGET=11223344

# Keep the money calculation deterministic while leaving the CGI status call
# on its real wall clock. The chosen lease is safely in the future.
bp_now() { printf '%s' "$NOW"; }

bp_rental_device_write "$DID" "$DSEC" "$BEFORE" "Fixture phone" "$NOW"
bp_rental_policy_ensure "$DID"

EVENT="r:$(printf 'rental|%s|%s|%s' "$CONTROLLER" "$NONCE" "$TARGET" | bp_sha256)"
[ -z "$(bp_rental_paid_receipt_snapshot "$EVENT")" ]

# Fault injection is limited to this shell and replaces only the final receipt
# append boundary. The real lease writer and paid-state marker remain intact.
bp_rental_append_paid_receipt() { return 8; }

set +e
RESULT="$(bp_rental_apply_coin "$DID" "$CONTROLLER" "$NONCE" "$TARGET" "$PULSES")"
RC=$?
set -e

AFTER="$(printf '%s' "$(bp_rental_device_line "$DID")" | cut -f3)"
RECEIPT="$(bp_rental_paid_receipt_snapshot "$EVENT")"
UNCERTAIN=0
[ -f "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ] && UNCERTAIN=1
EXPECTED_AFTER=$((BEFORE + 600 * PULSES))

# Current containment correctly refuses a success result.
[ "$RC" -ne 0 ]
case "$RESULT" in
  credited*|duplicate*)
    echo "REPRO SETUP FAILURE: successful ACK result escaped receipt failure: $RESULT" >&2
    exit 2 ;;
esac

LEASE_DIVERGED=0
RECEIPT_MISSING=0
[ "$AFTER" = "$EXPECTED_AFTER" ] && LEASE_DIVERGED=1
[ -z "$RECEIPT" ] && RECEIPT_MISSING=1

# Use a separate process for the real authenticated Rental status CGI. Current
# code still exposes the partially written lease while uncertainty is present.
STATUS_NONCE=statusatomic1
STATUS_SIG="$(bp_rental_hmac "$DSEC" "status|$STATUS_NONCE|$DSEC")"
RENTAL_CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
STATUS="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$DID" "$STATUS_NONCE" "$STATUS_SIG" |
  REQUEST_METHOD=POST sh "$RENTAL_CGI")"
STATUS_EXPOSES=0
if printf '%s' "$STATUS" | grep -q '"ok":true' &&
   printf '%s' "$STATUS" | grep -q "\"lease_until_ms\":$((EXPECTED_AFTER * 1000))"; then
  STATUS_EXPOSES=1
fi

if [ "$LEASE_DIVERGED" -eq 1 ] &&
   [ "$RECEIPT_MISSING" -eq 1 ] &&
   [ "$UNCERTAIN" -eq 1 ] &&
   [ "$STATUS_EXPOSES" -eq 1 ]; then
  echo "EXPECTED_UNSAFE RENTAL_V1_SPLIT_WRITE lease_changed=1 receipt_missing=1 uncertainty=1 status_exposes_partial_lease=1 rc=$RC" >&2
  exit 1
fi

if [ "$AFTER" != "$BEFORE" ] ||
   [ "$RECEIPT_MISSING" -ne 1 ] ||
   [ "$UNCERTAIN" -ne 1 ] ||
   [ "$STATUS_EXPOSES" -ne 0 ]; then
  echo "REPRO SETUP FAILURE: lease_before=$BEFORE lease_after=$AFTER receipt_present=$([ -n "$RECEIPT" ] && echo 1 || echo 0) uncertainty=$UNCERTAIN status_exposes=$STATUS_EXPOSES rc=$RC" >&2
  exit 2
fi
printf '%s' "$STATUS" | grep -q 'paid state uncertain; operator reconciliation required'

# Restore the real receipt writer. A different signed event cannot steal or
# clear the structured intent, and cannot change the compensated old lease.
. "$BP_RENTAL_LIB"
bp_now() { printf '%s' "$NOW"; }
WRONG_NONCE=deadbeef
set +e
WRONG="$(bp_rental_apply_coin "$DID" "$CONTROLLER" "$WRONG_NONCE" "$TARGET" "$PULSES")"
WRONG_RC=$?
set -e
[ "$WRONG_RC" -ne 0 ]
[ -z "$WRONG" ]
[ "$(printf '%s' "$(bp_rental_device_line "$DID")" | cut -f3)" = "$BEFORE" ]
[ -f "$BP_PAID_UNCERTAIN" ]

# Exact retry owns the intent and deterministically completes both lease and
# receipt. It is not a duplicate ACK because the original call never escaped.
RECOVERED="$(bp_rental_apply_coin "$DID" "$CONTROLLER" "$NONCE" "$TARGET" "$PULSES")"
[ "$RECOVERED" = "$(printf 'recovered\t%s' "$EXPECTED_AFTER")" ]
[ ! -e "$BP_PAID_UNCERTAIN" ] && [ ! -L "$BP_PAID_UNCERTAIN" ]
[ "$(printf '%s' "$(bp_rental_device_line "$DID")" | cut -f3)" = "$EXPECTED_AFTER" ]
RECOVERED_RECEIPT="$(bp_rental_paid_receipt_snapshot "$EVENT")"
[ "$(printf '%s' "$RECOVERED_RECEIPT" | cut -f2)" = "$DID" ]
[ "$(printf '%s' "$RECOVERED_RECEIPT" | cut -f3)" = "$EXPECTED_AFTER" ]
[ "$(printf '%s' "$RECOVERED_RECEIPT" | cut -f5)" = "p:$PULSES" ]

# Once the recovery is committed, later exact replay is an ordinary duplicate.
DUP="$(bp_rental_apply_coin "$DID" "$CONTROLLER" "$NONCE" "$TARGET" "$PULSES")"
[ "$DUP" = "$(printf 'duplicate\t%s' "$EXPECTED_AFTER")" ]

STATUS_NONCE_2=statusatomic2
STATUS_SIG_2="$(bp_rental_hmac "$DSEC" "status|$STATUS_NONCE_2|$DSEC")"
STATUS_2="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$DID" "$STATUS_NONCE_2" "$STATUS_SIG_2" |
  REQUEST_METHOD=POST sh "$RENTAL_CGI")"
printf '%s' "$STATUS_2" | grep -q '"ok":true'
printf '%s' "$STATUS_2" | grep -q "\"lease_until_ms\":$((EXPECTED_AFTER * 1000))"

echo "PASS: rental v1 intent rolls back synchronous receipt failure, hides uncertain lease, refuses wrong event, and recovers exact retry once"
