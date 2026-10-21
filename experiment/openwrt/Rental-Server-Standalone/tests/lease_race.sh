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
    elif [ "$BLAZE_RACE_MODE" = enroll_replace ]; then
        : > "$BLAZE_TEST_RACE_MARKER"
        printf '%s\t%s\t%s\t%s\n' \
            "$BLAZE_TEST_EID" "$BLAZE_TEST_REPLACEMENT_SECRET" \
            "$BLAZE_TEST_EXPIRY" 'Replacement phone' \
            > "$BLAZE_RENTAL_BASE/state/.enroll-race-next"
        mv "$BLAZE_RENTAL_BASE/state/.enroll-race-next" \
            "$BLAZE_RENTAL_BASE/state/enroll.tsv"
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
# Losing the policy authority must not turn a signed status into the broad
# wildcard default or permit a paid admin write. Preserve the paid file.
mv "$T/hub/state/policy.tsv" "$T/policy-held"
cp "$T/hub/state/devices.tsv" "$T/devices-before-policy-loss"
for policy_state in missing symlink; do
    if [ "$policy_state" = symlink ]; then
        ln -s "$T/policy-held" "$T/hub/state/policy.tsv"
    fi
    policy_status="$(run_status none)"
    printf '%s' "$policy_status" | grep -Fq '"ok":false' || {
        echo "FAIL: phone status accepted $policy_state policy authority" >&2; exit 1;
    }
    policy_admin="$(printf 'action=add_time&device_id=%s&seconds=600&request_id=%s\n' "$DID" "$RID" |
        env BLAZE_RENTAL_BASE="$T/hub" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
            REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
    printf '%s' "$policy_admin" | grep -Fq '"ok":false' || {
        echo "FAIL: admin paid write accepted $policy_state policy authority" >&2; exit 1;
    }
    cmp -s "$T/devices-before-policy-loss" "$T/hub/state/devices.tsv" || {
        echo "FAIL: $policy_state policy authority changed paid state" >&2; exit 1;
    }
    [ "$policy_state" = missing ] || rm "$T/hub/state/policy.tsv"
done
mv "$T/policy-held" "$T/hub/state/policy.tsv"
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

# A different damaged receipt must quarantine the whole paid state. Looking up
# only the new request ID would allow another grant over corrupt history.
seed_old
printf '@op\t%s\t%s\tadd_time\t600\tbroken\n' "$RID" "$DID" >> "$T/hub/state/devices.tsv"
cp "$T/hub/state/devices.tsv" "$T/corrupt-receipt-before"
corrupt_other="$(run_other_paid add_time 600 '33333333333333333333333333333333')"
printf '%s' "$corrupt_other" | grep -Fq '"ok":false' || {
    echo 'FAIL: paid grant accepted unrelated corrupt receipt' >&2; exit 1;
}
cmp -s "$T/corrupt-receipt-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: paid grant rewrote unrelated corrupt receipt' >&2; exit 1;
}
seed_old
cp "$T/hub/state/devices.tsv" "$T/duplicate-device-line"
cat "$T/duplicate-device-line" >> "$T/hub/state/devices.tsv"
cp "$T/hub/state/devices.tsv" "$T/duplicate-device-before"
duplicate_device="$(run_other_paid add_time 600 '44444444444444444444444444444444')"
printf '%s' "$duplicate_device" | grep -Fq '"ok":false' || {
    echo 'FAIL: paid grant accepted duplicate saved device' >&2; exit 1;
}
cmp -s "$T/duplicate-device-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: paid grant rewrote duplicate saved device' >&2; exit 1;
}

# Enrollment is another real writer of devices.tsv. It must preserve the
# corrupted paid state for inspection and leave the enrollment token unused.
seed_old
printf '@op\t%s\t%s\tadd_time\t600\tbroken\n' "$RID" "$DID" >> "$T/hub/state/devices.tsv"
cp "$T/hub/state/devices.tsv" "$T/enroll-corrupt-before"
EID='abcdef123456'
ESECRET='0123456789abcdef0123456789abcdef0123'
EXPIRY=$((NOW+900))
printf '%s\t%s\t%s\t%s\n' "$EID" "$ESECRET" "$EXPIRY" 'Test phone' > "$T/hub/state/enroll.tsv"
cp "$T/hub/state/enroll.tsv" "$T/enroll-before"
ENONCE='abcdefgh'
ETOKEN="$EID.$ESECRET"
ESIG="$(printf 'enroll|%s|%s' "$ENONCE" "$ETOKEN" |
    openssl dgst -sha256 -hmac "$ETOKEN" | awk '{print $NF}')"
