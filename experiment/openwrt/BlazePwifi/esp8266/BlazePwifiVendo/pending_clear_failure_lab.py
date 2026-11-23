"""Source-exact host regression for pending-journal reclamation failures.

This isolates clearPending() from GPIO/network behavior. The lab extracts the
production clearPending(), samePendingRecord(), and pendingAttemptMarkerMatches()
helpers unchanged. readPendingFile() and LittleFS remain explicit test adapters:
they model record-read failures and identity changes, not serialized bytes,
LittleFS wear, power loss, or physical durability.
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

def run_pending_clear_failure_lab(
    board,
    clear_pending_source,
    same_pending_record_source,
    load_pending_source,
    pending_attempt_marker_matches_source,
    compile_and_run,
):
    """Compile exact production helpers and reject fail-open reclamation mutations."""
    sources = {
        "clearPending": clear_pending_source,
        "loadPending": load_pending_source,
        "samePendingRecord": same_pending_record_source,
        "pendingAttemptMarkerMatches": pending_attempt_marker_matches_source,
    }
    for name, source in sources.items():
        if not source:
            raise AssertionError(f"{board}: missing source-exact {name} helper")

    def compile_case(label, expected=0, clear_source=None, same_record_source=None,
                     load_source=None, main_source=None):
        selected_clear = clear_source if clear_source is not None else clear_pending_source
        selected_same = (
            same_record_source
            if same_record_source is not None
            else same_pending_record_source
        )
        selected_load = load_source if load_source is not None else load_pending_source
        selected_main = main_source if main_source is not None else CLEAR_PENDING_MAIN
        program = (
            CLEAR_PENDING_STUBS
            + selected_same
            + "\n"
            + pending_attempt_marker_matches_source
            + "\n"
            + selected_load
            + "\n"
            + selected_clear
            + "\n"
            + selected_main
        )
        return compile_and_run(program, board, expected, label)

    baseline = compile_case("pending-clear-precondition-and-removal-failures")
    for marker in (
        "PENDING_CLEAR_REMOVE_FAILURE_INJECTION_PASS 4/4 plus success control",
        "PENDING_CLEAR_PRECONDITION_FAILURE_INJECTION_PASS 7/7",
    ):
        if marker not in baseline:
            raise AssertionError(f"{board}: pending-clear baseline marker missing: {marker}")
    print(f"{board} {baseline}")

    boot_baseline = compile_case(
        "pending-clear-orphan-attempt-boot-deny",
        main_source=BOOT_ORPHAN_ATTEMPT_MAIN,
    )
    if "PENDING_CLEAR_ORPHAN_ATTEMPT_BOOT_DENY_PASS" not in boot_baseline:
        raise AssertionError(f"{board}: orphan attempt marker boot-deny marker missing")
    print(f"{board} {boot_baseline}")
    print(f"{board} PENDING_CLEAR_ORPHAN_ATTEMPT_BOOT_DENY_PASS")

    orphan_attempt_anchor = 'if(hasAttempt){\n      journalRecoveryRequired=true;'
    orphan_attempt_mutation = load_pending_source.replace(
        orphan_attempt_anchor,
        'if(false && hasAttempt){\n      journalRecoveryRequired=true;',
        1,
    )
    if orphan_attempt_mutation == load_pending_source:
        raise AssertionError(f"{board}: orphan attempt boot-deny mutation anchor missing")
    compile_case(
        "pending-clear-orphan-attempt-boot-deny-mutation",
        102,
        load_source=orphan_attempt_mutation,
        main_source=BOOT_ORPHAN_ATTEMPT_MAIN,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-orphan-attempt-boot-deny "
        "expected_exit=102"
    )

    attempt_remove_anchor = (
        'if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){'
    )
    attempt_remove_mutation = clear_pending_source.replace(
        attempt_remove_anchor,
        'LittleFS.remove("/pending.attempt"); if(false){',
        1,
    )
    if attempt_remove_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker removal mutation anchor missing")
    compile_case(
        "pending-clear-ignores-attempt-marker-removal-failure",
        91,
        clear_source=attempt_remove_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-attempt-marker-removal-failure "
        "expected_exit=91"
    )

    attempt_remove_readback_anchor = (
        'if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){'
    )
    attempt_remove_readback_mutation = clear_pending_source.replace(
        attempt_remove_readback_anchor,
        'if(!LittleFS.remove("/pending.attempt")){',
        1,
    )
    if attempt_remove_readback_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker remove-readback mutation anchor missing")
    compile_case(
        "pending-clear-ignores-attempt-marker-remove-readback-failure",
        103,
        clear_source=attempt_remove_readback_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-attempt-marker-remove-readback-failure "
        "expected_exit=103"
    )

    attempt_recheck_anchor = (
        'if(!readPendingFile("/pending.attempt",attempt) ||\n'
        '     attempt.pulses!=pendingPulses ||\n'
        '     strcmp(attempt.nonce,pendingNonce.c_str())!=0 ||\n'
        '     strcmp(attempt.target,pendingTarget.c_str())!=0){'
    )
    attempt_recheck_mutation = clear_pending_source.replace(
        attempt_recheck_anchor,
        'if(!readPendingFile("/pending.attempt",attempt)){',
        1,
    )
    if attempt_recheck_mutation == clear_pending_source:
        raise AssertionError(f"{board}: attempt-marker identity recheck mutation anchor missing")
    compile_case(
        "pending-clear-skips-second-attempt-identity-check",
        96,
        clear_source=attempt_recheck_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-skips-second-attempt-identity-check "
        "expected_exit=96"
    )

    same_record_anchor = (
        "return left.magic==right.magic && left.pulses==right.pulses &&\n"
        "         strcmp(left.nonce,right.nonce)==0 &&\n"
        "         strcmp(left.target,right.target)==0 &&\n"
        "         left.checksum==right.checksum;"
    )
    same_record_mutation = same_pending_record_source.replace(
        same_record_anchor,
        "return true;",
        1,
    )
    if same_record_mutation == same_pending_record_source:
        raise AssertionError(f"{board}: durable-record identity mutation anchor missing")
    compile_case(
        "pending-clear-ignores-durable-record-identity",
        97,
        same_record_source=same_record_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-durable-record-identity "
        "expected_exit=97"
    )

    candidate_count_anchor = "if(candidateCount!=1 || !candidatePath){"
    candidate_count_mutation = clear_pending_source.replace(
        candidate_count_anchor,
        "if(false){",
        1,
    )
    if candidate_count_mutation == clear_pending_source:
        raise AssertionError(f"{board}: candidate-count guard mutation anchor missing")
    compile_case(
        "pending-clear-ignores-ambiguous-journal-candidates",
        99,
        clear_source=candidate_count_mutation,
    )
    print(
        f"{board} MUTATION_REJECTED pending-clear-ignores-ambiguous-journal-candidates "
        "expected_exit=99"
    )
