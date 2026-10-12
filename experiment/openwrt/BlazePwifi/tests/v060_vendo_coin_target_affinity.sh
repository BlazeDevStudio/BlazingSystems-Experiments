#!/bin/sh
# PAY-0733: signed real Full Vendo CGI. All money state is private /tmp.
# An old receipt for account A must NEVER ACK a live window now selecting B.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0733-XXXXXX)" || exit 1
trap 'rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf 'BLAZE-PAY-0733-SYNTHETIC-ONLY\n' > "$T/.fixture-only"
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo pay0733-test-secret;;
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
A=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
B=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
TARGET=1122334455667788
NOW="$(date +%s)"
printf '%s\t100\t0\t0\t0\t0\taa:bb:cc:dd:ee:ff\t10.0.0.9\t\n' "$A" > "$BP_STATE/accounts.tsv"
printf '%s\t100\t0\t0\t0\t0\tbb:cc:dd:ee:ff:00\t10.0.0.10\t\n' "$B" >> "$BP_STATE/accounts.tsv"
target_device() {
  printf '%s\t%s\t%s\t%s\tvendo-01\thotspot\n' "$1" "$2" "$TARGET" "$((NOW+600))" > "$BP_STATE/targets/vendo-01.tsv"
}
send_coin() {
  nonce="$1"; quantity="$2"
  sig="$(printf 'pay0733-test-secret|coin|vendo-01|%s|%s|%s|pay0733-test-secret' "$nonce" "$quantity" "$TARGET" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s' "$nonce" "$quantity" "$TARGET" "$sig" | sh "$VENDO"
}
money_hash() { sha256sum "$BP_STATE/accounts.tsv" | cut -d' ' -f1; }
balance() { awk -F '\t' -v d="$1" '$1==d {print $2}' "$BP_STATE/accounts.tsv"; }
assert_denied_no_money_change() {
  label="$1"; nonce="$2"; quantity="$3"
  before="$(money_hash)"
  output="$(send_coin "$nonce" "$quantity")"
  printf '%s' "$output" | grep -Fq '"ok":false' || {
    echo "PAY-0733 FAIL: $label falsely ACKed historical account: $output" >&2; exit 1
  }
  ! printf '%s' "$output" | grep -Fq '"duplicate":true' || exit 1
  [ "$(money_hash)" = "$before" ] || {
    echo "PAY-0733 FAIL: $label altered prepaid account state" >&2;exit 1
  }
}
target_device "$A" aa:bb:cc:dd:ee:ff
orig="$(send_coin 0102030405060708 2)"
printf '%s' "$orig" | grep -Fq '"ok":true'
printf '%s' "$orig" | grep -Fq '"duplicate":false'
[ "$(balance "$A"):$(balance "$B")" = "300:100" ]
valid="$(send_coin 0102030405060708 2)"
printf '%s' "$valid" | grep -Fq '"duplicate":true'
[ "$(balance "$A"):$(balance "$B")" = "300:100" ]

# Reassign the live coin target to a second account while retaining its
# controller nonce/window. The original A receipt MUST NOT ACK for B.
target_device "$B" bb:cc:dd:ee:ff:00
assert_denied_no_money_change first-duplicate-path 0102030405060708 2
[ "$(balance "$A"):$(balance "$B")" = "300:100" ]

# Force only the first duplicate lookup to miss via a fixture-only BP_LIB
# wrapper; second lookup still examines genuine paid account rows. This
# exercises the after-account-lock branch without stubbing a money writer.
cat > "$T/first-miss-wrapper.sh" <<'WRAPPER'
. "$PAY0733_REAL_COMMON"
bp_find_event_device() {
  if [ "${PAY0733_FORCE_MISS:-0}" = 1 ] &&
      [ ! -e "$PAY0733_MISS_MARKER" ]; then
    : > "$PAY0733_MISS_MARKER"
    return 0
  fi
  awk -F '\t' -v e="$1" '{
    n=split($9,a,",")
    for (i=1;i<=n;i++) if(a[i]==e || index(a[i],e "!")==1){print $1;exit}
  }' "$BP_ACCOUNTS"
}
WRAPPER
export PAY0733_REAL_COMMON="$BP_LIB" PAY0733_MISS_MARKER="$T/first-read-missed"
export BP_LIB="$T/first-miss-wrapper.sh" PAY0733_FORCE_MISS=1
assert_denied_no_money_change second-duplicate-path 0102030405060708 2
[ -e "$PAY0733_MISS_MARKER" ] || {
  echo 'PAY-0733 FAIL: second-replay branch not exercised' >&2; exit 1
}
unset PAY0733_FORCE_MISS
export BP_LIB="$PAY0733_REAL_COMMON"
[ "$(balance "$A"):$(balance "$B")" = "300:100" ]

# A newly signed different nonce can still legitimately credit selected B.
fresh="$(send_coin 1112131415161718 1)"
printf '%s' "$fresh" | grep -Fq '"duplicate":false'
[ "$(balance "$A"):$(balance "$B")" = "300:200" ]
assert_denied_no_money_change after-new-account-credit 0102030405060708 2
[ "$(balance "$A"):$(balance "$B")" = "300:200" ]
echo 'PAY-0733 PASS: signed old A receipt cannot ACK reassigned B target on either duplicate path; correct original and fresh B money preserved'
echo 'NOT PRODUCTION v2: independent witness, native crash-atomic server authority, owner signing and hardware acceptance remain blocked'
