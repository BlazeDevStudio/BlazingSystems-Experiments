#!/bin/sh
# RENT-0652: live standalone R281 signed Vendo coin CGI in disposable tempfs.
# Tests positive credit/replay, amount collision, paid rename and audit EIO.
# No real coins, credentials, accounts or appliances.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-coin-XXXXXX)"
stage=initialize
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "RENT-0652 test FAILED at stage: $stage (rc=$rc)" >&2; fi; rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo disposable-standalone-fixture-key;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.rental_seconds_per_pulse') echo 600;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh"
export BP_RENTAL_LIB="$LIB/rental.sh" BP_CONTROLLER_LIB="$LIB/controller.sh"
# Source shared libs with GET, since common.sh reads a POST body from
# stdin at load time; there is no POST body while setting up this fixture.
export REQUEST_METHOD=GET SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
stage=source-r281-common
. "$BP_LIB"
stage=source-r281-auth
. "$BP_AUTH_LIB"
stage=source-r281-rental
. "$BP_RENTAL_LIB"
export REQUEST_METHOD=POST
stage=init-rental-store
bp_rental_init
DEVICE=0123456789abcdef01234567
SECRET=00112233445566778899aabbccddeeff0011223344556677
TARGET=1122334455667788
VENDO="$ROOT/profiles/r281-rental/root/www/cgi-bin/vendo"
now="$(bp_now)"
lease=$((now+300))
expires=$((now+600))
stage=create-initial-device
bp_rental_device_write "$DEVICE" "$SECRET" "$lease" "Disposable rental" 123
stage=create-coin-target
printf '%s\t-\t%s\t%s\tvendo-01\trental\n' "$DEVICE" "$TARGET" "$expires" > "$BP_TARGET_DIR/vendo-01.tsv"
chmod 600 "$BP_TARGET_DIR/vendo-01.tsv"
stage=ready-to-accept-first-synthetic-coin
paid() { printf '%s' "$(bp_rental_device_line "$DEVICE")" | cut -f3; }
moneysha() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }
send_coin() {
  n="$1"; pulses="$2"
  proof="$(printf 'disposable-standalone-fixture-key|coin|vendo-01|%s|%s|%s|disposable-standalone-fixture-key' "$n" "$pulses" "$TARGET" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s' "$n" "$pulses" "$TARGET" "$proof" | sh "$VENDO"
}
stage=first-signed-payment
initial="$(moneysha)"
ok="$(send_coin 0102030405060708 1)"
printf 'R281 first credit response: %s\n' "$ok" >&2
printf '%s' "$ok" | grep -q '"ok":true'
printf '%s' "$ok" | grep -q '"duplicate":false'
[ "$(paid)" -eq $((lease+600)) ]
[ ! -e "$BP_PAID_UNCERTAIN" ]
stage=repeat-signed-payment
before="$(moneysha)"
replayed="$(send_coin 0102030405060708 1)"
printf 'R281 matching replay response: %s\n' "$replayed" >&2
printf '%s' "$replayed" | grep -q '"duplicate":true'
[ "$(moneysha)" = "$before" ]
stage=reused-id-changed-amount
different_pulses="$(send_coin 0102030405060708 2)"
printf 'R281 changed-amount response: %s\n' "$different_pulses" >&2
printf '%s' "$different_pulses" | grep -q '"ok":false'
printf '%s' "$different_pulses" | grep -q 'receipt collision'
[ "$(moneysha)" = "$before" ]

# Failure before commit: the paid rename fails, so no credit and no ACK.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
stage=paid-rename-injected-failure
fail="$(send_coin 1112131415161718 1)"
printf 'R281 paid-rename failure response: %s\n' "$fail" >&2
printf '%s' "$fail" | grep -q '"ok":false'
printf '%s' "$fail" | grep -q 'operator reconciliation required'
[ "$(moneysha)" = "$before" ] && [ -e "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true
retry="$(send_coin 1112131415161718 1)"
printf '%s' "$retry" | grep -q '"ok":false'
[ "$(moneysha)" = "$before" ]

# Only reset synthetic marker inside a disposable temp fixture to drive the
# *second* fault point. NEVER do this on a device holding customer money.
rm "$BP_PAID_UNCERTAIN"
cat > "$T/bin/chmod" <<'CHMOD'
#!/bin/sh
case "$*" in *rental-events.tsv*) exit 74;; esac
exec /bin/chmod "$@"
CHMOD
/bin/chmod 700 "$T/bin/chmod"
hash -r 2>/dev/null || true
before2="$(moneysha)"
stage=audit-chmod-injected-failure
audit_fail="$(send_coin 2122232425262728 1)"
printf 'R281 audit failure response: %s\n' "$audit_fail" >&2
printf '%s' "$audit_fail" | grep -q '"ok":false'
printf '%s' "$audit_fail" | grep -q 'operator reconciliation required'
# Lease may ALREADY have committed; failed receipt may be ambiguous.
[ "$(moneysha)" != "$before2" ]
[ -e "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/chmod"
hash -r 2>/dev/null || true
audit_retry="$(send_coin 2122232425262728 1)"
printf '%s' "$audit_retry" | grep -q '"ok":false'
printf '%s' "$audit_retry" | grep -q 'operator reconciliation required'
[ -e "$BP_PAID_UNCERTAIN" ]
pollsig="$(printf 'disposable-standalone-fixture-key|poll|vendo-01|3132333435363738|0||disposable-standalone-fixture-key' | sha256sum | cut -d' ' -f1)"
stage=uncertain-physical-poll-block
poll="$(printf 'action=poll&id=vendo-01&nonce=3132333435363738&pulses=0&sig=%s' "$pollsig" | sh "$VENDO")"
printf 'R281 uncertain physical poll response: %s\n' "$poll" >&2
printf '%s' "$poll" | grep -q '"insert":0'
echo 'RENT-0652 R281 signed coin CGI PASS: normal ACK+matching replay, changed pulse refused, failed paid rename NO ACK, failed audit keeps quarantine, unsafe retries disabled'
echo 'NOT production: legacy paid lease and receipt remain separate TSV; powercut WAL/source migration/Android signer/R281 hardware tests outstanding'
