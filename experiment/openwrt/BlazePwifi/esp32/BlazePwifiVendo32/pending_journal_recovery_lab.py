#!/usr/bin/env python3
"""PHX-HARDWARE source-extracted pending-journal boot safety LAB.

Compiles actual ESP32 and ESP8266 C++ readPendingFile, pendingChecksum,
loadPending, clearPending and applyOutputs functions against a fake LittleFS.
Verifies corrupt/ambiguous files are preserved, destructive clears are
preflighted, and no coin acceptance resumes.
NOT real-flash or power-cut evidence.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "esp8266/BlazePwifiVendo"))
from firmware_lab_source import extract_block, extract_function

SKETCHES = [
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
]

def extract(src: str, signature: str) -> str:
    if signature.startswith("struct "):
        return extract_block(src, signature)
    name = signature.split("(", 1)[0].split()[-1]
    return extract_function(src, name)


def verify_lexical_extractor_fixture():
    probes = (
        ("ordinary string", 'void target() { const char *brace = "}"; int retained = 1; }\nvoid next() { return; }\n'),
        ("raw string", 'void target() { const char *raw = R"tag(})tag"; int retained = 1; }\nvoid next() { return; }\n'),
        ("line comment", 'void target() { // }\n int retained = 1; }\nvoid next() { return; }\n'),
        ("block comment", 'void target() { /* } */ int retained = 1; }\nvoid next() { return; }\n'),
    )
    for label, probe in probes:
        body = extract(probe, "void target()")
        if "int retained = 1;" not in body or "void next" in body:
            raise RuntimeError(
                f"PENDING_JOURNAL_EXTRACTOR_FAIL: {label} brace truncated target()"
            )
    print("PENDING_JOURNAL_LEXICAL_EXTRACTOR_PASS 4/4")


verify_lexical_extractor_fixture()

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
  size_t size() const {return data.size();}
  size_t readBytes(char *out, size_t requested) {
    size_t n=std::min({requested,data.size(),readLimit});
    if(n) std::memcpy(out,data.data(),n);
    return n;
  }
  void close(){}
};
struct FakeLittleFS {
  std::map<std::string,std::vector<uint8_t>> files;
  bool failOpen=false,failRemove=false,ghostRemove=false;
  size_t readLimit=SIZE_MAX;
  unsigned removeCalls=0,renameCalls=0;
  bool exists(const char *p)const{return files.count(p)!=0;}
  File open(const char *p,const char *mode){
    (void)mode;
    auto i=files.find(p);
    if(failOpen || i==files.end()) return File{};
    return File{i->second,true,readLimit};
  }
  bool remove(const char *p){
    ++removeCalls;
    if(failRemove)return false;
    if(ghostRemove)return true;
    return files.erase(p)>0;
  }
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
bool fsReady=true,pendingReady=false,journalRecoveryRequired=false,pendingPostAttempted=false;
bool pollIntakeSuspended=false, pinConfigSafe=true;
bool outputPolarityKnown=true;
// This journal-recovery fixture exercises stored-record decisions, not ISR
// delivery. The separate poll-loop lab covers asynchronous edge transitions.
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
bool insertMode=true,controllerEnabled=true,coinEnabled=true;
bool ledEnabled=true,relayEnabled=true;
bool runRelayActiveHigh=true,runLedActiveHigh=true;
int runRelayPin=5,runLedPin=2;
bool relayOn=false,ledOn=false;
uint32_t lastSend=42;
uint8_t pendingPulses=0;
String pendingNonce,pendingTarget;
String activeTarget="target-01";
void writeLogical(int pin,bool on,bool){
  if(pin==runRelayPin)relayOn=on;
  if(pin==runLedPin)ledOn=on;
}
@@CHECKSUM@@
@@READ@@
@@SAME_RECORD@@
@@LOAD@@
@@ATTEMPT_MATCH@@
@@CLEAR@@
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
    fsReady=true;pendingReady=false;journalRecoveryRequired=false;pendingPostAttempted=false;
    coinEdgeSequence=0;lastHandledCoinEdgeSequence=0;
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

  for(int scenario=0;scenario<17;++scenario){
    LittleFS=FakeLittleFS{};
    fsReady=true;pendingReady=true;journalRecoveryRequired=false;pendingPostAttempted=true;
    coinEdgeSequence=0;lastHandledCoinEdgeSequence=0;
    pendingPulses=4;pendingNonce="nonce12345678";pendingTarget="target12345678";lastSend=42;
    auto r=validRecord();r.pulses=4;r.checksum=pendingChecksum(r);
    LittleFS.files["/pending.attempt"]=bytes(r);
    switch(scenario){
      case 0:break; // orphan marker: no pending candidate
      case 1:LittleFS.files["/pending.dat"]=bytes(r);break;
      case 2:LittleFS.files["/pending.new"]=bytes(r);break;
      case 3:LittleFS.files["/pending.bak"]=bytes(r);break;
      case 4:LittleFS.files["/pending.dat"]=bytes(r);
             LittleFS.files["/pending.new"]=bytes(r);break;
      case 5:LittleFS.files["/pending.dat"]=bytes(r);
             LittleFS.files["/pending.bak"]=bytes(r);break;
      case 6:LittleFS.files["/pending.new"]=bytes(r);
             LittleFS.files["/pending.bak"]=bytes(r);break;
      case 7:LittleFS.files["/pending.dat"]=bytes(r);LittleFS.failRemove=true;break;
      case 8:LittleFS.files["/pending.dat"]=bytes(r);LittleFS.ghostRemove=true;break;
      case 9:LittleFS.files["/pending.dat"]=bytes(r);fsReady=false;break;
      case 10:LittleFS.files["/pending.dat"]=bytes(r);journalRecoveryRequired=true;break;
      case 11:{auto bad=r;std::strcpy(bad.target,"target99999999");bad.checksum=pendingChecksum(bad);LittleFS.files["/pending.dat"]=bytes(r);LittleFS.files["/pending.attempt"]=bytes(bad);break;}
      case 12:{auto bad=r;std::strcpy(bad.nonce,"nonce99999999");bad.checksum=pendingChecksum(bad);LittleFS.files["/pending.dat"]=bytes(bad);break;}
      case 13:{auto bad=r;bad.checksum^=1;LittleFS.files["/pending.dat"]=bytes(bad);break;}
      case 14:LittleFS.files.erase("/pending.attempt");LittleFS.files["/pending.dat"]=bytes(r);break;
      case 15:pendingPostAttempted=false;LittleFS.files["/pending.dat"]=bytes(r);break;
      case 16:pendingReady=false;LittleFS.files["/pending.dat"]=bytes(r);break;
    }
    const auto originalFiles=LittleFS.files;
    const bool ok=clearPending();
    const bool expectSuccess=scenario>=1 && scenario<=3;
    const bool expectRecovery=!expectSuccess;
    const unsigned expectRemoveCalls=expectSuccess ? 2U : (scenario==7 || scenario==8 ? 1U : 0U);
    const bool filesCorrect=expectSuccess ? LittleFS.files.empty() : LittleFS.files==originalFiles;
    const bool expectPendingReady=(!expectSuccess && scenario!=16);
    if(ok!=expectSuccess || journalRecoveryRequired!=expectRecovery ||
       !filesCorrect || LittleFS.removeCalls!=expectRemoveCalls ||
       pendingReady!=expectPendingReady || pendingPulses!=(expectSuccess?0:4) ||
       pendingNonce!=(expectSuccess?"":"nonce12345678") ||
       pendingTarget!=(expectSuccess?"":"target12345678")){
      std::cerr<<"PENDING_CLEAR_LAB_FAIL case="<<scenario
               <<" ok="<<ok<<" recovery="<<journalRecoveryRequired
               <<" removes="<<LittleFS.removeCalls
               <<" files="<<LittleFS.files.size()<<"\n";
      return 1;
    }
  }
  std::cout<<"PENDING_CLEAR_LAB_PASS 17/17 source-extracted cases; physical tests NOT RUN\n";
  return 0;
}
'''

for board, path in SKETCHES:
    source = path.read_text(encoding="utf-8")
    for sig, token in [
        ("bool savePending(){", "journalRecoveryRequired"),
        ("bool clearPending(){", "journalRecoveryRequired"),
        ("void applyOutputs(){", "!journalRecoveryRequired"),
        ("void sampleCoinPulseEdge(bool active){", "!journalRecoveryRequired"),
    ]:
        if token not in extract(source,sig):
            raise SystemExit(f"{board}: no journal deny gate in {sig}")
    if "sampleCoinPulseEdge(active)" not in extract(source,"void loop(){"):
        raise SystemExit(f"{board}: loop does not call the source pulse-capture helper")
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
        "@@SAME_RECORD@@":extract(source,"bool samePendingRecord("),
        "@@LOAD@@":extract(source,"void loadPending(){"),
        "@@ATTEMPT_MATCH@@":extract(source,"bool pendingAttemptMarkerMatches(){"),
        "@@CLEAR@@":extract(source,"bool clearPending(){"),
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
print("PHX-HARDWARE: 32/32 boot-recovery and 34/34 pending-clear cases PASS; actual flash NOT TESTED")
