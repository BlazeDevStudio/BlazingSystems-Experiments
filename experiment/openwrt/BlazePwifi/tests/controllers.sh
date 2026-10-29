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
# Auto-registered controllers must stay fail-closed until explicit admin enable.
printf '%s' "$JSON" | grep -q '"enabled":0'
printf '%s' "$JSON" | grep -q '"coin_enabled":0'
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

# PHX-L-CORE P0 #31: fail an actual controller state-copy awk call while
# bp_controller_set holds the real fd4 admission lock. The admin writer must
# return failure AND preserve the prior complete controller registry.
# This uses disposable /tmp state; no CGI, device, customer or power-cut proof.
bp_controller_ensure vendo-02
before_controllers="$(sha256sum "$BP_CONTROLLERS" | cut -d' ' -f1)"
cat > "$T/bin/awk" <<'PHX_AWK_FAILURE'
#!/bin/sh
printf 'x' >> "$BP_STATE/awk-failure-invoked"
exit 74
PHX_AWK_FAILURE
chmod +x "$T/bin/awk"
# POSIX sh may cache /usr/bin/awk from earlier controller calls. Explicitly
# invalidate that cache and prove BOTH controller_line + write-copy hit shim.
hash -r
controller_ack=0
if bp_controller_set vendo-01 0 0 0 1 -1 5 14 1 1 1 55 450 9; then
  controller_ack=1
fi
rm -f "$T/bin/awk"
hash -r
invocations="$(wc -c < "$BP_STATE/awk-failure-invoked" 2>/dev/null || echo 0)"
if [ "$invocations" -lt 2 ]; then
  echo "PHX-L-CORE CONTROLLER_WRITE_COPY_FIXTURE_INVALID: awk failure not exercised twice" >&2
  exit 2
fi
if [ "$controller_ack" = 1 ]; then
  echo "PHX-L-CORE CONTROLLER_WRITE_COPY_RED: awk failed but admin controller_set ACKed" >&2
  exit 1
fi
after_controllers="$(sha256sum "$BP_CONTROLLERS" | cut -d' ' -f1)"
if [ "$before_controllers" != "$after_controllers" ]; then
  echo "PHX-L-CORE CONTROLLER_WRITE_COPY_RED: failed copy mutated registry" >&2
  exit 1
fi
echo "PHX-L-CORE CONTROLLER_WRITE_COPY_PASS: failed copy denied and registry preserved"

DOC="$ROOT/docs/PROTOCOL.md"
grep -q 'ESP8266' "$DOC"
grep -q 'ESP32' "$DOC"
grep -q 'Linux GPIO' "$DOC"

echo "BlazePwifi controller protocol and policy checks passed"
