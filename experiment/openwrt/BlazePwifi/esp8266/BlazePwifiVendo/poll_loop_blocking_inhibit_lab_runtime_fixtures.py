"""Host C++ runtime stubs for the blocking-poll regression lab.

Keep fake I/O semantics separate from scenario programs so persistence and
GPIO behavior can be reviewed without scrolling through every test case.
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
static bool coinInterruptAttached=false;
// Keep legacy scenario assertions bound to the production interrupt state.
static bool &interruptAttached=coinInterruptAttached;
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
// This loop fixture observes re-entry into the sticky latch. The real EEPROM/NVS
// first-writer implementation is source-extracted separately by the dual-store lab.
static uint32_t backupFirstFaultPulseEdges=0;
static unsigned backupWriteAttempts=0;
void observeBackupWrite();
bool writePollFaultBackup(uint32_t pulseEdges){
  observeBackupWrite();
  ++backupWriteAttempts;
  if(backupFirstFaultPulseEdges==0U) backupFirstFaultPulseEdges=pulseEdges;
  return backupFirstFaultPulseEdges!=0U;
}
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
static bool allowCoinPost=false, injectDuringCoinPost=false, injectDuringClear=false;
static unsigned injectDuringCoinPostEdgeCount=1;
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
static bool pollHttpReturned=false, pollPostHttpSampleObserved=false;
static bool pollPostHttpFaultLatchedBeforeSample=false;
static bool pollPostHttpMarkerPresentBeforeSample=false;
static bool pollPostHttpOutputsOffBeforeSample=false;
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
  String ssid="test-ssid", pass="test-pass", key="";
#else
  char ssid[33]="test-ssid"; char pass[65]="test-pass"; char key[33]="";
#endif
} cfg;
void clearControllerKey(){
#ifdef TARGET_ESP32
  cfg.key.clear();
#else
  cfg.key[0]='\0';
#endif
}
bool controllerKeyEmpty(){
#ifdef TARGET_ESP32
  return cfg.key.isEmpty();
#else
  return cfg.key[0]=='\0';
#endif
}
int digitalRead(int) {
  // Capture fault durability before the ordinary post-HTTP sample can mask a missing poll-edge reconciliation.
  if(pollHttpReturned && !pollPostHttpSampleObserved){
    pollPostHttpSampleObserved=true;
    pollPostHttpFaultLatchedBeforeSample=journalRecoveryRequired;
    pollPostHttpMarkerPresentBeforeSample=LittleFS.exists("/pollpulse.fault");
    pollPostHttpOutputsOffBeforeSample=!relayOn && !ledOn;
  }
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
bool clearPending(){
  ++clearCalls;
  pendingPulses=0;
  pendingReady=false;
  pendingPostAttempted=false;
  pendingTarget.clear();
  pendingNonce.clear();
  if(injectDuringClear){ coinEdgeISR(); injectDuringClear=false; }
  return true;
}
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
    // Simulate the production 3.5-second blocked poll request. The default
    // stub returns hostile positive data; the lab derives an empty-response
    // variant to exercise the HTTPClient transport-timeout result as well.
    pollEndAt=fakeNow;
    pollEndRelayOn=relayOn;
    pollEndSuspended=pollIntakeSuspended;
    pollHttpReturned=true;
    // Deliberately hostile positive response: the extracted production
    // acceptPollResponse() must still deny it until CORE/QA approve the contract.
    return String("{\"ok\":true,\"insert\":true,\"target\":\"spoof-target\"}");
  }
  if(action=="coin"){
    ++coinPostCalls;
    if(injectDuringCoinPost){
      const unsigned edgeCount=injectDuringCoinPostEdgeCount;
      injectDuringCoinPost=false;
      for(unsigned edge=0; edge<edgeCount; ++edge){
        if(interruptAttached && attachedIsr && attachedPin==runCoinPin &&
           attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr();
      }
    }
    fakeNow+=3500UL;
    return String("{\"ok\":true}");
  }
  return String("");
}
"""