enroll_corrupt="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$EID" "$ENONCE" "$ESIG" |
    env BLAZE_RENTAL_BASE="$T/hub" REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental")"
printf '%s' "$enroll_corrupt" | grep -Fq '"ok":false' || {
    echo 'FAIL: enrollment wrote through corrupt paid state' >&2; exit 1;
}
cmp -s "$T/enroll-corrupt-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: enrollment changed corrupt paid state' >&2; exit 1;
}
cmp -s "$T/enroll-before" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: corrupt-state enrollment consumed token' >&2; exit 1;
}

# A token authenticated before waiting for the lock must not authorize a
# replacement enrollment record with the same ID and a different secret.
seed_old
printf '%s\t%s\t%s\t%s\n' "$EID" "$ESECRET" "$EXPIRY" 'Test phone' > "$T/hub/state/enroll.tsv"
cp "$T/hub/state/devices.tsv" "$T/enroll-race-device-before"
replacement_secret='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
enroll_race="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$EID" "$ENONCE" "$ESIG" |
    env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
        BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=enroll_replace \
        BLAZE_TEST_EID="$EID" BLAZE_TEST_REPLACEMENT_SECRET="$replacement_secret" \
        BLAZE_TEST_EXPIRY="$EXPIRY" BLAZE_TEST_RACE_MARKER="$T/enroll-race-hit" \
        BLAZE_REAL_SYNC="$REAL_SYNC" BLAZE_SYNC_FAIL_AT=0 \
        BLAZE_SYNC_COUNT_FILE="$T/enroll-race-sync-count" \
        REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental")"
test -f "$T/enroll-race-hit" || {
    echo 'FAIL: enrollment lock-edge replacement was not exercised' >&2; exit 1;
}
printf '%s' "$enroll_race" | grep -Fq '"error":"enrollment changed"' || {
    printf '%s\n' "$enroll_race" | sed 's/"device_secret":"[^"]*"/"device_secret":"REDACTED"/' >&2
    echo 'FAIL: stale authenticated enrollment did not refuse changed token' >&2; exit 1;
}
cmp -s "$T/enroll-race-device-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: stale enrollment wrote a device' >&2; exit 1;
}
awk -F '\t' -v e="$EID" -v s="$replacement_secret" \
    '$1==e && $2==s {found++} END{exit(found==1?0:1)}' \
    "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: stale enrollment consumed replacement token' >&2; exit 1;
}

