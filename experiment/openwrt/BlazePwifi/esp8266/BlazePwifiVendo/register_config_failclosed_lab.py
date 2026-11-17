#!/usr/bin/env python3
"""Source-exact host regression for register-response remote-config denial.

Compiles the production connectSta() body from both ESP sketches with a
host-only Wi-Fi/HTTP shim. The shim deliberately offers positive and
signature-shaped register responses containing hostile config fields.
This is simulated control-flow evidence, not network or hardware acceptance.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def extract_connect_sta(source):
    match = re.search(r"\bvoid\s+connectSta\s*\(\s*\)\s*\{", source)
    if not match:
        raise RuntimeError("missing production connectSta()")
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise RuntimeError("unbalanced production connectSta()")


STUBS = r"""
#include <cctype>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>

struct String : std::string {
  using std::string::string;
  String(const std::string &value) : std::string(value) {}
  String(int value) : std::string(std::to_string(value)) {}
  size_t length() const { return size(); }
  bool isEmpty() const { return empty(); }
  int indexOf(const char *needle) const {
    const auto pos = find(needle);
    return pos == npos ? -1 : static_cast<int>(pos);
  }
  bool equalsIgnoreCase(const String &other) const {
    if (size() != other.size()) return false;
    for (size_t i = 0; i < size(); ++i) {
      if (std::tolower(static_cast<unsigned char>((*this)[i])) !=
          std::tolower(static_cast<unsigned char>(other[i]))) return false;
    }
    return true;
  }
};

#ifdef TARGET_ESP32
struct Config {
  String ssid = "ssid";
  String pass = "pass";
  String key = "";
  String id = "vendo-01";
} cfg;
#else
struct Config {
  char ssid[32] = "ssid";
  char pass[32] = "pass";
  char key[32] = "";
  char id[32] = "vendo-01";
} cfg;
#endif

static constexpr int WL_CONNECTED = 3;
int wifiStatus = WL_CONNECTED;
int wifiBeginCalls = 0;
int wifiFailures = 9;
int postCalls = 0;
int applyRemoteConfigCalls = 0;
uint32_t fakeNow = 0;
String lastAction;
String registerResponse = "{\"ok\":true}";
String responseSignature = "valid-signature";
String expectedSignature = "valid-signature";
String lastSentNonce = "nonce-123";
int serverTime = 123;
int jsonStringCalls = 0;
int digestCalls = 0;

bool controllerEnabled = true;
bool coinEnabled = true;
bool relayEnabled = true;
bool ledEnabled = true;
int remoteRevision = 7;
int runCoinPin = 4;
int runRelayPin = 26;
int runLedPin = 2;
bool runCoinActiveLow = true;
bool runRelayActiveHigh = true;
bool runLedActiveHigh = true;
int runDebounceMs = 70;
int maxWifiRetries = 5;

struct FakeWiFi {
  void begin(const char *, const char *) { ++wifiBeginCalls; }
  int status() const { return wifiStatus; }
} WiFi;

uint32_t millis() { return fakeNow; }
void delay(int ms) { fakeNow += static_cast<uint32_t>(ms); }
void yield() {}

String post(const char *action) {
  ++postCalls;
  lastAction = String(action);
  return registerResponse;
}
String jsonString(const String &, const char *key) {
  if (std::string(key) == "response_sig") { ++jsonStringCalls; return responseSignature; }
  return String("");
}
int jsonInt(const String &, const char *, int) { return serverTime; }
String hexDigest(const String &) { ++digestCalls; return expectedSignature; }
struct FakeSerial { template<class T> void println(const T &) {} } Serial;

void applyRemoteConfig(const String &) {
  ++applyRemoteConfigCalls;
  remoteRevision = 99;
  controllerEnabled = false;
  coinEnabled = false;
  relayEnabled = false;
  ledEnabled = false;
  runCoinPin = 12;
  runRelayPin = 13;
  runLedPin = 14;
  runCoinActiveLow = false;
  runRelayActiveHigh = false;
  runLedActiveHigh = false;
  runDebounceMs = 1;
  maxWifiRetries = 60;
}

