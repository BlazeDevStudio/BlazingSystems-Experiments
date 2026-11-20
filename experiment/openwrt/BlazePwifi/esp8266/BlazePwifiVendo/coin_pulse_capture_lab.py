#!/usr/bin/env python3
"""PHX-HARDWARE exact-source coin pulse, bounded-batch overflow, target-drift, post-finalization and ISR-unobserved edge safety lab.

Compiles production coinLineIdle(), canStartPoll(), applyOutputs(),
coinLineQuietAfterInhibit(), beginPollWindow(), latchPollPulseFault(),
quarantineCoinIngressTransition(), and sampleCoinPulseEdge() from both ESP sketches.
It also checks that pin reconfiguration does not silently advance the ISR baseline.
Only the two persistence backends
are fault-injected. The failed-save path checks all four dual-store outcomes,
the unresolved pulse identity, and logical relay/LED OFF before either store is
called. The companion dual-store lab separately extracts the real persistence
helpers. Host C++ uses fake GPIO/time/storage only; no physical acceptance is
claimed.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_function, mask_non_code

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)

CPP = r'''#include <cstdint>
#include <iostream>
#include <string>
using String=std::string;
static uint32_t fakeNow=0, lastPoll=0;
static volatile uint32_t coinEdgeSequence=0;
static uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){return coinEdgeSequence;}
static uint16_t runDebounceMs=40;
static uint32_t lastEdge=0;
static uint32_t pulseStart=0,pulseEnd=0;
static bool pulseEnabled=false;
static bool fsReady=true,journalRecoveryRequired=false,pendingReady=false;
static bool outputPolarityKnown=true;
static bool insertMode=true,lastCoin=false;
static bool runCoinActiveLow=true,pollIntakeSuspended=false,pollDrainAbortedOnActiveLine=false;
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
  fakeNow=now;lastPoll=0;runDebounceMs=40;lastEdge=0;
  coinEdgeSequence=0;lastHandledCoinEdgeSequence=0;
  pulseStart=0;pulseEnd=0;pulseEnabled=false;
  fsReady=true;journalRecoveryRequired=false;pendingReady=false;outputPolarityKnown=true;
  insertMode=true;lastCoin=false;runCoinActiveLow=activeLow;
  pollIntakeSuspended=false;pollDrainAbortedOnActiveLine=false;pinConfigSafe=true;controllerEnabled=true;coinEnabled=true;
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
  if(!pollIntakeSuspended || !pollDrainAbortedOnActiveLine || relayOn || ledOn)
    return fail(name,"drain abort did not retain inhibit for active line");
  const int raw=digitalRead(runCoinPin);
  const bool active=runCoinActiveLow?(raw==LOW):(raw==HIGH);
  if(!active) return fail(name,"drain abort did not leave an active pulse sample");
  sampleCoinPulseEdge(active);
  handlePollDrainAbortAfterSample();
  if(pendingPulses!=1 || saveCalls!=1 || nonceCalls!=1 ||
     pendingNonce!="nonce-1" || pendingTarget!=activeTarget || lastEdge!=fakeNow ||
     !pollIntakeSuspended || !pollDrainAbortedOnActiveLine || relayOn || ledOn)
    return fail(name,"first post-abort sample was not durably queued under inhibit");
  sampleCoinPulseEdge(active);
  fakeNow+=static_cast<uint32_t>(runDebounceMs)+1U;
  sampleCoinPulseEdge(active);
  if(pendingPulses!=1 || saveCalls!=1)
    return fail(name,"sustained high level was counted as another pulse");
  pulseEnabled=false;
  sampleCoinPulseEdge(false);
  handlePollDrainAbortAfterSample();
  if(pollIntakeSuspended || pollDrainAbortedOnActiveLine || !relayOn || !ledOn)
    return fail(name,"drain abort inhibit did not release after line became idle");
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
static bool runMissedPulseAfterBlockingPost(){
  resetState(500U);
  lastEdge=400U;
  insertMode=false;
  activeTarget.clear();
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  relayOn=false;ledOn=false;
  ++coinEdgeSequence; // ISR fires while coin POST blocks; pulse ends before the next GPIO sample.
  sampleCoinPulseEdge(false);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail("late-coin-post-edge","late coin POST pulse was not fail-closed");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" ||
     pendingTarget!="target-01" || saveCalls!=0 || nonceCalls!=0)
    return fail("late-coin-post-edge","finalized pending identity was mutated");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=5U || markerEdges!=5U)
    return fail("late-coin-post-edge","late edge was not persisted with the existing pending count");
  if(lastHandledCoinEdgeSequence!=1U)
    return fail("late-coin-post-edge","ISR sequence was not acknowledged after latching");
  return true;
}
static bool runMissedPulseDuringBlockingWork(){
  resetState(500U);
  lastEdge=400U;
  ++coinEdgeSequence; // Pulse starts and ends while a synchronous handler owns the loop.
  sampleCoinPulseEdge(false);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail("missed-blocking-pulse","missed blocking pulse was not fail-closed");
  if(pendingPulses!=0U || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=1U || markerEdges!=1U)
    return fail("missed-blocking-pulse","unobserved pulse was not durably marked as unresolved");
  return true;
}
static bool runMultipleUnobservedEdges(){
  resetState(500U);
  lastEdge=400U;
  coinEdgeSequence=3U;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail("multiple-unobserved-edges","multiple ISR edges were not quarantined");
  if(pendingPulses!=0U || saveCalls!=0 || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=3U || markerEdges!=3U)
    return fail("multiple-unobserved-edges","edge multiplicity was collapsed into a single pending pulse");
  return true;
}
static bool runSingleObservedEdge(){
  resetState(100U);
  coinEdgeSequence=1U;
  sampleCoinPulseEdge(true);
  if(journalRecoveryRequired || pendingPulses!=1U || saveCalls!=1 ||
     lastHandledCoinEdgeSequence!=1U)
    return fail("single-observed-edge","one sampled ISR edge was not attributed exactly once");
  sampleCoinPulseEdge(true);
  if(journalRecoveryRequired || pendingPulses!=1U || saveCalls!=1)
    return fail("single-observed-edge","sustained active level duplicated an already handled ISR edge");
  return true;
}
static bool runIngressTransitionCases(){
  resetState();
  if(!quarantineCoinIngressTransition() || journalRecoveryRequired ||
     backupCalls!=0 || markerCalls!=0)
    return fail("boot-idle-control","idle line with no unhandled ISR edge was quarantined");

  resetState();
  journalRecoveryRequired=true;
  if(quarantineCoinIngressTransition() || !journalRecoveryRequired ||
     backupCalls!=0 || markerCalls!=0 || relayOn || ledOn)
    return fail("prior-journal-fault","an existing journal fault was reported as a safe ingress transition");

  resetState(50U);
  insertMode=false;
  activeTarget.clear();
  pulseEnabled=true;pulseStart=0U;pulseEnd=100U;
  if(quarantineCoinIngressTransition())
    return fail("boot-active-line","active line at pin-configuration completion was accepted");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !lastCoin || relayOn || ledOn || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=1U || markerEdges!=1U)
    return fail("boot-active-line","active line was not persisted as unresolved with outputs OFF");

  resetState();
  coinEdgeSequence=2U;
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-unhandled-edges","unhandled ISR edges after pin attachment were ignored");
  if(lastHandledCoinEdgeSequence!=2U || backupEdges!=2U || markerEdges!=2U)
    return fail("reconfigure-unhandled-edges","edge multiplicity or handled baseline was not preserved");

  resetState();
  coinEdgeSequence=1U;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-counter-wrap","wrapped ISR sequence was accepted as idle");
  if(lastHandledCoinEdgeSequence!=1U || backupEdges!=3U || markerEdges!=3U)
    return fail("reconfigure-counter-wrap","unsigned edge delta did not preserve three wrapped edges");

  resetState(50U);
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  activeTarget="target-01";
  pulseEnabled=true;pulseStart=0U;pulseEnd=100U;
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-pending-event","active ingress with an existing pending batch was accepted");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" ||
     pendingTarget!="target-01" || !pendingReady || backupEdges!=5U ||
     markerEdges!=5U || relayOn || ledOn)
    return fail("reconfigure-pending-event","existing pending identity was not preserved and denied");
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
  if(!runMissedPulseAfterBlockingPost()) return 12;
  ++passed;
  if(!runMissedPulseDuringBlockingWork()) return 13;
  ++passed;
  if(!runMultipleUnobservedEdges()) return 14;
  ++passed;
  if(!runSingleObservedEdge()) return 15;
  ++passed;
  if(!runIngressTransitionCases()) return 16;
  ++passed;
  std::cout<<"COIN_PULSE_CAPTURE_PASS "<<passed<<"/16 top-level scenarios\n";
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
    "bool quarantineCoinIngressTransition(){",
    "void sampleCoinPulseEdge(bool active){",
    "void handlePollDrainAbortAfterSample(){",
)

FUNCTION_NAMES = (
    "coinLineIdle",
    "canStartPoll",
    "applyOutputs",
    "coinLineQuietAfterInhibit",
    "beginPollWindow",
    "latchPollPulseFault",
    "quarantineCoinIngressTransition",
    "sampleCoinPulseEdge",
    "handlePollDrainAbortAfterSample",
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

    # Exercise C++ raw strings, escaped ordinary strings, and phase-2 line
    # splicing in both comment openers and closers. Braces in these non-code
    # regions must not terminate the extracted production function.
    lexical_probe = (
        "bool lexical() {\n"
        '  const char *raw = u8R"tag( } // /* { )tag";\n'
        '  const char *escaped = "quote: \\" }";\n'
        "  const char brace = '}';\n"
        "  /" + "\\" + "\n" + "/ split line-comment opener { }\n"
        "  // continued line-comment \\" + "\n" + "  { }\n"
        "  /* split block-comment closer *" + "\\" + "\n" + "/\n"
        "  return raw[0] == ' ' && escaped[0] == 'q' && brace == '}';\n"
        "}\n"
        "bool afterLexical() { return false; }\n"
    )
    expected_lexical = lexical_probe.split("\nbool afterLexical", 1)[0]
    actual_lexical = extract_function(lexical_probe, "lexical")
    if actual_lexical != expected_lexical:
        raise RuntimeError("shared extractor mishandled raw strings or phase-2 comment splicing")
    masked_lexical = mask_non_code(lexical_probe)
    if len(masked_lexical) != len(lexical_probe) or masked_lexical.count("\n") != lexical_probe.count("\n"):
        raise RuntimeError("shared extractor mask changed source offsets or newline positions")
    if "\\" + "\n" not in lexical_probe or lexical_probe.count("\n") < 8:
        raise RuntimeError("phase-2 fixture did not contain physical backslash-newline pairs")

    # Prove this fixture would catch the former raw-brace counting strategy.
    start = lexical_probe.index("bool lexical()")
    opening = lexical_probe.index("{", start)
    depth = 0
    legacy_end = None
    for position in range(opening, len(lexical_probe)):
        if lexical_probe[position] == "{":
            depth += 1
        elif lexical_probe[position] == "}":
            depth -= 1
            if depth == 0:
                legacy_end = position + 1
                break
    if legacy_end is None or lexical_probe[start:legacy_end] == expected_lexical:
        raise RuntimeError("raw-string fixture does not reject the legacy brace counter")

    print("SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS")
    print("SHARED_EXTRACTOR_RAW_STRING_PHASE2_PASS")
    print("SHARED_EXTRACTOR_ISR_ATTRIBUTE_ORDER_PASS")



def verify_configure_runtime_pins_preserves_edge_baseline(source):
    body = extract_function(source, "configureRuntimePins")
    if "lastHandledCoinEdgeSequence=snapshotCoinEdgeSequence();" in body:
        raise RuntimeError("configureRuntimePins discards unhandled ISR edge baseline after attaching the coin ISR")
    if body.count("quarantineCoinIngressTransition();") != 2:
        raise RuntimeError("configureRuntimePins must quarantine ingress on both pin-attachment branches")


def main():
    verify_shared_extractor()
    mutations = (
        ("missing-edge-latch", "void sampleCoinPulseEdge(bool active){",
         "  lastHandledCoinEdgeSequence=observedEdgeSequence;" + "\n" + "  lastCoin=active;" + "\n" + "}",
         "  lastHandledCoinEdgeSequence=observedEdgeSequence;" + "\n" + "}", "sustained high level"),
        ("inclusive-debounce", "void sampleCoinPulseEdge(bool active){",
         "if(fsReady && !journalRecoveryRequired && active && !lastCoin &&\n     millis()-lastEdge>runDebounceMs){",
         "if(fsReady && !journalRecoveryRequired && active && !lastCoin &&\n     millis()-lastEdge>=runDebounceMs){", "deny-case-9"),
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
                 ("missing-ingress-transition-quarantine", "bool quarantineCoinIngressTransition(){",
          "if(lineIdle && unhandledEdges==0U) return true;", "if(true) return true;",
          "active line at pin-configuration completion was accepted"),
         ("missing-transition-edge-ack", "bool quarantineCoinIngressTransition(){",
          "  if(pendingPulses>0U) pendingReady=true;\n  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
          "  if(pendingPulses>0U) pendingReady=true;\n  lastCoin=!lineIdle;",
          "edge multiplicity or handled baseline was not preserved"),
         ("missing-pending-event-ready", "bool quarantineCoinIngressTransition(){",
          "  if(pendingPulses>0U) pendingReady=true;\n  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
          "  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
          "existing pending identity was not preserved and denied"),
         # Keep sampledSingleEdge referenced so -Werror tests the runtime deny path, not an unused-variable compile error.
        ("missing-isr-edge-reconciliation", "void sampleCoinPulseEdge(bool active){",
         "if(unseenEdges>0U && !sampledSingleEdge){", "if(false && !sampledSingleEdge){",
         "late coin POST pulse was not fail-closed"),
        ("multiple-isr-edges-accepted-as-one", "void sampleCoinPulseEdge(bool active){",
         "unseenEdges==1U", "unseenEdges<=3U",
         "multiple ISR edges were not quarantined"),
    )
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
            verify_configure_runtime_pins_preserves_edge_baseline(source)
            functions = [extract_function(source, name) for name in FUNCTION_NAMES]
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source failure: {result.stderr or result.stdout}")
                continue
            if "COIN_PULSE_CAPTURE_PASS 16/16" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_COIN_PULSE_CAPTURE_PASS 16/16")
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

# The quarantine workflow owns poll_loop_blocking_inhibit_lab.py as a separate step.
# Keep this entry point limited to the coin-pulse capture suite.
if __name__ == "__main__":
    main()
