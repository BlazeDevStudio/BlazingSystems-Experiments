#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
COMMON="$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
VENDO="$ROOT/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo"
E6="$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
E32="$ROOT/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
LINUX="$ROOT/linux-agent/blazepwifi-gpio-agent.sh"

for f in "$COMMON" "$VENDO" "$E6" "$E32" "$LINUX"; do
  [ -f "$f" ] || { echo "missing controller component: $f" >&2; exit 1; }
done

# v0.4 must preserve the v0.3 controller action surface and target-bound coin semantics.
for action in register poll coin; do
  grep -q "$action" "$VENDO"
  grep -Fq "post(\"$action\"" "$E6" || [ "$action" = coin ]
  grep -Fq "post(\"$action\"" "$E32" || [ "$action" = coin ]
done
grep -q 'target_nonce' "$VENDO"
grep -q 'coin target mismatch' "$VENDO"
grep -q 'another vendo selected' "$VENDO"
grep -q 'kind" = rental' "$VENDO"
grep -q 'bp_rental_apply_coin' "$VENDO"

# All three controller implementations must use the same canonical signature:
# key|action|id|nonce|pulses|target|key
grep -Fq 'String base=String(cfg.key)+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;' "$E6"
grep -Fq 'String base=cfg.key+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;' "$E32"
grep -Fq "printf '%s|%s|%s|%s|%s|%s|%s' \"\$key\" \"\$action\" \"\$id\" \"\$nonce\" \"\$pulses\" \"\$target\" \"\$key\" | sha256" "$LINUX"
grep -Fq "printf '%s|%s|%s|%s|%s|%s|%s' \"\$secret\" \"\$action\" \"\$id\" \"\$nonce\" \"\$pulses\" \"\$target\" \"\$secret\" | bp_sha256" "$COMMON"

# Execute the server signer with a deterministic key and compare with sha256sum.
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
  *'get blazepwifi.main.vendo_key') echo compatibility-secret;;
  *'get blazepwifi.main.durable_sync') echo 0;;
  *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
. "$COMMON"
ACTION=coin
ID=vendo-01
NONCE=0011223344556677
PULSES=3
TARGET=aabbccddeeff0011
CANON="compatibility-secret|$ACTION|$ID|$NONCE|$PULSES|$TARGET|compatibility-secret"
EXPECTED="$(printf '%s' "$CANON" | sha256sum | awk '{print $1}')"
ACTUAL="$(bp_vendo_sig_expected "$ACTION" "$ID" "$NONCE" "$PULSES" "$TARGET")"
[ "$ACTUAL" = "$EXPECTED" ] || {
  echo "controller signature drift: expected $EXPECTED got $ACTUAL" >&2
  exit 1
}

# Linux agent self-test exercises the same signer without GPIO hardware.
SELF="$(BP_GPIO_SELFTEST=1 sh "$LINUX")"
printf '%s' "$SELF" | grep -q 'selftest:ok'
printf '%s' "$SELF" | grep -q 'signature:64'

# Runtime configuration fields remain server-managed and revisioned.
for field in config_revision coin_debounce_ms pulse_group_ms max_wifi_retries; do
  grep -q "$field" "$E6"
  grep -q "$field" "$E32"
done

echo "BlazePwifi v0.4 controller compatibility passed"
