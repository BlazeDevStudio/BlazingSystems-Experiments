#!/bin/sh
# PAY-0731 P0: REAL signed Full Vendo coin CGI; private synthetic /tmp only.
# Regression for BOTH ordinary coin receipt fast paths bypassing paid lock.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-pay0731-XXXXXX)" || exit 1
trap 'touch "$T/release" 2>/dev/null || :; rm -rf "$T"' EXIT HUP INT TERM
chmod 700 "$T"
printf 'BLAZE-PAY-0731-SYNTHETIC-ONLY\n' > "$T/.fixture-only"
mkdir -p "$T/bin" "$T/state/targets" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo fixture-only-vendo-secret;;
  *'get blazepwifi.main.vendo_port') echo 4455;;
  *'get blazepwifi.main.pulse_value_centavos') echo 100;;
  *'get blazepwifi.main.event_history') echo 8;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH"
export BP_STATE="$T/state" BP_RUN="$T/run"
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
  nonce="$1"
  sig="$(printf 'fixture-only-vendo-secret|coin|vendo-01|%s|1|%s|fixture-only-vendo-secret' "$nonce" "$TARGET" | sha256sum | cut -d' ' -f1)"
  printf 'action=coin&id=vendo-01&nonce=%s&pulses=1&target=%s&sig=%s' "$nonce" "$TARGET" "$sig" | sh "$VENDO"
}
paid_digest() { sha256sum "$BP_STATE/accounts.tsv" "$BP_STATE/member-revision" "$BP_STATE/member-events.tsv" "$BP_STATE/rental-events.tsv" | awk '{print $1}'; }
assert_deny() {
  tag="$1"; nonce="$2"
  before="$(paid_digest)"
  response="$(send_coin "$nonce")"
  printf '%s' "$response" | grep -Fq '"ok":false' || {
    echo "PAY-0731 UNSAFE $tag success ACK: $response" >&2; exit 1
  }
  ! printf '%s' "$response" | grep -Fq '"duplicate":true' || exit 1
  [ "$(paid_digest)" = "$before" ] || { echo "PAY-0731 $tag mutated money" >&2; exit 1; }
}
# Explicitly provision only this disposable synthetic fixture. Unknown controllers
# must remain denied by default; production code is never auto-enabled.
REQUEST_METHOD=GET
. "$BP_LIB"
. "$BP_CONTROLLER_LIB"
REQUEST_METHOD=POST
bp_controller_ensure vendo-01
if bp_controller_paid_allowed vendo-01 coin; then
  echo 'PAY-0731 invalid fixture: unprovisioned controller accepted' >&2; exit 2
fi
bp_controller_set vendo-01 1 1 1 1 -1 -1 -1 1 1 1 40 400 6
bp_controller_paid_allowed vendo-01 coin || {
  echo 'PAY-0731 invalid fixture: synthetic admission setup failed' >&2; exit 2
}
# First record is genuinely committed by the normal signed CGI, and replayed.
first="$(send_coin 0102030405060708)"
printf '%s' "$first" | grep -Fq '"ok":true'
printf '%s' "$first" | grep -Fq '"duplicate":false'
replay="$(send_coin 0102030405060708)"
printf '%s' "$replay" | grep -Fq '"duplicate":true'
credit="$(awk -F '\t' '$1=="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"{print $2}' "$BP_STATE/accounts.tsv")"
[ "$credit" = 200 ]
paid_digest > "$T/before"

# PAY-0731: writer holds global financial lock BEFORE it writes uncertainty.
# The pre-existing up-front marker check alone does not cover this race.
(
  exec 8>"$BP_RUN/paid-financial.lock"
  flock -x 8
  : > "$T/held"
  while [ ! -f "$T/release" ]; do sleep 0.05; done
) &
lock_pid=$!
i=0
while [ ! -f "$T/held" ] && [ "$i" -lt 80 ]; do sleep 0.05; i=$((i+1)); done
[ -f "$T/held" ] || { echo "PAY-0731 lock holder setup failed" >&2; exit 1; }
assert_deny writer-held-before-marker 0102030405060708
: > "$T/release"
wait "$lock_pid"
rm "$T/release" "$T/held"
replay="$(send_coin 0102030405060708)"
printf '%s' "$replay" | grep -Fq '"duplicate":true'

