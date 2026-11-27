#!/bin/sh
# ENROLL-0655: real signed R281 Android enrollment CGI, disposable state only.
# Verifies one-time QR, persistence failure, no leaked secret, quarantine.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-r281-enroll-XXXXXX)"
stage=setup
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "ENROLL-0655 failed stage=$stage rc=$rc" >&2; fi; rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0 ;;
  *) exit 1 ;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi"
export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh" BP_RENTAL_LIB="$LIB/rental.sh"
export REQUEST_METHOD=GET REMOTE_ADDR=10.0.0.9
. "$BP_LIB"
. "$BP_AUTH_LIB"
. "$BP_RENTAL_LIB"
bp_rental_init
CGI="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental"
eid=abcdef123456
secret=111111111111111111111111111111111111
nonce=0102030405060708
label=FakePhone
now="$(bp_now)"
add_token() {
  printf '%s\t%s\t%s\t%s\n' "$eid" "$secret" "$((now+600))" "$label" >> "$BP_RENTAL_ENROLL"
}
request() {
  sig="$(bp_rental_hmac "$eid.$secret" "enroll|$nonce|$eid.$secret")"
  printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s' "$eid" "$nonce" "$sig" |
    REQUEST_METHOD=POST sh "$CGI"
}
devices_sha() { sha256sum "$BP_RENTAL_DEVICES" | cut -d' ' -f1; }
policy_sha() { sha256sum "$BP_RENTAL_POLICY" | cut -d' ' -f1; }
enroll_sha() { sha256sum "$BP_RENTAL_ENROLL" | cut -d' ' -f1; }
count_devices() { awk -F '\t' 'NF==5 {n++} END {print n+0}' "$BP_RENTAL_DEVICES"; }
stage=one-time-hmac-enrollment-success
add_token
response="$(request)"
printf '%s' "$response" | grep -q '"ok":true'
did="$(printf '%s' "$response" | sed -n 's/.*"device_id":"\([0-9a-f]*\)".*/\1/p')"
dsecret="$(printf '%s' "$response" | sed -n 's/.*"device_secret":"\([0-9a-f]*\)".*/\1/p')"
[ "${#did}" -eq 24 ] && [ "${#dsecret}" -eq 48 ]
[ "$(count_devices)" -eq 1 ]
[ "$(cut -f2 "$BP_RENTAL_DEVICES")" = "$dsecret" ]
[ "$(cut -f1 "$BP_RENTAL_POLICY")" = "$did" ]
[ ! -s "$BP_RENTAL_ENROLL" ]
[ ! -e "$BP_PAID_UNCERTAIN" ]

stage=same-token-reuse-must-refuse
again="$(request)"
printf '%s' "$again" | grep -q '"ok":false'
printf '%s' "$again" | grep -q 'enrollment invalid or used'
[ "$(count_devices)" -eq 1 ]
[ ! -e "$BP_PAID_UNCERTAIN" ]

# Run three independent signed/valid tokens against injected storage EIO.
# The old code emitted ok:true regardless of any of these write failures.
for mode in devices policy enroll; do
  stage="fault-$mode"
  # SYNTHETIC ONLY: reset prepared state for each independent fixture.
  : > "$BP_RENTAL_DEVICES"
  : > "$BP_RENTAL_POLICY"
  : > "$BP_RENTAL_ENROLL"
  rm -f "$BP_PAID_UNCERTAIN"
  add_token
  snapshot="$(enroll_sha)"
  cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${FAILING_FILE:-}:${2:-}" in
  devices:*/rental-devices.tsv|policy:*/rental-policy.tsv|enroll:*/rental-enroll.tsv) exit 74 ;;
esac
exec /bin/mv "$@"
MV
  chmod 700 "$T/bin/mv"
  hash -r 2>/dev/null || true
  export FAILING_FILE="$mode"
  stage="fault-$mode:request"
  fail="$(request)"
  stage="fault-$mode:must-reject-success"
  printf '%s' "$fail" | grep -q '"ok":false' || {
    echo "ENROLL-0655 unexpected response for fault=$mode (redacted)" >&2; exit 1;
  }
  stage="fault-$mode:must-quarantine-operator"
  printf '%s' "$fail" | grep -q 'operator reconciliation required' || {
    echo "ENROLL-0655 missing reconciliation error for fault=$mode" >&2; exit 1;
  }
  if printf '%s' "$fail" | grep -q '"device_secret"'; then
    echo "P0 private enrollment secret disclosed after $mode storage EIO" >&2
    exit 1
  fi
  stage="fault-$mode:marker-persist"
  [ -f "$BP_PAID_UNCERTAIN" ]
  stage="fault-$mode:enrollment-source-unchanged"
  [ "$(enroll_sha)" = "$snapshot" ]
  if [ "$mode" = devices ]; then
    stage="fault-$mode:device-not-created"
    [ "$(count_devices)" -eq 0 ]
  fi
  unset FAILING_FILE
  rm -f "$T/bin/mv"
  hash -r 2>/dev/null || true
  # Even with disk repaired, an unresolved two/three-file transaction must
  # not create a second valid identity or claim successful token consumption.
  before="$(devices_sha)"
  stage="fault-$mode:uncertainty-refuses-retry"
  retry="$(request)"
  printf '%s' "$retry" | grep -q '"ok":false'
  stage="fault-$mode:reconciliation-message-on-retry"
  printf '%s' "$retry" | grep -q 'operator reconciliation required' || {
    # Only the JSON error is printed; never log generated device secrets.
    error_text="$(printf '%s' "$retry" | sed -n 's/.*"error":"\([^"]*\)".*/\1/p')"
    echo "ENROLL-0655 unexpected $mode retry rejection error: $error_text" >&2
    exit 1
  }
  stage="fault-$mode:no-extra-identity"
  [ "$(devices_sha)" = "$before" ]
  [ -f "$BP_PAID_UNCERTAIN" ]
done

stage=duplicate-token-source:reset-fixture
: > "$BP_RENTAL_DEVICES"
: > "$BP_RENTAL_POLICY"
: > "$BP_RENTAL_ENROLL"
rm "$BP_PAID_UNCERTAIN"
stage=duplicate-token-source:prepare-source
add_token
add_token
before="$(enroll_sha)"
stage=duplicate-token-source:signed-request
response="$(request)"
stage=duplicate-token-source:refuse-success
printf '%s' "$response" | grep -q '"ok":false' ||
  { echo 'ENROLL-0655 duplicate token got a success response (credentials redacted)' >&2; exit 1; }
stage=duplicate-token-source:require-reconciliation
printf '%s' "$response" | grep -q 'operator reconciliation required' ||
  { echo 'ENROLL-0655 duplicate token lacked operator-reconciliation error' >&2; exit 1; }
stage=duplicate-token-source:source-remains-byte-identical
[ "$(enroll_sha)" = "$before" ]
stage=duplicate-token-source:paid-marker-retained
[ -f "$BP_PAID_UNCERTAIN" ]

echo 'ENROLL-0655 signed R281 CGI PASS: one QR = one durable identity+policy+consumed token; duplicate replay, EIO and malformed registry no false ACK; ambiguous state quarantined'
echo 'NOT production: signed device enrollment still spans separate v1 TSV files, no true fsync-backed atomic journal or OEM Device Owner proof'
