#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in *durable_sync*) echo 0;; *) exit 1;; esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
export BP_RENTAL_POLICY_V2="$T/state/rental-policy-v2.tsv"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/auth.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental.sh"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/rental_policy.sh"
bp_rental_init; bp_rental_policy_v2_init
D=0123456789abcdef01234567
bp_rental_policy_write "$D" 'com.example.one' abc def 4096 vendo1
bp_rental_policy_migrate "$D"
L="$(bp_rental_policy_v2_get "$D")"
[ "$(printf '%s' "$L" | cut -f2)" = 1 ]
[ "$(printf '%s' "$L" | cut -f6)" = com.example.one ]
[ "$(printf '%s' "$L" | cut -f8)" = vendo1 ]
[ "$(printf '%s' "$L" | cut -f15)" = abc ]
R="$(bp_rental_policy_v2_patch "$D" 1 test unrestricted 'com.example.one,com.example.two' '' @keep 0 1 @keep 5000 @keep always)"
[ "$R" = 2 ]
L2="$(bp_rental_policy_v2_get "$D")"
[ "$(printf '%s' "$L2" | cut -f5)" = unrestricted ]
[ "$(printf '%s' "$L2" | cut -f7)" = - ]
[ "$(printf '%s' "$L2" | cut -f9)" = always ]
[ "$(printf '%s' "$L2" | cut -f14)" = 5000 ]
R3="$(bp_rental_policy_v2_patch "$D" 2 clear rental - @keep @keep 1 1 - @keep @keep off)"
[ "$R3" = 3 ]
L3="$(bp_rental_policy_v2_get "$D")"
[ "$(printf '%s' "$L3" | cut -f6)" = - ]
[ "$(printf '%s' "$L3" | cut -f9)" = off ]
[ "$(printf '%s' "$L3" | cut -f11)" = - ]
J3="$(bp_rental_policy_v2_json "$D")"
printf '%s' "$J3" | grep -q '"allowed_packages":""'
printf '%s' "$J3" | grep -q '"quick_controls":""'
if bp_rental_policy_v2_patch "$D" 2 stale rental @keep @keep @keep @keep @keep @keep @keep @keep >/dev/null; then
  echo "stale CAS unexpectedly succeeded" >&2; exit 1
else
  [ "$?" -eq 4 ]
fi
echo "v0.4 rental policy tests passed"
