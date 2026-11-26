#!/usr/bin/env python3
"""Source-extracted output-enable sequencing lab for both Vendo boards.

The Arduino output latch must contain the logical OFF level before pinMode()
enables the relay or LED driver. This host lab records the exact call order
from production configureRuntimePins() and rejects the former OUTPUT-then-OFF
sequence, especially because LOW can energize an active-low relay.

Production functions are extracted by the shared C/C++ scanner so comments,
quoted strings and raw-string fixtures cannot masquerade as definitions.
Host simulation only: no GPIO voltage, relay contact, coin acceptor, or flash
hardware is measured.
"""
from pathlib import Path
import re
import subprocess
import tempfile

from firmware_source_extract import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)


def verify_shared_extractor_contract() -> None:
    """Ensure non-code decoys cannot shadow a real production definition."""
    fixture = r'''
// void configureRuntimePins(int pin) { unsafe(); }
const char *quoted = "void configureRuntimePins(int pin) { unsafe(); }";
const char *raw = R"phx(void configureRuntimePins(int pin) { unsafe(); })phx";
void configureRuntimePins(int pin) { pinMode(pin, OUTPUT); }
'''
    extracted = extract_function(fixture, "void configureRuntimePins")
    expected = "void configureRuntimePins(int pin) { pinMode(pin, OUTPUT); }"
    if extracted.strip() != expected:
        raise RuntimeError(
            "shared C/C++ extractor selected a comment/string decoy or lost the definition"
        )
    print("SOURCE_EXTRACTOR_PASS comments, quoted strings and raw strings ignored")


CPP = r'''
#include <iostream>
#include <vector>

static constexpr int HIGH=1, LOW=0, INPUT_PULLUP=2, OUTPUT=3;
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
@@WRITE_LOGICAL@@
@@CONFIGURE@@

int firstEvent(int kind,int pin,int value,int after=-1){
  for(size_t i=0;i<events.size();++i)
    if((int)i>after && events[i].kind==kind && events[i].pin==pin && events[i].value==value)
      return (int)i;
  return -1;
}

int scenario(bool activeHigh){
  events.clear();
  runCoinPin=4; runRelayPin=5; runLedPin=14;
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

int main(){
  int result=scenario(true); if(result) return result;
  result=scenario(false); if(result) return result;
  std::cout<<"OUTPUT_SEQUENCE_PASS active-high and active-low OFF preloaded before OUTPUT\n";
  return 0;
}
'''


def unsafe_mutation(configure: str) -> str:
    # Remove only the two new-pin preloads; retain old-pin shutdown and the
    # post-enable OFF confirmation so the regression isolates the latch race.
    pattern = (
        r"(runCoinPin=coinPin;\s*runRelayPin=relayPin;\s*runLedPin=ledPin;)\s*"
        r"(?://[^\n]*\n\s*)?"
        r"writeLogical\(runRelayPin,false,runRelayActiveHigh\);\s*"
        r"writeLogical\(runLedPin,false,runLedActiveHigh\);"
    )
    mutated, count = re.subn(pattern, r"\1", configure, count=1)
    if count != 1:
        raise RuntimeError("could not inject missing pre-output OFF latch mutation")
    return mutated


def active_write_mutation(configure: str, anchor: str, statement: str) -> str:
    """Inject an active-level write at a precise startup boundary."""
    if anchor not in configure:
        raise RuntimeError(f"active-write mutation anchor missing: {anchor}")
    return configure.replace(anchor, anchor + "\n  " + statement, 1)


def build_and_run(board: str, write_logical: str, configure: str, expect_pass: bool) -> None:
    code = CPP.replace("@@WRITE_LOGICAL@@", write_logical).replace("@@CONFIGURE@@", configure)
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


verify_shared_extractor_contract()
for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    write_logical = extract_function(source, "void writeLogical")
    configure = extract_function(source, "void configureRuntimePins")
    build_and_run(board, write_logical, configure, expect_pass=True)
    build_and_run(board, write_logical, unsafe_mutation(configure), expect_pass=False)
    active_write_mutations = (
        (
            "relay-active-before-output-enable",
            "  writeLogical(runRelayPin,false,runRelayActiveHigh);\n  writeLogical(runLedPin,false,runLedActiveHigh);",
            "writeLogical(runRelayPin,true,runRelayActiveHigh);",
        ),
        (
            "led-active-before-output-enable",
            "  writeLogical(runRelayPin,false,runRelayActiveHigh);\n  writeLogical(runLedPin,false,runLedActiveHigh);",
            "writeLogical(runLedPin,true,runLedActiveHigh);",
        ),
        (
            "relay-active-after-output-enable",
            "pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);",
            "writeLogical(runRelayPin,true,runRelayActiveHigh);",
        ),
        (
            "led-active-after-output-enable",
            "pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);",
            "writeLogical(runLedPin,true,runLedActiveHigh);",
        ),
    )
    for label, anchor, statement in active_write_mutations:
        mutated = active_write_mutation(configure, anchor, statement)
        build_and_run(board, write_logical, mutated, expect_pass=False)

print("PHX-HARDWARE: 4/4 output-enable sequence checks PASS; physical GPIO/relay behavior NOT TESTED")
