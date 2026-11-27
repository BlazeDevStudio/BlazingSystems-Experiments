#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"

cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.lan_if') echo br-lan;;
  *'get blazepwifi.main.coin_window') echo 120;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.vendo_key') echo vendokey;;
  *'get blazepwifi.main.pause_max_seconds') echo 0;;
  *'get blazepwifi.main.event_history') echo 16;;
  *'get blazepwifi.main.admin_port') echo 8443;;
  *'get blazepwifi.main.auth_max_attempts') echo 5;;
  *'get blazepwifi.main.auth_global_max_attempts') echo 30;;
  *'get blazepwifi.main.auth_window_seconds') echo 300;;
  *'get blazepwifi.main.auth_lock_seconds') echo 900;;
  *'get blazepwifi.main.auth_idle_seconds') echo 900;;
  *'get blazepwifi.main.auth_absolute_seconds') echo 28800;;
  *'get blazepwifi.main.auth_kdf_rounds') echo 8;;
  *'get blazepwifi.main.auth_bind_ip') echo 1;;
  *'get blazepwifi.main.walled_refresh_seconds') echo 120;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.walled_ip') exit 1;;
  *'get blazepwifi.main.walled_domain') exit 1;;
  *'get blazepwifi.p1.cents') echo 100;;
  *'get blazepwifi.p1.seconds') echo 600;;
  *'get blazepwifi.p1.label') echo 'P1 / 10 minutes';;
  *'show blazepwifi') echo "blazepwifi.p1=rate"; echo "blazepwifi.p1.cents='100'"; echo "blazepwifi.p1.seconds='600'"; echo "blazepwifi.p1.label='P1 / 10 minutes'";;
  *) exit 1;;
esac
UCI

cat > "$T/bin/ip" <<'IP'
#!/bin/sh
echo "$TEST_IP dev br-lan lladdr $TEST_MAC REACHABLE"
IP

cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
exit 0
NFT

chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_CONFIG_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/config.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export BP_MEMBER_MIGRATION_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member_migration.sh"
export BP_CONSOLE_OPS_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/console_ops.sh"
export BP_REMOTE_APPLY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/remote_apply.sh"
export REQUEST_METHOD=POST REMOTE_ADDR=10.0.0.2 TEST_IP=10.0.0.2 TEST_MAC=aa:bb:cc:dd:ee:ff SERVER_PORT=4455

API="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/api"
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
DEVICE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

echo "integration: portal/accounting start"
OUT="$(printf 'action=rates' | sh "$API")"
echo "integration: rates => $(printf '%s' "$OUT" | tr '\n' ' ')"
echo "$OUT" | grep -q '"rates"'
! echo "$OUT" | grep -q 'missing or invalid device token'

REGNONCE=0102030405060708
REGSIG="$(printf 'vendokey|register|vendo-01|%s|0||vendokey' "$REGNONCE" | sha256sum | awk '{print $1}')"
OUT="$(printf 'action=register&id=vendo-01&nonce=%s&pulses=0&target=&sig=%s' "$REGNONCE" "$REGSIG" | sh "$VENDO")"
echo "integration: register vendo-01 => $(printf '%s' "$OUT" | tr '\n' ' ')"
echo "$OUT" | grep -q '"ok":true'

OUT="$(printf 'action=vendos' | sh "$API")"
echo "integration: vendos => $(printf '%s' "$OUT" | tr '\n' ' ')"
echo "$OUT" | grep -q '"vendo-01"'

# Register a second physical Vendo so simultaneous target isolation is exercised.
REG2NONCE=0203040506070809
REG2SIG="$(printf 'vendokey|register|vendo-02|%s|0||vendokey' "$REG2NONCE" | sha256sum | awk '{print $1}')"
OUT="$(printf 'action=register&id=vendo-02&nonce=%s&pulses=0&target=&sig=%s' "$REG2NONCE" "$REG2SIG" | sh "$VENDO")"
echo "$OUT" | grep -q '"ok":true'

