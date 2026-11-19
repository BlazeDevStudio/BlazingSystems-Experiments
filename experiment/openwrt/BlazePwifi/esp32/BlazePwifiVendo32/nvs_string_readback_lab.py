#!/usr/bin/env python3
"""Exact-source ESP32 Preferences string-readback error/sentinel-collision lab.

Compiles the production nvsStringMatchesStored() and
configFieldsMatchStored() functions with a fake Preferences backend.
It injects NVS length/read errors while valid values deliberately equal the
old fallback sentinel. No credentials, board, GPIO, relay, or real NVS used.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "esp8266" / "BlazePwifiVendo"))
from firmware_lab_source import extract_function  # noqa: E402

SKETCH = ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"


def verify_shared_extractor() -> None:
    probe = (
        "bool sample() {\n"
        '  const char *brace = "}";\n'
        "  // }\n"
        "  /* { */\n"
        "  return brace[0] == '}';\n"
        "}\n"
        "bool after() { return false; }\n"
    )
    expected = probe.split("\nbool after", 1)[0]
    actual = extract_function(probe, "sample")
    if actual != expected:
        raise RuntimeError("shared extractor did not preserve the complete function around brace decoys")
    print("SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS")

CPP = r'''
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

using String = std::string;

struct Config {
  String ssid, pass, server, key, id, apPass;
  int coinPin=27, insertLedPin=2, relayPin=26;
  bool coinActiveLow=true, relayActiveHigh=false, ledActiveHigh=false;
  uint16_t coinDebounceMs=40, pulseGroupMs=400;
};
Config cfg;

struct FakePreferences {
  std::map<std::string,std::string> strings;
  std::map<std::string,int> ints;
  std::map<std::string,bool> bools;
  std::map<std::string,uint32_t> uints;
  std::map<std::string,uint8_t> uchars;
  std::string failLengthKey;
  std::string failReadKey;
  unsigned writeCount=0;

  bool begin(const char *, bool=false, const char * = nullptr) { return true; }
  void end() {}

  bool isKey(const char *key) const {
    const std::string k(key);
    return strings.count(k) || ints.count(k) || bools.count(k) ||
           uints.count(k) || uchars.count(k);
  }

  String getString(const char *key,const String &fallback) const {
    const std::string k(key);
    auto it=strings.find(k);
    if(it==strings.end() || failReadKey==k) return fallback;
    return it->second;
  }

  size_t getStringLength(const char *key) const {
    const std::string k(key);
    auto it=strings.find(k);
    if(it==strings.end() || failLengthKey==k) return 0;
    return it->second.size()+1;
  }

  size_t getString(const char *key,char *value,size_t maxLen) const {
    const std::string k(key);
    auto it=strings.find(k);
    if(it==strings.end() || failReadKey==k) return 0;
    const size_t bytes=it->second.size()+1;
    if(bytes>maxLen) return 0;
    std::memcpy(value,it->second.c_str(),bytes);
    return bytes;
  }

  int getInt(const char *key,int fallback) const {
    auto it=ints.find(key);
    return it==ints.end()?fallback:it->second;
  }

  bool getBool(const char *key,bool fallback) const {
    auto it=bools.find(key);
    return it==bools.end()?fallback:it->second;
  }

  uint32_t getUInt(const char *key,uint32_t fallback) const {
    auto it=uints.find(key);
    return it==uints.end()?fallback:it->second;
  }

  uint8_t getUChar(const char *key,uint8_t fallback) const {
    auto it=uchars.find(key);
    return it==uchars.end()?fallback:it->second;
  }

  size_t putString(const char *key,const String &value) {
    strings[key]=value;
    ++writeCount;
    return value.size();
  }
};
FakePreferences prefs;

bool outputPolarityKnown=false;
bool runRelayActiveHigh=false;
bool runLedActiveHigh=false;
bool pinConfigSafe=false;
bool insertMode=false;
String activeTarget;
struct SerialStub {
  void println(const char *) const {}
  template<class... Args> void printf(const char *,Args...) const {}
} Serial;
uint32_t esp_random(){ return 0x12345678U; }

@@BOUNDED@@
@@HELPER@@
@@MATCH@@
@@POLARITY@@
@@LOAD@@

static void seedSentinelValues() {
  const String sentinel="__PHX_NVS_READBACK_MISSING__";
  cfg.ssid=sentinel;
  cfg.pass=sentinel;
  cfg.server=sentinel;
  cfg.key=sentinel;
  cfg.id=sentinel;
  cfg.coinPin=27;
  cfg.insertLedPin=2;
  cfg.relayPin=26;
  cfg.coinActiveLow=true;
  cfg.coinDebounceMs=40;
  cfg.pulseGroupMs=400;

  prefs.strings["ssid"]=sentinel;
  prefs.strings["pass"]=sentinel;
  prefs.strings["server"]=sentinel;
  prefs.strings["key"]=sentinel;
  prefs.strings["id"]=sentinel;
  prefs.ints["coinpin"]=27;
  prefs.ints["ledpin"]=2;
  prefs.ints["relaypin"]=26;
  prefs.bools["coinlow"]=true;
  prefs.uints["debounce"]=40;
  prefs.uints["groupms"]=400;
}

static void seedValidBootConfig() {
  prefs=FakePreferences{};
  cfg=Config{};
  prefs.strings["ssid"]="ssid-boot";
  prefs.strings["pass"]="pass-boot";
  prefs.strings["server"]="192.0.2.99";
  prefs.strings["key"]="key-boot";
  prefs.strings["id"]="vendo-boot";
  prefs.strings["appass"]="local-admin-pass-123";
  prefs.ints["coinpin"]=27;
  prefs.ints["ledpin"]=2;
  prefs.ints["relaypin"]=26;
  prefs.bools["coinlow"]=true;
  prefs.uints["debounce"]=40;
  prefs.uints["groupms"]=400;
  prefs.uchars["polarityv"]=1;
  prefs.uchars["relayhi"]=0;
  prefs.uchars["ledhi"]=1;
}

static void simulateNvsReboot() {
  const FakePreferences persisted=prefs;
  prefs=FakePreferences{};
  prefs.strings=persisted.strings;
  prefs.ints=persisted.ints;
  prefs.bools=persisted.bools;
  prefs.uints=persisted.uints;
  prefs.uchars=persisted.uchars;
}

static void resetBootRuntime() {
  cfg=Config{};
  outputPolarityKnown=false;
  runRelayActiveHigh=false;
  runLedActiveHigh=false;
  pinConfigSafe=false;
  insertMode=true;
  activeTarget="stale-before-boot";
}

static bool validNvsRebootRestoresPolarity() {
  seedValidBootConfig();
  simulateNvsReboot();
  resetBootRuntime();
  loadConfig();
  return outputPolarityKnown && pinConfigSafe &&
         !runRelayActiveHigh && runLedActiveHigh &&
         cfg.ssid=="ssid-boot" && cfg.pass=="pass-boot" &&
         cfg.server=="192.0.2.99" && cfg.key=="key-boot" &&
         cfg.id=="vendo-boot" && !insertMode && activeTarget.empty() &&
         prefs.writeCount==0;
}

static bool bootReadFailureKeepsOutputsOff(const char *key,bool lengthFailure) {
  seedValidBootConfig();
  simulateNvsReboot();
  resetBootRuntime();
  if(lengthFailure) prefs.failLengthKey=key;
  else prefs.failReadKey=key;
  loadConfig();
  return !outputPolarityKnown && !pinConfigSafe &&
         !runRelayActiveHigh && !runLedActiveHigh &&
         !cfg.relayActiveHigh && !cfg.ledActiveHigh &&
         !insertMode && activeTarget.empty() && prefs.writeCount==0;
}

int main() {
  seedSentinelValues();
  const char *failed=nullptr;
  if(!configFieldsMatchStored(&failed)) {
    std::cerr<<"NORMAL_READBACK_REJECTED field="<<(failed?failed:"unknown")<<"\n";
    return 10;
  }

  const char *keys[]={"ssid","pass","server","key","id"};
  for(const char *key:keys) {
    prefs.failReadKey=key;
    failed=nullptr;
    if(configFieldsMatchStored(&failed)) {
      std::cerr<<"SENTINEL_COLLISION_FAIL_OPEN key="<<key<<"\n";
      return 42;
    }
    if(!failed || std::strcmp(failed,key)!=0) {
      std::cerr<<"WRONG_FAILED_FIELD_ON_READ_ERROR key="<<key<<"\n";
      return 43;
    }
    prefs.failReadKey.clear();

    prefs.failLengthKey=key;
    failed=nullptr;
    if(configFieldsMatchStored(&failed)) {
      std::cerr<<"STRING_LENGTH_ERROR_ACCEPTED key="<<key<<"\n";
      return 44;
    }
    if(!failed || std::strcmp(failed,key)!=0) {
      std::cerr<<"WRONG_FAILED_FIELD_ON_LENGTH_ERROR key="<<key<<"\n";
      return 45;
    }
    prefs.failLengthKey.clear();
  }

  cfg.pass.clear();
  prefs.strings["pass"].clear();
  failed=nullptr;
  if(!configFieldsMatchStored(&failed)) {
    std::cerr<<"VALID_EMPTY_STRING_REJECTED field="<<(failed?failed:"unknown")<<"\n";
    return 46;
  }

  prefs.strings["server"]="different";
  failed=nullptr;
  if(configFieldsMatchStored(&failed) || !failed || std::strcmp(failed,"server")!=0) {
    std::cerr<<"MISMATCH_NOT_REJECTED_OR_WRONG_FIELD\n";
    return 47;
  }

  if(!validNvsRebootRestoresPolarity()) {
    std::cerr<<"VALID_NVS_REBOOT_DID_NOT_RESTORE_LOCAL_POLARITY\n";
    return 48;
  }
  const char *bootKeys[]={"ssid","pass","server","key","id"};
  for(const char *key:bootKeys) {
    if(!bootReadFailureKeepsOutputsOff(key,false)) {
      std::cerr<<"NVS_BOOT_STRING_READ_ERROR_TRUSTED_POLARITY key="<<key<<"\n";
      return 50;
    }
    if(!bootReadFailureKeepsOutputsOff(key,true)) {
      std::cerr<<"NVS_BOOT_STRING_LENGTH_ERROR_TRUSTED_POLARITY key="<<key<<"\n";
      return 51;
    }
  }
  std::cout<<"ESP32_NVS_REBOOT_READ_FAILURE_FAIL_CLOSED_PASS 5/5 string reads and 5/5 length reads\n";
  std::cout<<"NVS_STRING_READBACK_EXPLICIT_STATUS_PASS 5/5 read failures, 5/5 length failures, empty and mismatch controls\n";
  return 0;
}
'''


def build_program(source: str, omit_boot_readback_guard: bool = False) -> str:
    bounded = "\n\n".join((
        extract_function(source, "boundedCoinDebounceMs"),
        extract_function(source, "boundedTimingMs"),
    ))
    helper = extract_function(source, "nvsStringMatchesStored", required=False)
    match = extract_function(source, "configFieldsMatchStored")
    polarity = extract_function(source, "loadLocalOutputPolarity")
    load = extract_function(source, "loadConfig")
    if omit_boot_readback_guard:
        guard = """  if(outputPolarityKnown){
    const char *failedField=nullptr;
    if(!configFieldsMatchStored(&failedField)){
      cfg.relayActiveHigh=false;
      cfg.ledActiveHigh=false;
      runRelayActiveHigh=false;
      runLedActiveHigh=false;
      outputPolarityKnown=false;
      pinConfigSafe=false;
      insertMode=false;
      activeTarget="";
      Serial.printf("CRITICAL: NVS config readback failed at key '%s'; outputs remain INPUT.\\n",
                    failedField?failedField:"unknown");
    }
  }"""
        if load.count(guard) != 1:
            raise RuntimeError("cannot build boot-readback guard-removal mutation")
        load = load.replace(guard, "  // injected mutation: skip boot-time config readback gate", 1)
    return (CPP.replace("@@BOUNDED@@", bounded)
               .replace("@@HELPER@@", helper)
               .replace("@@MATCH@@", match)
               .replace("@@POLARITY@@", polarity)
               .replace("@@LOAD@@", load))


def compile_and_run(program: str, label: str, expect_success: bool,
                    expected_failure: str = "") -> None:
    with tempfile.TemporaryDirectory(prefix="phx-nvs-string-readback-") as temp:
        cpp = Path(temp) / "nvs_string_readback.cpp"
        binary = Path(temp) / "nvs_string_readback"
        cpp.write_text(program, encoding="utf-8")
        compiled = subprocess.run(
            ["g++","-std=c++17","-Wall","-Wextra","-Werror","-pedantic","-O2",
             str(cpp),"-o",str(binary)],
            capture_output=True,text=True,check=False,timeout=30,
        )
        if compiled.returncode:
            raise RuntimeError(label+" compile failed:\n"+compiled.stderr[-5000:])
        result = subprocess.run(
            [str(binary)],capture_output=True,text=True,check=False,timeout=10,
        )
        output = result.stdout + result.stderr
        if expect_success:
            if result.returncode:
                print(output, end="")
                raise RuntimeError(label+" expected exit 0, got "+str(result.returncode))
            print(result.stdout, end="")
            return
        if result.returncode == 0:
            raise RuntimeError(label+" mutation unexpectedly survived")
        if expected_failure and expected_failure not in output:
            print(output, end="")
            raise RuntimeError(label+" failed for an unexpected reason")
        print("MUTATION_REJECTED "+label+" exit="+str(result.returncode))
        print(output, end="")


def main() -> None:
    source = SKETCH.read_text(encoding="utf-8")
    verify_shared_extractor()
    compile_and_run(
        build_program(source),
        "ESP32 NVS boot readback regression",
        True,
    )
    compile_and_run(
        build_program(source, omit_boot_readback_guard=True),
        "ESP32 missing boot readback guard mutation",
        False,
        "NVS_BOOT_STRING_READ_ERROR_TRUSTED_POLARITY key=ssid",
    )

if __name__=="__main__":
    main()
