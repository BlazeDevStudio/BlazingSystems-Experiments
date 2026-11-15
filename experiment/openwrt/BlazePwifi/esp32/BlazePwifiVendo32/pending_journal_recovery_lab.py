#!/usr/bin/env python3
"""PHX-HARDWARE source-extracted pending-journal boot safety LAB.

Compiles actual ESP32 and ESP8266 C++ readPendingFile, pendingChecksum,
loadPending and applyOutputs functions against a fake LittleFS. Verifies
corrupt/ambiguous files are preserved and no coin acceptance resumes.
NOT real-flash or power-cut evidence.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SKETCHES = [
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
]

def extract(src: str, signature: str) -> str:
    start = src.find(signature)
    if start < 0:
        raise RuntimeError(f"missing {signature}")
    brace = src.find("{", start)
    level = 0
    for pos in range(brace, len(src)):
        if src[pos] == "{":
            level += 1
        elif src[pos] == "}":
            level -= 1
            if level == 0:
                return src[start:pos+1]
    raise RuntimeError(f"unclosed {signature}")

CPP = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>
using String=std::string;
struct File {
  std::vector<uint8_t> data;
  bool opened=false;
  size_t readLimit=SIZE_MAX;
  explicit operator bool() const {return opened;}
  size_t readBytes(char *out, size_t requested) {
    size_t n=std::min({requested,data.size(),readLimit});
    if(n) std::memcpy(out,data.data(),n);
    return n;
  }
  void close(){}
};
struct FakeLittleFS {
  std::map<std::string,std::vector<uint8_t>> files;
  bool failOpen=false;
  size_t readLimit=SIZE_MAX;
  unsigned removeCalls=0,renameCalls=0;
  bool exists(const char *p)const{return files.count(p)!=0;}
  File open(const char *p,const char *mode){
    (void)mode;
    auto i=files.find(p);
    if(failOpen || i==files.end()) return File{};
    return File{i->second,true,readLimit};
  }
  bool remove(const char *p){++removeCalls;return files.erase(p)>0;}
  bool rename(const char *from,const char *to){
    ++renameCalls;
    auto it=files.find(from);
    if(it==files.end())return false;
    files[to]=it->second;files.erase(it);return true;
  }
} LittleFS;
struct FakeSerial {void println(const char*){}} Serial;
@@PENDING_STRUCT@@
const uint32_t PENDING_MAGIC=@@MAGIC@@;
bool fsReady=true,pendingReady=false,journalRecoveryRequired=false;
bool pollIntakeSuspended=false;
bool insertMode=true,controllerEnabled=true,coinEnabled=true;
bool ledEnabled=true,relayEnabled=true;
bool runRelayActiveHigh=true,runLedActiveHigh=true;
int runRelayPin=5,runLedPin=2;
bool relayOn=false,ledOn=false;
uint32_t lastSend=42;
uint8_t pendingPulses=0;
String pendingNonce,pendingTarget;
void writeLogical(int pin,bool on,bool){
  if(pin==runRelayPin)relayOn=on;
  if(pin==runLedPin)ledOn=on;
}
@@CHECKSUM@@
@@READ@@
@@LOAD@@
@@OUTPUTS@@
PendingRecord validRecord(){
  PendingRecord r{};
  r.magic=PENDING_MAGIC;
  r.pulses=3;
  std::strcpy(r.nonce,"nonce12345678");
  std::strcpy(r.target,"target12345678");
  r.checksum=pendingChecksum(r);
  return r;
}
std::vector<uint8_t> bytes(const PendingRecord &r){
  const uint8_t* p=reinterpret_cast<const uint8_t*>(&r);
  return std::vector<uint8_t>(p,p+sizeof(r));
}
int main(){
  for(int scenario=0;scenario<16;++scenario){
    LittleFS=FakeLittleFS{};
    fsReady=true;pendingReady=false;journalRecoveryRequired=false;
    pendingPulses=0;pendingNonce.clear();pendingTarget.clear();lastSend=42;
    relayOn=false;ledOn=false;
    auto r=validRecord();
    switch(scenario){
      case 0:break; // no journal: acceptance allowed with these synthetic auth gates
      case 1:LittleFS.files["/pending.dat"]=bytes(r);break;
      case 2:LittleFS.files["/pending.new"]=bytes(r);break;
      case 3:LittleFS.files["/pending.bak"]=bytes(r);break;
      case 4:r.checksum^=1;LittleFS.files["/pending.dat"]=bytes(r);break;
      case 5:{auto v=bytes(r);v.resize(v.size()-4);LittleFS.files["/pending.dat"]=v;break;}
      case 6:std::memset(r.nonce,'X',sizeof(r.nonce));r.checksum=pendingChecksum(r);
             LittleFS.files["/pending.dat"]=bytes(r);break;
      case 7:std::memset(r.target,'Y',sizeof(r.target));r.checksum=pendingChecksum(r);
             LittleFS.files["/pending.dat"]=bytes(r);break;
      case 8:std::strcpy(r.nonce,"short");r.checksum=pendingChecksum(r);
             LittleFS.files["/pending.dat"]=bytes(r);break;
      case 9:std::strcpy(r.target,"tiny");r.checksum=pendingChecksum(r);
             LittleFS.files["/pending.dat"]=bytes(r);break;
      case 10:r.pulses=21;r.checksum=pendingChecksum(r);
              LittleFS.files["/pending.dat"]=bytes(r);break;
      case 11:LittleFS.files["/pending.dat"]=bytes(r);
              LittleFS.files["/pending.new"]={0x01,0x02};break;
      case 12:LittleFS.files["/pending.dat"]=bytes(r);
              r.pulses=5;r.checksum=pendingChecksum(r);
              LittleFS.files["/pending.bak"]=bytes(r);break;
      case 13:LittleFS.files["/pending.new"]=bytes(r);
              LittleFS.files["/pending.bak"]=bytes(r);break;
      case 14:LittleFS.files["/pending.dat"]=bytes(r);
              LittleFS.failOpen=true;break;
      case 15:LittleFS.files["/pending.dat"]=bytes(r);
              LittleFS.readLimit=sizeof(PendingRecord)-1;break;
    }
    const auto originalFiles=LittleFS.files;
    loadPending();
    applyOutputs();
    const bool expectRecovery=scenario>=4;
    const bool expectPending=scenario>=1 && scenario<=3;
    const bool expectRelay=scenario==0;
    if(journalRecoveryRequired!=expectRecovery ||
       pendingReady!=expectPending ||
       relayOn!=expectRelay || ledOn!=expectRelay ||
       pendingPulses!=(expectPending?3:0) ||
       LittleFS.files!=originalFiles ||
       LittleFS.removeCalls!=0 || LittleFS.renameCalls!=0 ||
       (expectPending && (pendingNonce!="nonce12345678" || pendingTarget!="target12345678"))) {
      std::cerr<<"PENDING_JOURNAL_LAB_FAIL case="<<scenario
               <<" recovery="<<journalRecoveryRequired
               <<" pendingReady="<<pendingReady
               <<" pulses="<<(int)pendingPulses
               <<" relay="<<relayOn<<"\n";
      return 1;
    }
  }
  std::cout<<"PENDING_JOURNAL_LAB_PASS 16/16 source-extracted cases; physical tests NOT RUN\n";
  return 0;
}
'''

for board, path in SKETCHES:
    source = path.read_text(encoding="utf-8")
    for sig, token in [
        ("bool savePending(){", "journalRecoveryRequired"),
        ("void clearPending(){", "journalRecoveryRequired"),
        ("void applyOutputs(){", "!journalRecoveryRequired"),
        ("void loop(){", "!journalRecoveryRequired"),
    ]:
        if token not in extract(source,sig):
            raise SystemExit(f"{board}: no journal deny gate in {sig}")
    if "strlen(r.nonce)" in extract(source,"bool readPendingFile(") or "strlen(r.target)" in extract(source,"bool readPendingFile("):
        raise SystemExit(f"{board}: unsafe unbounded pending string read")
    magic = re.search(r"PENDING_MAGIC\s*=\s*(0x[0-9A-Fa-f]+)", source)
    if not magic:
        raise SystemExit(f"{board}: missing real PENDING_MAGIC")
    cpp = CPP
    for name, value in {
        "@@PENDING_STRUCT@@":extract(source,"struct PendingRecord {")+";",
        "@@MAGIC@@":magic.group(1),
        "@@CHECKSUM@@":extract(source,"uint32_t pendingChecksum("),
        "@@READ@@":extract(source,"bool readPendingFile("),
        "@@LOAD@@":extract(source,"void loadPending(){"),
        "@@OUTPUTS@@":extract(source,"void applyOutputs(){"),
    }.items():
        cpp=cpp.replace(name,value)
    with tempfile.TemporaryDirectory(prefix="phx-pending-recovery-") as tmp:
        path_cpp=Path(tmp)/"pending.cpp"
        path_bin=Path(tmp)/"pending"
        path_cpp.write_text(cpp,encoding="utf-8")
        subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O2",
                        str(path_cpp),"-o",str(path_bin)],check=True)
        subprocess.run([str(path_bin)],check=True)
    print(f"{board}: exact source journal parser/recovery and output gate verified")
print("PHX-HARDWARE: 32/32 synthetic pending journal cases PASS; actual flash NOT TESTED")
