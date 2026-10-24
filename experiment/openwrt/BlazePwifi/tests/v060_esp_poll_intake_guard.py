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
int digitalRead(int){return 1600<=now_ms && now_ms<1680?0:1;}
void startSetupAp(){}
void writeLogical(int pin,bool on,bool){if(pin==runRelayPin) relayOn=on;}
void applyRemoteConfig(const String&){}
bool jsonTrue(const String&s,const char*){return !s.empty();}
String jsonString(const String&s,const char*){return s.empty()?String(""):String("1234567890123456");}
String freshNonce(){return String("abcdefabcdefabcd");}
bool savePending(){saves++;return true;}
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
 return (control&&polls==1&&!relayDuringPoll)?0:19;
}
"""

failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text()
    assert "h.setTimeout(3500)" in sketch, "HTTP timeout contract changed: re-audit"
    loop = source_function(sketch, "loop")
    outputs = source_function(sketch, "applyOutputs")
    assert loop.index('post("poll")') < loop.index("digitalRead(runCoinPin)"), "poll order changed: re-audit"
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
    sys.exit("P0 #177: energized coin acceptor during blocking poll: " + ",".join(failed))
print("PHX-177: source loop/output guard PASS 2/2; NOT real hardware or physical acceptance")
