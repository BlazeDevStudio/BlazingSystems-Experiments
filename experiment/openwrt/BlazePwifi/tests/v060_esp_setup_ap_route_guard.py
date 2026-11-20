#!/usr/bin/env python3
"""PHX-HARDWARE: source-extracted setup-AP route isolation lab.

The exact interface predicate is compiled and exercised with AP, station, and
inactive-AP requests. This is a host network model, not hardware acceptance.
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


def source_function(source, name):
    match = re.search(r"\bbool\s+" + re.escape(name) + r"\s*\(\s*\)\s*\{", source)
    assert match, f"Missing production function {name}"
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"Unbalanced production function {name}")


def route_handler(source, marker):
    start = source.find(marker)
    assert start >= 0, f"Missing route {marker}"
    brace = source.find("{", start)
    depth = 0
    for pos in range(brace, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:pos]
    raise AssertionError(f"Unbalanced route {marker}")


failed = []
for chip, path in SOURCES.items():
    sketch = path.read_text(encoding="utf-8")
    allowed = source_function(sketch, "setupRequestAllowed")
    required = source_function(sketch, "requireSetupApRequest")
    assert "setupApOn" in allowed
    assert "web.client().localIP()" in allowed
    assert "WiFi.softAPIP()" in allowed
    assert "web.send(403" in required

    routes = {
        'web.on("/",[]()': "String h=",
        'web.on("/quarantine",[]()': "LittleFS",
        'web.on("/save",HTTP_POST,[]()': 'web.arg("s")',
    }
    for marker, sensitive in routes.items():
        handler = route_handler(sketch, marker)
        guard = handler.find("if(!requireSetupApRequest()) return;")
        first_sensitive = handler.find(sensitive)
        assert guard >= 0, f"{chip}: {marker} lacks setup-AP guard"
        assert first_sensitive < 0 or guard < first_sensitive, (
            f"{chip}: {marker} touches sensitive state before interface guard"
        )

    code = r"""
#include <iostream>
#include <string>
struct IPAddress {
  int value;
  bool operator==(const IPAddress &other)const{return value==other.value;}
};
struct FakeClient {
  IPAddress local{1};
  IPAddress localIP()const{return local;}
};
struct FakeWeb {
  FakeClient connection;
  int code=0;
  FakeClient &client(){return connection;}
  void send(int c,const char*,const char*){code=c;}
} web;
struct FakeWiFi {
  IPAddress ap{1};
  IPAddress softAPIP()const{return ap;}
} WiFi;
bool setupApOn=false;
""" + allowed + "\n" + required + r"""
int main(){
  setupApOn=true;web.connection.local={1};web.code=0;
  const bool apAllowed=requireSetupApRequest() && web.code==0;
  setupApOn=false;web.connection.local={1};web.code=0;
  const bool inactiveDenied=!requireSetupApRequest() && web.code==403;
  setupApOn=true;web.connection.local={2};web.code=0;
  const bool stationDenied=!requireSetupApRequest() && web.code==403;
  std::cout<<"ap_allowed="<<apAllowed
           <<" inactive_denied="<<inactiveDenied
           <<" station_denied="<<stationDenied<<"\n";
  return (apAllowed && inactiveDenied && stationDenied)?0:31;
}
"""
    with tempfile.TemporaryDirectory(prefix="phx-hw-setup-ap-") as folder:
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
    sys.exit("PHX-HARDWARE setup-AP route isolation failed: " + ",".join(failed))
print("PHX-HARDWARE: setup routes isolated from station interface PASS 2/2")
print("PHYSICAL_NETWORK_INTERFACE_VERIFIED=0")
print("PRODUCTION_CONFIGURATION_AUTHORIZED=0")
