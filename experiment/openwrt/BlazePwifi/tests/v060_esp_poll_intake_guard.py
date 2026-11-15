#!/usr/bin/env python3
"""PHX-HARDWARE #177: compile and execute the actual ESP loop/poll guards.

This is a host fault-injection lab. It proves source control flow only; it is
not physical relay, coin-acceptor, power-cut, or financial acceptance.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def source_function(source, name):
    match = re.search(r"\b(?:void|bool)\s+" + re.escape(name) + r"\s*\(\s*\)\s*\{", source)
    assert match, f"Missing production function {name}"
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"Unbalanced production function {name}")


STUBS = r"""
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  String(const std::string &value):std::string(value){}
  String(int value):std::string(std::to_string(value)){}
  String(unsigned int value):std::string(std::to_string(value)){}
  bool isEmpty()const{return empty();}
  int indexOf(const char *value)const{
    const auto pos=find(value); return pos==npos?-1:(int)pos;
  }
  bool equalsIgnoreCase(const String &other)const{
    if(size()!=other.size()) return false;
    for(size_t i=0;i<size();i++)
      if(std::tolower((unsigned char)(*this)[i])!=std::tolower((unsigned char)other[i])) return false;
    return true;
  }
};
uint32_t now_ms=1501,lastPoll=0,lastEdge=0,lastSend=0,configuredApSince=0;
int wifiFailures=0,maxWifiRetries=6,runCoinPin=27,runRelayPin=26,runLedPin=2,remoteRevision=0;
uint8_t pendingPulses=0;
uint16_t runDebounceMs=40,runPulseGroupMs=400;
bool insertMode=true,fsReady=true,pendingReady=false,journalRecoveryRequired=false,setupApOn=false;
bool controllerEnabled=true,coinEnabled=true,relayEnabled=true,ledEnabled=true;
bool runCoinActiveLow=true,runRelayActiveHigh=true,runLedActiveHigh=true,lastCoin=false;
bool pollIntakeSuspended=false,relayOn=false,relayDuringPoll=false;
int saves=0,polls=0,coinPosts=0,digitalReads=0;
bool edgeAfterFirstIdleRead=false;
uint32_t pulseFrom=1600,pulseUntil=1680;
String activeTarget="1234567890123456",pendingTarget,pendingNonce,lastSentNonce;
struct Config {
#ifdef TARGET_ESP32
  String ssid="test",pass="pw",key="",id="vendo-01";
#else
  char ssid[16]="test",pass[16]="pw",key[2]="",id[16]="vendo-01";
#endif
} cfg;
#define WL_CONNECTED 3
struct Wifi {
  int status(){return WL_CONNECTED;}
  void disconnect(){}
  void begin(const char*,const char*){}
  void softAPdisconnect(bool){}
} WiFi;
struct Web {void handleClient(){}} web;
struct SerialMock {
  void println(const char*){}
  void println(const String&){}
} Serial;
uint32_t millis(){return now_ms;}
void delay(int value){now_ms+=(uint32_t)value;}
int digitalRead(int){
  digitalReads++;
  if(edgeAfterFirstIdleRead && digitalReads>=2) return 0;
  return pulseFrom<=now_ms && now_ms<pulseUntil?0:1;
}
void startSetupAp(){}
void writeLogical(int pin,bool on,bool){if(pin==runRelayPin) relayOn=on;}
void applyRemoteConfig(const String&){}
bool jsonTrue(const String&,const String&){return false;}
String jsonString(const String&,const String&){return String("");}
int jsonInt(const String&,const String&,int fallback){return fallback;}
String hexDigest(const String&){return String("digest");}
String freshNonce(){return String("abcdefabcdefabcd");}
bool savePending(){saves++;return true;}
void clearPending(){pendingPulses=0;pendingReady=false;}
bool quarantinePending(const String&){return false;}
String post(const String& action,const String& pulses="0",
            const String& target="",const String& nonce=""){
  if(action=="poll"){
    polls++;
    relayDuringPoll=relayOn;
    now_ms+=3500;
    return String("");
  }
  if(action=="coin") coinPosts++;
  return String("");
}
"""

MAIN = r"""
void resetState(){
  now_ms=1501;lastPoll=0;lastEdge=0;lastSend=0;
  wifiFailures=0;pendingPulses=0;pendingReady=false;journalRecoveryRequired=false;
  insertMode=true;lastCoin=false;pollIntakeSuspended=false;
  saves=0;polls=0;coinPosts=0;digitalReads=0;relayDuringPoll=true;
  edgeAfterFirstIdleRead=false;
  pulseFrom=1600;pulseUntil=1680;activeTarget="1234567890123456";
  pendingTarget="";pendingNonce="";
  applyOutputs();
}
int main(){
  resetState();
  now_ms=1600;lastPoll=1600;
  loop();
  const bool control=(pendingPulses==1 && saves==1 && polls==0);

  resetState();
  loop();
  const bool networkGuard=(polls==1 && !relayDuringPoll &&
                           !pollIntakeSuspended && pendingPulses==0);

  resetState();
  pulseFrom=1490;pulseUntil=1570;
  loop();
  const bool activeEdgeSaved=(polls==0 && pendingPulses==1 && saves==1);

  resetState();
  edgeAfterFirstIdleRead=true;
  pulseFrom=9000;pulseUntil=9080;
  loop();
  const bool checkToInhibitEdgeSaved=(polls==0 && pendingPulses==1 &&
                                     saves==1 && !pollIntakeSuspended);

  resetState();
  pendingPulses=1;lastEdge=1450;
  loop();
  const bool settlingGroupDeferred=(polls==0 && pendingPulses==1 && !pendingReady);

  resetState();
  pendingPulses=1;pendingReady=true;pendingNonce="abcdefabcdefabcd";
  pendingTarget="1234567890123456";
  applyOutputs();
  loop();
  const bool owedCoinPrioritized=(polls==0 && coinPosts==1 && !relayOn);

  resetState();
  journalRecoveryRequired=true;
  applyOutputs();
  loop();
  const bool recoveryDenied=(polls==0 && saves==0 && !relayOn);

  std::cout<<"control="<<control
           <<" network_guard="<<networkGuard
           <<" active_edge_saved="<<activeEdgeSaved
           <<" check_to_inhibit_edge_saved="<<checkToInhibitEdgeSaved
           <<" settling_group_deferred="<<settlingGroupDeferred
           <<" owed_coin_prioritized="<<owedCoinPrioritized
           <<" recovery_denied="<<recoveryDenied<<"\n";
  return (control && networkGuard && activeEdgeSaved && checkToInhibitEdgeSaved &&
          settlingGroupDeferred && owedCoinPrioritized && recoveryDenied)?0:19;
}
"""

failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text(encoding="utf-8")
    assert "h.setTimeout(3500)" in sketch, f"{chip}: HTTP timeout contract changed; re-audit"
    names = ["canAttemptCoinPost", "coinLineIdle", "canStartPoll", "applyOutputs",
             "beginPollWindow", "loop"]
    extracted = "\n".join(source_function(sketch, name) for name in names)
    loop = source_function(sketch, "loop")
    assert loop.index('post("poll")') < loop.index("bool raw=digitalRead(runCoinPin)")
    begin = source_function(sketch, "beginPollWindow")
    assert "pollIntakeSuspended=true" in begin and "coinLineIdle()" in begin
    assert "pollIntakeSuspended=false" in begin and "pollIntakeSuspended=false" in loop
    code = ("#define TARGET_ESP32\n" if chip == "ESP32" else "") + STUBS + extracted + MAIN
    with tempfile.TemporaryDirectory(prefix="phx-hw-poll-guard-") as folder:
        cpp = Path(folder) / "test.cpp"
        binary = Path(folder) / "test"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30,
        )
        if built.returncode:
            print(chip, "COMPILE FAIL", built.stderr[-2400:])
            failed.append(chip)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
        print(chip, "PASS" if ran.returncode == 0 else "FAIL", ran.stdout.strip())
        if ran.returncode:
            failed.append(chip)

if failed:
    sys.exit("PHX-HARDWARE #177 poll guard failed: " + ",".join(failed))
print("PHX-HARDWARE #177: actual source loop/output guard PASS 2/2")
print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
print("FINANCIAL_PRODUCTION_AUTHORIZED=0")
