#!/usr/bin/env python3
"""Source-exact ESP8266 cold-boot polarity and persistence regression.

Host-only. This lab does not infer physical relay polarity or electrical safety.
It verifies that only a validated local ConfigV3 value can enable GPIO outputs.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "BlazePwifiVendo.ino"


def extract_functions(source: str, name: str) -> list[str]:
    pattern = re.compile(
        r"\b(?:void|bool|uint32_t|int|size_t|String)\s+"
        + re.escape(name) + r"\s*\([^;{}]*\)\s*\{"
    )
    found = []
    for match in pattern.finditer(source):
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
                    found.append(source[match.start():i + 1])
                    break
            i += 1
    return found


def extract_struct(source: str, name: str) -> str:
    match = re.search(
        r"\bstruct\s+" + re.escape(name) + r"\s*\{.*?\};",
        source,
        flags=re.S,
    )
    if not match:
        raise AssertionError("missing production struct " + name)
    return match.group(0)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    # These checks intentionally fail on the pre-implementation source.
    for token, message in (
        ("struct ConfigV2", "V2 compatibility record is missing"),
        ("outputPolarityConfigured", "local polarity-validity field is missing"),
        ("bool outputPolarityKnown=false", "boot polarity authority is not explicit"),
        ("configChecksum", "ConfigV3 corruption detection is missing"),
        ('name=relay_active_high', "local relay polarity selector is missing"),
        ('name=led_active_high', "local LED polarity selector is missing"),
        ('web.arg(\"relay_active_high\")', "relay polarity is not read from local setup"),
        ('web.arg(\"led_active_high\")', "LED polarity is not read from local setup"),
    ):
        require(token in source, message)

    load_cfg = extract_functions(source, "loadCfg")
    configure = extract_functions(source, "configureRuntimePins")
    apply_outputs = extract_functions(source, "applyOutputs")
    can_poll = extract_functions(source, "canStartPoll")
    can_post = extract_functions(source, "canAttemptCoinPost")
    save_cfg = extract_functions(source, "saveCfg")
    latch_failure = extract_functions(source, "latchConfigPersistenceFailure")
    require(len(load_cfg) == 1, "expected one loadCfg implementation")
    require(len(configure) == 1, "expected one configureRuntimePins implementation")
    require(len(apply_outputs) == 1, "expected one applyOutputs implementation")
    require(len(can_poll) == 1 and len(can_post) == 1, "admission helpers missing")
    require(len(save_cfg) == 1 and "bool saveCfg" in save_cfg[0],
            "saveCfg must return commit/readback status")
    require(len(latch_failure) == 1, "config persistence failure latch is missing")

    structs = "\n".join(extract_struct(source, name)
                       for name in ("ConfigV1", "ConfigV2", "Config"))
    functions = "\n".join(
        extract_functions(source, name)[0]
        for name in ("fixedStringTerminated", "configChecksum",
                     "configPolarityFieldsValid", "makeSetupPassword",
                     "defaults", "saveCfg", "latchConfigPersistenceFailure",
                     "loadCfg", "writeLogical", "configureRuntimePins",
                     "applyOutputs", "coinLineIdle", "canStartPoll", "canAttemptCoinPost")
    )
    string_checks = "\n".join(extract_functions(source, "configStringsTerminated"))
    require(len(extract_functions(source, "configStringsTerminated")) == 3,
            "V1/V2/V3 bounded-string validators are required")

    portal_start = source.index("void setupPortal()")
    portal_end = source.index("void connectSta()", portal_start)
    portal = source[portal_start:portal_end]
    route_start = portal.index('web.on("/save"')
    route = portal[route_start:]
    guard = route.find("if(!saveCfg())")
    success = route.find('web.send(200,"text/plain","Wi-Fi and local output polarity settings verified and saved.')
    restart = route.find("ESP.restart()")
    require(guard >= 0 and success > guard and restart > success,
            "setup route must fail closed before success response/reboot")
    failure_block = route[guard:success]
    require("web.send(500" in failure_block and "return;" in failure_block,
            "failed config persistence must return HTTP 500 without reboot")
    require('relayPolarity!="0"' in route and 'relayPolarity!="1"' in route and
            'ledPolarity!="0"' in route and 'ledPolarity!="1"' in route,
            "local polarity values must be strictly limited to 0 or 1")

    remote = extract_functions(source, "applyRemoteConfig")
    require(len(remote) == 1 and "relay_active_high" not in remote[0] and
            "led_active_high" not in remote[0],
            "unauthenticated remote config must not set output polarity")
    setup = extract_functions(source, "setup")
    require(len(setup) == 1 and
            setup[0].find("loadCfg()") < setup[0].find("configureRuntimePins("),
            "local polarity must load before first runtime GPIO configuration")
    require("if(!outputPolarityKnown) return;" in apply_outputs[0],
            "applyOutputs must not drive pins before local polarity is known")
    require("!outputPolarityKnown" in configure[0] and
            "pinMode(runRelayPin,INPUT)" in configure[0] and
            "pinMode(runLedPin,INPUT)" in configure[0],
            "unknown polarity must leave relay/LED pins as inputs")
    require("outputPolarityKnown" in can_poll[0] and
            "outputPolarityKnown" in can_post[0],
            "poll and coin POST admission must remain disabled until polarity is known")

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

""" + structs + r"""
static const uint32_t MAGIC_V1=0x42505731;
static const uint32_t MAGIC_V2=0x42505732;
static const uint32_t MAGIC=0x42505733;
static const size_t POLL_FAULT_EEPROM_OFFSET=512;
static const size_t POLL_FAULT_EEPROM_BYTES=544;

struct String {
  std::string value;
  String() = default;
  String(const char *s) : value(s ? s : "") {}
  String &operator=(const char *s) { value=s ? s : ""; return *this; }
  size_t length() const { return value.size(); }
};
struct EspStub { uint32_t random(){ return 0x12345678u; } } ESP;
struct SerialStub { void println(const char*){} } Serial;

size_t strlcpy(char *dst,const char *src,size_t cap){
  const size_t n=std::strlen(src);
  if(cap){const size_t copy=std::min(n,cap-1);std::memcpy(dst,src,copy);dst[copy]='\0';}
  return n;
}

struct FakeEEPROM {
  std::vector<uint8_t> flash=std::vector<uint8_t>(POLL_FAULT_EEPROM_BYTES,0xFF);
  std::vector<uint8_t> buffer;
  size_t size=0;
  bool failCommit=false;
  bool failRead=false;
  void begin(size_t n){
    size=n;
    if(flash.size()<n) flash.resize(n,0xFF);
    buffer.assign(flash.begin(),flash.begin()+n);
  }
  bool commit(){
    if(failCommit) return false;
    flash=buffer;
    return true;
  }
  bool end(){
    const bool ok=commit();
    size=0;
    buffer.clear();
    return ok;
  }
  size_t length() const { return size; }
  template<class T> void get(size_t offset,T &value){
    if(failRead || offset+sizeof(T)>buffer.size()){
      std::memset(&value,0xA5,sizeof(T));
      return;
    }
    std::memcpy(&value,buffer.data()+offset,sizeof(T));
  }
  template<class T> void put(size_t offset,const T &value){
    if(offset+sizeof(T)>buffer.size()) return;
    std::memcpy(buffer.data()+offset,&value,sizeof(T));
  }
} EEPROM;

Config cfg{};
bool pollFaultBackupReady=false;
bool outputPolarityKnown=false;
bool pinConfigSafe=true;
bool journalRecoveryRequired=false;
bool insertMode=false;
bool runRelayActiveHigh=false;
bool runLedActiveHigh=false;
bool runCoinActiveLow=true;
bool controllerEnabled=true,coinEnabled=true,relayEnabled=true,ledEnabled=true;
bool fsReady=true,pendingReady=false,pendingPostAttempted=false;
bool pollIntakeSuspended=false;
uint8_t pendingPulses=0;
int runCoinPin=4,runRelayPin=5,runLedPin=14;
String activeTarget;

uint32_t configChecksum(const Config &c);
bool fixedStringTerminated(const char *value,size_t capacity);
bool configStringsTerminated(const Config &c);
bool configStringsTerminated(const ConfigV2 &c);
bool configStringsTerminated(const ConfigV1 &c);
bool configPolarityFieldsValid(const Config &c);
void makeSetupPassword();
void defaults();
bool saveCfg();
void latchConfigPersistenceFailure(const char *reason);
void loadCfg();

static const int INPUT=0, OUTPUT=1, INPUT_PULLUP=2;
static const int HIGH=1, LOW=0, FALLING=2, RISING=3;
void pinMode(int,int);
void digitalWrite(int,int);
int digitalPinToInterrupt(int);
void detachInterrupt(int);
void coinEdgeISR();
void attachInterrupt(int,void(*)(),int);
int digitalRead(int);

""" + string_checks + "\n" + functions + r"""

std::map<int,int> pinModes, pinLevels;
std::vector<std::string> gpioOps;
void pinMode(int pin,int mode){
  pinModes[pin]=mode;
  gpioOps.push_back("mode:"+std::to_string(pin)+":"+std::to_string(mode));
}
void digitalWrite(int pin,int level){
  pinLevels[pin]=level;
  gpioOps.push_back("write:"+std::to_string(pin)+":"+std::to_string(level));
}
int digitalPinToInterrupt(int pin){ return pin; }
void detachInterrupt(int){}
void coinEdgeISR(){}
void attachInterrupt(int,void(*)(),int){}
int digitalRead(int){ return HIGH; }

void resetState(){
  EEPROM=FakeEEPROM();
  cfg=Config{};
  pollFaultBackupReady=false;
  outputPolarityKnown=false;
  pinConfigSafe=true;
  journalRecoveryRequired=false;
  insertMode=false;
  runRelayActiveHigh=false;
  runLedActiveHigh=false;
  runCoinActiveLow=true;
  controllerEnabled=true;coinEnabled=true;relayEnabled=true;ledEnabled=true;
  fsReady=true;pendingReady=false;pendingPostAttempted=false;
  pollIntakeSuspended=false;pendingPulses=0;
  runCoinPin=4;runRelayPin=5;runLedPin=14;
  activeTarget=String("");
  pinModes.clear();pinLevels.clear();gpioOps.clear();
}

Config makeV3(bool relayHigh,bool ledHigh,bool configured=true){
  Config c;
  std::memset(&c,0,sizeof(c));
  c.magic=MAGIC;
  std::strcpy(c.ssid,"test-ssid");
  std::strcpy(c.pass,"test-password");
  std::strcpy(c.server,"10.0.0.1");
  std::strcpy(c.key,"test-key");
  std::strcpy(c.id,"vendo-01");
  std::strcpy(c.apPass,"12345678");
  c.coinPin=4;c.insertLedPin=14;c.relayPin=5;c.coinActiveLow=1;
  c.relayActiveHigh=relayHigh?1:0;
  c.ledActiveHigh=ledHigh?1:0;
  c.outputPolarityConfigured=configured?1:0;
  c.checksum=configChecksum(c);
  return c;
}
void seedV3(bool relayHigh,bool ledHigh,bool configured=true){
  Config c=makeV3(relayHigh,ledHigh,configured);
  std::memcpy(EEPROM.flash.data(),&c,sizeof(c));
}
void seedV2(){
  ConfigV2 c;
  std::memset(&c,0,sizeof(c));
  c.magic=MAGIC_V2;
  std::strcpy(c.ssid,"old-ssid");std::strcpy(c.pass,"old-password");
  std::strcpy(c.server,"10.0.0.2");std::strcpy(c.key,"old-key");
  std::strcpy(c.id,"old-vendo");std::strcpy(c.apPass,"12345678");
  c.coinPin=4;c.insertLedPin=14;c.relayPin=5;c.coinActiveLow=1;
  std::memcpy(EEPROM.flash.data(),&c,sizeof(c));
}
void seedV1(){
  ConfigV1 c;
  std::memset(&c,0,sizeof(c));
  c.magic=MAGIC_V1;
  std::strcpy(c.ssid,"v1-ssid");std::strcpy(c.pass,"v1-password");
  std::strcpy(c.server,"10.0.0.3");std::strcpy(c.key,"v1-key");
  std::strcpy(c.id,"v1-vendo");
  c.coinPin=4;c.insertLedPin=14;c.relayPin=5;c.coinActiveLow=1;
  std::memcpy(EEPROM.flash.data(),&c,sizeof(c));
}

// A future schema marker must never be rewritten by older firmware.
void seedUnknownFutureVersion(){
  std::memset(EEPROM.flash.data(),0xA5,EEPROM.flash.size());
  const uint32_t futureMagic=0x42505734;
  std::memcpy(EEPROM.flash.data(),&futureMagic,sizeof(futureMagic));
}
std::vector<uint8_t> markerBytes(){
  return std::vector<uint8_t>(EEPROM.flash.begin()+POLL_FAULT_EEPROM_OFFSET,
                              EEPROM.flash.begin()+POLL_FAULT_EEPROM_OFFSET+20);
}
void assertUnknownPolarity(){
  assert(!outputPolarityKnown);
  assert(!pinConfigSafe);
  assert(!insertMode);
  assert(activeTarget.length()==0);
}
void assertConfiguredPolarity(bool relayHigh,bool ledHigh){
  assert(outputPolarityKnown);
  assert(runRelayActiveHigh==relayHigh);
  assert(runLedActiveHigh==ledHigh);
}

int main(){
  resetState();
  seedV3(true,true,true);
  loadCfg();
  assertConfiguredPolarity(true,true);

  resetState();
  seedV3(false,false,true);
  loadCfg();
  assertConfiguredPolarity(false,false);

  resetState();
  seedV3(true,false,false);
  loadCfg();
  assertUnknownPolarity();

  resetState();
  seedV3(true,true,true);
  EEPROM.flash[offsetof(Config,checksum)]^=0x01;
  loadCfg();
  assertUnknownPolarity();
  assert(cfg.magic==MAGIC && cfg.outputPolarityConfigured==0);

  resetState();
  seedV2();
  for(size_t i=POLL_FAULT_EEPROM_OFFSET;i<POLL_FAULT_EEPROM_OFFSET+20;i++)
    EEPROM.flash[i]=(uint8_t)(0x40+i-POLL_FAULT_EEPROM_OFFSET);
  const auto markerBefore=markerBytes();
  loadCfg();
  assertUnknownPolarity();
  assert(cfg.magic==MAGIC && cfg.outputPolarityConfigured==0);
  assert(markerBytes()==markerBefore);

  resetState();
  seedV1();
  loadCfg();
  assertUnknownPolarity();
  assert(cfg.magic==MAGIC && cfg.outputPolarityConfigured==0);

  resetState();
  loadCfg(); // erased/missing configuration
  assertUnknownPolarity();
  assert(cfg.magic==MAGIC && cfg.outputPolarityConfigured==0);

  resetState();
  seedUnknownFutureVersion();
  const auto futureBytesBefore=EEPROM.flash;
  loadCfg();
  assertUnknownPolarity();
  assert(journalRecoveryRequired);
  assert(EEPROM.flash==futureBytesBefore);

  resetState();
  EEPROM.failCommit=true;
  loadCfg();
  assertUnknownPolarity();
  assert(journalRecoveryRequired);

  resetState();
  EEPROM.failRead=true;
  loadCfg();
  assertUnknownPolarity();
  assert(journalRecoveryRequired);

  resetState();
  outputPolarityKnown=false;
  configureRuntimePins(4,5,14);
  assert(pinModes[5]==INPUT && pinModes[14]==INPUT);
  assert(pinLevels.find(5)==pinLevels.end() && pinLevels.find(14)==pinLevels.end());
  assert(!canStartPoll());
  pendingReady=true;pendingPulses=1;
  assert(!canAttemptCoinPost());
  const size_t before=pinLevels.size();
  applyOutputs();
  assert(pinLevels.size()==before);

  resetState();
  outputPolarityKnown=true;
  runRelayActiveHigh=true;runLedActiveHigh=true;
  configureRuntimePins(4,5,14);
  assert(pinModes[5]==OUTPUT && pinModes[14]==OUTPUT);
  assert(pinLevels[5]==LOW && pinLevels[14]==LOW);
  auto relayWrite=std::find(gpioOps.begin(),gpioOps.end(),"write:5:0");
  auto relayMode=std::find(gpioOps.begin(),gpioOps.end(),"mode:5:1");
  auto ledWrite=std::find(gpioOps.begin(),gpioOps.end(),"write:14:0");
  auto ledMode=std::find(gpioOps.begin(),gpioOps.end(),"mode:14:1");
  assert(relayWrite<relayMode && ledWrite<ledMode);

  resetState();
  outputPolarityKnown=true;
  runRelayActiveHigh=false;runLedActiveHigh=false;
  configureRuntimePins(4,5,14);
  assert(pinModes[5]==OUTPUT && pinModes[14]==OUTPUT);
  assert(pinLevels[5]==HIGH && pinLevels[14]==HIGH);

  std::cout << "ESP8266_BOOT_POLARITY_CONFIG_V3=PASS\\n";
  std::cout << "V1_V2_MIGRATION_REMAINS_UNCONFIGURED=PASS\\n";
  std::cout << "MISSING_CORRUPT_COMMIT_READBACK_FAIL_CLOSED=PASS\\n";
  std::cout << "RESERVED_POLL_FAULT_BYTES_PRESERVED=PASS\\n";
  std::cout << "UNKNOWN_POLARITY_OUTPUTS_REMAIN_INPUT=PASS\\n";
  std::cout << "ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_PRELOAD=PASS\\n";
  std::cout << "SIMULATED_ONLY=1\\n";
  std::cout << "PHYSICAL_RELAY_POLARITY_VERIFIED=0\\n";
  std::cout << "PHYSICAL_POWER_CUT_VERIFIED=0\\n";
  std::cout << "FINANCIAL_PRODUCTION_AUTHORIZED=0\\n";
  return 0;
}
"""
    with tempfile.TemporaryDirectory(prefix="phx-esp8266-boot-polarity-") as folder:
        cpp_path = Path(folder) / "boot_polarity.cpp"
        exe_path = Path(folder) / "boot_polarity"
        cpp_path.write_text(cpp, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             str(cpp_path), "-o", str(exe_path)],
            capture_output=True, text=True, timeout=30,
        )
        require(built.returncode == 0,
                "source-extracted C++ build failed:\n" + built.stderr[-5000:])
        result = subprocess.run(
            [str(exe_path)], capture_output=True, text=True, timeout=10,
        )
        require(result.returncode == 0,
                "source-extracted boot polarity assertions failed:\n" +
                result.stdout + result.stderr)
        print(result.stdout, end="")
    print("ESP8266_BOOT_POLARITY_LAB=PASS")


if __name__ == "__main__":
    main()
