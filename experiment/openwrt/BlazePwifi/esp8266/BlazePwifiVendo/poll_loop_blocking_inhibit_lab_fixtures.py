"""C++ fixture snippets and scenario builders for the blocking-poll host lab.

Keep embedded C++ support and scenario programs separate from Python orchestration.
These fixtures are source-extracted from the current firmware by the sibling lab.
"""

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
// Test-first: two post-drain ISR edges must retain their modulo delta across uint32 wrap.
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


def post_drain_rollover_main(active_low: bool) -> str:
    """Build the same rollover regression for either physical input polarity."""
    polarity = "true" if active_low else "false"
    interrupt_mode = "FALLING" if active_low else "RISING"
    scenario = "ACTIVE_LOW" if active_low else "ACTIVE_HIGH"
    failure_code = 59 if active_low else 56
    return MAIN[:MAIN.index("int main(){")] + rf"""
int main(){{
  resetState();
  runCoinActiveLow={polarity};
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectAfterDrainEdgeCount=2;
  injectAfterDrainEdge=true;
  loop();
  if(attachedMode!={interrupt_mode} || pollCalls!=0 || pollStartAt!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pendingPulses!=0U ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U ||
     lastPoll+2!=fakeNow) return {failure_code};
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=2")==std::string::npos) return {failure_code};
  std::cout<<"POLL_POST_DRAIN_{scenario}_MULTI_EDGE_ROLLOVER_DENY_PASS\\n";
  return 0;
}}
"""


ACTIVE_HIGH_MISSED_SAMPLE_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDrainAbortWithoutIsr=true;
  injectDrainAbortPulseEndsBeforeSample=true;
  loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine ||
     pendingPulses!=0U || saveCalls!=0 ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 57;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return 57;
  std::cout<<"POLL_ABORT_ACTIVE_HIGH_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS\\n";
  return 0;
}
"""


ACTIVE_LOW_MISSED_SAMPLE_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  runCoinActiveLow=true;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDrainAbortWithoutIsr=true;
  injectDrainAbortPulseEndsBeforeSample=true;
  loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine ||
     pendingPulses!=0U || saveCalls!=0 ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 58;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return 58;
  std::cout<<"POLL_ABORT_ACTIVE_LOW_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS\\n";
  return 0;
}
"""


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
