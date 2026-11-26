"""Fake board state, persistence stubs and the exact-source insertion point.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_RUNTIME = r'''#include <cstdint>
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

static void emitCoinEdges(uint32_t count){
  while(count>0U){
    coinEdgeISR();
    count-=1U;
  }
}

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
'''
