#!/bin/sh
# RENT-0650: signed Android rental status must NEVER rewrite paid lease rows.
# Synthetic /tmp data and fixture secrets only. No phones/customer credits.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-status-heartbeat-XXXXXX)"
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
LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh"
export BP_RENTAL_LIB="$LIB/rental.sh" BP_RENTAL_POLICY_LIB="$LIB/rental_policy.sh"
export BP_RENTAL_POLICY_V2="$BP_STATE/rental-policy-v2.tsv"
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
. "$BP_RENTAL_POLICY_LIB"
bp_rental_init
bp_rental_policy_v2_init
D=0123456789abcdef01234567
S=00112233445566778899aabbccddeeff0011223344556677
now="$(bp_now)"
original_lease=$((now+400))
bp_rental_device_write "$D" "$S" "$original_lease" "Synthetic Android phone" 123
bp_rental_policy_ensure "$D"
bp_rental_policy_migrate "$D"
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
checksum() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }
lease() { printf '%s' "$(bp_rental_device_line "$D")" | cut -f3; }
send_status() {
  nonce="$1"
  signature="$(bp_rental_hmac "$S" "status|$nonce|$S")"
  printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$D" "$nonce" "$signature" |
    REQUEST_METHOD=POST sh "$CGI"
}
before="$(checksum)"
out="$(send_status firstnonce)"
printf '%s' "$out" | grep -q '"ok":true'
printf '%s' "$out" | grep -Fq "\"lease_until_ms\":$((original_lease*1000))"
[ "$(checksum)" = "$before" ] || {
  echo 'P0 Android heartbeat changed authoritative paid lease file' >&2;exit 1;
}
seen_file="$BP_RUN/rental-last-seen/$D"
[ -f "$seen_file" ] && [ ! -L "$seen_file" ] || {
  echo 'volatile private rental heartbeat missing' >&2;exit 1;
}
seen="$(cat "$seen_file")"
case "$seen" in ''|*[!0-9]*) echo 'bad volatile heartbeat timestamp' >&2;exit 1;; esac
[ "$seen" -ge "$now" ] && [ "$seen" -le "$(bp_now)" ]
listing="$(bp_rental_list_json)"
printf '%s' "$listing" | grep -Fq "\"last_seen\":$seen"

# Even if *every* attempt to replace the PAID database now fails, a phone
# status heartbeat has no business touching that file and must still work.
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in
  */rental-devices.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
[ "$(command -v mv)" = "$T/bin/mv" ]
before="$(checksum)"
out="$(send_status aftercreditnonce)"
printf '%s' "$out" | grep -q '"ok":true'
[ "$(checksum)" = "$before" ]
[ "$(lease)" = "$original_lease" ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true

# Another signed paid event externally changes lease while Android is
# checking in. The following signed status must see the NEW server balance,
# not reapply the original cached lease.
credited_lease=$((now+1600))
bp_rental_device_write "$D" "$S" "$credited_lease" "Synthetic Android phone" 123
before="$(checksum)"
out="$(send_status currentnonce)"
printf '%s' "$out" | grep -q '"ok":true'
printf '%s' "$out" | grep -Fq "\"lease_until_ms\":$((credited_lease*1000))"
[ "$(checksum)" = "$before" ] && [ "$(lease)" = "$credited_lease" ]

# A poisoned presence-file symlink must never be followed or be mistaken
# for paid credit; status refuses, the trusted paid lease stays untouched.
rm "$seen_file"
printf '999\n' > "$T/poison"
ln -s "$T/poison" "$seen_file"
before="$(checksum)"
out="$(send_status poisonednonce)"
printf '%s' "$out" | grep -q '"ok":false'
printf '%s' "$out" | grep -q 'rental presence update failed'
[ "$(checksum)" = "$before" ]
[ "$(cat "$T/poison")" = 999 ]
rm "$seen_file"

# Restart/cleared /tmp presence must fall back to original saved last_seen.
listing="$(bp_rental_list_json)"
printf '%s' "$listing" | grep -Fq '"last_seen":123'
echo 'RENT-0650 signed Android CGI PASS: status cannot overwrite paid lease, survives paid store rename EIO, reports current credited balance and private volatile heartbeat in admin list'
echo 'NOT PRODUCTION: handset OEM, physical powercut and crash-atomic v2 authoritative journal still block 0.6'
