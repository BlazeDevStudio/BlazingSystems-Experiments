#!/usr/bin/env python3
"""PHX-HARDWARE exact-source coin pulse, bounded-batch overflow, target-drift, post-finalization edge and failed-journal safety lab.

Compiles production coinLineIdle(), canStartPoll(), applyOutputs(),
coinLineQuietAfterInhibit(), beginPollWindow(), latchPollPulseFault(), and
sampleCoinPulseEdge() from both ESP sketches. Only the two persistence backends
are fault-injected. The failed-save path checks all four dual-store outcomes,
the unresolved pulse identity, and logical relay/LED OFF before either store is
called. The companion dual-store lab separately extracts the real persistence
helpers. Host C++ uses fake GPIO/time/storage only; no physical acceptance is
claimed.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

from firmware_lab_source import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)

CPP = r'''#include <cstdint>
#include <iostream>
#include <string>
using String=std::string;
static uint32_t fakeNow=0;
static uint16_t runDebounceMs=40;
static uint32_t lastEdge=0;
static uint32_t pulseStart=0,pulseEnd=0;
static bool pulseEnabled=false;
static bool fsReady=true,journalRecoveryRequired=false,pendingReady=false;
static bool outputPolarityKnown=true;
static bool insertMode=true,lastCoin=false;
static bool runCoinActiveLow=true,pollIntakeSuspended=false;
static bool pinConfigSafe=true,controllerEnabled=true,coinEnabled=true;
static bool ledEnabled=true,relayEnabled=true;
static bool runRelayActiveHigh=true,runLedActiveHigh=true;
static int runCoinPin=4,runRelayPin=5,runLedPin=2;
static uint8_t pendingPulses=0;
static String pendingNonce,pendingTarget,activeTarget="target-01";
static bool relayOn=true,ledOn=true;
static unsigned saveCalls=0,nonceCalls=0;
static bool saveResult=true;
static constexpr int LOW=0,HIGH=1;
struct FakeSerial {
  std::string messages;
  void println(const char *message){
    if(!messages.empty()) messages+="\n";
    messages+=message?message:"";
  }
};
static FakeSerial Serial;
uint32_t millis(){return fakeNow;}
void delay(uint32_t ms){fakeNow+=ms;}
static bool pulseActive(){
  return pulseEnabled &&
         static_cast<uint32_t>(fakeNow-pulseStart) <
         static_cast<uint32_t>(pulseEnd-pulseStart);
}
int digitalRead(int){
  const bool active=pulseActive();
  if(runCoinActiveLow) return active?LOW:HIGH;
  return active?HIGH:LOW;
}
void writeLogical(int pin,bool on,bool){
  if(pin==runRelayPin) relayOn=on;
  if(pin==runLedPin) ledOn=on;
}
String freshNonce(){++nonceCalls;return "nonce-"+std::to_string(nonceCalls);}
bool savePending(){++saveCalls;return saveResult;}
static unsigned backupCalls=0,markerCalls=0;
static uint32_t backupEdges=0,markerEdges=0;
static bool backupResult=true,markerResult=true;
static bool backupSawFsReady=false,markerSawFsReady=false;
static bool backupSawRelayOff=false,backupSawLedOff=false;
static bool markerSawRelayOff=false,markerSawLedOff=false;
bool writePollFaultBackup(uint32_t edges){
  ++backupCalls;backupEdges=edges;backupSawFsReady=fsReady;
  backupSawRelayOff=!relayOn;backupSawLedOff=!ledOn;
  return backupResult;
}
bool writePollPulseFaultMarker(uint32_t edges){
  ++markerCalls;markerEdges=edges;markerSawFsReady=fsReady;
  markerSawRelayOff=!relayOn;markerSawLedOff=!ledOn;
  return markerResult;
}
@@FUNCTIONS@@

static void resetState(uint32_t now=0,bool activeLow=true){
  fakeNow=now;runDebounceMs=40;lastEdge=0;
  pulseStart=0;pulseEnd=0;pulseEnabled=false;
  fsReady=true;journalRecoveryRequired=false;pendingReady=false;outputPolarityKnown=true;
  insertMode=true;lastCoin=false;runCoinActiveLow=activeLow;
  pollIntakeSuspended=false;pinConfigSafe=true;controllerEnabled=true;coinEnabled=true;
  ledEnabled=true;relayEnabled=true;runRelayActiveHigh=true;runLedActiveHigh=true;
  pendingPulses=0;pendingNonce.clear();pendingTarget.clear();activeTarget="target-01";
  relayOn=true;ledOn=true;saveCalls=0;nonceCalls=0;saveResult=true;
  backupCalls=0;markerCalls=0;backupEdges=0;markerEdges=0;
  backupResult=true;markerResult=true;
  backupSawFsReady=false;markerSawFsReady=false;
  backupSawRelayOff=false;backupSawLedOff=false;
  markerSawRelayOff=false;markerSawLedOff=false;
  Serial.messages.clear();
}
static bool fail(const char*name,const char*detail){
  std::cerr<<"FAIL "<<name<<" "<<detail<<"\n";
  return false;
}
static bool runDrainCapture(const char*name,uint32_t startAt,uint32_t pulseAt,
                            uint32_t pulseUntil,uint32_t priorEdge,
                            uint16_t debounce,bool activeLow){
  resetState(startAt,activeLow);
  runDebounceMs=debounce;lastEdge=priorEdge;
  pulseEnabled=true;pulseStart=pulseAt;pulseEnd=pulseUntil;
  if(beginPollWindow()) return fail(name,"poll unexpectedly started");
  // This helper-only case has no ISR edge; model the loop releasing the
  // temporary inhibit only after confirming the edge sequence is unchanged.
  if(pollIntakeSuspended){ pollIntakeSuspended=false; applyOutputs(); }
  if(pollIntakeSuspended || !relayOn || !ledOn)
    return fail(name,"no-edge abort did not release for normal sampling");
  const int raw=digitalRead(runCoinPin);
  const bool active=runCoinActiveLow?(raw==LOW):(raw==HIGH);
  if(!active) return fail(name,"drain abort did not leave an active pulse sample");
  sampleCoinPulseEdge(active);
  if(pendingPulses!=1 || saveCalls!=1 || nonceCalls!=1 ||
     pendingNonce!="nonce-1" || pendingTarget!=activeTarget || lastEdge!=fakeNow)
    return fail(name,"first post-abort sample was not durably queued");
  sampleCoinPulseEdge(active);
  fakeNow+=static_cast<uint32_t>(runDebounceMs)+1U;
  sampleCoinPulseEdge(active);
  if(pendingPulses!=1 || saveCalls!=1)
    return fail(name,"sustained high level was counted as another pulse");
  sampleCoinPulseEdge(false);
  fakeNow+=static_cast<uint32_t>(runDebounceMs)+1U;
  sampleCoinPulseEdge(true);
  if(pendingPulses!=2 || saveCalls!=2 || nonceCalls!=1 ||
     pendingNonce!="nonce-1" || pendingTarget!=activeTarget)
    return fail(name,"released second edge did not reuse the pending event identity");
  return true;
}
static bool runNoPulseControl(){
  resetState();
  if(!beginPollWindow()) return fail("no-pulse-control","quiet poll window was rejected");
  if(!pollIntakeSuspended || relayOn || ledOn || fakeNow!=250U)
    return fail("no-pulse-control","poll admission did not retain output inhibit");
  return true;
}
static bool runSaveFailureCase(const char*name,bool backupOk,bool markerOk){
  resetState(100U);
  saveResult=false;
  backupResult=backupOk;
  markerResult=markerOk;
  sampleCoinPulseEdge(true);
  if(pendingPulses!=1 || saveCalls!=1 || fsReady || !pendingReady)
    return fail(name,"failed durable write did not disable filesystem/intake");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=1 || markerEdges!=1)
    return fail(name,"fault latch did not attempt both stores with the unresolved pulse count");
  if(!backupSawFsReady || !markerSawFsReady)
    return fail(name,"fault latch attempted persistence after LittleFS was marked unavailable");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail(name,"storage attempt occurred before outputs were logically OFF");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail(name,"failed journal write did not retain the deny latch and output inhibit");
  if(!backupOk && !markerOk &&
     (Serial.messages.find("both poll-pulse fault stores failed")==std::string::npos ||
      Serial.messages.find("reboot durability is NOT established")==std::string::npos))
    return fail(name,"dual-store failure was not classified as current-boot-only");
  sampleCoinPulseEdge(false);
  fakeNow=200U;
  sampleCoinPulseEdge(true);
  if(saveCalls!=1 || pendingPulses!=1 || backupCalls!=1 || markerCalls!=1)
    return fail(name,"another pulse or persistence retry was accepted after failed journal write");
  return true;
}
static bool runSaveFailure(){
  if(!runSaveFailureCase("both-stores-pass",true,true)) return false;
  if(!runSaveFailureCase("nvs-only",true,false)) return false;
  if(!runSaveFailureCase("littlefs-only",false,true)) return false;
  if(!runSaveFailureCase("both-stores-fail-current-boot-only",false,false)) return false;
  return true;
}
static bool runDeniedGates(){
  for(int scenario=0;scenario<10;++scenario){
    if(scenario==5 || scenario==6) continue; // explicit fault cases below
    resetState(141U);
    lastEdge=100U;
    bool active=true;
    switch(scenario){
      case 0:insertMode=false;break;
      case 1:fsReady=false;break;
      case 2:journalRecoveryRequired=true;break;
      case 3:pendingReady=true;active=false;break; // idle after finalization remains a no-op
      case 4:activeTarget.clear();break;
      case 7:lastCoin=true;break;
      case 8:active=false;break;
      case 9:fakeNow=140U;break; // exactly the configured debounce boundary
    }
    sampleCoinPulseEdge(active);
    if(saveCalls!=0 || pendingPulses!=0){
      std::cerr<<"FAIL deny-case-"<<scenario<<" saves="<<saveCalls
               <<" pulses="<<(unsigned)pendingPulses<<"\n";
      return false;
    }
  }
  return true;
}
static bool runPulseLimitBoundary(){
  resetState(141U);
  lastEdge=100U;
  pendingPulses=19U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  sampleCoinPulseEdge(true);
  if(pendingPulses!=20U || saveCalls!=1 || nonceCalls!=0 ||
     pendingNonce!="nonce-existing" || pendingTarget!="target-01")
    return fail("pulse-limit-20","supported twentieth pulse was not durably queued with its existing identity");
  if(journalRecoveryRequired || pendingReady || !relayOn || !ledOn ||
     backupCalls!=0 || markerCalls!=0)
    return fail("pulse-limit-20","valid twentieth pulse was incorrectly faulted or inhibited");
  return true;
}
static bool runUnrepresentablePulseFault(const char*name,uint8_t existing,
                                         const String&storedTarget){
  resetState(141U);
  lastEdge=100U;
  pendingPulses=existing;
  pendingNonce="nonce-existing";
  pendingTarget=storedTarget;
  sampleCoinPulseEdge(true);
  const uint32_t unresolvedEdges=(uint32_t)existing+1U;
  if(saveCalls!=0 || pendingPulses!=existing ||
     pendingNonce!="nonce-existing" || pendingTarget!=storedTarget || nonceCalls!=0)
    return fail(name,"unrepresentable pulse mutated or appended to the existing pending identity");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail(name,"overflow/target drift did not latch deny and force outputs OFF");
  if(backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=unresolvedEdges || markerEdges!=unresolvedEdges)
    return fail(name,"fault latch did not persist the complete unresolved edge count");
  if(!backupSawRelayOff || !backupSawLedOff ||
     !markerSawRelayOff || !markerSawLedOff)
    return fail(name,"fault persistence began before output inhibition");
  sampleCoinPulseEdge(false);
  fakeNow=200U;
  sampleCoinPulseEdge(true);
  if(saveCalls!=0 || pendingPulses!=existing ||
     backupCalls!=1 || markerCalls!=1)
    return fail(name,"later pulse retried or mutated the unresolved batch");
  return true;
}
static bool runUnrepresentablePulseCases(){
  if(!runUnrepresentablePulseFault("pulse-overflow-21",20U,"target-01")) return false;
  if(!runUnrepresentablePulseFault("pending-target-changed",1U,"other-target")) return false;
  return true;
}
static bool runLatePulseAfterReady(){
  resetState(141U);
  lastEdge=100U;
  insertMode=false;
  activeTarget.clear();
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  applyOutputs();
  if(relayOn || ledOn)
    return fail("late-pulse-after-ready","pending-ready state did not keep outputs OFF");
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail("late-pulse-after-ready","late edge after finalization did not latch unresolved batch and keep outputs OFF");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" || pendingTarget!="target-01" ||
     saveCalls!=0 || nonceCalls!=0)
    return fail("late-pulse-after-ready","late edge mutated or replaced the already-finalized pending identity");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=5U || markerEdges!=5U)
    return fail("late-pulse-after-ready","late edge was not persisted as one additional unresolved pulse");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail("late-pulse-after-ready","fault persistence began before output inhibition");
  return true;
}
int main(){
  int passed=0;
  if(!runDrainCapture("delayed-100ms-active-low",0U,100U,130U,0U,40U,true)) return 1;
  ++passed;
  if(!runDrainCapture("delayed-100ms-active-high",0U,100U,200U,0U,40U,false)) return 2;
  ++passed;
  if(!runDrainCapture("exact-250ms-boundary",0U,250U,330U,0U,40U,true)) return 3;
  ++passed;
  if(!runDrainCapture("configured-300ms-debounce",1000U,1280U,1360U,600U,300U,true)) return 4;
  ++passed;
  if(!runDrainCapture("millis-rollover",0xFFFFFFF0UL,0x20UL,0x50UL,
                      0xFFFFFFC0UL,40U,true)) return 5;
  ++passed;
  if(!runNoPulseControl()) return 6;
  ++passed;
  if(!runSaveFailure()) return 7;
  ++passed;
  if(!runDeniedGates()) return 8;
  ++passed;
  if(!runPulseLimitBoundary()) return 9;
  ++passed;
  if(!runUnrepresentablePulseCases()) return 10;
  ++passed;
  if(!runLatePulseAfterReady()) return 11;
  ++passed;
  std::cout<<"COIN_PULSE_CAPTURE_PASS "<<passed<<"/11 top-level scenarios\n";
  return 0;
}
'''

SIGNATURES = (
    "bool coinLineIdle(){",
    "bool canStartPoll(){",
    "void applyOutputs(){",
    "bool coinLineQuietAfterInhibit(){",
    "bool beginPollWindow(){",
    "void latchPollPulseFault(uint32_t pulseEdges){",
    "void sampleCoinPulseEdge(bool active){",
)

FUNCTION_NAMES = (
    "coinLineIdle",
    "canStartPoll",
    "applyOutputs",
    "coinLineQuietAfterInhibit",
    "beginPollWindow",
    "latchPollPulseFault",
    "sampleCoinPulseEdge",
)

def compile_and_run(functions):
    program = CPP.replace("@@FUNCTIONS@@", "\n\n".join(functions))
    with tempfile.TemporaryDirectory(prefix="phx-coin-pulse-capture-") as temp:
        cpp = Path(temp) / "coin_pulse_capture.cpp"
        binary = Path(temp) / "coin_pulse_capture"
        cpp.write_text(program, encoding="utf-8")
        compiled = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-O2", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, check=False,
        )
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        return subprocess.run([str(binary)], capture_output=True, text=True, check=False)


def verify_shared_extractor():
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
        raise RuntimeError("shared extractor truncated at a C++ comment/literal brace")
    attribute_probe = (
        "void ICACHE_RAM_ATTR marked() {\n"
        "  /* } */\n"
        "}\n"
        "void IRAM_ATTR next() { return; }\n"
    )
    expected_marked = attribute_probe.split("\nvoid IRAM_ATTR next", 1)[0]
    if extract_function(attribute_probe, "marked") != expected_marked:
        raise RuntimeError("shared extractor failed post-return ICACHE_RAM_ATTR function")
    if extract_function(attribute_probe, "next") != "void IRAM_ATTR next() { return; }":
        raise RuntimeError("shared extractor failed post-return IRAM_ATTR function")
    print("SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS")
    print("SHARED_EXTRACTOR_ISR_ATTRIBUTE_ORDER_PASS")



def main():
    verify_shared_extractor()
    mutations = (
        ("missing-edge-latch", "void sampleCoinPulseEdge(bool active){",
         "lastCoin=active;", "", "sustained high level"),
        ("inclusive-debounce", "void sampleCoinPulseEdge(bool active){",
         "millis()-lastEdge>runDebounceMs",
         "millis()-lastEdge>=runDebounceMs", "deny-case-9"),
        ("missing-pulse-overflow-guard", "void sampleCoinPulseEdge(bool active){",
         "pendingPulses>=20", "pendingPulses>20", "pulse-overflow-21"),
        ("missing-target-drift-guard", "void sampleCoinPulseEdge(bool active){",
         "pendingTarget!=activeTarget", "false", "pending-target-changed"),
        ("missing-pending-ready-late-edge-latch", "void sampleCoinPulseEdge(bool active){",
         "if(pendingReady){", "if(false){", "late edge after finalization did not latch unresolved batch"),
        ("missing-overflow-fault-latch", "void sampleCoinPulseEdge(bool active){",
         "if(pendingTarget!=activeTarget || pendingPulses>=20){\n        latchPollPulseFault((uint32_t)pendingPulses+1U);",
         "if(pendingTarget!=activeTarget || pendingPulses>=20){\n        // overflow fault latch removed",
         "overflow/target drift did not latch deny"),
        ("ignored-save-failure", "void sampleCoinPulseEdge(bool active){",
         "fsReady=false;\n          pendingReady=true;", "",
         "failed durable write did not disable filesystem/intake"),
        ("missing-persistent-fault-latch", "void sampleCoinPulseEdge(bool active){",
         "latchPollPulseFault(pendingPulses);", "",
         "fault latch did not attempt both stores"),
        ("missing-latch-output-inhibit", "void latchPollPulseFault(uint32_t pulseEdges){",
         "  applyOutputs();\n  const bool backupPersisted",
         "  const bool backupPersisted",
         "storage attempt occurred before outputs were logically OFF"),
    )
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
            functions = [extract_function(source, name) for name in FUNCTION_NAMES]
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source failure: {result.stderr or result.stdout}")
                continue
            if "COIN_PULSE_CAPTURE_PASS 11/11" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_COIN_PULSE_CAPTURE_PASS 11/11")
            for name, signature, old, new, expected in mutations:
                index = SIGNATURES.index(signature)
                if old not in functions[index]:
                    failures.append(f"{board} missing mutation anchor {name}")
                    break
                mutated = list(functions)
                mutated[index] = mutated[index].replace(old, new, 1)
                injected = compile_and_run(mutated)
                if injected.returncode == 0 or expected not in injected.stderr:
                    failures.append(f"{board} mutation not rejected: {name}")
                    break
                print(f"{board}_MUTATION_REJECTED {name}")
        except Exception as error:
            failures.append(f"{board} lab error: {error}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_COIN_PULSE_ACCEPTANCE=0")
    print("PHYSICAL_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")

if __name__ == "__main__":
    main()
    print("POLL_LOOP_BLOCKING_INHIBIT_LAB=START", flush=True)
    poll_loop_lab = Path(__file__).with_name("poll_loop_blocking_inhibit_lab.py")
    if not poll_loop_lab.is_file():
        raise RuntimeError(f"missing companion lab: {poll_loop_lab}")
    subprocess.run([sys.executable, str(poll_loop_lab)], check=True)
    print("POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS", flush=True)
    config_lab = Path(__file__).with_name("config_load_read_failure_lab.py")
    print("ESP8266_CONFIG_READ_LAB=START", flush=True)
    subprocess.run([sys.executable, str(config_lab)], check=True)
    print("ESP8266_CONFIG_READ_LAB=END", flush=True)
