#!/usr/bin/env python3
"""PHX-HARDWARE: exact source-extracted append/quarantine test, two ESP sketches.
Runs unmodified extracted function bodies with a C++17 fake LittleFS.
Neither flash power-cycle testing nor proof of durable financial accounting.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)

CPP = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  void remove(size_t index){erase(index);}
};
static constexpr size_t QUARANTINE_MAX_BYTES=4096;
static bool fsReady=true;
static bool journalRecoveryRequired=false;
static uint8_t pendingPulses=4;
static String pendingNonce="nonce001122334455";
static String pendingTarget="target0011223344";
static int clearCount=0;
static bool clearAllowed=true;
unsigned long millis(){return 1234UL;}
bool clearPending(){
  ++clearCount;
  if(!clearAllowed){journalRecoveryRequired=true; return false;}
  pendingPulses=0; pendingNonce.clear(); pendingTarget.clear();
  return true;
}
struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;
enum SeekMode { SeekSet };
struct FakeDisk {
  std::string bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
  bool priorOpenFail=false, appendOpenFail=false, verifyOpenFail=false;
  bool shortWrite=false, mutateAfterClose=false, mutateOnRead=false;
  bool removeOneByteAfterClose=false;
  bool hasWritten=false;
} disk;
struct File {
  FakeDisk* d=nullptr;
  bool writing=false;
  size_t cursor=0;
  File()=default;
  File(FakeDisk* p,bool writable):d(p),writing(writable){}
  explicit operator bool() const {return d!=nullptr;}
  size_t size() const{return d?d->bytes.size():0;}
  size_t write(const uint8_t* buf,size_t len){
    if(!d || !writing)return 0;
    size_t n=(d->shortWrite && len)?len-1:len;
    d->bytes.append((const char*)buf,n);
    d->hasWritten=true;
    return n;
  }
  void flush(){}
  void close(){
    if(d && writing){
      if(d->mutateAfterClose && !d->bytes.empty()) d->bytes.back()='Z';
      if(d->removeOneByteAfterClose && !d->bytes.empty()) d->bytes.pop_back();
    }
    d=nullptr;
  }
  bool seek(size_t offset,SeekMode){
    if(!d || writing || offset>d->bytes.size())return false;
    cursor=offset;
    return true;
  }
  size_t available() const{return d && !writing && cursor<d->bytes.size()?d->bytes.size()-cursor:0;}
  int read(){
    if(!d || writing || cursor>=d->bytes.size())return -1;
    int byte=(unsigned char)d->bytes[cursor++];
    return (d->mutateOnRead && d->hasWritten)?(byte^1):byte;
  }
};
struct FakeLittleFS {
  bool exists(const char* path){return strcmp(path,"/quarantine.log")==0;}
  File open(const char* path,const char* mode){
    if(strcmp(path,"/quarantine.log")!=0)return {};
    if(strcmp(mode,"a")==0) return disk.appendOpenFail?File():File(&disk,true);
    if(strcmp(mode,"r")==0) return (!disk.hasWritten && disk.priorOpenFail)
       || (disk.hasWritten && disk.verifyOpenFail)?File():File(&disk,false);
    return {};
  }
} LittleFS;

@@SOURCE_ENCODE@@
@@SOURCE_INSPECT@@
@@SOURCE_APPEND@@
@@SOURCE_QUARANTINE@@
int main(){
  for(int scenario=0;scenario<16;scenario++){
    disk=FakeDisk{};
    clearCount=0;
    clearAllowed=true;
    fsReady=true;
    journalRecoveryRequired=false;
    pendingPulses=4;
    pendingNonce="nonce001122334455";
    pendingTarget="target0011223344";
    if(scenario==1) fsReady=false;
    if(scenario==2) pendingPulses=0;
    if(scenario==3) disk.priorOpenFail=true;
    if(scenario==4) disk.appendOpenFail=true;
    if(scenario==5) disk.shortWrite=true;
    if(scenario==6) disk.verifyOpenFail=true;
    if(scenario==7) disk.removeOneByteAfterClose=true;
    if(scenario==8) disk.mutateAfterClose=true; // corrupts final newline
    if(scenario==9) disk.mutateOnRead=true; // verification read fault only
    if(scenario==10){
      const std::string valid="TIME=1 PULSES=1 NONCE=old TARGET=old REASON=old\n";
      disk.bytes.clear();
      while(disk.bytes.size()<=QUARANTINE_MAX_BYTES) disk.bytes+=valid;
    }
    if(scenario==11) clearAllowed=false;
    String reason="window expired";
    if(scenario==12) reason=String("bad\nRECORD=forged\t\\");
    if(scenario==13) journalRecoveryRequired=true;
    if(scenario==14)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce001122334455 TARGET=target0011223344 REASON=earlier\n";
    if(scenario==15)
      disk.bytes+="TIME=9 PULSES=4 NONCE=nonce001122334455";
    const std::string bytesBefore=disk.bytes;
    bool expectClear=(scenario==0 || scenario==12 || scenario==14);
    bool expectClearAttempt=expectClear || scenario==11;
    bool expectRecovery=scenario==3 || (scenario>=5 && scenario<=9) ||\n                        scenario==11 || scenario==13 || scenario==15;
    bool ok=quarantinePending(reason);
    if(ok!=expectClear || clearCount!=(expectClearAttempt?1:0) ||
       (!expectClear && pendingPulses!=(scenario==2?0:4)) ||
       (scenario==12 &&
        (std::count(disk.bytes.begin(),disk.bytes.end(),'\n')!=2 ||
         disk.bytes.find("bad\\nRECORD=forged\\t\\\\")==std::string::npos)) ||
       (scenario==14 && disk.bytes!=bytesBefore) ||
       (scenario==15 && disk.bytes!=bytesBefore) ||
       journalRecoveryRequired!=expectRecovery){
      std::cerr<<"SOURCE_QUARANTINE_FAIL scenario="<<scenario<<"\n";
      return 1;
    }
    if(expectRecovery){
      const std::string ambiguousBytes=disk.bytes;
      const int attemptsBeforeRetry=clearCount;
      disk.shortWrite=false;
      disk.verifyOpenFail=false;
      disk.removeOneByteAfterClose=false;
      disk.mutateAfterClose=false;
      disk.mutateOnRead=false;
      clearAllowed=true;
      if(quarantinePending(reason) || disk.bytes!=ambiguousBytes ||
         clearCount!=attemptsBeforeRetry || !journalRecoveryRequired){
        std::cerr<<"SOURCE_QUARANTINE_RETRY_MUTATED scenario="<<scenario<<"\n";
        return 1;
      }
    }
    if((scenario>=5 && scenario<=9) || scenario==11){
      // Simulate volatile latch loss on reboot while retaining LittleFS bytes.
      const std::string rebootBytes=disk.bytes;
      const int clearsBeforeReboot=clearCount;
      journalRecoveryRequired=false;
      disk.hasWritten=false;
      bool rebootOk=quarantinePending(reason);
      bool tornTail=(scenario==5 || scenario==7 || scenario==8);
      if(tornTail){
        if(rebootOk || !journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot || pendingPulses!=4){
          std::cerr<<"SOURCE_QUARANTINE_TORN_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      } else {
        if(!rebootOk || journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot+1 || pendingPulses!=0){
          std::cerr<<"SOURCE_QUARANTINE_IDEMPOTENT_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      }
    }
  }
  std::cout<<"SOURCE_QUARANTINE_PASS 16/16 scenarios (physical power cut NOT tested)\n";
}
'''

def extract(src: str, signature: str) -> str:
    pos = src.find(signature)
    if pos < 0:
        raise RuntimeError(f"Missing real function: {signature}")
    brace = src.find("{", pos)
    depth = 0
    for i in range(brace, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[pos:i + 1]
    raise RuntimeError(f"Unbalanced source: {signature}")

for board, ino in BOARDS:
    source = ino.read_text(encoding="utf-8")
    actual = CPP.replace("@@SOURCE_ENCODE@@", extract(source, "String quarantineLogField("))
    actual = actual.replace("@@SOURCE_INSPECT@@", extract(source, "bool inspectQuarantineLog("))
    actual = actual.replace("@@SOURCE_APPEND@@", extract(source, "bool appendQuarantineRecord("))
    actual = actual.replace("@@SOURCE_QUARANTINE@@", extract(source, "bool quarantinePending("))
    with tempfile.TemporaryDirectory(prefix="phx-hw-q-") as temp:
        cpp = Path(temp, "test.cpp")
        binary = Path(temp, "test")
        cpp.write_text(actual, encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(cpp), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print(f"{board}: compiled exact extracted source")
print("PHX-HARDWARE: 32/32 source-extracted host scenarios PASS; no hardware evidence")
