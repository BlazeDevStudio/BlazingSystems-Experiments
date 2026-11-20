#!/usr/bin/env python3
"""Source-exact ESP32 cold-boot output-polarity gate regression.

Host-only: verifies local persisted polarity authority, unknown-profile INPUT
hold, output OFF preload, and fail-closed poll/coin gates. It is not electrical
or physical relay acceptance.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "BlazePwifiVendo32.ino"


def extract_function(source: str, name: str) -> str:
    pattern = re.compile(
        r"\b(?:void|bool|uint32_t|int|size_t|String)\s+"
        + re.escape(name) + r"\s*\([^;{}]*\)\s*\{"
    )
    matches = list(pattern.finditer(source))
    if len(matches) != 1:
        raise AssertionError(
            "expected exactly one production function " + name +
            ", found " + str(len(matches))
        )
    match = matches[0]
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    pos = source.find("{", match.start())
    i = pos
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        elif ch == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():i + 1]
        i += 1
    raise AssertionError("unterminated production function " + name)


def extract_struct(source: str, name: str) -> str:
    pattern = re.compile(r"\bstruct\s+" + re.escape(name) + r"\s*\{")
    match = pattern.search(source)
    if not match:
        raise AssertionError("missing production struct " + name)
    pos = source.find("{", match.start())
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    i = pos
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 1
        elif quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        elif ch == "/" and nxt == "/":
            line_comment = True
            i += 1
        elif ch == "/" and nxt == "*":
            block_comment = True
            i += 1
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = source.find(";", i)
                if end < 0:
                    raise AssertionError("unterminated production struct " + name)
                return source[match.start():end + 1]
        i += 1
    raise AssertionError("unterminated production struct " + name)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    # These assertions intentionally fail on the pre-gate ESP32 source.
    for token, message in (
        ("bool outputPolarityKnown=false", "ESP32 boot polarity authority is missing"),
        ("bool loadLocalOutputPolarity()", "local persisted polarity loader is missing"),
        ("bool persistLocalOutputPolarity()", "verified local polarity persistence is missing"),
        ('prefs.getUChar("polarityv"', "versioned local polarity marker is missing"),
        ('prefs.putUChar("polarityv",0)', "polarity marker is not invalidated before writes"),
        ('prefs.putUChar("polarityv",1)', "polarity marker is not committed last"),
    ):
        require(token in source, message)

    load_config = extract_function(source, "loadConfig")
    save_config = extract_function(source, "saveConfig")
    load_local = extract_function(source, "loadLocalOutputPolarity")
    persist_local = extract_function(source, "persistLocalOutputPolarity")
    configure = extract_function(source, "configureRuntimePins")
    apply_outputs = extract_function(source, "applyOutputs")
    can_poll = extract_function(source, "canStartPoll")
    can_post = extract_function(source, "canAttemptCoinPost")
    setup = extract_function(source, "setup")
    portal = extract_function(source, "setupPortal")
    remote = extract_function(source, "applyRemoteConfig")

    require("loadLocalOutputPolarity()" in load_config,
            "loadConfig must load local polarity before setup configures GPIO")
    require('prefs.getBool("relayhi",true)' not in load_config and
            'prefs.getBool("ledhi",true)' not in load_config,
            "missing Preferences keys must not default to active-high")
    require("persistLocalOutputPolarity()" in save_config and
            'if(prefs.putUChar("polarityv",0)!=1) return false;' in save_config and
            "return persistLocalOutputPolarity();" in save_config,
            "saveConfig must invalidate first and propagate polarity persistence/readback failure")
    require("if(!outputPolarityKnown)" in configure and
            "pinMode(runRelayPin,INPUT)" in configure and
            "pinMode(runLedPin,INPUT)" in configure,
            "unknown local polarity must leave relay and LED as INPUT")
    require("quarantineCoinIngressTransition();" in configure,
            "pin attachment must quarantine active or unobserved coin ingress")
    require("if(!outputPolarityKnown) return;" in apply_outputs,
            "applyOutputs must not drive unknown-polarity outputs")
    require("outputPolarityKnown" in can_poll and
            "outputPolarityKnown" in can_post,
            "poll and coin POST admission must remain denied until polarity is known")
    require(setup.find("loadConfig()") < setup.find("configureRuntimePins("),
            "loadConfig must precede the first runtime GPIO configuration")
    require("requireSetupApRequest()" in portal and
            'web.arg("rh")' in portal and 'web.arg("lh")' in portal,
            "polarity selection must be restricted to the local setup AP")
    require('relayPolarity!="0"' in portal and 'relayPolarity!="1"' in portal and
            'ledPolarity!="0"' in portal and 'ledPolarity!="1"' in portal,
            "local relay and LED polarity values must be strictly 0 or 1")
    require("if(!saveConfig())" in portal and "web.send(500" in portal,
            "setup must refuse success/reboot when local polarity persistence fails")
    require("relay_active_high" not in remote and
            "led_active_high" not in remote and
            "nextRelayActiveHigh" not in remote and
            "nextLedActiveHigh" not in remote,
            "remote configuration must not become a polarity authority")

    config = extract_struct(source, "Config")
    functions = "\n".join(
        extract_function(source, name)
        for name in (
            "loadLocalOutputPolarity",
            "persistLocalOutputPolarity",
            "writeLogical",
            "configureRuntimePins",
            "applyOutputs",
            "canStartPoll",
            "canAttemptCoinPost",
        )
    )
    # This harness isolates local output-polarity ordering. The exact ingress
    # helper is compiled and failure-injected by coin_pulse_capture_lab.py.
    functions = functions.replace(
        configure,
        "bool quarantineCoinIngressTransition(){ return true; }\n" + configure,
        1,
    )

    cpp = r"""
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>