void setKey(const char *value) {
#ifdef TARGET_ESP32
  cfg.key = value;
#else
  std::strncpy(cfg.key, value, sizeof(cfg.key) - 1);
  cfg.key[sizeof(cfg.key) - 1] = '\0';
#endif
}
void setSsid(const char *value) {
#ifdef TARGET_ESP32
  cfg.ssid = value;
#else
  std::strncpy(cfg.ssid, value, sizeof(cfg.ssid) - 1);
  cfg.ssid[sizeof(cfg.ssid) - 1] = '\0';
#endif
}
void resetState() {
  setSsid("ssid");
  setKey("");
  wifiStatus = WL_CONNECTED;
  wifiBeginCalls = 0;
  wifiFailures = 9;
  postCalls = 0;
  applyRemoteConfigCalls = 0;
  jsonStringCalls = 0;
  digestCalls = 0;
  fakeNow = 0;
  lastAction.clear();
  registerResponse = "{\"ok\":true,\"controller\":{\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"coin_pin\":12,\"relay_pin\":13,\"led_pin\":14,\"coin_active_low\":0,\"relay_active_high\":0,\"led_active_high\":0,\"coin_debounce_ms\":1,\"max_wifi_retries\":60}}";
  responseSignature = "valid-signature";
  expectedSignature = "valid-signature";
  remoteRevision = 7;
  controllerEnabled = true;
  coinEnabled = true;
  relayEnabled = true;
  ledEnabled = true;
  runCoinPin = 4;
  runRelayPin = 26;
  runLedPin = 2;
  runCoinActiveLow = true;
  runRelayActiveHigh = true;
  runLedActiveHigh = true;
  runDebounceMs = 70;
  maxWifiRetries = 5;
}
bool configUntouched() {
  return applyRemoteConfigCalls == 0 && remoteRevision == 7 &&
         controllerEnabled && coinEnabled && relayEnabled && ledEnabled &&
         runCoinPin == 4 && runRelayPin == 26 && runLedPin == 2 &&
         runCoinActiveLow && runRelayActiveHigh && runLedActiveHigh &&
         runDebounceMs == 70 && maxWifiRetries == 5;
}
"""

MAIN = r"""
int main() {
  // 1. Keyless bootstrap plus a positive register reply must not apply config.
  resetState();
  setKey("");
  responseSignature = "valid-signature";
  connectSta();
  if (postCalls != 1 || lastAction != "register" || jsonStringCalls != 0 || digestCalls != 0 || !configUntouched()) return 11;

  // 2. A valid register-tuple signature does not authenticate appended config.
  resetState();
  setKey("test-key");
  responseSignature = "valid-signature";
  expectedSignature = "valid-signature";
  connectSta();
  if (postCalls != 1 || jsonStringCalls != 1 || digestCalls != 1 || !configUntouched()) return 12;

  // 3. A bad configured-key signature cannot cause a config mutation.
  resetState();
  setKey("test-key");
  responseSignature = "bad-signature";
  expectedSignature = "valid-signature";
  connectSta();
  if (postCalls != 1 || jsonStringCalls != 1 || digestCalls != 1 || !configUntouched()) return 13;

  // 4. A missing configured-key signature cannot cause a config mutation.
  resetState();
  setKey("test-key");
  responseSignature = "";
  connectSta();
  if (postCalls != 1 || jsonStringCalls != 1 || digestCalls != 0 || !configUntouched()) return 14;

  // 5. Nested ok:true under a top-level denial is not configuration authority.
  resetState();
  setKey("");
  registerResponse = "{\"ok\":false,\"controller\":{\"ok\":true,\"coin_pin\":12}}";
  connectSta();
  if (postCalls != 1 || !configUntouched()) return 15;

  // 6. A disconnected station never issues register or mutates config.
  resetState();
  wifiStatus = 0;
  connectSta();
  if (wifiBeginCalls != 1 || postCalls != 0 || !configUntouched()) return 16;

  // 7. Empty SSID never starts Wi-Fi or issues register.
  resetState();
  setSsid("");
  connectSta();
  if (wifiBeginCalls != 0 || postCalls != 0 || !configUntouched()) return 17;

  std::cout << "REGISTER_CONFIG_FAILCLOSED_PASS 7/7 scenarios\n";
  std::cout << "REMOTE_CONFIG_APPLIED_FROM_REGISTER=0\n";
  std::cout << "PHYSICAL_REGISTER_CONFIG_VERIFIED=0\n";
  std::cout << "PRODUCTION_FINANCIAL_AUTHORIZED=0\n";
  return 0;
}
"""

failed = []
for board, path in BOARDS.items():
    source = path.read_text(encoding="utf-8")
    call_sites = len(re.findall(r"\bapplyRemoteConfig\s*\(", source))
    if call_sites != 1:
        raise RuntimeError(
            f"{board}: expected only the dormant applyRemoteConfig definition; "
            f"found {call_sites} definition/call occurrences"
        )
    connect_sta = extract_connect_sta(source)
    code = ("#define TARGET_ESP32\n" if board == "ESP32" else "") + STUBS + connect_sta + MAIN
    with tempfile.TemporaryDirectory(prefix="phx-register-config-") as folder:
        cpp = Path(folder) / "register_config.cpp"
        binary = Path(folder) / "register_config"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            print(board, "COMPILE FAIL", built.stderr[-3000:])
            failed.append(board)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        print(board, "PASS" if ran.returncode == 0 else "FAIL",
              ran.stdout.strip(), ran.stderr.strip(), "exit=", ran.returncode)
        if ran.returncode:
            failed.append(board)

if failed:
    sys.exit("register remote-config denial lab failed: " + ",".join(failed))
print("PHX-HARDWARE: register-response config mutation denied on both source-extracted boards")
