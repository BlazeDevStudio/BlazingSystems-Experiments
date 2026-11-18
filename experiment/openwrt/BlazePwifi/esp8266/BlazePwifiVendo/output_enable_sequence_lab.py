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
#include <vector>

static constexpr int HIGH=1, LOW=0, INPUT_PULLUP=2, OUTPUT=3;
struct Event { int kind; int pin; int value; };
std::vector<Event> events;
void digitalWrite(int pin,int level){ events.push_back({1,pin,level}); }
void pinMode(int pin,int mode){ events.push_back({2,pin,mode}); }

int runCoinPin=4, runRelayPin=5, runLedPin=14;
bool runRelayActiveHigh=true, runLedActiveHigh=true;
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
    coin_mode = configure.index("pinMode(runCoinPin,INPUT_PULLUP)")
    relay_mode = configure.index("pinMode(runRelayPin,OUTPUT)", coin_mode)
    prefix = configure[:coin_mode]
    middle = configure[coin_mode:relay_mode]
    suffix = configure[relay_mode:]
    middle = re.sub(
        r"\s*writeLogical\(runRelayPin,false,runRelayActiveHigh\);",
        "",
        middle,
        count=1,
    )
    middle = re.sub(
        r"\s*writeLogical\(runLedPin,false,runLedActiveHigh\);",
        "",
        middle,
        count=1,
    )
    return prefix + middle + suffix


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


for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    write_logical = extract(source, "writeLogical")
    configure = extract(source, "configureRuntimePins")
    build_and_run(board, write_logical, configure, expect_pass=True)
    build_and_run(board, write_logical, unsafe_mutation(configure), expect_pass=False)

print("PHX-HARDWARE: 4/4 output-enable sequence checks PASS; physical GPIO/relay behavior NOT TESTED")

