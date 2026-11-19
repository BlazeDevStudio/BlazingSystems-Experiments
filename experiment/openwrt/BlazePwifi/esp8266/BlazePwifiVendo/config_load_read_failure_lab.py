#!/usr/bin/env python3
"""Execute the real ESP8266 config loader against a fault-injected EEPROM model.

The model follows ESP8266 Arduino core 3.1.2 EEPROM.cpp: begin() allocates
indeterminate RAM for a new buffer, reuses a same-size buffer, and only logs
a failed flashRead without clearing or reporting it to the caller. The lab
uses deterministic poison bytes to model that untrusted RAM state.

Core source:
https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp

The lab covers full-image read failures for erased and valid non-erased v3
images, same-boot setup-save denial after malformed v1/v2 or unknown records,
successful local v1/v2-to-v3 migration with poll-fault marker preservation,
and failed migration commit followed by cold-boot recovery. These are
fake-flash host simulations, not physical power-cut acceptance or the
separate financial ledger migration.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_block, extract_functions

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"

def extract_constants(source: str, names):
    selected = []
    for line in source.splitlines():
        if line.lstrip().startswith(("static const ", "const ")) and any(name in line for name in names):
            selected.append(line)
    return "\n".join(selected)

def verify_eeprom_layout_guards(source: str) -> None:
    required = (
        ("Config must stay before the reserved poll-fault region",
         "static_assert(sizeof(Config)<=POLL_FAULT_EEPROM_OFFSET"),
        ("Poll-fault record must fit inside the reserved EEPROM image",
         "static_assert(POLL_FAULT_EEPROM_OFFSET+sizeof(PollFaultRecord)<=POLL_FAULT_EEPROM_BYTES"),
        ("Poll-fault record binary size must remain explicit",
         "static_assert(sizeof(PollFaultRecord)==20"),
        ("EEPROM reserved-region offset must have one definition",
         "static const size_t POLL_FAULT_EEPROM_OFFSET="),
        ("EEPROM image length must have one definition",
         "static const size_t POLL_FAULT_EEPROM_BYTES="),
    )
    for label, token in required:
        count = source.count(token)
        if count != 1:
            raise RuntimeError(f"{label}: expected exactly one source guard/definition, found {count}")
    print("ESP8266_EEPROM_LAYOUT_GUARDS_UNIQUE_PASS")


def verify_eeprom_layout_guard_mutations(source: str) -> None:
    guard_lines = [
        line for line in source.splitlines()
        if "static_assert(sizeof(Config)<=POLL_FAULT_EEPROM_OFFSET" in line
    ]
    if len(guard_lines) != 1:
        raise RuntimeError("cannot build duplicate/missing guard mutations from a non-canonical source")
    guard = guard_lines[0]
    duplicate = source.replace(guard, guard + "\n" + guard, 1)
    missing = source.replace(guard + "\n", "", 1)
    for label, mutated in (
        ("duplicate Config/EEPROM overlap assertion", duplicate),
        ("missing Config/EEPROM overlap assertion", missing),
    ):
        try:
            verify_eeprom_layout_guards(mutated)
        except RuntimeError:
            print("MUTATION_REJECTED " + label)
        else:
            raise RuntimeError("EEPROM layout guard mutation survived: " + label)


def source_functions(source: str, omit_failure_invalidation: bool = False,
                     omit_full_image_read_guard: bool = False) -> str:
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
        for index, item in enumerate(found):
            function = item[1]
            if (name == "latchConfigPersistenceFailure" and
                    index == 0 and omit_failure_invalidation):
                anchor = "  configImageReadVerified=false;"
                if anchor not in function:
                    raise RuntimeError("mutation anchor missing from failure latch")
                function = function.replace(
                    anchor,
                    "  // injected mutation: verified-image authority was not revoked",
                    1,
                )
            if (name == "loadCfg" and index == 0 and omit_full_image_read_guard):
                anchor = """  if(!refreshVerifiedEepromImage()){
    latchConfigPersistenceFailure("CRITICAL: full EEPROM image read/restore failed; preserve configuration and poll-fault bytes; outputs disabled.");
    return;
  }"""
                if anchor not in function:
                    raise RuntimeError("mutation anchor missing from loadCfg full-image guard")
                function = function.replace(
                    anchor,
                    "  // injected mutation: skip status-bearing full-image verification",
                    1,
                )
            pieces.append(function)
    return "\n\n".join(pieces)

def harness(source: str, omit_failure_invalidation: bool = False,
            omit_full_image_read_guard: bool = False,
            valid_v3_only: bool = False) -> str:
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
static bool runValidV3Only=false;

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
    functions = source_functions(source, omit_failure_invalidation,
                                 omit_full_image_read_guard)
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
Config makeValidV3(){
  Config value{};
  value.magic=MAGIC;
  strlcpy(value.ssid,"verified-v3-ssid",sizeof(value.ssid));
  strlcpy(value.pass,"verified-v3-pass",sizeof(value.pass));
  strlcpy(value.server,"192.0.2.44",sizeof(value.server));
  strlcpy(value.key,"verified-v3-key",sizeof(value.key));
  strlcpy(value.id,"verified-v3-id",sizeof(value.id));
  strlcpy(value.apPass,"verified-setup-pass",sizeof(value.apPass));
  value.coinPin=4;
  value.insertLedPin=14;
  value.relayPin=5;
  value.coinActiveLow=1;
  value.relayActiveHigh=0;
  value.ledActiveHigh=1;
  value.outputPolarityConfigured=1;
  value.checksum=configChecksum(value);
  return value;
}
bool runValidV3ImageReadFailureScenario(){
  const auto marker=seedPreexistingMarker();
  const Config validV3=makeValidV3();
  memcpy(FakeEEPROM::flash.data(),&validV3,sizeof(validV3));
  const auto original=FakeEEPROM::flash;

  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=2; // EEPROM.begin() read and full-image read both fail.
  rawReadPersistentFailure=false;
  loadCfg();
  Config emptyConfig{};
  if(configImageReadVerified || memcmp(&cfg,&emptyConfig,sizeof(Config))!=0 ||
     !journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     flashWriteCount!=0 || FakeEEPROM::flash!=original ||
     !markerUnchanged(marker)) return false;
  // The setup-AP save entrypoint must remain blocked after the read failure.
  if(saveCfg()) return false;
  if(flashWriteCount!=0 || FakeEEPROM::flash!=original ||
     !markerUnchanged(marker)) return false;

  // A later cold boot with readable flash must recover the original v3 image,
  // not defaults, while the pre-existing fault marker still denies outputs.
  resetEepromObject();
  resetRuntime();
  rawReadFailFirstCount=0;
  rawReadPersistentFailure=false;
  loadCfg();
  if(!configImageReadVerified || cfg.magic!=MAGIC ||
     strcmp(cfg.ssid,"verified-v3-ssid")!=0 || !outputPolarityKnown ||
     flashWriteCount!=0) return false;
  loadPollPulseFaultLatch();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !markerUnchanged(marker) || FakeEEPROM::flash!=original) return false;
  return true;
}
int main(){
  if(!runValidV3ImageReadFailureScenario()) return 58;
  std::cout<<"VALID_V3_IMAGE_READ_FAILURE_PRESERVE_COLD_BOOT_PASS\n";
  if(runValidV3Only) return 0;
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
    program = "\n".join([
        prelude,
        structs,
        "Config cfg{};",
        constants,
        functions,
        main,
    ])
    if valid_v3_only:
        anchor = "static bool runValidV3Only=false;"
        if anchor not in program:
            raise RuntimeError("valid-v3-only selector anchor missing")
        program = program.replace(anchor, "static bool runValidV3Only=true;", 1)
    return program

def main():
    source=SOURCE.read_text(encoding="utf-8")
    verify_eeprom_layout_guards(source)
    verify_eeprom_layout_guard_mutations(source)

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
                print("MUTATION_REJECTED "+label+" exit="+str(ran.returncode))
            return ran.returncode

    # Test-first RED: bypass the production full-image read guard. A valid,
    # non-erased v3 image must not be mistaken for defaults when both reads fail.
    compile_and_run(
        harness(source, omit_full_image_read_guard=True, valid_v3_only=True),
        "ESP8266 missing full-image guard mutation",
        False,
    )
    compile_and_run(harness(source), "ESP8266 config read/migration lab", True)
    # Prove the malformed-record/setup-save assertions detect removal of the
    # production failure-latch write-authority revocation.
    compile_and_run(
        harness(source, omit_failure_invalidation=True),
        "ESP8266 missing-config-image-invalidation mutation",
        False,
    )

if __name__ == "__main__":
    main()
