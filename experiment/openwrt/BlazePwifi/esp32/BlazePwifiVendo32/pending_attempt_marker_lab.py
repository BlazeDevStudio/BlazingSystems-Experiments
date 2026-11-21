#!/usr/bin/env python3
"""PHX-HARDWARE source-extracted one-shot coin POST attempt-marker lab.

Compiles the actual pending record/checksum/read/load/marker/clear/POST-gate
functions from both sketches against fault-injected fake LittleFS.
Host simulation only; physical flash power-cut durability is NOT tested.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "esp8266/BlazePwifiVendo"))
from firmware_lab_source import extract_block, extract_function
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)

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
  std::vector<uint8_t>* bytes=nullptr;
  bool writable=false,shortWrite=false;
  size_t readLimit=SIZE_MAX;
  File()=default;
  File(std::vector<uint8_t>* p,bool w,bool sw,size_t lim):bytes(p),writable(w),shortWrite(sw),readLimit(lim){}
  explicit operator bool()const{return bytes!=nullptr;}
  size_t size()const{return bytes?bytes->size():0;}
  size_t readBytes(char*out,size_t requested){
    if(!bytes||writable)return 0;
    size_t n=std::min({requested,bytes->size(),readLimit});
    if(n)std::memcpy(out,bytes->data(),n);
    return n;
  }
  size_t write(const uint8_t*data,size_t requested){
    if(!bytes||!writable)return 0;
    size_t n=shortWrite&&requested?requested-1:requested;
    bytes->insert(bytes->end(),data,data+n);
    return n;
  }
  void flush(){}
  void close(){}
};
struct FakeLittleFS {
  std::map<std::string,std::vector<uint8_t>> files;
  std::string failWriteOpenPath,failReadOpenPath,failRemovePath;
  bool shortWrite=false;
  size_t readLimit=SIZE_MAX;
  std::vector<std::string> removed;
  bool exists(const char*p)const{return files.count(p)!=0;}
  File open(const char*p,const char*mode){
    if(std::strcmp(mode,"w")==0){
      if(failWriteOpenPath==p)return File{};
      auto&v=files[p];v.clear();return File(&v,true,shortWrite,readLimit);
    }
    if(std::strcmp(mode,"r")==0){
      if(failReadOpenPath==p)return File{};
      auto i=files.find(p);if(i==files.end())return File{};
      return File(&i->second,false,shortWrite,readLimit);
    }
    return File{};
  }
  bool remove(const char*p){
    removed.emplace_back(p);
    if(failRemovePath==p)return false;
    return files.erase(p)>0;
  }
} LittleFS;
struct FakeSerial{template<class T>void println(const T&){} } Serial;

@@STRUCT@@
const uint32_t PENDING_MAGIC=@@MAGIC@@;
bool fsReady=true,pendingReady=false,journalRecoveryRequired=false,pendingPostAttempted=false;
bool outputPolarityKnown=true, pinConfigSafe=true;
uint8_t pendingPulses=0;
uint32_t lastSend=0;
String pendingNonce,pendingTarget;
@@CHECKSUM@@
@@READ@@
@@SAME@@
@@LOAD@@
@@MARK@@
@@ATTEMPT_MATCH@@
@@CLEAR@@
@@GATE@@
PendingRecord record(const char*n="nonce12345678",const char*t="target12345678",uint8_t p=4){
  PendingRecord r{};r.magic=PENDING_MAGIC;r.pulses=p;
  std::strcpy(r.nonce,n);std::strcpy(r.target,t);r.checksum=pendingChecksum(r);return r;
}
void store(const char*p,const PendingRecord&r){
  const uint8_t*b=reinterpret_cast<const uint8_t*>(&r);
  LittleFS.files[p]=std::vector<uint8_t>(b,b+sizeof(r));
}
void reboot(){
  fsReady=true;pendingReady=false;journalRecoveryRequired=false;pendingPostAttempted=false;pinConfigSafe=true;
  pendingPulses=0;lastSend=0;pendingNonce.clear();pendingTarget.clear();
}
#define CHECK(c,n) do{if(!(c)){std::cerr<<"ATTEMPT_MARKER_FAIL "<<n<<"\n";return 1;}++passed;}while(0)
int main(){
  int passed=0;
  LittleFS=FakeLittleFS{};reboot();loadPending();
  CHECK(!pendingReady&&!journalRecoveryRequired&&!canAttemptCoinPost(),"empty journal");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  pinConfigSafe=false;
  CHECK(pendingReady&&!canAttemptCoinPost(),"unsafe GPIO map blocks pending dispatch");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  CHECK(pendingReady&&!journalRecoveryRequired&&canAttemptCoinPost(),"unattempted pending eligible");
  CHECK(markPendingPostAttempt()&&LittleFS.exists("/pending.attempt")&&pendingPostAttempted&&
        !canAttemptCoinPost()&&!markPendingPostAttempt(),"verified marker is one-shot");
  reboot();loadPending();
  CHECK(pendingReady&&pendingPostAttempted&&journalRecoveryRequired&&!canAttemptCoinPost(),
        "matching marker blocks reboot replay");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());
  store("/pending.attempt",record("nonce9999999999","target12345678"));loadPending();
  CHECK(journalRecoveryRequired&&pendingReady&&!canAttemptCoinPost(),"mismatched marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());
  auto bad=record();bad.checksum^=1;store("/pending.attempt",bad);loadPending();
  CHECK(journalRecoveryRequired&&pendingReady&&!canAttemptCoinPost(),"bad marker checksum");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());
  auto torn=record();const uint8_t*tb=reinterpret_cast<const uint8_t*>(&torn);
  LittleFS.files["/pending.attempt"]=std::vector<uint8_t>(tb,tb+sizeof(torn)-1);loadPending();
  CHECK(journalRecoveryRequired&&pendingReady&&!canAttemptCoinPost(),"truncated marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.attempt",record());loadPending();
  CHECK(journalRecoveryRequired&&!pendingReady&&!canAttemptCoinPost(),"orphan marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  LittleFS.failWriteOpenPath="/pending.attempt";
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&!LittleFS.exists("/pending.attempt")&&
        !canAttemptCoinPost(),"marker open failure");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  LittleFS.shortWrite=true;
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&LittleFS.exists("/pending.attempt")&&
        !canAttemptCoinPost(),"short marker write");
  LittleFS.shortWrite=false;reboot();loadPending();
  CHECK(journalRecoveryRequired&&!canAttemptCoinPost(),"short write reboot hold");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  LittleFS.failReadOpenPath="/pending.attempt";
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&LittleFS.exists("/pending.attempt")&&
        !canAttemptCoinPost(),"marker readback failure");
  LittleFS.failReadOpenPath.clear();reboot();loadPending();
  CHECK(journalRecoveryRequired&&!canAttemptCoinPost(),"readback failure reboot hold");

  LittleFS=FakeLittleFS{};reboot();pendingReady=true;pendingPulses=4;
  pendingNonce="nonce12345678";pendingTarget="target12345678";
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&!LittleFS.exists("/pending.attempt"),
        "RAM-only pending cannot dispatch");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();markPendingPostAttempt();
  CHECK(clearPending()&&LittleFS.files.empty()&&pendingPulses==0&&!pendingReady&&
        !pendingPostAttempted&&!journalRecoveryRequired&&LittleFS.removed.size()==2&&
        LittleFS.removed[0]=="/pending.dat"&&LittleFS.removed[1]=="/pending.attempt",
        "successful disposition removes pending before marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();markPendingPostAttempt();
  LittleFS.failRemovePath="/pending.dat";
  CHECK(!clearPending()&&journalRecoveryRequired&&LittleFS.exists("/pending.dat")&&
        LittleFS.exists("/pending.attempt"),"pending delete failure retains both");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();markPendingPostAttempt();
  LittleFS.failRemovePath="/pending.attempt";
  CHECK(!clearPending()&&journalRecoveryRequired&&!LittleFS.exists("/pending.dat")&&
        LittleFS.exists("/pending.attempt"),"marker delete failure leaves orphan");
  LittleFS.failRemovePath.clear();reboot();loadPending();
  CHECK(journalRecoveryRequired&&!pendingReady&&!canAttemptCoinPost(),"orphan after partial clear");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());
  store("/pending.new",record("nonce2234567890","target22345678"));
  store("/pending.attempt",record());loadPending();
  CHECK(journalRecoveryRequired&&!canAttemptCoinPost()&&LittleFS.files.size()==3,
        "multiple pending candidates preserved");


  // clearPending must not delete the only remaining attempt evidence.
  LittleFS=FakeLittleFS{};reboot();pendingReady=true;pendingPostAttempted=true;
  pendingPulses=4;pendingNonce="nonce12345678";pendingTarget="target12345678";
  store("/pending.attempt",record());
  CHECK(!clearPending()&&journalRecoveryRequired&&LittleFS.exists("/pending.attempt")&&
        LittleFS.files.size()==1&&LittleFS.removed.empty()&&pendingPulses==4&&pendingReady,
        "orphan attempt marker retained by clear");

  // Multiple candidates remain ambiguous even when one matches the marker.
  LittleFS=FakeLittleFS{};reboot();pendingReady=true;pendingPostAttempted=true;
  pendingPulses=4;pendingNonce="nonce12345678";pendingTarget="target12345678";
  store("/pending.dat",record());store("/pending.bak",record());store("/pending.attempt",record());
  CHECK(!clearPending()&&journalRecoveryRequired&&LittleFS.files.size()==3&&LittleFS.removed.empty(),
        "duplicate candidates retained by clear");

  // A single but different journal must not be erased by a matching RAM marker.
  LittleFS=FakeLittleFS{};reboot();pendingReady=true;pendingPostAttempted=true;
  pendingPulses=4;pendingNonce="nonce12345678";pendingTarget="target12345678";
  store("/pending.dat",record("nonce99999999","target12345678"));
  store("/pending.attempt",record());
  CHECK(!clearPending()&&journalRecoveryRequired&&LittleFS.exists("/pending.dat")&&
        LittleFS.exists("/pending.attempt")&&LittleFS.removed.empty(),
        "mismatched pending candidate retained by clear");

  // A corrupt single candidate must also be preserved for reconciliation.
  LittleFS=FakeLittleFS{};reboot();pendingReady=true;pendingPostAttempted=true;
  pendingPulses=4;pendingNonce="nonce12345678";pendingTarget="target12345678";
  auto corruptPending=record();corruptPending.checksum^=1;
  store("/pending.dat",corruptPending);store("/pending.attempt",record());
  CHECK(!clearPending()&&journalRecoveryRequired&&LittleFS.exists("/pending.dat")&&
        LittleFS.exists("/pending.attempt")&&LittleFS.removed.empty(),
        "corrupt pending candidate retained by clear");


  // A POST marker must bind exactly one pending journal candidate, not merely
  // find one matching file while another candidate remains ambiguous.
  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  store("/pending.bak",record("nonce99999999","target12345678"));
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&
        !LittleFS.exists("/pending.attempt")&&pendingReady&&pendingPulses==4,
        "conflicting extra pending candidate denies POST marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  store("/pending.bak",record());
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&
        !LittleFS.exists("/pending.attempt")&&pendingReady&&pendingPulses==4,
        "duplicate extra pending candidate denies POST marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.dat",record());loadPending();
  LittleFS.files["/pending.bak"]={0x01,0x02};
  CHECK(!markPendingPostAttempt()&&journalRecoveryRequired&&
        !LittleFS.exists("/pending.attempt")&&pendingReady&&pendingPulses==4,
        "corrupt extra pending candidate denies POST marker");


  // A single recovered candidate in either interrupted-rotation slot remains
  // eligible for a one-shot marker; the exact-one rule must not require /pending.dat.
  LittleFS=FakeLittleFS{};reboot();store("/pending.new",record());loadPending();
  CHECK(pendingReady&&!journalRecoveryRequired&&markPendingPostAttempt()&&
        LittleFS.exists("/pending.attempt")&&pendingPostAttempted,
        "single pending.new candidate permits marker");

  LittleFS=FakeLittleFS{};reboot();store("/pending.bak",record());loadPending();
  CHECK(pendingReady&&!journalRecoveryRequired&&markPendingPostAttempt()&&
        LittleFS.exists("/pending.attempt")&&pendingPostAttempted,
        "single pending.bak candidate permits marker");

  std::cout<<"PENDING_ATTEMPT_MARKER_PASS "<<passed<<"/29 source-extracted cases; physical power cuts NOT TESTED\n";
}
'''

for board,path in BOARDS:
    src=path.read_text(encoding="utf-8")
    loop=extract_function(src,"loop")
    gate=extract_function(src,"canAttemptCoinPost")
    if "!pendingPostAttempted" not in gate:
        raise SystemExit(f"{board}: previous attempt is not denied by POST gate")
    if loop.count('post("coin"')!=1 or loop.find("markPendingPostAttempt()")<0 or loop.find("markPendingPostAttempt()")>loop.find('post("coin"'):
        raise SystemExit(f"{board}: marker is not before the only coin POST call")
    coin_post=loop.find('String r=post("coin"')
    if coin_post < 0 or "handleCoinPostResponse(r);" not in loop[coin_post:]:
        raise SystemExit(f"{board}: coin POST does not delegate to disposition helper")
    handler=extract_function(src,"handleCoinPostResponse")
    auth_guard=handler.find("if(!coinPostDispositionVerified(response,pendingNonce,pendingTarget,pendingPulses))")
    clear_pending=handler.find("clearPending();")
    quarantine=handler.find("quarantinePending(response);")
    if "journalRecoveryRequired=true;" not in handler or auth_guard < 0 or (clear_pending >= 0 and clear_pending < auth_guard) or (quarantine >= 0 and quarantine < auth_guard):
        raise SystemExit(f"{board}: ambiguous POST outcome is not fail-closed in disposition helper")
    magic=re.search(r"(?:static\s+)?const uint32_t PENDING_MAGIC\s*=\s*(0x[0-9A-Fa-f]+)",src)
    if not magic: raise SystemExit(f"{board}: missing pending magic")
    values={
      "@@STRUCT@@":extract_block(src,"struct PendingRecord {")+";",
      "@@MAGIC@@":magic.group(1),
      "@@CHECKSUM@@":extract_function(src,"pendingChecksum"),
      "@@READ@@":extract_function(src,"readPendingFile"),
      "@@SAME@@":extract_function(src,"samePendingRecord"),
      "@@LOAD@@":extract_function(src,"loadPending"),
      "@@MARK@@":extract_function(src,"markPendingPostAttempt"),
      "@@ATTEMPT_MATCH@@":extract_function(src,"pendingAttemptMarkerMatches"),
      "@@CLEAR@@":extract_function(src,"clearPending"),
      "@@GATE@@":gate,
    }
    cpp=CPP
    for token,value in values.items(): cpp=cpp.replace(token,value)
    with tempfile.TemporaryDirectory(prefix="phx-attempt-marker-") as folder:
      cp=Path(folder)/"test.cpp";exe=Path(folder)/"test"
      cp.write_text(cpp,encoding="utf-8")
      subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O2",str(cp),"-o",str(exe)],check=True)
      subprocess.run([str(exe)],check=True)
    print(f"{board}: exact source functions compiled and tested")
print("PHX-HARDWARE: 29/29 source-extracted cases per board (58/58 total) PASS; actual flash NOT TESTED")