class String {
 public:
  String() = default;
  String(const char *value) : value_(value ? value : "") {}
  String(int value) : value_(std::to_string(value)) {}
  String &operator=(const char *value) {
    value_ = value ? value : "";
    return *this;
  }
  size_t length() const { return value_.size(); }
  const char *c_str() const { return value_.c_str(); }
  bool isEmpty() const { return value_.empty(); }
 private:
  std::string value_;
};

""" + config + r"""
struct Preferences {
  std::map<std::string,uint8_t> values;
  std::string fail_key;
  std::string read_override_key;
  uint8_t read_override_value=0;
  bool isKey(const char *key) const {
    return values.find(key) != values.end();
  }
  uint8_t getUChar(const char *key,uint8_t fallback) const {
    if(read_override_key==key) return read_override_value;
    auto it=values.find(key);
    return it==values.end()?fallback:it->second;
  }
  size_t putUChar(const char *key,uint8_t value) {
    if(fail_key==key) return 0;
    values[key]=value;
    return 1;
  }
};

Preferences prefs;
Config cfg;
bool outputPolarityKnown=false;
bool pinConfigSafe=false;
bool insertMode=false;
bool controllerEnabled=true,coinEnabled=true,relayEnabled=true,ledEnabled=true;
bool fsReady=true,journalRecoveryRequired=false,pendingReady=false;
bool pollIntakeSuspended=false,pendingPostAttempted=false;
bool runCoinActiveLow=true,runRelayActiveHigh=false,runLedActiveHigh=false;
uint8_t pendingPulses=0;
int runCoinPin=27,runRelayPin=26,runLedPin=2;
String activeTarget;
static const int INPUT=0,OUTPUT=1,INPUT_PULLUP=2;
static const int HIGH=1,LOW=0,FALLING=2,RISING=3;
std::map<int,int> pin_modes,pin_levels;
std::vector<std::string> gpio_ops;
void pinMode(int pin,int mode) {
  pin_modes[pin]=mode;
  gpio_ops.push_back("mode:"+std::to_string(pin)+":"+std::to_string(mode));
}
void digitalWrite(int pin,int level) {
  pin_levels[pin]=level;
  gpio_ops.push_back("write:"+std::to_string(pin)+":"+std::to_string(level));
}
int digitalPinToInterrupt(int pin) { return pin; }
void detachInterrupt(int) {}
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
void coinEdgeISR() {}
void attachInterrupt(int,void(*)(),int) {}
bool coinLineIdle() { return true; }
struct SerialStub { void println(const char *) {} } Serial;

