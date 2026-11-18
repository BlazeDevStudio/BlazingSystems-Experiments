#!/usr/bin/env python3
"""PHX-HARDWARE source-extracted quarantine append/readback regression.
Compiles the actual appendQuarantineRecord()/quarantinePending() bodies from
both ESP sketches against a failure-injectable fake LittleFS. SIMULATED only.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)


def extract_function(source: str, signature: str, required: bool = True) -> str:
    pos = source.find(signature)
    if pos < 0:
        if required:
            raise RuntimeError(f"missing production function: {signature}")
        return ""
    brace = source.find("{", pos)
    depth = 0
    quote = None
    escaped = False
    for i in range(brace, len(source)):
        ch = source[i]
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
                return source[pos:i + 1]
    raise RuntimeError(f"unterminated production function: {signature}")


def compile_and_run(board: str, source: str, temp: Path) -> None:
    match = re.search(r"static const size_t QUARANTINE_MAX_BYTES\s*=\s*([0-9]+)\s*;", source)
    if not match:
        raise RuntimeError(f"{board}: missing QUARANTINE_MAX_BYTES")
    max_bytes = match.group(1)
    helper_signatures = (
        "uint32_t quarantineCrc32Update",
        "bool fingerprintQuarantinePrefix",
        "bool verifyQuarantineAppend",
    )
    helpers = "\n".join(extract_function(source, sig, required=False) for sig in helper_signatures)
    append = extract_function(source, "bool appendQuarantineRecord")
    quarantine = extract_function(source, "bool quarantinePending")
    cpp = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>
struct String : std::string { using std::string::string; };
static const size_t QUARANTINE_MAX_BYTES=@@MAX_BYTES@@;
static bool fsReady=true;
static uint8_t pendingPulses=4;
static String pendingNonce="nonce00112233445";
static String pendingTarget="target0011223344";
static int clearCalls=0;
static bool pendingReady=true;
static std::string lastSerial;
unsigned long millis(){ return 1234UL; }
struct FakeSerial {
  template<class T> void println(const T &value){ lastSerial=value; }
} Serial;
void clearPending(){ ++clearCalls; pendingPulses=0; pendingReady=false; }
struct FakeDisk {
  std::map<std::string,std::vector<uint8_t>> files;
  bool priorOpenFail=false, appendOpenFail=false, verifyOpenFail=false;
  bool shortWrite=false, corruptPrefixAfterWrite=false, corruptSuffixAfterWrite=false;
  bool truncateAfterWrite=false, failReadAfterWrite=false, writeCompleted=false;
} disk;
struct File {
  FakeDisk *d=nullptr;
  std::string path;
  bool writing=false;
  size_t cursor=0;
  File()=default;
  File(FakeDisk *disk,const std::string &name,bool writable):d(disk),path(name),writing(writable){}
  explicit operator bool() const { return d!=nullptr; }
  size_t size() const { return d?d->files[path].size():0; }
  size_t write(const uint8_t *data,size_t len){
    if(!d || !writing) return 0;
    const size_t count=(d->shortWrite && len)?len-1:len;
    auto &bytes=d->files[path];
    bytes.insert(bytes.end(),data,data+count);
    d->writeCompleted=true;
    return count;
  }
  void flush(){}
  int available() const {
    if(!d || writing || (d->failReadAfterWrite && d->writeCompleted)) return 0;
    const auto &bytes=d->files.at(path);
    return cursor<bytes.size()?(int)(bytes.size()-cursor):0;
  }
  int read(){
    if(!d || writing || (d->failReadAfterWrite && d->writeCompleted)) return -1;
    const auto &bytes=d->files.at(path);
    if(cursor>=bytes.size()) return -1;
    return bytes[cursor++];
  }
  void close(){
    if(d && writing && d->writeCompleted){
      auto &bytes=d->files[path];
      if(d->corruptPrefixAfterWrite && !bytes.empty()) bytes[0]^=0x01;
      if(d->corruptSuffixAfterWrite && !bytes.empty()) bytes.back()^=0x01;
      if(d->truncateAfterWrite && !bytes.empty()) bytes.pop_back();
    }
    d=nullptr;
  }
};
struct FakeLittleFS {
  bool exists(const char *path) const { return disk.files.find(path)!=disk.files.end(); }
  File open(const char *path,const char *mode){
    if(std::strcmp(mode,"a")==0){
      if(disk.appendOpenFail) return {};
      disk.files[path];
      return File(&disk,path,true);
    }
    if(std::strcmp(mode,"r")==0){
      if(!exists(path)) return {};
      if(!disk.writeCompleted && disk.priorOpenFail) return {};
      if(disk.writeCompleted && disk.verifyOpenFail) return {};
      return File(&disk,path,false);
    }
    return {};
  }
} LittleFS;
@@HELPERS@@
@@APPEND_FUNCTION@@
@@QUARANTINE_FUNCTION@@
static void reset(){
  disk=FakeDisk{}; clearCalls=0; fsReady=true; pendingPulses=4; pendingReady=true;
  pendingNonce="nonce00112233445"; pendingTarget="target0011223344"; lastSerial.clear();
}
static bool scenario(int id,const char *name,bool expected){
  reset();
  const std::string prefix="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
  if(id!=10) disk.files["/quarantine.log"]={prefix.begin(),prefix.end()};
  if(id==1) disk.priorOpenFail=true;
  if(id==2) disk.appendOpenFail=true;
  if(id==3) disk.shortWrite=true;
  if(id==4) disk.verifyOpenFail=true;
  if(id==5) disk.truncateAfterWrite=true;
  if(id==6) disk.corruptSuffixAfterWrite=true;
  if(id==7) disk.corruptPrefixAfterWrite=true;
  if(id==8) disk.failReadAfterWrite=true;
  if(id==9) disk.files["/quarantine.log"].resize(QUARANTINE_MAX_BYTES,'X');
  if(id==11) fsReady=false;
  if(id==12) pendingPulses=0;
  const std::string before=disk.files.count("/quarantine.log")?
    std::string(disk.files["/quarantine.log"].begin(),disk.files["/quarantine.log"].end()):std::string();
  const bool result=quarantinePending(String("window expired"));
  const bool shouldClear=expected;
  if(result!=expected || clearCalls!=(shouldClear?1:0) ||
     pendingPulses!=(shouldClear?0:(id==12?0:4)) || pendingReady==shouldClear){
    std::cerr<<"FAIL "<<name<<" result="<<result<<" clearCalls="<<clearCalls
             <<" pendingPulses="<<(int)pendingPulses<<" pendingReady="<<pendingReady<<"\n";
    return false;
  }
  if(expected && id==10){
    const std::string after(disk.files["/quarantine.log"].begin(),disk.files["/quarantine.log"].end());
    if(after.find("TIME=1234 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window expired\n")==std::string::npos){
      std::cerr<<"FAIL first append bytes\n"; return false;
    }
  }
  if(!expected && id==7 && disk.files.count("/quarantine.log")){
    const std::string after(disk.files["/quarantine.log"].begin(),disk.files["/quarantine.log"].end());
    if(after==before){ std::cerr<<"FAIL prefix mutation was not injected\n"; return false; }
  }
  std::cout<<"PASS "<<name<<"\n";
  return true;
}
int main(){
  bool ok=true;
  ok &= scenario(0,"existing log exact append",true);
  ok &= scenario(1,"prior log open failure",false);
  ok &= scenario(2,"append open failure",false);
  ok &= scenario(3,"short append write",false);
  ok &= scenario(4,"readback open failure",false);
  ok &= scenario(5,"post-close truncation",false);
  ok &= scenario(6,"same-size appended suffix corruption",false);
  ok &= scenario(7,"same-size pre-existing prefix corruption",false);
  ok &= scenario(8,"readback read failure",false);
  ok &= scenario(9,"capacity exhaustion",false);
  ok &= scenario(10,"first-ever log creation",true);
  ok &= scenario(11,"filesystem unavailable",false);
  ok &= scenario(12,"empty pending event",false);
  if(!ok) return 1;
  std::cout<<"QUARANTINE_APPEND_READBACK=PASS 13/13; SIMULATED ONLY\n";
  return 0;
}
'''
    cpp = cpp.replace("@@MAX_BYTES@@", max_bytes)
    cpp = cpp.replace("@@HELPERS@@", helpers).replace("@@APPEND_FUNCTION@@", append).replace("@@QUARANTINE_FUNCTION@@", quarantine)
    source_file = temp / f"{board.lower()}_quarantine_append.cpp"
    binary = temp / f"{board.lower()}_quarantine_append"
    source_file.write_text(cpp, encoding="utf-8")
    subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(source_file), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
    print(f"{board}: quarantine append/readback scenarios passed")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="phx-quarantine-readback-") as directory:
        temp = Path(directory)
        for board, path in BOARDS:
            source = path.read_text(encoding="utf-8")
            compile_and_run(board, source, temp)
    print("QUARANTINE_APPEND_READBACK_LAB=PASS (SIMULATED; no physical flash/power cut)")
    subprocess.run(
        [sys.executable, str(Path(__file__).with_name("pending_journal_boot_failclosed_lab.py"))],
        check=True,
    )

if __name__ == "__main__":
    main()
