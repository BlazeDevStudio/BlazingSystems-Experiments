#!/usr/bin/env python3
"""PHX-L-VERIFY: compile actual ESP firmware reconfiguration functions with GPIO mocks.

Tests ordering and fail-closed behavior only. NOT physical relay acceptance.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

def extract(source, name):
    m = re.search(r"\bvoid\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", source)
    assert m, "missing actual firmware function " + name
    depth = 0
    for i in range(m.end() - 1, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return source[m.start():i + 1]
    raise AssertionError("unbalanced actual function " + name)

STUBS = r"""
#include <cstdint>
#include <iostream>
#include <map>
#include <regex>
#include <string>
#include <vector>
using String = std::string;
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT_PULLUP 2
struct Op {char type;int pin;int value;};
std::vector<Op> trace;
std::map<int,int> levels;
void digitalWrite(int pin,int value){trace.push_back({'W',pin,value});levels[pin]=value;}
void pinMode(int pin,int mode){trace.push_back({'M',pin,mode});}
int constrain(int n,int lo,int hi){return n<lo?lo:(n>hi?hi:n);}
int jsonInt(const String& body,const char* key,int fallback){
 std::regex rx(String("\\\"")+key+"\\\"\\s*:\\s*(-?[0-9]+)");
 std::smatch m;
 return std::regex_search(body,m,rx)?std::stoi(m[1].str()):fallback;
}
struct Config {
 int coinPin=4,relayPin=5,insertLedPin=14;
 bool coinActiveLow=true,relayActiveHigh=true,ledActiveHigh=true;
 int coinDebounceMs=40,pulseGroupMs=400;
} cfg;
int runCoinPin=4,runRelayPin=5,runLedPin=14,remoteRevision=1,maxWifiRetries=6;
bool runCoinActiveLow=true,runRelayActiveHigh=true,runLedActiveHigh=true;
bool controllerEnabled=true,coinEnabled=true,relayEnabled=true,ledEnabled=true;
bool insertMode=true,fsReady=true,pendingReady=false,pollIntakeSuspended=false;
uint8_t pendingPulses=0;
uint16_t runDebounceMs=40,runPulseGroupMs=400;
String activeTarget="abcdef0123456789",pendingTarget="";
void writeLogical(int pin,bool on,bool activeHigh);
void configureRuntimePins(int coinPin,int relayPin,int ledPin);
void applyOutputs();
void applyRemoteConfig(const String& r);
"""
MAIN = r"""
int fails=0,checks=0;
void reset(){
 cfg=Config{};
 runCoinPin=4;runRelayPin=5;runLedPin=14;remoteRevision=1;
 runCoinActiveLow=true;runRelayActiveHigh=true;runLedActiveHigh=true;
 controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=fsReady=true;
 pendingReady=pollIntakeSuspended=false;pendingPulses=0;
 activeTarget="abcdef0123456789";pendingTarget="";
 levels.clear();trace.clear();
 digitalWrite(5,HIGH);digitalWrite(14,HIGH);trace.clear();
}
int first(char kind,int pin=-1,int value=-1){
 for(size_t i=0;i<trace.size();++i)
  if(trace[i].type==kind&&(pin<0||trace[i].pin==pin)&&
     (value<0||trace[i].value==value))return (int)i;
 return -1;
}
void check(const char* name,bool ok){
 ++checks;if(!ok)++fails;
 std::cout<<(ok?"PASS ":"RED ")<<name<<"\n";
}
int main(){
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"relay_active_high\":0,\"led_active_high\":1,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 check("relay_polarity_change_rejected_old_off",
  levels[5]==LOW&&runRelayActiveHigh&&remoteRevision==1&&
  !controllerEnabled&&!coinEnabled&&!insertMode&&first('M')<0);
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"relay_active_high\":1,\"led_active_high\":0,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 check("led_polarity_change_rejected_old_off",
  levels[14]==LOW&&runLedActiveHigh&&remoteRevision==1&&
  !controllerEnabled&&!coinEnabled&&!insertMode&&first('M')<0);
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"relay_active_high\":1,\"led_active_high\":1,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 int mode=first('M');
 check("same_pin_old_outputs_off_before_mode",
  mode>=0&&first('W',5,LOW)>=0&&first('W',14,LOW)>=0&&
  first('W',5,LOW)<mode&&first('W',14,LOW)<mode&&
  levels[5]==LOW&&levels[14]==LOW&&remoteRevision==2);
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"relay_active_high\":1,\"led_active_high\":1,\"coin_pin\":4,\"relay_pin\":12,\"led_pin\":13}");
 mode=first('M');
 check("live_pin_move_rejected_until_hardware_reprovision",
  first('M')<0&&levels[5]==LOW&&levels[14]==LOW&&
  runRelayPin==5&&runLedPin==14&&remoteRevision==1&&
  !controllerEnabled&&!coinEnabled&&!insertMode);
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":1,\"coin_enabled\":1,\"relay_active_high\":1,\"led_active_high\":1,\"coin_pin\":5,\"relay_pin\":5,\"led_pin\":14}");
 check("coin_relay_alias_denied_before_pin_mode",
  first('M')<0&&levels[5]==LOW&&remoteRevision==1&&
  !controllerEnabled&&!coinEnabled&&!insertMode);
 reset();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":1,\"coin_enabled\":1,\"relay_active_high\":1,\"led_active_high\":1,\"coin_pin\":4,\"relay_pin\":14,\"led_pin\":14}");
 check("relay_led_alias_denied_before_pin_mode",
  first('M')<0&&levels[5]==LOW&&levels[14]==LOW&&remoteRevision==1&&
  !controllerEnabled&&!coinEnabled&&!insertMode);
 reset();
 remoteRevision=3;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig("{\"config_revision\":2,\"enabled\":1,\"coin_enabled\":1,\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 check("stale_revision_cannot_reenable_coin",
  remoteRevision==3&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')<0);
 reset();
 remoteRevision=3;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig("{\"config_revision\":0,\"enabled\":1,\"coin_enabled\":1,\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 check("zero_revision_cannot_reenable_coin",
  remoteRevision==3&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')<0);
 reset();
 remoteRevision=3;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig("{\"config_revision\":4,\"enabled\":0,\"coin_enabled\":0,\"relay_enabled\":0,\"led_enabled\":0,\"coin_pin\":4,\"relay_pin\":5,\"led_pin\":14}");
 check("higher_revision_disabled_config_accepted",
  remoteRevision==4&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')>=0);

 // Cold-boot admission: revision 0 is untrusted, and missing/nonpositive
 // revisions must not bootstrap a previously disabled coin acceptor.
 reset();
 remoteRevision=0;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"enabled":1,"coin_enabled":1,"relay_enabled":1,"led_enabled":1,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("bootstrap_missing_revision_denied",
  remoteRevision==0&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')<0);
 reset();
 remoteRevision=0;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"config_revision":0,"enabled":1,"coin_enabled":1,"relay_enabled":1,"led_enabled":1,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("bootstrap_zero_revision_denied",
  remoteRevision==0&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')<0);
 reset();
 remoteRevision=0;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"config_revision":-1,"enabled":1,"coin_enabled":1,"relay_enabled":1,"led_enabled":1,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("bootstrap_negative_revision_denied",
  remoteRevision==0&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')<0);
 reset();
 remoteRevision=0;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"config_revision":1,"enabled":0,"coin_enabled":0,"relay_enabled":0,"led_enabled":0,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("bootstrap_positive_disabled_config_accepted",
  remoteRevision==1&&!controllerEnabled&&!coinEnabled&&!insertMode&&levels[5]==LOW&&first('M')>=0);

 // A positive integer alone does not authenticate an enabling config response.
 // This is an untrusted response-body test, not a forged network packet.
 reset();
 remoteRevision=4;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"config_revision":5,"enabled":1,"coin_enabled":1,"relay_enabled":1,"led_enabled":1,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("untrusted_positive_revision_cannot_enable_coin",
  remoteRevision==4&&!controllerEnabled&&!coinEnabled&&!insertMode&&
  levels[5]==LOW&&first('M')<0);

 // Actual firmware declares remoteRevision=0 on boot, with no protected
 // persistent highwater. Model power-cycle by resetting RAM, retaining only
 // the knowledge that a prior revision 10 disabled intake.
 reset();
 remoteRevision=10;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 reset(); // simulated cold reboot; the sketch initializes remoteRevision=0
 remoteRevision=0;controllerEnabled=coinEnabled=relayEnabled=ledEnabled=insertMode=false;
 digitalWrite(5,LOW);digitalWrite(14,LOW);trace.clear();
 applyRemoteConfig(R"({"config_revision":2,"enabled":1,"coin_enabled":1,"relay_enabled":1,"led_enabled":1,"coin_pin":4,"relay_pin":5,"led_pin":14})");
 check("cold_reboot_older_positive_revision_cannot_enable_coin",
  remoteRevision==0&&!controllerEnabled&&!coinEnabled&&!insertMode&&
  levels[5]==LOW&&first('M')<0);

 std::cout<<"CHECKS "<<checks<<" FAILED "<<fails<<" physical_verified=0\n";
 return fails?18:0;
}
"""
failed=[]
for board, path in SOURCES.items():
    src=path.read_text(encoding="utf-8")
    bodies="\n".join(extract(src,name) for name in
                     ("writeLogical","configureRuntimePins","applyOutputs","applyRemoteConfig"))
    with tempfile.TemporaryDirectory(prefix="phx-relay-rebind-") as folder:
        cpp=Path(folder)/"test.cpp"
        exe=Path(folder)/"test"
        cpp.write_text(STUBS+bodies+MAIN,encoding="utf-8")
        build=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror",
                              "-pedantic",str(cpp),"-o",str(exe)],
                             capture_output=True,text=True,timeout=30)
        if build.returncode:
            print(board,"HARNESS_COMPILE_ERROR",build.stderr[-2400:])
            failed.append(board+":compile")
            continue
        run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
        print(board,run.stdout.strip())
        if run.returncode:
            failed.append(board+":contract")
if failed:
    sys.exit("PHX-L-VERIFY source-linked GPIO rebind RED: "+",".join(failed))
print("PHX-L-VERIFY real firmware function host reconfiguration PASS both boards; physical_verified=0")
