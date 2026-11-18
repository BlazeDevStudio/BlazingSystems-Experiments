#!/usr/bin/env python3
"""Exact-source dual-store poll-fault persistence regression for ESP32 and ESP8266.

This host lab models the NVS and EEPROM APIs. It does not emulate flash physics,
power-loss timing, wear, or an independent physical witness.
"""
from pathlib import Path
import subprocess
import tempfile
import sys

ROOT = Path.cwd()
ESP32 = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
ESP8266 = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

def extract_block(source: str, marker: str) -> str:
    start = source.index(marker)
    brace = source.index("{", start)
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise RuntimeError(f"unclosed block: {marker}")

def extract_function(source: str, name: str) -> str:
    marker = name + "("
    index = source.index(marker)
    start = source.rfind("\n", 0, index) + 1
    brace = source.index("{", index)
    depth = 0
    for end in range(brace, len(source)):
        if source[end] == "{":
            depth += 1
        elif source[end] == "}":
            depth -= 1
            if depth == 0:
                return source[start:end + 1]
    raise RuntimeError(f"unclosed function: {name}")

def constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith("static const ") and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

def harness(board: str, source: str) -> str:
    record = extract_block(source, "struct PollFaultRecord") + ";"
    helpers = "\n".join(extract_function(source, name) for name in (
        "pollFaultRecordChecksum",
        "makePollFaultRecord",
        "validPollFaultRecord",
        "pollFaultBackupPresentOrCorrupt",
        "writePollFaultBackup",
        "loadPollPulseFaultLatch",
        "latchPollPulseFault",
    ))
    consts = constants(source, (
        "POLL_FAULT_RECORD_MAGIC",
        "POLL_FAULT_RECORD_VERSION",
        "POLL_FAULT_EEPROM_OFFSET",
        "POLL_FAULT_EEPROM_BYTES",
    ))
    if board == "ESP32":
        backend = r"""
struct Preferences {
  static std::vector<uint8_t> durable;
  bool failPut=false, failRead=false;
  bool isKey(const char*) const { return !durable.empty(); }
  size_t getBytesLength(const char*) const { return durable.size(); }
  size_t putBytes(const char*, const void* src, size_t n) {
    if(failPut) return 0;
    if(!outputsInhibited) persistenceBeforeOutputInhibit=true;
    const uint8_t* p=(const uint8_t*)src;
    durable.assign(p,p+n);
    return n;
  }
  size_t getBytes(const char*, void* dst, size_t n) {
    if(failRead) return 0;
    if(durable.size()<n) return durable.size();
    memcpy(dst,durable.data(),n);
    return n;
  }
};
std::vector<uint8_t> Preferences::durable;
Preferences faultPrefs;
bool pollFaultBackupReady=true;
void resetStorage(){ Preferences::durable.clear(); faultPrefs.failPut=false; faultPrefs.failRead=false; pollFaultBackupReady=true; }
void rebootStorage(){ faultPrefs=Preferences(); pollFaultBackupReady=true; }
void corruptStorage(){ if(!Preferences::durable.empty()) Preferences::durable[0]^=0x01; }
"""
        fail_write = "faultPrefs.failPut=true;"
        fail_read = "faultPrefs.failRead=true;"
        clear_fail = "faultPrefs.failPut=false; faultPrefs.failRead=false;"
        no_marker = "Preferences::durable.clear();"
    else:
        backend = r"""
struct FakeEEPROM {
  static std::vector<uint8_t> flash;
  std::vector<uint8_t> buffer;
  size_t size=0;
  bool ready=true, failCommit=false, failRead=false, failReadAfterCommit=false;
  bool begin(size_t n) {
    if(!ready) return false;
    size=n;
    if(flash.size()<n) flash.resize(n,0xFF);
    buffer.assign(flash.begin(),flash.begin()+n);
    return true;
  }
  void end(){ size=0; buffer.clear(); }
  bool commit(){ if(failCommit) return false; if(!outputsInhibited) persistenceBeforeOutputInhibit=true; flash=buffer; if(failReadAfterCommit) failRead=true; return true; }
  size_t length() const { return size; }
  template<class T> void put(size_t offset,const T& value) {
    memcpy(buffer.data()+offset,&value,sizeof(T));
  }
  template<class T> void get(size_t offset,T& value) {
    if(failRead){ memset(&value,0,sizeof(T)); return; }
    memcpy(&value,buffer.data()+offset,sizeof(T));
  }
};
std::vector<uint8_t> FakeEEPROM::flash;
FakeEEPROM EEPROM;
bool pollFaultBackupReady=true;
void resetStorage(){
  FakeEEPROM::flash.clear(); EEPROM=FakeEEPROM();
  pollFaultBackupReady=EEPROM.begin(POLL_FAULT_EEPROM_BYTES);
}
void rebootStorage(){
  EEPROM.end(); pollFaultBackupReady=EEPROM.begin(POLL_FAULT_EEPROM_BYTES);
}
void corruptStorage(){
  if(FakeEEPROM::flash.size()>POLL_FAULT_EEPROM_OFFSET)
    FakeEEPROM::flash[POLL_FAULT_EEPROM_OFFSET]^=0x01;
  rebootStorage();
}
"""
        fail_write = "EEPROM.failCommit=true;"
        fail_read = "EEPROM.failReadAfterCommit=true;"
        clear_fail = "EEPROM.failCommit=false; EEPROM.failRead=false; EEPROM.failReadAfterCommit=false;"
        no_marker = "FakeEEPROM::flash.clear(); rebootStorage();"

    prelude = r"""
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
uint32_t millis(){ return 123456u; }
struct SerialStub { void println(const char*){} } Serial;
struct LittleFSStub {
  bool marker=false;
  bool exists(const char*) const { return marker; }
} LittleFS;
bool fsReady=true;
bool journalRecoveryRequired=false;
bool insertMode=true;
std::string activeTarget="target";
bool fsMarkerWriteResult=false;
bool outputsInhibited=false;
bool persistenceBeforeOutputInhibit=false;
int outputApplyCount=0;
void applyOutputs(){
  ++outputApplyCount;
  outputsInhibited=journalRecoveryRequired && !insertMode && activeTarget.empty();
}
bool writePollPulseFaultMarker(uint32_t pulseEdges){
  (void)pulseEdges;
  if(!outputsInhibited) persistenceBeforeOutputInhibit=true;
  if(fsMarkerWriteResult) LittleFS.marker=true;
  return fsMarkerWriteResult;
}
"""
    main = r"""
void resetRuntime(){
  journalRecoveryRequired=false;
  insertMode=true;
  activeTarget="target";
  fsReady=true;
  LittleFS.marker=false;
  fsMarkerWriteResult=false;
  outputsInhibited=false;
  persistenceBeforeOutputInhibit=false;
  outputApplyCount=0;
}
void assertBootDenied(){
  journalRecoveryRequired=false;
  insertMode=true;
  activeTarget="target";
  fsReady=true;
  loadPollPulseFaultLatch();
  assert(journalRecoveryRequired);
  assert(!insertMode);
  assert(activeTarget.empty());
}
int main(){
  resetStorage();
  resetRuntime();
  assert(!pollFaultBackupPresentOrCorrupt());

  // LittleFS open/write failure must fall back to the secondary store.
  latchPollPulseFault(3);
  assert(journalRecoveryRequired && !insertMode);
  assert(outputsInhibited);
  assert(!persistenceBeforeOutputInhibit);
  assert(pollFaultBackupPresentOrCorrupt());
  rebootStorage();
  assertBootDenied();

  // A malformed/partial non-empty backup is a deny marker, never a clean state.
  corruptStorage();
  assert(pollFaultBackupPresentOrCorrupt());
  assertBootDenied();

  // Readback failure does not clear the current hold; the committed record is
  // still discovered on the next successful boot read.
  resetStorage();
  resetRuntime();
  READ_FAIL_SETUP
  assert(!writePollFaultBackup(4));
  READ_FAIL_CLEAR
  rebootStorage();
  assertBootDenied();

  // If the secondary store is unavailable, boot fails closed.
  pollFaultBackupReady=false;
  resetRuntime();
  loadPollPulseFaultLatch();
  assert(journalRecoveryRequired && !insertMode);

  // The primary LittleFS marker remains a valid fallback if the secondary
  // store cannot commit.
  resetStorage();
  resetRuntime();
  WRITE_FAIL_SETUP
  fsMarkerWriteResult=true;
  latchPollPulseFault(5);
  assert(journalRecoveryRequired && LittleFS.marker);
  rebootStorage();
  assertBootDenied();

  // If BOTH persistent domains fail, only the current-boot RAM latch remains.
  // This is an explicit residual limitation, not counted as durable success.
  resetStorage();
  resetRuntime();
  WRITE_FAIL_SETUP
  fsMarkerWriteResult=false;
  latchPollPulseFault(6);
  assert(journalRecoveryRequired && !insertMode);
  WRITE_FAIL_CLEAR
  NO_MARKER_RESET
  resetRuntime();
  loadPollPulseFaultLatch();
  assert(!journalRecoveryRequired);
  std::cout << "DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY\n";
  std::cout << "POLL_FAULT_DUAL_STORE_LAB=PASS board=BOARD_NAME\n";
}
"""
    main = main.replace("READ_FAIL_SETUP", fail_read).replace("READ_FAIL_CLEAR", clear_fail)
    main = main.replace("WRITE_FAIL_SETUP", fail_write).replace("WRITE_FAIL_CLEAR", clear_fail)
    main = main.replace("NO_MARKER_RESET", no_marker)
    main = main.replace("BOARD_NAME", board)
    return "\n".join([
        prelude,
        record,
        consts,
        backend,
        helpers,
        main,
    ])

def run(board: str, path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness(board, source)
    with tempfile.TemporaryDirectory(prefix="phx-poll-fault-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(program, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        try:
            result = subprocess.run([str(exe)], check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            print(exc.stdout or "", end="")
            print(exc.stderr or "", file=sys.stderr, end="")
            raise
        print(result.stdout, end="")

if __name__ == "__main__":
    run("ESP32", ESP32)
    run("ESP8266", ESP8266)
