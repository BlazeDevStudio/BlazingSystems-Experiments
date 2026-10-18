#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/hub/state"
REAL_MKDIR="$(command -v mkdir)"
DID='0123456789abcdef01234567'
SECRET='0123456789abcdef0123456789abcdef0123456789abcdef'
NOW="$(date +%s)"
OLD=$((NOW+600))
NEWER=$((NOW+3600))
printf 'known-token\n' > "$T/hub/admin.token"
: > "$T/hub/state/policy.tsv"
: > "$T/hub/state/events.tsv"
: > "$T/hub/state/enroll.tsv"

cat > "$T/bin/mkdir" <<'EOF'
#!/bin/sh
set -eu
if [ "${1:-}" = "$BLAZE_RENTAL_BASE/state/.lock" ] && [ "$BLAZE_RACE_MODE" != none ]; then
    "$BLAZE_REAL_MKDIR" "$1" || exit 1
    if [ "$BLAZE_RACE_MODE" = revoke ]; then
        : > "$BLAZE_RENTAL_BASE/state/devices.tsv"
    else
        printf '%s\t%s\t%s\tTest phone\t0\n' \
            "$BLAZE_TEST_DID" "$BLAZE_TEST_SECRET" "$BLAZE_TEST_LEASE" \
            > "$BLAZE_RENTAL_BASE/state/.race-next"
        mv "$BLAZE_RENTAL_BASE/state/.race-next" "$BLAZE_RENTAL_BASE/state/devices.tsv"
    fi
    rmdir "$1"
fi
exec "$BLAZE_REAL_MKDIR" "$@"
EOF
chmod 755 "$T/bin/mkdir"

seed_old(){
    printf '%s\t%s\t%s\tTest phone\t0\n' "$DID" "$SECRET" "$OLD" \
        > "$T/hub/state/devices.tsv"
}
lease_now(){ awk -F '\t' -v id="$DID" '$1==id {print $3; exit}' "$T/hub/state/devices.tsv"; }
run_admin(){
    printf 'action=add_time&device_id=%s&seconds=600\n' "$DID" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=advance \
            BLAZE_TEST_DID="$DID" BLAZE_TEST_SECRET="$SECRET" \
            BLAZE_TEST_LEASE="$NEWER" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
            REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin"
}
run_status(){
    mode="$1"
    nonce='abcdefgh'
    sig="$(printf 'status|%s|%s' "$nonce" "$SECRET" |
        openssl dgst -sha256 -hmac "$SECRET" | awk '{print $NF}')"
    printf 'action=status&device_id=%s&nonce=%s&sig=%s\n' "$DID" "$nonce" "$sig" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE="$mode" \
            BLAZE_TEST_DID="$DID" BLAZE_TEST_SECRET="$SECRET" \
            BLAZE_TEST_LEASE="$NEWER" REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental"
}

seed_old
admin_response="$(run_admin)"
[ "$(lease_now)" -eq $((NEWER+600)) ] || {
    echo 'FAIL: admin add_time overwrote a newer lease acquired before lock' >&2; exit 1;
}
printf '%s' "$admin_response" | grep -Fq '"ok":true' || {
    echo 'FAIL: admin add_time did not acknowledge the current lease' >&2; exit 1;
}

seed_old
status_response="$(run_status advance)"
[ "$(lease_now)" -eq "$NEWER" ] || {
    echo 'FAIL: device status overwrote a newer lease acquired before lock' >&2; exit 1;
}
printf '%s' "$status_response" | grep -Fq '"ok":true' || {
    echo 'FAIL: device status did not acknowledge the current lease' >&2; exit 1;
}

seed_old
revoke_response="$(run_status revoke)"
[ ! -s "$T/hub/state/devices.tsv" ] || {
    echo 'FAIL: device status resurrected a revoked device' >&2; exit 1;
}
printf '%s' "$revoke_response" | grep -Fq '"ok":false' || {
    echo 'FAIL: revoked device received a status acknowledgement' >&2; exit 1;
}

seed_old
rm -f "$T/hub/state/seen-$DID"
cp "$T/hub/state/devices.tsv" "$T/devices-before-status"
plain_status_response="$(run_status none)"
printf '%s' "$plain_status_response" | grep -Fq '"ok":true' || {
    echo 'FAIL: authenticated status request was denied' >&2; exit 1;
}
cmp -s "$T/devices-before-status" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: status poll rewrote the paid lease file' >&2; exit 1;
}
list_response="$(printf 'action=list\n' |
    env BLAZE_RENTAL_BASE="$T/hub" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$list_response" | grep -Eq '"last_seen":[1-9][0-9]*' || {
    echo 'FAIL: status activity was not visible to the admin' >&2; exit 1;
}

# A damaged paid lease is not an expired lease. Every reader and money writer
# must refuse it without replacing the original record.
printf '%s\t%s\t%s\tTest phone\t0\n' "$DID" "$SECRET" 'corrupt' \
    > "$T/hub/state/devices.tsv"
cp "$T/hub/state/devices.tsv" "$T/corrupt-lease-before"
for request in \
    'action=list' \
    "action=add_time&device_id=$DID&seconds=600" \
    "action=set_time&device_id=$DID&seconds=600" \
    "action=expire&device_id=$DID"; do
    response="$(printf '%s\n' "$request" |
        env BLAZE_RENTAL_BASE="$T/hub" \
            HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental-admin")"
    printf '%s' "$response" | grep -Fq '"ok":false' || {
        echo "FAIL: admin accepted corrupt lease for $request" >&2; exit 1;
    }
    cmp -s "$T/corrupt-lease-before" "$T/hub/state/devices.tsv" || {
        echo "FAIL: admin rewrote corrupt lease for $request" >&2; exit 1;
    }
done
status_response="$(run_status none)"
printf '%s' "$status_response" | grep -Fq '"ok":false' || {
    echo 'FAIL: phone status accepted corrupt lease' >&2; exit 1;
}
cmp -s "$T/corrupt-lease-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: phone status rewrote corrupt lease' >&2; exit 1;
}
echo 'Standalone rental lock-edge lease refusal PASS'
