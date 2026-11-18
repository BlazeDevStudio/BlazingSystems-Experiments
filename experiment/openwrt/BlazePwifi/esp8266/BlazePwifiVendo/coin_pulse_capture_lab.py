#!/usr/bin/env python3
"""PHX-HARDWARE exact-source pulse capture after poll-drain abort.

Compiles production coinLineIdle(), canStartPoll(), applyOutputs(),
coinLineQuietAfterInhibit(), beginPollWindow(), and sampleCoinPulseEdge()
from both ESP sketches. It verifies a pulse observed during the inhibit drain
is captured by the next normal loop sample and sent through savePending().
Host C++ with fake GPIO/time/storage only; no physical acceptance is claimed.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

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
struct FakeSerial { void println(const char*){} };
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
@@FUNCTIONS@@

static void resetState(uint32_t now=0,bool activeLow=true){
  fakeNow=now;runDebounceMs=40;lastEdge=0;
  pulseStart=0;pulseEnd=0;pulseEnabled=false;
  fsReady=true;journalRecoveryRequired=false;pendingReady=false;
  insertMode=true;lastCoin=false;runCoinActiveLow=activeLow;
  pollIntakeSuspended=false;pinConfigSafe=true;controllerEnabled=true;coinEnabled=true;
  ledEnabled=true;relayEnabled=true;runRelayActiveHigh=true;runLedActiveHigh=true;
  pendingPulses=0;pendingNonce.clear();pendingTarget.clear();activeTarget="target-01";
  relayOn=true;ledOn=true;saveCalls=0;nonceCalls=0;saveResult=true;
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
  if(pollIntakeSuspended || !relayOn || !ledOn)
    return fail(name,"abort did not restore normal sampling outputs");
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
static bool runSaveFailure(){
  resetState(100U);
  saveResult=false;
  sampleCoinPulseEdge(true);
  if(pendingPulses!=1 || saveCalls!=1 || fsReady || !pendingReady)
    return fail("save-failure","failed durable write did not disable filesystem/intake");
  if(relayOn || ledOn) return fail("save-failure","outputs remained enabled immediately after failed save");
  sampleCoinPulseEdge(false);
  fakeNow=200U;
  sampleCoinPulseEdge(true);
  if(saveCalls!=1 || pendingPulses!=1)
    return fail("save-failure","another pulse was accepted after failed persistence");
  return true;
}
static bool runDeniedGates(){
  for(int scenario=0;scenario<10;++scenario){
    resetState(141U);
    lastEdge=100U;
    bool active=true;
    switch(scenario){
      case 0:insertMode=false;break;
      case 1:fsReady=false;break;
      case 2:journalRecoveryRequired=true;break;
      case 3:pendingReady=true;break;
      case 4:activeTarget.clear();break;
      case 5:pendingPulses=20;break;
      case 6:pendingPulses=1;pendingTarget="other-target";break;
      case 7:lastCoin=true;break;
      case 8:active=false;break;
      case 9:fakeNow=140U;break; // exactly the configured debounce boundary
    }
    const uint8_t expected=scenario==5?20U:(scenario==6?1U:0U);
    sampleCoinPulseEdge(active);
    if(saveCalls!=0 || pendingPulses!=expected){
      std::cerr<<"FAIL deny-case-"<<scenario<<" saves="<<saveCalls
               <<" pulses="<<(unsigned)pendingPulses<<"\n";
      return false;
    }
  }
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
  std::cout<<"COIN_PULSE_CAPTURE_PASS "<<passed<<"/8 top-level scenarios\n";
  return 0;
}
'''

SIGNATURES = (
    "bool coinLineIdle(){",
    "bool canStartPoll(){",
    "void applyOutputs(){",
    "bool coinLineQuietAfterInhibit(){",
    "bool beginPollWindow(){",
    "void sampleCoinPulseEdge(bool active){",
)

def extract(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise RuntimeError(f"missing production function: {signature}")
    brace = source.find("{", start)
    depth = 0
    for pos in range(brace, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1]
    raise RuntimeError(f"unbalanced production function: {signature}")

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

def main():
    mutations = (
        ("missing-edge-latch", "lastCoin=active;", "",
         "sustained high level"),
        ("inclusive-debounce", "millis()-lastEdge>runDebounceMs",
         "millis()-lastEdge>=runDebounceMs", "deny-case-9"),
        ("missing-target-binding", "pendingTarget==activeTarget && ", "",
         "deny-case-6"),
        ("ignored-save-failure", "fsReady=false;\n        pendingReady=true;", "",
         "save-failure"),
        ("missing-immediate-output-inhibit", "applyOutputs();\n        Serial.println",
         "Serial.println", "outputs remained enabled immediately"),
    )
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
            functions = [extract(source, signature) for signature in SIGNATURES]
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source failure: {result.stderr or result.stdout}")
                continue
            if "COIN_PULSE_CAPTURE_PASS 8/8" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_COIN_PULSE_CAPTURE_PASS 8/8")
            for name, old, new, expected in mutations:
                index = SIGNATURES.index("void sampleCoinPulseEdge(bool active){")
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