""" + functions + r"""

void resetState() {
  prefs=Preferences();
  coinEdgeSequence=0;
  lastHandledCoinEdgeSequence=0;
  cfg=Config{};
  outputPolarityKnown=false;
  pinConfigSafe=false;
  insertMode=false;
  controllerEnabled=true;coinEnabled=true;relayEnabled=true;ledEnabled=true;
  fsReady=true;journalRecoveryRequired=false;pendingReady=false;
  pollIntakeSuspended=false;pendingPostAttempted=false;
  runCoinActiveLow=true;runRelayActiveHigh=false;runLedActiveHigh=false;
  pendingPulses=0;
  runCoinPin=27;runRelayPin=26;runLedPin=2;
  activeTarget="";
  pin_modes.clear();pin_levels.clear();gpio_ops.clear();
}

bool hasWrite(int pin) {
  const std::string prefix="write:"+std::to_string(pin)+":";
  return std::any_of(gpio_ops.begin(),gpio_ops.end(),[&](const std::string &op) {
    return op.rfind(prefix,0)==0;
  });
}
int firstWriteLevel(int pin) {
  const std::string prefix="write:"+std::to_string(pin)+":";
  for(const auto &op:gpio_ops) {
    if(op.rfind(prefix,0)==0) return op.back()=='1'?HIGH:LOW;
  }
  return -1;
}
size_t opIndex(const std::string &wanted) {
  auto it=std::find(gpio_ops.begin(),gpio_ops.end(),wanted);
  return it==gpio_ops.end()?gpio_ops.size():static_cast<size_t>(it-gpio_ops.begin());
}

