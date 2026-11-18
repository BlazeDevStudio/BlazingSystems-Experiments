#!/usr/bin/env python3
"""Exact-source dual-store poll-fault persistence regression for ESP32 and ESP8266.

This host lab models the NVS and EEPROM APIs. It does not emulate flash physics,
power-loss timing, wear, or an independent physical witness.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import sys

ROOT = Path.cwd()
ESP32 = ROOT / "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"
ESP8266 = ROOT / "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

def _matching_brace(source: str, opening: int) -> int:
    """Return the matching C/C++ closing brace, ignoring comments and literals."""
    if opening < 0 or opening >= len(source) or source[opening] != "{":
        raise ValueError("opening index must point to '{'")

    depth = 0
    state = "code"
    raw_terminator = ""
    index = opening

    while index < len(source):
        char = source[index]

        if state == "code":
            if source.startswith("//", index):
                state = "line_comment"
                index += 2
                continue
            if source.startswith("/*", index):
                state = "block_comment"
                index += 2
                continue
            if source.startswith('R"', index):
                delimiter_start = index + 2
                paren = source.find("(", delimiter_start)
                if paren != -1 and paren - delimiter_start <= 16:
                    delimiter = source[delimiter_start:paren]
                    if not any(ch.isspace() or ch in "\\()"
                               for ch in delimiter):
                        raw_terminator = ")" + delimiter + '"'
                        state = "raw_string"
                        index = paren + 1
                        continue
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index

        elif state == "line_comment":
            if char == "\n":
                state = "code"

        elif state == "block_comment":
            if source.startswith("*/", index):
                state = "code"
                index += 2
                continue

        elif state in ("string", "char"):
            if char == "\\":
                index += 2
                continue
            if ((state == "string" and char == '"') or
                    (state == "char" and char == "'")):
                state = "code"

        elif state == "raw_string":
            if source.startswith(raw_terminator, index):
                state = "code"
                index += len(raw_terminator)
                continue

        index += 1

    raise RuntimeError("unclosed C/C++ block")


def extract_block(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise RuntimeError(f"missing block marker: {marker}")
    brace = source.find("{", start)
    if brace < 0:
        raise RuntimeError(f"missing block opener: {marker}")
    end = _matching_brace(source, brace)
    return source[start:end + 1]


def extract_function(source: str, name: str) -> str:
    # Match a definition, not a call, comment, or forward declaration.
    # The signature set used by this lab has simple, single-line parameters.
    signature = re.compile(
        rf"(?m)^[ \t]*(?:(?:static|inline|constexpr|IRAM_ATTR|ICACHE_RAM_ATTR)\s+)*"
        rf"(?:[A-Za-z_][\w:<>*&]*[ \t]+)+{re.escape(name)}"
        r"\s*\([^;{}]*\)\s*(?:const\s*)?\{"
    )
    match = signature.search(source)
    if not match:
        raise RuntimeError(f"missing function definition: {name}")
    opening = match.end() - 1
    end = _matching_brace(source, opening)
    return source[match.start():end + 1]


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
    record = extract_block(sample, "struct Record")
    function = extract_function(sample, "selected")
    if "int nested[2] = {1, 2};" not in record:
        raise AssertionError("struct extractor stopped inside a literal/comment")
    if not function.startswith("bool selected") or "if (value) { return true; }" not in function:
        raise AssertionError("function extractor did not select the definition")
    if not function.endswith("}"):
        raise AssertionError("function extractor returned an incomplete body")

    try:
        extract_block('struct Broken { const char *value = "}" ;', "struct Broken")
    except RuntimeError:
        pass
    else:
        raise AssertionError("unterminated block must fail closed")


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
  static std::vector<uint8_t> staged;
};
std::vector<uint8_t> NvsFlash::durable;
std::vector<uint8_t> NvsFlash::staged;
static bool nvsReadError=false, nvsFailSet=false, nvsFailCommit=false;
static bool nvsFailCommitAfterWrite=false;
static bool nvsFailOpen=false, nvsTypeMismatch=false, nvsFailReadback=false;
nvs_handle_t pollFaultNvsHandle=0;
bool pollFaultBackupReady=false;
void initPollFaultBackupStore();
esp_err_t nvs_open(const char*,int,nvs_handle_t* handle){
  if(nvsFailOpen) return ESP_FAIL;
  *handle=1;
  return ESP_OK;
}
esp_err_t nvs_get_blob(nvs_handle_t handle,const char*,void* value,size_t* length){
  if(handle==0 || !length || nvsReadError) return ESP_FAIL;
  if(nvsTypeMismatch) return ESP_ERR_NVS_TYPE_MISMATCH;
  if(NvsFlash::durable.empty()) return ESP_ERR_NVS_NOT_FOUND;
  if(!value){ *length=NvsFlash::durable.size(); return ESP_OK; }
  if(*length<NvsFlash::durable.size()){
    *length=NvsFlash::durable.size();
    return ESP_ERR_NVS_INVALID_LENGTH;
  }
  memcpy(value,NvsFlash::durable.data(),NvsFlash::durable.size());
  *length=NvsFlash::durable.size();
  return ESP_OK;
}
esp_err_t nvs_set_blob(nvs_handle_t handle,const char*,const void* value,size_t length){
  if(handle==0 || nvsFailSet) return ESP_FAIL;
  const uint8_t* bytes=(const uint8_t*)value;
  NvsFlash::staged.assign(bytes,bytes+length);
  return ESP_OK;
}
esp_err_t nvs_commit(nvs_handle_t handle){
  if(handle==0 || nvsFailCommit) return ESP_FAIL;
  NvsFlash::durable=NvsFlash::staged;
  // Model an ambiguous API result: bytes reached durable media, but commit reports failure.
  if(nvsFailCommitAfterWrite) return ESP_FAIL;
  if(nvsFailReadback) nvsReadError=true;
  return ESP_OK;
}
void resetStorage(){
  NvsFlash::durable.clear(); NvsFlash::staged.clear();
  nvsReadError=false; nvsFailSet=false; nvsFailCommit=false;
  nvsFailCommitAfterWrite=false;
  nvsFailOpen=false; nvsTypeMismatch=false; nvsFailReadback=false;
  pollFaultNvsHandle=0; pollFaultBackupReady=false;
  initPollFaultBackupStore();
}
void rebootStorage(){
  nvsReadError=false; nvsFailReadback=false;
  pollFaultNvsHandle=0; pollFaultBackupReady=false;
  initPollFaultBackupStore();
}
void corruptStorage(){
  if(!NvsFlash::durable.empty()) NvsFlash::durable[0]^=0x01;
}
"""
        fail_write = "nvsFailCommit=true;"
        fail_read = "nvsFailReadback=true;"
        ambiguous_commit_setup = "nvsFailCommitAfterWrite=true;"
        clear_fail = "nvsReadError=false; nvsFailSet=false; nvsFailCommit=false; nvsFailCommitAfterWrite=false; nvsFailOpen=false; nvsTypeMismatch=false; nvsFailReadback=false;"
        no_marker = "NvsFlash::durable.clear(); NvsFlash::staged.clear();"
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
struct FakeEEPROM {
  static std::vector<uint8_t> flash;
  std::vector<uint8_t> buffer;
  size_t size=0;
  bool ready=true, failCommit=false, failCommitAfterWrite=false, failRead=false, failReadAfterCommit=false;
  bool begin(size_t n) {
    if(!ready) return false;
    size=n;
    if(flash.size()<n) flash.resize(n,0xFF);
    buffer.assign(flash.begin(),flash.begin()+n);
    return true;
  }
  void end(){ size=0; buffer.clear(); }
  bool commit(){
    if(failCommit) return false;
    if(!outputsInhibited) persistenceBeforeOutputInhibit=true;
    flash=buffer;
    // Model a write that reached flash even though the API reports a failed commit.
    if(failCommitAfterWrite) return false;
    if(failReadAfterCommit) failRead=true;
    return true;
  }
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
}
"""
        fail_write = "EEPROM.failCommit=true;"
        fail_read = "EEPROM.failReadAfterCommit=true;"
        ambiguous_commit_setup = "EEPROM.failCommitAfterWrite=true;"
        clear_fail = "EEPROM.failCommit=false; EEPROM.failCommitAfterWrite=false; EEPROM.failRead=false; EEPROM.failReadAfterCommit=false;"
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
  assert(journalRecoveryRequired && !insertMode);
  assert(outputsInhibited);
  assert(!persistenceBeforeOutputInhibit);
  assert(pollFaultBackupPresentOrCorrupt());
  rebootStorage();
  assertBootDenied();

  // An NVS lookup error must not make an existing sticky marker appear absent.
  NVS_READ_ERROR_SCENARIO

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
    main = main.replace("NVS_READ_ERROR_SCENARIO", nvs_read_error)
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

if __name__ == "__main__":
    test_extractors()
    print("POLL_FAULT_EXTRACTOR_SELFTEST=PASS", flush=True)
    run("ESP32", ESP32)
    run("ESP8266", ESP8266)
