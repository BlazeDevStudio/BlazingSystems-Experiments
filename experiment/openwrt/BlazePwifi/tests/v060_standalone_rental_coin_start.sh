#!/bin/sh
# RENT-0653: real standalone R281 signed Android coin_start must retain the
# controller target nonce across retries and refuse storage false readiness.
# Synthetic state and fake device secrets only; no live router or coins.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-coinstart-XXXXXX)"
stage=prepare
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "RENT-0653 failed at $stage (rc=$rc)" >&2; fi; rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.coin_window') echo 120;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh" BP_RENTAL_LIB="$LIB/rental.sh"
# Common.sh loads POST stdin when sourced. This setup is not yet a request.
export REQUEST_METHOD=GET REMOTE_ADDR=10.0.0.9
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
bp_rental_init
CGI="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental"
D1=0123456789abcdef01234567
D2=abcdef0123456789abcdef01
S1=00112233445566778899aabbccddeeff0011223344556677
S2=ffeeddccbbaa99887766554433221100ffeeddccbbaa9988
now="$(bp_now)"
bp_rental_device_write "$D1" "$S1" "$((now+300))" "R281 fake rental A" 0
bp_rental_device_write "$D2" "$S2" "$((now+300))" "R281 fake rental B" 0
target_file="$BP_TARGET_DIR/vendo-01.tsv"
send_start() {
  did="$1"; key="$2"; n="$3"
  sig="$(bp_rental_hmac "$key" "coin_start|$n|$key")"
  printf 'action=coin_start&device_id=%s&nonce=%s&sig=%s&vendo=vendo-01' "$did" "$n" "$sig" |
    REQUEST_METHOD=POST sh "$CGI"
}
target_sha() { sha256sum "$target_file" | cut -d' ' -f1; }
stage=open-initial-signed-rental-window
out="$(send_start "$D1" "$S1" 0102030405060708)"
printf '%s' "$out" | grep -q '"ok":true'
nonce="$(printf '%s' "$out" | sed -n 's/.*"target_nonce":"\([0-9a-f]*\)".*/\1/p')"
[ -n "$nonce" ]
[ "$(cut -f3 "$target_file")" = "$nonce" ]
[ "$(cut -f6 "$target_file")" = rental ]
before="$(target_sha)"
expires="$(cut -f4 "$target_file")"

stage=reuse-active-target-after-client-retry
repeat="$(send_start "$D1" "$S1" 1112131415161718)"
printf '%s' "$repeat" | grep -Fq "\"target_nonce\":\"$nonce\""
printf '%s' "$repeat" | grep -Fq "\"expires\":$expires"
[ "$(target_sha)" = "$before" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]

stage=reject-competing-device
other="$(send_start "$D2" "$S2" 2122232425262728)"
printf '%s' "$other" | grep -q '"ok":false'
printf '%s' "$other" | grep -q 'controller is busy'
[ "$(target_sha)" = "$before" ]

stage=reject-malformed-target
printf '%s\t-\tNOTHEX\t%s\tvendo-01\trental\n' "$D1" "$expires" > "$target_file"
broken="$(target_sha)"
out="$(send_start "$D1" "$S1" 3132333435363738)"
printf '%s' "$out" | grep -q '"ok":false'
printf '%s' "$out" | grep -q 'malformed coin target nonce'
[ "$(target_sha)" = "$broken" ]

# Expired window may rotate, but its new paid-ready target must be durable.
stage=failed-target-rename-cannot-ack
printf '%s\t-\t%s\t%s\tvendo-01\trental\n' "$D1" "$nonce" "$((now-1))" > "$target_file"
before="$(target_sha)"
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${2:-}" in */targets/vendo-01.tsv) exit 74;; esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/mv"
hash -r 2>/dev/null || true
out="$(send_start "$D1" "$S1" 4142434445464748)"
printf '%s' "$out" | grep -q '"ok":false'
printf '%s' "$out" | grep -q 'could not persist coin window'
[ "$(target_sha)" = "$before" ]
[ -f "$BP_PAID_UNCERTAIN" ]
rm "$T/bin/mv"
hash -r 2>/dev/null || true

stage=paid-quarantine-denies-coin-start-retry
out="$(send_start "$D1" "$S1" 5152535455565758)"
printf '%s' "$out" | grep -q '"ok":false'
printf '%s' "$out" | grep -q 'operator reconciliation required'
[ "$(target_sha)" = "$before" ]
[ -f "$BP_PAID_UNCERTAIN" ]

# Symlink target safety is checked on a clean disposable fixture ONLY.
stage=refuse-symlink-target
rm "$BP_PAID_UNCERTAIN"
mv "$target_file" "$T/trusted-window"
ln -s "$T/trusted-window" "$target_file"
out="$(send_start "$D1" "$S1" 6162636465666768)"
printf '%s' "$out" | grep -q '"ok":false'
printf '%s' "$out" | grep -q 'unsafe coin target file'
[ ! -e "$BP_PAID_UNCERTAIN" ]
rm "$target_file"
mv "$T/trusted-window" "$target_file"
echo 'RENT-0653 R281 signed coin_start PASS: repeated Android request retains controller target nonce, competing device and corrupt window refused, failed target rename NO ACK with persistent quarantine, symlink refused'
echo 'NOT PRODUCTION: split TSV/quarantine not crash-atomic, physical coinslot powercut and owner-signed Android Device Owner acceptance pending'