OUT="$(printf 'action=me&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"credit_cents":0'
echo "$OUT" | grep -q '"mac":"aa:bb:cc:dd:ee:ff"'
[ ! -s "$T/state/accounts.tsv" ]

# A client may not forge a MAC fallback when the router has no ARP entry.
# This must fail before opening a coin window or creating an account.
OUT="$(printf 'action=coin_start&device=%s&vendo=vendo-01&mac=aa:bb:cc:dd:ee:ff' "$DEVICE" | TEST_MAC= sh "$API")"
echo "$OUT" | grep -q 'client network identity unavailable'
[ ! -s "$T/state/accounts.tsv" ]
[ ! -e "$T/state/targets/vendo-01.tsv" ]

# PAY-0628: a failed coin window rename must not advertise payment readiness.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in
  */targets/vendo-01.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod +x "$T/bin/mv"
OUT="$(printf 'action=coin_start&device=%s&vendo=vendo-01' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'could not persist coin window'
[ ! -e "$T/state/targets/vendo-01.tsv" ]
rm -f "$T/bin/mv"

OUT="$(printf 'action=coin_start&device=%s&vendo=vendo-01' "$DEVICE" | sh "$API")"
echo "integration: coin_start => $(printf '%s' "$OUT" | tr '\n' ' ')"
echo "$OUT" | grep -q '"ok":true'
TARGET="$(printf '%s' "$OUT" | sed -n 's/.*"target_nonce":"\([0-9a-f]*\)".*/\1/p')"
[ -n "$TARGET" ]
[ -s "$T/state/targets/vendo-01.tsv" ]
# A same-device retry/page refresh must return the SAME live controller nonce,
# not invalidate already-inserted physical coins.
REPEAT="$(printf 'action=coin_start&device=%s&vendo=vendo-01' "$DEVICE" | sh "$API")"
echo "$REPEAT" | grep -q '"ok":true'
echo "$REPEAT" | grep -Fq "\"target_nonce\":\"$TARGET\""
[ "$(cut -f3 "$T/state/targets/vendo-01.tsv")" = "$TARGET" ]

# Simulate a router reboot/tmpfs loss before the ESP reports the coin.
rm -rf "$T/run"
mkdir -p "$T/run"
chmod 700 "$T/run"

# Another customer cannot steal vendo-01, but can use vendo-02 concurrently.
DEVICE2=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
export TEST_IP=10.0.0.4 TEST_MAC=02:aa:bb:cc:dd:ee REMOTE_ADDR=10.0.0.4
OUT="$(printf 'action=me&device=%s' "$DEVICE2" | sh "$API")"
echo "$OUT" | grep -q '"ok":true'
OUT="$(printf 'action=coin_start&device=%s&vendo=vendo-01' "$DEVICE2" | sh "$API")"
echo "$OUT" | grep -q 'selected vendo is busy'
OUT="$(printf 'action=coin_start&device=%s&vendo=vendo-02' "$DEVICE2" | sh "$API")"
echo "$OUT" | grep -q '"ok":true'
echo "$OUT" | grep -q '"vendo":"vendo-02"'
OUT="$(printf 'action=coin_stop&device=%s' "$DEVICE2" | sh "$API")"
echo "$OUT" | grep -q '"ok":true'
export TEST_IP=10.0.0.2 TEST_MAC=aa:bb:cc:dd:ee:ff REMOTE_ADDR=10.0.0.2

echo "integration: controller targeting ok"
EVENT=1122334455667788
SIG="$(printf 'vendokey|coin|vendo-01|%s|1|%s|vendokey' "$EVENT" "$TARGET" | sha256sum | awk '{print $1}')"
BODY="action=coin&id=vendo-01&nonce=$EVENT&pulses=1&target=$TARGET&sig=$SIG"
OUT="$(printf '%s' "$BODY" | sh "$VENDO")"
echo "$OUT" | grep -q '"credited_cents":100'
echo "$OUT" | grep -q '"duplicate":false'

