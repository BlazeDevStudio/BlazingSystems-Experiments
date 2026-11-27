#!/bin/sh
# BlazePwifi transactional overlay updater.
# Normal feature/revision updates are applied to the writable overlay and do
# not require reflashing the base OpenWrt image.

BP_UPDATE_ROOT=${BP_UPDATE_ROOT:-/etc/blazepwifi/update}
BP_UPDATE_RUN=${BP_UPDATE_RUN:-/tmp/blazepwifi-update}
BP_UPDATE_HISTORY="$BP_UPDATE_ROOT/history.tsv"
BP_UPDATE_PENDING="$BP_UPDATE_ROOT/pending.env"
BP_UPDATE_STABLE="$BP_UPDATE_ROOT/stable.env"
BP_UPDATE_LAST_ROLLBACK="$BP_UPDATE_ROOT/last-rollback.env"
BP_UPDATE_LOCK="$BP_UPDATE_RUN/update.lock"
BP_UPDATE_MAX_BYTES=${BP_UPDATE_MAX_BYTES:-67108864}

bp_update_init() {
    mkdir -p "$BP_UPDATE_ROOT/snapshots" "$BP_UPDATE_RUN"
    chmod 700 "$BP_UPDATE_ROOT" "$BP_UPDATE_ROOT/snapshots" "$BP_UPDATE_RUN"
    touch "$BP_UPDATE_HISTORY"
    chmod 600 "$BP_UPDATE_HISTORY"
}

bp_update_current_version() {
    if [ -r /usr/share/blazepwifi/VERSION ]; then cat /usr/share/blazepwifi/VERSION
    elif [ -r /etc/blazepwifi/VERSION ]; then cat /etc/blazepwifi/VERSION
    else printf 'unknown\n'; fi
}

