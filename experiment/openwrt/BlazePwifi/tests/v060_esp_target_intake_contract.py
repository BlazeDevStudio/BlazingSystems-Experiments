#!/usr/bin/env python3
"""PHX-L-VERIFY: execute real ESP applyOutputs() with synthetic GPIO state.

No coin acceptor, paid customer, electrical polarity, or hardware power tested.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def function(text, name):
    m = re.search(r"\bvoid\s+" + re.escape(name) + r"\s*\(\s*\)\s*\{", text)
    assert m, "Missing actual source function " + name
    level = 0
    for i in range(m.end() - 1, len(text)):
        if text[i] == "{":
            level += 1
        elif text[i] == "}":
            level -= 1
            if level == 0:
                return text[m.start():i + 1]
    raise AssertionError("Unterminated actual function " + name)


FIXTURE = r"""
#include <iostream>
#include <string>
#include <cstdint>
using String=std::string;
// HOST-ONLY test seam for historical positives; production has constant-false gate.
bool kCoinAdmissionEnabled=true;
bool controllerEnabled=true,coinEnabled=true,insertMode=true,fsReady=true;
bool pendingReady=false,pollIntakeSuspended=false,ledEnabled=true,relayEnabled=true;
bool runRelayActiveHigh=true,runLedActiveHigh=true;
int runLedPin=14,runRelayPin=5;
uint8_t pendingPulses=0;
String activeTarget="aaaabbbbccccdddd",pendingTarget="";
bool relayLogical=false,ledLogical=false;
int relayWrites=0,ledWrites=0;
void applyOutputs();
void writeLogical(int pin,bool on,bool polarity) {
  // The test verifies the exact real output CALL contract, not electronics.
  (void)polarity;
  if(pin==runRelayPin){relayLogical=on;++relayWrites;}
  if(pin==runLedPin){ledLogical=on;++ledWrites;}
}
void defaults(){
 kCoinAdmissionEnabled=true;
 controllerEnabled=coinEnabled=insertMode=fsReady=true;
 pendingReady=pollIntakeSuspended=false;
 ledEnabled=relayEnabled=true;
 runRelayActiveHigh=runLedActiveHigh=true;
 pendingPulses=0;
 activeTarget="aaaabbbbccccdddd";
 pendingTarget="";
 relayLogical=ledLogical=false;
 relayWrites=ledWrites=0;
}
int fails=0,checks=0;
void verify(const char *name,bool expectedRelay,bool expectedLed){
 applyOutputs();
 ++checks;
 bool ok=relayLogical==expectedRelay && ledLogical==expectedLed &&
         relayWrites==1 && ledWrites==1;
 std::cout<<(ok?"PASS ":"RED ")<<name
          <<" relay="<<relayLogical<<" led="<<ledLogical
          <<" expected="<<expectedRelay<<"/"<<expectedLed<<"\n";
 if(!ok)++fails;
}
int main(){
 defaults();verify("normal selected target accepts",true,true);
 defaults();activeTarget="";verify("missing server-selected target MUST inhibit",false,false);
 defaults();pendingPulses=1;pendingTarget=activeTarget;
 verify("same target unfinished group accepts another pulse",true,true);
 defaults();pendingPulses=1;pendingTarget="ffffeeee00001111";
 verify("selected target changed during unfinished group MUST inhibit",false,false);
 defaults();pendingPulses=20;pendingTarget=activeTarget;
 verify("saturated 20-pulse journal MUST inhibit",false,false);
 defaults();pendingReady=true;verify("pending coin HTTP ACK MUST inhibit",false,false);
 defaults();pollIntakeSuspended=true;verify("blocking poll MUST inhibit",false,false);
 defaults();insertMode=false;verify("closed insert window MUST inhibit",false,false);
 defaults();fsReady=false;verify("flash journal failure MUST inhibit",false,false);
 defaults();coinEnabled=false;verify("admin coin disable MUST inhibit",false,false);
 defaults();controllerEnabled=false;verify("admin controller disable MUST inhibit",false,false);
 defaults();relayEnabled=false;verify("remote relay disable MUST inhibit",false,true);
 defaults();ledEnabled=false;verify("remote led disable MUST inhibit",true,false);
 defaults();kCoinAdmissionEnabled=false;
 verify("Phase A production denial even for valid target",false,false);
 std::cout<<"CHECKS "<<checks<<" FAILED "<<fails<<"\n";
 return fails?18:0;
}
"""
# C++ fixture uses applyOutputs ahead of the test case code which calls it.
prefix,main = FIXTURE.split("int main(){",1)
fail = []
for board,path in BOARDS.items():
    source = path.read_text(encoding="utf-8")
    extracted = function(source,"applyOutputs")
    assert "static constexpr bool kCoinAdmissionEnabled=false;" in source, "Phase A production denial missing"
    assert "bool accepting=" in extracted
    code = prefix + "\n" + extracted + "\nint main(){" + main
    with tempfile.TemporaryDirectory(prefix="blaze-target-relay-lab-") as folder:
        cpp = Path(folder)/"test.cpp"
        exe = Path(folder)/"test"
        cpp.write_text(code,encoding="utf-8")
        compile_ = subprocess.run(
            ["g++","-std=c++17","-Wall","-Wextra","-Werror","-O0",str(cpp),"-o",str(exe)],
            capture_output=True,text=True,timeout=30)
        if compile_.returncode:
            print(board,"HARNESS_COMPILE_ERROR",compile_.stderr[-2500:])
            fail.append(board)
            continue
        run = subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
        print(board,run.stdout.strip())
        if run.returncode:
            print(board,"RED: coin relay accepted non-journalable input; exit",run.returncode)
            fail.append(board)
if fail:
    sys.exit("PHX-VERIFY P0 target-bound output admission safety RED: "+",".join(fail))
print("PHX-VERIFY 14/14 extracted-output host controls per board (13 historical hypothetical + 1 Phase A denial); physical_coin_acceptance_verified=0")
