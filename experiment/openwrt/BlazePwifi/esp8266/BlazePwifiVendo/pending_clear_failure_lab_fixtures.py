"""C++ fixtures for source-exact pending-journal and quarantine failure tests.

Keep fake storage adapters and scenario programs separate from orchestration so
failure behavior can be reviewed without scrolling through every test case.
These fixtures model host behavior only; they do not prove flash durability.
"""

CLEAR_PENDING_STUBS = r"""
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

using String = std::string;

struct PendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};

struct FakeLittleFS {
  std::map<std::string,std::string> files;
  std::string failRemovePath;
  std::string retainRemovePath;

  bool exists(const char *path) const {
    return files.find(path) != files.end();
  }

  bool remove(const char *path) {
    const std::string candidate(path);
    if(candidate == failRemovePath) return false;
    if(candidate == retainRemovePath) return true;
    return files.erase(candidate) == 1U;
  }
} LittleFS;

struct SerialStub {
  void println(const char *message) { (void)message; }
  void println(const String &message) { (void)message; }
} Serial;

bool fsReady = true;
bool journalRecoveryRequired = false;
uint8_t pendingPulses = 4U;
bool pendingReady = true;
bool pendingPostAttempted = true;
std::string pendingNonce = "nonce-existing";
std::string pendingTarget = "target-01";
uint32_t lastSend = 123U;
PendingRecord expectedRecord{};

std::string failReadPath;
bool mismatchAttemptRecord = false;
bool mismatchDurableRecord = false;
bool changePersistedIdentityAfterFirstAttemptRead = false;
unsigned attemptReadCount = 0U;

bool readPendingFile(const char *path, PendingRecord &record) {
  const std::string candidate(path);
  if(!LittleFS.exists(path) || candidate == failReadPath) return false;

  record = expectedRecord;
  if(candidate == "/pending.attempt") {
    ++attemptReadCount;
    if(mismatchAttemptRecord ||
       (changePersistedIdentityAfterFirstAttemptRead && attemptReadCount >= 2U)) {
      ++record.pulses;
    }
  } else if(candidate == "/pending.dat" &&
            (mismatchDurableRecord ||
             (changePersistedIdentityAfterFirstAttemptRead && attemptReadCount >= 2U))) {
    ++record.pulses;
  }
  return true;
}

void resetState() {
  LittleFS.files.clear();
  LittleFS.failRemovePath.clear();
  LittleFS.retainRemovePath.clear();
  LittleFS.files["/pending.dat"] = "opaque-pending-record";
  LittleFS.files["/pending.attempt"] = "opaque-attempt-marker";
  fsReady = true;
  journalRecoveryRequired = false;
  pendingPulses = 4U;
  pendingReady = true;
  pendingPostAttempted = true;
  pendingNonce = "nonce-existing";
  pendingTarget = "target-01";
  lastSend = 123U;
  expectedRecord = PendingRecord{};
  expectedRecord.magic = 0x42505733U;
  expectedRecord.pulses = pendingPulses;
  std::strcpy(expectedRecord.nonce,pendingNonce.c_str());
  std::strcpy(expectedRecord.target,pendingTarget.c_str());
  expectedRecord.checksum = 0x12345678U;
  failReadPath.clear();
  mismatchAttemptRecord = false;
  mismatchDurableRecord = false;
  changePersistedIdentityAfterFirstAttemptRead = false;
  attemptReadCount = 0U;
}

bool pendingRamIdentityPreserved() {
  return pendingPulses == 4U && pendingReady && pendingPostAttempted &&
         pendingNonce == "nonce-existing" &&
         pendingTarget == "target-01" && lastSend == 123U;
}

bool attemptMarkerBytesPreserved() {
  const auto marker = LittleFS.files.find("/pending.attempt");
  return marker != LittleFS.files.end() &&
         marker->second == "opaque-attempt-marker";
}

bool pendingAndAttemptBytesPreserved() {
  const auto pending = LittleFS.files.find("/pending.dat");
  return pending != LittleFS.files.end() &&
         pending->second == "opaque-pending-record" &&
         attemptMarkerBytesPreserved();
}
"""
CLEAR_PENDING_MAIN = r"""
int main() {
  resetState();
  LittleFS.failRemovePath = "/pending.dat";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     !pendingAndAttemptBytesPreserved()) return 90;
  std::cout << "PENDING_CLEAR_JOURNAL_REMOVE_FAILURE_PRESERVED_PASS\n";

  resetState();
  LittleFS.failRemovePath = "/pending.attempt";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     LittleFS.exists("/pending.dat") ||
     !attemptMarkerBytesPreserved()) return 91;
  std::cout << "PENDING_CLEAR_ATTEMPT_MARKER_REMOVE_FAILURE_PRESERVED_PASS\n";

  resetState();
  LittleFS.retainRemovePath = "/pending.attempt";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     LittleFS.exists("/pending.dat") ||
     !attemptMarkerBytesPreserved()) return 103;
  std::cout << "PENDING_CLEAR_ATTEMPT_MARKER_REMOVE_READBACK_FAILURE_PRESERVED_PASS\n";

  resetState();
  LittleFS.retainRemovePath = "/pending.dat";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     !pendingAndAttemptBytesPreserved()) return 92;
  std::cout << "PENDING_CLEAR_REMOVE_READBACK_FAILURE_PRESERVED_PASS\n";

  resetState();
  if(!clearPending() || journalRecoveryRequired ||
     pendingPulses != 0U || pendingReady || pendingPostAttempted ||
     !pendingNonce.empty() || !pendingTarget.empty() || lastSend != 0U ||
     LittleFS.exists("/pending.dat") || LittleFS.exists("/pending.attempt")) return 93;
  std::cout << "PENDING_CLEAR_SUCCESS_CONTROL_PASS\n";
  std::cout << "PENDING_CLEAR_REMOVE_FAILURE_INJECTION_PASS 4/4 plus success control\n";

  resetState();
  mismatchAttemptRecord = true;
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved()) return 94;
  std::cout << "PENDING_CLEAR_ATTEMPT_IDENTITY_MISMATCH_PRESERVED_PASS\n";

  resetState();
  failReadPath = "/pending.attempt";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved()) return 95;
  std::cout << "PENDING_CLEAR_ATTEMPT_READ_FAILURE_PRESERVED_PASS\n";

  resetState();
  changePersistedIdentityAfterFirstAttemptRead = true;
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved()) return 96;
  std::cout << "PENDING_CLEAR_ATTEMPT_RECHECK_IDENTITY_CHANGE_PRESERVED_PASS\n";

  resetState();
  mismatchDurableRecord = true;
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved()) return 97;
  std::cout << "PENDING_CLEAR_DURABLE_RECORD_MISMATCH_PRESERVED_PASS\n";

  resetState();
  failReadPath = "/pending.dat";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved()) return 98;
  std::cout << "PENDING_CLEAR_DURABLE_RECORD_READ_FAILURE_PRESERVED_PASS\n";

  resetState();
  LittleFS.files["/pending.new"] = "opaque-new-candidate";
  const auto extraCandidateBytes = std::string("opaque-new-candidate");
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || !pendingAndAttemptBytesPreserved() ||
     LittleFS.files.find("/pending.new") == LittleFS.files.end() ||
     LittleFS.files.find("/pending.new")->second != extraCandidateBytes) return 99;
  std::cout << "PENDING_CLEAR_AMBIGUOUS_CANDIDATES_PRESERVED_PASS\n";

  resetState();
  LittleFS.files.erase("/pending.dat");
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || LittleFS.exists("/pending.dat") ||
     !attemptMarkerBytesPreserved()) return 100;
  std::cout << "PENDING_CLEAR_MISSING_CANDIDATE_PRESERVED_PASS\n";
  std::cout << "PENDING_CLEAR_PRECONDITION_FAILURE_INJECTION_PASS 7/7\n";
  return 0;
}
"""
BOOT_ORPHAN_ATTEMPT_MAIN = r"""
int main() {
  resetState();
  LittleFS.failRemovePath = "/pending.attempt";
  if(clearPending() || !journalRecoveryRequired ||
     LittleFS.exists("/pending.dat") ||
     !LittleFS.exists("/pending.attempt")) return 101;

  // Simulate reboot: retain fake flash, discard every volatile pending field.
  journalRecoveryRequired = false;
  pendingPulses = 0U;
  pendingReady = false;
  pendingPostAttempted = false;
  pendingNonce.clear();
  pendingTarget.clear();
  lastSend = 0U;
  loadPending();

  if(!journalRecoveryRequired || pendingPulses != 0U ||
     pendingReady || pendingPostAttempted ||
     LittleFS.exists("/pending.dat") ||
     !LittleFS.exists("/pending.attempt")) return 102;
  std::cout << "PENDING_CLEAR_ORPHAN_ATTEMPT_BOOT_DENY_PASS\n";
  return 0;
}
"""
QUARANTINE_PENDING_STUBS = r"""
bool appendQuarantineShouldFail = true;
unsigned appendQuarantineCalls = 0U;

bool appendQuarantineRecord(const String &reason) {
  (void)reason;
  ++appendQuarantineCalls;
  return !appendQuarantineShouldFail;
}
"""
QUARANTINE_PENDING_MAIN = r"""
int main() {
  resetState();
  appendQuarantineShouldFail = true;
  appendQuarantineCalls = 0U;
  if(quarantinePending("controller rejected") || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     !pendingAndAttemptBytesPreserved() ||
     appendQuarantineCalls != 1U) return 110;
  std::cout << "QUARANTINE_APPEND_FAILURE_PRESERVES_PENDING_AND_ATTEMPT_PASS\n";

  resetState();
  appendQuarantineShouldFail = false;
  appendQuarantineCalls = 0U;
  if(!quarantinePending("controller rejected") || journalRecoveryRequired ||
     pendingPulses != 0U || pendingReady || pendingPostAttempted ||
     !pendingNonce.empty() || !pendingTarget.empty() ||
     LittleFS.exists("/pending.dat") || LittleFS.exists("/pending.attempt") ||
     appendQuarantineCalls != 1U) return 111;
  std::cout << "QUARANTINE_APPEND_SUCCESS_CLEAR_CONTROL_PASS\n";

  resetState();
  appendQuarantineShouldFail = false;
  appendQuarantineCalls = 0U;
  LittleFS.failRemovePath = "/pending.attempt";
  if(quarantinePending("controller rejected") || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() || LittleFS.exists("/pending.dat") ||
     !attemptMarkerBytesPreserved() || appendQuarantineCalls != 1U) return 114;
  std::cout << "QUARANTINE_CLEAR_FAILURE_PRESERVES_ATTEMPT_AND_RAM_PASS\n";

  resetState();
  appendQuarantineShouldFail = true;
  appendQuarantineCalls = 0U;
  pendingPulses = 0U;
  if(quarantinePending("controller rejected") || !journalRecoveryRequired ||
     !pendingAndAttemptBytesPreserved() || appendQuarantineCalls != 0U) return 112;
  std::cout << "QUARANTINE_MISSING_PENDING_DENIED_PASS\n";

  resetState();
  appendQuarantineShouldFail = true;
  appendQuarantineCalls = 0U;
  mismatchAttemptRecord = true;
  if(quarantinePending("controller rejected") || !journalRecoveryRequired ||
     !pendingAndAttemptBytesPreserved() || appendQuarantineCalls != 0U) return 113;
  std::cout << "QUARANTINE_MISMATCHED_ATTEMPT_DENIED_PASS\n";
  std::cout << "QUARANTINE_DISPOSITION_FAILURE_INJECTION_PASS 1/1 plus 2 preconditions and success control\n";
  return 0;
}
"""
