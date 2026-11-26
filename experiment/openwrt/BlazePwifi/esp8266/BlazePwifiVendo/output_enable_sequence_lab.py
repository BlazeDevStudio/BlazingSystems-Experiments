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

from firmware_lab_source import extract_function as extract

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
)


def verify_extractor_ignores_non_code_braces() -> None:
    """A brace in a C++ literal/comment must not truncate a production function."""
    fixture = r"""
void target() {
  const char *quoted = "}";
  const char *raw = R"tag({ raw })tag";
  // }
  /* } */
  const char *after = "still inside";
}
void following() {}
"""
    extracted = extract(fixture, "target")
    if 'const char *after = "still inside";' not in extracted:
        raise SystemExit("OUTPUT_EXTRACTOR_FAIL: non-code brace truncated target()")
    if "void following()" in extracted:
        raise SystemExit("OUTPUT_EXTRACTOR_FAIL: extractor crossed into following()")
    print("OUTPUT_EXTRACTOR_LEXICAL_FIXTURE_PASS")


verify_extractor_ignores_non_code_braces()


CPP = r'''
#include <cstdint>
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
// Dependencies outside this lab's output-order contract are deliberately stubbed.
bool coinInterruptAttached=false;
bool pollIntakeSuspended=false;
bool runtimePinsSafe(int,int,int){ return true; }
void applyOutputs(){}
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }

int runCoinPin=4, runRelayPin=5, runLedPin=14;
bool runRelayActiveHigh=true, runLedActiveHigh=true, runCoinActiveLow=false;
bool outputPolarityKnown=true, pinConfigSafe=true, insertMode=true;
std::string activeTarget="target";
@@WRITE_LOGICAL@@
// This lab isolates output ordering; exact ingress behavior has its own source lab.
bool quarantineCoinIngressTransition(){ return true; }
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
  configureRuntimePins(12,13,15,runCoinActiveLow);
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
  configureRuntimePins(12,13,15,runCoinActiveLow);
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
    # Board implementations have converged on one or more combined
    # polarity/pin-safety guards. Remove the actual guard(s) present; retain
    # the ESP32 legacy-block fallback for older source shapes.
    mutated, count = re.subn(r"!outputPolarityKnown\s*\|\|\s*", "", configure)
    if count in (1, 2):
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

def verify_runtime_pin_quarantine(configure: str, board: str) -> None:
    pre_detach = re.search(
        r"if\s*\(\s*coinInterruptAttached\s*&&\s*!\s*"
        r"quarantineCoinIngressTransition\s*\(\s*\)\s*\)\s*return\s+false\s*;",
        configure,
    )
    detach = re.search(r"\bdetachInterrupt\s*\(", configure)
    inhibit = configure.find("pollIntakeSuspended=true")
    output_off = configure.find("applyOutputs();")
    if not pre_detach or not detach or not (0 <= inhibit < output_off < pre_detach.start() < detach.start()):
        raise RuntimeError(f"{board}: ingress must be inhibited and quarantined before detaching the ISR")

    attach_positions = [m.start() for m in re.finditer(r"\battachInterrupt\s*\(", configure)]
    attached_positions = [m.start() for m in re.finditer(r"coinInterruptAttached\s*=\s*true", configure)]
    post_pattern = (
        r"if\s*\(\s*!\s*quarantineCoinIngressTransition\s*\(\s*\)\s*\)\s*return\s+false\s*;"
    )
    post_positions = [m.start() for m in re.finditer(post_pattern, configure)]
    restore_positions = [m.start() for m in re.finditer(
        r"pollIntakeSuspended\s*=\s*priorPollIntakeSuspended", configure
    )]
    if not (len(attach_positions) == len(attached_positions) == len(post_positions) == len(restore_positions) == 2):
        raise RuntimeError(f"{board}: expected two attach → quarantine → intake-restore paths")
    for attach, attached, quarantine, restore in zip(
        attach_positions, attached_positions, post_positions, restore_positions
    ):
        if not attach < attached < quarantine < restore:
            raise RuntimeError(f"{board}: ingress quarantine must succeed before intake resumes")


def reject_quarantine_mutation(configure: str, board: str, label: str, pattern: str) -> None:
    mutated, count = re.subn(pattern, "", configure, count=1)
    if count != 1:
        raise RuntimeError(f"{board}: could not inject {label} mutation")
    try:
        verify_runtime_pin_quarantine(mutated, board)
    except RuntimeError:
        print(f"{board}: {label} mutation rejected")
        return
    raise RuntimeError(f"{board}: {label} mutation was not rejected")

for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    write_logical = extract(source, "writeLogical")
    configure = extract(source, "configureRuntimePins")
    # Verify source-level ISR quarantine ordering here; runtime behavior is
    # exercised by the dedicated coin-pulse and blocking-poll labs.
    verify_runtime_pin_quarantine(configure, board)
    reject_quarantine_mutation(
        configure, board, "pre-detach-quarantine",
        r"if\s*\(\s*coinInterruptAttached\s*&&\s*!\s*"
        r"quarantineCoinIngressTransition\s*\(\s*\)\s*\)\s*return\s+false\s*;",
    )
    reject_quarantine_mutation(
        configure, board, "post-attach-quarantine",
        r"if\s*\(\s*!\s*quarantineCoinIngressTransition\s*\(\s*\)\s*\)\s*return\s+false\s*;",
    )
    has_local_polarity_guard = "outputPolarityKnown" in configure
    build_and_run(board, write_logical, configure, expect_pass=True,
                  has_local_polarity_guard=has_local_polarity_guard)
    build_and_run(board, write_logical, unsafe_mutation(configure), expect_pass=False,
                  has_local_polarity_guard=has_local_polarity_guard)
    if has_local_polarity_guard:
        build_and_run(board, write_logical, remove_local_polarity_gate(configure),
                      expect_pass=False, has_local_polarity_guard=True)

print("PHX-HARDWARE: output-order/polarity and ISR-quarantine source mutations rejected; physical GPIO/relay behavior NOT TESTED")

