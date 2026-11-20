#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
E6="$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
E32="$ROOT/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
[ -f "$E6" ] || { echo "missing ESP8266 controller" >&2; exit 1; }
[ -f "$E32" ] || { echo "missing ESP32 controller" >&2; exit 1; }

for f in "$E6" "$E32"; do
  grep -q 'cgi-bin/vendo' "$f"
  grep -q 'register' "$f"
  grep -q 'poll' "$f"
  grep -q 'coin' "$f"
  grep -q 'target' "$f"
  grep -q 'sig' "$f"
  grep -q 'pending' "$f"
  grep -q 'verifyWifi' "$f"
  grep -q 'maxWifiRetries' "$f"
  grep -q 'wifiFailures' "$f"
  grep -q 'applyRemoteConfig' "$f"
  grep -q 'config_revision' "$f"
  grep -q 'Wi-Fi verification failed' "$f"
done

grep -q 'Preferences' "$E32"
grep -q 'LittleFS' "$E32"
grep -q 'coinDebounceMs' "$E32"
grep -q 'pulseGroupMs' "$E32"
grep -q 'LittleFS' "$E6"

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/bin" "$T/state" "$T/run"
cat > "$T/bin/uci" <<'UCI'
#!/bin/sh
case "$*" in
 *'get blazepwifi.main.durable_sync') echo 0;;
 *) exit 1;;
esac
UCI
chmod +x "$T/bin/uci"
export PATH="$T/bin:$PATH" BP_STATE="$T/state" BP_RUN="$T/run"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/common.sh"
BP_VENDOS="$T/run/vendos.tsv"; : > "$BP_VENDOS"
. "$ROOT/openwrt/rootfs/usr/lib/blazepwifi/controller.sh"
bp_controller_ensure vendo-01
JSON="$(bp_controller_json vendo-01)"
printf '%s' "$JSON" | grep -q '"enabled":1'
printf '%s' "$JSON" | grep -q '"max_wifi_retries":6'
bp_controller_set vendo-01 1 1 0 1 -1 5 14 1 1 1 55 450 9
JSON="$(bp_controller_json vendo-01)"
printf '%s' "$JSON" | grep -q '"relay_enabled":0'
printf '%s' "$JSON" | grep -q '"relay_pin":5'
printf '%s' "$JSON" | grep -q '"coin_debounce_ms":55'
printf '%s' "$JSON" | grep -q '"max_wifi_retries":9'
if bp_controller_set vendo-01 1 1 1 1 99 5 14 1 1 1 55 450 9; then
  echo "invalid controller pin unexpectedly accepted" >&2; exit 1
fi

DOC="$ROOT/docs/PROTOCOL.md"
grep -q 'ESP8266' "$DOC"
grep -q 'ESP32' "$DOC"
grep -q 'Linux GPIO' "$DOC"

echo "BlazePwifi controller protocol and policy checks passed"
