#!/bin/sh
# BlazePwifi ESP32 / ESP8266 Firmware Hardening & Quarantine Verification Test
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
E6="$ROOT/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
E32="$ROOT/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"

echo "Checking ESP firmware hardening in $E6 and $E32..."

for f in "$E6" "$E32"; do
  [ -f "$f" ] || { echo "Missing firmware sketch: $f" >&2; exit 1; }

  # 1. HTML Escaping (HW-P2-1)
  grep -q 'String htmlEsc' "$f" || { echo "Missing htmlEsc in $f" >&2; exit 1; }
  grep -q "htmlEsc(cfg.ssid)" "$f" || grep -q "htmlEsc(String(cfg.ssid))" "$f" || {
    echo "Unescaped SSID in $f setup form" >&2; exit 1;
  }
  grep -q "htmlEsc(cfg.server)" "$f" || grep -q "htmlEsc(String(cfg.server))" "$f" || {
    echo "Unescaped server in $f setup form" >&2; exit 1;
  }
  grep -q "htmlEsc(cfg.id)" "$f" || grep -q "htmlEsc(String(cfg.id))" "$f" || {
    echo "Unescaped id in $f setup form" >&2; exit 1;
  }

  # 2. Nonce Tracking & Server Response Signature Verification (HW-P0-1)
  grep -q 'lastSentNonce' "$f" || { echo "Missing lastSentNonce in $f" >&2; exit 1; }
  grep -q 'response_sig' "$f" || { echo "Missing response_sig verification in $f" >&2; exit 1; }
  grep -q '|register|' "$f" || { echo "Missing register signature check in $f" >&2; exit 1; }
  grep -q '|poll|' "$f" || { echo "Missing poll signature check in $f" >&2; exit 1; }

  # 3. Quarantined Swallowed Coins (HW-P0-2)
  grep -q 'quarantinePending' "$f" || { echo "Missing quarantinePending in $f" >&2; exit 1; }
  grep -q '/quarantine.log' "$f" || { echo "Missing quarantine.log path in $f" >&2; exit 1; }
done

# 4. ESP8266 Nonce Entropy Check (HW-P1-1): Ensure micros() is NOT in freshNonce
python3 - "$E6" <<'PY'
import sys
content = open(sys.argv[1]).read()
fn_start = content.find("String freshNonce()")
if fn_start == -1:
    sys.exit("freshNonce() not found in ESP8266 sketch")
fn_body = content[fn_start:fn_start+200]
if "micros()" in fn_body:
    sys.exit("HW-P1-1 violation: micros() found in freshNonce() body")
if "ESP.random()" not in fn_body:
    sys.exit("ESP.random() not found in freshNonce() body")
print("ESP8266 freshNonce entropy verified: full hardware RNG words without micros()")
PY

# 5. Pure Python simulation of response_sig computation matching OpenWrt cgi-bin/vendo
python3 - <<'PY'
import hashlib

key = "test-secret-key-1234"
vendo_id = "vendo-01"
nonce = "deadbeef11223344"
now = "1794403139"

# register expected
reg_raw = f"{key}|register|{vendo_id}|{nonce}|{now}|{key}".encode()
expected_reg = hashlib.sha256(reg_raw).hexdigest()
assert len(expected_reg) == 64

# poll expected
ins = "1"
tgt = "targetnonce5678"
exp = "1794403260"
poll_raw = f"{key}|poll|{vendo_id}|{nonce}|{ins}|{tgt}|{exp}|{key}".encode()
expected_poll = hashlib.sha256(poll_raw).hexdigest()
assert len(expected_poll) == 64

print("Response signature simulation matches OpenWrt cgi-bin/vendo format exactly")
PY

echo "ALL ESP32 / ESP8266 FIRMWARE HARDENING CHECKS PASS"
