#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin" "$T/hub/state"
REAL_MKDIR="$(command -v mkdir)"
DID='0123456789abcdef01234567'
RID='0123456789abcdef0123456789abcdef'
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
    printf 'action=add_time&device_id=%s&seconds=600&request_id=%s\n' "$DID" "$RID" |
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
for malformed in corrupt 000123 2147483648; do
    printf '%s\t%s\t%s\tTest phone\t0\n' "$DID" "$SECRET" "$malformed" \
        > "$T/hub/state/devices.tsv"
    cp "$T/hub/state/devices.tsv" "$T/corrupt-lease-before"
    for request in \
        'action=list' \
        "action=add_time&device_id=$DID&seconds=600&request_id=$RID" \
        "action=set_time&device_id=$DID&seconds=600&request_id=$RID" \
        "action=expire&device_id=$DID&request_id=$RID"; do
        response="$(printf '%s\n' "$request" |
            env BLAZE_RENTAL_BASE="$T/hub" \
                HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
                sh "$ROOT/root/www/cgi-bin/rental-admin")"
        printf '%s' "$response" | grep -Fq '"ok":false' || {
            echo "FAIL: admin accepted corrupt lease for $request ($malformed)" >&2; exit 1;
        }
        cmp -s "$T/corrupt-lease-before" "$T/hub/state/devices.tsv" || {
            echo "FAIL: admin rewrote corrupt lease for $request ($malformed)" >&2; exit 1;
        }
    done
    status_response="$(run_status none)"
    printf '%s' "$status_response" | grep -Fq '"ok":false' || {
        echo "FAIL: phone status accepted corrupt lease ($malformed)" >&2; exit 1;
    }
    cmp -s "$T/corrupt-lease-before" "$T/hub/state/devices.tsv" || {
        echo "FAIL: phone status rewrote corrupt lease ($malformed)" >&2; exit 1;
    }
done

# The original helper ignored a failed sync and returned a paid success. A
# failure before rename has no committed lease; after rename the outcome is
# uncertain and must never be acknowledged as durable.
REAL_SYNC="$(command -v sync)"
cat > "$T/bin/sync" <<'EOF'
#!/bin/sh
set -eu
count=0
[ ! -s "$BLAZE_SYNC_COUNT_FILE" ] || count="$(cat "$BLAZE_SYNC_COUNT_FILE")"
count=$((count+1))
printf '%s\n' "$count" > "$BLAZE_SYNC_COUNT_FILE"
[ "$count" -ne "$BLAZE_SYNC_FAIL_AT" ] || exit 1
exec "$BLAZE_REAL_SYNC" "$@"
EOF
chmod 755 "$T/bin/sync"
run_sync_fault(){
    printf 'action=add_time&device_id=%s&seconds=600&request_id=%s\n' "$DID" "$RID" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=none \
            BLAZE_REAL_SYNC="$REAL_SYNC" BLAZE_SYNC_FAIL_AT="$1" \
            BLAZE_SYNC_COUNT_FILE="$T/sync-count" \
            HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental-admin"
}
seed_old
cp "$T/hub/state/devices.tsv" "$T/lease-before-sync"
rm -f "$T/sync-count"
response="$(run_sync_fault 1)"
printf '%s' "$response" | grep -Fq '"ok":false' || {
    echo 'FAIL: pre-rename sync failure received a paid ACK' >&2; exit 1;
}
cmp -s "$T/lease-before-sync" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: pre-rename sync failure replaced the lease' >&2; exit 1;
}
seed_old
rm -f "$T/sync-count"
response="$(run_sync_fault 2)"
printf '%s' "$response" | grep -Fq '"ok":false' || {
    echo 'FAIL: post-rename sync failure received a paid ACK' >&2; exit 1;
}
printf '%s' "$response" | grep -Fq 'outcome uncertain' || {
    echo 'FAIL: post-rename sync failure hid the uncertain outcome' >&2; exit 1;
}

