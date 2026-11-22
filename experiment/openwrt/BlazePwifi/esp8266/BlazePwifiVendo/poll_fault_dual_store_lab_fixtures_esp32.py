"""ESP32 NVS backend and failure controls for the dual-store poll-fault lab."""

def backend():
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
        nvs_write_before_commit_assert = "if(nvsSetWasDurableBeforeCommit){ std::cerr<<\"ESP32_NVS_SET_BLOB_DURABLE_BEFORE_COMMIT\\n\"; return 60; } std::cout<<\"ESP32_NVS_SET_BLOB_NOT_DURABLE_BEFORE_COMMIT_PASS\\n\";"
        commit_fail_before_persistence_setup = "nvsFailCommit=true;"
        commit_fail_before_persistence_clear = "nvsFailCommit=false;"
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