# A failed post-rename flush leaves a visible new device but an unconsumed
# enrollment token. Retrying that exact signed token must not issue a second
# device or a different secret after the response was lost.
run_enroll_sync_fault(){
    printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$EID" "$ENONCE" "$ESIG" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=none \
            BLAZE_REAL_SYNC="$REAL_SYNC" BLAZE_SYNC_FAIL_AT="$1" \
            BLAZE_SYNC_COUNT_FILE="$T/enroll-sync-count" \
            REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental"
}
seed_old
: > "$T/hub/state/policy.tsv"
printf '%s\t%s\t%s\t%s\n' "$EID" "$ESECRET" "$EXPIRY" 'Test phone' > "$T/hub/state/enroll.tsv"
rm -f "$T/enroll-sync-count"
first_enroll="$(run_enroll_sync_fault 2)"
printf '%s' "$first_enroll" | grep -Fq '"ok":false' || {
    echo 'FAIL: uncertain first enrollment received a positive ACK' >&2; exit 1;
}
first_count="$(awk -F '\t' '$1!="@op" && $1!="@enroll" {n++} END{print n+0}' "$T/hub/state/devices.tsv")"
[ "$first_count" -eq 2 ] || {
    echo 'FAIL: post-rename enrollment fault did not leave one new device' >&2; exit 1;
}
receipt_device="$(awk -F '\t' -v e="$EID" '$1=="@enroll" && $2==e {print $4; n++} END{if(n!=1)exit 1}' "$T/hub/state/devices.tsv")" || {
    echo 'FAIL: first enrollment did not atomically save one receipt' >&2; exit 1;
}
receipt_secret="$(awk -F '\t' -v e="$EID" '$1=="@enroll" && $2==e {print $5}' "$T/hub/state/devices.tsv")"
rm -f "$T/enroll-sync-count"
retry_enroll="$(run_enroll_sync_fault 0)"
printf '%s' "$retry_enroll" | grep -Fq '"ok":true' || {
    echo 'FAIL: same-token enrollment retry did not resolve' >&2; exit 1;
}
retry_count="$(awk -F '\t' '$1!="@op" && $1!="@enroll" {n++} END{print n+0}' "$T/hub/state/devices.tsv")"
[ "$retry_count" -eq 2 ] || {
    echo 'FAIL: uncertain enrollment retry issued a second device' >&2; exit 1;
}
printf '%s' "$retry_enroll" | grep -Fq "\"device_id\":\"$receipt_device\"" || {
    echo 'FAIL: retry did not return the recorded device' >&2; exit 1;
}
printf '%s' "$retry_enroll" | grep -Fq "\"device_secret\":\"$receipt_secret\"" || {
    echo 'FAIL: retry did not return the recorded credential' >&2; exit 1;
}
printf '%s' "$retry_enroll" | grep -Fq '"replayed":true' || {
    echo 'FAIL: retry ACK was not marked as replay' >&2; exit 1;
}
cp "$T/hub/state/devices.tsv" "$T/enroll-receipt-before"
test ! -s "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: successful replay left the enrollment token active' >&2; exit 1;
}
again_enroll="$(run_enroll_sync_fault 0)"
printf '%s' "$again_enroll" | grep -Fq "\"device_secret\":\"$receipt_secret\"" || {
    echo 'FAIL: retry after token consumption lost the recorded credential' >&2; exit 1;
}
cmp -s "$T/enroll-receipt-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: retry after token consumption rewrote saved devices' >&2; exit 1;
}
awk -F '\t' -v d="$receipt_device" 'BEGIN{OFS="\t"} $1==d {$2="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"} {print}' \
    "$T/enroll-receipt-before" > "$T/hub/state/devices.tsv"
changed_enroll="$(run_enroll_sync_fault 0)"
printf '%s' "$changed_enroll" | grep -Fq '"error":"enrollment device changed"' || {
    echo 'FAIL: changed device credential received enrollment replay' >&2; exit 1;
}
cp "$T/enroll-receipt-before" "$T/hub/state/devices.tsv"
printf '@enroll\t%s\t%s\t%s\t%s\t%s\n' "$EID" "$ESECRET" "$receipt_device" "$receipt_secret" "$EXPIRY" >> "$T/hub/state/devices.tsv"
receipt_corrupt="$(run_enroll_sync_fault 0)"
printf '%s' "$receipt_corrupt" | grep -Fq '"error":"corrupt paid state"' || {
    echo 'FAIL: duplicate enrollment receipt was accepted' >&2; exit 1;
}

