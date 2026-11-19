#!/usr/bin/env python3
"""Exact-source dual-store poll-fault persistence regression for ESP32 and ESP8266.

This host lab models the NVS and EEPROM APIs. It does not emulate flash physics,
power-loss timing, wear, or an independent physical witness.
"""
from pathlib import Path
import subprocess
import tempfile
import sys

from firmware_lab_source import extract_block, extract_function, extract_functions, mask_non_code

ROOT = Path.cwd()
ESP32 = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
ESP8266 = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

def constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith("static const ") and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

def test_extractors():
    sample = r'''
/*
bool selected(int value) { return false; }
struct Record { int fake; };
*/
const char *rawMarker = R"fake(
bool selected(int value) { return false; }
struct Record { int fake; };
)fake";
// bool selected(int value) { this is only a line comment }
bool selected(int value);
void caller() { selected(1); }
struct Record {
  const char *text = "}";
  char brace = '{';
  // } { inside a line comment
  /* { } inside a block comment */
  const char *raw = R"tag({ raw } )tag";
  int nested[2] = {1, 2};
};
bool selected(int value) {
  const char *text = "}";
  if (value) { return true; }
  return false;
}
'''
    masked = mask_non_code(sample)
    if len(masked) != len(sample) or masked.count("\n") != sample.count("\n"):
        raise AssertionError("source mask must preserve offsets and line positions")
    if "bool selected(int value) { return false; }" in masked:
        raise AssertionError("comment/raw-string decoy was not masked")

    record = extract_block(sample, "struct Record")
    function = extract_function(sample, "selected")
    functions = extract_functions(sample, "selected")
    if "int nested[2] = {1, 2};" not in record:
        raise AssertionError("struct extractor stopped inside a literal/comment")
    if not function.startswith("bool selected") or "if (value) { return true; }" not in function:
        raise AssertionError("function extractor did not select the definition")
    if len(functions) != 1 or functions[0][1] != function:
        raise AssertionError("function list must contain the single real definition")

    # C++ translation phase 2 removes backslash-newline before // comment
    # recognition. A continued comment must not expose a fake function body.
    continued_comment = (
        "// continued comment " + "\\" + "\n"
        + "bool selected(int value) { return false; }\n"
    )
    continued_masked = mask_non_code(continued_comment)
    if len(continued_masked) != len(continued_comment):
        raise AssertionError("continued-comment mask must preserve source offsets")
    if extract_functions(continued_comment, "selected"):
        raise AssertionError("backslash-newline // comment exposed a fake function")

    continued_crlf = (
        "// continued CRLF comment " + "\\" + "\r\n"
        + "bool selected(int value) { return false; }\r\n"
    )
    continued_crlf_masked = mask_non_code(continued_crlf)
    if continued_crlf_masked.count("\r\n") != continued_crlf.count("\r\n"):
        raise AssertionError("continued CRLF comment must preserve newline positions")
    if extract_functions(continued_crlf, "selected"):
        raise AssertionError("backslash-CRLF // comment exposed a fake function")

    # C++ translation phase 2 runs before comment-token recognition. A splice
    # can form the delimiter itself, not only continue an already-open comment.
    spliced_line_comment = (
        "/" + "\\" + "\n" + "/" + "\\" + "\r\n"
        + "bool selected(int value) { return false; }\r\n"
    )
    line_masked = mask_non_code(spliced_line_comment)
    if len(line_masked) != len(spliced_line_comment):
        raise AssertionError("spliced // opener must preserve source offsets")
    if line_masked.count("\r\n") != spliced_line_comment.count("\r\n"):
        raise AssertionError("spliced // opener must preserve CRLF positions")
    if extract_functions(spliced_line_comment, "selected"):
        raise AssertionError("line-spliced // opener exposed a fake function")

    spliced_block_comment = (
        "/" + "\\" + "\n" + "*\n"
        + "bool selected(int value) { return false; }\n*/\n"
    )
    block_masked = mask_non_code(spliced_block_comment)
    if len(block_masked) != len(spliced_block_comment):
        raise AssertionError("spliced /* opener must preserve source offsets")
    if extract_functions(spliced_block_comment, "selected"):
        raise AssertionError("line-spliced /* opener exposed a fake function")

    spliced_block_terminator = (
        "/* hidden " + "*" + "\\" + "\r\n" + "/\r\n"
        + "bool selected(int value) { return true; }\r\n"
    )
    terminator_masked = mask_non_code(spliced_block_terminator)
    if len(terminator_masked) != len(spliced_block_terminator):
        raise AssertionError("spliced */ terminator must preserve source offsets")
    if terminator_masked.count("\r\n") != spliced_block_terminator.count("\r\n"):
        raise AssertionError("spliced */ terminator must preserve CRLF positions")
    terminated_functions = extract_functions(spliced_block_terminator, "selected")
    if len(terminated_functions) != 1 or "return true;" not in terminated_functions[0][1]:
        raise AssertionError("line-spliced */ terminator did not expose following code")

    if not function.endswith("}"):
        raise AssertionError("function extractor returned an incomplete body")

    attributed = "void ICACHE_RAM_ATTR edgeHandler() { if (true) { ++count; } }"
    if "edgeHandler" not in extract_function(attributed, "edgeHandler"):
        raise AssertionError("attribute-qualified function definition was not found")

    if extract_function("bool declared(int value);", "declared", required=False):
        raise AssertionError("declaration must not be returned as a definition")

    try:
        extract_block('struct Broken { const char *value = "}" ;', "struct Broken")
    except RuntimeError:
        pass
    else:
        raise AssertionError("unterminated block must fail closed")

    print("POLL_FAULT_EXTRACTOR_SELFTEST=PASS")


