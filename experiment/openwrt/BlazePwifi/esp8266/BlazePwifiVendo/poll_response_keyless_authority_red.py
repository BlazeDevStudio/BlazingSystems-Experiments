#!/usr/bin/env python3
"""Source-extracted regression probe for keyless ESP poll authorization.

This regression probe extracts and compiles the production acceptPollResponse() and
applyOutputs() bodies from both sketches. After the default-deny fix, the expected
result is exit 0 on both boards. Exit 1 means an unsigned keyless positive poll
was accepted and energized simulated output. This is NOT a hardware test and
must not be treated as an acceptance gate by itself.
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


def extract(source, name):
    match = re.search(
        r"\b(?:void|bool)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{",
        source,
    )
    assert match, f"missing production function: {name}"
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"unbalanced production function: {name}")


STUBS = r"""
#include <cctype>
#include <cstdint>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  String(const std::string &v):std::string(v){}
  String(int v):std::string(std::to_string(v)){}
  size_t length() const { return size(); }
  int indexOf(const char *v) const {
    const auto p=find(v); return p==npos?-1:(int)p;
  }
  bool equalsIgnoreCase(const String &v) const {
    if(size()!=v.size()) return false;
    for(size_t i=0;i<size();++i)
      if(std::tolower((unsigned char)(*this)[i])!=std::tolower((unsigned char)v[i])) return false;
    return true;
  }
};
struct Config {
#ifdef TARGET_ESP32
  String key="test-key", id="vendo-01";
#else
  char key[32]="test-key", id[32]="vendo-01";
#endif
} cfg;
String lastSentNonce="nonce-123", activeTarget="old-target";
bool insertMode=false, fsReady=true, journalRecoveryRequired=false;
bool pendingReady=false, pollIntakeSuspended=true;
bool pinConfigSafe=true, controllerEnabled=true, coinEnabled=true;
bool relayEnabled=true, ledEnabled=true;
bool runRelayActiveHigh=true, runLedActiveHigh=true;
int runRelayPin=26, runLedPin=2;
bool relayOn=false, ledOn=false;
String responseSignature="", responseTarget="target-03";
bool responseInsert=true;
String jsonString(const String &, const char *key) {
  if(std::string(key)=="response_sig") return responseSignature;
  if(std::string(key)=="target_nonce") return responseTarget;
  return String("");
}
bool jsonTrue(const String &, const char *key) {
  return std::string(key)=="insert" && responseInsert;
}
int jsonInt(const String &, const char *, int fallback) { return fallback; }
String hexDigest(const String &) { return String("unused"); }
void applyRemoteConfig(const String &) {}
void writeLogical(int pin, bool on, bool) {
  if(pin==runRelayPin) relayOn=on;
  if(pin==runLedPin) ledOn=on;
}
"""

MAIN = r"""
int main(){
#ifdef TARGET_ESP32
  cfg.key="";
#else
  cfg.key[0]='\0';
#endif
  // Start with no active target and an unsigned positive poll response.
  insertMode=false;
  activeTarget="";
  responseSignature="";
  responseTarget="target-03";
  responseInsert=true;
  pollIntakeSuspended=true;
  applyOutputs();
  if(relayOn || ledOn) return 40; // the in-flight poll must remain inhibited

  const bool accepted=acceptPollResponse(
    String("{\"ok\":true,\"insert\":true,\"target_nonce\":\"target-03\"}")
  );
  pollIntakeSuspended=false;
  applyOutputs();

  if(accepted && insertMode && activeTarget=="target-03" && relayOn && ledOn){
    std::cout << "RED: keyless positive poll energized relay and LED\n";
    return 42;
  }
  std::cout << "keyless positive poll denied\n";
  return 0;
}
"""

failed = []
reproduced = []
for board, path in BOARDS.items():
    source = path.read_text(encoding="utf-8")
    code = ("#define TARGET_ESP32\n" if board == "ESP32" else "")
    code += STUBS + extract(source, "acceptPollResponse") + extract(source, "coinIngressConfigurationAllows") + extract(source, "applyOutputs") + MAIN
    with tempfile.TemporaryDirectory(prefix="phx-keyless-poll-red-") as folder:
        cpp = Path(folder) / "probe.cpp"
        binary = Path(folder) / "probe"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30,
        )
        if built.returncode:
            print(board, "COMPILE FAIL", built.stderr[-2000:])
            failed.append(board)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        if ran.returncode == 42:
            print(board, "EXPECTED RED REPRODUCED", ran.stdout.strip())
            reproduced.append(board)
        elif ran.returncode == 0:
            print(board, "NO KEYLESS AUTHORITY GAP", ran.stdout.strip())
        else:
            print(board, "PROBE ERROR", ran.returncode, ran.stdout, ran.stderr)
            failed.append(board)

if failed:
    sys.exit("probe execution failed: " + ",".join(failed))
if reproduced:
    print("AUDIT_RESULT=KEYLESS_AUTHORITY_GAP_REPRODUCED")
    sys.exit(1)
print("AUDIT_RESULT=NO_KEYLESS_AUTHORITY_GAP")
