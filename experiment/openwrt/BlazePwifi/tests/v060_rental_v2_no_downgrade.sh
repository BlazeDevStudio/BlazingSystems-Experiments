#!/bin/sh
# RENT-0726 P0 #32: real signed Vendo CGI must reject every rental_v2_*
# action before heartbeat, receipt, target progress or any paid mutation.
# This is a synthetic NO-PRODUCTION-AUTHORITY test. No v2 credits issued.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
T="$(mktemp -d /tmp/blaze-rent-v2-no-downgrade-XXXXXX)"
trap 'rm -rf "$T"' EXIT HUP INT TERM
mkdir -m 700 "$T/bin" "$T/state" "$T/run" "$T/state/targets"
cat >"$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') printf 'synthetic-rental-secret\n';;
  *'get blazepwifi.main.vendo_port') printf '4455\n';;
  *'get blazepwifi.main.durable_sync') printf '0\n';;
  *) exit 1;;
esac
UCI
chmod 700 "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
export BP_RENTAL_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
export BP_CONTROLLER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
export BP_MEMBER_LIB="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/member.sh"
export REQUEST_METHOD=POST SERVER_PORT=4455 REMOTE_ADDR=10.1.2.3
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"

call() {
  action="$1"; target="$2"; pulses="$3"; nonce="$4"
  sig="$(printf 'synthetic-rental-secret|%s|vendo-01|%s|%s|%s|synthetic-rental-secret' \
    "$action" "$nonce" "$pulses" "$target" | sha256sum | cut -d' ' -f1)"
  printf 'action=%s&id=vendo-01&nonce=%s&pulses=%s&target=%s&sig=%s\n' \
    "$action" "$nonce" "$pulses" "$target" "$sig" | sh "$VENDO"
}

# Prove baseline signed legacy controller heartbeat still works. This
# creates the normal synthetic run/state files BEFORE taking the snapshots.
boot="$(call ping placeholder 0 aabbccddee112233)"
printf '%s' "$boot" | grep -q '"ok":true' || {
  echo 'RENT-0726 baseline signed ping unavailable' >&2;exit 1;
}
printf 'dev01\tfake-rental-secret\t2140000000\tSynthetic Rental\t1234\n' > "$BP_STATE/rental-devices.tsv"
printf 'existing-receipt\tdev01\t2140000000\t1234\t3\n' > "$BP_STATE/rental-events.tsv"
printf 'dev01\taa:bb:cc:dd:ee:ff\taabbccddeeff0011\t2147483000\tvendo-01\trental\n' > "$BP_STATE/targets/vendo-01.tsv"
printf '3\n' > "$BP_STATE/targets/vendo-01.progress"
printf 'alice\tAlice\t1\tsha256i\tsalt\thash\t4096\t900\t1\t1234\tfixture\n' > "$BP_STATE/members.tsv"
printf 'original-receipt\n' > "$BP_STATE/member-events.tsv"
printf '1\n' > "$BP_STATE/member-revision"
chmod 600 "$BP_STATE/"*.tsv "$BP_STATE/member-revision" "$BP_STATE/targets/"*
FILES="$BP_STATE/rental-devices.tsv $BP_STATE/rental-events.tsv $BP_STATE/members.tsv $BP_STATE/member-events.tsv $BP_STATE/member-revision $BP_STATE/targets/vendo-01.tsv $BP_STATE/targets/vendo-01.progress $BP_RUN/vendos.tsv"
# shellcheck disable=SC2086
before="$(sha256sum $FILES)"
for op in rental_v2_negotiate rental_v2_commit rental_v2_replay rental_v2_lease; do
  response="$(call "$op" 'dev01:aabbccddeeff0011' 2 deadbeef00112233)"
  printf '%s' "$response" | grep -q '"ok":false' || {
    echo "RENT-0726 false v2 success: $op" >&2;exit 1;
  }
  printf '%s' "$response" | grep -q 'rental v2 authority unavailable; no v1 fallback' || {
    echo "RENT-0726 missing strict v2 denial: $op" >&2;exit 1;
  }
  ! printf '%s' "$response" | grep -q '"lease_until"\|"duplicate":true\|"credited_cents"' || exit 1
  # shellcheck disable=SC2086
  [ "$before" = "$(sha256sum $FILES)" ] || {
    echo "RENT-0726 signed $op mutated v1 paid state or heartbeat" >&2;exit 1;
  }
done
bad="$(printf 'action=rental_v2_commit&id=vendo-01&nonce=feedbeef00112233&pulses=2&target=dev01:aabbccddeeff0011&sig=%064d\n' 0 | sh "$VENDO")"
printf '%s' "$bad" | grep -q '"ok":false' || exit 1
printf '%s' "$bad" | grep -q 'bad signature' || {
  echo 'RENT-0726 signature verification did not precede v2 denial' >&2;exit 1;
}
# shellcheck disable=SC2086
[ "$before" = "$(sha256sum $FILES)" ] || exit 1
# Reject semantic downgrades and deliberate v1 action aliases when signed
# as v2; signature binds the action and no v1 receipt/progress is reused.
for op in rental_v2_coin rental_v2_coin_commit rental_v2_coin_replay; do
  response="$(call "$op" aabbccddeeff0011 2 0123456789abcdef)"
  printf '%s' "$response" | grep -q 'rental v2 authority unavailable; no v1 fallback' || exit 1
  # shellcheck disable=SC2086
  [ "$before" = "$(sha256sum $FILES)" ] || exit 1
done
# Executable source-order defense: signature FIRST, explicit rental-v2
# denial SECOND, heartbeat handler THIRD.
sig_line="$(grep -nF 'bp_check_vendo_sig "$action"' "$VENDO" | head -n1 | cut -d: -f1)"
deny_line="$(grep -nF 'rental_v2_*) bp_fail "rental v2 authority unavailable; no v1 fallback"' "$VENDO" | head -n1 | cut -d: -f1)"
heartbeat_line="$(grep -nF 'heartbeat() {' "$VENDO" | head -n1 | cut -d: -f1)"
case "$sig_line:$deny_line:$heartbeat_line" in
  *[!0-9:]*|:*|*::*) echo 'RENT-0726 preheartbeat denial markers missing' >&2;exit 1;;
esac
[ "$sig_line" -lt "$deny_line" ] && [ "$deny_line" -lt "$heartbeat_line" ] || {
  echo 'RENT-0726 downgrade gate moved behind heartbeat or before signature' >&2;exit 1;
}
echo 'RENT-0726 PASS: signed rental-v2 protocol is denied before heartbeat, lease, receipt, or coin-window mutations'
echo 'NOT PRODUCTION: no authenticated v2 rental signer, durable journal cutover, independent witness or physical acceptance'
