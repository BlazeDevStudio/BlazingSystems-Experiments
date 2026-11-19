#!/usr/bin/env python3
"""Execute the real ESP8266 config loader against a fault-injected EEPROM model.

The model follows ESP8266 Arduino core 3.1.2 EEPROM.cpp: begin() allocates
indeterminate RAM for a new buffer, reuses a same-size buffer, and only logs
a failed flashRead without clearing or reporting it to the caller. The lab
uses deterministic poison bytes to model that untrusted RAM state.

Core source:
https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp

The lab covers full-image read failures, same-boot setup-save denial after
malformed v1/v2 or unknown records, successful local v1/v2-to-v3 migration
with poll-fault marker preservation, and a failed migration commit followed
by cold-boot recovery. These are fake-flash host simulations, not physical
power-cut acceptance or the separate financial ledger migration.
"""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

def mask_non_code(source: str) -> str:
    masked = list(source)
    def blank(start: int, end: int) -> None:
        for p in range(start, end):
            if source[p] not in "\r\n":
                masked[p] = " "
    i = 0
    while i < len(source):
        if source.startswith("//", i):
            start = i
            i += 2
            while i < len(source) and source[i] not in "\r\n":
                i += 1
            blank(start, i)
            continue
        if source.startswith("/*", i):
            start = i
            end = source.find("*/", i + 2)
            if end < 0:
                raise RuntimeError("unterminated C/C++ comment")
            i = end + 2
            blank(start, i)
            continue
        if source.startswith('R"', i):
            delimiter_start = i + 2
            paren = source.find("(", delimiter_start)
            if paren != -1 and paren - delimiter_start <= 16:
                delimiter = source[delimiter_start:paren]
                if not any(ch.isspace() or ch in "\\()" for ch in delimiter):
                    terminator = ")" + delimiter + '"'
                    end = source.find(terminator, paren + 1)
                    if end < 0:
                        raise RuntimeError("unterminated C/C++ raw string")
                    end += len(terminator)
                    blank(i, end)
                    i = end
                    continue
        if source[i] in ('"', "'"):
            quote = source[i]
            start = i
            i += 1
            while i < len(source):
                if source[i] == "\\":
                    i += 2
                    continue
                if source[i] == quote:
                    i += 1
                    break
                i += 1
            else:
                raise RuntimeError("unterminated C/C++ literal")
            blank(start, i)
            continue
        i += 1
    return "".join(masked)

