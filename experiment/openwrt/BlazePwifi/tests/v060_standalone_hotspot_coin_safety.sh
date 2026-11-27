#!/bin/sh
# HOTSPOT-0654: signed R281 standalone nonrental coin CGI under synthetic IO.
# No real coins, customers, secrets or installed devices.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-hotspot-XXXXXX)"
stage=setup
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "HOTSPOT-0654 failed at $stage (rc=$rc)" >&2; fi; rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo disposable-r281-hotspot-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh" BP_RENTAL_LIB="$LIB/rental.sh"
export BP_CONTROLLER_LIB="$LIB/controller.sh"
export REQUEST_METHOD=GET SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
bp_rental_init
DEVICE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TARGET=1122334455667788
VENDO="$ROOT/profiles/r281-rental/root/www/cgi-bin/vendo"
NOW="$(bp_now)"
EXPIRES=$((NOW+900))
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_ACCOUNTS"
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\thotspot\n' "$DEVICE" "$TARGET" "$EXPIRES" > "$BP_TARGET_DIR/vendo-01.tsv"
chmod 600 "$BP_ACCOUNTS" "$BP_TARGET_DIR/vendo-01.tsv"
balance() { awk -F '\t' -v d="$DEVICE" '$1==d {print $2;exit}' "$BP_ACCOUNTS"; }
moneysha() { sha256sum "$BP_ACCOUNTS" | cut -d' ' -f1; }
coin_count() {
  awk -F '\t' -v d="$DEVICE" '$1==d {n=split($9,a,",");for(i=1;i<=n;i++) if(a[i] ~ /^c:/) c++} END{print c+0}' "$BP_ACCOUNTS"
}
send_coin() {
  n="$1"; pulses="$2"
  sig="$(printf 'disposable-r281-hotspot-secret|coin|vendo-01|%s|%s|%s|disposable-r281-hotspot-secret' "$n" "$pulses" "$TARGET" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s' "$n" "$pulses" "$TARGET" "$sig" |
    REQUEST_METHOD=POST sh "$VENDO"
}
stage=normal-12-physical-events-beyond-history-8
i=1
while [ "$i" -le 12 ]; do
  nonce="$(printf '%016x' "$i")"
  out="$(send_coin "$nonce" 1)"
  printf '%s' "$out" | grep -q '"ok":true'
  printf '%s' "$out" | grep -q '"duplicate":false'
  i=$((i+1))
done
[ "$(balance)" -eq 1300 ]
[ "$(coin_count)" -ge 12 ] || { echo 'active coin proofs trimmed while target still live' >&2;exit 1; }
[ ! -e "$BP_PAID_UNCERTAIN" ]

stage=oldest-replay
before="$(moneysha)"
replay="$(send_coin 0000000000000001 1)"
printf '%s' "$replay" | grep -q '"duplicate":true'
printf '%s' "$replay" | grep -q '"credited_cents":0'
[ "$(moneysha)" = "$before" ]

stage=oldest-amount-collision
collision="$(send_coin 0000000000000001 2)"
printf '%s' "$collision" | grep -q '"ok":false'
printf '%s' "$collision" | grep -q 'coin receipt pulse collision'
[ "$(moneysha)" = "$before" ]

# Normal signed cash event fails an injected rename; no successful credited
# ACK and no balance mutation, with persistent operator reconciliation.
stage=failed-financial-rename
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */accounts.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
failed="$(send_coin 0000000000000013 1)"
printf '%s' "$failed" | grep -q '"ok":false'
printf '%s' "$failed" | grep -q 'operator reconciliation required'
[ "$(moneysha)" = "$before" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true
stage=unsafe-retry-refused
retry="$(send_coin 0000000000000013 1)"
printf '%s' "$retry" | grep -q '"ok":false'
printf '%s' "$retry" | grep -q 'operator reconciliation required'
[ "$(moneysha)" = "$before" ]

stage=physical-controller-poll-stopped
pollsig="$(printf 'disposable-r281-hotspot-secret|poll|vendo-01|3132333435363738|0||disposable-r281-hotspot-secret' | sha256sum | cut -d' ' -f1)"
poll="$(printf 'action=poll&id=vendo-01&nonce=3132333435363738&pulses=0&sig=%s' "$pollsig" | REQUEST_METHOD=POST sh "$VENDO")"
printf '%s' "$poll" | grep -q '"insert":0'
[ "$(balance)" -eq 1300 ]

echo 'HOTSPOT-0654 PASS: R281 signed hotspot cash ledger retains 12 live receipts with history limit 8, refuses oldest replay changed pulses and storage false ACK, quarantines and disables controller'
echo 'NOT production: multi-file v1 paid state not fsync-atomic; hardware coin/powercut, owner signer and source migration P0'
