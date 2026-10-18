#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/fail-bin" "$T/admin/state" "$T/app/state"
for command in hexdump od; do
    printf '#!/bin/sh\nexit 1\n' > "$T/fail-bin/$command"
    chmod 755 "$T/fail-bin/$command"
done

admin_function="$(sed -n '/^admin_token_hex(){/,/^}/p' "$ROOT/install.sh")"
test -n "$admin_function" || { echo 'FAIL: installer entropy function missing' >&2; exit 1; }
if (eval "$admin_function"; PATH="$T/fail-bin:$PATH"; export PATH; admin_token_hex >/dev/null); then
    echo 'FAIL: installer accepted missing random bytes' >&2; exit 1
fi
admin_token="$(eval "$admin_function"; admin_token_hex)"
printf '%s' "$admin_token" | grep -Eq '^[0-9a-f]{48}$' || {
    echo 'FAIL: installer did not produce a complete admin token' >&2; exit 1;
}

printf 'known-token\n' > "$T/admin/admin.token"
admin_response="$(printf 'action=enroll_create&admin_token=known-token&ttl=900\n' |
    env -u HTTP_X_BLAZE_RENTAL_ADMIN PATH="$T/fail-bin:$PATH" \
        BLAZE_RENTAL_BASE="$T/admin" REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$admin_response" | grep -Fq '"ok":false' || {
    echo 'FAIL: admin issued a token with no random bytes' >&2; exit 1;
}
test ! -s "$T/admin/state/enroll.tsv" || {
    echo 'FAIL: admin wrote an enrollment with no random bytes' >&2; exit 1;
}

eid='abcdef123456'
secret='0123456789abcdef0123456789abcdef0123'
nonce='abcdefgh'
token="$eid.$secret"
expires="$(($(date +%s) + 900))"
printf '%s\t%s\t%s\t%s\n' "$eid" "$secret" "$expires" 'Test phone' > "$T/app/state/enroll.tsv"
before="$(sha256sum "$T/app/state/enroll.tsv" | awk '{print $1}')"
sig="$(printf 'enroll|%s|%s' "$nonce" "$token" |
    openssl dgst -sha256 -hmac "$token" | awk '{print $NF}')"
app_response="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$eid" "$nonce" "$sig" |
    env PATH="$T/fail-bin:$PATH" BLAZE_RENTAL_BASE="$T/app" \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental")"
printf '%s' "$app_response" | grep -Fq '"ok":false' || {
    echo 'FAIL: app issued a device secret with no random bytes' >&2; exit 1;
}
test "$(sha256sum "$T/app/state/enroll.tsv" | awk '{print $1}')" = "$before" || {
    echo 'FAIL: enrollment token consumed after entropy failure' >&2; exit 1;
}
test ! -s "$T/app/state/devices.tsv" || {
    echo 'FAIL: device written after entropy failure' >&2; exit 1;
}

good_admin_response="$(printf 'action=enroll_create&admin_token=known-token&ttl=900\n' |
    env -u HTTP_X_BLAZE_RENTAL_ADMIN BLAZE_RENTAL_BASE="$T/admin" \
        REQUEST_METHOD=POST sh "$ROOT/root/www/cgi-bin/rental-admin")"
printf '%s' "$good_admin_response" | grep -Fq '"ok":true' || {
    printf '%s\n' "$good_admin_response" | sed 's/"token":"[^"]*"/"token":"REDACTED"/' >&2
    echo 'FAIL: healthy entropy did not issue enrollment' >&2; exit 1;
}
good_app_response="$(printf 'action=enroll&enroll_id=%s&nonce=%s&sig=%s\n' "$eid" "$nonce" "$sig" |
    env BLAZE_RENTAL_BASE="$T/app" REQUEST_METHOD=POST \
        sh "$ROOT/root/www/cgi-bin/rental")"
printf '%s' "$good_app_response" | grep -Fq '"ok":true' || {
    printf '%s\n' "$good_app_response" | sed 's/"device_secret":"[^"]*"/"device_secret":"REDACTED"/' >&2
    echo 'FAIL: healthy entropy did not enroll device' >&2; exit 1;
}
echo 'Standalone rental entropy failure refusal PASS'
