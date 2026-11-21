#!/usr/bin/env python3
"""PHX-HARDWARE: exact source-extracted append/quarantine test, two ESP sketches.
Runs unmodified extracted function bodies with a C++17 fake LittleFS.
Neither flash power-cycle testing nor proof of durable financial accounting.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "esp8266/BlazePwifiVendo"))
from firmware_lab_source import extract_function
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)

CPP = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  void remove(size_t index){erase(index);}
};
static constexpr size_t QUARANTINE_MAX_BYTES=4096;
static bool fsReady=true;
static bool journalRecoveryRequired=false;
// Mirrors the production one-shot gate state used by canAttemptCoinPost().
static bool pendingPostAttempted=false;
bool outputPolarityKnown=true;
static bool attemptMarkerExists=true, attemptMarkerValid=true;
static uint8_t pendingPulses=4;
static bool pendingReady=true;
static String pendingNonce="nonce00112233445";
static String pendingTarget="target0011223344";
struct PendingRecord { uint8_t pulses=0; char nonce[17]{}; char target[33]{}; };
static PendingRecord attemptMarker{};
bool readPendingFile(const char *path,PendingRecord &out){
  if(std::strcmp(path,"/pending.attempt")!=0 || !attemptMarkerExists || !attemptMarkerValid) return false;
  out=attemptMarker;
  return true;
}
@@SOURCE_ATTEMPT_MATCH@@
static int clearCount=0;
static bool clearAllowed=true;
unsigned long millis(){return 1234UL;}
bool clearPending(){
  ++clearCount;
  if(!clearAllowed){journalRecoveryRequired=true; return false;}
  pendingPulses=0; pendingNonce.clear(); pendingTarget.clear();
  // Production clearPending resets this only after durable disposition succeeds.
  pendingPostAttempted=false;
  attemptMarkerExists=false;
  return true;
}
struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;
enum SeekMode { SeekSet };
struct FakeDisk {
  std::string bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
  bool priorOpenFail=false, appendOpenFail=false, verifyOpenFail=false;
  bool logExists=true;
  bool shortWrite=false, mutateAfterClose=false, mutatePrefixAfterClose=false, mutateOnRead=false;
  bool removeOneByteAfterClose=false;
  bool hasWritten=false;
} disk;
struct File {
  FakeDisk* d=nullptr;
  bool writing=false;
  size_t cursor=0;
  File()=default;
  File(FakeDisk* p,bool writable):d(p),writing(writable){}
  explicit operator bool() const {return d!=nullptr;}
  size_t size() const{return d?d->bytes.size():0;}
  size_t write(const uint8_t* buf,size_t len){
    if(!d || !writing)return 0;
    size_t n=(d->shortWrite && len)?len-1:len;
    d->bytes.append((const char*)buf,n);
    d->hasWritten=true;
    return n;
  }
  void flush(){}
  void close(){
    if(d && writing){
      if(d->mutateAfterClose && !d->bytes.empty()) d->bytes.back()='Z';
      // Simulate same-size corruption of an older record while the new suffix stays intact.
      if(d->mutatePrefixAfterClose && !d->bytes.empty()) d->bytes[0]='U';
      if(d->removeOneByteAfterClose && !d->bytes.empty()) d->bytes.pop_back();
    }
    d=nullptr;
  }
  bool seek(size_t offset,SeekMode){
    if(!d || writing || offset>d->bytes.size())return false;
    cursor=offset;
    return true;
  }
  size_t available() const{return d && !writing && cursor<d->bytes.size()?d->bytes.size()-cursor:0;}
  int read(){
    if(!d || writing || cursor>=d->bytes.size())return -1;
    int byte=(unsigned char)d->bytes[cursor++];
    return (d->mutateOnRead && d->hasWritten)?(byte^1):byte;
  }
};
struct FakeLittleFS {
  bool exists(const char* path){
    return strcmp(path,"/quarantine.log")==0 && disk.logExists;
  }
  File open(const char* path,const char* mode){
    if(strcmp(path,"/quarantine.log")!=0)return {};
    if(strcmp(mode,"a")==0){
      if(disk.appendOpenFail)return {};
      // Append mode creates the first quarantine log when it is absent.
      disk.logExists=true;
      return File(&disk,true);
    }
    if(strcmp(mode,"r")==0){
      if(!disk.logExists || (!disk.hasWritten && disk.priorOpenFail) ||
         (disk.hasWritten && disk.verifyOpenFail)) return {};
      return File(&disk,false);
    }
    return {};
  }
} LittleFS;

@@SOURCE_COIN_POST_GATE@@
@@SOURCE_ENCODE@@
@@SOURCE_TOKEN_VALID@@
@@SOURCE_RECORD_VALID@@
@@SOURCE_CRC32_UPDATE@@
@@SOURCE_INSPECT@@
@@SOURCE_APPEND@@
@@SOURCE_QUARANTINE@@
int main(){
  for(int scenario=0;scenario<36;scenario++){
    disk=FakeDisk{};
    clearCount=0;
    clearAllowed=true;
    fsReady=true;
    journalRecoveryRequired=false;
    pendingPostAttempted=true;
    pendingPulses=4;
    pendingReady=true;
    pendingNonce="nonce00112233445";
    pendingTarget="target0011223344";
    attemptMarker=PendingRecord{};
    attemptMarker.pulses=pendingPulses;
    std::strcpy(attemptMarker.nonce,pendingNonce.c_str());
    std::strcpy(attemptMarker.target,pendingTarget.c_str());
    attemptMarkerExists=true;
    attemptMarkerValid=true;
    if(scenario==1) fsReady=false;
    if(scenario==2) pendingPulses=0;
    if(scenario==3) disk.priorOpenFail=true;
    if(scenario==4) disk.appendOpenFail=true;
    if(scenario==5) disk.shortWrite=true;
    if(scenario==6) disk.verifyOpenFail=true;
    if(scenario==7) disk.removeOneByteAfterClose=true;
    if(scenario==8) disk.mutateAfterClose=true; // corrupts final newline
    if(scenario==9) disk.mutateOnRead=true; // verification read fault only
    if(scenario==10){
      const std::string valid="TIME=1 PULSES=1 NONCE=old TARGET=old REASON=old\n";
      disk.bytes.clear();
      while(disk.bytes.size()<=QUARANTINE_MAX_BYTES) disk.bytes+=valid;
    }
    if(scenario==11) clearAllowed=false;
    String reason="window expired";
    if(scenario==12) reason=String("bad\nRECORD=forged\t\\");
    if(scenario==13) journalRecoveryRequired=true;
    if(scenario==14)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier\n";
    if(scenario==15)
      disk.bytes+="TIME=9 PULSES=4 NONCE=nonce00112233445";
    if(scenario==16)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier\n"
                 "TIME=9 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=duplicate\n";
    if(scenario==17)
      disk.bytes="TIME=not-a-number PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=forged-but-complete\n";
    if(scenario==18)
      disk.bytes="TIME=4294967296 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=overflowed-time\n";
    if(scenario==19) pendingPostAttempted=false; // attempted state missing
    if(scenario==20) attemptMarkerExists=false;
    if(scenario==21) attemptMarkerValid=false;
    if(scenario==22) std::strcpy(attemptMarker.nonce,"wrongnonce123456");
    // Malformed prior quarantine records must never authorize pending deletion.
    if(scenario==23)
      disk.bytes="TIME=1 PULSES=not-a-number NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==24)
      disk.bytes="TIME=1 PULSES=21 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==25)
      disk.bytes="TIME=1 PULSES=1 NONCE= TARGET=oldtarget REASON=old\n";
    if(scenario==26)
      disk.bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET= REASON=old\n";
    if(scenario==27)
      disk.bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=\n";
    if(scenario==28)
      disk.bytes="TIME=1 PULSES=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==29){
      pendingTarget="target0011223344 REASON=earlier";
      std::strcpy(attemptMarker.target,pendingTarget.c_str());
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier REASON=window expired\n";
    }
    if(scenario==30){
      pendingTarget="target with spaces";
      std::strcpy(attemptMarker.target,pendingTarget.c_str());
    }
    if(scenario==31) reason=String("window REASON=expired");
    if(scenario==32)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window REASON=expired\n";
    // First-ever quarantine record: no file exists before append.
    if(scenario==33){ disk.logExists=false; disk.bytes.clear(); }
    // First-ever append open failure must not create a log or clear pending.
    if(scenario==34){ disk.logExists=false; disk.bytes.clear(); disk.appendOpenFail=true; }
    // Scenario 35 corrupts a pre-existing record but leaves the appended suffix exact.
    if(scenario==35) disk.mutatePrefixAfterClose=true;
    const std::string bytesBefore=disk.bytes;
    bool expectClear=(scenario==0 || scenario==12 || scenario==14 || scenario==31 || scenario==33);
    bool expectClearAttempt=expectClear || scenario==11;
    bool expectRecovery=scenario==1 || scenario==3 || scenario==4 ||
                        (scenario>=5 && scenario<=10) ||
                        scenario==11 || scenario==13 || scenario==15 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33);
    bool ok=quarantinePending(reason);
    if(ok!=expectClear || clearCount!=(expectClearAttempt?1:0) ||
       (!expectClear && pendingPulses!=(scenario==2?0:4)) ||
       (scenario==12 &&
        (std::count(disk.bytes.begin(),disk.bytes.end(),'\n')!=2 ||
         disk.bytes.find("bad\\nRECORD=forged\\t\\\\")==std::string::npos)) ||
       (scenario==4 && disk.bytes!=bytesBefore) ||
       (scenario==10 && disk.bytes!=bytesBefore) ||
       (scenario==14 && disk.bytes!=bytesBefore) ||
       (scenario==15 && disk.bytes!=bytesBefore) ||
       (scenario==16 && disk.bytes!=bytesBefore) ||
       (scenario==17 && disk.bytes!=bytesBefore) ||
       (scenario==18 && disk.bytes!=bytesBefore) ||
       (scenario>=19 && scenario!=31 && scenario!=33 && scenario!=35 && disk.bytes!=bytesBefore) ||
       (scenario==31 && (disk.bytes.find(std::string("window")+char(92)+"x20REASON=expired")==std::string::npos || disk.bytes.find("window REASON=expired")!=std::string::npos)) ||
       (scenario==33 && (!disk.logExists || disk.bytes.empty() ||
         disk.bytes.find("TIME=1234 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window expired") == std::string::npos)) ||
       (scenario==34 && (disk.logExists || !disk.bytes.empty())) ||
       (scenario==35 && (disk.bytes.empty() || disk.bytes[0]!='U' ||
         disk.bytes.find("TIME=1234 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window expired\n")==std::string::npos)) ||
       journalRecoveryRequired!=expectRecovery || canAttemptCoinPost()){
      std::cerr<<"SOURCE_QUARANTINE_FAIL scenario="<<scenario<<"\n";
      return 1;
    }
    if(expectRecovery){
      const std::string ambiguousBytes=disk.bytes;
      const int attemptsBeforeRetry=clearCount;
      disk.shortWrite=false;
      disk.verifyOpenFail=false;
      disk.removeOneByteAfterClose=false;
      disk.mutateAfterClose=false;
      disk.mutateOnRead=false;
      clearAllowed=true;
      if(quarantinePending(reason) || disk.bytes!=ambiguousBytes ||
         clearCount!=attemptsBeforeRetry || !journalRecoveryRequired ||
         canAttemptCoinPost()){
        std::cerr<<"SOURCE_QUARANTINE_RETRY_MUTATED scenario="<<scenario<<"\n";
        return 1;
      }
    }
    if(scenario==3 || scenario==4 || (scenario>=5 && scenario<=10) ||
       scenario==11 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33)){
      // Simulate volatile latch loss on reboot while retaining LittleFS bytes.
      const std::string rebootBytes=disk.bytes;
      const int clearsBeforeReboot=clearCount;
      journalRecoveryRequired=false;
      disk.hasWritten=false;
      bool rebootOk=quarantinePending(reason);
      bool persistentHardStop=(scenario==3 || scenario==4 || scenario==5 ||
                                scenario==7 || scenario==8 || scenario==10 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33));
      if(persistentHardStop){
        if(rebootOk || !journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot || pendingPulses!=4 || canAttemptCoinPost()){
          std::cerr<<"SOURCE_QUARANTINE_TORN_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      } else {
        if(!rebootOk || journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot+1 || pendingPulses!=0 || canAttemptCoinPost()){
          std::cerr<<"SOURCE_QUARANTINE_IDEMPOTENT_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      }
    }
  }
  std::cout<<"SOURCE_QUARANTINE_PASS 36/36 scenarios (physical power cut NOT tested)\n";
}
'''

def extract(src: str, signature: str) -> str:
    # The caller stores a C++ signature prefix; delegate lexical parsing to the
    # shared helper so braces in comments and literals cannot truncate a body.
    name = signature.split("(", 1)[0].split()[-1]
    return extract_function(src, name)

def verify_lexical_extractor():
    fixture = (
        'String lexicalProbe(){\n'
        '  const char *ordinary = "}";\n'
        '  const char *raw = R"tag({ })tag";\n'
        '  /* } */\n'
        '  return ordinary;\n'
        '}'
    )
    if extract(fixture, "String lexicalProbe(") != fixture:
        raise SystemExit(
            "PHX-HARDWARE: source extractor truncated a C++ literal/comment fixture"
        )


verify_lexical_extractor()


# These helpers define the pending-event/quarantine safety boundary. They are
# intentionally byte-identical across ESP32 and ESP8266 so board drift cannot
# silently weaken one controller while the other remains protected.
PARITY_SIGNATURES = (
    # Pending-event and quarantine persistence must remain byte-identical.
    "bool readPendingFile(",
    "bool markPendingPostAttempt(",
    "bool pendingAttemptMarkerMatches()",
    "bool clearPending(",
    "String quarantineLogField(",
    "bool quarantineLogTokenValid(",
    "bool quarantineLogRecordValid(",
    "uint32_t quarantineLogCrc32Update(",
    "bool inspectQuarantineLog(",
    "bool appendQuarantineRecord(",
    "bool quarantinePending(",
    # The two board consumers must also share one poll/coin response boundary.
    "bool pollJsonSpace(",
    "bool pollJsonHex(",
    "bool pollJsonSkipString(",
    "bool pollJsonSkipComposite(",
    "bool pollJsonSkipPrimitive(",
    "bool pollJsonSkipValue(",
    "bool pollJsonTopLevelTrue(",
    "bool validSha256Hex(",
    "bool coinPostDispositionVerified(",
    "void handleCoinPostResponse(",
    "bool acceptPollResponse(",
)


POLARITY_SIGNATURE = "bool canAttemptCoinPost(){"


def board_safety_helpers():
    result = {}
    for board, ino in BOARDS:
        source = ino.read_text(encoding="utf-8")
        result[board] = {
            signature: extract(source, signature)
            for signature in PARITY_SIGNATURES
        }
        # This gate is intentionally board-specific until ESP32 has its own
        # reviewed local polarity profile. Compare its shared admission body
        # after validating the ESP8266-only interlock separately.
        result[board][POLARITY_SIGNATURE] = extract(source, POLARITY_SIGNATURE)
    return result


def board_parity_mismatches(helpers):
    return [
        signature for signature in PARITY_SIGNATURES
        if helpers["ESP32"][signature] != helpers["ESP8266"][signature]
    ]


def board_polarity_guard_problem(helpers):
    esp8266 = helpers["ESP8266"][POLARITY_SIGNATURE]
    esp32 = helpers["ESP32"][POLARITY_SIGNATURE]
    if "outputPolarityKnown && pinConfigSafe && fsReady" not in esp8266:
        return "ESP8266 local polarity/GPIO admission guard is missing"
    if "outputPolarityKnown && pinConfigSafe && fsReady" not in esp32:
        return "ESP32 local polarity/GPIO admission guard is missing"
    normalized_esp8266 = " ".join(esp8266.split())
    normalized_esp32 = " ".join(esp32.split())
    if normalized_esp8266 != normalized_esp32:
        return "coin POST gate differs between ESP32 and ESP8266 after local polarity guards"
    return None


def verify_board_safety_parity():
    helpers = board_safety_helpers()
    mismatches = board_parity_mismatches(helpers)
    if mismatches:
        raise SystemExit(
            "PHX-HARDWARE: ESP shared safety-helper drift: " + ", ".join(mismatches)
        )
    polarity_problem = board_polarity_guard_problem(helpers)
    if polarity_problem:
        raise SystemExit("PHX-HARDWARE: " + polarity_problem)

    # Failure injection: a fail-open append result on one board must be
    # detected before that board can diverge from the reviewed peer.
    mutated = {board: dict(functions) for board, functions in helpers.items()}
    signature = "bool appendQuarantineRecord("
    original = mutated["ESP8266"][signature]
    if "return verified;" not in original:
        raise SystemExit("PHX-HARDWARE: parity mutation anchor missing")
    mutated["ESP8266"][signature] = original.replace(
        "return verified;", "return true;", 1
    )
    if not board_parity_mismatches(mutated):
        raise SystemExit("PHX-HARDWARE: fail-open board-drift mutation was not detected")

    # A one-board fail-open coin disposition must be rejected before drift ships.
    disposition_signature = "bool coinPostDispositionVerified("
    disposition = mutated["ESP8266"][disposition_signature]
    if disposition.count("return false;") != 1:
        raise SystemExit("PHX-HARDWARE: coin-disposition fail-open mutation anchor is not unique")
    mutated_disposition = {board: dict(functions) for board, functions in helpers.items()}
    mutated_disposition["ESP8266"][disposition_signature] = disposition.replace(
        "return false;", "return true;", 1
    )
    if not board_parity_mismatches(mutated_disposition):
        raise SystemExit("PHX-HARDWARE: coin-disposition fail-open mutation was not detected")

    # A one-board permissive root-status parser must also be rejected.
    parser_signature = "bool pollJsonTopLevelTrue("
    parser = helpers["ESP8266"][parser_signature]
    parser_anchor = "return p==n && found==1 && accepted;"
    if parser.count(parser_anchor) != 1:
        raise SystemExit("PHX-HARDWARE: poll-parser permissive mutation anchor is not unique")
    mutated_parser = {board: dict(functions) for board, functions in helpers.items()}
    mutated_parser["ESP8266"][parser_signature] = parser.replace(
        parser_anchor, "return true;", 1
    )
    if not board_parity_mismatches(mutated_parser):
        raise SystemExit("PHX-HARDWARE: permissive poll-parser mutation was not detected")

    # acceptPollResponse is deliberately deny-only until CORE/QA approve a contract.
    admission_signature = "bool acceptPollResponse("
    admission = helpers["ESP8266"][admission_signature]
    if admission.count("return false;") != 1:
        raise SystemExit("PHX-HARDWARE: poll-admission mutation anchor is not unique")
    mutated_admission = {board: dict(functions) for board, functions in helpers.items()}
    mutated_admission["ESP8266"][admission_signature] = admission.replace(
        "return false;", "return true;", 1
    )
    if not board_parity_mismatches(mutated_admission):
        raise SystemExit("PHX-HARDWARE: positive poll-admission mutation was not detected")

    # Both boards must retain the local polarity admission gate.
    for board in ("ESP8266", "ESP32"):
        polarity_mutated = {name: dict(functions) for name, functions in helpers.items()}
        polarity_mutated[board][POLARITY_SIGNATURE] = (
            polarity_mutated[board][POLARITY_SIGNATURE].replace(
                "outputPolarityKnown && ", "", 1
            )
        )
        if board_polarity_guard_problem(polarity_mutated) is None:
            raise SystemExit("PHX-HARDWARE: " + board + " output-polarity gate removal mutation was not detected")

    print("BOARD_SHARED_SAFETY_PARITY_PASS 22/22 functions byte-identical")
    print("ESP32_AND_ESP8266_LOCAL_POLARITY_GATES_PASS")
    print("BOARD_PARITY_MUTATION_REJECTED fail-open append verification bypass")
    print("BOARD_PARITY_MUTATION_REJECTED fail-open coin disposition")
    print("BOARD_PARITY_MUTATION_REJECTED permissive poll status parser")
    print("BOARD_PARITY_MUTATION_REJECTED positive poll response admission")
    print("ESP32_AND_ESP8266_POLARITY_MUTATIONS_REJECTED removed local gate")


verify_board_safety_parity()
failed_boards = []
for board, ino in BOARDS:
    source = ino.read_text(encoding="utf-8")
    actual = CPP.replace("@@SOURCE_COIN_POST_GATE@@", extract(source, "bool canAttemptCoinPost(){"))
    actual = actual.replace("@@SOURCE_ATTEMPT_MATCH@@", extract(source, "bool pendingAttemptMarkerMatches(){"))
    actual = actual.replace("@@SOURCE_ENCODE@@", extract(source, "String quarantineLogField("))
    actual = actual.replace("@@SOURCE_TOKEN_VALID@@", extract(source, "bool quarantineLogTokenValid("))
    actual = actual.replace("@@SOURCE_RECORD_VALID@@", extract(source, "bool quarantineLogRecordValid("))
    actual = actual.replace("@@SOURCE_CRC32_UPDATE@@", extract(source, "uint32_t quarantineLogCrc32Update("))
    actual = actual.replace("@@SOURCE_INSPECT@@", extract(source, "bool inspectQuarantineLog("))
    actual = actual.replace("@@SOURCE_APPEND@@", extract(source, "bool appendQuarantineRecord("))
    actual = actual.replace("@@SOURCE_QUARANTINE@@", extract(source, "bool quarantinePending("))
    with tempfile.TemporaryDirectory(prefix="phx-hw-q-") as temp:
        cpp = Path(temp, "test.cpp")
        binary = Path(temp, "test")
        cpp.write_text(actual, encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(cpp), "-o", str(binary)], check=True)
        completed = subprocess.run([str(binary)], capture_output=True, text=True)
        if completed.stdout:
            print(completed.stdout, end="")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end="")
        if completed.returncode:
            failed_boards.append(board)
        else:
            print(f"{board}: compiled exact extracted source")
            # Append-open, short-write, readback and corruption failures are
            # exercised in the normal source-exact scenario matrix above.

if failed_boards:
    raise SystemExit("PHX-HARDWARE: quarantine regression failed on " + ", ".join(failed_boards))
print("PHX-HARDWARE: 72/72 source-extracted host scenarios PASS; no hardware evidence")
poll_lab = ROOT / "esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py"
subprocess.run([sys.executable, str(poll_lab)], check=True)
register_lab = ROOT / "esp8266/BlazePwifiVendo/register_config_failclosed_lab.py"
subprocess.run([sys.executable, str(register_lab)], check=True)
attempt_marker_lab = ROOT / "esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py"
attempt_marker_result = subprocess.run(
    [sys.executable, str(attempt_marker_lab)],
    capture_output=True, text=True,
)
print(attempt_marker_result.stdout, end="")
if attempt_marker_result.stderr:
    print(attempt_marker_result.stderr, file=sys.stderr, end="")
if attempt_marker_result.returncode:
    raise SystemExit(attempt_marker_result.returncode)
if attempt_marker_result.stdout.count("PENDING_ATTEMPT_MARKER_PASS 28/28") != len(BOARDS):
    raise SystemExit("PHX-HARDWARE: attempt-marker per-board summary count mismatch")
if "PHX-HARDWARE: 28/28 source-extracted cases per board (56/56 total) PASS" not in attempt_marker_result.stdout:
    raise SystemExit("PHX-HARDWARE: attempt-marker aggregate summary mismatch")

