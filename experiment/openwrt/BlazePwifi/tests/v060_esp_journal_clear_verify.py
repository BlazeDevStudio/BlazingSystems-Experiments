#!/usr/bin/env python3
"""Source-linked regression for verified ESP journal deletion."""

from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
]


def extract_function(text: str, signature: str) -> str:
    start = text.index(signature)
    brace = text.index("{", start)
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    raise AssertionError("unterminated source function")


functions = [
    extract_function(path.read_text(encoding="utf-8"), "bool clearPending(){")
    for path in SOURCES
]
assert functions[0] == functions[1], "ESP clearPending implementations diverged"
clear_pending = functions[0]
assert clear_pending.index("LittleFS.remove") < clear_pending.index("pendingPulses=0")
assert "journalRecoveryRequired=true" in clear_pending
assert "if(LittleFS.exists(paths[i])) removed=false;" in clear_pending

harness = r"""
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <set>
#include <string>

struct String {
  std::string value;
  String() = default;
  String(const char *s): value(s) {}
  String &operator=(const char *s){ value=s; return *this; }
};

struct FakeFS {
  std::set<std::string> files;
  std::string failPath;
  unsigned removeCalls=0;

  bool exists(const char *path) const {
    return files.count(path)!=0;
  }

  bool remove(const char *path){
    ++removeCalls;
    if(failPath==path) return false;
    return files.erase(path)!=0;
  }
} LittleFS;

struct FakeSerial {
  void println(const char *) {}
} Serial;

bool journalRecoveryRequired=false;
bool fsReady=true;
uint8_t pendingPulses=0;
bool pendingReady=false;
String pendingNonce;
String pendingTarget;
uint32_t lastSend=0;
""" + clear_pending + r"""

void reset(){
  LittleFS.files.clear();
  LittleFS.failPath.clear();
  LittleFS.removeCalls=0;
  journalRecoveryRequired=false;
  fsReady=true;
  pendingPulses=3;
  pendingReady=true;
  pendingNonce="nonce-123";
  pendingTarget="target-123";
  lastSend=99;
}

void assertRamRetained(){
  assert(pendingPulses==3);
  assert(pendingReady);
  assert(pendingNonce.value=="nonce-123");
  assert(pendingTarget.value=="target-123");
  assert(lastSend==99);
}

int main(){
  reset();
  LittleFS.files.insert("/pending.dat");
  assert(clearPending());
  assert(LittleFS.files.empty());
  assert(pendingPulses==0 && !pendingReady && lastSend==0);
  assert(pendingNonce.value.empty() && pendingTarget.value.empty());

  reset();
  LittleFS.files.insert("/pending.dat");
  LittleFS.failPath="/pending.dat";
  assert(!clearPending());
  assertRamRetained();
  assert(journalRecoveryRequired);
  assert(LittleFS.exists("/pending.dat"));

  reset();
  fsReady=false;
  assert(!clearPending());
  assertRamRetained();
  assert(journalRecoveryRequired);
  assert(LittleFS.removeCalls==0);

  reset();
  journalRecoveryRequired=true;
  LittleFS.files.insert("/pending.dat");
  assert(!clearPending());
  assertRamRetained();
  assert(LittleFS.removeCalls==0);

  reset();
  LittleFS.files={"/pending.dat","/pending.new"};
  LittleFS.failPath="/pending.new";
  assert(!clearPending());
  assertRamRetained();
  assert(journalRecoveryRequired);
  assert(LittleFS.exists("/pending.new"));
}
"""

with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "journal_clear.cpp"
    binary = Path(tmp) / "journal_clear"
    src.write_text(harness, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
         "-fsanitize=address,undefined", str(src), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)

print("PHX-HARDWARE: verified journal clear PASS 5 success/failure cases x2 sketches")
