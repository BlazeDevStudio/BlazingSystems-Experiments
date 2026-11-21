"""C++ fixtures for exact-source dual-store poll-fault persistence tests.

The runner owns repository discovery, self-tests and mutation execution.
This module owns the extracted C++ model and board-specific fault scenarios.
Keep fixture bodies here so persistence behavior can be reviewed separately
from Python orchestration.
"""
from firmware_lab_source import extract_block, extract_function

__all__ = ["constants", "harness"]

def constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith("static const ") and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

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
  if(backupCommitCalls()!=1){
    std::cerr<<"POLL_FAULT_BACKUP_COMMIT_CALL_COUNT_FAIL board=BOARD_NAME actual="<<backupCommitCalls()<<std::endl;
    return 61;
  }
  std::cout<<"POLL_FAULT_BACKUP_COMMIT_CALL_COUNT_PASS board=BOARD_NAME calls=1"<<std::endl;
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
