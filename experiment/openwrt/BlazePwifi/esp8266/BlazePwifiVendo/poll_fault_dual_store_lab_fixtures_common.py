"""Shared C++ fixture text for the dual-store poll-fault lab.

Keep common scenarios separate from board-specific persistence backends.
The strings are compiled against source-extracted firmware helpers.
"""

def constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith("static const ") and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

PRELUDE = r"""
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
  if(!fsReady) return false;
  if(fsMarkerWriteResult) LittleFS.marker=true;
  return fsMarkerWriteResult;
}
"""

MAIN = r"""
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

  // Boot-time GPIO quarantine runs before LittleFS mount. The secondary
  // EEPROM/NVS marker must still survive and deny after the filesystem comes up.
  resetStorage();
  resetRuntime();
  fsReady=false;
  LittleFS.marker=false;
  latchPollPulseFault(8);
  assert(journalRecoveryRequired && !insertMode && outputsInhibited);
  assert(pollFaultBackupPresentOrCorrupt());
  assert(!LittleFS.marker);
  fsReady=true;
  rebootStorage();
  assertBootDenied();
  std::cout << "PRE_LITTLEFS_SECONDARY_BACKUP_REBOOT_DENY_PASS board=BOARD_NAME" << std::endl;

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

RAW_FLASH_READ_ERROR = r"""
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
