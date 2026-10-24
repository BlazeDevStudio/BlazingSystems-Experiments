#!/usr/bin/env python3
"""PHX-L-VERIFY #177: execute actual sketch loop() + applyOutputs() against a
host-injected synchronous poll timeout. Not physical/electrical QA or a payment test."""
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
    m = re.search(r"\bvoid\s+" + name + r"\s*\(\s*\)\s*\{", source)
    assert m, "Missing original " + name
    level = 0
    for j in range(m.end() - 1, len(source)):
        if source[j] == "{":
            level += 1
        elif source[j] == "}":
            level -= 1
            if level == 0:
                return source[m.start():j + 1]
    raise AssertionError("Unbalanced original " + name)

STUBS = r"""
#include <cstdint>
#include <cstring>
#include <string>
#include <iostream>
struct String:std::string {
 using std::string::string;
 String(const std::string& x):std::string(x){}
 String(int x):std::string(std::to_string(x)){}
 bool isEmpty()const{return empty();}
 int indexOf(const char*x)const{auto i=find(x);return i==npos?-1:(int)i;}
};
uint32_t now_ms=1501,lastPoll=0,lastEdge=0,lastSend=0,configuredApSince=0;
int wifiFailures=0,maxWifiRetries=6,runCoinPin=27,runRelayPin=26,runLedPin=2;
uint8_t pendingPulses=0;
uint16_t runDebounceMs=40,runPulseGroupMs=400;
bool insertMode=true,fsReady=true,pendingReady=false,setupApOn=false;
bool controllerEnabled=true,coinEnabled=true,relayEnabled=true,ledEnabled=true;
bool runCoinActiveLow=true,runRelayActiveHigh=true,runLedActiveHigh=true,lastCoin=false;
bool pollIntakeSuspended=false,relayOn=false,relayDuringPoll=false;
int saves=0,polls=0;
bool failNextSave=false;
uint32_t pulseFrom=1600,pulseUntil=1680;
String activeTarget="1234567890123456",pendingTarget,pendingNonce;
struct Config {
#ifdef TARGET_ESP32
 String ssid="test",pass="pw";
#else
 char ssid[16]="test",pass[16]="pw";
#endif
} cfg;
#define WL_CONNECTED 3
struct Wifi {int status(){return WL_CONNECTED;}void disconnect(){}
 void begin(const char*,const char*){}void softAPdisconnect(bool){}} WiFi;
struct Web {void handleClient(){}} web;
struct SerialMock {void println(const char*){}} Serial;
uint32_t millis(){return now_ms;}
void delay(int n){now_ms+=(uint32_t)n;}
int digitalRead(int){return pulseFrom<=now_ms && now_ms<pulseUntil?0:1;}
void startSetupAp(){}
void writeLogical(int pin,bool on,bool){if(pin==runRelayPin) relayOn=on;}
void applyRemoteConfig(const String&){}
bool jsonTrue(const String&s,const char*){return !s.empty();}
String jsonString(const String&s,const char*){return s.empty()?String(""):String("1234567890123456");}
String freshNonce(){return String("abcdefabcdefabcd");}
bool savePending(){saves++;return !failNextSave;}
bool clearPending(bool){pendingPulses=0;pendingReady=false;return true;}
String post(const String& action,const String& pulse="0",const String& target="",const String& nonce=""){
 if(action=="poll") {polls++;relayDuringPoll=relayOn;now_ms+=3500;return String("");}
 return String("");
}
"""
MAIN = r"""
int main(){
 now_ms=1600;lastPoll=1600;applyOutputs();loop();
 bool control=(pendingPulses==1 && saves==1 && polls==0);
 std::cout<<"control_logged_one="<<control<<" ";
 now_ms=1501;lastPoll=0;lastEdge=0;lastSend=0;
 insertMode=true;pendingReady=false;pendingPulses=0;lastCoin=false;saves=0;
 activeTarget="1234567890123456";applyOutputs();
 loop();
 std::cout<<"polls="<<polls<<" relay_during_poll="<<relayDuringPoll
  <<" unrecorded_pulse="<<(pendingPulses==0&&saves==0)<<"\n";
 bool blockedPollGuard=(control&&polls==1&&!relayDuringPoll);
 // A pulse began before scheduled polling: network IO must be deferred
 // until that active pulse has been sampled into the persistent journal.
 pulseFrom=1490;pulseUntil=1570;
 now_ms=1501;lastPoll=0;lastEdge=0;lastSend=0;
 insertMode=true;pendingReady=false;pendingPulses=0;lastCoin=false;saves=0;polls=0;
 activeTarget="1234567890123456";applyOutputs();loop();
 bool activeEdgeRecorded=(polls==0&&pendingPulses==1&&saves==1);
 std::cout<<" active_edge_saved="<<activeEdgeRecorded;
 // A pulse train with an active journal group must settle before HTTP poll
 // can suspend the relay (avoid cutting a multi-pulse coin sequence).
 pulseFrom=4000;pulseUntil=4080;
 now_ms=1501;lastPoll=0;lastEdge=1450;lastSend=0;
 pendingPulses=1;pendingReady=false;lastCoin=false;saves=0;polls=0;
 insertMode=true;applyOutputs();loop();
 bool pendingGroupDeferred=(polls==0&&pendingPulses==1);
 std::cout<<" pending_group_deferred="<<pendingGroupDeferred<<"\n";
 // The 20th detected pulse consumes the final journal slot.
 // Existing applyOutputs predicate forbids more intake, but the real loop
 // must actually call applyOutputs after changing pendingPulses.
 now_ms=5200;lastPoll=5200;lastEdge=4000;lastSend=5200;
 pulseFrom=5200;pulseUntil=5280;
 pendingPulses=19;pendingTarget=activeTarget;
 pendingReady=false;fsReady=true;pollIntakeSuspended=false;
 lastCoin=false;saves=0;polls=0;failNextSave=false;
 applyOutputs();bool capInitiallyOn=relayOn;
 loop();
 bool capInhibited=capInitiallyOn&&pendingPulses==20&&saves==1&&!relayOn;
 std::cout<<" cap_last_pulse_relay_off="<<capInhibited
          <<" pulse_count="<<(int)pendingPulses<<"\n";
 // A forced flash write error makes the journal unusable. Coin relay must
 // drop immediately in the SAME loop(), before another poll or retry.
 now_ms=6200;lastPoll=6200;lastEdge=4000;lastSend=6200;
 pulseFrom=6200;pulseUntil=6280;
 pendingPulses=0;pendingTarget="";pendingNonce="";
 pendingReady=false;fsReady=true;pollIntakeSuspended=false;
 lastCoin=false;saves=0;polls=0;failNextSave=true;
 applyOutputs();bool beforeFailureOn=relayOn;
 loop();
 bool flashFailInhibited=beforeFailureOn&&pendingPulses==1&&saves==1&&
                         !fsReady&&pendingReady&&!relayOn;
 std::cout<<" flash_save_failure_relay_off="<<flashFailInhibited
          <<" fs_ready="<<fsReady<<" pending_ready="<<pendingReady<<"\n";
 return (blockedPollGuard&&activeEdgeRecorded&&pendingGroupDeferred&&
         capInhibited&&flashFailInhibited)?0:19;
}
"""

failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text()
    assert "h.setTimeout(3500)" in sketch, "HTTP timeout contract changed: re-audit"
    loop = source_function(sketch, "loop")
    outputs = source_function(sketch, "applyOutputs")
    assert loop.index('post("poll")') < loop.index("bool raw=digitalRead(runCoinPin)"), "poll order changed: re-audit"
    code = ("#define TARGET_ESP32\n" if chip == "ESP32" else "") + STUBS + outputs + loop + MAIN
    with tempfile.TemporaryDirectory(prefix="blaze-esp-host-lab-") as folder:
        cpp = Path(folder) / "test.cpp"
        binary = Path(folder) / "test"
        cpp.write_text(code)
        built = subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra",
                                "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
                               capture_output=True, text=True, timeout=30)
        if built.returncode:
            print(chip, "COMPILE FAIL", built.stderr[-1800:])
            failed.append(chip)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
        print(chip, "PASS" if ran.returncode == 0 else "FAIL", ran.stdout.strip())
        if ran.returncode:
            failed.append(chip)
if failed:
    sys.exit("P0 #177: real loop output transition safety RED: " + ",".join(failed))
print("PHX-177: source loop/output guard PASS 2/2; NOT real hardware or physical acceptance")