def harness(board: str, source: str) -> str:
    record = extract_block(source, "struct PollFaultRecord") + ";"
    helper_names = [
        "pollFaultRecordChecksum",
        "makePollFaultRecord",
        "validPollFaultRecord",
        "pollFaultBackupPresentOrCorrupt",
        "writePollFaultBackup",
        "loadPollPulseFaultLatch",
        "latchPollPulseFault",
    ]
    if board == "ESP32":
        helper_names.append("initPollFaultBackupStore")
    else:
        helper_names.insert(3,"readPollFaultBackupFlash")
        helper_names.insert(3,"readFullEepromImage")
        helper_names.insert(4,"restoreEepromRamImage")
        helper_names.insert(5,"refreshVerifiedEepromImage")
    helpers = "\n".join(extract_function(source, name) for name in helper_names)
    consts = constants(source, (
        "POLL_FAULT_RECORD_MAGIC",
        "POLL_FAULT_RECORD_VERSION",
        "POLL_FAULT_EEPROM_OFFSET",
        "POLL_FAULT_EEPROM_BYTES",
    ))
    if board == "ESP32":
        backend = r"""
using nvs_handle_t = uint32_t;
using esp_err_t = int;
static constexpr esp_err_t ESP_OK=0;
static constexpr esp_err_t ESP_ERR_NVS_NOT_FOUND=1;
static constexpr esp_err_t ESP_ERR_NVS_TYPE_MISMATCH=2;
static constexpr esp_err_t ESP_ERR_NVS_INVALID_LENGTH=3;
static constexpr esp_err_t ESP_FAIL=4;
static constexpr int NVS_READWRITE=1;
struct NvsFlash {
  static std::vector<uint8_t> durable;
  static std::vector<uint8_t> pending;
};
std::vector<uint8_t> NvsFlash::durable;
std::vector<uint8_t> NvsFlash::pending;
static bool nvsReadError=false, nvsFailSet=false, nvsFailCommit=false;
static bool nvsFailCommitAfterWrite=false;
static bool nvsFailOpen=false, nvsTypeMismatch=false, nvsFailReadback=false;
nvs_handle_t pollFaultNvsHandle=0;
bool pollFaultBackupReady=false;
bool pollFaultBackupWriteFailed=false;
static unsigned nvsCommitCalls=0;
static bool nvsSetWasDurableBeforeCommit=false;
unsigned backupCommitCalls(){ return nvsCommitCalls; }
void initPollFaultBackupStore();
esp_err_t nvs_open(const char*,int,nvs_handle_t* handle){
  if(nvsFailOpen) return ESP_FAIL;
  *handle=1;
  return ESP_OK;
}
esp_err_t nvs_get_blob(nvs_handle_t handle,const char*,void* value,size_t* length){
  if(handle==0 || !length || nvsReadError) return ESP_FAIL;
  if(nvsTypeMismatch) return ESP_ERR_NVS_TYPE_MISMATCH;
  const std::vector<uint8_t>& visible=NvsFlash::pending.empty()?NvsFlash::durable:NvsFlash::pending;
  if(visible.empty()) return ESP_ERR_NVS_NOT_FOUND;
  if(!value){ *length=visible.size(); return ESP_OK; }
  if(*length<visible.size()){
    *length=visible.size();
    return ESP_ERR_NVS_INVALID_LENGTH;
  }
  memcpy(value,visible.data(),visible.size());
  *length=visible.size();
  return ESP_OK;
}
esp_err_t nvs_set_blob(nvs_handle_t handle,const char*,const void* value,size_t length){
  if(handle==0 || nvsFailSet) return ESP_FAIL;
  const uint8_t* bytes=(const uint8_t*)value;
  NvsFlash::pending.assign(bytes,bytes+length);
  return ESP_OK;
}
esp_err_t nvs_commit(nvs_handle_t handle){
  ++nvsCommitCalls;
  nvsSetWasDurableBeforeCommit=!NvsFlash::durable.empty();
  // ESP-IDF documents nvs_set_blob as pending until nvs_commit. Model both
  // ambiguous failure outcomes: no durable write, or bytes reaching flash
  // even though the commit call reports failure.
  if(handle==0 || nvsFailCommit) return ESP_FAIL;
  if(!NvsFlash::pending.empty()){
    NvsFlash::durable=NvsFlash::pending;
    NvsFlash::pending.clear();
  }
  if(nvsFailCommitAfterWrite) return ESP_FAIL;
  if(nvsFailReadback) nvsReadError=true;
  return ESP_OK;
}
void resetStorage(){
  NvsFlash::durable.clear();
  NvsFlash::pending.clear();
  nvsReadError=false; nvsFailSet=false; nvsFailCommit=false;
  nvsFailCommitAfterWrite=false; nvsCommitCalls=0; pollFaultBackupWriteFailed=false;
  nvsFailOpen=false; nvsTypeMismatch=false; nvsFailReadback=false;
  nvsSetWasDurableBeforeCommit=false;
  pollFaultNvsHandle=0; pollFaultBackupReady=false;
  initPollFaultBackupStore();
}
void rebootStorage(){
  pollFaultBackupWriteFailed=false;
  // Pending handle-local data is volatile and must not survive a simulated reboot.
  NvsFlash::pending.clear();
  nvsReadError=false; nvsFailReadback=false;
  pollFaultNvsHandle=0; pollFaultBackupReady=false;
  initPollFaultBackupStore();
}
void corruptStorage(){
  if(!NvsFlash::durable.empty()) NvsFlash::durable[0]^=0x01;
}
"""
        fail_write = "nvsFailSet=true;"
        fail_read = "nvsFailReadback=true;"
        ambiguous_commit_setup = "nvsFailCommitAfterWrite=true;"
        clear_fail = "nvsReadError=false; nvsFailSet=false; nvsFailCommit=false; nvsFailCommitAfterWrite=false; nvsFailOpen=false; nvsTypeMismatch=false; nvsFailReadback=false;"
        no_marker = "NvsFlash::durable.clear(); NvsFlash::pending.clear();"
        nvs_read_error = r"""
  resetRuntime();
  nvsReadError=true;
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 21;
  nvsReadError=false;
  std::cout << "ESP32_NVS_READ_ERROR_DENY_PASS\\n";

  resetRuntime();
  nvsTypeMismatch=true;
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 22;
  nvsTypeMismatch=false;
  std::cout << "ESP32_NVS_TYPE_MISMATCH_DENY_PASS\\n";

  // Failure to open the secondary store must also latch deny before intake.
  resetRuntime();
  nvsFailOpen=true;
  initPollFaultBackupStore();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 23;
  nvsFailOpen=false;
  std::cout << "ESP32_NVS_OPEN_FAILURE_DENY_PASS\\n";
"""
    else:
        backend = r"""
static const uint32_t EEPROM_start=0x40200000UL;
static bool rawFlashReadFailure=false;
static uint32_t lastRawFlashReadAddress=UINT32_MAX;
bool fakeFlashRead(uint32_t address,uint8_t* data,size_t length);
struct FakeEEPROM {
  static std::vector<uint8_t> flash;
  std::vector<uint8_t> buffer;
  size_t size=0;
  bool ready=true, failCommit=false, failCommitAfterWrite=false, failRead=false, failReadAfterCommit=false;
  unsigned commitCalls=0;
  bool begin(size_t n) {
    if(!ready) return false;
    size=n;
    if(flash.size()<n) flash.resize(n,0xFF);
    // ESP8266 core 3.1.2 ignores flashRead's return value in EEPROM.begin().
    // Fill with erased-looking bytes on failure to model a possible false-clean RAM image.
    buffer.assign(n,0xFF);
    (void)fakeFlashRead((uint32_t)(EEPROM_start-0x40200000UL),buffer.data(),n);
    return true;
  }
  bool end(){ size=0; buffer.clear(); return true; }
  bool commit(){
    ++commitCalls;
    if(failCommit) return false;
    if(!outputsInhibited) persistenceBeforeOutputInhibit=true;
    flash=buffer;
    // Model a write that reached flash even though the API reports a failed commit.
    if(failCommitAfterWrite) return false;
    if(failReadAfterCommit){ failRead=true; rawFlashReadFailure=true; }
    return true;
  }
  size_t length() const { return size; }
  uint8_t* getDataPtr(){ return buffer.empty()?nullptr:buffer.data(); }
  const uint8_t* getConstDataPtr() const { return buffer.empty()?nullptr:buffer.data(); }
  template<class T> void put(size_t offset,const T& value) {
    memcpy(buffer.data()+offset,&value,sizeof(T));
  }
  template<class T> void get(size_t offset,T& value) {
    if(failRead){ memset(&value,0,sizeof(T)); return; }
    memcpy(&value,buffer.data()+offset,sizeof(T));
  }
};
std::vector<uint8_t> FakeEEPROM::flash;
bool fakeFlashRead(uint32_t address,uint8_t* data,size_t length){
  lastRawFlashReadAddress=address;
  const uint32_t base=(uint32_t)(EEPROM_start-0x40200000UL);
  if(rawFlashReadFailure || address<base) return false;
  const size_t offset=(size_t)(address-base);
  if(offset+length>FakeEEPROM::flash.size()) return false;
  memcpy(data,FakeEEPROM::flash.data()+offset,length);
  return true;
}
struct EspFlashStub {
  bool flashRead(uint32_t address,uint8_t* data,size_t length){
    return fakeFlashRead(address,data,length);
  }
} ESP;
FakeEEPROM EEPROM;
bool pollFaultBackupReady=true;
bool configImageReadVerified=true; // This lab starts after loadCfg() has verified the full image.
bool pollFaultBackupWriteFailed=false;
unsigned backupCommitCalls(){ return EEPROM.commitCalls; }
void resetStorage(){
  FakeEEPROM::flash.clear(); EEPROM=FakeEEPROM();
  rawFlashReadFailure=false; lastRawFlashReadAddress=UINT32_MAX;
  pollFaultBackupWriteFailed=false;
  pollFaultBackupReady=EEPROM.begin(POLL_FAULT_EEPROM_BYTES);
  configImageReadVerified=true;
}
void rebootStorage(){
  EEPROM.end();
  pollFaultBackupWriteFailed=false;
  pollFaultBackupReady=EEPROM.begin(POLL_FAULT_EEPROM_BYTES);
  configImageReadVerified=true;
}
void corruptStorage(){
  if(FakeEEPROM::flash.size()>POLL_FAULT_EEPROM_OFFSET)
    FakeEEPROM::flash[POLL_FAULT_EEPROM_OFFSET]^=0x01;
}
"""
        fail_write = "EEPROM.failCommit=true;"
        fail_read = "EEPROM.failReadAfterCommit=true;"
        ambiguous_commit_setup = "EEPROM.failCommitAfterWrite=true;"
        clear_fail = "EEPROM.failCommit=false; EEPROM.failCommitAfterWrite=false; EEPROM.failRead=false; EEPROM.failReadAfterCommit=false; rawFlashReadFailure=false;"
        no_marker = "FakeEEPROM::flash.clear(); rebootStorage();"
        nvs_read_error = ""

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
  NVS_WRITE_BEFORE_COMMIT_ASSERT
  assert(journalRecoveryRequired && !insertMode);
  assert(outputsInhibited);
  assert(!persistenceBeforeOutputInhibit);
  assert(pollFaultBackupPresentOrCorrupt());
  rebootStorage();
  assertBootDenied();

  // An NVS lookup error must not make an existing sticky marker appear absent.
  NVS_READ_ERROR_SCENARIO

  RAW_FLASH_READ_ERROR_SCENARIO

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

  // A commit can report failure after bytes reached flash. Reboot must still
  // discover the sticky marker rather than treating the failed return as absence.
  resetStorage();
  resetRuntime();
  LittleFS.marker=false;
  AMBIGUOUS_COMMIT_SETUP
  fsMarkerWriteResult=false;
  latchPollPulseFault(7);
  assert(journalRecoveryRequired && !insertMode && outputsInhibited);
  assert(!LittleFS.marker);
  AMBIGUOUS_COMMIT_CLEAR
  rebootStorage();
  assertBootDenied();
  std::cout << "AMBIGUOUS_COMMIT_REBOOT_DENY_PASS board=BOARD_NAME\\n";

  // A failed commit is ambiguous for this boot. Never let a dirty EEPROM/NVS
  // cache make a later call report a durable marker without a fresh boot read.
  resetStorage();
  resetRuntime();
  WRITE_FAIL_SETUP
  assert(!writePollFaultBackup(8));
  if(!pollFaultBackupWriteFailed) return 24;
  const unsigned commitsBeforeRetry=backupCommitCalls();
  WRITE_FAIL_CLEAR
  if(writePollFaultBackup(8)) return 25;
  if(backupCommitCalls()!=commitsBeforeRetry) return 26;
  rebootStorage();
  if(pollFaultBackupPresentOrCorrupt()) return 27;
  std::cout << "FAILED_COMMIT_RETRY_HELD_UNTIL_REBOOT_PASS board=BOARD_NAME\\n";

  // An ambiguous commit may have reached flash despite returning failure.
  // Do not retry from the same boot; after reboot, inspect the actual durable bytes.
  resetStorage();
  resetRuntime();
  AMBIGUOUS_COMMIT_SETUP
  if(writePollFaultBackup(9)) return 28;
  if(!pollFaultBackupWriteFailed) return 29;
  const unsigned ambiguousCommitCalls=backupCommitCalls();
  AMBIGUOUS_COMMIT_CLEAR
  if(writePollFaultBackup(9)) return 30;
  if(backupCommitCalls()!=ambiguousCommitCalls) return 31;
  rebootStorage();
  if(!pollFaultBackupPresentOrCorrupt()) return 32;
  std::cout << "AMBIGUOUS_COMMIT_RETRY_DENY_REBOOT_MARKER_PASS board=BOARD_NAME\\n";

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
  // A successful nvs_set_blob/EEPROM.put is not a durability receipt:
  // the documented NVS contract requires a successful nvs_commit, and a failed
  // commit may leave no durable marker after reboot when LittleFS also fails.
  resetStorage();
  resetRuntime();
  LittleFS.marker=false;
  fsMarkerWriteResult=false;
  COMMIT_FAIL_BEFORE_PERSISTENCE_SETUP
  latchPollPulseFault(12);
  if(!journalRecoveryRequired || insertMode || !outputsInhibited ||
     !pollFaultBackupWriteFailed) return 41;
  COMMIT_FAIL_BEFORE_PERSISTENCE_CLEAR
  rebootStorage();
  resetRuntime();
  loadPollPulseFaultLatch();
  if(journalRecoveryRequired){
    std::cerr<<"COMMIT_FAILURE_BEFORE_PERSISTENCE_WAS_MISTAKEN_FOR_DURABILITY board=BOARD_NAME"<<std::endl;
    return 42;
  }
  std::cout<<"COMMIT_FAILURE_BEFORE_PERSISTENCE_REBOOT_LIMITATION=REPRODUCED board=BOARD_NAME"<<std::endl;

  std::cout << "POLL_FAULT_DUAL_STORE_LAB=PASS board=BOARD_NAME\n";
}
"""
    if board == "ESP32":
        nvs_write_before_commit_assert = "if(nvsSetWasDurableBeforeCommit){ std::cerr<<\"ESP32_NVS_SET_BLOB_DURABLE_BEFORE_COMMIT\\n\"; return 60; } std::cout<<\"ESP32_NVS_SET_BLOB_NOT_DURABLE_BEFORE_COMMIT_PASS\\n\";"
        commit_fail_before_persistence_setup = "nvsFailCommit=true;"
        commit_fail_before_persistence_clear = "nvsFailCommit=false;"
    else:
        nvs_write_before_commit_assert = ""
        commit_fail_before_persistence_setup = "EEPROM.failCommit=true;"
        commit_fail_before_persistence_clear = "EEPROM.failCommit=false;"
    main = main.replace("NVS_WRITE_BEFORE_COMMIT_ASSERT", nvs_write_before_commit_assert)
    main = main.replace("COMMIT_FAIL_BEFORE_PERSISTENCE_SETUP", commit_fail_before_persistence_setup)
    main = main.replace("COMMIT_FAIL_BEFORE_PERSISTENCE_CLEAR", commit_fail_before_persistence_clear)
    main = main.replace("NVS_READ_ERROR_SCENARIO", nvs_read_error)
    raw_flash_read_error = r"""
  // EEPROM.begin() ignores a failed flashRead. Its RAM image may look erased;
  // the fault check must use a status-bearing direct read of the reserved flash bytes.
  rawFlashReadFailure=true;
  rebootStorage();
  lastRawFlashReadAddress=UINT32_MAX;
  resetRuntime();
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 33;
  if(lastRawFlashReadAddress != (uint32_t)(EEPROM_start-0x40200000UL)+POLL_FAULT_EEPROM_OFFSET) return 34;
  // A failed raw read is NOT evidence that a deny marker already exists.
  // The writer must refuse to claim secondary-store persistence or skip the write.
  resetStorage();
  resetRuntime();
  rawFlashReadFailure=true;
  const unsigned commitsBeforeUnavailableRead=backupCommitCalls();
  if(writePollFaultBackup(11)) return 35;
  if(!pollFaultBackupWriteFailed) return 36;
  if(backupCommitCalls()!=commitsBeforeUnavailableRead) return 37;
  rawFlashReadFailure=false;
  std::cout << "ESP8266_RAW_FLASH_READ_ERROR_WRITE_DENY_PASS\\n";
  std::cout << "ESP8266_RAW_FLASH_READ_ERROR_DENY_PASS\\n";
