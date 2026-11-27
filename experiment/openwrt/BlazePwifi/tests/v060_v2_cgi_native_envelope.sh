#!/bin/sh
# PAY-0751: installed signed CGI -> runtime-domain native envelope verification.
# Disposable state only. A verified envelope must still receive no money ACK.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-v2-cgi-XXXXXX)"
RT="$(mktemp -d /tmp/blaze-v2-native-XXXXXX)"
trap 'rm -rf "$T" "$RT"' EXIT HUP INT TERM
umask 077
mkdir -m 700 "$T/bin" "$T/run"
cc -std=c11 -Wall -Wextra -Werror -O2 -DBLAZE_RUNTIME_AUTHORITY \
  -DBLAZE_RUNTIME_TEST_ROOT_OVERRIDE \
  "$ROOT/tools/v060_journal_authority_native.c" -lcrypto -o "$T/runtime"
cat >"$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') printf 'synthetic-cgi-secret\n';;
  *'get blazepwifi.main.vendo_port') printf '4455\n';;
  *'get blazepwifi.main.durable_sync') printf '0\n';;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
cat >"$T/common-test.sh" <<'COMMON'
. "$REAL_COMMON"
bp_v2_verify_envelope() {
  if "$AUTH_BIN" "$BP_STATE" "$@" --verify-envelope-only \
      >"$VERIFY_LOG.stdout" 2>"$VERIFY_LOG.stderr"; then
    printf 'verified\n' > "$VERIFY_LOG"
    return 0
  fi
  printf 'rejected\n' > "$VERIFY_LOG"
  return 1
}
COMMON
printf 'BLAZE-V2-SYNTHETIC-ONLY\n' >"$RT/.blaze-v2-fixture-only"
key=3333333333333333333333333333333333333333333333333333333333333333
printf 'vendo-01\t%s\n' "$key" >"$RT/controller-keys.tsv"
printf 'V\t2\nA\talice\t100\nL\tdev01\t0\n' >"$RT/ledger.tsv"
base="$(sha256sum "$RT/ledger.tsv" | cut -d' ' -f1)"
printf 'H\t%s\n' "$base" >>"$RT/ledger.tsv"
chmod 600 "$RT/.blaze-v2-fixture-only" "$RT/controller-keys.tsv" "$RT/ledger.tsv"
export PATH="$T/bin:$PATH" BP_STATE="$RT" BP_RUN="$T/run"
export BP_LIB="$T/common-test.sh"
export REAL_COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export AUTH_BIN="$T/runtime" VERIFY_LOG="$T/verify-status"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.1.2.3
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
sign_v2() {
  printf 'BLAZE-V2-AUTH/1\tvendo-01\t%s\tvendo-01:%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$1" "$1" "$2" "$3" "$4" "$5" "$6" |
    openssl dgst -sha256 -mac HMAC -macopt "hexkey:$key" -r | awk '{print $1}'
}
call() {
  action="$1"; seq="$2"; subject="$3"; destination="$4"
  units="$5"; v2time="$6"; v2mac="$7"
  target=dev01; nonce=deadbeef00112233; pulses=2
  legacy="$(printf 'synthetic-cgi-secret|%s|vendo-01|%s|%s|%s|synthetic-cgi-secret' \
    "$action" "$nonce" "$pulses" "$target" | sha256sum | cut -d' ' -f1)"
  printf 'action=%s&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s&v2_seq=%s&v2_subject=%s&v2_destination=%s&v2_units=%s&v2_time=%s&v2_hmac=%s\n' \
    "$action" "$nonce" "$pulses" "$target" "$legacy" "$seq" "$subject" \
    "$destination" "$units" "$v2time" "$v2mac" | sh "$VENDO"
}
boot="$(call ping 1 alice - 1 1000 0000000000000000000000000000000000000000000000000000000000000000)"
printf '%s' "$boot" | grep -q '"ok":true'
test ! -e "$VERIFY_LOG"
printf 'alice\tAlice\t1\tsha256i\tsalt\thash\t4096\t900\t1\t1234\tfixture\n' >"$RT/members.tsv"
printf 'dev01\tfake-rental-secret\t2140000000\tSynthetic Rental\t1234\n' >"$RT/rental-devices.tsv"
printf 'original-receipt\n' >"$RT/member-events.tsv"
printf 'existing-receipt\tdev01\t2140000000\t1234\t3\n' >"$RT/rental-events.tsv"
chmod 600 "$RT/members.tsv" "$RT/rental-devices.tsv" "$RT/member-events.tsv" "$RT/rental-events.tsv"
snapshot() {
  sha256sum "$RT/ledger.tsv" "$RT/members.tsv" "$RT/rental-devices.tsv" \
    "$RT/member-events.tsv" "$RT/rental-events.tsv" "$T/run/vendos.tsv"
}
before="$(snapshot)"
assert_denied() {
  response="$1"
  printf '%s' "$response" | grep -q '"ok":false'
  ! printf '%s' "$response" | grep -Eq '"duplicate":true|"lease_until"|"credited_cents"|ACKP1'
  [ "$(snapshot)" = "$before" ] || {
    echo 'PAY-0751 CGI changed v1 or v2 financial state/heartbeat' >&2; exit 1;
  }
  [ ! -e "$RT/.v2-native-lock" ] || {
    echo 'PAY-0751 verifier created a paid writer lock' >&2; exit 1;
  }
}
member_mac="$(sign_v2 1 AM alice - 40 1000)"
member="$(call member_v2_add 1 alice - 40 1000 "$member_mac")"
assert_denied "$member"
grep -qx verified "$VERIFY_LOG"
rm -f "$VERIFY_LOG"
bad_legacy="$(printf 'action=member_v2_add&id=vendo-01&nonce=deadbeef00112233&pulses=2&target=dev01&sig=%064d&v2_seq=1&v2_subject=alice&v2_destination=-&v2_units=40&v2_time=1000&v2_hmac=%s\n' \
  0 "$member_mac" | sh "$VENDO")"
assert_denied "$bad_legacy"
printf '%s' "$bad_legacy" | grep -q 'bad signature'
test ! -e "$VERIFY_LOG"
# Identical signed retry after a lost response remains denied, with no replay ACK.
member="$(call member_v2_add 1 alice - 40 1000 "$member_mac")"
assert_denied "$member"
grep -qx verified "$VERIFY_LOG"
tampered="$(call member_v2_add 1 alice - 41 1000 "$member_mac")"
assert_denied "$tampered"
grep -qx rejected "$VERIFY_LOG"
rental_mac="$(sign_v2 2 LR dev01 - 600 1000)"
rental="$(call rental_v2_lease 2 dev01 - 600 1000 "$rental_mac")"
assert_denied "$rental"
grep -qx verified "$VERIFY_LOG"
# A staged partial write and corrupt ledger must not yield any public success.
printf 'partial\n' >"$RT/.ledger-next-test"
printf 'corrupt\n' >>"$RT/ledger.tsv"
before="$(snapshot)"
rental="$(call rental_v2_lease 2 dev01 - 600 1000 "$rental_mac")"
assert_denied "$rental"
grep -qx verified "$VERIFY_LOG"
[ "$(cat "$RT/.ledger-next-test")" = partial ]
rm -f "$VERIFY_LOG"
unknown="$(call rental_v2_unknown 3 dev01 - 600 1000 "$rental_mac")"
assert_denied "$unknown"
test ! -e "$VERIFY_LOG"
echo 'PAY-0751 PASS: signed installed CGI reaches native v2 HMAC verification but never credits, replays, heartbeats or ACKs'
