#!/bin/sh
BP_RENTAL_UPDATE_FILE=${BP_RENTAL_UPDATE_FILE:-$BP_STATE/rental-update.tsv}

bp_rental_update_init() {
    mkdir -p "$BP_STATE"
    [ -f "$BP_RENTAL_UPDATE_FILE" ] || : > "$BP_RENTAL_UPDATE_FILE"
    chmod 600 "$BP_RENTAL_UPDATE_FILE"
}

bp_rental_update_url_ok() {
    # Fail closed on URL-like strings with no hostname or embedded credentials.
    # This is syntax filtering; downloaded APKs additionally require SHA-256
    # and the permanent BlazeRental signing certificate on the Android side.
    case "$1" in https://*) ;; *) return 1;; esac
    [ "$(printf '%s' "$1" | wc -c)" -le 512 ] || return 1
    printf '%s' "$1" | grep -q '[[:space:][:cntrl:]]' && return 1
    case "$1" in *'#'*) return 1;; esac
    printf '%s' "$1" | grep -Fq '\' && return 1
    authority="${1#https://}"
    authority="${authority%%/*}"
    authority="${authority%%\?*}"
    case "$authority" in ''|:*|*@*|'[]'*|'[') return 1;; esac
    return 0
}

bp_rental_update_sha_ok() { printf '%s' "$1" | grep -Eq '^[0-9a-fA-F]{64}$'; }

bp_rental_update_set() {
    version="$1"; code="$2"; url="$3"; sha="$4"; rollback_version="$5"; rollback_code="$6"; rollback_url="$7"; rollback_sha="$8"
    printf '%s' "$version" | grep -Eq '^[A-Za-z0-9._+-]{1,32}$' || return 2
    case "$code" in ''|*[!0-9]*) return 2;; esac
    [ "$code" -gt 0 ] 2>/dev/null || return 2
    bp_rental_update_url_ok "$url" || return 2
    bp_rental_update_sha_ok "$sha" || return 2
    if [ -n "$rollback_url" ]; then
        printf '%s' "$rollback_version" | grep -Eq '^[A-Za-z0-9._+-]{1,48}$' || return 2
        case "$rollback_code" in ''|*[!0-9]*) return 2;; esac
        [ "$rollback_code" -gt "$code" ] 2>/dev/null || return 2
        bp_rental_update_url_ok "$rollback_url" || return 2
        bp_rental_update_sha_ok "$rollback_sha" || return 2
    fi
    tmp="$BP_RENTAL_UPDATE_FILE.tmp.$$"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n'       "$version" "$code" "$url" "$(printf '%s' "$sha" | tr A-F a-f)"       "$rollback_version" "$rollback_code" "$rollback_url" "$(printf '%s' "$rollback_sha" | tr A-F a-f)" > "$tmp" || return 1
    chmod 600 "$tmp"; mv "$tmp" "$BP_RENTAL_UPDATE_FILE"
}

bp_rental_update_line() { bp_rental_update_init; head -n1 "$BP_RENTAL_UPDATE_FILE"; }

bp_rental_update_json() {
    line="$(bp_rental_update_line)"
    [ -n "$line" ] || { printf '{"available":false}'; return; }
    IFS="$(printf '\t')" read -r version code url sha rollback_version rollback_code rollback_url rollback_sha <<EOF
$line
EOF
    printf '{"available":true,"version":"%s","version_code":%s,"apk_url":"%s","apk_sha256":"%s","rollback_version":"%s","rollback_version_code":%s,"rollback_url":"%s","rollback_sha256":"%s"}'       "$(bp_json_escape "$version")" "${code:-0}" "$(bp_json_escape "$url")" "$(bp_json_escape "$sha")"       "$(bp_json_escape "$rollback_version")" "${rollback_code:-0}" "$(bp_json_escape "$rollback_url")" "$(bp_json_escape "$rollback_sha")"
}