# The PAY-0730 cutover marker must halt old signed coin ACKs and new coins.
for marker in regular directory dangling; do
  case "$marker" in
    regular) printf 'CUTOVER\n' > "$BP_STATE/paid-v2-cutover-intent" ;;
    directory) mkdir "$BP_STATE/paid-v2-cutover-intent" ;;
    dangling) ln -s "$T/missing" "$BP_STATE/paid-v2-cutover-intent" ;;
  esac
  assert_deny "$marker old-receipt" 0102030405060708
  assert_deny "$marker fresh" 1112131415161718
  case "$marker" in
    directory) rmdir "$BP_STATE/paid-v2-cutover-intent" ;;
    *) rm "$BP_STATE/paid-v2-cutover-intent" ;;
  esac
done
printf 'PENDING\t123\n' > "$BP_STATE/paid-state-uncertain"
assert_deny uncertainty-existing-receipt 0102030405060708
rm "$BP_STATE/paid-state-uncertain"

# Exercise SECOND duplicate read after the account lock handoff. Inject a
# first-read miss in a disposable BP_LIB wrapper, then a synthetic competitor
# holding paid-financial.lock exactly AFTER first read lock was released.
# No production library, controller or coin hardware is mocked or mutated.
cat > "$T/lib-wrapper.sh" <<'WRAPPER'
. "$PAY0731_REAL_COMMON"
bp_find_event_device() {
  if [ "${PAY0731_FORCE_SECOND:-0}" = 1 ] && [ ! -f "$PAY0731_SEEN" ]; then
    : > "$PAY0731_SEEN"
    return 0
  fi
  event="$1"
  awk -F '\t' -v e="$event" '{
    n=split($9,a,",")
    for(i=1;i<=n;i++) if(a[i]==e || index(a[i],e "!")==1){print $1;exit}
  }' "$BP_ACCOUNTS"
}
bp_lock() {
  if [ "${PAY0731_FORCE_SECOND:-0}" = 1 ] &&
     [ -f "$PAY0731_SEEN" ] && [ ! -f "$PAY0731_STARTED" ]; then
    : > "$PAY0731_STARTED"
    (
      exec 8>"$BP_RUN/paid-financial.lock"
      flock -x 8 || exit 1
      : > "$PAY0731_HELD"
      while [ ! -f "$PAY0731_RELEASE" ]; do sleep 0.05; done
    ) >/dev/null 2>&1 </dev/null &
    n=0
    while [ ! -f "$PAY0731_HELD" ] && [ "$n" -lt 80 ]; do sleep 0.05; n=$((n+1)); done
    [ -f "$PAY0731_HELD" ] || return 1
  fi
  mkdir -p "$BP_RUN" || return 1
  exec 9>"$BP_RUN/account.lock" || return 1
  flock -w 10 9 || { exec 9>&-; return 1; }
}
WRAPPER
export PAY0731_REAL_COMMON="$BP_LIB"
export BP_LIB="$T/lib-wrapper.sh"
export PAY0731_FORCE_SECOND=1
export PAY0731_SEEN="$T/late-seen" PAY0731_STARTED="$T/late-started"
export PAY0731_HELD="$T/late-held" PAY0731_RELEASE="$T/release"
assert_deny late-duplicate-under-paid-writer 0102030405060708
[ -f "$PAY0731_SEEN" ] && [ -f "$PAY0731_STARTED" ] && [ -f "$PAY0731_HELD" ] || {
  echo 'PAY-0731 second read path was not exercised' >&2; exit 1
}
: > "$T/release"
unset PAY0731_FORCE_SECOND
export BP_LIB="$PAY0731_REAL_COMMON"
replay="$(send_coin 0102030405060708)"
printf '%s' "$replay" | grep -Fq '"duplicate":true'
[ "$(awk -F '\t' '$1=="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"{print $2}' "$BP_STATE/accounts.tsv")" = 200 ]
[ ! -e "$BP_STATE/paid-state-uncertain" ]
echo 'PAY-0731 PASS: REAL signed Vendo coin ACK old/new correctly gated by global money lock, cutover, uncertain marker, plus late duplicate writer race'
echo 'NOT PRODUCTION: v1 credit receipts remain bounded to coin window; independent witness/crash-atomic v2/hardware still BLOCKED'
