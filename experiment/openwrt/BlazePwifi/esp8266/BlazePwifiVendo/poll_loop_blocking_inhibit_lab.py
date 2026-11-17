#!/usr/bin/env python3
"""Execute the actual ESP loop() around the synchronous poll with bounded host I/O stubs.

The production loop, poll-window helpers, and output gate are extracted unchanged
from both sketches. Only Wi-Fi/HTTP/GPIO/filesystem edges are stubbed. This is
SIMULATED control-flow evidence, not electrical or physical coin-acceptor proof.
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
    pattern = r"\b(?:void|bool|uint16_t)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{"
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
#include <cstring>
#include <iostream>
#include <string>
static constexpr int HIGH=1, LOW=0, WL_CONNECTED=3;
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
};
static uint32_t fakeNow=2000;
static int pulseStart=-1, pulseEnd=-1;
static bool relayOn=false, ledOn=false;
static bool relayLevelHigh=false, ledLevelHigh=false;
static bool injectDuringHttp=false;
static int pollCalls=0, saveCalls=0;
static uint32_t pollStartAt=0, pollEndAt=0;
static bool pollStartRelayOn=true, pollStartSuspended=false;
static bool pollStartCoinIdle=false, pollEndRelayOn=true, pollEndSuspended=false;
static bool pollPulseObservedDuringHttp=false, pollPulseRelayOff=false, pollPulseSuspended=false;
bool insertMode=true, lastCoin=false;
bool pollIntakeSuspended=false, pinConfigSafe=true;
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
struct ConfigStub { char ssid[33]="test-ssid"; char pass[65]="test-pass"; } cfg;
int digitalRead(int) {
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
  }
  return String("");
}
bool acceptPollResponse(const String&){
  // The current Master contract is default-deny until CORE/QA approve the
  // authenticated producer/consumer vectors. A failed response clears stale
  // admission state; it never re-energizes the coin relay.
  insertMode=false;
  activeTarget.clear();
  return false;
}
"""

MAIN = r"""
void resetState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  relayOn=false; ledOn=false; relayLevelHigh=false; ledLevelHigh=false;
  injectDuringHttp=false; pollCalls=0; saveCalls=0;
  pollStartAt=0; pollEndAt=0; pollStartRelayOn=true; pollStartSuspended=false;
  pollStartCoinIdle=false; pollEndRelayOn=true; pollEndSuspended=false;
  pollPulseObservedDuringHttp=false; pollPulseRelayOff=false; pollPulseSuspended=false;
  insertMode=true; lastCoin=false; pollIntakeSuspended=false; pinConfigSafe=true;
  controllerEnabled=true; coinEnabled=true; relayEnabled=true; ledEnabled=true;
  setupApOn=false; runCoinActiveLow=true; runRelayActiveHigh=true; runLedActiveHigh=true;
  pendingReady=false; fsReady=true; journalRecoveryRequired=false; pendingPostAttempted=false;
  lastPoll=0; lastEdge=0; lastSend=0; configuredApSince=0;
  pendingPulses=0; runCoinPin=4; runLedPin=2; runRelayPin=26;
  maxWifiRetries=6; wifiFailures=0; runDebounceMs=40; runPulseGroupMs=400;
  activeTarget="target-01"; pendingTarget=""; pendingNonce="";
  applyOutputs();
}
bool recordedPulseState(){
  return pollCalls==0 && pendingPulses==1 && !pendingReady &&
         pendingTarget=="target-01" && pendingNonce=="nonce12345678" &&
         lastCoin && relayOn && !pollIntakeSuspended && saveCalls==1;
}
int main(){
  // Actual loop(): relay must be OFF before post("poll"), stay OFF for the
  // full 3.5 s blocking wait, and remain OFF after default-deny response.
  resetState();
  injectDuringHttp=true;
  loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollStartAt-2000<250 ||
     pollStartRelayOn || !pollStartSuspended || !pollStartCoinIdle ||
     pollEndAt-pollStartAt!=3500 || pollEndRelayOn || !pollEndSuspended ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     pollIntakeSuspended || relayOn || ledOn || insertMode ||
     !activeTarget.empty() || pendingPulses!=0 || lastPoll!=pollEndAt ||
     fakeNow!=pollEndAt+2) return 11;

  // A pulse observed during the inhibit/drain window cancels the poll and is
  // sampled by the same production loop after the temporary inhibit is lifted.
  resetState(); pulseStart=2050; pulseEnd=2130;
  loop();
  if(!recordedPulseState()) return 21;

  // The opposite input polarity follows the same cancellation path.
  resetState(); runCoinActiveLow=false; pulseStart=2200; pulseEnd=2280;
  loop();
  if(!recordedPulseState()) return 22;

  // A pulse beginning exactly at the 250 ms boundary must cancel polling.
  resetState(); pulseStart=2250; pulseEnd=2330;
  loop();
  if(!recordedPulseState()) return 23;

  // Existing pending or recovery state must prevent a poll and keep outputs OFF.
  resetState(); pendingReady=true; pendingPulses=1; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 31;
  resetState(); journalRecoveryRequired=true; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 32;
  resetState(); fsReady=false; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 33;

  std::cout<<"POLL_LOOP_INHIBIT_PASS 7/7 actual-loop scenarios; HTTP wait 3500 ms\n";
  std::cout<<"SIMULATED_ONLY=1 PHYSICAL_COIN_ACCEPTOR_VERIFIED=0 PHYSICAL_POWER_CUT_VERIFIED=0\n";
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

for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    loop=extract(source,"loop")
    write=extract(source,"writeLogical")
    output=extract(source,"applyOutputs")
    idle=extract(source,"coinLineIdle")
    can_start=extract(source,"canStartPoll")
    quiet=extract(source,"coinLineQuietAfterInhibit")
    begin=extract(source,"beginPollWindow")

    def assemble(loop_source=loop,output_source=output,quiet_source=quiet):
        return STUBS+write+output_source+idle+can_start+quiet_source+begin+SUPPORT+loop_source+MAIN

    print(board,compile_and_run(assemble(),board,0,"exact-source"))
    mutations=(
      ("remove-beginPollWindow",loop.replace("&& beginPollWindow()){","&& true){",1),output,quiet),
      ("ignore-pollIntakeSuspended",loop,output.replace(" && !pollIntakeSuspended","",1),quiet),
      ("shorten-quiet-window-to-249ms",loop,output,quiet.replace("pulseTrainQuietMs=250UL;","pulseTrainQuietMs=249UL;",1)),
    )
    for name,mut_loop,mut_output,mut_quiet in mutations:
        if name=="remove-beginPollWindow" and mut_loop==loop:
            raise AssertionError(f"{board}: poll-window call mutation did not apply")
        if name=="ignore-pollIntakeSuspended" and mut_output==output:
            raise AssertionError(f"{board}: output-gate mutation did not apply")
        if name=="shorten-quiet-window-to-249ms" and mut_quiet==quiet:
            raise AssertionError(f"{board}: quiet-window mutation did not apply")
        compile_and_run(assemble(mut_loop,mut_output,mut_quiet),board,11,name)
        print(f"{board} MUTATION_REJECTED {name} expected_exit=11")

print("PHX-HARDWARE: actual-loop host simulation passed on ESP8266 and ESP32; no hardware evidence")
