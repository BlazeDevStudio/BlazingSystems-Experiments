#!/usr/bin/env python3
"""PHX-HARDWARE exact-source poll-inhibit drain-window lab.

Compiles production coinLineIdle(), canStartPoll(), applyOutputs(),
coinLineQuietAfterInhibit(), and beginPollWindow() from both ESP sketches.
Injects 30–100 ms coin pulses during the inhibit-settle interval.
Host C++ only; no physical relay, acceptor, or power-cut evidence.
"""
from pathlib import Path
import subprocess
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
static int pulseStart=-1, pulseEnd=-1;
static constexpr int LOW=0, HIGH=1;
static bool fsReady=true, journalRecoveryRequired=false, pendingReady=false;
bool outputPolarityKnown=true;
static uint8_t pendingPulses=0;
static bool runCoinActiveLow=true, pollIntakeSuspended=false;
static int runCoinPin=4, runRelayPin=5, runLedPin=2;
static bool pinConfigSafe=true, controllerEnabled=true, coinEnabled=true, insertMode=true;
static bool ledEnabled=true, relayEnabled=true, runRelayActiveHigh=true, runLedActiveHigh=true;
static String activeTarget="target-01";
static bool relayOn=true, ledOn=true;
uint32_t millis(){return fakeNow;}
void delay(uint32_t ms){fakeNow+=ms;}
int digitalRead(int){
  return pulseStart>=0 && fakeNow>=(uint32_t)pulseStart &&
         fakeNow<(uint32_t)pulseEnd ? LOW : HIGH;
}
void writeLogical(int pin,bool on,bool){
  if(pin==runRelayPin) relayOn=on;
  if(pin==runLedPin) ledOn=on;
}
@@FUNCTIONS@@
static bool runCase(const char*name,int start,int end,uint16_t debounce,
                    bool expectPoll,uint32_t expectedElapsed,uint32_t startAt=0){
  fakeNow=startAt; pulseStart=start; pulseEnd=end; runDebounceMs=debounce;
  fsReady=true; journalRecoveryRequired=false; pendingReady=false; pendingPulses=0;
  pollIntakeSuspended=false; relayOn=true; ledOn=true;
  const uint32_t started=fakeNow;
  const bool opened=beginPollWindow();
  const uint32_t elapsed=(uint32_t)(fakeNow-started);
  if(opened!=expectPoll){
    std::cerr<<"FAIL "<<name<<" poll="<<opened<<" expected="<<expectPoll
             <<" elapsed="<<elapsed<<"\n";
    return false;
  }
  if(expectPoll){
    if(elapsed!=expectedElapsed || !pollIntakeSuspended || relayOn || ledOn){
      std::cerr<<"FAIL "<<name<<" elapsed="<<elapsed<<" expected="<<expectedElapsed
               <<" inhibit="<<pollIntakeSuspended<<" relay="<<relayOn
               <<" led="<<ledOn<<"\n";
      return false;
    }
  } else if(pollIntakeSuspended || !relayOn || !ledOn || coinLineIdle()){
    std::cerr<<"FAIL "<<name<<" abort-state inhibit="<<pollIntakeSuspended
             <<" relay="<<relayOn<<" led="<<ledOn
             <<" idle="<<coinLineIdle()<<"\n";
    return false;
  }
  return true;
}
int main(){
  int passed=0;
  if(!runCase("pulse-100ms-width30",100,130,40,false,0)) return 1;
  ++passed;
  if(!runCase("pulse-100ms-width100",100,200,40,false,0)) return 2;
  ++passed;
  if(!runCase("pulse-30ms-start",30,110,40,false,0)) return 3;
  ++passed;
  if(!runCase("pulse-249ms-start",249,329,40,false,0)) return 4;
  ++passed;
  if(!runCase("pulse-boundary-250ms",250,330,40,false,0)) return 5;
  ++passed;
  if(!runCase("idle-floor", -1,-1,40,true,250)) return 6;
  ++passed;
  if(!runCase("idle-rollover-floor",-1,-1,40,true,250,0xFFFFFF80UL)) return 7;
  ++passed;
  if(!runCase("configured-debounce-300ms",-1,-1,300,true,300)) return 8;
  ++passed;
  if(!runCase("configured-debounce-rollover-300ms",-1,-1,300,true,300,0xFFFFFF80UL)) return 9;
  ++passed;
  if(!runCase("pulse-during-300ms-debounce",280,360,300,false,0)) return 10;
  ++passed;
  if(!runCase("pulse-after-millis-rollover",0x20,0x50,40,false,0,0xFFFFFFF0UL)) return 11;
  ++passed;
  std::cout<<"POLL_WINDOW_DRAIN_PASS "<<passed<<"/11\n";
  return 0;
}
'''

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
    source = CPP.replace("@@FUNCTIONS@@", "\n\n".join(functions))
    with tempfile.TemporaryDirectory(prefix="phx-poll-drain-") as temp:
        cpp = Path(temp) / "poll_window_drain.cpp"
        binary = Path(temp) / "poll_window_drain"
        cpp.write_text(source, encoding="utf-8")
        compiled = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-O2", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, check=False,
        )
        if compiled.returncode:
            raise RuntimeError(compiled.stderr)
        return subprocess.run([str(binary)], capture_output=True, text=True, check=False)

def main():
    signatures = (
        "bool coinLineIdle(){",
        "bool canStartPoll(){",
        "void applyOutputs(){",
        "bool coinLineQuietAfterInhibit(){",
        "bool beginPollWindow(){",
    )
    failures = []
    for board, sketch in BOARDS:
        try:
            source = sketch.read_text(encoding="utf-8")
            functions = [extract(source, signature) for signature in signatures]
            result = compile_and_run(functions)
            if result.returncode:
                failures.append(f"{board} exact-source RED: {result.stderr or result.stdout}")
                continue
            if "POLL_WINDOW_DRAIN_PASS 11/11" not in result.stdout:
                failures.append(f"{board} missing pass marker: {result.stdout}")
                continue
            print(f"{board}_POLL_WINDOW_DRAIN_PASS 11/11")

            quiet_index = signatures.index("bool coinLineQuietAfterInhibit(){")
            mutated = list(functions)
            needle = "pulseTrainQuietMs=250UL"
            if needle not in mutated[quiet_index]:
                failures.append(f"{board} missing 250 ms floor for mutation test")
                continue
            mutated[quiet_index] = mutated[quiet_index].replace(
                needle, "pulseTrainQuietMs=0UL", 1
            )
            mutation = compile_and_run(mutated)
            if mutation.returncode == 0 or "FAIL pulse-100ms-width30" not in mutation.stderr:
                failures.append(f"{board} short-debounce mutation was not rejected")
                continue
            print(f"{board}_POLL_WINDOW_MUTATION_REJECTED short-debounce-only")

            mutated = list(functions)
            needle = "millis()-started<quietMs"
            if needle not in mutated[quiet_index]:
                failures.append(f"{board} missing wrap-safe elapsed expression for mutation test")
                continue
            mutated[quiet_index] = mutated[quiet_index].replace(
                needle, "millis()<started+quietMs", 1
            )
            rollover_mutation = compile_and_run(mutated)
            if (rollover_mutation.returncode == 0 or
                    "FAIL idle-rollover-floor" not in rollover_mutation.stderr):
                failures.append(f"{board} unsafe absolute-deadline mutation was not rejected")
                continue
            print(f"{board}_POLL_WINDOW_MUTATION_REJECTED unsafe-deadline-rollover")
        except Exception as error:
            failures.append(f"{board} lab error: {error}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("SIMULATED_ONLY=1")
    print("PHYSICAL_RELAY_ACCEPTANCE=0")
    print("PHYSICAL_COIN_PULSE_ACCEPTANCE=0")
    print("PHYSICAL_POWER_CUT_ACCEPTANCE=0")

if __name__ == "__main__":
    main()
