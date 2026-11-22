#!/usr/bin/env python3
"""Source-exact monotonic revision guard tests for both ESP controller sketches.

The remote-config consumer is intentionally dormant. These host tests only
verify that the dormant mutation helper cannot roll configuration state back
when given a stale, duplicate, or zero initial revision.
"""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_lab_source import extract_function

ROOT = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": Path(__file__).with_name("BlazePwifiVendo.ino"),
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}
FUNCTIONS = ("jsonInt", "applyRemoteConfig")


def _program(sketch: Path, board: str, mutate_guard: bool = False):
    source = sketch.read_text(encoding="utf-8")
    extracted = {name: extract_function(source, name) for name in FUNCTIONS}
    guard = re.search(
        r"if\s*\(\s*rev\s*<=\s*remoteRevision\s*\)\s*return\s*;",
        extracted["applyRemoteConfig"],
    )
    if not guard:
        if mutate_guard:
            raise AssertionError(f"{board}: monotonic revision guard is absent")
    elif mutate_guard:
        function = extracted["applyRemoteConfig"]
        extracted["applyRemoteConfig"] = (
            function[:guard.start()] + "if(false) return;" + function[guard.end():]
        )

    stubs = r"""
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

struct String : std::string {
  using std::string::string;
  using std::string::operator=;
  String()=default;
  String(const std::string &value):std::string(value){}
  size_t length() const { return size(); }
  int indexOf(const String &needle) const {
    const auto position = find(needle);
    return position == npos ? -1 : static_cast<int>(position);
  }
  String substring(int start, int end) const {
    if(start < 0 || end < start || static_cast<size_t>(start) > size()) return String();
    return String(std::string::substr(static_cast<size_t>(start), static_cast<size_t>(end-start)));
  }
  long toInt() const {
    char *end = nullptr;
    const long value = std::strtol(c_str(), &end, 10);
    return end == c_str() ? 0 : value;
  }
  friend String operator+(const char *left, const String &right) {
    return String(std::string(left) + static_cast<const std::string&>(right));
  }
  friend String operator+(const String &left, const char *right) {
    return String(static_cast<const std::string&>(left) + right);
  }
};

static bool controllerEnabled, coinEnabled, relayEnabled, ledEnabled;
static bool runCoinActiveLow, pinConfigSafe;
static int runCoinPin, runRelayPin, runLedPin, remoteRevision, maxWifiRetries;
static uint16_t runDebounceMs, runPulseGroupMs;
static int configureCalls, applyOutputsCalls;
struct Config { int coinDebounceMs=40; int pulseGroupMs=400; } cfg;
void configureRuntimePins(int coinPin,int relayPin,int ledPin) {
  ++configureCalls;
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
}
void applyOutputs() { ++applyOutputsCalls; }
bool runtimePinsSafe(int,int,int) { return true; }
int boundedCoinDebounceMs(int value) { return value<20?20:(value>2000?2000:value); }
int constrain(int value,int low,int high) {
  return value<low?low:(value>high?high:value);
}
int isDigit(char value) { return value>='0' && value<='9'; }
struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;
"""
    main = r"""
static void resetState() {
  controllerEnabled=false; coinEnabled=false; relayEnabled=false; ledEnabled=false;
  runCoinActiveLow=false; pinConfigSafe=true;
  runCoinPin=3; runRelayPin=12; runLedPin=13;
  remoteRevision=5; maxWifiRetries=9;
  runDebounceMs=80; runPulseGroupMs=900;
  configureCalls=0; applyOutputsCalls=0;
}

static bool statePreserved() {
  return !controllerEnabled && !coinEnabled && !relayEnabled && !ledEnabled &&
         !runCoinActiveLow && pinConfigSafe &&
         runCoinPin==3 && runRelayPin==12 && runLedPin==13 &&
         remoteRevision==5 && maxWifiRetries==9 &&
         runDebounceMs==80 && runPulseGroupMs==900;
}

int main() {
  const String stale="{\"config_revision\":4,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":2,\"relay_pin\":14,"
      "\"led_pin\":15,\"coin_active_low\":1,\"coin_debounce_ms\":100,"
      "\"pulse_group_ms\":1200,\"max_wifi_retries\":20}";
  resetState();
  applyRemoteConfig(stale);
  if(!statePreserved() || configureCalls!=0 || applyOutputsCalls!=0) return 10;
  std::cout<<"REMOTE_CONFIG_STALE_REVISION_DENY_PASS\n";

  const String equal="{\"config_revision\":5,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":2,\"relay_pin\":14,"
      "\"led_pin\":15,\"coin_active_low\":1}";
  resetState();
  applyRemoteConfig(equal);
  if(!statePreserved() || configureCalls!=0 || applyOutputsCalls!=0) return 11;
  std::cout<<"REMOTE_CONFIG_EQUAL_REVISION_DENY_PASS\n";

  resetState();
  remoteRevision=0;
  applyRemoteConfig(String("{\"config_revision\":0,\"enabled\":1,\"coin_pin\":2,"
      "\"relay_pin\":14,\"led_pin\":15}"));
  if(remoteRevision!=0 || controllerEnabled || runCoinPin!=3 ||
     configureCalls!=0 || applyOutputsCalls!=0) return 12;
  std::cout<<"REMOTE_CONFIG_ZERO_INITIAL_REVISION_DENY_PASS\n";

  resetState();
  applyRemoteConfig(String("{\"config_revision\":6,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":2,\"relay_pin\":14,"
      "\"led_pin\":15,\"coin_active_low\":1,\"coin_debounce_ms\":100,"
      "\"pulse_group_ms\":1200,\"max_wifi_retries\":20}"));
  if(remoteRevision!=6 || !controllerEnabled || !coinEnabled || !relayEnabled ||
     !ledEnabled || !runCoinActiveLow || runCoinPin!=2 || runRelayPin!=14 ||
     runLedPin!=15 || runDebounceMs!=100 || runPulseGroupMs!=1200 ||
     maxWifiRetries!=20 || configureCalls!=1 || applyOutputsCalls!=1) return 13;
  std::cout<<"REMOTE_CONFIG_NEWER_REVISION_ACCEPT_PASS\n";
  return 0;
}
"""
    return stubs + "\n" + extracted["jsonInt"] + "\n" + extracted["applyRemoteConfig"] + "\n" + main


