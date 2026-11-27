#!/bin/sh
# MIG-0656 — actual full and R281 legacy MAC paid-credit binding under EIO.
# Synthetic disposable accounts; no live finance or network configuration.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-legacy-bind-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -p "$T/bin"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
cat > "$T/bin/nft" <<'NFT'
#!/bin/sh
printf '%s\n' "$*" >> "$BP_NET_LOG"
NFT
cat > "$T/bin/mv" <<'MV'
#!/bin/sh
case "${MIG_FAULT:-}:${2:-}" in
  account:*/accounts.tsv|cleanup:*/credits.tsv) exit 74;;
esac
exec /bin/mv "$@"
MV
chmod 700 "$T/bin/"*
export PATH="$T/bin:$PATH"
MAC=aa:bb:cc:dd:ee:ff
D1=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
D2=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
D3=cccccccccccccccccccccccccccccccc
NOW="$(date +%s)"
EXPIRY=$((NOW+1200))
for profile in full r281; do
  (
    stage="$profile:init"
    trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "MIG-0656 FAILED stage=$stage profile=$profile rc=$rc" >&2; [ -f "$T/error.log" ] && cat "$T/error.log" >&2; fi' EXIT
    case "$profile" in
      full) LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh";;
      r281) LIB="$ROOT/profiles/r281-rental/root/usr/lib/blazepwifi/common.sh";;
    esac
    export BP_STATE="$T/$profile/state" BP_RUN="$T/$profile/run"
    export BP_NET_LOG="$T/$profile/network-actions.txt"
    export REQUEST_METHOD=GET
    . "$LIB"
    bp_init_dirs
    : > "$BP_NET_LOG"
    printf '%s\t200\n' "$MAC" > "$BP_LEGACY_CREDITS"
    printf '%s\t%s\n' "$MAC" "$EXPIRY" > "$BP_LEGACY_SESSIONS"
    chmod 600 "$BP_LEGACY_CREDITS" "$BP_LEGACY_SESSIONS"
    credits_sha="$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)"
    sessions_sha="$(sha256sum "$BP_LEGACY_SESSIONS" | cut -d' ' -f1)"
    account_credit() {
      awk -F '\t' -v d="$1" '$1==d {print $2;exit}' "$BP_ACCOUNTS"
    }
    assert_refused() {
      # Avoid the shell's global variable namespace: outer scenarios
      # also keep a "before" checksum of the original legacy cash source.
      refused_account_sha="$(sha256sum "$BP_ACCOUNTS" | cut -d' ' -f1)"
      set +e
      bp_lock
      bp_bind_device "$1" "$MAC" 10.1.1.9 1 >"$T/error.log" 2>&1
      status=$?
      bp_unlock
      set -e
      [ "$status" -ne 0 ] || {
        echo "$stage $profile: unsafe legacy bind acknowledged" >&2;exit 1;
      }
      [ "$(sha256sum "$BP_ACCOUNTS" | cut -d' ' -f1)" = "$refused_account_sha" ] || {
        echo "$stage $profile: account file changed" >&2;exit 1;
      }
    }

    stage="$profile:pre-account-rename-EIO"
    export MIG_FAULT=account
    assert_refused "$D1"
    [ "$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)" = "$credits_sha" ]
    [ "$(sha256sum "$BP_LEGACY_SESSIONS" | cut -d' ' -f1)" = "$sessions_sha" ]
    [ -f "$BP_PAID_UNCERTAIN" ]
    [ ! -s "$BP_NET_LOG" ]
    unset MIG_FAULT
    # On a real router an operator MUST reconcile the marker before retry;
    # only this disposable synthetic state can clear it for another scenario.
    set +e
    bp_lock
    bp_bind_device "$D1" "$MAC" 10.1.1.9 1 >"$T/error.log" 2>&1
    rc=$?
    bp_unlock
    set -e
    [ "$rc" -ne 0 ] && [ -f "$BP_PAID_UNCERTAIN" ]
    [ ! -s "$BP_ACCOUNTS" ]
    rm "$BP_PAID_UNCERTAIN"

    stage="$profile:clean-paid-legacy-migration"
    bp_lock
    bp_bind_device "$D1" "$MAC" 10.1.1.9 1
    bp_unlock
    [ "$(account_credit "$D1")" = 200 ]
    [ "$(awk -F '\t' -v d="$D1" '$1==d{print $3}' "$BP_ACCOUNTS")" = "$EXPIRY" ]
    [ ! -s "$BP_LEGACY_CREDITS" ] && [ ! -s "$BP_LEGACY_SESSIONS" ]
    [ ! -e "$BP_PAID_UNCERTAIN" ]
    grep -q "auth_macs" "$BP_NET_LOG"

    stage="$profile:claimed:prepare"
    printf '%s\t150\n' "$MAC" > "$BP_LEGACY_CREDITS"
    before="$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)"
    : > "$BP_NET_LOG"
    stage="$profile:claimed:reject-double-identity"
    assert_refused "$D2"
    stage="$profile:claimed:keep-legacy-evidence"
    [ "$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)" = "$before" ]
    stage="$profile:claimed:never-mint-new-credit"
    [ -z "$(account_credit "$D2")" ]
    stage="$profile:claimed:keep-first-paid-account"
    [ "$(account_credit "$D1")" = 200 ]
    stage="$profile:claimed:no-uncertain-financial-operation"
    [ ! -e "$BP_PAID_UNCERTAIN" ]
    stage="$profile:claimed:no-network-authorization"
    [ ! -s "$BP_NET_LOG" ]

    stage="$profile:ambiguous-legacy-record"
    : > "$BP_ACCOUNTS"
    printf '%s\t200\n%s\t300\n' "$MAC" "$MAC" > "$BP_LEGACY_CREDITS"
    before="$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)"
    assert_refused "$D3"
    [ "$(sha256sum "$BP_LEGACY_CREDITS" | cut -d' ' -f1)" = "$before" ]
    [ ! -e "$BP_PAID_UNCERTAIN" ]

    stage="$profile:cleanup-fault-after-credit-write"
    printf '%s\t200\n' "$MAC" > "$BP_LEGACY_CREDITS"
    printf '%s\t%s\n' "$MAC" "$EXPIRY" > "$BP_LEGACY_SESSIONS"
    export MIG_FAULT=cleanup
    set +e
    bp_lock
    bp_bind_device "$D3" "$MAC" 10.1.1.9 1 >"$T/error.log" 2>&1
    rc=$?
    bp_unlock
    set -e
    [ "$rc" -ne 0 ] || {
      echo "cleanup failure returned success: $profile" >&2;exit 1;
    }
    [ -f "$BP_PAID_UNCERTAIN" ]
    [ "$(account_credit "$D3")" = 200 ]
    [ "$(cat "$BP_LEGACY_CREDITS")" = "$(printf '%s\t200' "$MAC")" ]
    [ ! -s "$BP_NET_LOG" ]
    unset MIG_FAULT
    echo "MIG-0656 $profile PASS: no source-credit loss, clean carry, claimed-MAC denial, malformed source denial, EIO quarantine without paid access"
  )
done
echo 'MIG-0656 both full and R281 profile PASS — NOT production v2 crash atomic; separate TSVs still require signed durable migration and hardware powercut'
