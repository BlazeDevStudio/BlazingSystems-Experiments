#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *'get blazepwifi.main.durable_sync') echo 0;;
 *'get blazepwifi.main.rental_seconds_per_pulse') echo 600;;
 *'get blazepwifi.main.pulse_value_centavos') echo 100;;
 *'get blazepwifi.main.vendo_port') echo 4455;;
 *'get blazepwifi.main.vendo_key') echo rental-test-vendo-secret;;
 *) exit 1;;
esac
UCI
chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
. "$BP_LIB"; . "$BP_AUTH_LIB"; . "$BP_RENTAL_LIB"; . "$BP_CONTROLLER_LIB"
bp_rental_init

TOKEN="$(bp_rental_enroll_create 'Phone 01' 600)"
EID="${TOKEN%%.*}"
N=abcDEF123
SIG="$(bp_rental_hmac "$TOKEN" "enroll|$N|$TOKEN")"
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
OUT="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s' "$EID" "$N" "$SIG" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUT" | grep -q '"ok":true'
DID="$(printf '%s' "$OUT" | sed -n 's/.*"device_id":"\([^"]*\)".*/\1/p')"
DSEC="$(printf '%s' "$OUT" | sed -n 's/.*"device_secret":"\([^"]*\)".*/\1/p')"
ES="$(printf '%s' "$OUT" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
EL="$(printf '%s' "$OUT" | sed -n 's/.*"lease_until_ms":\([0-9]*\).*/\1/p')"
EG="$(printf '%s' "$OUT" | sed -n 's/.*"enroll_sig":"\([^"]*\)".*/\1/p')"
[ "${#DID}" -eq 24 ]
[ "${#DSEC}" -eq 48 ]
[ -n "$ES" ] && [ "$EL" = "$ES" ]
[ "$EG" = "$(bp_rental_hmac "$TOKEN" "enroll_response|$N|$DID|$DSEC|$ES|$EL|false")" ]

# Simulate a crash after the durable enrollment claim but before the device
# row survives. Retrying with the same nonce must recreate the exact identity.
awk -F '\t' -v d="$DID" '$1!=d {print}' "$BP_RENTAL_DEVICES" > "$T/devices.tmp"
mv "$T/devices.tmp" "$BP_RENTAL_DEVICES"
[ -z "$(bp_rental_device_line "$DID")" ]

OUT2="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s' "$EID" "$N" "$SIG" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUT2" | grep -q '"ok":true'
echo "$OUT2" | grep -q '"reused":true'
DID2="$(printf '%s' "$OUT2" | sed -n 's/.*"device_id":"\([^"]*\)".*/\1/p')"
DSEC2="$(printf '%s' "$OUT2" | sed -n 's/.*"device_secret":"\([^"]*\)".*/\1/p')"
ES2="$(printf '%s' "$OUT2" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
EL2="$(printf '%s' "$OUT2" | sed -n 's/.*"lease_until_ms":\([0-9]*\).*/\1/p')"
EG2="$(printf '%s' "$OUT2" | sed -n 's/.*"enroll_sig":"\([^"]*\)".*/\1/p')"
[ "$DID2" = "$DID" ] && [ "$DSEC2" = "$DSEC" ]
[ -n "$ES2" ] && [ "$EL2" = "$ES2" ]
[ "$EG2" = "$(bp_rental_hmac "$TOKEN" "enroll_response|$N|$DID2|$DSEC2|$ES2|$EL2|true")" ]
[ "$(printf '%s' "$(bp_rental_device_line "$DID")" | cut -f2)" = "$DSEC" ]

# A different request nonce cannot recover or mint credentials from the
# already-claimed one-time token.
NB=def456789
SIGB="$(bp_rental_hmac "$TOKEN" "enroll|$NB|$TOKEN")"
OUTB="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s' "$EID" "$NB" "$SIGB" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUTB" | grep -q 'enrollment already claimed'

bp_rental_policy_ensure "$DID"
bp_rental_admin_password_set "$DID" 'admin-strong-123'
bp_rental_policy_set "$DID" 'com.android.chrome,com.example.game' 'vendo-02'
bp_rental_inventory_write "$DID" 'com.android.chrome,com.example.game,com.example.other'
bp_rental_device_write "$DID" "$DSEC" 2000003600 'Phone 01' 2000000000

N2=stat123
SIG2="$(bp_rental_hmac "$DSEC" "status|$N2|$DSEC")"
OUT="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s&inventory=com.android.chrome%%2Ccom.example.game' "$DID" "$N2" "$SIG2" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUT" | grep -q '"ok":true'
echo "$OUT" | grep -q '"allowed_packages":"com.android.chrome,com.example.game"'
echo "$OUT" | grep -q '"preferred_vendo":"vendo-02"'
echo "$OUT" | grep -q '"admin_salt":"[0-9a-f]'
echo "$OUT" | grep -q '"policy_sig":"[0-9a-f]'
echo "$OUT" | grep -q '"coin_window_expires_ms":0'
echo "$OUT" | grep -q '"coin_window_sig":"[0-9a-f]'

# The first authenticated request using the permanent device secret retires
# the retry record. The original QR token is invalid from this point onward.
[ -z "$(bp_rental_enroll_lookup "$EID")" ]
OUT_AFTER_STATUS="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s' "$EID" "$N" "$SIG" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUT_AFTER_STATUS" | grep -q 'enrollment invalid or used'

# Opening a rental coin window is authenticated, server-timed and recoverable
# through status. The returned reservation state has its own HMAC.
NC=coinopen123
SIGC="$(bp_rental_hmac "$DSEC" "coin_start|$NC|$DSEC")"
COIN="$(printf 'action=coin_start&device_id=%s&nonce=%s&sig=%s' "$DID" "$NC" "$SIGC" | REQUEST_METHOD=POST sh "$CGI")"
echo "$COIN" | grep -q '"ok":true'
echo "$COIN" | grep -q '"vendo":"vendo-02"'
CS="$(printf '%s' "$COIN" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
CE="$(printf '%s' "$COIN" | sed -n 's/.*"expires_ms":\([0-9]*\).*/\1/p')"
CG="$(printf '%s' "$COIN" | sed -n 's/.*"coin_window_sig":"\([^"]*\)".*/\1/p')"
[ -n "$CS" ] && [ -n "$CE" ] && [ "$CE" -gt "$CS" ]
[ "$CG" = "$(bp_rental_hmac "$DSEC" "coin_window|$DID|$CS|$CE|vendo-02|0|0")" ]
[ -f "$BP_TARGET_DIR/vendo-02.tsv" ]
[ -f "$BP_TARGET_DIR/vendo-02.progress" ]
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 0 ]
[ "$(cut -f6 "$BP_TARGET_DIR/vendo-02.tsv")" = rental ]

# Send one signed 2-pulse coin event through the real Vendo CGI, then replay
# the exact same event. Only the first may increase lease/progress.
VENDO_CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
TARGET="$(printf '%s' "$COIN" | sed -n 's/.*"target_nonce":"\([^"]*\)".*/\1/p')"
VN=aabbccdd
VSIG="$(bp_vendo_sig_expected coin vendo-02 "$VN" 2 "$TARGET")"
V1="$(printf 'action=coin&id=vendo-02&nonce=%s&pulses=2&target=%s&sig=%s' "$VN" "$TARGET" "$VSIG" | REQUEST_METHOD=POST SERVER_PORT=4455 sh "$VENDO_CGI")"
echo "$V1" | grep -q '"ok":true'
echo "$V1" | grep -q '"duplicate":false'
echo "$V1" | grep -q '"received_pulses":2'
echo "$V1" | grep -q '"received_cents":200'
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 2 ]

V2="$(printf 'action=coin&id=vendo-02&nonce=%s&pulses=2&target=%s&sig=%s' "$VN" "$TARGET" "$VSIG" | REQUEST_METHOD=POST SERVER_PORT=4455 sh "$VENDO_CGI")"
echo "$V2" | grep -q '"ok":true'
echo "$V2" | grep -q '"duplicate":true'
echo "$V2" | grep -q '"received_pulses":2'
echo "$V2" | grep -q '"received_cents":200'
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 2 ]

# Reopening while active must reuse the exact reservation and preserve progress.
NR=coinretry123
SIGR="$(bp_rental_hmac "$DSEC" "coin_start|$NR|$DSEC")"
REOPEN="$(printf 'action=coin_start&device_id=%s&nonce=%s&sig=%s' "$DID" "$NR" "$SIGR" | REQUEST_METHOD=POST sh "$CGI")"
echo "$REOPEN" | grep -q '"ok":true'
echo "$REOPEN" | grep -q '"reused":true'
echo "$REOPEN" | grep -q '"received_pulses":2'
echo "$REOPEN" | grep -q '"received_cents":200'
RT="$(printf '%s' "$REOPEN" | sed -n 's/.*"target_nonce":"\([^"]*\)".*/\1/p')"
RE="$(printf '%s' "$REOPEN" | sed -n 's/.*"expires_ms":\([0-9]*\).*/\1/p')"
[ "$RT" = "$TARGET" ] && [ "$RE" = "$CE" ]
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 2 ]

NS=coinstatus123
SIGS="$(bp_rental_hmac "$DSEC" "status|$NS|$DSEC")"
COINSTATUS="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$DID" "$NS" "$SIGS" | REQUEST_METHOD=POST sh "$CGI")"
SS="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
SE="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"coin_window_expires_ms":\([0-9]*\).*/\1/p')"
SV="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"coin_window_vendo":"\([^"]*\)".*/\1/p')"
SP="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"coin_received_pulses":\([0-9]*\).*/\1/p')"
SC="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"coin_received_cents":\([0-9]*\).*/\1/p')"
SG="$(printf '%s' "$COINSTATUS" | sed -n 's/.*"coin_window_sig":"\([^"]*\)".*/\1/p')"
[ "$SE" = "$CE" ] && [ "$SV" = vendo-02 ]
[ "$SP" -eq 2 ] && [ "$SC" -eq 200 ]
[ "$SG" = "$(bp_rental_hmac "$DSEC" "coin_window|$DID|$SS|$SE|$SV|$SP|$SC")" ]

NX=coinstop123
SIGX="$(bp_rental_hmac "$DSEC" "coin_stop|$NX|$DSEC")"
STOP="$(printf 'action=coin_stop&device_id=%s&nonce=%s&sig=%s' "$DID" "$NX" "$SIGX" | REQUEST_METHOD=POST sh "$CGI")"
echo "$STOP" | grep -q '"ok":true'
XS="$(printf '%s' "$STOP" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
XP="$(printf '%s' "$STOP" | sed -n 's/.*"received_pulses":\([0-9]*\).*/\1/p')"
XC="$(printf '%s' "$STOP" | sed -n 's/.*"received_cents":\([0-9]*\).*/\1/p')"
XG="$(printf '%s' "$STOP" | sed -n 's/.*"coin_window_sig":"\([^"]*\)".*/\1/p')"
[ "$XP" -eq 2 ] && [ "$XC" -eq 200 ]
[ "$XG" = "$(bp_rental_hmac "$DSEC" "coin_window|$DID|$XS|0||$XP|$XC")" ]
[ ! -f "$BP_TARGET_DIR/vendo-02.tsv" ]
[ ! -f "$BP_TARGET_DIR/vendo-02.progress" ]

# Reset the lease baseline before the lower-level library duplicate test.
bp_rental_device_write "$DID" "$DSEC" 2000003600 'Phone 01' 2000000000
R1="$(bp_rental_apply_coin "$DID" vendo-02 aabbccdd 11223344 2)"
echo "$R1" | grep -q '^credited'
LEASE="$(printf '%s' "$R1" | cut -f2)"
[ "$LEASE" -eq 2000004800 ]

R2="$(bp_rental_apply_coin "$DID" vendo-02 aabbccdd 11223344 2)"
echo "$R2" | grep -q '^duplicate'
[ "$(printf '%s' "$R2" | cut -f2)" -eq "$LEASE" ]

LIST="$(bp_rental_list_json)"
printf '%s' "$LIST" | grep -q '"admin_password_set":true'
printf '%s' "$LIST" | grep -q '"preferred_vendo":"vendo-02"'
printf '%s' "$LIST" | grep -q '"inventory":"com.android.chrome,com.example.game"'

# An expired rental must still be able to synchronize so it can receive a new
# lease later. The server reports lease_until_ms == server_time_ms while
# retaining the expired authoritative lease in state.
bp_rental_device_write "$DID" "$DSEC" 1 'Phone 01' 1
N3=expired123
SIG3="$(bp_rental_hmac "$DSEC" "status|$N3|$DSEC")"
OUT3="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$DID" "$N3" "$SIG3" | REQUEST_METHOD=POST sh "$CGI")"
echo "$OUT3" | grep -q '"ok":true'
S3="$(printf '%s' "$OUT3" | sed -n 's/.*"server_time_ms":\([0-9]*\).*/\1/p')"
L3="$(printf '%s' "$OUT3" | sed -n 's/.*"lease_until_ms":\([0-9]*\).*/\1/p')"
[ -n "$S3" ] && [ "$L3" = "$S3" ]
[ "$(printf '%s' "$(bp_rental_device_line "$DID")" | cut -f3)" -eq 1 ]

# Operator helpers used by the R281 rental deployment profile.
bp_rental_device_rename "$DID" 'Owner Test Phone'
printf '%s' "$(bp_rental_device_line "$DID")" | grep -q 'Owner Test Phone'
ADDED="$(bp_rental_lease_add "$DID" 120)"
[ "$ADDED" -gt "$(bp_now)" ]
# Forfeiting still-active rental credit is an explicit admin settlement,
# never an ordinary one-click expire.
set +e
bp_rental_lease_expire "$DID" > "$T/denied-active-expiry" 2>&1
expire_rc=$?
set -e
[ "$expire_rc" -eq 6 ]
EXPIRED="$(bp_rental_lease_expire "$DID" CONFIRM_FORFEIT)"
[ "$EXPIRED" -le "$(bp_now)" ]
EVENTS="$(bp_rental_events_json 16)"
printf '%s' "$EVENTS" | grep -q '"kind":"rename"'
printf '%s' "$EVENTS" | grep -q '"kind":"lease_add"'
printf '%s' "$EVENTS" | grep -q '"kind":"expire"'

# RENT-0688: inject a real signed coin request after the lease+receipt
# succeeded but a private window progress rename fails. It MUST NOT get
# a success ACK and further payments MUST be frozen for reconciliation.
NC4=progressfail123
SIG4="$(bp_rental_hmac "$DSEC" "coin_start|$NC4|$DSEC")"
START4="$(printf 'action=coin_start&device_id=%s&nonce=%s&sig=%s' "$DID" "$NC4" "$SIG4" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$START4" | grep -q '"ok":true'
TARGET4="$(printf '%s' "$START4" | sed -n 's/.*"target_nonce":"\([^"]*\)".*/\1/p')"
[ -n "$TARGET4" ]
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 0 ]
before_lease="$(bp_rental_device_line "$DID" | cut -f3)"
before_receipts="$(wc -l < "$BP_RENTAL_EVENTS")"
cat > "$T/bin/mv" <<'PROGRESS_EIO'
#!/bin/sh
# For this disposable test ONLY, fail the final progress replacement;
# all other real rent/member/pending journal renames continue normally.
case "$2" in *.progress) exit 74;; esac
exec /bin/mv "$@"
PROGRESS_EIO
chmod 700 "$T/bin/mv"
VN4=feedbeef
SIGV4="$(bp_vendo_sig_expected coin vendo-02 "$VN4" 1 "$TARGET4")"
FAIL4="$(printf 'action=coin&id=vendo-02&nonce=%s&pulses=1&target=%s&sig=%s' "$VN4" "$TARGET4" "$SIGV4" | REQUEST_METHOD=POST SERVER_PORT=4455 sh "$VENDO_CGI")"
printf '%s' "$FAIL4" | grep -q '"ok":false'
printf '%s' "$FAIL4" | grep -q 'rental progress commit failed'
[ "$(bp_rental_device_line "$DID" | cut -f3)" -gt "$before_lease" ]
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq $((before_receipts+1)) ]
[ "$(cat "$BP_TARGET_DIR/vendo-02.progress")" -eq 0 ]
[ -f "$BP_STATE/paid-state-uncertain" ]
RETRY4="$(printf 'action=coin&id=vendo-02&nonce=%s&pulses=1&target=%s&sig=%s' "$VN4" "$TARGET4" "$SIGV4" | REQUEST_METHOD=POST SERVER_PORT=4455 sh "$VENDO_CGI")"
printf '%s' "$RETRY4" | grep -q '"ok":false'
printf '%s' "$RETRY4" | grep -q 'paid state uncertain'
[ "$(wc -l < "$BP_RENTAL_EVENTS")" -eq $((before_receipts+1)) ]
echo 'RENT-0688 PASS: signed post-credit progress EIO never ACKs and halts retries for reconciliation'

echo "BlazeRental production server checks passed"
