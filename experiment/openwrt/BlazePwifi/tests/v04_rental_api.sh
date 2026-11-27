#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *durable_sync*) echo 0;;
 *rental_seconds_per_pulse*) echo 600;;
 *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_AUTH_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_RENTAL_POLICY_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
export BP_RENTAL_POLICY_V2="$T/state/rental-policy-v2.tsv"
. "$BP_LIB"; . "$BP_AUTH_LIB"; . "$BP_RENTAL_LIB"; . "$BP_RENTAL_POLICY_LIB"
bp_rental_init; bp_rental_policy_v2_init
D=0123456789abcdef01234567
S=00112233445566778899aabbccddeeff0011223344556677
bp_rental_device_write "$D" "$S" 1 'Phone' 1
bp_rental_policy_ensure "$D"; bp_rental_policy_migrate "$D"
CGI="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/rental"
N=abc123
SIG="$(bp_rental_hmac "$S" "status|$N|$S")"
OUT="$(printf 'action=status&device_id=%s&nonce=%s&sig=%s' "$D" "$N" "$SIG" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$OUT" | grep -q '"policy_revision":1'
printf '%s' "$OUT" | grep -q '"policy_sig":"[0-9a-f]'
printf '%s' "$OUT" | grep -q '"policy_sig_v2":"[0-9a-f]'
printf '%s' "$OUT" | grep -q '"policy_sig_v3":"[0-9a-f]'
printf '%s' "$OUT" | grep -q '"timer_mode":"overlay"'
printf '%s' "$OUT" | grep -q '"notifications_enabled":1'
printf '%s' "$OUT" | grep -q '"admin_gesture_value":"4000"'
N2=patch1
CAN="policy_patch|$N2|$D|1|unrestricted|@keep|@keep|@keep|@keep|@keep|@keep|@keep|@keep"
SIG2="$(bp_rental_hmac "$S" "$CAN")"
OUT2="$(printf 'action=policy_patch&device_id=%s&nonce=%s&expected_revision=1&launcher_mode=unrestricted&allowed_packages=%%40keep&hidden_packages=%%40keep&preferred_vendo=%%40keep&timer_user_toggle=%%40keep&notifications_enabled=%%40keep&quick_controls=%%40keep&admin_gesture_value=%%40keep&admin_password=%%40keep&sig=%s' "$D" "$N2" "$SIG2" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$OUT2" | grep -q '"ok":true'
printf '%s' "$OUT2" | grep -q '"policy_revision":2'
N3=stale
SIG3="$(bp_rental_hmac "$S" "policy_patch|$N3|$D|1|rental|@keep|@keep|@keep|@keep|@keep|@keep|@keep|@keep")"
OUT3="$(printf 'action=policy_patch&device_id=%s&nonce=%s&expected_revision=1&launcher_mode=rental&allowed_packages=%%40keep&hidden_packages=%%40keep&preferred_vendo=%%40keep&timer_user_toggle=%%40keep&notifications_enabled=%%40keep&quick_controls=%%40keep&admin_gesture_value=%%40keep&admin_password=%%40keep&sig=%s' "$D" "$N3" "$SIG3" | REQUEST_METHOD=POST sh "$CGI")"
printf '%s' "$OUT3" | grep -q 'stale policy revision'
grep -q '\[ "\$allowed" = "-" \] && allowed=""' "$CGI" || { echo "empty-list sentinel normalization missing" >&2; exit 1; }
echo "v0.4 rental API tests passed"
