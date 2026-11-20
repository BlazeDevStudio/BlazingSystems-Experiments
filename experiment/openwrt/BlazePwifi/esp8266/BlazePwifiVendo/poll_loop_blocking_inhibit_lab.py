#!/usr/bin/env python3
"""Execute the actual ESP loop() around the synchronous poll with bounded host I/O stubs.

The production loop, poll-window helpers, output gate, coin POST disposition
helper and default-deny acceptPollResponse() are extracted unchanged from both sketches. Secondary
NVS/EEPROM helpers are stubbed here; poll_fault_dual_store_lab.py tests them
separately. This is SIMULATED control-flow evidence, not physical coin proof.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

STUBS = r"""
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif
#ifndef ICACHE_RAM_ATTR
#define ICACHE_RAM_ATTR
#endif
static constexpr int HIGH=1, LOW=0, WL_CONNECTED=3;
static constexpr int INPUT=0, INPUT_PULLUP=2, OUTPUT=1, FALLING=4, RISING=5;
static bool fakeShortWrite=false, fakeCorruptReadback=false, fakeOpenFail=false;
class File {
  std::string *data=nullptr;
  size_t pos=0;
public:
  File()=default;
  explicit File(std::string *value):data(value){}
  explicit operator bool() const { return data!=nullptr; }
  size_t write(const uint8_t *bytes,size_t length){
    if(!data) return 0;
    size_t actual=length;
    if(fakeShortWrite && actual) --actual;
    data->append(reinterpret_cast<const char*>(bytes),actual);
    return actual;
  }
  void flush(){}
  void close(){}
  size_t size() const { return data?data->size():0; }
  int read(){
    if(!data || pos>=data->size()) return -1;
    unsigned char value=(unsigned char)(*data)[pos++];
    if(fakeCorruptReadback && pos==1) value^=1;
    return value;
  }
};
void observeFaultMarkerOpen();
struct FakeLittleFS {
  std::map<std::string,std::string> files;
  bool begin(bool){ return true; }
  bool begin(){ return true; }
  bool exists(const char *path) const { return files.find(path)!=files.end(); }
  File open(const char *path,const char *mode){
    if(fakeOpenFail) return File();
    const std::string key(path);
    if(key=="/pollpulse.fault" && mode[0]=='w') observeFaultMarkerOpen();
    if(mode[0]=='w'){ files[key].clear(); return File(&files[key]); }
    auto found=files.find(key);
    return found==files.end()?File():File(&found->second);
  }
} LittleFS;
static bool interruptAttached=false;
static int attachedPin=-1, attachedMode=-1;
static void (*attachedIsr)()=nullptr;
int digitalPinToInterrupt(int pin){ return pin; }
void attachInterrupt(int pin,void (*handler)(),int mode){
  interruptAttached=true; attachedPin=pin; attachedMode=mode; attachedIsr=handler;
}
void detachInterrupt(int pin){
  if(interruptAttached && attachedPin==pin){
    interruptAttached=false; attachedPin=-1; attachedMode=-1; attachedIsr=nullptr;
  }
}
void pinMode(int,int){}
void loadPending(){}
// This lab isolates the production loop and LittleFS marker path. The exact
// secondary-store implementation and reboot fallback are covered separately
// by poll_fault_dual_store_lab.py.
bool pollFaultBackupPresentOrCorrupt(){ return false; }
void observeBackupWrite();
bool writePollFaultBackup(uint32_t){ observeBackupWrite(); return false; }
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
struct String : std::string {
  using std::string::string;
  using std::string::operator=;
  String()=default;
  String(const std::string &v):std::string(v){}
  String(int v):std::string(std::to_string(v)){}
  size_t length() const { return size(); }
  int indexOf(const char *needle) const {
    const auto p=find(needle);
    return p==npos?-1:(int)p;
  }
  bool isEmpty() const { return empty(); }
};
static uint32_t fakeNow=2000;
static int pulseStart=-1, pulseEnd=-1;
static bool relayOn=false, ledOn=false;
static bool backupWriteSawRelayOn=false, backupWriteSawLedOn=false;
static bool markerOpenSawRelayOn=false, markerOpenSawLedOn=false;
void observeBackupWrite(){ backupWriteSawRelayOn=relayOn; backupWriteSawLedOn=ledOn; }
void observeFaultMarkerOpen(){ markerOpenSawRelayOn=relayOn; markerOpenSawLedOn=ledOn; }
static bool relayLevelHigh=false, ledLevelHigh=false;
static bool injectDuringHttp=false;
static unsigned injectDuringHttpEdgeCount=1;
static bool injectTimedPollPulse=false, timedPulseIsrInjected=false;
static bool allowCoinPost=false, injectDuringCoinPost=false;
static int coinPostCalls=0, clearCalls=0;
static bool injectAfterDrainEdge=false;
unsigned injectAfterDrainEdgeCount=1;
static bool injectDuringDrainAbort=false;
static bool injectDrainAbortWithoutIsr=false;
static bool injectDrainAbortPulseEndsBeforeSample=false;
static bool injectDuringPollRelease=false;
static bool injectDuringPollReleaseAtRelayWrite=false;
static bool pollReleaseEdgeInjected=false;
static bool pollReleaseEdgeSawRelayOff=false;
static bool pollReleaseRelayEnergizedBeforeLatch=false;
static bool pollReleaseRelayClearedBeforeLatch=false;
static int drainAbortReadCount=0;
static bool drainAbortInjected=false;
static bool drainAbortSawRelayOn=false;
static bool drainAbortSampleSawRelayOn=false;
static bool drainAbortReenabledBeforeLatch=false;
static bool drainAbortActiveLineReenabled=false;
static int pollCalls=0, saveCalls=0;
static uint32_t pollStartAt=0, pollEndAt=0;
static bool pollStartRelayOn=true, pollStartSuspended=false;
static bool pollStartCoinIdle=false, pollEndRelayOn=true, pollEndSuspended=false;
static bool pollPulseObservedDuringHttp=false, pollPulseRelayOff=false, pollPulseSuspended=false;
bool insertMode=true, lastCoin=false;
bool pollIntakeSuspended=false, pollDrainAbortedOnActiveLine=false, pinConfigSafe=true;
bool outputPolarityKnown=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true;
bool setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
bool pendingReady=false, fsReady=true, journalRecoveryRequired=false;
bool pendingPostAttempted=false;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
int runCoinPin=4, runLedPin=2, runRelayPin=26;
int maxWifiRetries=6, wifiFailures=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;
String activeTarget="target-01", pendingTarget="", pendingNonce="";
struct ConfigStub {
#ifdef TARGET_ESP32
  String ssid="test-ssid", pass="test-pass";
#else
  char ssid[33]="test-ssid"; char pass[65]="test-pass";
#endif
} cfg;
int digitalRead(int) {
  if(injectDuringDrainAbort){
    ++drainAbortReadCount;
    if(drainAbortReadCount==2 && !drainAbortInjected){
      drainAbortInjected=true;
      if(interruptAttached && attachedIsr && attachedPin==runCoinPin &&
         attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr();
      drainAbortSawRelayOn=relayOn;
      return runCoinActiveLow?LOW:HIGH;
    }
    if(drainAbortReadCount==3) drainAbortSampleSawRelayOn=relayOn;
  }
  if(injectDrainAbortWithoutIsr){
    ++drainAbortReadCount;
    if(drainAbortReadCount==2 && !drainAbortInjected){
      drainAbortInjected=true;
      pulseStart=(int)fakeNow;
      pulseEnd=(int)fakeNow+(injectDrainAbortPulseEndsBeforeSample?0:100);
      drainAbortSawRelayOn=relayOn;
      return runCoinActiveLow?LOW:HIGH;
    }
  }
  if(injectTimedPollPulse && !timedPulseIsrInjected && pulseStart>=0 &&
     fakeNow>=(uint32_t)pulseStart && fakeNow<(uint32_t)pulseEnd){
    timedPulseIsrInjected=true;
    if(interruptAttached && attachedIsr && attachedPin==runCoinPin &&
       attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr();
  }
  const bool active=pulseStart>=0 &&
    fakeNow>=(uint32_t)pulseStart && fakeNow<(uint32_t)pulseEnd;
  if(runCoinActiveLow) return active?LOW:HIGH;
  return active?HIGH:LOW;
}
void digitalWrite(int pin,int level) {
  const bool injectAtLed=injectDuringPollRelease && pin==runLedPin;
  const bool injectAtRelay=injectDuringPollReleaseAtRelayWrite && pin==runRelayPin;
  if((injectAtLed || injectAtRelay) && pollCalls==1 && !pollIntakeSuspended &&
     !journalRecoveryRequired && !pollReleaseEdgeInjected){
    pollReleaseEdgeInjected=true;
    pollReleaseEdgeSawRelayOff=!relayOn;
    pulseStart=(int)fakeNow;
    pulseEnd=(int)fakeNow+100;
    if(interruptAttached && attachedIsr && attachedPin==runCoinPin &&
       attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr();
  }
  if(pin==runRelayPin) {
    relayLevelHigh=(level==HIGH);
    relayOn=(level==(runRelayActiveHigh?HIGH:LOW));
    if(pollReleaseEdgeInjected && !journalRecoveryRequired){
      if(relayOn) pollReleaseRelayEnergizedBeforeLatch=true;
      else pollReleaseRelayClearedBeforeLatch=true;
    }
  }
  if(pin==runLedPin) {
    ledLevelHigh=(level==HIGH);
    ledOn=(level==(runLedActiveHigh?HIGH:LOW));
  }
  // During a drain-abort injection, any re-energized output before the sticky
  // recovery latch is set proves that the poll inhibit was released too early.
  if(injectDuringDrainAbort && drainAbortInjected && !journalRecoveryRequired &&
     (relayOn || ledOn)) drainAbortReenabledBeforeLatch=true;
  if(injectDrainAbortWithoutIsr && drainAbortInjected && !journalRecoveryRequired &&
     !pollIntakeSuspended && (relayOn || ledOn) && pulseStart>=0 &&
     fakeNow<(uint32_t)pulseEnd) drainAbortActiveLineReenabled=true;
}
uint32_t millis(){ return fakeNow; }
void delay(int ms){ fakeNow+=(uint32_t)ms; }
struct FakeWiFi {
  int status() const { return WL_CONNECTED; }
  void disconnect() {}
  void softAPdisconnect(bool) {}
  void begin(const char*,const char*) {}
} WiFi;
struct FakeWeb { void handleClient() {} } web;
struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;
"""

SUPPORT = r"""
String freshNonce(){ return String("nonce12345678"); }
bool savePending(){ ++saveCalls; return true; }
bool canAttemptCoinPost(){ return allowCoinPost && outputPolarityKnown && fsReady && !journalRecoveryRequired && !pendingPostAttempted && pendingReady && pendingPulses>0; }
bool markPendingPostAttempt(){ if(!allowCoinPost) return false; pendingPostAttempted=true; return true; }
bool coinPostDispositionVerified(const String&,const String&,const String&,uint8_t){ return allowCoinPost; }
bool pollJsonTopLevelTrue(const String&,const char*){ return allowCoinPost; }
bool clearPending(){ ++clearCalls; pendingPulses=0; pendingReady=false; pendingPostAttempted=false; pendingTarget.clear(); pendingNonce.clear(); return true; }
bool quarantinePending(const String&){ return false; }
void startSetupAp(){}
String post(const String &action,const String &pulses=String("0"),
            const String &target=String(""),const String &forcedNonce=String("")){
  (void)pulses; (void)target; (void)forcedNonce;
  if(action=="poll"){
    ++pollCalls;
    pollStartAt=fakeNow;
    pollStartRelayOn=relayOn;
    pollStartSuspended=pollIntakeSuspended;
    pollStartCoinIdle=coinLineIdle();
    if(injectDuringHttp){
      pulseStart=(int)fakeNow+50;
      pulseEnd=(int)fakeNow+130;
      fakeNow+=50UL;
      pollPulseObservedDuringHttp=!coinLineIdle();
      if(interruptAttached && attachedIsr && attachedPin==runCoinPin &&
         attachedMode==(runCoinActiveLow?FALLING:RISING)) {
        for(unsigned edge=0; edge<injectDuringHttpEdgeCount; ++edge) attachedIsr();
      }
      pollPulseRelayOff=!relayOn;
      pollPulseSuspended=pollIntakeSuspended;
      fakeNow+=80UL;
      fakeNow+=3370UL;
    } else {
      fakeNow+=3500UL;
    }
    // Simulate the production HTTPClient timeout. The extracted loop remains
    // blocked while the relay and poll-inhibit state must remain unchanged.
    pollEndAt=fakeNow;
    pollEndRelayOn=relayOn;
    pollEndSuspended=pollIntakeSuspended;
    // Deliberately hostile positive response: the extracted production
    // acceptPollResponse() must still deny it until CORE/QA approve the contract.
    return String("{\"ok\":true,\"insert\":true,\"target\":\"spoof-target\"}");
  }
  if(action=="coin"){
    ++coinPostCalls;
    if(injectDuringCoinPost){ coinEdgeSequence++; injectDuringCoinPost=false; }
    fakeNow+=3500UL;
    return String("{\"ok\":true}");
  }
  return String("");
}
"""

MAIN = r"""
void resetState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  coinEdgeSequence=0; lastHandledCoinEdgeSequence=0; interruptAttached=false; attachedPin=-1; attachedMode=-1; attachedIsr=nullptr;
  fakeShortWrite=false; fakeCorruptReadback=false; fakeOpenFail=false; LittleFS.files.clear();
  relayOn=false; ledOn=false; backupWriteSawRelayOn=false; backupWriteSawLedOn=false;
  markerOpenSawRelayOn=false; markerOpenSawLedOn=false; relayLevelHigh=false; ledLevelHigh=false;
  injectDuringHttp=false; injectDuringHttpEdgeCount=1; injectTimedPollPulse=false; timedPulseIsrInjected=false;
  injectAfterDrainEdge=false; injectAfterDrainEdgeCount=1; injectDuringDrainAbort=false;
  injectDrainAbortWithoutIsr=false; injectDrainAbortPulseEndsBeforeSample=false;
  injectDuringPollRelease=false; injectDuringPollReleaseAtRelayWrite=false;
  pollReleaseEdgeInjected=false; pollReleaseEdgeSawRelayOff=false;
  pollReleaseRelayEnergizedBeforeLatch=false; pollReleaseRelayClearedBeforeLatch=false;
  allowCoinPost=false; injectDuringCoinPost=false; coinPostCalls=0; clearCalls=0;
  drainAbortReadCount=0; drainAbortInjected=false; drainAbortSawRelayOn=false;
  drainAbortSampleSawRelayOn=false; drainAbortReenabledBeforeLatch=false;
  drainAbortActiveLineReenabled=false;
  pollCalls=0; saveCalls=0;
  pollStartAt=0; pollEndAt=0; pollStartRelayOn=true; pollStartSuspended=false;
  pollStartCoinIdle=false; pollEndRelayOn=true; pollEndSuspended=false;
  pollPulseObservedDuringHttp=false; pollPulseRelayOff=false; pollPulseSuspended=false;
  insertMode=true; lastCoin=false; pollIntakeSuspended=false; pollDrainAbortedOnActiveLine=false; pinConfigSafe=true; outputPolarityKnown=true;
  controllerEnabled=true; coinEnabled=true; relayEnabled=true; ledEnabled=true;
  setupApOn=false; runCoinActiveLow=true; runRelayActiveHigh=true; runLedActiveHigh=true;
  pendingReady=false; fsReady=true; journalRecoveryRequired=false; pendingPostAttempted=false;
  lastPoll=0; lastEdge=0; lastSend=0; configuredApSince=0;
  pendingPulses=0; runCoinPin=4; runLedPin=2; runRelayPin=26;
  maxWifiRetries=6; wifiFailures=0; runDebounceMs=40; runPulseGroupMs=400;
  activeTarget="target-01"; pendingTarget=""; pendingNonce="";
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  applyOutputs();
}
bool recordedPulseState(){
  return pollCalls==0 && pendingPulses==1 && !pendingReady &&
         pendingTarget=="target-01" && pendingNonce=="nonce12345678" &&
         lastCoin && !relayOn && !ledOn && pollIntakeSuspended &&
         pollDrainAbortedOnActiveLine && saveCalls==1;
}
bool releaseRecordedPulseAfterIdle(){
  fakeNow=(uint32_t)pulseEnd;
  loop();
  return !pollIntakeSuspended && !pollDrainAbortedOnActiveLine &&
         relayOn && ledOn && pendingPulses==1U && !journalRecoveryRequired;
}
int main(){
  // A prior persistent journal fault must abort even with an idle line and no new ISR edge.
  resetState();
  journalRecoveryRequired=true;
  lastCoin=true;
  relayOn=true;
  ledOn=true;
  const bool idleFaultAccepted=quarantineCoinIngressTransition();
  if(idleFaultAccepted || !journalRecoveryRequired || relayOn || ledOn || lastCoin) return 48;
  std::cout<<"POLL_INGRESS_PRIOR_JOURNAL_FAULT_IDLE_LINE_DENY_PASS\n";

  // A normal blocked poll remains inhibited and default-deny when no edge occurs.
  resetState(); loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollStartRelayOn ||
     !pollStartSuspended || !pollStartCoinIdle ||
     pollEndAt-pollStartAt!=3500 || pollEndRelayOn || !pollEndSuspended ||
     pollIntakeSuspended || relayOn || ledOn || insertMode ||
     !activeTarget.empty() || pendingPulses!=0 || journalRecoveryRequired ||
     LittleFS.exists("/pollpulse.fault") || lastPoll!=pollEndAt ||
     fakeNow!=pollEndAt+2) return 10;

  // Verify the latch requests OFF before either persistent store is entered.
  // The first hook is the secondary NVS/EEPROM writer; the second is LittleFS open.
  resetState();
  relayOn=true; ledOn=true; insertMode=true; activeTarget="target-01";
  latchPollPulseFault(1);
  if(backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn || relayOn || ledOn ||
     !journalRecoveryRequired || insertMode || !activeTarget.empty()) return 23;
  std::cout<<"POLL_FAULT_PRE_PERSISTENCE_OUTPUT_OFF_PASS backup-write and LittleFS-open\\n";

  // A pulse edge during the 3.5 s synchronous poll must be captured by the
  // production ISR, latched to LittleFS, and never interpreted as a credit.
  resetState(); injectDuringHttp=true; loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollStartAt-2000<250 ||
     pollStartRelayOn || !pollStartSuspended || !pollStartCoinIdle ||
     pollEndAt-pollStartAt!=3500 || pollEndRelayOn || !pollEndSuspended ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     pollIntakeSuspended || relayOn || ledOn || insertMode ||
     !activeTarget.empty() || pendingPulses!=0 || lastPoll!=pollEndAt ||
     fakeNow!=pollEndAt+2) return 11;
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 12;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return 13;

  // A reboot must restore the persistent fault latch before any output can energize.
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  applyOutputs();
  if(!relayOn) return 14;
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn) return 15;

  // The ISR edge counter is uint32_t: an edge during the blocked poll must
  // remain visible when the sequence wraps from UINT32_MAX to zero.
  resetState();
  coinEdgeSequence=0xFFFFFFFFUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFFUL;
  injectDuringHttp=true;
  loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollEndAt-pollStartAt!=3500 ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || lastPoll!=pollEndAt || fakeNow!=pollEndAt+2) return 50;
  const std::string rolloverMarker=LittleFS.files["/pollpulse.fault"];
  if(rolloverMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     rolloverMarker.find("pulses=1")==std::string::npos) return 50;
  std::cout<<"POLL_BLOCKED_ISR_SEQUENCE_ROLLOVER_DENY_PASS\\n";

  // Two ISR edges crossing UINT32_MAX must retain the exact modulo delta, not collapse to one.
  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectDuringHttpEdgeCount=2;
  injectDuringHttp=true;
  loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollEndAt-pollStartAt!=3500 ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || lastPoll!=pollEndAt || fakeNow!=pollEndAt+2) return 51;
  const std::string multiEdgeRolloverMarker=LittleFS.files["/pollpulse.fault"];
  if(multiEdgeRolloverMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     multiEdgeRolloverMarker.find("pulses=2")==std::string::npos) return 51;
  std::cout<<"POLL_BLOCKED_ISR_MULTI_EDGE_ROLLOVER_DENY_PASS\\n";

  // Active-high input polarity must attach the opposite edge and fail closed too.
  resetState(); runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDuringHttp=true; loop();
  if(attachedMode!=RISING || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 16;

  // A short write leaves a path that boot treats as a fault even when readback fails.
  resetState(); fakeShortWrite=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 17;
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || relayOn) return 18;

  // Readback corruption is rejected; existence alone remains a boot-time deny latch.
  resetState(); fakeCorruptReadback=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 19;
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || relayOn) return 20;

  // If marker creation itself is unavailable, the current boot still remains denied.
  resetState(); fakeOpenFail=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 21;

  // A pulse can abort the drain and end before the next ordinary loop sample.
  // The ISR sequence must be reconciled and the deny marker persisted before release.
  resetState(); injectDuringDrainAbort=true; loop();
  if(!drainAbortInjected || drainAbortSawRelayOn || drainAbortSampleSawRelayOn ||
     drainAbortReenabledBeforeLatch || pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || lastPoll+2!=fakeNow ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 25;
  const std::string abortMarker=LittleFS.files["/pollpulse.fault"];
  if(abortMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     abortMarker.find("pulses=1")==std::string::npos) return 27;
  std::cout<<"POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS\\n";
  std::cout<<"POLL_ABORTED_DRAIN_ISR_EDGE_PERSISTED_PASS\\n";

  // The same drain-abort edge must be caught for active-high coin wiring.
  resetState(); runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDuringDrainAbort=true; loop();
  if(!drainAbortInjected || drainAbortSawRelayOn || drainAbortSampleSawRelayOn ||
     drainAbortReenabledBeforeLatch || pollCalls!=0 || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || lastPoll+2!=fakeNow ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 28;
  std::cout<<"POLL_ABORTED_DRAIN_ISR_EDGE_ACTIVE_HIGH_PASS\\n";

  // An ISR edge can arrive after the pre-release snapshot but during the first
  // GPIO writes that re-enable the acceptor. It must be reconciled before the
  // next ordinary sample can turn that in-flight edge into a new pending coin.
  resetState(); injectDuringPollRelease=true; loop();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff || pollCalls!=1 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 29;
  const std::string releaseMarker=LittleFS.files["/pollpulse.fault"];
  if(releaseMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     releaseMarker.find("pulses=1")==std::string::npos) return 30;
  std::cout<<"POLL_RELEASE_WINDOW_ISR_EDGE_PERSISTED_PASS\\n";

  // GPIO sees a pulse during drain without an ISR delta. Capture and persist
  // it while the poll inhibit stays asserted; release only after the line is idle.
  resetState(); injectDrainAbortWithoutIsr=true; loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !pollIntakeSuspended || !pollDrainAbortedOnActiveLine ||
     relayOn || ledOn || journalRecoveryRequired || pendingPulses!=1U ||
     pendingReady || pendingTarget!="target-01" || pendingNonce!="nonce12345678" ||
     saveCalls!=1 || !lastCoin) return 34;
  std::cout<<"POLL_ABORT_ACTIVE_LINE_WITHOUT_ISR_CAPTURED_HELD_PASS\\n";
  fakeNow=(uint32_t)pulseEnd; loop();
  if(pollIntakeSuspended || pollDrainAbortedOnActiveLine || !relayOn || !ledOn ||
     pendingPulses!=1U || saveCalls!=1 || journalRecoveryRequired) return 35;
  std::cout<<"POLL_ABORT_ACTIVE_LINE_RELEASES_AFTER_IDLE_PASS\\n";

  // Active-high wiring follows the same capture/hold/release ordering.
  resetState(); runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDrainAbortWithoutIsr=true; loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !pollIntakeSuspended || !pollDrainAbortedOnActiveLine ||
     relayOn || ledOn || journalRecoveryRequired || pendingPulses!=1U ||
     pendingReady || pendingTarget!="target-01" || pendingNonce!="nonce12345678" ||
     saveCalls!=1 || !lastCoin) return 36;
  std::cout<<"POLL_ABORT_ACTIVE_HIGH_WITHOUT_ISR_CAPTURED_HELD_PASS\\n";
  fakeNow=(uint32_t)pulseEnd; loop();
  if(pollIntakeSuspended || pollDrainAbortedOnActiveLine || !relayOn || !ledOn ||
     pendingPulses!=1U || saveCalls!=1 || journalRecoveryRequired) return 37;
  std::cout<<"POLL_ABORT_ACTIVE_HIGH_RELEASES_AFTER_IDLE_PASS\\n";

  // If the observed pulse disappears before the normal sample, the ingress
  // cannot be assigned to a durable pending event and must latch a fault.
  resetState(); injectDrainAbortWithoutIsr=true;
  injectDrainAbortPulseEndsBeforeSample=true; loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine || pendingPulses!=0U ||
     saveCalls!=0 || backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 40;
  const std::string missedSampleMarker=LittleFS.files["/pollpulse.fault"];
  if(missedSampleMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     missedSampleMarker.find("pulses=1")==std::string::npos) return 41;
  std::cout<<"POLL_ABORT_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS\\n";

  // A prior persistent journal fault must dominate stale positive controller
  // state when the temporary active-line drain hold is cleared.
  resetState();
  journalRecoveryRequired=true;
  pollIntakeSuspended=true;
  pollDrainAbortedOnActiveLine=true;
  insertMode=true;
  activeTarget="stale-target";
  relayOn=true;
  ledOn=true;
  handlePollDrainAbortAfterSample();
  if(!journalRecoveryRequired || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine || !insertMode ||
     activeTarget!="stale-target" || relayOn || ledOn) return 47;
  std::cout<<"POLL_ABORT_PRIOR_JOURNAL_FAULT_REMAINS_DENY_PASS\\n";

  // Existing pulse-drain behavior remains intact for a pulse observed before poll.
  resetState(); pulseStart=2050; pulseEnd=2130; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 31;
  resetState(); runCoinActiveLow=false; configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  pulseStart=2200; pulseEnd=2280; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 32;
  resetState(); pulseStart=2250; pulseEnd=2330; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 33;

  // Existing pending/recovery/FS guards remain fail-closed.
  resetState(); pendingReady=true; pendingPulses=1; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 41;
  resetState(); journalRecoveryRequired=true; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 42;
  resetState(); fsReady=false; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 43;

  // An ISR edge already present before poll admission must abort before HTTP.
  resetState(); coinEdgeSequence=1U; loop();
  if(pollCalls!=0 || !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || pollIntakeSuspended || lastPoll!=2000U || fakeNow!=2002U) return 44;
  std::cout<<"POLL_UNOBSERVED_PRE_POLL_EDGE_ABORT_PASS\\n";

  // A coin pulse captured by the ISR while the synchronous coin POST blocks
  // must be persisted before a success disposition can clear the pending record.
  resetState(); allowCoinPost=true; pendingReady=true; pendingPulses=4U;
  pendingNonce="nonce-existing"; pendingTarget="target-01";
  insertMode=false; activeTarget=""; injectDuringCoinPost=true; loop();
  if(coinPostCalls!=1 || clearCalls!=0 || pendingPulses!=4U || !pendingReady ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 45;
  std::cout<<"COIN_POST_BLOCKED_ISR_EDGE_RETAINED_PASS\\n";

  // With no intervening ISR edge, the existing authenticated success path may clear.
  resetState(); allowCoinPost=true; pendingReady=true; pendingPulses=4U;
  pendingNonce="nonce-existing"; pendingTarget="target-01";
  insertMode=false; activeTarget=""; loop();
  if(coinPostCalls!=1 || clearCalls!=1 || pendingPulses!=0U || pendingReady ||
     journalRecoveryRequired || LittleFS.exists("/pollpulse.fault")) return 46;
  std::cout<<"COIN_POST_NO_EDGE_CLEAR_CONTROL_PASS\\n";

  std::cout<<"POLL_BLOCKED_EDGE_FAULT_PASS 8/8 fault-marker scenarios; existing poll-loop guards 7/7\n";
  std::cout<<"SIMULATED_ONLY=1 PHYSICAL_COIN_ACCEPTOR_VERIFIED=0 PHYSICAL_POWER_CUT_VERIFIED=0\n";
  return 0;
}
"""

RACE_MAIN = MAIN.replace(
    "  // Existing pulse-drain behavior remains intact for a pulse observed before poll.",
    "  // An ISR edge after the final quiet sample must be persisted before HTTP begins.\n"
    "  resetState(); injectAfterDrainEdge=true; loop();\n"
    "  if(pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||\n"
    "     !LittleFS.exists(\"/pollpulse.fault\") || relayOn || ledOn ||\n"
    "     insertMode || !activeTarget.empty() || pollIntakeSuspended ||\n"
    "     pendingPulses!=0 || lastPoll+2!=fakeNow ||\n"
    "     backupWriteSawRelayOn || backupWriteSawLedOn ||\n"
    "     markerOpenSawRelayOn || markerOpenSawLedOn) return 22;\n"
    "  const std::string prePollMarker=LittleFS.files[\"/pollpulse.fault\"];\n"
    "  if(prePollMarker.find(\"COIN_INGRESS_UNRESOLVED\")==std::string::npos ||\n"
    "     prePollMarker.find(\"pulses=1\")==std::string::npos) return 24;\n\n"
    "  // Two ISR edges after the final quiet sample must retain modulo count across wrap.\n"
    "  resetState();\n"
    "  coinEdgeSequence=0xFFFFFFFEUL;\n"
    "  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;\n"
    "  injectAfterDrainEdgeCount=2;\n"
    "  injectAfterDrainEdge=true;\n"
    "  loop();\n"
    "  if(pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||\n"
    "     !LittleFS.exists(\"/pollpulse.fault\") || relayOn || ledOn ||\n"
    "     insertMode || !activeTarget.empty() || pollIntakeSuspended ||\n"
    "     pendingPulses!=0 || coinEdgeSequence!=0U ||\n"
    "     lastHandledCoinEdgeSequence!=0U || lastPoll+2!=fakeNow) return 54;\n"
    "  const std::string wrappedPrePollMarker=LittleFS.files[\"/pollpulse.fault\"];\n"
    "  if(wrappedPrePollMarker.find(\"COIN_INGRESS_UNRESOLVED\")==std::string::npos ||\n"
    "     wrappedPrePollMarker.find(\"pulses=2\")==std::string::npos) return 55;\n"
    "  std::cout<<\"POLL_POST_DRAIN_MULTI_EDGE_ROLLOVER_DENY_PASS\\\\n\";\n\n"
    "  // Existing pulse-drain behavior remains intact for a pulse observed before poll.",
    1,
)


TIMING_MAIN = MAIN.replace(
    "int main(){",
    """int main(){
  resetState();
  fakeNow=1501U;
  pulseStart=1600;
  pulseEnd=1680;
  injectTimedPollPulse=true;
  loop();
  if(!timedPulseIsrInjected || pollCalls!=0 || pollStartAt!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine) return 47;
  const std::string timingMarker=LittleFS.files["/pollpulse.fault"];
  if(timingMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     timingMarker.find("pulses=1")==std::string::npos) return 49;
  std::cout<<"PHX_177_ORIGINAL_1501_1600_1680_PULSE_ABORTED_BEFORE_HTTP_PASS\\n";
  return 0;
""",
    1,
)


RELEASE_EDGE_MAIN = r"""
void resetReleaseEdgeState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  coinEdgeSequence=0; lastHandledCoinEdgeSequence=0;
  interruptAttached=true; attachedPin=4; attachedMode=FALLING; attachedIsr=coinEdgeISR;
  relayOn=false; ledOn=false; relayLevelHigh=false; ledLevelHigh=false;
  pollCalls=0; pollIntakeSuspended=false; journalRecoveryRequired=false;
  pendingReady=false; pendingPulses=0; pendingPostAttempted=false; fsReady=true;
  outputPolarityKnown=true; pinConfigSafe=true; controllerEnabled=true;
  coinEnabled=true; relayEnabled=true; ledEnabled=true; insertMode=true;
  runCoinActiveLow=true; runRelayActiveHigh=true; runLedActiveHigh=true;
  runCoinPin=4; runRelayPin=26; runLedPin=2; activeTarget="target-01";
  pollReleaseEdgeInjected=false; pollReleaseEdgeSawRelayOff=false;
  pollReleaseRelayEnergizedBeforeLatch=false; pollReleaseRelayClearedBeforeLatch=false;
  injectDuringPollRelease=false; injectDuringPollReleaseAtRelayWrite=false;
}
int main(){
  // This isolated output-gate build does not use the poll-drain hook.
  (void)injectAfterDrainEdge;
  // Isolate the output gate with a previously valid positive local state.
  // The poll response itself remains default-deny in the production sketch.
  resetReleaseEdgeState();
  pollIntakeSuspended=true;
  applyOutputs();
  pollIntakeSuspended=false;
  pollCalls=1;
  injectDuringPollRelease=true;
  applyOutputs();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff ||
     pollReleaseRelayEnergizedBeforeLatch || !pollReleaseRelayClearedBeforeLatch ||
     relayOn || ledOn || journalRecoveryRequired ||
     coinEdgeSequence==lastHandledCoinEdgeSequence) return 52;
  std::cout<<"POLL_RELEASE_LED_WRITE_ISR_EDGE_BLOCKS_RELAY_PASS\n";

  resetReleaseEdgeState();
  pollIntakeSuspended=true;
  applyOutputs();
  pollIntakeSuspended=false;
  pollCalls=1;
  injectDuringPollReleaseAtRelayWrite=true;
  applyOutputs();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff ||
     !pollReleaseRelayEnergizedBeforeLatch || !pollReleaseRelayClearedBeforeLatch ||
     relayOn || ledOn || journalRecoveryRequired ||
     coinEdgeSequence==lastHandledCoinEdgeSequence) return 53;
  std::cout<<"POLL_RELEASE_RELAY_WRITE_ISR_EDGE_DEASSERTED_PASS\n";
  return 0;
}
"""


def compile_and_run(code, board, expected=0, label="normal"):
    with tempfile.TemporaryDirectory(prefix="phx-poll-loop-") as folder:
        cpp=Path(folder)/"poll_loop.cpp"
        binary=Path(folder)/"poll_loop"
        cpp.write_text(code,encoding="utf-8")
        built=subprocess.run(
            ["g++","-std=c++17","-Wall","-Wextra","-Werror",
             "-Wno-unused-parameter",str(cpp),"-o",str(binary)],
            capture_output=True,text=True,timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board} {label}: compile failed:\n{built.stderr[-3000:]}")
        ran=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        if ran.returncode!=expected:
            raise RuntimeError(
                f"{board} {label}: expected exit {expected}, got {ran.returncode}\n"
                f"stdout={ran.stdout}\nstderr={ran.stderr}"
            )
        return ran.stdout.strip()

POLL_SAFETY_PARITY = (
    "coinEdgeISR",
    "snapshotCoinEdgeSequence",
    "boundedCoinDebounceMs",
    "canStartPoll",
    "applyOutputs",
    "beginPollWindow",
    "sampleCoinPulseEdge",
    "latchPollPulseFault",
    "quarantineCoinIngressTransition",
    "handlePollDrainAbortAfterSample",
    "reconcileUnobservedCoinEdges",
)


def poll_safety_helpers():
    helpers = {}
    for board, path in BOARDS.items():
        source = path.read_text(encoding="utf-8")
        helpers[board] = {}
        for name in POLL_SAFETY_PARITY:
            body = extract_function(source, name)
            if not body:
                raise AssertionError(f"{board}: missing shared poll-safety helper {name}")
            # Ignore formatting-only changes; comments and executable tokens remain
            # part of the comparison so safety intent cannot drift silently.
            helpers[board][name] = " ".join(body.split())
    return helpers


def poll_safety_parity_mismatches(helpers):
    reference = helpers["ESP8266"]
    candidate = helpers["ESP32"]
    return [
        name for name in POLL_SAFETY_PARITY
        if not reference.get(name) or reference.get(name) != candidate.get(name)
    ]


def verify_poll_safety_board_parity():
    helpers = poll_safety_helpers()
    mismatches = poll_safety_parity_mismatches(helpers)
    if mismatches:
        raise SystemExit(
            "POLL_SAFETY_BOARD_PARITY_FAIL: " + ", ".join(mismatches)
        )
    print(
        f"POLL_SAFETY_BOARD_PARITY_PASS {len(POLL_SAFETY_PARITY)}/"
        f"{len(POLL_SAFETY_PARITY)} normalized helpers"
    )

    # Failure-inject a fail-open ESP32 drift in the persistent-fault output
    # gate and prove the parity guard detects it before either board is built.
    mutated = {
        board: dict(board_helpers)
        for board, board_helpers in helpers.items()
    }
    marker = "!journalRecoveryRequired"
    apply_outputs = mutated["ESP32"]["applyOutputs"]
    if marker not in apply_outputs:
        raise AssertionError("ESP32 applyOutputs parity mutation anchor missing")
    mutated["ESP32"]["applyOutputs"] = apply_outputs.replace(
        marker, "journalRecoveryRequired", 1
    )
    if not poll_safety_parity_mismatches(mutated):
        raise SystemExit(
            "POLL_SAFETY_BOARD_PARITY_MUTATION_SURVIVED: "
            "ESP32 applyOutputs lost journal-fault deny guard"
        )
    print(
        "POLL_SAFETY_BOARD_PARITY_MUTATION_REJECTED "
        "ESP32_applyOutputs_journal_fault_guard"
    )


verify_poll_safety_board_parity()


for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    edge_decl=source.find("volatile uint32_t coinEdgeSequence")
    edge_isr=min(
        (pos for pos in (
            source.find("void ICACHE_RAM_ATTR coinEdgeISR"),
            source.find("void IRAM_ATTR coinEdgeISR"),
        ) if pos >= 0),
        default=-1,
    )
    if edge_decl < 0 or edge_isr < 0 or edge_decl > edge_isr:
        raise AssertionError(f"{board}: coinEdgeSequence must be declared before coinEdgeISR")
    loop=extract_function(source, "loop")
    write=extract_function(source, "writeLogical")
    output=extract_function(source, "applyOutputs")
    idle=extract_function(source, "coinLineIdle")
    can_start=extract_function(source, "canStartPoll")
    quiet=extract_function(source, "coinLineQuietAfterInhibit")
    begin=extract_function(source, "beginPollWindow")
    accept=extract_function(source, "acceptPollResponse")
    isr=extract_function(source, "coinEdgeISR")
    snapshot=extract_function(source, "snapshotCoinEdgeSequence")
    configure=extract_function(source, "configureRuntimePins")
    write_fault=extract_function(source, "writePollPulseFaultMarker")
    load_fault=extract_function(source, "loadPollPulseFaultLatch")
    latch_fault=extract_function(source, "latchPollPulseFault")
    quarantine=extract_function(source, "quarantineCoinIngressTransition")
    init_store=extract_function(source, "initPendingStore")
    sample=extract_function(source, "sampleCoinPulseEdge")
    drain_abort=extract_function(source, "handlePollDrainAbortAfterSample")
    reconcile=extract_function(source, "reconcileUnobservedCoinEdges")
    handle=extract_function(source, "handleCoinPostResponse")

    def assemble(loop_source=loop,output_source=output,quiet_source=quiet,accept_source=accept,
                 configure_source=configure,isr_source=isr,write_fault_source=write_fault,
                 load_fault_source=load_fault,latch_fault_source=latch_fault,init_store_source=init_store,
                 begin_source=begin,sample_source=sample,main_source=MAIN,reconcile_source=reconcile,
                 handle_source=handle,drain_abort_source=drain_abort,quarantine_source=quarantine):
        board_define = "#define TARGET_ESP32\n" if board=="ESP32" else "#define ESP8266\n"
        return (board_define+STUBS+isr_source+snapshot+write+output_source+idle+can_start+
                quiet_source+begin_source+write_fault_source+
                load_fault_source+latch_fault_source+quarantine_source+configure_source+accept_source+reconcile_source+init_store_source+SUPPORT+handle_source+sample_source+drain_abort_source+loop_source+main_source)

    print(board,compile_and_run(assemble(),board,0,"exact-source"))
    print(board,compile_and_run(assemble(main_source=RELEASE_EDGE_MAIN),board,0,
                                "poll-release-output-interlock"))
    timing_output=compile_and_run(assemble(main_source=TIMING_MAIN),board,0,
                                 "issue-177-original-1501-1600-1680-timing")
    if "PHX_177_ORIGINAL_1501_1600_1680_PULSE_ABORTED_BEFORE_HTTP_PASS" not in timing_output:
        raise AssertionError(f"{board}: exact #177 timing marker missing")
    print(f"{board} PHX_177_ORIGINAL_1501_1600_1680_TIMING_PASS")
    unsafe_timing_loop=loop.replace(
        "const bool pollWindowReady=beginPollWindow();",
        "const bool pollWindowReady=true;",
        1,
    )
    if unsafe_timing_loop==loop:
        raise AssertionError(f"{board}: #177 pre-poll inhibit mutation anchor missing")
    compile_and_run(assemble(loop_source=unsafe_timing_loop,main_source=TIMING_MAIN),
                    board,47,"issue-177-missing-prepoll-inhibit")
    print(f"{board} MUTATION_REJECTED issue-177-missing-prepoll-inhibit expected_exit=47")
    non_wrap_safe_loop=loop.replace(
        "latchPollPulseFault(pollEdgeEnd-pollEdgeStart);",
        "latchPollPulseFault(pollEdgeEnd>pollEdgeStart ? pollEdgeEnd-pollEdgeStart : 0U);",
        1,
    )
    if non_wrap_safe_loop==loop:
        raise AssertionError(f"{board}: poll-edge wrap mutation anchor missing")
    compile_and_run(assemble(loop_source=non_wrap_safe_loop),board,50,
                    "non-wrap-safe-poll-edge-delta")
    print(f"{board} MUTATION_REJECTED non-wrap-safe-poll-edge-delta expected_exit=50")
    single_edge_loop=loop.replace(
        "latchPollPulseFault(pollEdgeEnd-pollEdgeStart);",
        "latchPollPulseFault(1U);",
        1,
    )
    if single_edge_loop==loop:
        raise AssertionError(f"{board}: exact poll-edge count mutation anchor missing")
    compile_and_run(assemble(loop_source=single_edge_loop),board,51,
                    "single-edge-poll-delta")
    print(f"{board} MUTATION_REJECTED single-edge-poll-delta expected_exit=51")
    idle_fault_shortcut = quarantine.replace(
        "  if(journalRecoveryRequired){",
        "  if(lineIdle && unhandledEdges==0U) return true;\n  if(journalRecoveryRequired){",
        1,
    )
    if idle_fault_shortcut == quarantine:
        raise AssertionError(f"{board}: journal-fault idle-line mutation anchor missing")
    compile_and_run(assemble(quarantine_source=idle_fault_shortcut),board,48,
                    "journal-fault-idle-line-shortcut")
    print(f"{board} MUTATION_REJECTED journal-fault-idle-line-shortcut")
    edge_hook = begin.replace(
        "return coinLineQuietAfterInhibit();",
        "if(coinLineQuietAfterInhibit()){ if(injectAfterDrainEdge){ coinEdgeSequence++; injectAfterDrainEdge=false; } return true; } return false;",
        1,
    )
    if edge_hook == begin:
        raise AssertionError(f"{board}: missing post-drain edge injection point")
    compile_and_run(assemble(begin_source=edge_hook,main_source=RACE_MAIN),board,0,
                    "edge-after-drain-before-snapshot")
    print(f"{board} POLL_EDGE_SNAPSHOT_RACE_PASS")
    single_post_drain_edge_loop = loop.replace(
        "latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart);",
        "latchPollPulseFault(1U);",
        1,
    )
    if single_post_drain_edge_loop == loop:
        raise AssertionError(f"{board}: post-drain exact-edge-count mutation anchor missing")
    compile_and_run(
        assemble(loop_source=single_post_drain_edge_loop,begin_source=edge_hook,main_source=RACE_MAIN),
        board,55,"single-edge-post-drain-count"
    )
    print(f"{board} MUTATION_REJECTED single-edge-post-drain-count expected_exit=55")
    release_on_abort = drain_abort.replace(
        "if(!coinLineIdle()) return;",
        "pollDrainAbortedOnActiveLine=false; pollIntakeSuspended=false; applyOutputs(); return;",
        1,
    )
    if release_on_abort == drain_abort:
        raise AssertionError(f"{board}: drain-abort release mutation anchor missing")
    compile_and_run(assemble(drain_abort_source=release_on_abort),board,34,"release-while-active-drain-line")
    print(f"{board} MUTATION_REJECTED release-while-active-drain-line")
    pre_poll_guard = loop.find("if(pollEdgeAfterDrain!=pollEdgeStart)")
    poll_call = loop.find('String r=post("poll")')
    if pre_poll_guard < 0 or poll_call < 0 or pre_poll_guard > poll_call:
        raise AssertionError(f"{board}: pre-poll edge guard must precede HTTP poll")

    begin_poll = loop.find("const bool pollWindowReady=beginPollWindow();")
    drain_snapshot = loop.find("const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();", begin_poll)
    if begin_poll < 0 or drain_snapshot < begin_poll or pre_poll_guard < drain_snapshot:
        raise AssertionError(f"{board}: ISR snapshot must follow either drain outcome before branching")
    poll_guard_removed = loop.replace(
        "const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();",
        "const uint32_t pollEdgeAfterDrain=pollEdgeStart;",
        1,
    )
    if poll_guard_removed == loop:
        raise AssertionError(f"{board}: missing pre-poll edge-abort guard")
    compile_and_run(assemble(loop_source=poll_guard_removed,begin_source=edge_hook,main_source=RACE_MAIN),
                    board,25,"missing-drain-abort-edge-reconciliation")
    print(f"{board} MUTATION_REJECTED missing-pre-poll-edge-abort")
    mutations=(
      ("remove-beginPollWindow",loop.replace("const bool pollWindowReady=beginPollWindow();","const bool pollWindowReady=true;",1),output,quiet,accept),
      ("ignore-pollIntakeSuspended",loop,output.replace(" && !pollIntakeSuspended","",1),quiet,accept),
      ("shorten-quiet-window-to-249ms",loop,output,quiet.replace("pulseTrainQuietMs=250UL;","pulseTrainQuietMs=249UL;",1),accept),
      ("keep-insert-enabled-after-poll",loop,output,quiet,accept.replace("insertMode=false;","insertMode=true;",1)),
      ("retain-stale-target-after-poll",loop,output,quiet,accept.replace('activeTarget="";','activeTarget="stale-target";',1)),
    )
    journal_fault_guard_removed = output.replace("!journalRecoveryRequired && ", "", 1)
    if journal_fault_guard_removed == output:
        raise AssertionError(f"{board}: journal-recovery output guard mutation did not apply")
    compile_and_run(assemble(output_source=journal_fault_guard_removed),board,48,
                    "ignore-journal-recovery-output-deny")
    print(f"{board} MUTATION_REJECTED ignore-journal-recovery-output-deny expected_exit=48")

    for name,mut_loop,mut_output,mut_quiet,mut_accept in mutations:
        if name=="remove-beginPollWindow" and mut_loop==loop:
            raise AssertionError(f"{board}: poll-window call mutation did not apply")
        if name=="ignore-pollIntakeSuspended" and mut_output==output:
            raise AssertionError(f"{board}: output-gate mutation did not apply")
        if name=="shorten-quiet-window-to-249ms" and mut_quiet==quiet:
            raise AssertionError(f"{board}: quiet-window mutation did not apply")
        if name=="keep-insert-enabled-after-poll" and mut_accept==accept:
            raise AssertionError(f"{board}: insert-state mutation did not apply")
        if name=="retain-stale-target-after-poll" and mut_accept==accept:
            raise AssertionError(f"{board}: stale-target mutation did not apply")
        compile_and_run(assemble(mut_loop,mut_output,mut_quiet,mut_accept),board,10,name)
        print(f"{board} MUTATION_REJECTED {name} expected_exit=10")

    extra_mutations=(
      ("remove-edge-interrupt-attachment",loop,output,quiet,accept,
       configure.replace("attachInterrupt(digitalPinToInterrupt(runCoinPin),coinEdgeISR,runCoinActiveLow?FALLING:RISING);",""),isr,write_fault,load_fault,latch_fault,init_store,12),
      ("ignore-poll-edge-delta",loop.replace("if(pollEdgeEnd!=pollEdgeStart){","if(false){",1),output,quiet,accept,
       configure,isr,write_fault,load_fault,latch_fault,init_store,12),
      ("no-op-coin-isr",loop,output,quiet,accept,configure,
       isr.replace("coinEdgeSequence++;","coinEdgeSequence+=0;",1),write_fault,load_fault,latch_fault,init_store,12),
      ("remove-fault-marker-write",loop,output,quiet,accept,configure,isr,
       write_fault,load_fault,latch_fault.replace("const bool littleFsPersisted=writePollPulseFaultMarker(pulseEdges);","const bool littleFsPersisted=false;",1),init_store,12),
      ("defer-fault-output-inhibit",loop,output,quiet,accept,configure,isr,write_fault,load_fault,
       latch_fault.replace("  // Deassert the physical outputs before any flash persistence can block.\n  applyOutputs();\n  const bool backupPersisted=writePollFaultBackup(pulseEdges);",
                           "  const bool backupPersisted=writePollFaultBackup(pulseEdges);",1),
       init_store,23),
      ("remove-boot-fault-latch",loop,output,quiet,accept,configure,isr,write_fault,
       load_fault.replace("if(backupHold || littleFsHold){","if(backupHold && littleFsHold){",1),
       latch_fault,init_store,15),
    )
    for name,ml,mo,mq,ma,mc,mi,mw,mload,mlatch,ms,expected in extra_mutations:
        if name=="remove-edge-interrupt-attachment" and mc==configure:
            raise AssertionError(f"{board}: interrupt-attachment mutation did not apply")
        if name=="ignore-poll-edge-delta" and ml==loop:
            raise AssertionError(f"{board}: poll-edge-delta mutation did not apply")
        if name=="no-op-coin-isr" and mi==isr:
            raise AssertionError(f"{board}: ISR mutation did not apply")
        if name=="remove-fault-marker-write" and mlatch==latch_fault:
            raise AssertionError(f"{board}: fault-marker mutation did not apply")
        if name=="defer-fault-output-inhibit" and mlatch==latch_fault:
            raise AssertionError(f"{board}: pre-persistence output-inhibit mutation did not apply")
        if name=="remove-boot-fault-latch" and mload==load_fault:
            raise AssertionError(f"{board}: boot-latch mutation did not apply")
        compile_and_run(assemble(ml,mo,mq,ma,mc,mi,mw,mload,mlatch,ms),board,expected,name)
        print(f"{board} MUTATION_REJECTED {name} expected_exit={expected}")

    # Prove the release-window ISR edge is caught by the ordinary sample path
    # when it arrives after the post-poll snapshot but before the loop's final sample.
    missing_release_sample = loop.replace(
        "sampleCoinPulseEdge(active);",
        "(void)active; // mutation: final post-poll sample omitted",
        1,
    )
    if missing_release_sample == loop:
        raise AssertionError(f"{board}: final post-poll sample mutation did not apply")
    compile_and_run(assemble(loop_source=missing_release_sample),board,29,
                    "skip-poll-release-edge-sample")
    print(f"{board} MUTATION_REJECTED skip-poll-release-edge-sample")

    pre_poll_edge_guard_removed = loop.replace(
        "if(pollEdgeStart!=lastHandledCoinEdgeSequence){",
        "if(false){",
        1,
    )
    if pre_poll_edge_guard_removed == loop:
        raise AssertionError(f"{board}: pre-poll unobserved-edge guard mutation did not apply")
    compile_and_run(assemble(loop_source=pre_poll_edge_guard_removed),board,44,
                    "ignore-unobserved-edge-before-poll")
    print(f"{board} MUTATION_REJECTED ignore-unobserved-edge-before-poll")
    missing_coin_post_latch = reconcile.replace(
        "latchPollPulseFault((uint32_t)pendingPulses+unhandledEdges);",
        "// mutation: unresolved edge persistence omitted",
        1,
    )
    if missing_coin_post_latch == reconcile:
        raise AssertionError(f"{board}: coin-post persistence mutation did not apply")
    compile_and_run(assemble(reconcile_source=missing_coin_post_latch),board,45,
                    "missing-coin-post-edge-persistence")
    print(f"{board} MUTATION_REJECTED missing-coin-post-edge-persistence")

print("PHX-HARDWARE: poll-fault and coin-POST ISR reconciliation passed on ESP8266 and ESP32; no hardware evidence")
