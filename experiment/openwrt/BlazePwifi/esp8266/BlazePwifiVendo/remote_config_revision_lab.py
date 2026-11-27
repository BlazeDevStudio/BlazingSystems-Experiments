#!/usr/bin/env python3
"""Source-exact monotonic revision and output-polarity state tests for both ESP sketches.

The remote-config consumer remains intentionally dormant. These host tests
exercise the actual JSON parser, GPIO validation and pin-configuration helpers;
they do not authenticate or activate remote configuration.
"""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_lab_source import extract_function, mask_active_cpp_code, mask_non_code

ROOT = Path(__file__).resolve().parents[2]
SKETCHES = {
    "ESP8266": Path(__file__).with_name("BlazePwifiVendo.ino"),
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}
FUNCTIONS = (
    "jsonInt",
    "writeLogical",
    "validInputPullupPin",
    "validOutputPin",
    "runtimePinsSafe",
    "configureRuntimePins",
    "applyRemoteConfig",
)


def _remote_config_dormancy_violation(source: str) -> bool:
    """Return true if an active callsite can apply unverified register/poll config."""
    active = mask_active_cpp_code(source)
    code = mask_non_code(active)
    definitions = re.findall(r"\bvoid\s+applyRemoteConfig\s*\(", code)
    references = re.findall(r"\bapplyRemoteConfig\s*\(", code)
    return len(definitions) != 1 or len(references) != 1


def _assert_remote_config_consumer_dormant(source: str, board: str) -> None:
    if _remote_config_dormancy_violation(source):
        raise AssertionError(
            f"{board}: applyRemoteConfig must remain definition-only until "
            "the authenticated configuration envelope is approved"
        )

    # Failure-inject forbidden callsites into both network entry points. The
    # active-code scanner must reject them while ignoring comments/literals
    # and inactive preprocessor branches.
    for function_name in ("connectSta", "loop"):
        match = re.search(
            rf"\bvoid\s+{function_name}\s*\([^)]*\)\s*\{{",
            source,
        )
        if not match:
            raise AssertionError(f"{board}: missing {function_name} injection anchor")
        injected = (
            source[:match.end()]
            + '\n  applyRemoteConfig(String("{}"));'
            + source[match.end():]
        )
        if not _remote_config_dormancy_violation(injected):
            raise AssertionError(
                f"{board}: dormant-consumer guard accepted injected {function_name} callsite"
            )

    print(f"{board} REMOTE_CONFIG_CONSUMER_DORMANT_PASS")
    print(f"{board} REMOTE_CONFIG_CALLSITE_MUTATIONS_REJECTED 2/2")


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

static constexpr int HIGH=1, LOW=0, INPUT=0, INPUT_PULLUP=2, OUTPUT=1;
static constexpr int FALLING=4, RISING=5;
static bool controllerEnabled, coinEnabled, relayEnabled, ledEnabled;
static bool runCoinActiveLow, pinConfigSafe, outputPolarityKnown;
// configureRuntimePins owns these runtime states on both boards.
static bool pollIntakeSuspended, coinInterruptAttached;
static bool runRelayActiveHigh, runLedActiveHigh, insertMode;
static int runCoinPin, runRelayPin, runLedPin, remoteRevision, maxWifiRetries;
static uint16_t runDebounceMs, runPulseGroupMs;
// One initial inhibit + one selected configureRuntimePins branch exit + the
// final applyRemoteConfig refresh. The two branch-exit callsites are exclusive.
static constexpr int EXPECTED_APPLY_OUTPUT_CALLS=3;
static int applyOutputsCalls, quarantineCalls, outputModeCalls, pinModeCalls;
static int digitalWriteCalls;
static int pinModes[64], pinLevels[64];
static String activeTarget;
struct Config { int coinDebounceMs=40; int pulseGroupMs=400; } cfg;

void pinMode(int pin,int mode) {
  ++pinModeCalls;
  if(pin>=0 && pin<64) pinModes[pin]=mode;
  if(mode==OUTPUT) ++outputModeCalls;
}
void digitalWrite(int pin,int level) {
  ++digitalWriteCalls;
  if(pin>=0 && pin<64) pinLevels[pin]=level;
}
int digitalPinToInterrupt(int pin) { return pin; }
void detachInterrupt(int) {}
void attachInterrupt(int,void(*)(),int) {}
void coinEdgeISR() {}
bool quarantineCoinIngressTransition() { ++quarantineCalls; return true; }
void applyOutputs() { ++applyOutputsCalls; }
int boundedCoinDebounceMs(int value) {
  return value<20?20:(value>2000?2000:value);
}
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
  for(int i=0;i<64;++i) { pinModes[i]=INPUT; pinLevels[i]=LOW; }
  controllerEnabled=false; coinEnabled=false; relayEnabled=false; ledEnabled=false;
  runCoinActiveLow=false; pinConfigSafe=true; outputPolarityKnown=true;
  pollIntakeSuspended=false; coinInterruptAttached=false;
  runRelayActiveHigh=false; runLedActiveHigh=false; insertMode=false; activeTarget="";
  runCoinPin=3; runRelayPin=12; runLedPin=13;
  remoteRevision=5; maxWifiRetries=9;
  runDebounceMs=80; runPulseGroupMs=900;
  applyOutputsCalls=0; quarantineCalls=0; outputModeCalls=0;
  pinModeCalls=0; digitalWriteCalls=0;
}

