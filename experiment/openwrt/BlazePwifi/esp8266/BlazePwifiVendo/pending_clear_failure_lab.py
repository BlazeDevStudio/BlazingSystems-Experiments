"""Source-exact host regression for pending-journal reclamation failures.

This isolates clearPending() from GPIO/network behavior. The fake filesystem
injects delete failures and false-success readback; it does not emulate LittleFS
wear, power loss, or record serialization. Physical durability remains untested.
"""

CLEAR_PENDING_STUBS = r"""
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

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

bool readPendingFile(const char *path, PendingRecord &record) {
  if(!LittleFS.exists(path)) return false;
  record = expectedRecord;
  return true;
}

bool samePendingRecord(const PendingRecord &left,const PendingRecord &right) {
  return left.magic == right.magic &&
         left.pulses == right.pulses &&
         std::strcmp(left.nonce,right.nonce) == 0 &&
         std::strcmp(left.target,right.target) == 0 &&
         left.checksum == right.checksum;
}

bool pendingAttemptMarkerMatches() {
  PendingRecord attempt{};
  return readPendingFile("/pending.attempt",attempt) &&
         attempt.pulses == pendingPulses &&
         std::strcmp(attempt.nonce,pendingNonce.c_str()) == 0 &&
         std::strcmp(attempt.target,pendingTarget.c_str()) == 0;
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
}

bool pendingRamIdentityPreserved() {
  return pendingPulses == 4U && pendingReady && pendingPostAttempted &&
         pendingNonce == "nonce-existing" &&
         pendingTarget == "target-01" && lastSend == 123U;
}
"""

CLEAR_PENDING_MAIN = r"""
int main() {
  resetState();
  LittleFS.failRemovePath = "/pending.dat";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     !LittleFS.exists("/pending.dat") ||
     !LittleFS.exists("/pending.attempt")) return 90;
  std::cout << "PENDING_CLEAR_JOURNAL_REMOVE_FAILURE_PRESERVED_PASS\\n";

  resetState();
  LittleFS.failRemovePath = "/pending.attempt";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     LittleFS.exists("/pending.dat") ||
     !LittleFS.exists("/pending.attempt")) return 91;
  std::cout << "PENDING_CLEAR_ATTEMPT_MARKER_REMOVE_FAILURE_PRESERVED_PASS\\n";

  resetState();
  LittleFS.retainRemovePath = "/pending.dat";
  if(clearPending() || !journalRecoveryRequired ||
     !pendingRamIdentityPreserved() ||
     !LittleFS.exists("/pending.dat") ||
     !LittleFS.exists("/pending.attempt")) return 92;
  std::cout << "PENDING_CLEAR_REMOVE_READBACK_FAILURE_PRESERVED_PASS\\n";

  resetState();
  if(!clearPending() || journalRecoveryRequired ||
     pendingPulses != 0U || pendingReady || pendingPostAttempted ||
     !pendingNonce.empty() || !pendingTarget.empty() || lastSend != 0U ||
     LittleFS.exists("/pending.dat") || LittleFS.exists("/pending.attempt")) return 93;
  std::cout << "PENDING_CLEAR_SUCCESS_CONTROL_PASS\\n";
  std::cout << "PENDING_CLEAR_REMOVE_FAILURE_INJECTION_PASS 3/3 plus success control\\n";
  return 0;
}
"""


def run_pending_clear_failure_lab(board, clear_pending_source, compile_and_run):
    """Compile the exact board helper and reject a fail-open deletion mutation."""
    if not clear_pending_source:
        raise AssertionError(f"{board}: clearPending source extraction is empty")

    baseline = compile_and_run(
        CLEAR_PENDING_STUBS + clear_pending_source + CLEAR_PENDING_MAIN,
        board,
        0,
        "pending-clear-removal-failure-injection",
    )
    if "PENDING_CLEAR_REMOVE_FAILURE_INJECTION_PASS 3/3 plus success control" not in baseline:
        raise AssertionError(f"{board}: pending-clear baseline marker missing")

    anchor = 'if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){'
    mutation = clear_pending_source.replace(
        anchor,
        'LittleFS.remove("/pending.attempt"); if(false){',
        1,
    )
    if mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker deletion mutation anchor missing")

    compile_and_run(
        CLEAR_PENDING_STUBS + mutation + CLEAR_PENDING_MAIN,
        board,
        91,
        "pending-clear-ignores-attempt-marker-removal-failure",
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-attempt-marker-removal-failure "
        "expected_exit=91"
    )
