#!/usr/bin/env python3
"""Execute the actual ESP loop() around the synchronous poll with bounded host I/O stubs.

The production loop, poll-window helpers, output gate and default-deny
acceptPollResponse() are extracted unchanged from both sketches. Secondary
NVS/EEPROM helpers are stubbed here; poll_fault_dual_store_lab.py tests them
separately. This is SIMULATED control-flow evidence, not physical coin proof.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

def extract(source, name):
    pattern = r"\b(?:void|bool|uint16_t|uint32_t)\s+(?:(?:IRAM_ATTR|ICACHE_RAM_ATTR)\s+)?" + re.escape(name) + r"\s*\([^)]*\)\s*\{"
    match = re.search(pattern, source)
    if not match:
        raise AssertionError(f"missing production function: {name}")
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"unbalanced production function: {name}")

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
static bool injectAfterDrainEdge=false;
static bool injectDuringDrainAbort=false;
static int drainAbortReadCount=0;
static bool drainAbortInjected=false;
static bool drainAbortSawRelayOn=false;
static bool drainAbortSampleSawRelayOn=false;
static bool drainAbortReenabledBeforeLatch=false;
static int pollCalls=0, saveCalls=0;
static uint32_t pollStartAt=0, pollEndAt=0;
static bool pollStartRelayOn=true, pollStartSuspended=false;
static bool pollStartCoinIdle=false, pollEndRelayOn=true, pollEndSuspended=false;
static bool pollPulseObservedDuringHttp=false, pollPulseRelayOff=false, pollPulseSuspended=false;
bool insertMode=true, lastCoin=false;
bool pollIntakeSuspended=false, pinConfigSafe=true;
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
  const bool active=pulseStart>=0 &&
    fakeNow>=(uint32_t)pulseStart && fakeNow<(uint32_t)pulseEnd;
  if(runCoinActiveLow) return active?LOW:HIGH;
  return active?HIGH:LOW;
}
void digitalWrite(int pin,int level) {
  if(pin==runRelayPin) {
    relayLevelHigh=(level==HIGH);
    relayOn=(level==(runRelayActiveHigh?HIGH:LOW));
  }
  if(pin==runLedPin) {
    ledLevelHigh=(level==HIGH);
    ledOn=(level==(runLedActiveHigh?HIGH:LOW));
  }
  // During a drain-abort injection, any re-energized output before the sticky
  // recovery latch is set proves that the poll inhibit was released too early.
  if(injectDuringDrainAbort && drainAbortInjected && !journalRecoveryRequired &&
     (relayOn || ledOn)) drainAbortReenabledBeforeLatch=true;
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
bool canAttemptCoinPost(){ return false; }
bool markPendingPostAttempt(){ return false; }
bool coinPostDispositionVerified(const String&,const String&,const String&,uint8_t){ return false; }
bool pollJsonTopLevelTrue(const String&,const char*){ return false; }
bool clearPending(){ return false; }
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
         attachedMode==(runCoinActiveLow?FALLING:RISING)) attachedIsr();
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
  return String("");
}
"""

