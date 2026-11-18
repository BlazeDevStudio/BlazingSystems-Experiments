#!/usr/bin/env python3
"""PHX-HARDWARE source-extracted pending-journal boot recovery lab.

Compiles the exact PendingRecord, pendingChecksum(), readPendingFile(), and
loadPending() from both ESP sketches against a read-only/failure-observable
fake LittleFS. It checks bounded record parsing, ambiguous candidate denial,
and preservation of every source file. SIMULATED only; not flash/power-cut
or financial-accounting evidence.
"""
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)


def extract_function(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise RuntimeError(f"missing production function: {signature}")
    brace = source.find("{", start)
    depth = 0
    quote = None
    escaped = False
    for pos in range(brace, len(source)):
        ch = source[pos]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[start:pos + 1]
    raise RuntimeError(f"unterminated production function: {signature}")


CPP = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using String = std::string;

@@PENDING_STRUCT@@
static const uint32_t PENDING_MAGIC=@@MAGIC@@;

struct File {
  std::vector<uint8_t> data;
  size_t cursor=0;
  bool opened=false;
  explicit operator bool() const { return opened; }
  size_t size() const { return data.size(); }
  size_t readBytes(char *out,size_t requested) {
    const size_t remaining=cursor<data.size()?data.size()-cursor:0;
    const size_t count=std::min(requested,remaining);
    if(count) std::memcpy(out,data.data()+cursor,count);
    cursor+=count;
    return count;
  }
  void close(){ opened=false; }
};

struct FakeLittleFS {
  std::map<std::string,std::vector<uint8_t>> files;
  unsigned removeCalls=0;
  unsigned renameCalls=0;
  bool exists(const char *path) const {
    return files.find(path)!=files.end();
  }
  File open(const char *path,const char *mode) {
    if(std::strcmp(mode,"r")!=0) return File{};
    const auto it=files.find(path);
    if(it==files.end()) return File{};
    return File{it->second,0,true};
  }
  bool remove(const char *path) {
    ++removeCalls;
    return files.erase(path)>0;
  }
  bool rename(const char *from,const char *to) {
    ++renameCalls;
    const auto it=files.find(from);
    if(it==files.end()) return false;
    if(files.find(to)!=files.end()) return false;
    files[to]=it->second;
    files.erase(it);
    return true;
  }
} LittleFS;

struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;

bool fsReady=true;
bool pendingReady=false;
uint8_t pendingPulses=0;
String pendingNonce;
String pendingTarget;
uint32_t lastSend=123;

@@CHECKSUM@@
@@READ_PENDING@@
@@LOAD_PENDING@@

static PendingRecord validRecord() {
  PendingRecord record{};
  record.magic=PENDING_MAGIC;
  record.pulses=3;
  std::strcpy(record.nonce,"nonce12345678");
  std::strcpy(record.target,"target12345678");
  record.checksum=pendingChecksum(record);
  return record;
}

static std::vector<uint8_t> recordBytes(const PendingRecord &record) {
  const uint8_t *begin=reinterpret_cast<const uint8_t*>(&record);
  return std::vector<uint8_t>(begin,begin+sizeof(record));
}

static void reset() {
  LittleFS=FakeLittleFS{};
  fsReady=true;
  pendingReady=false;
  pendingPulses=0;
  pendingNonce.clear();
  pendingTarget.clear();
  lastSend=123;
}

static bool check(const char *name,bool expectedFsReady,bool expectedPendingReady,
                  uint8_t expectedPulses,const char *expectedNonce,
                  const char *expectedTarget) {
  const auto before=LittleFS.files;
  loadPending();
  const bool unchanged=LittleFS.files==before &&
                       LittleFS.removeCalls==0 && LittleFS.renameCalls==0;
  const bool state=fsReady==expectedFsReady &&
                   pendingReady==expectedPendingReady &&
                   pendingPulses==expectedPulses &&
                   pendingNonce==expectedNonce &&
                   pendingTarget==expectedTarget;
  if(!unchanged || !state) {
    std::cerr<<"FAIL "<<name
             <<" fsReady="<<fsReady
             <<" pendingReady="<<pendingReady
             <<" pulses="<<(unsigned)pendingPulses
             <<" nonce="<<pendingNonce
             <<" target="<<pendingTarget
             <<" files_unchanged="<<unchanged<<"\n";
    return false;
  }
  std::cout<<"PASS "<<name<<"\n";
  return true;
}

int main() {
  bool ok=true;
  reset();
  ok &= check("empty journal",true,false,0,"","");

  reset();
  auto record=validRecord();
  LittleFS.files["/pending.dat"]=recordBytes(record);
  ok &= check("single primary",true,true,3,"nonce12345678","target12345678");

  reset();
  record=validRecord();
  LittleFS.files["/pending.new"]=recordBytes(record);
  ok &= check("single interrupted new candidate preserved",true,true,3,"nonce12345678","target12345678");

  reset();
  record=validRecord();
  LittleFS.files["/pending.bak"]=recordBytes(record);
  ok &= check("single interrupted backup candidate preserved",true,true,3,"nonce12345678","target12345678");

  reset();
  record=validRecord();
  LittleFS.files["/pending.dat"]=recordBytes(record);
  auto second=record;
  second.pulses=4;
  second.checksum=pendingChecksum(second);
  LittleFS.files["/pending.new"]=recordBytes(second);
  ok &= check("two valid candidates deny and preserve both",false,true,0,"","");

  reset();
  record=validRecord();
  LittleFS.files["/pending.dat"]=recordBytes(record);
  auto corrupt=validRecord();
  corrupt.checksum^=1U;
  LittleFS.files["/pending.bak"]=recordBytes(corrupt);
  ok &= check("valid plus corrupt candidate deny and preserve both",false,true,0,"","");

  reset();
  corrupt=validRecord();
  corrupt.checksum^=1U;
  LittleFS.files["/pending.dat"]=recordBytes(corrupt);
  ok &= check("single corrupt candidate hard stop",false,true,0,"","");

  reset();
  record=validRecord();
  auto oversized=recordBytes(record);
  oversized.push_back(0xA5);
  LittleFS.files["/pending.dat"]=oversized;
  ok &= check("trailing bytes rejected",false,true,0,"","");

  reset();
  record=validRecord();
  auto truncated=recordBytes(record);
  truncated.pop_back();
  LittleFS.files["/pending.dat"]=truncated;
  ok &= check("truncated record hard stop",false,true,0,"","");

  reset();
  record=validRecord();
  std::memset(record.nonce,'N',sizeof(record.nonce));
  record.checksum=pendingChecksum(record);
  LittleFS.files["/pending.dat"]=recordBytes(record);
  ok &= check("unterminated nonce rejected without cross-field read",false,true,0,"","");

  reset();
  record=validRecord();
  record.nonce[14]='X'; // non-zero data after the first NUL
  record.checksum=pendingChecksum(record);
  LittleFS.files["/pending.dat"]=recordBytes(record);
  ok &= check("hidden nonce suffix rejected",false,true,0,"","");

  reset();
  record=validRecord();
  record.target[15]='X'; // non-zero data after the first NUL
  record.checksum=pendingChecksum(record);
  LittleFS.files["/pending.dat"]=recordBytes(record);
  ok &= check("hidden target suffix rejected",false,true,0,"","");

  reset();
  corrupt=validRecord();
  corrupt.checksum^=1U;
  record=validRecord();
  LittleFS.files["/pending.dat"]=recordBytes(corrupt);
  LittleFS.files["/pending.new"]=recordBytes(record);
  ok &= check("corrupt primary plus valid new preserves ambiguity",false,true,0,"","");

  reset();
  record=validRecord();
  LittleFS.files["/pending.dat"]=recordBytes(record);
  LittleFS.files["/pending.bak"]=recordBytes(record);
  ok &= check("duplicate candidate paths remain ambiguous",false,true,0,"","");

  if(!ok) return 1;
  std::cout<<"PENDING_JOURNAL_BOOT_FAILCLOSED=PASS 13/13; SIMULATED ONLY\n";
  return 0;
}
'''


def compile_and_run(board: str, sketch: Path, temp: Path) -> None:
    source = sketch.read_text(encoding="utf-8")
    struct_match = re.search(r"struct PendingRecord\s*\{.*?\};", source, re.S)
    magic_match = re.search(
        r"(?:static\s+)?const uint32_t PENDING_MAGIC\s*=\s*(0x[0-9A-Fa-f]+)\s*;",
        source,
    )
    if not struct_match or not magic_match:
        raise RuntimeError(f"{board}: pending record definition/magic missing")

    cpp = CPP.replace("@@PENDING_STRUCT@@", struct_match.group(0))
    cpp = cpp.replace("@@MAGIC@@", magic_match.group(1))
    cpp = cpp.replace("@@CHECKSUM@@", extract_function(source, "uint32_t pendingChecksum"))
    cpp = cpp.replace("@@READ_PENDING@@", extract_function(source, "bool readPendingFile"))
    cpp = cpp.replace("@@LOAD_PENDING@@", extract_function(source, "void loadPending"))

    source_file = temp / f"{board.lower()}_pending_boot.cpp"
    binary = temp / f"{board.lower()}_pending_boot"
    source_file.write_text(cpp, encoding="utf-8")
    subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source_file), "-o", str(binary)],
        check=True,
    )
    subprocess.run([str(binary)], check=True)
    print(f"{board}: pending journal boot scenarios passed")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phx-pending-boot-") as directory:
        temp = Path(directory)
        for board, sketch in BOARDS:
            compile_and_run(board, sketch, temp)
    print("PENDING_JOURNAL_BOOT_FAILCLOSED_LAB=PASS (SIMULATED; no physical flash/power cut)")


if __name__ == "__main__":
    main()
