#!/bin/sh
# PAY-0732: REAL signed Full Vendo CGI in isolated /tmp fixture only.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0732-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf 'BLAZE-PAY-0732-SYNTHETIC-ONLY\n' > "$T/.lab"
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo pay0732-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
DEVICE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TARGET=1122334455667788
NOW="$(date +%s)"
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_STATE/accounts.tsv"
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\thotspot\n' "$DEVICE" "$TARGET" "$((NOW+600))" > "$BP_STATE/targets/vendo-01.tsv"
send_coin() {
  nonce="$1"; pulses="$2"; destination="${3:-$TARGET}"
  sig="$(printf 'pay0732-secret|coin|vendo-01|%s|%s|%s|pay0732-secret' "$nonce" "$pulses" "$destination" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s' "$nonce" "$pulses" "$destination" "$sig" | sh "$VENDO"
}
credit() { awk -F '\t' '$1=="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" {print $2}' "$BP_STATE/accounts.tsv"; }
events() { awk -F '\t' '$1=="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" {print $9}' "$BP_STATE/accounts.tsv"; }
# Verify the real signed CGI rejects an unknown/unprovisioned controller
# without changing even one byte of the account. Enable only this /tmp lab.
pre_sha="$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)"
unprovisioned="$(send_coin deadbeefdeadbeef 2)"
printf '%s' "$unprovisioned" | grep -Fq '"ok":false'
printf '%s' "$unprovisioned" | grep -Fq 'controller disabled or coin intake disabled'
[ "$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)" = "$pre_sha" ]
REQUEST_METHOD=GET
. "$BP_LIB"
. "$BP_CONTROLLER_LIB"
REQUEST_METHOD=POST
bp_controller_ensure vendo-01
if bp_controller_paid_allowed vendo-01 coin; then
  echo 'PAY-0732 invalid fixture: default-deny bypassed' >&2; exit 2
fi
bp_controller_set vendo-01 1 1 1 1 -1 -1 -1 1 1 1 40 400 6
bp_controller_paid_allowed vendo-01 coin || {
  echo 'PAY-0732 invalid fixture: explicit disposable provision failed' >&2; exit 2
}
echo 'PAY-0732 UNPROVISIONED-DENY-PASS: account bytes preserved'
orig="$(send_coin 0102030405060708 2)"
printf '%s' "$orig" | grep -Fq '"duplicate":false'
[ "$(credit)" = 300 ] && printf '%s' "$(events)" | grep -Fq '!2'
again="$(send_coin 0102030405060708 2)"
printf '%s' "$again" | grep -Fq '"duplicate":true'
[ "$(credit)" = 300 ]
# PAY-0733: the same authenticated controller nonce+target must never ACK
# another device when an operator reselects the live target entry.
# Every fault below is synthetic and must leave the paid account bytes intact.
deny_old_receipt() {
  tag="$1"
  before="$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)"
  reply="$(send_coin 0102030405060708 2)"
  printf '%s' "$reply" | grep -Fq '"ok":false' || {
    echo "PAY-0733 false success ACK: $tag: $reply" >&2; exit 1
  }
  [ "$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)" = "$before" ] || {
    echo "PAY-0733 changed paid balance/receipt during $tag" >&2; exit 1
  }
}
OTHER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
cp "$BP_STATE/targets/vendo-01.tsv" "$T/target-good"
cp "$BP_STATE/accounts.tsv" "$T/accounts-good"
printf '%s\t0\t0\t0\t0\t0\taa:bb:cc:dd:ee:00\t10.0.0.10\t\n' "$OTHER" >> "$BP_STATE/accounts.tsv"
printf '%s\taa:bb:cc:dd:ee:00\t%s\t%s\tvendo-01\thotspot\n' "$OTHER" "$TARGET" "$((NOW+600))" > "$BP_STATE/targets/vendo-01.tsv"
deny_old_receipt reselected-window-different-device
cp "$T/target-good" "$BP_STATE/targets/vendo-01.tsv"
# A corrupt unrelated account, duplicate account identity, duplicated receipt
# or malformed credited balance cannot become a success ACK via first-match.
printf 'corrupt-row\n' >> "$BP_STATE/accounts.tsv"
deny_old_receipt corrupt-unrelated-account
cp "$T/accounts-good" "$BP_STATE/accounts.tsv"
cat "$T/accounts-good" >> "$BP_STATE/accounts.tsv"
deny_old_receipt duplicated-paid-account
cp "$T/accounts-good" "$BP_STATE/accounts.tsv"
printf '%s\t0\t0\t0\t0\t0\taa:bb:cc:dd:ee:00\t10.0.0.10\t%s\n' "$OTHER" "$(events)" >> "$BP_STATE/accounts.tsv"
deny_old_receipt duplicate-receipt-on-other-account
cp "$T/accounts-good" "$BP_STATE/accounts.tsv"
sed 's/\t300\t/\tNaN\t/' "$T/accounts-good" > "$BP_STATE/accounts.tsv"
deny_old_receipt malformed-credit-on-receipt-owner
cp "$T/accounts-good" "$BP_STATE/accounts.tsv"
[ "$(send_coin 0102030405060708 2 | grep -o '"duplicate":true')" = '"duplicate":true' ]
changed="$(send_coin 0102030405060708 3)"
printf '%s' "$changed" | grep -Fq '"ok":false'
printf '%s' "$changed" | grep -Fq 'coin pulse payload collision'
[ "$(credit)" = 300 ]
wrong_target="$(send_coin 0102030405060708 2 8888777766665555)"
printf '%s' "$wrong_target" | grep -Fq '"ok":false'
[ "$(credit)" = 300 ]
# Synthetic legacy unsuffixed event carries no original quantity; never
# infer 2 (or silently treat the nonce as fresh) after old snapshot restore.
sed 's/!2//g' "$BP_STATE/accounts.tsv" > "$T/old-account"
mv "$T/old-account" "$BP_STATE/accounts.tsv"
before="$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)"
legacy="$(send_coin 0102030405060708 2)"
printf '%s' "$legacy" | grep -Fq '"ok":false'
[ "$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)" = "$before" ]
# 12 active-window receipts must survive UI retention=8.
sed -i 's/!2/!2/' "$BP_STATE/accounts.tsv"
# Test fresh different nonces with varying signed original pulse counts.
for n in 1111111111111101 1111111111111102 1111111111111103 1111111111111104 1111111111111105 1111111111111106 1111111111111107 1111111111111108 1111111111111109 1111111111111110 1111111111111111 1111111111111112; do
  response="$(send_coin "$n" 1)"
  printf '%s' "$response" | grep -Fq '"duplicate":false'
done
replay="$(send_coin 1111111111111101 1)"
printf '%s' "$replay" | grep -Fq '"duplicate":true'
echo 'PAY-0732 PASS: signed ordinary coin original pulses bound to same paid account row; changed replay denied, old legacy ambiguous ACK denied, active window retained'
echo 'PAY-0733 PASS: signed coin old receipts cannot ACK a reselected device, duplicate/invalid account rows, duplicated receipts or malformed paid balance'
echo 'NOT v2: real authenticated atomic witness-gated journal, physical hardware, P-256 and release still blocked'