OUT="$(printf '%s' "$BODY" | sh "$VENDO")"
echo "$OUT" | grep -q '"duplicate":true'
echo "$OUT" | grep -q '"credited_cents":0'

OUT="$(printf 'action=me&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"credit_cents":100'

BADTARGET=0011223344556677
BADSIG="$(printf 'vendokey|coin|vendo-01|9988776655443322|1|%s|vendokey' "$BADTARGET" | sha256sum | awk '{print $1}')"
OUT="$(printf 'action=coin&id=vendo-01&nonce=9988776655443322&pulses=1&target=%s&sig=%s' "$BADTARGET" "$BADSIG" | sh "$VENDO")"
echo "$OUT" | grep -q 'coin target mismatch'

echo "integration: coin accounting ok"
# A failed close must not say ok while the physical acceptor can still vend.
cat > "$T/bin/rm" <<'RM'
#!/bin/sh
case "${2:-}" in
  */targets/vendo-01.tsv) exit 74;;
esac
exec /bin/rm "$@"
RM
chmod +x "$T/bin/rm"
OUT="$(printf 'action=coin_stop&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'could not close coin window'
[ -f "$T/state/targets/vendo-01.tsv" ]
rm -f "$T/bin/rm"
OUT="$(printf 'action=coin_stop&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"ok":true'
[ ! -e "$T/state/targets/vendo-01.tsv" ]
OUT="$(printf 'action=connect&device=%s&cents=100' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"ok":true'
echo "$OUT" | grep -q '"credit_cents":0'

OUT="$(printf 'action=pause&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"paused":1'
PAUSED="$(printf '%s' "$OUT" | sed -n 's/.*"remaining_seconds":\([0-9]*\).*/\1/p')"
[ "$PAUSED" -gt 0 ]

OUT="$(printf 'action=resume&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"paused":0'

export TEST_IP=10.0.0.3 TEST_MAC=02:11:22:33:44:55 REMOTE_ADDR=10.0.0.3
OUT="$(printf 'action=me&device=%s' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"mac":"02:11:22:33:44:55"'
REMAIN="$(printf '%s' "$OUT" | sed -n 's/.*"remaining_seconds":\([0-9]*\).*/\1/p')"
[ "$REMAIN" -gt 0 ]
[ "$(awk -F '\t' -v d="$DEVICE" '$1==d {c++} END{print c+0}' "$T/state/accounts.tsv")" -eq 1 ]

echo "integration: session rotation ok"
printf 'TESTCODE\t250\n' > "$T/state/vouchers.tsv"
OUT="$(printf 'action=redeem&device=%s&code=TESTCODE' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q '"credit_cents":250'

export TEST_IP=10.0.0.4 TEST_MAC=02:aa:bb:cc:dd:ee REMOTE_ADDR=10.0.0.4
OUT="$(printf 'action=redeem&device=%s&code=TESTCODE' "$DEVICE2" | sh "$API")"
echo "$OUT" | grep -q 'voucher invalid or used'