# A response lost after the rename leaves the new lease visible. Repeating the
# exact request ID must return the prior result without granting time twice.
run_paid_request(){
    printf 'action=add_time&device_id=%s&seconds=%s&request_id=%s\n' \
        "$DID" "$2" "$1" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=none \
            BLAZE_REAL_SYNC="$REAL_SYNC" BLAZE_SYNC_FAIL_AT="$3" \
            BLAZE_SYNC_COUNT_FILE="$T/sync-count" \
            HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental-admin"
}
seed_old
rm -f "$T/sync-count"
first="$(run_paid_request "$RID" 600 2)"
printf '%s' "$first" | grep -Fq '"ok":false' || {
    echo 'FAIL: uncertain first grant received a positive ACK' >&2; exit 1;
}
first_lease="$(lease_now)"
[ "$first_lease" -eq $((OLD+600)) ] || {
    echo 'FAIL: post-rename fault did not expose the first lease' >&2; exit 1;
}
rm -f "$T/sync-count"
retry="$(run_paid_request "$RID" 600 0)"
printf '%s' "$retry" | grep -Fq '"ok":true' || {
    echo 'FAIL: same-ID retry was not acknowledged' >&2; exit 1;
}
[ "$(lease_now)" -eq "$first_lease" ] || {
    echo 'FAIL: lost-ACK retry granted paid time twice' >&2; exit 1;
}
rm -f "$T/sync-count"
conflict="$(run_paid_request "$RID" 1200 0)"
printf '%s' "$conflict" | grep -Fq '"ok":false' || {
    echo 'FAIL: request ID reused with different seconds was accepted' >&2; exit 1;
}
[ "$(lease_now)" -eq "$first_lease" ] || {
    echo 'FAIL: conflicting request ID changed the lease' >&2; exit 1;
}
rm -f "$T/sync-count"
missing="$(run_paid_request '' 600 0)"
printf '%s' "$missing" | grep -Fq '"ok":false' || {
    echo 'FAIL: paid grant without a request ID was accepted' >&2; exit 1;
}
[ "$(lease_now)" -eq "$first_lease" ] || {
    echo 'FAIL: missing request ID changed the lease' >&2; exit 1;
}
awk -F '\t' -v id="$RID" '$1=="@op" && $2==id && NF==6 {found++} END{exit(found==1?0:1)}' \
    "$T/hub/state/devices.tsv" || {
    echo 'FAIL: paid lease and request receipt were not saved in one file' >&2; exit 1;
}
list_response="$(printf 'action=list\n' |
    env BLAZE_RENTAL_BASE="$T/hub" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$list_response" | grep -Fq '"ok":true' || {
    echo 'FAIL: receipt row broke the admin device list' >&2; exit 1;
}
run_other_paid(){
    printf 'action=%s&device_id=%s&seconds=%s&request_id=%s\n' "$1" "$DID" "$2" "$3" |
        env BLAZE_RENTAL_BASE="$T/hub" \
            HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental-admin"
}
SET_RID='11111111111111111111111111111111'
set_first="$(run_other_paid set_time 300 "$SET_RID")"
printf '%s' "$set_first" | grep -Fq '"ok":true' || {
    echo 'FAIL: request-ID set_time failed' >&2; exit 1;
}
set_lease="$(lease_now)"
set_retry="$(run_other_paid set_time 300 "$SET_RID")"
printf '%s' "$set_retry" | grep -Fq '"replayed":true' || {
    echo 'FAIL: set_time retry was not identified as replay' >&2; exit 1;
}
[ "$(lease_now)" -eq "$set_lease" ] || {
    echo 'FAIL: set_time retry changed the lease' >&2; exit 1;
}
EXP_RID='22222222222222222222222222222222'
exp_first="$(run_other_paid expire '-' "$EXP_RID")"
printf '%s' "$exp_first" | grep -Fq '"ok":true' || {
    echo 'FAIL: request-ID expire failed' >&2; exit 1;
}
exp_lease="$(lease_now)"
exp_retry="$(run_other_paid expire '-' "$EXP_RID")"
printf '%s' "$exp_retry" | grep -Fq '"replayed":true' || {
    echo 'FAIL: expire retry was not identified as replay' >&2; exit 1;
}
[ "$(lease_now)" -eq "$exp_lease" ] || {
    echo 'FAIL: expire retry changed the lease' >&2; exit 1;
}
awk -F '\t' -v id="$SET_RID" '$1=="@op" && $2==id {print;exit}' \
    "$T/hub/state/devices.tsv" > "$T/duplicate-receipt-line"
cat "$T/duplicate-receipt-line" >> "$T/hub/state/devices.tsv"
cp "$T/hub/state/devices.tsv" "$T/duplicate-receipt-before"
duplicate="$(run_other_paid set_time 300 "$SET_RID")"
printf '%s' "$duplicate" | grep -Fq '"ok":false' || {
    echo 'FAIL: duplicate request receipt was accepted' >&2; exit 1;
}
cmp -s "$T/duplicate-receipt-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: duplicate receipt request changed financial state' >&2; exit 1;
}
echo 'Standalone rental lock-edge lease refusal PASS'
