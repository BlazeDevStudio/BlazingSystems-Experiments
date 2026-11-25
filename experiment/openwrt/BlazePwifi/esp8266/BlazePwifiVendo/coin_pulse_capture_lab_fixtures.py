"""Exact C++ host fixture for source-extracted ESP8266/ESP32 coin pulse behavior.

Keep board-independent fake GPIO/time/storage behavior here. Production helpers
are inserted only by the runner after extraction from the literal sketch files.
"""

CPP = r'''#include <cstdint>
#include <iostream>
#include <string>
using String=std::string;
#define ICACHE_RAM_ATTR
#define IRAM_ATTR
static uint32_t fakeNow=0, lastPoll=0;
static volatile uint32_t coinEdgeSequence=0;
static uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){return coinEdgeSequence;}
static uint16_t runDebounceMs=40;
static uint32_t lastEdge=0;
static uint32_t pulseStart=0,pulseEnd=0;
static bool pulseEnabled=false;
static bool fsReady=true,journalRecoveryRequired=false,pendingReady=false;
static bool pendingPostAttempted=false;
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
  fsReady=true;journalRecoveryRequired=false;pendingReady=false;pendingPostAttempted=false;outputPolarityKnown=true;
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
static bool runInvalidPinConfig(){
  // An unsafe GPIO map must never turn a sampled fallback-pin edge into a coin event.
  resetState(1000U);
  pinConfigSafe=false;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn){
    std::cerr<<"UNSAFE_PIN_DEBUG journal="<<journalRecoveryRequired
             <<" insert="<<insertMode<<" target="<<activeTarget
             <<" relay="<<relayOn<<" led="<<ledOn
             <<" pin="<<pinConfigSafe<<" now="<<millis()
             <<" last="<<lastEdge<<" debounce="<<runDebounceMs<<"\\n";
    return fail("unsafe-pin-sample","unsafe pin mapping did not latch unresolved ingress");
  }
  if(pendingPulses!=0 || saveCalls!=0 || nonceCalls!=0)
    return fail("unsafe-pin-sample","unsafe pin mapping was assigned to a coin batch");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=1U || markerEdges!=1U)
    return fail("unsafe-pin-sample","unsafe pin mapping did not persist one unresolved edge");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail("unsafe-pin-sample","fault persistence began before outputs were OFF");

  // Even an older pending batch must not be dispatched while the pin map is unsafe.
  resetState();
  pinConfigSafe=false;
  pendingReady=true;
  pendingPulses=1U;
  if(canAttemptCoinPost())
    return fail("unsafe-pin-post-gate","coin POST remained eligible with an unsafe pin mapping");
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

static bool runIsrSequenceWraparound(){
  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  coinEdgeISR();
  if(snapshotCoinEdgeSequence()!=0xFFFFFFFFUL)
    return fail("isr-sequence-did-not-wrap","first ISR edge did not advance to UINT32_MAX");
  coinEdgeISR();
  if(snapshotCoinEdgeSequence()!=0U)
    return fail("isr-sequence-did-not-wrap","second ISR edge did not wrap to zero");
  if(quarantineCoinIngressTransition())
    return fail("isr-sequence-did-not-wrap","two wrapped unhandled ISR edges were accepted as idle");
  if(lastHandledCoinEdgeSequence!=0U || backupEdges!=2U || markerEdges!=2U)
    return fail("isr-sequence-did-not-wrap","wrapped ISR delta was not preserved in both fault stores");
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
  if(!runInvalidPinConfig()) return 17;
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
  if(!runIsrSequenceWraparound()) return 18;
  ++passed;
  std::cout<<"COIN_PULSE_CAPTURE_PASS "<<passed<<"/18 top-level scenarios\n";
  return 0;
}'''
