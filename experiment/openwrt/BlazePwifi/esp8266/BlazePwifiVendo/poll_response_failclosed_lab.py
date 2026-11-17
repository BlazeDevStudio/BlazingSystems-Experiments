#!/usr/bin/env python3
"""Source-exact host lab for fail-closed ESP poll-response handling.

Compiles the production poll-status parser, acceptPollResponse(), and applyOutputs() functions from both board sketches. This is simulated control-flow evidence only.
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
    match = re.search(r"\b(?:void|bool)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", source)
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
#include <cstring>
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
String lastSentNonce="nonce-123";
String activeTarget="old-target";
bool insertMode=true, fsReady=true, journalRecoveryRequired=false;
bool pendingReady=false, pollIntakeSuspended=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true;
bool runRelayActiveHigh=true, runLedActiveHigh=true;
int runRelayPin=26, runLedPin=2;
bool relayOn=false, ledOn=false;
String responseSignature="valid-signature", responseTarget="target-01";
bool responseInsert=true;
int applyRemoteConfigCalls=0;
String jsonString(const String &, const char *key) {
  if(std::string(key)=="response_sig") return responseSignature;
  if(std::string(key)=="target_nonce") return responseTarget;
  return String("");
}
bool jsonTrue(const String &, const char *key) {
  return std::string(key)=="insert" && responseInsert;
}
int jsonInt(const String &, const char *, int fallback) { return fallback==0?123:fallback; }
String hexDigest(const String &) { return String("valid-signature"); }
void applyRemoteConfig(const String &) { ++applyRemoteConfigCalls; }
void writeLogical(int pin, bool on, bool) {
  if(pin==runRelayPin) relayOn=on;
  if(pin==runLedPin) ledOn=on;
}
"""

MAIN = r"""
int main(){
  // Root-only ok parsing: nested objects, arrays and quoted text are not authority.
  if(!pollJsonTopLevelTrue(String("{\"ok\":true}"),"ok")) return 31;
  if(pollJsonTopLevelTrue(String("{\"ok\":false,\"controller\":{\"ok\":true}}"),"ok")) return 32;
  if(pollJsonTopLevelTrue(String("{\"controller\":{\"ok\":true},\"ok\":false}"),"ok")) return 33;
  if(!pollJsonTopLevelTrue(String("{\"controller\":{\"ok\":false},\"ok\":true}"),"ok")) return 34;
  if(pollJsonTopLevelTrue(String("{\"ok\":true,\"ok\":true}"),"ok")) return 35;
  if(pollJsonTopLevelTrue(String("{\"controller\":[{\"ok\":true}]}"),"ok")) return 36;
  if(pollJsonTopLevelTrue(String("{\"message\":\"\\\"ok\\\":true\",\"ok\":false}"),"ok")) return 37;
  if(pollJsonTopLevelTrue(String("{\"ok\":true,}"),"ok")) return 38;
  if(pollJsonTopLevelTrue(String("{\"ok\":true}trailing"),"ok")) return 39;
  if(!pollJsonTopLevelTrue(String(" { \"ok\" : true, \"controller\":{\"ok\":false} } "),"ok")) return 40;
  if(pollJsonTopLevelTrue(String("{\"o\\u006b\":true}"),"ok")) return 41;
  if(pollJsonTopLevelTrue(String("{\"controller\":bad,\"ok\":true}"),"ok")) return 42;
  if(pollJsonTopLevelTrue(String("{\"controller\":{\"x\":1],\"ok\":true}"),"ok")) return 43;
  // Empty / timed-out poll after a previously positive poll must stay OFF.
  insertMode=true; responseTarget="old-target"; responseSignature="";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("")) || !pollIntakeSuspended || insertMode || !activeTarget.empty() || relayOn) return 11;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn || applyRemoteConfigCalls!=0) return 12;

  // Explicit controller denial also clears stale permission.
  insertMode=true; activeTarget="old-target"; responseSignature="valid-signature";
  responseInsert=false; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":false}")) || insertMode || !activeTarget.empty() || relayOn) return 13;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 14;

  // A positive-looking reply with a bad signature cannot restore intake.
  insertMode=true; activeTarget="old-target"; responseSignature="bad-signature";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 15;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 16;

  // A positive-looking reply without a required signature must stay OFF.
  insertMode=true; activeTarget="old-target"; responseSignature="";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 22;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 23;

  // A fresh valid positive poll may restore intake after the inhibit is released.
  insertMode=false; activeTarget=""; responseSignature="valid-signature";
  responseTarget="target-02"; responseInsert=true; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(!acceptPollResponse(String("{\"ok\":true}")) || !insertMode || activeTarget!="target-02") return 17;
  if(relayOn) return 18; // intake remains inhibited while response is processed
  pollIntakeSuspended=false; applyOutputs();
  if(!relayOn || !ledOn || applyRemoteConfigCalls!=1) return 19;

  // A valid negative insert state remains disabled.
  responseInsert=false; responseSignature="valid-signature"; responseTarget="target-03";
  pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(!acceptPollResponse(String("{\"ok\":true}")) || insertMode || activeTarget!="target-03") return 20;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 21;

  // A positive insert response without a target nonce must be rejected.
  insertMode=true; activeTarget="old-target"; responseTarget="";
  responseSignature="valid-signature"; responseInsert=true;
  pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 24;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 25;

  // Defense in depth: a stale positive flag without a target cannot energize output.
  insertMode=true; activeTarget=""; pollIntakeSuspended=false;
  relayOn=true; ledOn=true; applyOutputs();
  if(relayOn || ledOn) return 26;

  // A nested ok:true cannot override an explicit top-level denial.
  insertMode=true; activeTarget="old-target"; responseSignature="valid-signature";
  responseTarget="target-04"; responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("{\"ok\":false,\"controller\":{\"ok\":true}}")) ||
     insertMode || !activeTarget.empty() || relayOn) return 27;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 28;

  std::cout << "poll-response fail-closed cases: 9/9 PASS; strict root JSON cases: 13/13 PASS\n";
  return 0;
}
"""

failed=[]
for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    loop=extract(source,"loop")
    assert loop.index('String r=post("poll")') < loop.index("acceptPollResponse(r)") < loop.index("pollIntakeSuspended=false") < loop.index("applyOutputs();lastPoll=millis()"), board+": poll release ordering changed"
    parser="\n".join(extract(source,name) for name in ("pollJsonSpace","pollJsonHex","pollJsonSkipString","pollJsonSkipComposite","pollJsonSkipPrimitive","pollJsonSkipValue","pollJsonTopLevelTrue"))
    code=("#define TARGET_ESP32\n" if board=="ESP32" else "")+STUBS+parser+extract(source,"acceptPollResponse")+extract(source,"applyOutputs")+MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-response-") as folder:
        cpp=Path(folder)/"test.cpp"; binary=Path(folder)/"test"
        cpp.write_text(code,encoding="utf-8")
        built=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-Wno-unused-parameter",str(cpp),"-o",str(binary)],capture_output=True,text=True,timeout=30)
        if built.returncode:
            print(board,"COMPILE FAIL",built.stderr[-2000:]); failed.append(board); continue
        ran=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        print(board,"PASS" if ran.returncode==0 else "FAIL",ran.stdout.strip(),ran.stderr.strip())
        if ran.returncode: failed.append(board)
if failed: sys.exit("poll-response fail-closed lab failed: "+",".join(failed))
print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
print("PRODUCTION_FINANCIAL_AUTHORIZED=0")
