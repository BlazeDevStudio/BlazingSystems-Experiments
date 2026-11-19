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
        'bool sample() {\\n'
        '  const char *brace = "}";\\n'
        '  // }\\n'
        '  /* { */\\n'
        '  return brace[0] == \' }\';\\n'
        '}\\n'
        'bool after() { return false; }\\n'
    )
    expected = probe.split("\\nbool after", 1)[0]
    actual = extract_function(probe, "sample")
    if actual != expected:
        raise RuntimeError("shared extractor did not preserve the complete function around brace decoys")
    print("SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS")


CPP = r'''
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

using String = std::string;

struct Config {
  String ssid, pass, server, key, id;
  int coinPin=27, insertLedPin=2, relayPin=26;
  bool coinActiveLow=true;
  uint16_t coinDebounceMs=40, pulseGroupMs=400;
};
Config cfg;

struct FakePreferences {
  std::map<std::string,std::string> strings;
  std::map<std::string,int> ints;
  std::map<std::string,bool> bools;
  std::map<std::string,uint32_t> uints;
  std::string failLengthKey;
  std::string failReadKey;

  bool isKey(const char *key) const {
    const std::string k(key);
    return strings.count(k) || ints.count(k) || bools.count(k) || uints.count(k);
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
};
FakePreferences prefs;

@@HELPER@@
@@MATCH@@

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

  std::cout<<"NVS_STRING_READBACK_EXPLICIT_STATUS_PASS 5/5 read failures, 5/5 length failures, empty and mismatch controls\n";
  return 0;
}
'''


def main() -> None:
    source = SKETCH.read_text(encoding="utf-8")
    verify_shared_extractor()
    helper = extract_function(source, "nvsStringMatchesStored", required=False)
    match = extract_function(source, "configFieldsMatchStored")
    program = CPP.replace("@@HELPER@@", helper).replace("@@MATCH@@", match)

    with tempfile.TemporaryDirectory(prefix="phx-nvs-string-readback-") as temp:
        cpp = Path(temp) / "nvs_string_readback.cpp"
        binary = Path(temp) / "nvs_string_readback"
        cpp.write_text(program, encoding="utf-8")
        compiled = subprocess.run(
            ["g++","-std=c++17","-Wall","-Wextra","-Werror","-pedantic","-O2",
             str(cpp),"-o",str(binary)],
            capture_output=True,text=True,check=False,
        )
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        result = subprocess.run([str(binary)],capture_output=True,text=True,check=False)
        if result.stdout:
            print(result.stdout,end="")
        if result.stderr:
            print(result.stderr,end="")
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__=="__main__":
    main()