bp_update_path_allowed() {
    p="$1"
    if [ -n "${BP_UPDATE_TEST_PREFIX:-}" ]; then
        case "$p" in "$BP_UPDATE_TEST_PREFIX"/*) return 0;; esac
    fi
    case "$p" in
        /usr/lib/blazepwifi/*|/usr/sbin/blazepwifi-*|/usr/sbin/blazepwifi-core|/www/blazepwifi/*|/etc/init.d/blazepwifi*|/usr/share/blazepwifi/*|/etc/uci-defaults/99-blazepwifi)
            return 0 ;;
        *) return 1 ;;
    esac
}

bp_update_lock() {
    bp_update_init
    exec 8>"$BP_UPDATE_LOCK"
    flock -w 15 8
}

bp_update_unlock() { flock -u 8 2>/dev/null || true; exec 8>&-; }

bp_update_env_get() {
    file="$1"; key="$2"
    [ -r "$file" ] || return 0
    sed -n "s/^${key}=//p" "$file" | head -n1
}

bp_update_write_env() {
    file="$1"; shift
    tmp="$file.tmp.$$"
    : > "$tmp" || return 1
    chmod 600 "$tmp"
    for kv in "$@"; do printf '%s\n' "$kv" >> "$tmp"; done
    mv "$tmp" "$file"
}

bp_update_history() {
    printf '%s\t%s\t%s\t%s\n' "$(date +%s)" "$1" "$2" "$3" >> "$BP_UPDATE_HISTORY"
}

bp_update_sha256_file() { sha256sum "$1" | awk '{print $1}'; }

bp_update_safe_archive() {
    bundle="$1"
    tar -tzf "$bundle" 2>/dev/null | awk '
      /^\// {bad=1}
      /(^|\/)\.\.($|\/)/ {bad=1}
      END {exit bad?1:0}
    '
}

bp_update_extract_verify() {
    bundle="$1"; out="$2"; expected="${3:-}"
    [ -s "$bundle" ] || { echo "bundle missing" >&2; return 1; }
    size="$(wc -c < "$bundle" | tr -d ' ')"
    [ "$size" -le "$BP_UPDATE_MAX_BYTES" ] 2>/dev/null || { echo "bundle too large" >&2; return 1; }
    if [ -n "$expected" ]; then
        printf '%s' "$expected" | grep -Eq '^[0-9a-fA-F]{64}$' || { echo "invalid expected sha256" >&2; return 1; }
        actual="$(bp_update_sha256_file "$bundle")"
        [ "$(printf '%s' "$actual" | tr A-F a-f)" = "$(printf '%s' "$expected" | tr A-F a-f)" ] || { echo "bundle sha256 mismatch" >&2; return 1; }
    fi
    bp_update_safe_archive "$bundle" || { echo "unsafe archive paths" >&2; return 1; }
    rm -rf "$out"; mkdir -p "$out"
    tar -xzf "$bundle" -C "$out" || return 1
    [ -r "$out/release.env" ] && [ -r "$out/manifest.tsv" ] && [ -d "$out/payload" ] || { echo "invalid bundle layout" >&2; return 1; }

    while IFS="$(printf '\t')" read -r sha mode path; do
        [ -n "$sha" ] || continue
        printf '%s' "$sha" | grep -Eq '^[0-9a-f]{64}$' || { echo "bad manifest sha" >&2; return 1; }
        printf '%s' "$mode" | grep -Eq '^[0-7]{3,4}$' || { echo "bad manifest mode" >&2; return 1; }
        bp_update_path_allowed "$path" || { echo "path not allowed: $path" >&2; return 1; }
        src="$out/payload/${path#/}"
        [ -f "$src" ] || { echo "payload missing: $path" >&2; return 1; }
        [ "$(bp_update_sha256_file "$src")" = "$sha" ] || { echo "payload checksum failed: $path" >&2; return 1; }
    done < "$out/manifest.tsv"

    if [ -r "$out/manifest.sig" ] && [ -r "$BP_UPDATE_ROOT/trusted.pub" ] && command -v usign >/dev/null 2>&1; then
        usign -V -p "$BP_UPDATE_ROOT/trusted.pub" -m "$out/manifest.tsv" -x "$out/manifest.sig" || {
            echo "update signature verification failed" >&2; return 1;
        }
    fi
}

bp_update_release_value() {
    file="$1"; key="$2"
    sed -n "s/^${key}=//p" "$file" | head -n1
}

bp_update_snapshot() {
    extracted="$1"; id="$2"; previous="$3"
    snap="$BP_UPDATE_ROOT/snapshots/$id"
    rm -rf "$snap"; mkdir -p "$snap/files"
    cp "$extracted/manifest.tsv" "$snap/targets.tsv"
    : > "$snap/absent.txt"
    while IFS="$(printf '\t')" read -r sha mode path; do
        [ -n "$sha" ] || continue
        rel="${path#/}"
        if [ -e "$path" ] || [ -L "$path" ]; then
            mkdir -p "$snap/files/$(dirname "$rel")"
            cp -p "$path" "$snap/files/$rel" || return 1
        else
            printf '%s\n' "$path" >> "$snap/absent.txt"
        fi
    done < "$extracted/manifest.tsv"
    tar -czf "$snap/files.tar.gz" -C "$snap/files" .
    rm -rf "$snap/files"
    bp_update_write_env "$snap/meta.env" "PREVIOUS_VERSION=$previous" "CREATED_AT=$(date +%s)"
}

bp_update_apply_payload() {
    extracted="$1"
    while IFS="$(printf '\t')" read -r sha mode path; do
        [ -n "$sha" ] || continue
        src="$extracted/payload/${path#/}"
        dir="$(dirname "$path")"; mkdir -p "$dir" || return 1
        tmp="$dir/.bp-update.$$.$(basename "$path")"
        cp "$src" "$tmp" || return 1
        chmod "$mode" "$tmp" || { rm -f "$tmp"; return 1; }
        mv "$tmp" "$path" || return 1
    done < "$extracted/manifest.tsv"
    sync 2>/dev/null || true
}

bp_update_health() {
    if [ -n "${BP_UPDATE_HEALTH_HOOK:-}" ]; then sh -c "$BP_UPDATE_HEALTH_HOOK"; return; fi
    [ -x /usr/sbin/blazepwifi-core ] || return 1
    [ -r /usr/lib/blazepwifi/common.sh ] || return 1
    for f in /usr/lib/blazepwifi/*.sh /www/blazepwifi/cgi-bin/*; do
        [ -f "$f" ] || continue
        sh -n "$f" >/dev/null 2>&1 || return 1
    done
    /etc/init.d/blazepwifi restart >/dev/null 2>&1 || return 1
    sleep 2
    pgrep -f '/usr/sbin/blazepwifi-core' >/dev/null 2>&1 || return 1
    return 0
}

bp_update_restore_snapshot() {
    id="$1"; reason="${2:-manual}"
    snap="$BP_UPDATE_ROOT/snapshots/$id"
    [ -r "$snap/targets.tsv" ] && [ -r "$snap/files.tar.gz" ] || { echo "rollback snapshot unavailable" >&2; return 1; }
    work="$BP_UPDATE_RUN/rollback.$$"; rm -rf "$work"; mkdir -p "$work"
    tar -xzf "$snap/files.tar.gz" -C "$work" || return 1
    while IFS="$(printf '\t')" read -r sha mode path; do
        [ -n "$sha" ] || continue
        rel="${path#/}"
        if grep -Fxq "$path" "$snap/absent.txt" 2>/dev/null; then
            rm -f "$path"
        elif [ -e "$work/$rel" ] || [ -L "$work/$rel" ]; then
            mkdir -p "$(dirname "$path")"
            cp -p "$work/$rel" "$path" || return 1
        fi
    done < "$snap/targets.tsv"
    rm -rf "$work"
    previous="$(bp_update_env_get "$snap/meta.env" PREVIOUS_VERSION)"
    rm -f "$BP_UPDATE_PENDING"
    bp_update_write_env "$BP_UPDATE_STABLE" "VERSION=${previous:-unknown}" "PROMOTED_AT=$(date +%s)" "SOURCE=rollback:$id"
    bp_update_history rollback "${previous:-unknown}" "$reason:$id"
    bp_update_health || return 1
    return 0
}

bp_update_apply() {
    bundle="$1"; expected="${2:-}"
    bp_update_lock || { echo "another update is running" >&2; return 1; }
    if [ -r "$BP_UPDATE_PENDING" ]; then
        echo "an update candidate is still pending health promotion; promote or roll it back first" >&2
        bp_update_unlock
        return 1
    fi
    extracted="$BP_UPDATE_RUN/extracted.$$"
    if ! bp_update_extract_verify "$bundle" "$extracted" "$expected"; then bp_update_unlock; return 1; fi
    release="$extracted/release.env"
    version="$(bp_update_release_value "$release" VERSION)"
    [ -n "$version" ] || { echo "bundle version missing" >&2; rm -rf "$extracted"; bp_update_unlock; return 1; }
    previous="$(bp_update_current_version)"
    grace="$(uci -q get blazepwifi.main.update_stability_seconds 2>/dev/null || true)"
    [ -n "$grace" ] || grace="$(bp_update_release_value "$release" STABILITY_GRACE_SECONDS)"
    [ -n "$grace" ] || grace=600
    case "$grace" in ''|*[!0-9]*) grace=600;; esac
    [ -r "$BP_UPDATE_STABLE" ] || bp_update_write_env "$BP_UPDATE_STABLE" "VERSION=$previous" "PROMOTED_AT=$(date +%s)" "SOURCE=pre-update"

    id="$(date +%Y%m%d%H%M%S)-$$"
    bp_update_snapshot "$extracted" "$id" "$previous" || { rm -rf "$extracted"; bp_update_unlock; return 1; }
    cp "$bundle" "$BP_UPDATE_ROOT/snapshots/$id/update-bundle.tar.gz" 2>/dev/null || true

    if ! bp_update_apply_payload "$extracted"; then
        bp_update_restore_snapshot "$id" apply-failed >/dev/null 2>&1 || true
        rm -rf "$extracted"; bp_update_unlock; return 1
    fi
    [ -x /usr/lib/blazepwifi/update-migrate.sh ] && /usr/lib/blazepwifi/update-migrate.sh "$previous" "$version" || true
    if ! bp_update_health; then
        bp_update_restore_snapshot "$id" health-failed >/dev/null 2>&1 || true
        rm -rf "$extracted"; bp_update_unlock; return 1
    fi

    now="$(date +%s)"
    bp_update_write_env "$BP_UPDATE_PENDING"         "VERSION=$version" "PREVIOUS_VERSION=$previous" "SNAPSHOT_ID=$id"         "APPLIED_AT=$now" "PROMOTE_AFTER=$((now+grace))" "FAILURES=0"
    bp_update_write_env "$BP_UPDATE_LAST_ROLLBACK" "SNAPSHOT_ID=$id" "VERSION=$previous"
    bp_update_history candidate "$version" "from:$previous snapshot:$id"
    # Promote after real service time even when the device is not rebooted.
    # All descriptors are redirected so the detached guard cannot hold a CGI
    # connection open.
    (
        sleep "$grace"
        /usr/sbin/blazepwifi-update guard
    ) >"$BP_UPDATE_RUN/promote-$id.log" 2>&1 </dev/null &
    rm -rf "$extracted"
    bp_update_unlock
    return 0
}

bp_update_prune_snapshots() {
    keep="$(uci -q get blazepwifi.main.update_retention 2>/dev/null || true)"
    case "$keep" in ''|*[!0-9]*) keep=3;; esac
    [ "$keep" -ge 1 ] 2>/dev/null || keep=1
    protected="$(bp_update_env_get "$BP_UPDATE_LAST_ROLLBACK" SNAPSHOT_ID)"
    count=0
    for d in $(ls -1dt "$BP_UPDATE_ROOT"/snapshots/* 2>/dev/null || true); do
        [ -d "$d" ] || continue
        id="$(basename "$d")"
        [ "$id" = "$protected" ] && continue
        count=$((count+1))
        [ "$count" -le "$keep" ] || rm -rf "$d"
    done
}

bp_update_guard() {
    bp_update_init
    [ -r "$BP_UPDATE_PENDING" ] || return 0
    bp_update_lock || return 1
    [ -r "$BP_UPDATE_PENDING" ] || { bp_update_unlock; return 0; }
    version="$(bp_update_env_get "$BP_UPDATE_PENDING" VERSION)"
    id="$(bp_update_env_get "$BP_UPDATE_PENDING" SNAPSHOT_ID)"
    promote="$(bp_update_env_get "$BP_UPDATE_PENDING" PROMOTE_AFTER)"
    failures="$(bp_update_env_get "$BP_UPDATE_PENDING" FAILURES)"; [ -n "$failures" ] || failures=0
    now="$(date +%s)"
    if ! bp_update_health; then
        failures=$((failures+1))
        if [ "$failures" -ge 2 ]; then
            bp_update_restore_snapshot "$id" boot-health-failed
            rc=$?
            bp_update_unlock
            return "$rc"
        fi
        sed -i "s/^FAILURES=.*/FAILURES=$failures/" "$BP_UPDATE_PENDING"
        bp_update_unlock
        return 1
    fi
    if [ -n "$promote" ] && [ "$now" -ge "$promote" ] 2>/dev/null; then
        bp_update_write_env "$BP_UPDATE_STABLE" "VERSION=$version" "PROMOTED_AT=$now" "SOURCE=health-grace"
        rm -f "$BP_UPDATE_PENDING"
        bp_update_history stable "$version" "health-grace-passed"
        bp_update_prune_snapshots
    fi
    bp_update_unlock
    return 0
}

