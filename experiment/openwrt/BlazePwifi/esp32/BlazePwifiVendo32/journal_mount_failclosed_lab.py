#!/usr/bin/env python3
"""PHX-HARDWARE journal mount acceptance denial: exact-source C++17 host lab.

Extracts the REAL initPendingStore() and applyOutputs() function bodies from
ESP32/ESP8266 sketches. A fake LittleFS tests mount failure and acceptance
gating. Does not initialize, flash, or power cycle any physical device.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = [
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
]
CPP = r'''
#include <iostream>
#include <cstdint>
#include <string>
struct FakeLittleFS {
  bool mountOk=false;
  int beginCalls=0, formatCalls=0;
  bool formatOnFailure=false;
  bool faultMarkerExists=false;
  bool exists(const char *path) const { (void)path; return faultMarkerExists; }
  bool begin(bool formatOnFail=false) {
    ++beginCalls;
    formatOnFailure=formatOnFail;
    return mountOk;
  }
  bool format() {++formatCalls;return true;}
} LittleFS;
struct FakeSerial {void println(const char*){}} Serial;
// This lab isolates LittleFS mount behavior; the dedicated dual-store lab tests the real backup reader.
bool pollFaultBackupPresentOrCorrupt(){ return false; }
bool fsReady=false;
bool pendingReady=false;
bool journalRecoveryRequired=false;
bool pollIntakeSuspended=false, pinConfigSafe=true;
bool outputPolarityKnown=true;
// The mount lab tests persistence admission, not asynchronous ISR delivery.
// Keep the new applyOutputs() edge-snapshot dependency idle in this fixture.
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
std::string activeTarget="target-01";
bool insertMode=true,controllerEnabled=true,coinEnabled=true;
bool relayEnabled=true,ledEnabled=true;
bool runRelayActiveHigh=true,runLedActiveHigh=true;
int runRelayPin=5,runLedPin=2;
bool relayOn=false,ledOn=false;
int loadCalls=0;
void loadPending(){++loadCalls;}
@@POLL_PULSE_LATCH@@
void writeLogical(int pin,bool enable,bool){
  if(pin==runRelayPin) relayOn=enable;
  if(pin==runLedPin) ledOn=enable;
}
@@INIT_FUNCTION@@
@@OUTPUTS_FUNCTION@@
int main(){
  for(int scenario=0;scenario<8;++scenario){
    LittleFS=FakeLittleFS{};
    LittleFS.faultMarkerExists=(scenario==7);
    fsReady=false;pendingReady=false;journalRecoveryRequired=false;
    coinEdgeSequence=0;lastHandledCoinEdgeSequence=0;
    activeTarget="target-01";
    insertMode=true;controllerEnabled=true;coinEnabled=true;
    relayEnabled=true;ledEnabled=true;
    relayOn=false;ledOn=false;loadCalls=0;
    LittleFS.mountOk=scenario!=0;
    if(scenario==2)pendingReady=true;
    if(scenario==3)coinEnabled=false;
    if(scenario==4)controllerEnabled=false;
    if(scenario==5)insertMode=false;
    if(scenario==6)journalRecoveryRequired=true;
    initPendingStore();
    applyOutputs();
    const bool expectedRelay=(scenario==1);
    if(fsReady!=LittleFS.mountOk ||
       LittleFS.beginCalls!=1 ||
       LittleFS.formatCalls!=0 ||
       LittleFS.formatOnFailure ||
       loadCalls!=(LittleFS.mountOk?1:0) ||
       journalRecoveryRequired!=(scenario==0 || scenario==6 || scenario==7) ||
       insertMode!=(scenario!=0 && scenario!=5 && scenario!=7) ||
       ((scenario==0 || scenario==7) && !activeTarget.empty()) ||
       relayOn!=expectedRelay ||
       ledOn!=expectedRelay) {
      std::cerr<<"MOUNT_SOURCE_LAB_FAIL scenario="<<scenario
               <<" mount="<<LittleFS.mountOk
               <<" fsReady="<<fsReady
               <<" loadCalls="<<loadCalls
               <<" formatCalls="<<LittleFS.formatCalls
               <<" formatOnFailure="<<LittleFS.formatOnFailure
               <<" relayOn="<<relayOn<<"\n";
      return 1;
    }
  }
  std::cout<<"MOUNT_SOURCE_LAB_PASS 8/8 source-extracted scenarios, no physical tests\n";
  return 0;
}
'''

def extract(src: str, token: str) -> str:
    start = src.find(token)
    if start < 0:
        raise RuntimeError(f"Missing firmware function {token}")
    depth = 0
    brace = src.find("{", start)
    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[start:i+1]
    raise RuntimeError(f"Unclosed firmware function {token}")


def verify_lexical_extractor_regression():
    cases = (
        ("ordinary string", '  const char *value = "}";'),
        ("C++ raw string", '  const char *value = R"tag({ } )tag";'),
        ("line comment", "  // }"),
        ("block comment", "  /* } { */"),
    )
    for label, statement in cases:
        fixture = (
            "bool target(){\n"
            + statement
            + "\n  return true;\n}\nbool after(){ return false; }\n"
        )
        extracted = extract(fixture, "bool target(){")
        if "return true;" not in extracted or "bool after()" in extracted:
            raise SystemExit(
                f"JOURNAL_MOUNT_EXTRACTOR_FAIL: {label} brace truncated target()"
            )
    print("JOURNAL_MOUNT_LEXICAL_EXTRACTOR_PASS 4/4")


verify_lexical_extractor_regression()

for board, path in BOARDS:
    real = path.read_text(encoding="utf-8")
    setup = extract(real, "void setup(){")
    if "initPendingStore();" not in setup:
        raise SystemExit(f"{board}: setup does not call guarded journal mount")
    if "LittleFS.format()" in real or "LittleFS.begin(true)" in real:
        raise SystemExit(f"{board}: dangerous automatic journal formatting remains")
    code = CPP.replace("@@POLL_PULSE_LATCH@@", extract(real, "void loadPollPulseFaultLatch(){"))
    code = code.replace("@@INIT_FUNCTION@@", extract(real, "void initPendingStore(){"))
    code = code.replace("@@OUTPUTS_FUNCTION@@", extract(real, "void applyOutputs(){"))
    with tempfile.TemporaryDirectory(prefix="phx-hw-mount-") as tmp:
        source = Path(tmp) / "mount.cpp"
        executable = Path(tmp) / "mount"
        source.write_text(code, encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(source), "-o", str(executable)], check=True)
        subprocess.run([str(executable)], check=True)
    print(f"{board}: real mount/output functions compiled and exercised")
print("PHX-HARDWARE: 16/16 fake-LittleFS mount/relay scenarios PASS; actual devices NOT TESTED")
