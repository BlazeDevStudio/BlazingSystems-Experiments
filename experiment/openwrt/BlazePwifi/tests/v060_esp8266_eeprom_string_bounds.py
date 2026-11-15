#!/usr/bin/env python3
"""Source-linked regression for bounded ESP8266 EEPROM string validation."""

from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"
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
                end = index + 1
                if end < len(text) and text[end] == ";":
                    end += 1
                return text[start:end]
    raise AssertionError("unterminated source block")


structs = []
for name in ("ConfigV1", "Config"):
    start = text.index(f"struct {name} {{")
    structs.append(extract_braced(start))

template_start = text.index("template <size_t N>\nbool fixedStringTerminated")
helpers = [extract_braced(template_start)]
cursor = template_start
for signature in (
    "bool configStringsTerminated(const Config &c)",
    "bool configStringsTerminated(const ConfigV1 &c)",
):
    start = text.index(signature, cursor)
    helpers.append(extract_braced(start))
    cursor = start + len(signature)

load_start = text.index("void loadCfg(){")
load_body = extract_braced(load_start)
current_guard = (
    "cfg.magic==MAGIC && configStringsTerminated(cfg) &&\n"
    "     strnlen(cfg.apPass,sizeof(cfg.apPass))>=8"
)
assert current_guard in load_body
assert "oldCfg.magic==MAGIC_V1 && configStringsTerminated(oldCfg)" in load_body
assert "strlen(cfg.apPass)" not in load_body

harness = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
""" + "\n\n".join(structs + helpers) + r"""

template <size_t N>
void corrupt(char (&field)[N]){
  memset(field, 'X', N);
}

int main(){
  Config current{};
  assert(configStringsTerminated(current));
  corrupt(current.ssid); assert(!configStringsTerminated(current)); current.ssid[0]=0;
  corrupt(current.pass); assert(!configStringsTerminated(current)); current.pass[0]=0;
  corrupt(current.server); assert(!configStringsTerminated(current)); current.server[0]=0;
  corrupt(current.key); assert(!configStringsTerminated(current)); current.key[0]=0;
  corrupt(current.id); assert(!configStringsTerminated(current)); current.id[0]=0;
  corrupt(current.apPass); assert(!configStringsTerminated(current)); current.apPass[0]=0;
  assert(configStringsTerminated(current));

  ConfigV1 legacy{};
  assert(configStringsTerminated(legacy));
  corrupt(legacy.ssid); assert(!configStringsTerminated(legacy)); legacy.ssid[0]=0;
  corrupt(legacy.pass); assert(!configStringsTerminated(legacy)); legacy.pass[0]=0;
  corrupt(legacy.server); assert(!configStringsTerminated(legacy)); legacy.server[0]=0;
  corrupt(legacy.key); assert(!configStringsTerminated(legacy)); legacy.key[0]=0;
  corrupt(legacy.id); assert(!configStringsTerminated(legacy)); legacy.id[0]=0;
  assert(configStringsTerminated(legacy));
}
"""

with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "eeprom_bounds.cpp"
    binary = Path(tmp) / "eeprom_bounds"
    src.write_text(harness, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", str(src), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("PHX-HARDWARE: ESP8266 EEPROM fixed-string bounds PASS 11 corruption cases")
