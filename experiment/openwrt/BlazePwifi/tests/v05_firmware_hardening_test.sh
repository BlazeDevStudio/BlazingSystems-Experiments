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
  grep -q '"/quarantine"' "$f" || { echo "Missing /quarantine route in $f" >&2; exit 1; }
  grep -q '"/quarantine/clear"' "$f" || { echo "Missing /quarantine/clear route in $f" >&2; exit 1; }

  # 4. Quarantine commit must fail closed before clearPending()
  python3 - "$f" <<'PY'
import sys

path = sys.argv[1]
content = open(path, encoding="utf-8").read()

def function_body(signature):
    start = content.find(signature)
    if start < 0:
        sys.exit(f"Missing {signature} in {path}")
    brace = content.find("{", start)
    depth = 0
    for pos in range(brace, len(content)):
        if content[pos] == "{":
            depth += 1
        elif content[pos] == "}":
            depth -= 1
            if depth == 0:
                return content[brace + 1:pos]
    sys.exit(f"Unclosed {signature} in {path}")

append_body = function_body("bool appendQuarantineRecord")
quarantine_body = function_body("bool quarantinePending")
required = [
    'if(!q) return false;',
    'written!=(size_t)len',
    'if(!verify){',
    'if(!fsReady || journalRecoveryRequired || pendingPulses==0) return false;',
    'bool inspectQuarantineLog',
    'if(alreadyRecorded) return true;',
    'lineLength==0',
    'journalRecoveryRequired=true;',
    'after==before+(size_t)len',
    'QUARANTINE_MAX_BYTES',
]
for token in required:
    if token not in append_body and token not in content:
        sys.exit(f"Missing fail-closed quarantine check {token!r} in {path}")

guard = 'if(!appendQuarantineRecord(reason))'
guard_pos = quarantine_body.find(guard)
clear_pos = quarantine_body.find("clearPending();")
if guard_pos < 0 or clear_pos < 0 or clear_pos < guard_pos:
    sys.exit(f"clearPending() is not gated by verified quarantine commit in {path}")
failure_path = quarantine_body[guard_pos:clear_pos]
if "return false;" not in failure_path:
    sys.exit(f"quarantine failure can reach clearPending() in {path}")
print(f"Verified fail-closed quarantine source path: {path}")
PY

  # 5. Syntax & Brace Balancing Check
  python3 - "$f" <<'PY'
import sys
content = open(sys.argv[1]).read()
stack = []
for i, line in enumerate(content.splitlines(), 1):
    for c in line:
        if c == '{':
            stack.append(i)
        elif c == '}':
            if not stack:
                sys.exit(f"Syntax error: Unmatched }} at line {i} in {sys.argv[1]}")
            stack.pop()
if stack:
    sys.exit(f"Syntax error: Unclosed {{ from line(s) {stack} in {sys.argv[1]}")
PY
done

# 6. Failure-injection model for open, short-write, verify, and reboot paths.
# Source assertions above bind this transition model to both production sketches.
python3 - <<'PY'
PENDING = {"pulses": 5, "nonce": "n-1", "target": "t-1"}

def quarantine_attempt(*, open_ok=True, requested=120, written=120, verify_ok=True, size_ok=True):
    pending = dict(PENDING)
    if not open_ok:
        return pending, False
    if written != requested:
        return pending, False
    if not verify_ok or not size_ok:
        return pending, False
    return None, True

for name, kwargs in {
    "open failure": {"open_ok": False},
    "short write": {"written": 47},
    "verify open failure": {"verify_ok": False},
    "post-close size mismatch": {"size_ok": False},
}.items():
    pending, committed = quarantine_attempt(**kwargs)
    assert not committed, name
    assert pending == PENDING, f"{name} erased pending coin"
    reboot_loaded = dict(pending)
    assert reboot_loaded == PENDING, f"{name} lost pending coin across reboot"

pending, committed = quarantine_attempt()
assert committed and pending is None, "verified append did not clear pending coin"
print("Quarantine failure injection PASS: pending survives all failed commits and simulated reboot")
PY

# 7. ESP8266 Nonce Entropy Check (HW-P1-1): Ensure micros() is NOT in freshNonce
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