def matching_brace(source: str, opening: int) -> int:
    masked = mask_non_code(source)
    depth = 0
    for i in range(opening, len(source)):
        if masked[i] == "{":
            depth += 1
        elif masked[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise RuntimeError("unbalanced C/C++ block")

def extract_block(source: str, marker: str) -> str:
    masked = mask_non_code(source)
    start = masked.find(marker)
    if start < 0:
        raise RuntimeError(f"missing source block: {marker}")
    opening = masked.find("{", start)
    if opening < 0:
        raise RuntimeError(f"missing source block opener: {marker}")
    return source[start:matching_brace(source, opening) + 1]

def extract_functions(source: str, name: str):
    masked = mask_non_code(source)
    signature = re.compile(
        rf"(?m)^[ \t]*(?:(?:static|inline|constexpr)\s+)*"
        rf"(?:[A-Za-z_][\w:<>*&]*[ \t]+)+{re.escape(name)}"
        r"\s*\([^;{}]*\)\s*(?:const\s*)?\{"
    )
    found = []
    pos = 0
    while True:
        match = signature.search(masked, pos)
        if not match:
            break
        opening = match.end() - 1
        end = matching_brace(source, opening)
        found.append((match.start(), source[match.start():end + 1]))
        pos = end + 1
    return found

def extract_function(source: str, name: str, optional=False) -> str:
    found = extract_functions(source, name)
    if not found:
        if optional:
            return ""
        raise RuntimeError(f"missing production function: {name}")
    return found[0][1]

def extract_constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith(("static const ", "const ")) and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

def source_functions(source: str, omit_failure_invalidation: bool = False) -> str:
    names = [
        "makeSetupPassword",
        "configChecksum",
        "fixedStringTerminated",
        "configStringsTerminated",
        "configPolarityFieldsValid",
        "configRecordErased",
        "readFullEepromImage",
        "restoreEepromRamImage",
        "refreshVerifiedEepromImage",
        "readPollFaultBackupFlash",
        "pollFaultRecordChecksum",
        "makePollFaultRecord",
        "validPollFaultRecord",
        "pollFaultBackupPresentOrCorrupt",
        "writePollFaultBackup",
        "loadPollPulseFaultLatch",
        "defaults",
        "latchConfigPersistenceFailure",
        "saveCfg",
        "loadCfg",
    ]
    pieces = []
    for name in names:
        found = extract_functions(source, name)
        if name == "readFullEepromImage" and not found:
            continue
        if not found:
            raise RuntimeError(f"missing production function: {name}")
        function = found[0][1]
        if name == "latchConfigPersistenceFailure" and omit_failure_invalidation:
            anchor = "  configImageReadVerified=false;"
            if anchor not in function:
                raise RuntimeError("mutation anchor missing from failure latch")
            function = function.replace(
                anchor,
                "  // injected mutation: verified-image authority was not revoked",
                1,
            )
        pieces.append(function)
    return "\n\n".join(pieces)

def harness(source: str, omit_failure_invalidation: bool = False) -> str:
    structs = "\n\n".join([
        extract_block(source, "struct ConfigV1") + ";",
        extract_block(source, "struct ConfigV2") + ";",
        extract_block(source, "struct Config {") + ";",
        extract_block(source, "struct PollFaultRecord") + ";",
    ])
    constants = extract_constants(source, (
        "MAGIC_V1", "MAGIC_V2", "MAGIC",
        "POLL_FAULT_EEPROM_OFFSET", "POLL_FAULT_EEPROM_BYTES",
        "POLL_FAULT_RECORD_MAGIC", "POLL_FAULT_RECORD_VERSION",
    ))
    prelude = r"""
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

static const uint32_t EEPROM_start=0x40210000UL;
static unsigned rawFlashReadCalls=0;
static unsigned rawReadFailFirstCount=0;
static bool rawReadPersistentFailure=false;
static unsigned flashWriteCount=0;
static bool fakeCommitFailure=false;

bool fakeFlashRead(uint32_t address,uint8_t* destination,size_t length);
struct FakeEEPROM {
  static std::vector<uint8_t> flash;
  std::vector<uint8_t> buffer;
  size_t size=0;
  bool dirty=false;
  void begin(size_t requested){
    if(requested==0) return;
    if(requested>4096) requested=4096;
    requested=(requested+3)&(~(size_t)3);
    if(flash.size()<requested) flash.resize(requested,0xFF);
    // Core 3.1.2 keeps an existing same-size allocation. A new uint8_t[]
    // buffer is indeterminate; 0xA5 is deterministic poison for this lab.
    if(buffer.empty() || requested!=size) buffer.assign(requested,0xA5);
    size=requested;
    // Match EEPROMClass's sector calculation and ignored flashRead result.
    const uint32_t sector=(uint32_t)(EEPROM_start-0x40200000UL)/4096UL;
    (void)fakeFlashRead(sector*4096UL,buffer.data(),size);
    dirty=false;
  }
  bool commit(){
    if(!size) return false;
    if(!dirty) return true;
    if(fakeCommitFailure) return false;
    flash=buffer;
    dirty=false;
    ++flashWriteCount;
    return true;
  }
  bool end(){
    const bool result=commit();
    buffer.clear();
    size=0;
    dirty=false;
    return result;
  }
  size_t length() const { return size; }
  uint8_t* getDataPtr(){
    if(buffer.empty()) return nullptr;
    dirty=true;
    return buffer.data();
  }
  const uint8_t* getConstDataPtr() const {
    return buffer.empty()?nullptr:buffer.data();
  }
  template<class T> T& get(int offset,T& value){
    if(offset<0 || (size_t)offset+sizeof(T)>buffer.size()) return value;
    memcpy(&value,buffer.data()+offset,sizeof(T));
    return value;
  }
  template<class T> const T& put(int offset,const T& value){
    if(offset<0 || (size_t)offset+sizeof(T)>buffer.size()) return value;
    if(memcmp(buffer.data()+offset,&value,sizeof(T))!=0){
      memcpy(buffer.data()+offset,&value,sizeof(T));
      dirty=true;
    }
    return value;
  }
};
std::vector<uint8_t> FakeEEPROM::flash;
bool fakeFlashRead(uint32_t address,uint8_t* destination,size_t length){
  ++rawFlashReadCalls;
  if(rawReadPersistentFailure) return false;
  if(rawReadFailFirstCount){
    --rawReadFailFirstCount;
    return false;
  }
  const uint32_t base=(uint32_t)(EEPROM_start-0x40200000UL);
  if(address<base) return false;
  const size_t offset=(size_t)(address-base);
  if(offset+length>FakeEEPROM::flash.size()) return false;
  memcpy(destination,FakeEEPROM::flash.data()+offset,length);
  return true;
}
FakeEEPROM EEPROM;
struct EspStub {
  bool flashRead(uint32_t address,uint8_t* destination,size_t length){
    return fakeFlashRead(address,destination,length);
  }
  uint32_t random(){ return 0x12345678UL; }
} ESP;
struct SerialStub { void println(const char*){} } Serial;
struct LittleFSStub { bool marker=false; bool exists(const char*) const { return marker; } } LittleFS;
uint32_t millis(){ return 123456UL; }
size_t strlcpy(char* destination,const char* source,size_t capacity){
  const size_t length=strlen(source);
  if(capacity){
    const size_t copied=std::min(length,capacity-1);
    memcpy(destination,source,copied);
    destination[copied]='\0';
  }
  return length;
}

bool pollFaultBackupReady=false;
bool pollFaultBackupWriteFailed=false;
bool configImageReadVerified=false;
bool outputPolarityKnown=false;
bool runRelayActiveHigh=false;
bool runLedActiveHigh=false;
bool pinConfigSafe=false;
bool insertMode=false;
bool journalRecoveryRequired=false;
bool fsReady=true;
std::string activeTarget="target";
"""
    functions = source_functions(source, omit_failure_invalidation)
    main = r"""
std::array<uint8_t,32> seedPreexistingMarker(){
  FakeEEPROM::flash.assign(POLL_FAULT_EEPROM_BYTES,0xFF);
  PollFaultRecord record=makePollFaultRecord(17);
  memcpy(FakeEEPROM::flash.data()+POLL_FAULT_EEPROM_OFFSET,&record,sizeof(record));
  std::array<uint8_t,32> marker{};
  memcpy(marker.data(),FakeEEPROM::flash.data()+POLL_FAULT_EEPROM_OFFSET,marker.size());
  return marker;
}
bool markerUnchanged(const std::array<uint8_t,32>& marker){
  return FakeEEPROM::flash.size()>=POLL_FAULT_EEPROM_BYTES &&
         memcmp(marker.data(),FakeEEPROM::flash.data()+POLL_FAULT_EEPROM_OFFSET,marker.size())==0;
}
void resetRuntime(){
  cfg=Config{};
  pollFaultBackupReady=false;
  pollFaultBackupWriteFailed=false;
  configImageReadVerified=false;
  outputPolarityKnown=false;
  runRelayActiveHigh=false;
  runLedActiveHigh=false;
  pinConfigSafe=false;
  insertMode=true;
  journalRecoveryRequired=false;
  fsReady=true;
  activeTarget="target";
  LittleFS.marker=false;
}
void resetEepromObject(){
  EEPROM=FakeEEPROM();
  rawFlashReadCalls=0;
  flashWriteCount=0;
  fakeCommitFailure=false;
}
bool coldBootAndCheckMarker(){
  resetRuntime();
  resetEepromObject();
  rawReadFailFirstCount=0;
  rawReadPersistentFailure=false;
  loadCfg();
  loadPollPulseFaultLatch();
  return journalRecoveryRequired && !insertMode && activeTarget.empty();
}
bool rejectedConfigCannotBeSaved(const std::vector<uint8_t>& original,
                                 const std::array<uint8_t,32>& marker){
  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=0;
  rawReadPersistentFailure=false;
  loadCfg();
  if(configImageReadVerified || !journalRecoveryRequired || insertMode ||
     !activeTarget.empty() || flashWriteCount!=0 || FakeEEPROM::flash!=original)
    return false;
  // This is the same saveCfg() entrypoint used by the local setup AP route.
  if(saveCfg()) return false;
  if(flashWriteCount!=0 || FakeEEPROM::flash!=original || !markerUnchanged(marker))
    return false;
  if(!coldBootAndCheckMarker()) return false;
  return FakeEEPROM::flash==original && markerUnchanged(marker);
}
ConfigV1 makeValidV1(){
  ConfigV1 value{};
  value.magic=MAGIC_V1;
  strlcpy(value.ssid,"legacy-v1-ssid",sizeof(value.ssid));
  strlcpy(value.pass,"legacy-v1-pass",sizeof(value.pass));
  strlcpy(value.server,"192.0.2.10",sizeof(value.server));
  strlcpy(value.key,"legacy-v1-key",sizeof(value.key));
  strlcpy(value.id,"legacy-v1-id",sizeof(value.id));
  value.coinPin=4;
  value.insertLedPin=14;
  value.relayPin=5;
  value.coinActiveLow=1;
  return value;
}
ConfigV2 makeValidV2(){
  ConfigV2 value{};
  value.magic=MAGIC_V2;
  strlcpy(value.ssid,"legacy-v2-ssid",sizeof(value.ssid));
  strlcpy(value.pass,"legacy-v2-pass",sizeof(value.pass));
  strlcpy(value.server,"192.0.2.20",sizeof(value.server));
  strlcpy(value.key,"legacy-v2-key",sizeof(value.key));
  strlcpy(value.id,"legacy-v2-id",sizeof(value.id));
  strlcpy(value.apPass,"legacy-ap-pass",sizeof(value.apPass));
  value.coinPin=4;
  value.insertLedPin=14;
  value.relayPin=5;
  value.coinActiveLow=1;
  return value;
}
int main(){
  // RED target: EEPROM.begin's first 544-byte read fails, then a direct full
  // image read can recover. Default Config save must preserve the valid marker.
  auto marker=seedPreexistingMarker();
  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=1;
  rawReadPersistentFailure=false;
  loadCfg();
  if(!configImageReadVerified || cfg.magic!=MAGIC ||
     cfg.outputPolarityConfigured!=0 || flashWriteCount!=1 ||
     !markerUnchanged(marker)) return 31;
  if(!pollFaultBackupPresentOrCorrupt()) return 32;
  std::cout<<"ESP8266_EEPROM_BEGIN_READ_FAIL_THEN_FULL_READ_RECOVER_MARKER_PRESERVED_PASS\n";
  if(!coldBootAndCheckMarker()) return 33;
  if(!markerUnchanged(marker)) return 33;
  std::cout<<"ESP8266_EEPROM_RECOVERED_IMAGE_COLD_BOOT_DENY_PASS\n";

  // A second failed full-image read must not fall through to Config-erased
  // defaults. The later marker-only read may succeed, but no guessed image is
  // allowed to reach EEPROM.commit().
  marker=seedPreexistingMarker();
  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=2;
  rawReadPersistentFailure=false;
  loadCfg();
  if(configImageReadVerified || !journalRecoveryRequired || insertMode ||
     !activeTarget.empty() || flashWriteCount!=0 || !markerUnchanged(marker)) return 34;
  if(!coldBootAndCheckMarker()) return 35;
  if(!markerUnchanged(marker)) return 35;
  std::cout<<"ESP8266_EEPROM_FULL_READ_FAIL_MARKER_ONLY_RECOVERY_NO_COMMIT_PASS\n";

  // Persistent whole-image read failure remains deny-only and must not commit
  // defaults, an unverified Config buffer, or a secondary marker into that buffer.
  marker=seedPreexistingMarker();
  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=0;
  rawReadPersistentFailure=true;
  loadCfg();
  if(configImageReadVerified || !journalRecoveryRequired || insertMode ||
     !activeTarget.empty() || flashWriteCount!=0 || !markerUnchanged(marker)) return 36;
  defaults();
  if(saveCfg()) return 37;
  rawReadPersistentFailure=false; // the existing marker-only read is now available
  if(writePollFaultBackup(9) && flashWriteCount!=0) return 38;
  if(flashWriteCount!=0 || !markerUnchanged(marker)) return 39;
  if(!coldBootAndCheckMarker()) return 40;
  if(!markerUnchanged(marker)) return 40;
  std::cout<<"ESP8266_EEPROM_FULL_READ_PERSISTENT_FAILURE_NO_COMMIT_PASS\n";
  // Core 3.1.2 reuses an existing same-size allocation. When begin()'s
  // internal flashRead fails, stale RAM remains; the full-image status read
  // must fail closed rather than interpreting those bytes as configuration.
  marker=seedPreexistingMarker();
  resetEepromObject();
  EEPROM.begin(POLL_FAULT_EEPROM_BYTES);
  if(EEPROM.buffer.size()!=POLL_FAULT_EEPROM_BYTES) return 41;
  std::fill(EEPROM.buffer.begin(),EEPROM.buffer.end(),0xA5);
  resetRuntime();
  rawReadFailFirstCount=2; // failed begin() read, then failed full-image read
  rawReadPersistentFailure=false;
  loadCfg();
  if(!std::all_of(EEPROM.buffer.begin(),EEPROM.buffer.end(),
                  [](uint8_t value){ return value==0xA5; })) return 42;
  if(configImageReadVerified || !journalRecoveryRequired || insertMode ||
     !activeTarget.empty() || flashWriteCount!=0 || !markerUnchanged(marker)) return 43;
  if(!coldBootAndCheckMarker() || !markerUnchanged(marker)) return 44;
  std::cout<<"ESP8266_EEPROM_SAME_SIZE_STALE_BUFFER_READ_FAILURE_DENY_PASS\\n";
  // A malformed v1 record must remain byte-for-byte intact even if the
  // setup AP's saveCfg() entrypoint is called after the boot failure latch.
  auto rejectedMarker=seedPreexistingMarker();
  ConfigV1 malformedV1=makeValidV1();
  memset(malformedV1.ssid,'V',sizeof(malformedV1.ssid));
  memcpy(FakeEEPROM::flash.data(),&malformedV1,sizeof(malformedV1));
  auto rejectedImage=FakeEEPROM::flash;
  if(!rejectedConfigCannotBeSaved(rejectedImage,rejectedMarker)) return 45;
  std::cout<<"MALFORMED_V1_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS\\n";

  // v2's AP password and all fixed strings are bounded before migration.
  rejectedMarker=seedPreexistingMarker();
  ConfigV2 malformedV2=makeValidV2();
  memset(malformedV2.apPass,'P',sizeof(malformedV2.apPass));
  memcpy(FakeEEPROM::flash.data(),&malformedV2,sizeof(malformedV2));
  rejectedImage=FakeEEPROM::flash;
  if(!rejectedConfigCannotBeSaved(rejectedImage,rejectedMarker)) return 46;
  std::cout<<"MALFORMED_V2_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS\\n";

  // Unknown non-erased schemas are not defaults and cannot be overwritten by
  // a later local setup save in the same boot.
  rejectedMarker=seedPreexistingMarker();
  const uint32_t unknownMagic=0xDEADBEEFUL;
  memcpy(FakeEEPROM::flash.data(),&unknownMagic,sizeof(unknownMagic));
  rejectedImage=FakeEEPROM::flash;
  if(!rejectedConfigCannotBeSaved(rejectedImage,rejectedMarker)) return 47;
  std::cout<<"UNKNOWN_SCHEMA_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS\\n";

  // Valid local v1 migration is allowed only after a verified full-image read;
  // the reserved poll-fault record must survive the v3 commit and cold boot.
  auto migrationMarker=seedPreexistingMarker();
  ConfigV1 validV1=makeValidV1();
  memcpy(FakeEEPROM::flash.data(),&validV1,sizeof(validV1));
  auto preMigrationImage=FakeEEPROM::flash;
  resetEepromObject();
  resetRuntime();
  loadCfg();
  if(!configImageReadVerified || cfg.magic!=MAGIC ||
     strcmp(cfg.ssid,"legacy-v1-ssid")!=0 ||
     cfg.outputPolarityConfigured!=0 || outputPolarityKnown ||
     flashWriteCount!=1 || FakeEEPROM::flash==preMigrationImage ||
     !markerUnchanged(migrationMarker)) return 48;
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 49;
  if(!coldBootAndCheckMarker() || !markerUnchanged(migrationMarker)) return 50;
  std::cout<<"VALID_V1_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS\\n";

  // Valid local v2 migration has the same reserved-marker preservation rule.
  migrationMarker=seedPreexistingMarker();
  ConfigV2 validV2=makeValidV2();
  memcpy(FakeEEPROM::flash.data(),&validV2,sizeof(validV2));
  preMigrationImage=FakeEEPROM::flash;
  resetEepromObject();
  resetRuntime();
  loadCfg();
  if(!configImageReadVerified || cfg.magic!=MAGIC ||
     strcmp(cfg.ssid,"legacy-v2-ssid")!=0 ||
     strcmp(cfg.apPass,"legacy-ap-pass")!=0 ||
     cfg.outputPolarityConfigured!=0 || outputPolarityKnown ||
     flashWriteCount!=1 || FakeEEPROM::flash==preMigrationImage ||
     !markerUnchanged(migrationMarker)) return 51;
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty()) return 52;
  if(!coldBootAndCheckMarker() || !markerUnchanged(migrationMarker)) return 53;
  std::cout<<"VALID_V2_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS\\n";

  // A failed v2 migration commit must revoke write authority for this boot.
  // The next cold boot may retry the still-present legacy image from flash.
  migrationMarker=seedPreexistingMarker();
  validV2=makeValidV2();
  memcpy(FakeEEPROM::flash.data(),&validV2,sizeof(validV2));
  preMigrationImage=FakeEEPROM::flash;
  resetEepromObject();
  resetRuntime();
  fakeCommitFailure=true;
  loadCfg();
  if(configImageReadVerified || !journalRecoveryRequired ||
     flashWriteCount!=0 || FakeEEPROM::flash!=preMigrationImage) return 54;
  if(saveCfg()) return 55;
  if(flashWriteCount!=0 || FakeEEPROM::flash!=preMigrationImage ||
     !markerUnchanged(migrationMarker)) return 56;
  if(!coldBootAndCheckMarker() || !markerUnchanged(migrationMarker)) return 57;
  std::cout<<"V2_MIGRATION_COMMIT_FAILURE_SAME_BOOT_DENY_COLD_BOOT_RETRY_PASS\\n";
  std::cout<<"EEPROM_CORE_3_1_2_BUFFER_SEMANTICS=MODELED\\n";
  std::cout<<"LOCAL_CONFIG_MIGRATION_LAB_ONLY=1 FINANCIAL_MIGRATION_TESTED=0 PRODUCTION_MIGRATION_AUTHORIZED=0\n";
  std::cout<<"SIMULATED_ONLY=1 PHYSICAL_POWER_CUT_VERIFIED=0\n";
  return 0;
}
"""
    return "\n".join([
        prelude,
        structs,
        "Config cfg{};",
        constants,
        functions,
        main,
    ])

def main():
    source=SOURCE.read_text(encoding="utf-8")

    def compile_and_run(program: str, label: str, expect_success: bool) -> int:
        with tempfile.TemporaryDirectory(prefix="phx-eeprom-config-read-") as folder:
            cpp=Path(folder)/"config_read.cpp"
            exe=Path(folder)/"config_read"
            cpp.write_text(program,encoding="utf-8")
            built=subprocess.run(
                ["g++","-std=c++17","-Wall","-Wextra","-Werror",
                 "-Wno-unused-parameter",str(cpp),"-o",str(exe)],
                capture_output=True,text=True,timeout=30
            )
            if built.returncode:
                raise RuntimeError(label+" compile failed:\\n"+built.stderr[-5000:])
            ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
            if expect_success:
                if ran.returncode:
                    print(ran.stdout,end="")
                    print(ran.stderr,end="")
                    raise RuntimeError(label+" expected exit 0, got "+str(ran.returncode))
                print(ran.stdout,end="")
            else:
                if ran.returncode==0:
                    raise RuntimeError(label+" mutation unexpectedly survived")
                print("MUTATION_REJECTED missing-config-image-invalidation exit="+str(ran.returncode))
            return ran.returncode

    compile_and_run(harness(source), "ESP8266 config read/migration lab", True)
    # Prove the new malformed-record/setup-save assertions detect removal of
    # the production failure-latch write-authority revocation.
    compile_and_run(
        harness(source, omit_failure_invalidation=True),
        "ESP8266 missing-config-image-invalidation mutation",
        False,
    )

if __name__ == "__main__":
    main()
