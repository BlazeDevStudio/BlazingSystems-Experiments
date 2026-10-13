#!/bin/sh
# PAY-0741: reuse real signed CGI fixture then fault both money branches.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
. "$ROOT/tests/v060_vendo_coin_pulse_replay.sh"
# The sourced script supplies a private 0700 /tmp state, real signed
# send_coin(), account fixture and cleanup trap, never customer accounts.
export PAY0741_UNIT_FILE="$T/coin-unit"
printf '100\n' > "$PAY0741_UNIT_FILE"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo pay0732-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') cat "$PAY0741_UNIT_FILE";;
  *'get blazepwifi.main.rental_seconds_per_pulse') echo 600;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
money_sha() {
  sha256sum "$BP_STATE/accounts.tsv" "$BP_STATE/member-events.tsv" \
    "$BP_STATE/rental-devices.tsv" "$BP_STATE/rental-events.tsv" |
    awk '{print $1}'
}
deny_no_credit() {
  label="$1"; nonce="$2"; count="$3"
  before="$(money_sha)"
  reply="$(send_coin "$nonce" "$count")" || {
    echo "PAY-0741 $label CGI crashed before clean rejection" >&2; exit 1
  }
  printf '%s' "$reply" | grep -Fq '"ok":false' || {
    echo "PAY-0741 UNSAFE $label positive ACK: $reply" >&2; exit 1
  }
  [ "$(money_sha)" = "$before" ] || {
    echo "PAY-0741 UNSAFE $label changed paid balance/receipt" >&2; exit 1
  }
  [ ! -e "$BP_STATE/paid-state-uncertain" ] || exit 1
}
# Reset only synthetic account row from the already tested signed fixture.
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_STATE/accounts.tsv"
for val in 08 000100 -7 0 bad 2147483648 1073741824; do
  printf '%s\n' "$val" > "$PAY0741_UNIT_FILE"
  deny_no_credit "hotspot-rate-$val" 9999999999999901 2
done
# Individually in-range 2147483647 cents still overflows when
# added to an existing positive bank balance (1 signed pulse).
printf '2147483647\n' > "$PAY0741_UNIT_FILE"
deny_no_credit hotspot-addition-overflow 9999999999999907 1
printf '100\n' > "$PAY0741_UNIT_FILE"
for bad in 08 01 00 21 0000000001; do
  deny_no_credit "hotspot-pulses-$bad" 9999999999999902 "$bad"
done
for balance in 08 2147483648 2147483640; do
  printf '%s\t%s\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" "$balance" > "$BP_STATE/accounts.tsv"
  deny_no_credit "hotspot-bank-$balance" 9999999999999903 1
done
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$DEVICE" > "$BP_STATE/accounts.tsv"
good="$(send_coin 9999999999999904 2)"
printf '%s' "$good" | grep -Fq '"duplicate":false'
[ "$(credit)" = 300 ]
# Real rental paid entrypoint: invalid progress/rate must reject BEFORE lease
# credit, receipt append, partial progress or any success response.
RENTAL=rent01
printf '%s\taa:bb:cc:dd:ee:ff\t%s\t%s\tvendo-01\trental\n' "$RENTAL" "$TARGET" "$((NOW+600))" > "$BP_STATE/targets/vendo-01.tsv"
printf '%s\ttest-only-secret\t0\tFixture Rental\t0\n' "$RENTAL" > "$BP_STATE/rental-devices.tsv"
printf '0\n' > "$BP_STATE/targets/vendo-01.progress"
rental_ok="$(send_coin 9999999999999910 1)"
printf '%s' "$rental_ok" | grep -Fq '"received_cents":100'
[ "$(cat "$BP_STATE/targets/vendo-01.progress")" = 1 ]
for val in 08 000100 -7 0 bad 2147483648 2147483647; do
  printf '%s\n' "$val" > "$PAY0741_UNIT_FILE"
  deny_no_credit "rental-rate-$val" 9999999999999911 1
  [ "$(cat "$BP_STATE/targets/vendo-01.progress")" = 1 ]
done
printf '100\n' > "$PAY0741_UNIT_FILE"
for progress in 08 000001 bad 2147483648 1000000; do
  printf '%s\n' "$progress" > "$BP_STATE/targets/vendo-01.progress"
  deny_no_credit "rental-progress-$progress" 9999999999999912 1
  [ "$(cat "$BP_STATE/targets/vendo-01.progress")" = "$progress" ]
done
echo 'PAY-0741 PASS: actual signed coin and rental paths reject malformed, octal and overflow inputs before prepaid mutation/ACK'
echo 'NOT v2: atomic journal, independent witness and owner physical signing acceptance are still unverified'
