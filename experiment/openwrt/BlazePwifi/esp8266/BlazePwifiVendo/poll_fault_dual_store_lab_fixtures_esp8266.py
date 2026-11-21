"""ESP8266 EEPROM/flash backend and failure controls for the dual-store poll-fault lab."""

def backend():
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
        nvs_write_before_commit_assert = ""
        commit_fail_before_persistence_setup = "EEPROM.failCommit=true;"
        commit_fail_before_persistence_clear = "EEPROM.failCommit=false;"
        return {
            "backend": backend,
            "fail_write": fail_write,
            "fail_read": fail_read,
            "ambiguous_commit_setup": ambiguous_commit_setup,
            "clear_fail": clear_fail,
            "no_marker": no_marker,
            "nvs_read_error": nvs_read_error,
            "nvs_write_before_commit_assert": nvs_write_before_commit_assert,
            "commit_fail_before_persistence_setup": commit_fail_before_persistence_setup,
            "commit_fail_before_persistence_clear": commit_fail_before_persistence_clear,
        }