bp_update_manual_rollback() {
    bp_update_lock || return 1
    if [ -r "$BP_UPDATE_PENDING" ]; then id="$(bp_update_env_get "$BP_UPDATE_PENDING" SNAPSHOT_ID)"
    else id="$(bp_update_env_get "$BP_UPDATE_LAST_ROLLBACK" SNAPSHOT_ID)"; fi
    [ -n "$id" ] || { echo "no rollback snapshot" >&2; bp_update_unlock; return 1; }
    bp_update_restore_snapshot "$id" manual
    rc=$?
    bp_update_unlock
    return "$rc"
}

bp_update_fetch() {
    url="$1"; out="$2"
    printf '%s' "$url" | grep -q '[[:space:][:cntrl:]]' && return 1
    case "$url" in https://*) ;; *) echo "https required" >&2; return 1;; esac
    prefix="$(uci -q get blazepwifi.main.update_source_url 2>/dev/null || true)"
    [ -n "$prefix" ] || prefix='https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/download/'
    case "$url" in "$prefix"*) ;; *) echo "url outside configured update source" >&2; return 1;; esac
    if command -v uclient-fetch >/dev/null 2>&1; then uclient-fetch -T 30 -O "$out" "$url"
    elif command -v wget >/dev/null 2>&1; then wget -T 30 -O "$out" "$url"
    else echo "no HTTPS fetcher available" >&2; return 1; fi
    [ -s "$out" ] || return 1
    [ "$(wc -c < "$out")" -le "$BP_UPDATE_MAX_BYTES" ] 2>/dev/null
}

bp_update_status_json() {
    current="$(bp_update_current_version)"
    stable="$(bp_update_env_get "$BP_UPDATE_STABLE" VERSION)"; [ -n "$stable" ] || stable="$current"
    pending="$(bp_update_env_get "$BP_UPDATE_PENDING" VERSION)"
    rollback="$(bp_update_env_get "$BP_UPDATE_LAST_ROLLBACK" VERSION)"
    promote="$(bp_update_env_get "$BP_UPDATE_PENDING" PROMOTE_AFTER)"
    printf '{"current":"%s","stable":"%s","pending":"%s","rollback":"%s","promote_after":%s,"rollback_available":%s}'       "$current" "$stable" "${pending:-}" "${rollback:-}" "${promote:-0}" "$([ -n "$rollback" ] && echo true || echo false)"
}