MAIN = r"""
void resetState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  coinEdgeSequence=0; interruptAttached=false; attachedPin=-1; attachedMode=-1; attachedIsr=nullptr;
  fakeShortWrite=false; fakeCorruptReadback=false; fakeOpenFail=false; LittleFS.files.clear();
  relayOn=false; ledOn=false; backupWriteSawRelayOn=false; backupWriteSawLedOn=false;
  markerOpenSawRelayOn=false; markerOpenSawLedOn=false; relayLevelHigh=false; ledLevelHigh=false;
  injectDuringHttp=false; injectAfterDrainEdge=false; injectDuringDrainAbort=false;
  drainAbortReadCount=0; drainAbortInjected=false; drainAbortSawRelayOn=false;
  drainAbortSampleSawRelayOn=false; drainAbortReenabledBeforeLatch=false;
  pollCalls=0; saveCalls=0;
  pollStartAt=0; pollEndAt=0; pollStartRelayOn=true; pollStartSuspended=false;
  pollStartCoinIdle=false; pollEndRelayOn=true; pollEndSuspended=false;
  pollPulseObservedDuringHttp=false; pollPulseRelayOff=false; pollPulseSuspended=false;
  insertMode=true; lastCoin=false; pollIntakeSuspended=false; pinConfigSafe=true; outputPolarityKnown=true;
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
         lastCoin && relayOn && !pollIntakeSuspended && saveCalls==1;
}
int main(){
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

  // Existing pulse-drain behavior remains intact for a pulse observed before poll.
  resetState(); pulseStart=2050; pulseEnd=2130; loop();
  if(!recordedPulseState()) return 31;
  resetState(); runCoinActiveLow=false; configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  pulseStart=2200; pulseEnd=2280; loop();
  if(!recordedPulseState()) return 32;
  resetState(); pulseStart=2250; pulseEnd=2330; loop();
  if(!recordedPulseState()) return 33;

  // Existing pending/recovery/FS guards remain fail-closed.
  resetState(); pendingReady=true; pendingPulses=1; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 41;
  resetState(); journalRecoveryRequired=true; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 42;
  resetState(); fsReady=false; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 43;

  std::cout<<"POLL_BLOCKED_EDGE_FAULT_PASS 7/7 fault-marker scenarios; existing poll-loop guards 7/7\n";
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
    "  // Existing pulse-drain behavior remains intact for a pulse observed before poll.",
    1,
)


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
    loop=extract(source,"loop")
    write=extract(source,"writeLogical")
    output=extract(source,"applyOutputs")
    idle=extract(source,"coinLineIdle")
    can_start=extract(source,"canStartPoll")
    quiet=extract(source,"coinLineQuietAfterInhibit")
    begin=extract(source,"beginPollWindow")
    accept=extract(source,"acceptPollResponse")
    isr=extract(source,"coinEdgeISR")
    snapshot=extract(source,"snapshotCoinEdgeSequence")
    configure=extract(source,"configureRuntimePins")
    write_fault=extract(source,"writePollPulseFaultMarker")
    load_fault=extract(source,"loadPollPulseFaultLatch")
    latch_fault=extract(source,"latchPollPulseFault")
    init_store=extract(source,"initPendingStore")
    sample=extract(source,"sampleCoinPulseEdge")

    def assemble(loop_source=loop,output_source=output,quiet_source=quiet,accept_source=accept,
                 configure_source=configure,isr_source=isr,write_fault_source=write_fault,
                 load_fault_source=load_fault,latch_fault_source=latch_fault,init_store_source=init_store,
                 begin_source=begin,sample_source=sample,main_source=MAIN):
        board_define = "#define TARGET_ESP32\n" if board=="ESP32" else "#define ESP8266\n"
        return (board_define+STUBS+isr_source+snapshot+write+output_source+idle+can_start+
                quiet_source+begin_source+configure_source+accept_source+write_fault_source+
                load_fault_source+latch_fault_source+init_store_source+SUPPORT+sample_source+loop_source+main_source)

    print(board,compile_and_run(assemble(),board,0,"exact-source"))
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
    release_on_abort = begin.replace(
        "return coinLineQuietAfterInhibit();",
        "if(coinLineQuietAfterInhibit()) return true;\n  pollIntakeSuspended=false;\n  applyOutputs();\n  return false;",
        1,
    )
    if release_on_abort == begin:
        raise AssertionError(f"{board}: drain-abort release mutation anchor missing")
    compile_and_run(assemble(begin_source=release_on_abort),board,25,"release-before-drain-abort-reconciliation")
    print(f"{board} MUTATION_REJECTED release-before-drain-abort-reconciliation")
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
    late_snapshot_loop = loop.replace(
        "    const uint32_t pollEdgeStart=snapshotCoinEdgeSequence();\n    const bool pollWindowReady=beginPollWindow();\n    // Reconcile ISR edges for both drain outcomes while outputs remain inhibited.\n    const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();",
        "    const bool pollWindowReady=beginPollWindow();\n    const uint32_t pollEdgeStart=snapshotCoinEdgeSequence();\n    const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();",
        1,
    )
    if late_snapshot_loop == loop:
        raise AssertionError(f"{board}: late-snapshot mutation did not apply")
    compile_and_run(assemble(loop_source=late_snapshot_loop,begin_source=edge_hook,main_source=RACE_MAIN),
                    board,25,"late-snapshot-regression")
    print(f"{board} MUTATION_REJECTED late-poll-edge-snapshot")
    mutations=(
      ("remove-beginPollWindow",loop.replace("if(beginPollWindow()){","if(true){",1),output,quiet,accept),
      ("ignore-pollIntakeSuspended",loop,output.replace(" && !pollIntakeSuspended","",1),quiet,accept),
      ("shorten-quiet-window-to-249ms",loop,output,quiet.replace("pulseTrainQuietMs=250UL;","pulseTrainQuietMs=249UL;",1),accept),
      ("keep-insert-enabled-after-poll",loop,output,quiet,accept.replace("insertMode=false;","insertMode=true;",1)),
      ("retain-stale-target-after-poll",loop,output,quiet,accept.replace('activeTarget="";','activeTarget="stale-target";',1)),
    )
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

print("PHX-HARDWARE: poll-fault output inhibition before secondary-store and LittleFS persistence passed on ESP8266 and ESP32; no hardware evidence")
