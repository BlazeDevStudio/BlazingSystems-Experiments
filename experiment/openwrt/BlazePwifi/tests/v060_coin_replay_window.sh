#!/bin/sh
# PAY-0630: signed physical-controller ACK replay despite legacy history rollover.
# Synthetic tempfs only; no connected coin acceptor or real customer accounts.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-coin-replay-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo synthetic-vendo-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *'get blazepwifi.main.lan_if') echo br-lan;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/ip" <<'IP'
#!/bin/sh
echo "10.0.0.9 dev br-lan lladdr aa:bb:cc:dd:ee:ff REACHABLE"
IP
chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
DEVICE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TARGET=1122334455667788
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
API="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/api"
NOW="$(date +%s)"
EXPIRES=$((NOW+600))
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_STATE/accounts.tsv"
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\thotspot\n' "$DEVICE" "$TARGET" "$EXPIRES" > "$BP_STATE/targets/vendo-01.tsv"
credit() { awk -F '\t' -v d="$DEVICE" '$1==d {print $2;exit}' "$BP_STATE/accounts.tsv"; }
coin_count() {
  awk -F '\t' '$1!="" {n=split($9,a,","); for(i=1;i<=n;i++) if(a[i] ~ /^c:/) c++} END{print c+0}' "$BP_STATE/accounts.tsv"
}
send_coin() {
    n="$1"
    proof="$(printf 'synthetic-vendo-secret|coin|vendo-01|%s|1|%s|synthetic-vendo-secret' "$n" "$TARGET" | sha256sum | cut -d' ' -f1)"
    printf 'action=coin&id=vendo-01&nonce=%s&pulses=1&target=%s&sig=%s' "$n" "$TARGET" "$proof" | sh "$VENDO"
}
i=1
while [ "$i" -le 12 ]; do
    nonce="$(printf '%016x' "$i")"
    result="$(send_coin "$nonce")"
    printf '%s' "$result" | grep -q '"ok":true'
    printf '%s' "$result" | grep -q '"duplicate":false'
    i=$((i+1))
done
[ "$(credit)" = 1300 ]
[ "$(coin_count)" -ge 12 ] || {
    echo 'P0 old valid coin ID was prematurely evicted' >&2; exit 1;
}

# Voucher flow must also preserve live coin receipts (not only next coin ACK).
printf 'LIVECOUPON\t50\n' > "$BP_STATE/vouchers.tsv"
result="$(printf 'action=redeem&device=%s&code=LIVECOUPON' "$DEVICE" | sh "$API")"
printf '%s' "$result" | grep -q '"credit_cents":1350'
[ "$(coin_count)" -ge 12 ]
replay="$(send_coin 0000000000000001)"
printf '%s' "$replay" | grep -q '"duplicate":true'
printf '%s' "$replay" | grep -q '"credited_cents":0'
[ "$(credit)" = 1350 ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]

# Once the original physical window has expired, old receipt display history
# is permitted to compact because that nonce can no longer be accepted.
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\thotspot\n' "$DEVICE" "$TARGET" "$((NOW-1))" > "$BP_STATE/targets/vendo-01.tsv"
printf 'AFTEREXPIRE\t50\n' >> "$BP_STATE/vouchers.tsv"
result="$(printf 'action=redeem&device=%s&code=AFTEREXPIRE' "$DEVICE" | sh "$API")"
printf '%s' "$result" | grep -q '"credit_cents":1400'
[ "$(coin_count)" -le 8 ] || {
    echo 'expired receipts were not bounded' >&2; exit 1;
}
expired="$(send_coin 0000000000000001)"
printf '%s' "$expired" | grep -q 'coin window expired'
[ "$(credit)" = 1400 ]
echo 'PAY-0630 synthetic signed-coin replay PASS: 12 live receipts retained beyond legacy 8, voucher preserves active proofs, old retry did not double-credit, expired IDs compact'
echo 'NOT PRODUCTION: legacy v1 historical random receipts require quiesced migration, atomic money journal and real hardware interruption proof'
