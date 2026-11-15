#!/usr/bin/env python3
"""PHX-HARDWARE: execute the source-extracted quarantine-clear denial.

A hostile network POST is simulated against the exact handler body from each
sketch. This is not physical flash, power-cut, or financial acceptance.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}


def clear_handler(source):
    pattern = re.compile(
        r'web\.on\("/quarantine/clear",HTTP_POST,\[\]\(\)\{(?P<body>.*?)\n  \}\);',
        re.DOTALL,
    )
    match = pattern.search(source)
    assert match, "Missing quarantine-clear handler"
    return match.group("body")


failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text(encoding="utf-8")
    body = clear_handler(sketch)
    assert 'LittleFS.remove("/quarantine.log")' not in sketch, (
        f"{chip}: quarantine evidence still has a network deletion path"
    )
    assert "web.send(403" in body
    assert "preserve and reconcile evidence offline" in body
    assert 'web.on("/quarantine",[]()' in sketch, (
        f"{chip}: read/export route unexpectedly removed"
    )

    code = r"""
#include <iostream>
#include <string>
struct FakeWeb {
  int code=0;
  std::string type;
  std::string body;
  void send(int c,const char *t,const char *b){code=c;type=t;body=b;}
} web;
void hostilePost(){
""" + body + r"""
}
int main(){
  hostilePost();
  const bool denied=web.code==403;
  const bool plain=web.type=="text/plain";
  const bool preserved=web.body.find("preserve and reconcile evidence offline")!=std::string::npos;
  std::cout<<"denied="<<denied<<" plain="<<plain<<" preserved="<<preserved<<"\n";
  return (denied && plain && preserved)?0:29;
}
"""
    with tempfile.TemporaryDirectory(prefix="phx-hw-quarantine-clear-") as folder:
        cpp = Path(folder) / "test.cpp"
        binary = Path(folder) / "test"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30,
        )
        if built.returncode:
            print(chip, "COMPILE FAIL", built.stderr[-2400:])
            failed.append(chip)
            continue
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=15)
        print(chip, "PASS" if ran.returncode == 0 else "FAIL", ran.stdout.strip())
        if ran.returncode:
            failed.append(chip)

if failed:
    sys.exit("PHX-HARDWARE quarantine-clear denial failed: " + ",".join(failed))
print("PHX-HARDWARE: hostile quarantine-clear POST denied PASS 2/2")
print("PHYSICAL_FLASH_DURABILITY_VERIFIED=0")
print("FINANCIAL_RECONCILIATION_COMPLETE=0")