echo "integration: voucher replay ok"
AUTH="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
LOGIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin-login"
export BP_AUTH_NOW=2000000000 SERVER_PORT=8443
echo "integration: auth provision"
sh "$AUTH" --set-password admin admin 'Integration-Admin-123!'
LOUT="$(printf '%s' 'username=admin&password=Integration-Admin-123%21' | REQUEST_METHOD=POST sh "$LOGIN")"
LERR="$(printf '%s' "$LOUT" | sed -n 's/.*"error":"\([^"]*\)".*/\1/p')"
LUSER="$(printf '%s' "$LOUT" | sed -n 's/.*"username":"\([^"]*\)".*/\1/p')"
echo "integration: auth login => ${LERR:-ok} user=${LUSER:-missing}"
SAFE_LOUT="$(printf '%s\n' "$LOUT" | sed -E 's/(blaze_admin=)[0-9a-f]+/\1<redacted>/g; s/("csrf":")[^"]*/\1<redacted>/g')"
printf '%s\n' "$SAFE_LOUT" | sed 's/^/integration: login-response /'
COOKIE="$(printf '%s\n' "$LOUT" | sed -n 's/^Set-Cookie: \(blaze_admin=[^;]*\).*/\1/p' | tr -d '\r')"
CSRF="$(printf '%s' "$LOUT" | sed -n 's/.*"csrf":"\([^"]*\)".*/\1/p')"
echo "integration: auth material cookie=${COOKIE:+present} csrf=${CSRF:+present}"
[ -n "$COOKIE" ] && [ -n "$CSRF" ]

export SERVER_PORT=8080 HTTP_COOKIE="$COOKIE" HTTP_X_BLAZE_CSRF="$CSRF"
OUT="$(printf 'action=status' | sh "$ADMIN")"
HERR="$(printf '%s' "$OUT" | sed -n 's/.*"error":"\([^"]*\)".*/\1/p')"
echo "integration: http gate => ${HERR:-unclassified}"
echo "$OUT" | grep -q 'requires HTTPS'

export SERVER_PORT=8443
OUT="$(printf 'action=status' | sh "$ADMIN")"
AERR="$(printf '%s' "$OUT" | sed -n 's/.*"error":"\([^"]*\)".*/\1/p')"
echo "integration: authenticated status => ${AERR:-ok}"
echo "$OUT" | grep -q '"ok":true'

echo "integration: admin session ok"

# PAY-0629. Actual portal API: a failed bank-to-session debit or paid voucher
# credit must reject the ACK, leave the existing record unchanged and freeze
# ALL subsequent paid attempts for authenticated operator reconciliation.
export TEST_IP=10.0.0.3 TEST_MAC=02:11:22:33:44:55 REMOTE_ADDR=10.0.0.3
before_money="$(sha256sum "$T/state/accounts.tsv" | cut -d' ' -f1)"
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in
  */accounts.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod +x "$T/bin/mv"
OUT="$(printf 'action=connect&device=%s&cents=100' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'paid account write failed'
echo "$OUT" | grep -q '"ok":false'
[ "$(sha256sum "$T/state/accounts.tsv" | cut -d' ' -f1)" = "$before_money" ]
[ -f "$T/state/paid-state-uncertain" ]
rm -f "$T/bin/mv"
OUT="$(printf 'action=connect&device=%s&cents=100' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'paid state uncertain'

# Simulate an operator resolving this SYNTHETIC ONLY exception to execute a
# separate voucher-storage fault scenario; NEVER clear live uncertainty this way.
rm -f "$T/state/paid-state-uncertain"
printf 'TESTEIO\t250\n' >> "$T/state/vouchers.tsv"
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in
  */accounts.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod +x "$T/bin/mv"
before_voucher="$(sha256sum "$T/state/accounts.tsv" | cut -d' ' -f1)"
OUT="$(printf 'action=redeem&device=%s&code=TESTEIO' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'paid account write failed'
echo "$OUT" | grep -q '"ok":false'
[ "$(sha256sum "$T/state/accounts.tsv" | cut -d' ' -f1)" = "$before_voucher" ]
[ -f "$T/state/paid-state-uncertain" ]
rm -f "$T/bin/mv"
OUT="$(printf 'action=redeem&device=%s&code=TESTEIO' "$DEVICE" | sh "$API")"
echo "$OUT" | grep -q 'paid state uncertain'
[ "$(sha256sum "$T/state/accounts.tsv" | cut -d' ' -f1)" = "$before_voucher" ]

echo 'integration: captive paid connect and voucher storage fault quarantine ok'
echo 'BlazePwifi integration checks passed'