# An admin enrollment token must not be acknowledged after either failed
# flush. A pre-rename failure must leave the token file unchanged.
run_create_sync_fault(){
    printf 'action=enroll_create&label=Test%%20phone&ttl=%s&request_id=%s\n' "${3:-900}" "${2:-0123456789abcdef0123456789abcdef}" |
        env PATH="$T/bin:$PATH" BLAZE_RENTAL_BASE="$T/hub" \
            BLAZE_REAL_MKDIR="$REAL_MKDIR" BLAZE_RACE_MODE=none \
            BLAZE_REAL_SYNC="$REAL_SYNC" BLAZE_SYNC_FAIL_AT="$1" \
            BLAZE_SYNC_COUNT_FILE="$T/create-sync-count" \
            HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
            sh "$ROOT/root/www/cgi-bin/rental-admin"
}
seed_old
: > "$T/hub/state/enroll.tsv"
rm -f "$T/create-sync-count"
create_pre="$(run_create_sync_fault 1)"
printf '%s' "$create_pre" | grep -Fq '"ok":false' || {
    echo 'FAIL: pre-rename enrollment token flush received positive ACK' >&2; exit 1;
}
test ! -s "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: pre-rename enrollment token failure changed token file' >&2; exit 1;
}
rm -f "$T/create-sync-count"
create_post="$(run_create_sync_fault 2)"
printf '%s' "$create_post" | grep -Fq '"ok":false' || {
    echo 'FAIL: post-rename enrollment token flush received positive ACK' >&2; exit 1;
}
: > "$T/hub/state/enroll.tsv"
printf 'bad-token-row\n' > "$T/hub/state/enroll.tsv"
cp "$T/hub/state/enroll.tsv" "$T/create-corrupt-before"
rm -f "$T/create-sync-count"
create_corrupt="$(run_create_sync_fault 0)"
printf '%s' "$create_corrupt" | grep -Fq '"error":"corrupt enrollment state"' || {
    echo 'FAIL: corrupt enrollment token state was accepted' >&2; exit 1;
}
cmp -s "$T/create-corrupt-before" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: corrupt enrollment token state was rewritten' >&2; exit 1;
}
: > "$T/hub/state/enroll.tsv"
rm -f "$T/create-sync-count"
create_ok="$(run_create_sync_fault 0)"
printf '%s' "$create_ok" | grep -Fq '"ok":true' || {
    echo 'FAIL: healthy enrollment token issuance refused' >&2; exit 1;
}
awk -F '\t' 'NF==4 {n++} END {exit n==1?0:1}' "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: healthy enrollment token was not saved exactly once' >&2; exit 1;
}

# A lost response after the token-file rename must resolve the same operator
# request ID to the original live token; retry must not issue a second token.
: > "$T/hub/state/enroll.tsv"
rm -f "$T/create-sync-count"
create_lost="$(run_create_sync_fault 2)"
printf '%s' "$create_lost" | grep -Fq '"ok":false' || {
    echo 'FAIL: lost token-create response received positive ACK' >&2; exit 1;
}
first_token="$(awk -F '\t' '$1!="@create" {print $1"."$2; n++} END{if(n!=1)exit 1}' "$T/hub/state/enroll.tsv")" || {
    echo 'FAIL: post-rename token-create fault did not leave one token' >&2; exit 1;
}
rm -f "$T/create-sync-count"
create_retry="$(run_create_sync_fault 0)"
printf '%s' "$create_retry" | grep -Fq "\"token\":\"$first_token\"" || {
    echo 'FAIL: token-create retry did not return the original token' >&2; exit 1;
}
awk -F '\t' '$1!="@create" {n++} END{exit n==1?0:1}' "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: token-create retry issued a second live token' >&2; exit 1;
}
cp "$T/hub/state/enroll.tsv" "$T/create-before-conflict"
create_conflict="$(run_create_sync_fault 0 0123456789abcdef0123456789abcdef 901)"
printf '%s' "$create_conflict" | grep -Fq '"error":"request id conflict"' || {
    echo 'FAIL: conflicting token-create request reused one ID' >&2; exit 1;
}
cmp -s "$T/create-before-conflict" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: conflicting token-create request changed token state' >&2; exit 1;
}
first_id="${first_token%%.*}"
awk -F '\t' -v i="$first_id" '$1!=i {print}' "$T/hub/state/enroll.tsv" > "$T/create-used"
cp "$T/create-used" "$T/hub/state/enroll.tsv"
create_used="$(run_create_sync_fault 0)"
printf '%s' "$create_used" | grep -Fq '"error":"enrollment already used or removed"' || {
    echo 'FAIL: consumed token-create request issued another token' >&2; exit 1;
}
cmp -s "$T/create-used" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: consumed token-create retry changed token state' >&2; exit 1;
}

