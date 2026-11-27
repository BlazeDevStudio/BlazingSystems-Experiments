#!/bin/sh
# PAY-0627: real vendo CGI under synthetic filesystem/injected storage EIO.
# NO physical coins, no customer router state and no operator-key material.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-coin-fail-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/state/targets" "$T/run" "$T/bin"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo synthetic-vendo-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${MVMODE:-ok}:${2:-}" in
  fail:*/accounts.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/"*
export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.0.0.9
export MVMODE=ok
DEVICE=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
TARGET=1122334455667788
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
NOW="$(date +%s)"
EXPIRES=$((NOW+240))
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_STATE/accounts.tsv"
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\thotspot\n' "$DEVICE" "$TARGET" "$EXPIRES" > "$BP_STATE/targets/vendo-01.tsv"
credit() { awk -F '\t' -v d="$DEVICE" '$1==d {print $2; exit}' "$BP_STATE/accounts.tsv"; }
send_coin() {
  nonce="$1"
  signature="$(printf 'synthetic-vendo-secret|coin|vendo-01|%s|1|%s|synthetic-vendo-secret' "$nonce" "$TARGET" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=1&target=%s&sig=%s' "$nonce" "$TARGET" "$signature" | sh "$VENDO"
}

# Positive baseline: the CGI really applies and ACKs a valid signed pulse.
first="$(send_coin 0102030405060708)"
printf '%s' "$first" | grep -q '"ok":true'
printf '%s' "$first" | grep -q '"duplicate":false'
[ "$(credit)" = 200 ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
replay="$(send_coin 0102030405060708)"
printf '%s' "$replay" | grep -q '"duplicate":true'
[ "$(credit)" = 200 ]

# Fail the exact rename of accounts.tsv, but allow the earlier paid-halt
# marker rename to succeed. A false "ok:true" would represent lost paid money.
export MVMODE=fail
before="$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)"
failed="$(send_coin 1112131415161718)"
printf '%s' "$failed" | grep -q '"ok":false'
if printf '%s' "$failed" | grep -q '"ok":true'; then
  echo 'P0 FALSE ACK after failed financial rename' >&2; exit 1
fi
[ "$(sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1)" = "$before" ] || {
  echo 'failed rename mutated synthetic credited balance' >&2; exit 1;
}
[ "$(credit)" = 200 ]
[ -f "$BP_STATE/paid-state-uncertain" ] || {
  echo 'P0 missing uncertain-paid-state quarantine marker' >&2; exit 1;
}

# Even if the storage error disappears, an ordinary retry MUST NOT ACK as
# successful until the uncertain marker has been reconciled by an operator.
export MVMODE=ok
retry="$(send_coin 1112131415161718)"
printf '%s' "$retry" | grep -q '"ok":false'
printf '%s' "$retry" | grep -q 'operator reconciliation required'
[ "$(credit)" = 200 ]
[ -f "$BP_STATE/paid-state-uncertain" ]

echo 'PAY-0627 ordinary signed coin CGI PASS: normal ACK and replay, failed rename NO ACK, unchanged money, persistent quarantine and blocked retry'
echo 'NOT crash-atomic production: bounded legacy coin receipt history, fsync/power-loss and genuine v2 migration still block release'
