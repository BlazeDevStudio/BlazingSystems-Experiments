#!/usr/bin/env python3
"""Source-extracted output-enable sequencing lab for both Vendo boards.

The Arduino output latch must contain the logical OFF level before pinMode()
enables the relay or LED driver. This host lab records the exact call order
from production configureRuntimePins() and rejects the former OUTPUT-then-OFF
sequence, especially because LOW can energize an active-low relay.

Host simulation only: no GPIO voltage, relay contact, coin acceptor, or flash
hardware is measured.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)


def extract(source: str, name: str) -> str:
    match = re.search(r"\bvoid\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", source)
    if not match:
        raise RuntimeError(f"missing production function: {name}")
    depth = 0
    for index in range(match.end() - 1, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():index + 1]
    raise RuntimeError(f"unbalanced production function: {name}")


CPP = r'''
#include <iostream>
#include <string>
#include <vector>

static constexpr int HIGH=1, LOW=0, INPUT=4, INPUT_PULLUP=2, OUTPUT=3;
struct Event { int kind; int pin; int value; };
std::vector<Event> events;
void digitalWrite(int pin,int level){ events.push_back({1,pin,level}); }
void pinMode(int pin,int mode){ events.push_back({2,pin,mode}); }
static constexpr int FALLING=4, RISING=5;
int digitalPinToInterrupt(int pin){ return pin; }
void detachInterrupt(int) {}
void attachInterrupt(int,void (*)(void),int) {}
void coinEdgeISR() {}

int runCoinPin=4, runRelayPin=5, runLedPin=14;
bool runRelayActiveHigh=true, runLedActiveHigh=true, runCoinActiveLow=false;
bool outputPolarityKnown=true, pinConfigSafe=true, insertMode=true;
std::string activeTarget="target";
@@WRITE_LOGICAL@@
@@CONFIGURE@@
static constexpr bool HAS_LOCAL_POLARITY_GUARD=@@HAS_LOCAL_POLARITY_GUARD@@;

int firstEvent(int kind,int pin,int value,int after=-1){
  for(size_t i=0;i<events.size();++i)
    if((int)i>after && events[i].kind==kind && events[i].pin==pin && events[i].value==value)
      return (int)i;
  return -1;
}

int scenario(bool activeHigh){
  events.clear();
  runCoinPin=4; runRelayPin=5; runLedPin=14;
  outputPolarityKnown=true; pinConfigSafe=true; insertMode=true; activeTarget="target";
  runRelayActiveHigh=activeHigh; runLedActiveHigh=activeHigh;
  configureRuntimePins(12,13,15);
  const int offLevel=activeHigh?LOW:HIGH;
  const int relayOff=firstEvent(1,13,offLevel);
  const int relayOutput=firstEvent(2,13,OUTPUT);
  const int ledOff=firstEvent(1,15,offLevel);
  const int ledOutput=firstEvent(2,15,OUTPUT);
  const int relayConfirm=firstEvent(1,13,offLevel,relayOutput);
  const int ledConfirm=firstEvent(1,15,offLevel,ledOutput);
  const int oldRelayOff=firstEvent(1,5,offLevel);
  const int oldLedOff=firstEvent(1,14,offLevel);
  if(relayOff<0 || relayOutput<0 || relayOff>=relayOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL relay OFF must precede OUTPUT mode\n"; return 10;
  }
  if(ledOff<0 || ledOutput<0 || ledOff>=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL LED OFF must precede OUTPUT mode\n"; return 11;
  }
  if(relayConfirm<=relayOutput || ledConfirm<=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL OFF level must be confirmed after OUTPUT mode\n"; return 12;
  }
  if(oldRelayOff<0 || oldLedOff<0 || oldRelayOff>=relayOutput || oldLedOff>=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL old outputs were not disabled before reassignment\n"; return 13;
  }
  return 0;
}


int unknownPolarityScenario(){
  events.clear();
  runCoinPin=4; runRelayPin=5; runLedPin=14;
  outputPolarityKnown=false; pinConfigSafe=true; insertMode=true; activeTarget="target";
  configureRuntimePins(12,13,15);
  if(firstEvent(2,12,INPUT_PULLUP)<0 ||
     firstEvent(2,13,INPUT)<0 || firstEvent(2,15,INPUT)<0){
    std::cerr<<"OUTPUT_UNKNOWN_POLARITY_FAIL relay/LED must remain INPUT"; return 20;
  }
  if(firstEvent(2,13,OUTPUT)>=0 || firstEvent(2,15,OUTPUT)>=0){
    std::cerr<<"OUTPUT_UNKNOWN_POLARITY_FAIL output driver enabled"; return 21;
  }
  for(const auto &event : events){
    if(event.kind==1 && (event.pin==13 || event.pin==15)){
      std::cerr<<"OUTPUT_UNKNOWN_POLARITY_FAIL unknown-polarity pin was driven"; return 22;
    }
  }
  if(pinConfigSafe || insertMode || !activeTarget.empty()){
    std::cerr<<"OUTPUT_UNKNOWN_POLARITY_FAIL admission state not cleared"; return 23;
  }
  return 0;
}

int main(){
  int result=scenario(true); if(result) return result;
  result=scenario(false); if(result) return result;
  if(HAS_LOCAL_POLARITY_GUARD){
    result=unknownPolarityScenario(); if(result) return result;
    std::cout<<"OUTPUT_UNKNOWN_POLARITY_DENY_PASS"<<std::endl;
  }
  std::cout<<"OUTPUT_SEQUENCE_PASS active-high and active-low OFF preloaded before OUTPUT\n";
  return 0;
}
'''


def unsafe_mutation(configure: str) -> str:
    # Remove only the two new-pin preloads; retain old-pin shutdown and the
    # post-enable OFF confirmation so the regression isolates the latch race.
    pattern = (
        r"(// Preload[^\n]*\n\s*)"
        r"writeLogical\(runRelayPin,false,runRelayActiveHigh\);\s*"
        r"writeLogical\(runLedPin,false,runLedActiveHigh\);"
    )
    mutated, count = re.subn(pattern, r"\1", configure, count=1)
    if count != 1:
        raise RuntimeError("could not inject missing pre-output OFF latch mutation")
    return mutated


def build_and_run(board: str, write_logical: str, configure: str, expect_pass: bool,
                  has_local_polarity_guard: bool) -> None:
    code = (CPP.replace("@@WRITE_LOGICAL@@", write_logical)
            .replace("@@CONFIGURE@@", configure)
            .replace("@@HAS_LOCAL_POLARITY_GUARD@@",
                     "true" if has_local_polarity_guard else "false"))
    with tempfile.TemporaryDirectory(prefix="phx-output-sequence-") as tmp:
        source_path = Path(tmp) / "sequence.cpp"
        binary_path = Path(tmp) / "sequence"
        source_path.write_text(code, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
             str(source_path), "-o", str(binary_path)],
            check=True,
        )
        result = subprocess.run([str(binary_path)], text=True, capture_output=True)
    if expect_pass and result.returncode != 0:
        raise SystemExit(
            f"{board}: production sequence failed ({result.returncode}): {result.stderr.strip()}"
        )
    if not expect_pass and result.returncode == 0:
        raise SystemExit(f"{board}: unsafe OUTPUT-before-OFF mutation was not rejected")
    if expect_pass:
        print(f"{board}: {result.stdout.strip()}")
    else:
        print(f"{board}: unsafe-order mutation rejected at exit {result.returncode}")



def remove_local_polarity_gate(configure: str) -> str:
    # ESP8266 has two combined polarity/pin-safety guards; ESP32 keeps one
    # early unknown-polarity INPUT-only block. Remove the board's actual gate,
    # not a textual pattern copied from the other architecture.
    mutated, count = re.subn(r"!outputPolarityKnown\s*\|\|\s*", "", configure)
    if count == 2:
        return mutated

    if count == 0:
        pattern = (
            r"(?s)\n\s*if\(!outputPolarityKnown\)\{\s*"
            r"// No default or remote value can establish physical relay/LED polarity\.\s*"
            r".*?\s*return;\s*\}"
        )
        mutated, count = re.subn(pattern, "\n", configure, count=1)
        if count == 1:
            return mutated

    raise RuntimeError(f"could not remove one board-specific local polarity gate (combined guards={count})")


for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    write_logical = extract(source, "writeLogical")
    configure = extract(source, "configureRuntimePins")
    has_local_polarity_guard = "outputPolarityKnown" in configure
    build_and_run(board, write_logical, configure, expect_pass=True,
                  has_local_polarity_guard=has_local_polarity_guard)
    build_and_run(board, write_logical, unsafe_mutation(configure), expect_pass=False,
                  has_local_polarity_guard=has_local_polarity_guard)
    if has_local_polarity_guard:
        build_and_run(board, write_logical, remove_local_polarity_gate(configure),
                      expect_pass=False, has_local_polarity_guard=True)

print("PHX-HARDWARE: 5/5 output-enable/polarity host checks PASS; physical GPIO/relay behavior NOT TESTED")