"""
    main = main.replace("RAW_FLASH_READ_ERROR_SCENARIO", raw_flash_read_error if board == "ESP8266" else "")
    main = main.replace("READ_FAIL_SETUP", fail_read).replace("READ_FAIL_CLEAR", clear_fail)
    main = main.replace("WRITE_FAIL_SETUP", fail_write).replace("WRITE_FAIL_CLEAR", clear_fail)
    main = main.replace("AMBIGUOUS_COMMIT_SETUP", ambiguous_commit_setup).replace("AMBIGUOUS_COMMIT_CLEAR", clear_fail)
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

def run_esp32_precommit_persistence_mutation(path: Path):
    source = path.read_text(encoding="utf-8")
    program = harness("ESP32", source)
    needle = "NvsFlash::pending.assign(bytes,bytes+length);\n  return ESP_OK;"
    replacement = (
        "NvsFlash::pending.assign(bytes,bytes+length);\n"
        "  NvsFlash::durable.assign(bytes,bytes+length);\\n"
        "  return ESP_OK;"
    )
    if program.count(needle) != 1:
        raise AssertionError("ESP32 NVS pre-commit mutation anchor must occur exactly once")
    mutated = program.replace(needle, replacement, 1)
    with tempfile.TemporaryDirectory(prefix="phx-nvs-precommit-mutation-") as tmp:
        cpp = Path(tmp) / "lab.cpp"
        exe = Path(tmp) / "lab"
        cpp.write_text(mutated, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", str(cpp), "-o", str(exe)],
            check=True,
        )
        result = subprocess.run([str(exe)], text=True, capture_output=True)
    if result.returncode != 60 or "ESP32_NVS_SET_BLOB_DURABLE_BEFORE_COMMIT" not in result.stderr:
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        raise AssertionError("premature ESP32 NVS durability mutation was not rejected")
    print("MUTATION_REJECTED ESP32_NVS_SET_BLOB_PREMATURE_DURABILITY exit=60")


if __name__ == "__main__":
    test_extractors()
    print("POLL_FAULT_EXTRACTOR_SELFTEST=PASS", flush=True)
    run("ESP32", ESP32)
    run_esp32_precommit_persistence_mutation(ESP32)
    run("ESP8266", ESP8266)
