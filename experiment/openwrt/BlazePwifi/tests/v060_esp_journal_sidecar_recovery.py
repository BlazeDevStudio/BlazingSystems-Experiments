#!/usr/bin/env python3
"""PHX-VERIFY: crash-stage fault tests execute the real ESP loadPending() bodies.

All flash files and rename faults are synthetic PRIVATE RAM fixtures. This does
NOT demonstrate actual LittleFS fsync, real power cuts or accepted customer cash.
"""
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "esp/libraries/BlazePendingSequence/src"
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

def load_pending_function(text):
    m = re.search(r"\bbool\s+loadPending\s*\(\s*\)\s*\{", text)
    assert m, "Missing real firmware loadPending"
    level = 0
    for pos in range(m.end() - 1, len(text)):
        if text[pos] == "{": level += 1
        if text[pos] == "}":
            level -= 1
            if not level: return text[m.start():pos + 1]
    raise AssertionError("Unterminated real firmware loadPending")

STUBS = r"""
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include "v060_pending_sequence.h"
struct String: std::string {
 using std::string::string;
 String(const std::string& s):std::string(s){}
};
bool fsReady=true, pendingReady=false;
uint8_t pendingPulses=0;
uint32_t lastSend=0;
BpPendingSequence pendingSequenceState;
String pendingNonce, pendingTarget;
struct SerialImpl {void println(const char*){}} Serial;
struct Flash {
 std::map<std::string,BpPendingSequence> files;
 bool failRename=false;
 bool exists(const char *p)const {return files.count(p)!=0;}
 bool remove(const char *p){return files.erase(p)!=0;}
 bool rename(const char *from,const char *to){
   if(failRename||!exists(from)) return false;
   files[to]=files.at(from);files.erase(from);return true;
 }
} LittleFS;
bool readPendingFile(const char *path,BpPendingSequence &s,bool &legacy){
 if(!LittleFS.exists(path))return false;
 s=LittleFS.files.at(path); legacy=false;
 return bp_pending_sequence_valid(&s);
}
bool persistPendingSequence(const BpPendingSequence &s) {
 if(!bp_pending_sequence_valid(&s))return false;
 LittleFS.files["/pending.dat"]=s;return true;
}
void reset(){
 LittleFS.files.clear(); LittleFS.failRename=false;
 fsReady=true;pendingReady=false;pendingPulses=0;lastSend=5;
 pendingNonce="";pendingTarget="";
 bp_pending_sequence_init(&pendingSequenceState);
}
BpPendingSequence event(int pulses,const char *nonce="abcdef0102030405"){
 BpPendingSequence s; bp_pending_sequence_init(&s);
 if(!bp_pending_sequence_reserve(&s,(uint8_t)pulses,nonce,"abcdef0102030405"))
  throw std::runtime_error("bad fixture");
 return s;
}
void require(bool yes,const char*name){
 if(!yes)throw std::runtime_error(name);
 std::cout<<"PASS "<<name<<"\n";
}
"""

CASES = r"""
int main() {
 try{
 // Crash after writing and flushing 2-pulse /pending.new, BEFORE moving dat
 // to backup. Old /pending.dat still contains one valid observed pulse.
 reset();LittleFS.files["/pending.dat"]=event(1);
 LittleFS.files["/pending.new"]=event(2);
 require(loadPending() && pendingPulses==2 && pendingReady &&
         LittleFS.files.count("/pending.dat")==1 &&
         LittleFS.files.count("/pending.new")==0,
         "recover flushed pending.new with second pulse instead of stale dat");
 // A valid sidecar must not make recovered state look successful when its
 // promotion to canonical flash path fails.
 reset();LittleFS.files["/pending.dat"]=event(1);
 LittleFS.files["/pending.new"]=event(2);
 LittleFS.failRename=true;
 require(!loadPending(), "block startup when new sidecar cannot be promoted");
 // Known valid but different event identity at equal sequence/epoch should
 // never silently rebind paid pulses. Quarantine until operator reconciliation.
 reset();LittleFS.files["/pending.dat"]=event(1);
 LittleFS.files["/pending.new"]=event(2,"fedcba0102030405");
 require(!loadPending(), "refuse different paid event ID at same sequence");
 // An ACKed transaction persisted in newer .new must supersede older pending.
 reset();LittleFS.files["/pending.dat"]=event(2);
 auto ack=event(2);if(!bp_pending_sequence_commit(&ack))return 90;
 LittleFS.files["/pending.new"]=ack;
 require(loadPending() && !pendingReady && pendingPulses==0 &&
         pendingSequenceState.acked_sequence==1,
         "restore newer durable ACK state after rename crash");
 // An explicit known rejected pending event creates a valid later idle state
 // with the same acknowledged sequence, distinct from an earlier idle state.
 reset();LittleFS.files["/pending.dat"]=event(2);
 auto dropped=event(2);if(!bp_pending_sequence_abandon(&dropped))return 91;
 LittleFS.files["/pending.new"]=dropped;
 require(loadPending() && !pendingReady && pendingPulses==0,
         "restore newer known rejection idle state");
 // A partial/corrupt sidecar does not outrank the last intact journal.
 reset();LittleFS.files["/pending.dat"]=event(1);
 auto corrupt=event(2);corrupt.checksum^=1;
 LittleFS.files["/pending.new"]=corrupt;
 require(loadPending() && pendingReady && pendingPulses==1,
         "recover valid dat if partial new invalid");
 // If primary is absent after dat->bak rename, newest valid sidecar survives.
 reset();LittleFS.files["/pending.bak"]=event(1);
 LittleFS.files["/pending.new"]=event(2);
 require(loadPending() && pendingPulses==2,
         "recover new sidecar after dat backup stage");
 // No prior journal: create empty only when there are no unexplained files.
 reset();require(loadPending() && !pendingReady && pendingPulses==0,
         "fresh empty journal initializes safely");
 } catch(const std::exception& e){
   std::cerr<<"RED crash recovery: "<<e.what()<<"\n";return 23;
 }
 return 0;
}
"""

failed = []
for board,path in BOARDS.items():
    src = path.read_text(encoding="utf-8")
    body = load_pending_function(src)
    with tempfile.TemporaryDirectory(prefix="blaze-vendo-rename-lab-") as tmp:
        cpp = Path(tmp)/"repro.cpp"
        exe = Path(tmp)/"repro"
        cpp.write_text(STUBS+body+CASES)
        compile_run = subprocess.run(["g++","-std=c++17","-Wall","-Wextra",
                                      "-Werror","-O0","-I",str(HEADER),
                                      str(cpp),"-o",str(exe)],
                                     capture_output=True,text=True,timeout=30)
        if compile_run.returncode:
            print(board,"HARNESS_COMPILE_FAILED",compile_run.stderr[-2500:])
            failed.append(board)
            continue
        run = subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
        print(board,"GREEN" if run.returncode==0 else "RED",
              run.stdout.strip(),run.stderr.strip())
        if run.returncode: failed.append(board)
if failed:
    sys.exit("PHX-VERIFY P0 journal sidecar crash-stage RED: "+",".join(failed))
print("PHX-VERIFY 8/8 per ESP board source-extracted crash-stage tests PASS; physical_powercut_verified=0")