# A small configured ceiling exercises the installed writers without making
# a huge fixture. Each refused write must leave its authority file unchanged.
seed_old
cp "$T/hub/state/devices.tsv" "$T/cap-devices-before"
cap_paid="$(printf 'action=add_time&device_id=%s&seconds=600&request_id=%s\n' "$DID" "$RID" |
    env BLAZE_RENTAL_MAX_STATE_BYTES=128 BLAZE_RENTAL_BASE="$T/hub" \
        HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$cap_paid" | grep -Fq '"ok":false' || {
    echo 'FAIL: paid receipt overflow received positive ACK' >&2; exit 1;
}
printf '%s' "$cap_paid" | grep -Fq 'receipt capacity reached' || {
    echo 'FAIL: paid receipt overflow did not report capacity' >&2; exit 1;
}
cmp -s "$T/cap-devices-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: paid receipt overflow changed saved devices' >&2; exit 1;
}
: > "$T/hub/state/enroll.tsv"
cp "$T/hub/state/enroll.tsv" "$T/cap-enroll-before"
cap_create="$(printf 'action=enroll_create&label=Test%%20phone&ttl=900&request_id=%s\n' "$RID" |
    env BLAZE_RENTAL_MAX_STATE_BYTES=128 BLAZE_RENTAL_BASE="$T/hub" \
        HTTP_X_BLAZE_RENTAL_ADMIN=known-token REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$cap_create" | grep -Fq '"ok":false' || {
    echo 'FAIL: token receipt overflow received positive ACK' >&2; exit 1;
}
printf '%s' "$cap_create" | grep -Fq 'enrollment capacity reached' || {
    echo 'FAIL: token receipt overflow did not report capacity' >&2; exit 1;
}
cmp -s "$T/cap-enroll-before" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: token receipt overflow changed saved tokens' >&2; exit 1;
}
printf '%s\t%s\t%s\t%s\n' "$EID" "$ESECRET" "$EXPIRY" 'Test phone' > "$T/hub/state/enroll.tsv"
cp "$T/hub/state/enroll.tsv" "$T/cap-phone-token-before"
cap_phone="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$EID" "$ENONCE" "$ESIG" |
    env BLAZE_RENTAL_MAX_STATE_BYTES=128 BLAZE_RENTAL_BASE="$T/hub" \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental")"
printf '%s' "$cap_phone" | grep -Fq '"ok":false' || {
    echo 'FAIL: phone receipt overflow received positive ACK' >&2; exit 1;
}
printf '%s' "$cap_phone" | grep -Fq 'receipt capacity reached' || {
    echo 'FAIL: phone receipt overflow did not report capacity' >&2; exit 1;
}
cmp -s "$T/cap-devices-before" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: phone receipt overflow changed saved devices' >&2; exit 1;
}
cmp -s "$T/cap-phone-token-before" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: phone receipt overflow consumed token' >&2; exit 1;
}
# Startup must never reconstruct a lost paid or token authority file.
cp "$T/hub/state/devices.tsv" "$T/missing-devices-snapshot"
cp "$T/hub/state/enroll.tsv" "$T/missing-enroll-snapshot"
rm "$T/hub/state/devices.tsv"
missing_devices="$(printf 'action=enroll_create&label=Test%%20phone&ttl=900&request_id=%032x\n' 999 |
    env BLAZE_RENTAL_BASE="$T/hub" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$missing_devices" | grep -Fq 'authority state missing or unsafe' || {
    echo 'FAIL: missing paid authority was accepted or silently recreated' >&2; exit 1;
}
test ! -e "$T/hub/state/devices.tsv" || {
    echo 'FAIL: missing paid authority was recreated' >&2; exit 1;
}
cmp -s "$T/missing-enroll-snapshot" "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: missing paid authority changed token state' >&2; exit 1;
}
cp "$T/missing-devices-snapshot" "$T/hub/state/devices.tsv"
rm "$T/hub/state/enroll.tsv"
missing_tokens="$(printf 'action=enroll_create&label=Test%%20phone&ttl=900&request_id=%032x\n' 998 |
    env BLAZE_RENTAL_BASE="$T/hub" HTTP_X_BLAZE_RENTAL_ADMIN=known-token \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$missing_tokens" | grep -Fq 'authority state missing or unsafe' || {
    echo 'FAIL: missing token authority was accepted or silently recreated' >&2; exit 1;
}
test ! -e "$T/hub/state/enroll.tsv" || {
    echo 'FAIL: missing token authority was recreated' >&2; exit 1;
}
cmp -s "$T/missing-devices-snapshot" "$T/hub/state/devices.tsv" || {
    echo 'FAIL: missing token authority changed paid state' >&2; exit 1;
}
cp "$T/missing-enroll-snapshot" "$T/hub/state/enroll.tsv"
echo 'Standalone rental lock-edge lease refusal PASS'
