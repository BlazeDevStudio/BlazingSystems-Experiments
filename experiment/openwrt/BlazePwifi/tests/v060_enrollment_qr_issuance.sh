#!/bin/sh
# QR-0658: actual full + R281 enrollment token writers. All tokens fake /tmp.
# A scannable binding or factory-reset provisioning QR must not be returned
# unless its one-time setup token is truly present in the local registry.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-qr-issue-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${QR_MV_FAIL:-}:${2:-}" in
  1:*/rental-enroll.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/"*
export PATH="$T/bin:$PATH" REQUEST_METHOD=GET
for profile in full r281; do
  (
    stage="$profile:setup"
    trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "QR-0658 FAIL profile=$profile stage=$stage rc=$rc" >&2; fi' EXIT
    case "$profile" in
      full) LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi";;
      r281) LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi";;
    esac
    export BP_STATE="$T/$profile/state" BP_RUN="$T/$profile/run"
    export BP_LIB="$LIB/common.sh" BP_AUTH_LIB="$LIB/auth.sh" BP_RENTAL_LIB="$LIB/rental.sh"
    . "$BP_LIB"
    . "$BP_AUTH_LIB"
    . "$BP_RENTAL_LIB"
    bp_rental_init
    state_sha() { sha256sum "$BP_RENTAL_ENROLL" | cut -d' ' -f1; }
    count_tokens() { awk -F '\t' 'NF>=4 {n++} END{print n+0}' "$BP_RENTAL_ENROLL"; }
    issue() { bp_rental_enroll_create "FictionalPhone" 600; }
    stage="$profile:two-nonconflicting-QR-tokens"
    bp_lock
    a="$(issue)"
    b="$(issue)"
    bp_unlock
    printf '%s' "$a" | LC_ALL=C grep -Eq '^[a-f0-9]{12}\.[a-f0-9]{36}$'
    printf '%s' "$b" | LC_ALL=C grep -Eq '^[a-f0-9]{12}\.[a-f0-9]{36}$'
    [ "$a" != "$b" ]
    [ "$(count_tokens)" -eq 2 ]
    [ "$(cut -f1 "$BP_RENTAL_ENROLL" | sort -u | wc -l | tr -d '[:space:]')" -eq 2 ]

    stage="$profile:injected-rename-no-token-ACK"
    before="$(state_sha)"
    export QR_MV_FAIL=1
    set +e
    bp_lock
    failed="$(issue)"
    code=$?
    bp_unlock
    set -e
    [ "$code" -ne 0 ] && [ -z "$failed" ] || {
      echo "QR-0658 emitted token despite failed persistent registry rename" >&2;exit 1;
    }
    [ "$(state_sha)" = "$before" ]
    unset QR_MV_FAIL

    stage="$profile:duplicate-ID-existing-source-refused"
    head -n 1 "$BP_RENTAL_ENROLL" > "$T/first-fake-token"
    cat "$T/first-fake-token" >> "$BP_RENTAL_ENROLL"
    before="$(state_sha)"
    set +e
    duplicate="$(issue)"
    code=$?
    set -e
    [ "$code" -ne 0 ] && [ -z "$duplicate" ]
    [ "$(state_sha)" = "$before" ]

    stage="$profile:malformed-source-refused"
    sed -i '$d' "$BP_RENTAL_ENROLL"
    printf 'broken\tpartial\n' >> "$BP_RENTAL_ENROLL"
    before="$(state_sha)"
    set +e
    malformed="$(issue)"
    code=$?
    set -e
    [ "$code" -ne 0 ] && [ -z "$malformed" ] && [ "$(state_sha)" = "$before" ]

    stage="$profile:symlink-registry-refused"
    sed -i '$d' "$BP_RENTAL_ENROLL"
    mv "$BP_RENTAL_ENROLL" "$T/$profile-registry"
    ln -s "$T/$profile-registry" "$BP_RENTAL_ENROLL"
    set +e
    link_token="$(issue)"
    code=$?
    set -e
    [ "$code" -ne 0 ] && [ -z "$link_token" ]
    [ "$(count_tokens)" -eq 2 ]
    rm "$BP_RENTAL_ENROLL"
    mv "$T/$profile-registry" "$BP_RENTAL_ENROLL"

    stage="$profile:admin-CGI-guarantees-failed-QR-not-returned"
    if [ "$profile" = full ]; then
      ADMIN="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/admin"
      [ "$(grep -Fc 'token="$(bp_rental_enroll_create "$label" 600)" ||' "$ADMIN")" -eq 2 ]
    else
      ADMIN="$ROOT/profiles/r281-rental/root/www/cgi-bin/rental-admin"
      grep -Fq 'token="$(bp_rental_enroll_create "${label:-Rental phone}" "$ttl")" ||' "$ADMIN"
    fi
    sh -n "$ADMIN"
    grep -Fq 'enrollment token storage failed; QR not issued' "$ADMIN"
    echo "QR-0658 $profile PASS: only stored tokens leave issuance, malformed/symlink/rename failure no QR, operator CGI refuses false ACK"
  )
done
echo 'NOT PRODUCTION OEM PROVISIONING: no Lineage-2 signer or physical Device Owner QR factory-reset acceptance; signed authoritative v2 ledger and source rollback still required'