int main() {
  // Legacy relayhi/ledhi keys without a local marker are not trusted.
  resetState();
  prefs.values["relayhi"]=1;
  prefs.values["ledhi"]=1;
  assert(!loadLocalOutputPolarity());
  assert(!outputPolarityKnown && !pinConfigSafe);
  configureRuntimePins(27,26,2);
  assert(pin_modes[26]==INPUT && pin_modes[2]==INPUT);
  assert(!hasWrite(26) && !hasWrite(2));
  assert(!canStartPoll());
  pendingReady=true;pendingPulses=1;
  assert(!canAttemptCoinPost());
  const size_t writesBefore=gpio_ops.size();
  applyOutputs();
  assert(gpio_ops.size()==writesBefore);

  // A corrupt/unsupported marker or out-of-range value remains unknown.
  resetState();
  prefs.values["polarityv"]=2;
  prefs.values["relayhi"]=0;
  prefs.values["ledhi"]=1;
  assert(!loadLocalOutputPolarity());
  resetState();
  prefs.values["polarityv"]=1;
  prefs.values["relayhi"]=2;
  prefs.values["ledhi"]=0;
  assert(!loadLocalOutputPolarity());

  // A failed partial write must leave the version marker invalid.
  resetState();
  cfg.relayActiveHigh=true;
  cfg.ledActiveHigh=false;
  prefs.fail_key="ledhi";
  assert(!persistLocalOutputPolarity());
  assert(prefs.values["polarityv"]==0);
  assert(!outputPolarityKnown);

  // A valid-looking but mismatched readback must invalidate the marker again.
  resetState();
  cfg.relayActiveHigh=true;
  cfg.ledActiveHigh=true;
  prefs.read_override_key="ledhi";
  prefs.read_override_value=0;
  assert(!persistLocalOutputPolarity());
  assert(prefs.values["polarityv"]==0);
  assert(!outputPolarityKnown);

  // Successful local persistence is read back before becoming authoritative.
  resetState();
  cfg.relayActiveHigh=false;
  cfg.ledActiveHigh=true;
  assert(persistLocalOutputPolarity());
  assert(outputPolarityKnown);
  assert(prefs.values["polarityv"]==1);
  assert(prefs.values["relayhi"]==0 && prefs.values["ledhi"]==1);
  outputPolarityKnown=false;
  assert(loadLocalOutputPolarity());
  assert(!runRelayActiveHigh && runLedActiveHigh);

  // Active-high local profile preloads LOW before enabling either output.
  resetState();
  prefs.values["polarityv"]=1;
  prefs.values["relayhi"]=1;
  prefs.values["ledhi"]=1;
  assert(loadLocalOutputPolarity());
  configureRuntimePins(27,26,2);
  assert(pin_modes[26]==OUTPUT && pin_modes[2]==OUTPUT);
  assert(firstWriteLevel(26)==LOW && firstWriteLevel(2)==LOW);
  assert(opIndex("write:26:0")<opIndex("mode:26:1"));
  assert(opIndex("write:2:0")<opIndex("mode:2:1"));

  // Active-low local profile preloads HIGH before enabling either output.
  resetState();
  prefs.values["polarityv"]=1;
  prefs.values["relayhi"]=0;
  prefs.values["ledhi"]=0;
  assert(loadLocalOutputPolarity());
  configureRuntimePins(27,26,2);
  assert(pin_modes[26]==OUTPUT && pin_modes[2]==OUTPUT);
  assert(firstWriteLevel(26)==HIGH && firstWriteLevel(2)==HIGH);
  assert(opIndex("write:26:1")<opIndex("mode:26:1"));
  assert(opIndex("write:2:1")<opIndex("mode:2:1"));

  std::cout << "ESP32_BOOT_POLARITY_GATE=PASS\n";
  std::cout << "UNKNOWN_AND_LEGACY_PROFILE_REMAINS_INPUT=PASS\n";
  std::cout << "LOCAL_POLARITY_MARKER_READBACK=PASS\n";
  std::cout << "ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_PRELOAD=PASS\n";
  std::cout << "REMOTE_POLARITY_AUTHORITY=DENIED\n";
  std::cout << "SIMULATED_ONLY=1\n";
  std::cout << "PHYSICAL_RELAY_POLARITY_VERIFIED=0\n";
  std::cout << "PHYSICAL_POWER_CUT_VERIFIED=0\n";
  std::cout << "FINANCIAL_PRODUCTION_AUTHORIZED=0\n";
  return 0;
}
"""
    with tempfile.TemporaryDirectory(prefix="phx-esp32-boot-polarity-") as tmp:
        cpp_path = Path(tmp) / "esp32_boot_polarity.cpp"
        exe_path = Path(tmp) / "esp32_boot_polarity"
        cpp_path.write_text(cpp, encoding="utf-8")
        compile_result = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp_path), "-o", str(exe_path)],
            text=True, capture_output=True, check=False,
        )
        require(compile_result.returncode == 0,
                "source-extracted ESP32 boot-polarity compile failed:\n" +
                compile_result.stdout + compile_result.stderr)
        result = subprocess.run(
            [str(exe_path)], text=True, capture_output=True, check=False,
        )
        require(result.returncode == 0,
                "source-extracted ESP32 boot-polarity assertions failed:\n" +
                result.stdout + result.stderr)
        print(result.stdout, end="")
    print("PHX-HARDWARE: ESP32 local-polarity boot gate source-extracted PASS")
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_RELAY_POLARITY_VERIFIED=0")
    print("PHYSICAL_POWER_CUT_VERIFIED=0")
    print("FINANCIAL_PRODUCTION_AUTHORIZED=0")


if __name__ == "__main__":
    main()
