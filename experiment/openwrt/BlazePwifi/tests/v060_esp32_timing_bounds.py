#!/usr/bin/env python3
"""Source-linked regression for ESP32 persisted timing bounds."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
text = SOURCE.read_text(encoding="utf-8")


def extract_braced(start: int) -> str:
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise AssertionError("unterminated source block")


helper_start = text.index(
    "uint16_t boundedTimingMs(uint32_t raw,uint16_t minimum,uint16_t maximum)"
)
helper = extract_braced(helper_start)
load_start = text.index("void loadConfig(){")
load_body = extract_braced(load_start)

assert (
    'cfg.coinDebounceMs=boundedTimingMs(prefs.getUInt("debounce",40),1,2000);'
    in load_body
)
assert (
    'cfg.pulseGroupMs=boundedTimingMs(prefs.getUInt("groupms",400),10,10000);'
    in load_body
)
assert '(uint16_t)prefs.getUInt' not in load_body

harness = r"""
#include <cassert>
#include <cstdint>
#include <limits>
""" + helper + r"""

int main(){
  const uint32_t max=std::numeric_limits<uint32_t>::max();

  assert(boundedTimingMs(0,1,2000)==1);
  assert(boundedTimingMs(1,1,2000)==1);
  assert(boundedTimingMs(40,1,2000)==40);
  assert(boundedTimingMs(2000,1,2000)==2000);
  assert(boundedTimingMs(2001,1,2000)==2000);
  assert(boundedTimingMs(max,1,2000)==2000);

  assert(boundedTimingMs(0,10,10000)==10);
  assert(boundedTimingMs(10,10,10000)==10);
  assert(boundedTimingMs(400,10,10000)==400);
  assert(boundedTimingMs(10000,10,10000)==10000);
  assert(boundedTimingMs(10001,10,10000)==10000);
  assert(boundedTimingMs(max,10,10000)==10000);
}
"""

with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "timing_bounds.cpp"
    binary = Path(tmp) / "timing_bounds"
    src.write_text(harness, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", str(src), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("PHX-HARDWARE: ESP32 stored timing bounds PASS 12 boundary/overflow cases")