static bool statePreserved() {
  return !controllerEnabled && !coinEnabled && !relayEnabled && !ledEnabled &&
         !runCoinActiveLow && pinConfigSafe && outputPolarityKnown &&
         runCoinPin==3 && runRelayPin==12 && runLedPin==13 &&
         remoteRevision==5 && maxWifiRetries==9 &&
         runDebounceMs==80 && runPulseGroupMs==900;
}

int main() {
  // Common safe tuple: GPIO4/13/14 avoids ESP8266 and ESP32 boot-strap pins.
  const String stale="{\"config_revision\":4,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":13,"
      "\"led_pin\":14,\"coin_active_low\":1,\"coin_debounce_ms\":100,"
      "\"pulse_group_ms\":1200,\"max_wifi_retries\":20}";
  resetState();
  applyRemoteConfig(stale);
  if(!statePreserved() || quarantineCalls!=0 || applyOutputsCalls!=0 ||
     pinModeCalls!=0 || outputModeCalls!=0) return 10;
  std::cout<<"REMOTE_CONFIG_STALE_REVISION_DENY_PASS\n";

  const String equal="{\"config_revision\":5,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":13,"
      "\"led_pin\":14,\"coin_active_low\":1}";
  resetState();
  applyRemoteConfig(equal);
  if(!statePreserved() || quarantineCalls!=0 || applyOutputsCalls!=0 ||
     pinModeCalls!=0 || outputModeCalls!=0) return 11;
  std::cout<<"REMOTE_CONFIG_EQUAL_REVISION_DENY_PASS\n";

  resetState();
  remoteRevision=0;
  applyRemoteConfig(String("{\"config_revision\":0,\"enabled\":1,\"coin_pin\":4,"
      "\"relay_pin\":13,\"led_pin\":14}"));
  if(remoteRevision!=0 || controllerEnabled || runCoinPin!=3 ||
     quarantineCalls!=0 || applyOutputsCalls!=0 || pinModeCalls!=0) return 12;
  std::cout<<"REMOTE_CONFIG_ZERO_INITIAL_REVISION_DENY_PASS\n";

  resetState();
  applyRemoteConfig(String("{\"config_revision\":6,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":13,"
      "\"led_pin\":14,\"coin_active_low\":1,\"coin_debounce_ms\":100,"
      "\"pulse_group_ms\":1200,\"max_wifi_retries\":20}"));
  if(remoteRevision!=6 || !controllerEnabled || !coinEnabled || !relayEnabled ||
     !ledEnabled || !runCoinActiveLow || runCoinPin!=4 || runRelayPin!=13 ||
     runLedPin!=14 || runDebounceMs!=100 || runPulseGroupMs!=1200 ||
     maxWifiRetries!=20 || quarantineCalls!=1 || applyOutputsCalls!=EXPECTED_APPLY_OUTPUT_CALLS ||
     outputModeCalls!=2 || pinModes[13]!=OUTPUT || pinModes[14]!=OUTPUT) return 13;
  std::cout<<"REMOTE_CONFIG_NEWER_REVISION_ACCEPT_PASS\n";

  resetState();
  outputPolarityKnown=false;
  pinConfigSafe=false;
  applyRemoteConfig(String("{\"config_revision\":6,\"enabled\":1,\"coin_enabled\":1,"
      "\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":13,"
      "\"led_pin\":14,\"coin_active_low\":1}"));
  if(remoteRevision!=6 || pinConfigSafe || pinModes[4]!=INPUT_PULLUP ||
     pinModes[13]!=INPUT || pinModes[14]!=INPUT || outputModeCalls!=0 ||
     insertMode || activeTarget.length()!=0 || quarantineCalls!=1 ||
     applyOutputsCalls!=EXPECTED_APPLY_OUTPUT_CALLS) return 14;
  std::cout<<"REMOTE_CONFIG_UNKNOWN_POLARITY_DENY_PASS\n";
  return 0;
}
"""
    return stubs + "\n" + "\n".join(extracted[name] for name in FUNCTIONS) + "\n" + main


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
        _assert_remote_config_consumer_dormant(
            sketch.read_text(encoding="utf-8"), board
        )
        try:
            output = _compile_and_run(_program(sketch, board), board, 0, "exact-source")
            print(f"{board} REMOTE_CONFIG_REVISION_GUARD_PASS 5/5")
            print(output)
            _compile_and_run(
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