def _compile_and_run(code: str, board: str, expected: int, label: str):
    with tempfile.TemporaryDirectory(prefix="phx-remote-config-revision-") as folder:
        cpp = Path(folder) / "remote_config_revision.cpp"
        binary = Path(folder) / "remote_config_revision"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board} {label}: compile failed:\n{built.stderr[-3000:]}")
        ran = subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10
        )
        if ran.returncode != expected:
            raise RuntimeError(
                f"{board} {label}: expected exit {expected}, got {ran.returncode}\n"
                f"stdout={ran.stdout}\nstderr={ran.stderr}"
            )
        return ran.stdout.strip()


def run_remote_config_revision_lab():
    failures = []
    for board, sketch in SKETCHES.items():
        if not sketch.is_file():
            raise RuntimeError(f"{board}: missing sketch {sketch}")
        try:
            output = _compile_and_run(_program(sketch, board), board, 0, "exact-source")
            print(f"{board} REMOTE_CONFIG_REVISION_GUARD_PASS 4/4")
            print(output)
            mutated = _compile_and_run(
                _program(sketch, board, mutate_guard=True), board, 10,
                "removed-monotonic-revision-guard",
            )
            print(f"{board} MUTATION_REJECTED removed-monotonic-revision-guard")
        except Exception as error:
            failures.append(str(error))
    if failures:
        raise RuntimeError("remote-config revision guard failures:\n" + "\n".join(failures))
    print("REMOTE_CONFIG_REVISION_GUARD_SIMULATED_ONLY=1")
    print("REMOTE_CONFIG_AUTHORIZATION_ENABLED=0")
    print("PHYSICAL_HARDWARE_ACCEPTANCE=0")


if __name__ == "__main__":
    run_remote_config_revision_lab()
