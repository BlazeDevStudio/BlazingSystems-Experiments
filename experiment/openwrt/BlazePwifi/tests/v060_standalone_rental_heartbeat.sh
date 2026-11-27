#!/bin/sh
# RENT-0651: R281 standalone actual signed status must not overwrite paid time.
# Fictional secrets and accounts only, disposable /tmp, NOT physical router.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-status-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *'get blazepwifi.main.durable_sync') echo 0;;
 *'get blazepwifi.main.rental_seconds_per_pulse') echo 600;;
 *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh" BP_RENTAL_LIB="$LIB/rental.sh"
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
bp_rental_init
D=0123456789abcdef01234567
S=00112233445566778899aabbccddeeff0011223344556677
now="$(bp_now)"
lease1=$((now+480))
bp_rental_device_write "$D" "$S" "$lease1" "Standalone test" 123
bp_rental_policy_ensure "$D"
CGI="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental"
hashpaid() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }
paid() { printf '%s' "$(bp_rental_device_line "$D")" | cut -f3; }
send_status() {
  nonce="$1"
  sig="$(bp_rental_hmac "$S" "status|$nonce|$S")"
  printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$D" "$nonce" "$sig" |
    REQUEST_METHOD=POST sh "$CGI"
}
before="$(hashpaid)"
out="$(send_status noncea)"
printf '%s' "$out" | grep -q '"ok":true'
printf '%s' "$out" | grep -Fq "\"lease_until_ms\":$((lease1*1000))"
[ "$(hashpaid)" = "$before" ] || { echo 'standalone status wrote paid lease' >&2;exit 1; }
[ -f "$BP_RUN/rental-last-seen/$D" ]
seen="$(cat "$BP_RUN/rental-last-seen/$D")"
case "$seen" in ''|*[!0-9]*) echo 'invalid presence timestamp' >&2;exit 1;; esac
listing="$(bp_rental_list_json)"
printf '%s' "$listing" | grep -Fq "\"last_seen\":$seen"

# Break every rename into the PAID file. A status must have zero dependence
# on monetary writes, and cannot double-spend or undo a coin increment.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */rental-devices.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
before="$(hashpaid)"
out="$(send_status nonceb)"
printf '%s' "$out" | grep -q '"ok":true'
[ "$(hashpaid)" = "$before" ] && [ "$(paid)" = "$lease1" ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true

# After a credited coin event, the next HMAC status must show exactly the
# latest authoritative lease without resetting paid time to the older value.
lease2=$((now+1780))
bp_rental_device_write "$D" "$S" "$lease2" "Standalone test" 123
before="$(hashpaid)"
out="$(send_status noncec)"
printf '%s' "$out" | grep -Fq "\"lease_until_ms\":$((lease2*1000))"
[ "$(hashpaid)" = "$before" ]
[ "$(paid)" = "$lease2" ]

# Standalone copy now rejects corrupt and duplicated paid source data.
printf '%s\t%s\t%s\tX\t111\n' "$D" "$S" "$lease2" >> "$BP_RENTAL_DEVICES"
before="$(hashpaid)"
set +e
bp_rental_device_write "$D" "$S" "$lease2" "Overwrite" 111 >"$T/rejected" 2>&1
rc=$?
set -e
[ "$rc" -eq 8 ] && [ "$(hashpaid)" = "$before" ]

# No volatile heartbeat file? Admin uses legacy last_seen field as fallback.
sed '$d' "$BP_RENTAL_DEVICES" > "$T/restored"
cp "$T/restored" "$BP_RENTAL_DEVICES"
rm "$BP_RUN/rental-last-seen/$D"
listing="$(bp_rental_list_json)"
printf '%s' "$listing" | grep -Fq '"last_seen":123'

echo 'RENT-0651 standalone R281 signed-CGI PASS: paid file unchanged by status, failed paid rename isolated, latest lease reflected, admin list volatile presence and duplicate paid record refusal'
echo 'NOT PRODUCTION: v2 authenticated money journal, original Android signer and physical R281 hardware powercut validation pending'
