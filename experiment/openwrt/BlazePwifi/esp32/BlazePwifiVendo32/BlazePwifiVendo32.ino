#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <nvs.h>
#include <LittleFS.h>
#include <string.h>
#include <stdlib.h>
#include <mbedtls/version.h>
#if MBEDTLS_VERSION_MAJOR == 4
#include <psa/crypto.h>
#elif MBEDTLS_VERSION_MAJOR == 3
#include <mbedtls/sha256.h>
#else
#error "Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only"
#endif
#include <esp_system.h>

struct Config {
  String ssid, pass, server, key, id, apPass;
  int coinPin=27, insertLedPin=2, relayPin=26;
  // Relay/LED polarity has no trusted default. Only the local setup AP may
  // establish it after Preferences commit/readback.
  bool coinActiveLow=true, relayActiveHigh=false, ledActiveHigh=false;
  uint16_t coinDebounceMs=40, pulseGroupMs=400;
};

struct PendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};

struct PollFaultRecord {
  uint32_t magic;
  uint16_t version;
  uint16_t size;
  uint32_t pulseEdges;
  uint32_t bootMillis;
  uint32_t checksum;
};
static const uint32_t POLL_FAULT_RECORD_MAGIC=0x50484631;
static const uint16_t POLL_FAULT_RECORD_VERSION=1;
static_assert(sizeof(PollFaultRecord)==20,"PollFaultRecord layout changed; review persistent format");

volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;

// The ISR only counts the configured active edge. No String, filesystem,
// network or logging calls are permitted from interrupt context.
#if defined(ESP8266)
void ICACHE_RAM_ATTR coinEdgeISR(){ coinEdgeSequence++; }
#else
void IRAM_ATTR coinEdgeISR(){ coinEdgeSequence++; }
#endif
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }

// Master Architecture Contracts §2.1: never accept a debounce below 20 ms.
// Apply the same bound to persisted, local-setup, and controller-provided values.
uint16_t boundedCoinDebounceMs(long long requested){
  if(requested<20LL) return 20;
  if(requested>2000LL) return 2000;
  return (uint16_t)requested;
}


static const uint32_t PENDING_MAGIC=0x42504332;
Config cfg;
Preferences prefs;
bool outputPolarityKnown=false;
nvs_handle_t pollFaultNvsHandle=0;
bool pollFaultBackupReady=false;
// A failed commit is ambiguous until a cold boot reads the flash-backed store.
// Do not count a same-boot NVS cache entry as a durable deny marker.
bool pollFaultBackupWriteFailed=false;
WebServer web(80);
bool insertMode=false, lastCoin=false, pendingReady=false, fsReady=false, journalRecoveryRequired=false, pendingPostAttempted=false;
bool pollIntakeSuspended=false, pollDrainAbortedOnActiveLine=false, pinConfigSafe=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=false, runLedActiveHigh=false;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
int runCoinPin=27, runLedPin=2, runRelayPin=26, maxWifiRetries=6, wifiFailures=0, remoteRevision=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;

String activeTarget, pendingTarget, pendingNonce, setupApName;

String hexDigest(const String &s){
  unsigned char out[32]; char buf[65];
#if MBEDTLS_VERSION_MAJOR == 4
  // Mbed TLS 4 removes the legacy SHA module API; keep the same SHA-256
  // digest bytes through the supported PSA one-shot hash interface.
  if(psa_crypto_init()!=PSA_SUCCESS) return String();
  size_t digestLength=0;
  psa_status_t status=psa_hash_compute(
    PSA_ALG_SHA_256,
    (const uint8_t*)s.c_str(),
    s.length(),
    out,
    sizeof(out),
    &digestLength
  );
  if(status!=PSA_SUCCESS || digestLength!=sizeof(out)) return String();
#elif MBEDTLS_VERSION_MAJOR == 3
  mbedtls_sha256_context c;
  mbedtls_sha256_init(&c);
  int status=mbedtls_sha256_starts(&c,0);
  if(status==0) status=mbedtls_sha256_update(&c,(const unsigned char*)s.c_str(),s.length());
  if(status==0) status=mbedtls_sha256_finish(&c,out);
  mbedtls_sha256_free(&c);
  if(status!=0) return String();
#endif
  for(int i=0;i<32;i++) sprintf(buf+i*2,"%02x",out[i]);
  buf[64]=0; return String(buf);
}

String freshNonce(){
  char b[17];
  snprintf(b,sizeof(b),"%08lx%08lx",(unsigned long)esp_random(),(unsigned long)esp_random());
  return String(b);
}

String esc(const String &s){
  String o;
  for(size_t i=0;i<s.length();i++){
    char c=s[i];
    if(isalnum((unsigned char)c)||c=='-'||c=='_'||c=='.') o+=c;
    else { char b[4]; snprintf(b,sizeof(b),"%%%02X",(unsigned char)c); o+=b; }
  }
  return o;
}

String htmlEsc(const String &s){
  String o;
  for(size_t i=0;i<s.length();i++){
    char c=s[i];
    if(c=='&') o+="&amp;";
    else if(c=='\'') o+="&#39;";
    else if(c=='\"') o+="&quot;";
    else if(c=='<') o+="&lt;";
    else if(c=='>') o+="&gt;";
    else o+=c;
  }
  return o;
}

uint32_t pendingChecksum(const PendingRecord &r){
  const uint8_t *p=(const uint8_t*)&r; uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(PendingRecord,checksum);i++){ h^=p[i]; h*=16777619UL; }
  return h;
}

bool readPendingFile(const char *path, PendingRecord &r){
  if(!fsReady || !LittleFS.exists(path)) return false;
  File f=LittleFS.open(path,"r"); if(!f) return false;
  const size_t storedSize=f.size();
  size_t n=f.readBytes((char*)&r,sizeof(r)); f.close();
  if(storedSize!=sizeof(r) || n!=sizeof(r) || r.magic!=PENDING_MAGIC ||
     r.pulses==0 || r.pulses>20 ||
     r.checksum!=pendingChecksum(r)) return false;
  // A corrupt record may not terminate either fixed-size string. Never use strlen here.
  const char *nonceEnd=(const char*)memchr(r.nonce,'\0',sizeof(r.nonce));
  const char *targetEnd=(const char*)memchr(r.target,'\0',sizeof(r.target));
  if(!nonceEnd || !targetEnd) return false;
  const size_t nonceLength=(size_t)(nonceEnd-r.nonce);
  const size_t targetLength=(size_t)(targetEnd-r.target);
  if(nonceLength<8 || targetLength<8) return false;
  // Writers zero-fill both arrays. Reject hidden suffix bytes that would be
  // discarded by String(char*) and collapse distinct disk records to one identity.
  for(size_t i=nonceLength+1;i<sizeof(r.nonce);++i) if(r.nonce[i]!='\0') return false;
  for(size_t i=targetLength+1;i<sizeof(r.target);++i) if(r.target[i]!='\0') return false;
  return true;
}

bool samePendingRecord(const PendingRecord &left,const PendingRecord &right){
  return left.magic==right.magic && left.pulses==right.pulses &&
         strcmp(left.nonce,right.nonce)==0 &&
         strcmp(left.target,right.target)==0 &&
         left.checksum==right.checksum;
}

bool removePendingCandidate(const char *path){
  if(!LittleFS.exists(path)) return true;
  return LittleFS.remove(path) && !LittleFS.exists(path);
}

bool savePending(){
  if(!fsReady || journalRecoveryRequired || pendingPostAttempted || pendingPulses==0 || pendingPulses>20 ||
     pendingNonce.length()<8 || pendingTarget.length()<8) return false;
  PendingRecord r{}; r.magic=PENDING_MAGIC; r.pulses=pendingPulses;
  const size_t nonceLength=strlcpy(r.nonce,pendingNonce.c_str(),sizeof(r.nonce));
  const size_t targetLength=strlcpy(r.target,pendingTarget.c_str(),sizeof(r.target));
  if(nonceLength>=sizeof(r.nonce) || targetLength>=sizeof(r.target)) return false;
  r.checksum=pendingChecksum(r);
  File f=LittleFS.open("/pending.new","w"); if(!f) return false;
  size_t n=f.write((const uint8_t*)&r,sizeof(r)); f.flush(); f.close();
  if(n!=sizeof(r)){
    if(!removePendingCandidate("/pending.new")) journalRecoveryRequired=true;
    return false;
  }
  PendingRecord verify{};
  if(!readPendingFile("/pending.new",verify) || memcmp(&r,&verify,sizeof(r))!=0){
    if(!removePendingCandidate("/pending.new")) journalRecoveryRequired=true;
    return false;
  }
  if(!removePendingCandidate("/pending.bak")){
    journalRecoveryRequired=true;
    return false;
  }
  const bool hadPrimary=LittleFS.exists("/pending.dat");
  if(hadPrimary &&
     (!LittleFS.rename("/pending.dat","/pending.bak") ||
      LittleFS.exists("/pending.dat") || !LittleFS.exists("/pending.bak"))){
    // pending.new was already read back successfully. A failed or ambiguous
    // rotation must preserve both versions for operator reconciliation.
    journalRecoveryRequired=true;
    return false;
  }
  if(!LittleFS.rename("/pending.new","/pending.dat") ||
     LittleFS.exists("/pending.new") || !LittleFS.exists("/pending.dat")){
    // Do not roll back by deleting the verified updated candidate. Preserve
    // every durable version and require reconciliation after any ambiguity.
    journalRecoveryRequired=true;
    return false;
  }
  if(hadPrimary && !removePendingCandidate("/pending.bak")){
    journalRecoveryRequired=true;
    return false;
  }
  return true;
}

bool markPendingPostAttempt(){
  if(!fsReady || journalRecoveryRequired || !pendingReady ||
     pendingPulses==0 || pendingPulses>20 || pendingPostAttempted) return false;
  if(LittleFS.exists("/pending.attempt")){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: prior coin POST attempt marker exists; reconciliation required.");
    return false;
  }

  PendingRecord record{};
  record.magic=PENDING_MAGIC;
  record.pulses=pendingPulses;
  const size_t nonceLength=pendingNonce.length();
  const size_t targetLength=pendingTarget.length();
  if(nonceLength<8 || nonceLength>=sizeof(record.nonce) ||
     targetLength<8 || targetLength>=sizeof(record.target)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: pending identity cannot be represented in attempt marker.");
    return false;
  }
  memcpy(record.nonce,pendingNonce.c_str(),nonceLength);
  memcpy(record.target,pendingTarget.c_str(),targetLength);
  record.checksum=pendingChecksum(record);

  const char *pendingPaths[]={"/pending.dat","/pending.new","/pending.bak"};
  unsigned candidateCount=0;
  const char *candidatePath=nullptr;
  for(size_t i=0;i<sizeof(pendingPaths)/sizeof(pendingPaths[0]);++i){
    if(LittleFS.exists(pendingPaths[i])){
      ++candidateCount;
      candidatePath=pendingPaths[i];
    }
  }
  // Never dispatch against one matching record while another candidate could
  // represent a different unpaid coin or an ambiguous interrupted rotation.
  if(candidateCount!=1 || !candidatePath){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: exactly one durable pending journal is required before coin POST; coin POST denied.");
    return false;
  }
  PendingRecord durable{};
  if(!readPendingFile(candidatePath,durable) ||
     !samePendingRecord(record,durable)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: durable pending journal does not match the coin POST attempt; coin POST denied.");
    return false;
  }

  File marker=LittleFS.open("/pending.attempt","w");
  if(!marker){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: cannot persist coin POST attempt marker; network dispatch denied.");
    return false;
  }
  const size_t written=marker.write((const uint8_t*)&record,sizeof(record));
  marker.flush();
  marker.close();
  PendingRecord verify{};
  if(written!=sizeof(record) ||
     !readPendingFile("/pending.attempt",verify) ||
     !samePendingRecord(record,verify)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: coin POST attempt marker readback failed; network dispatch denied.");
    return false;
  }
  pendingPostAttempted=true;
  return true;
}

bool pendingAttemptMarkerMatches(){
  if(!fsReady || journalRecoveryRequired || !pendingReady ||
     !pendingPostAttempted || pendingPulses==0 || pendingPulses>20 ||
     pendingNonce.length()<8 || pendingNonce.length()>=17 ||
     pendingTarget.length()<8 || pendingTarget.length()>=33) return false;
  PendingRecord attempt{};
  if(!readPendingFile("/pending.attempt",attempt)) return false;
  return attempt.pulses==pendingPulses &&
         strcmp(attempt.nonce,pendingNonce.c_str())==0 &&
         strcmp(attempt.target,pendingTarget.c_str())==0;
}

void loadPending(){
  if(!fsReady) return;
  pendingPostAttempted=false;
  const bool hasAttempt=LittleFS.exists("/pending.attempt");
  const bool hasDat=LittleFS.exists("/pending.dat");
  const bool hasNew=LittleFS.exists("/pending.new");
  const bool hasBak=LittleFS.exists("/pending.bak");
  const unsigned journalCount=(unsigned)hasDat+(unsigned)hasNew+(unsigned)hasBak;
  if(!journalCount){
    if(hasAttempt){
      journalRecoveryRequired=true;
      Serial.println("CRITICAL: orphan coin POST attempt marker; operator reconciliation required.");
    }
    return;
  }
  // Multiple candidates can represent DIFFERENT unpaid coins after a power cut.
  // Never choose one and delete another without a durable receipt/ACK contract.
  if(journalCount!=1){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: multiple pending journals; preserving all evidence, coin intake disabled.");
    return;
  }
  const char *chosen=hasDat?"/pending.dat":(hasNew?"/pending.new":"/pending.bak");
  PendingRecord r{};
  if(!readPendingFile(chosen,r)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: corrupt/unreadable pending journal; preserving evidence, coin intake disabled.");
    return;
  }
  pendingPulses=r.pulses;
  pendingNonce=String(r.nonce);
  pendingTarget=String(r.target);
  pendingReady=true;
  lastSend=0;
  if(hasAttempt){
    PendingRecord attempt{};
    if(!readPendingFile("/pending.attempt",attempt) ||
       !samePendingRecord(r,attempt)){
      journalRecoveryRequired=true;
      Serial.println("CRITICAL: coin POST attempt marker is corrupt or mismatched; preserving evidence.");
    } else {
      pendingPostAttempted=true;
      journalRecoveryRequired=true;
      Serial.println("CRITICAL: coin POST may have reached the server; automatic replay is denied.");
    }
  }
  // Do not rename or delete evidence at boot. Clear only after an authorized,
  // durable receipt/quarantine disposition and successful marker reclamation.
  Serial.println("Recovered unacknowledged coin event from flash.");
}


uint32_t pollFaultRecordChecksum(const PollFaultRecord &record){
  const uint8_t *bytes=(const uint8_t*)&record;
  uint32_t hash=2166136261UL;
  for(size_t i=0;i<sizeof(PollFaultRecord)-sizeof(record.checksum);++i){
    hash^=bytes[i];
    hash*=16777619UL;
  }
  return hash;
}

PollFaultRecord makePollFaultRecord(uint32_t pulseEdges){
  PollFaultRecord record{};
  record.magic=POLL_FAULT_RECORD_MAGIC;
  record.version=POLL_FAULT_RECORD_VERSION;
  record.size=(uint16_t)sizeof(record);
  record.pulseEdges=pulseEdges;
  record.bootMillis=millis();
  record.checksum=pollFaultRecordChecksum(record);
  return record;
}

bool validPollFaultRecord(const PollFaultRecord &record){
  return record.magic==POLL_FAULT_RECORD_MAGIC &&
         record.version==POLL_FAULT_RECORD_VERSION &&
         record.size==sizeof(PollFaultRecord) &&
         record.checksum==pollFaultRecordChecksum(record);
}


bool pollFaultBackupPresentOrCorrupt(){
  // Only a genuine missing-key result is clean. Type mismatch, corruption,
  // and every other NVS read error remain a permanent deny state.
  if(!pollFaultBackupReady) return true;
  size_t storedLength=0;
  const esp_err_t result=nvs_get_blob(pollFaultNvsHandle,"poll_fault",nullptr,&storedLength);
  return result!=ESP_ERR_NVS_NOT_FOUND;
}

bool writePollFaultBackup(uint32_t pulseEdges){
  if(!pollFaultBackupReady || pollFaultBackupWriteFailed) return false;
  size_t existingLength=0;
  const esp_err_t existing=nvs_get_blob(pollFaultNvsHandle,"poll_fault",nullptr,&existingLength);
  if(existing==ESP_OK) return true; // Any existing value, including malformed data, keeps the deny latch.
  if(existing!=ESP_ERR_NVS_NOT_FOUND){
    pollFaultBackupWriteFailed=true;
    return false;
  }

  const PollFaultRecord record=makePollFaultRecord(pulseEdges);
  if(nvs_set_blob(pollFaultNvsHandle,"poll_fault",&record,sizeof(record))!=ESP_OK){
    pollFaultBackupWriteFailed=true;
    return false;
  }
  if(nvs_commit(pollFaultNvsHandle)!=ESP_OK){
    pollFaultBackupWriteFailed=true;
    return false;
  }

  PollFaultRecord verify{};
  size_t readLength=sizeof(verify);
  const esp_err_t read=nvs_get_blob(pollFaultNvsHandle,"poll_fault",&verify,&readLength);
  const bool verified=read==ESP_OK && readLength==sizeof(verify) &&
                      validPollFaultRecord(verify) && memcmp(&record,&verify,sizeof(record))==0;
  if(!verified) pollFaultBackupWriteFailed=true;
  return verified;
}

void initPollFaultBackupStore(){
  // NVS is a separate flash partition from LittleFS, not an independent physical witness.
  pollFaultNvsHandle=0;
  pollFaultBackupReady=nvs_open("phx_fault",NVS_READWRITE,&pollFaultNvsHandle)==ESP_OK;
  if(!pollFaultBackupReady){
    pollFaultNvsHandle=0;
    journalRecoveryRequired=true;
    insertMode=false;
    activeTarget="";
    Serial.println("CRITICAL: NVS fault-backup store unavailable; coin admission remains denied.");
  }
}

// Legacy /pollpulse.fault path is retained so older firmware keeps denying on any existing marker.
bool writePollPulseFaultMarker(uint32_t pulseEdges){
  if(!fsReady) return false;
  if(LittleFS.exists("/pollpulse.fault")) return true;
  char record[96];
  int length=snprintf(record,sizeof(record),
      "COIN_INGRESS_UNRESOLVED pulses=%lu millis=%lu\n",
      (unsigned long)pulseEdges,(unsigned long)millis());
  if(length<=0 || (size_t)length>=sizeof(record)) return false;
  File marker=LittleFS.open("/pollpulse.fault","w");
  if(!marker) return false;
  size_t written=marker.write((const uint8_t*)record,(size_t)length);
  marker.flush();
  marker.close();
  if(written!=(size_t)length) return false;
  File verify=LittleFS.open("/pollpulse.fault","r");
  if(!verify) return false;
  bool matches=verify.size()==(size_t)length;
  for(size_t i=0;matches && i<(size_t)length;++i){
    if(verify.read()!=(unsigned char)record[i]) matches=false;
  }
  verify.close();
  return matches;
}

void loadPollPulseFaultLatch(){
  // Either persistent domain is enough to keep the device denied; never auto-clear either.
  const bool backupHold=pollFaultBackupPresentOrCorrupt();
  const bool littleFsHold=fsReady && LittleFS.exists("/pollpulse.fault");
  if(backupHold || littleFsHold){
    journalRecoveryRequired=true;
    insertMode=false;
    activeTarget="";
    Serial.println("CRITICAL: persistent coin-ingress fault found; preserve evidence and reconcile offline before enabling intake.");
  }
}

void initPendingStore(){
  fsReady=LittleFS.begin(false);
  if(!fsReady){
    journalRecoveryRequired=true;
    insertMode=false;
    activeTarget="";
    loadPollPulseFaultLatch();
    Serial.println("CRITICAL: LittleFS mount failed; preserving journal for recovery. Coin intake disabled.");
    return;
  }
  loadPending();
  loadPollPulseFaultLatch();
}


bool pendingAttemptMarkerMatches();

bool clearPending(){
  if(journalRecoveryRequired) return false;
  if(!fsReady){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: cannot clear pending journal while LittleFS is unavailable.");
    return false;
  }
  if(!pendingAttemptMarkerMatches()){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: cannot clear pending journal without a matching durable attempt marker.");
    return false;
  }
  PendingRecord attempt{};
  if(!readPendingFile("/pending.attempt",attempt) ||
     attempt.pulses!=pendingPulses ||
     strcmp(attempt.nonce,pendingNonce.c_str())!=0 ||
     strcmp(attempt.target,pendingTarget.c_str())!=0){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: attempt marker changed or no longer matches the pending event.");
    return false;
  }

  const char *paths[]={"/pending.dat","/pending.new","/pending.bak"};
  unsigned candidateCount=0;
  const char *candidatePath=nullptr;
  for(size_t i=0;i<sizeof(paths)/sizeof(paths[0]);++i){
    if(LittleFS.exists(paths[i])){
      ++candidateCount;
      candidatePath=paths[i];
    }
  }
  if(candidateCount!=1 || !candidatePath){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: exactly one durable pending journal is required; preserving all evidence.");
    return false;
  }
  PendingRecord durable{};
  if(!readPendingFile(candidatePath,durable) ||
     !samePendingRecord(attempt,durable)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: pending journal does not match the attempt marker; preserving all evidence.");
    return false;
  }
  if(!LittleFS.remove(candidatePath) || LittleFS.exists(candidatePath)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: pending journal deletion failed; preserving attempt marker and RAM event.");
    return false;
  }
  // Remove the attempt marker LAST. A power cut after pending deletion but
  // before marker deletion leaves an orphan marker that blocks boot admission.
  if(!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt")){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: pending event cleared but attempt marker remains; operator reconciliation required.");
    return false;
  }
  pendingPulses=0;
  pendingReady=false;
  pendingPostAttempted=false;
  pendingNonce="";
  pendingTarget="";
  lastSend=0;
  return true;
}

static const size_t QUARANTINE_MAX_BYTES=32768;

String quarantineLogField(const String &value,size_t maxLen){
  String out;
  out.reserve(maxLen);
  size_t i=0;
  for(;i<value.length();++i){
    const unsigned char c=(unsigned char)value[i];
    const char *escaped=nullptr;
    if(c=='\\') escaped="\\\\";
    else if(c=='\r') escaped="\\r";
    else if(c=='\n') escaped="\\n";
    else if(c=='\t') escaped="\\t";
    else if(c==' ' && i+8<=value.length() &&
            ((value[i+1]=='R' && value[i+2]=='E' && value[i+3]=='A' &&
              value[i+4]=='S' && value[i+5]=='O' && value[i+6]=='N' && value[i+7]=='=') ||
             (value[i+1]=='T' && value[i+2]=='A' && value[i+3]=='R' &&
              value[i+4]=='G' && value[i+5]=='E' && value[i+6]=='T' && value[i+7]=='=')))
      escaped="\\x20";
    if(escaped){
      const size_t escapedLength=strlen(escaped);
      if(out.length()+escapedLength>maxLen) break;
      out+=escaped;
    } else {
      if(out.length()+1>maxLen) break;
      out+=(c<0x20 || c==0x7f)?'?':(char)c;
    }
  }
  if(i<value.length() && maxLen>=3){
    while(out.length()+3>maxLen) out.remove(out.length()-1);
    out+="...";
  }
  return out;
}

bool quarantineLogTokenValid(const String &value,size_t minLength,size_t maxLength){
  const size_t length=value.length();
  if(length<minLength || length>maxLength) return false;
  for(size_t i=0;i<length;++i){
    const unsigned char c=(unsigned char)value[i];
    if(c<=0x20 || c==0x7f) return false;
  }
  return true;
}

bool quarantineLogRecordValid(const char *line,const char *identity,bool &sameIdentity){
  sameIdentity=false;
  if(!line) return false;

  const char *cursor=line;
  if(strncmp(cursor,"TIME=",5)!=0) return false;
  cursor+=5;
  const char *timeEnd=strchr(cursor,' ');
  if(!timeEnd || timeEnd==cursor) return false;
  const size_t timeLength=(size_t)(timeEnd-cursor);
  if(timeLength>10 || (timeLength>1 && cursor[0]=='0')) return false;
  unsigned long parsedTimestamp=0;
  for(const char *digit=cursor;digit<timeEnd;++digit){
    if(*digit<'0' || *digit>'9') return false;
    const unsigned long value=(unsigned long)(*digit-'0');
    if(parsedTimestamp>(0xFFFFFFFFUL-value)/10UL) return false;
    parsedTimestamp=parsedTimestamp*10UL+value;
  }
  (void)parsedTimestamp;

  cursor=timeEnd+1;
  if(strncmp(cursor,"PULSES=",7)!=0) return false;
  cursor+=7;
  const char *pulsesEnd=strchr(cursor,' ');
  if(!pulsesEnd || pulsesEnd==cursor) return false;
  const size_t pulseLength=(size_t)(pulsesEnd-cursor);
  if(pulseLength>2 || (pulseLength>1 && cursor[0]=='0')) return false;
  unsigned int pulses=0;
  for(const char *digit=cursor;digit<pulsesEnd;++digit){
    if(*digit<'0' || *digit>'9') return false;
    pulses=pulses*10U+(unsigned int)(*digit-'0');
  }
  if(pulses==0 || pulses>20) return false;

  cursor=pulsesEnd+1;
  if(strncmp(cursor,"NONCE=",6)!=0) return false;
  cursor+=6;
  const char *targetField=strstr(cursor," TARGET=");
  if(!targetField || targetField==cursor) return false;
  const size_t nonceLength=(size_t)(targetField-cursor);
  if(nonceLength<8 || nonceLength>=17) return false;
  for(const char *p=cursor;p<targetField;++p){
    const unsigned char c=(unsigned char)*p;
    if(c<=0x20 || c==0x7f) return false;
  }

  cursor=targetField+8;
  const char *reasonField=strstr(cursor," REASON=");
  if(!reasonField || reasonField==cursor) return false;
  const size_t targetLength=(size_t)(reasonField-cursor);
  if(targetLength<8 || targetLength>=33) return false;
  for(const char *p=cursor;p<reasonField;++p){
    const unsigned char c=(unsigned char)*p;
    if(c<=0x20 || c==0x7f) return false;
  }

  cursor=reasonField+8;
  if(*cursor=='\0' || strstr(cursor," REASON=")) return false;
  const size_t reasonLength=strlen(cursor);
  if(reasonLength>128) return false;
  for(const char *p=cursor;*p;++p){
    const unsigned char c=(unsigned char)*p;
    if(c<0x20 || c==0x7f) return false;
  }

  if(identity){
    const size_t identityLength=strlen(identity);
    sameIdentity=strncmp(timeEnd+1,identity,identityLength)==0;
  }
  return true;
}

uint32_t quarantineLogCrc32Update(uint32_t crc,uint8_t byte){
  crc^=(uint32_t)byte;
  for(uint8_t bit=0;bit<8;++bit){
    crc=(crc&1U)?((crc>>1)^0xEDB88320UL):(crc>>1);
  }
  return crc;
}

bool inspectQuarantineLog(const char *identity,size_t &bytes,bool &alreadyRecorded,uint32_t &prefixCrc32){
  bytes=0; alreadyRecorded=false; prefixCrc32=0;
  if(!LittleFS.exists("/quarantine.log")) return true;
  File prior=LittleFS.open("/quarantine.log","r");
  if(!prior) return false;
  bytes=prior.size();
  char line[320];
  size_t lineLength=0,readCount=0;
  uint32_t prefixCrc=0xFFFFFFFFUL;
  bool valid=true;
  while(valid && prior.available()){
    int next=prior.read();
    if(next<0){ valid=false; break; }
    ++readCount;
    prefixCrc=quarantineLogCrc32Update(prefixCrc,(uint8_t)next);
    if(next=='\n'){
      if(lineLength==0){ valid=false; break; }
      line[lineLength]='\0';
      bool sameIdentity=false;
      if(!quarantineLogRecordValid(line,identity,sameIdentity)){
        valid=false;
        break;
      }
      if(sameIdentity){
        // More than one complete record for one event is conflicting accounting
        // evidence. Preserve pending state until an operator reconciles the log.
        if(alreadyRecorded){ valid=false; break; }
        alreadyRecorded=true;
      }
      lineLength=0;
    } else if(next=='\0' || lineLength+1>=sizeof(line)){
      valid=false;
    } else {
      line[lineLength++]=(char)next;
    }
  }
  prior.close();
  // Every generated record has exactly one final newline. An unterminated tail
  // is durable evidence of a torn append and must survive reboot as a hard stop.
  if(!valid || readCount!=bytes || lineLength!=0) return false;
  prefixCrc32=~prefixCrc;
  return true;
}

bool appendQuarantineRecord(const String &reason){
  if(!fsReady || journalRecoveryRequired || pendingPulses==0) return false;
  if(!quarantineLogTokenValid(pendingNonce,8,16) ||
     !quarantineLogTokenValid(pendingTarget,8,32)){
    journalRecoveryRequired=true;
    return false;
  }

  char record[320];
  const String logNonce=quarantineLogField(pendingNonce,40);
  const String logTarget=quarantineLogField(pendingTarget,80);
  const String logReason=quarantineLogField(reason,128);
  char identity[192];
  int identityLen=snprintf(identity,sizeof(identity),
                           "PULSES=%u NONCE=%s TARGET=%s REASON=",
                           (unsigned int)pendingPulses,
                           logNonce.c_str(),logTarget.c_str());
  if(identityLen<=0 || (size_t)identityLen>=sizeof(identity)) return false;

  int len=snprintf(record,sizeof(record),
                   "TIME=%lu %s%s\n",
                   (unsigned long)millis(),identity,logReason.c_str());
  if(len<=0 || (size_t)len>=sizeof(record)) return false;
  record[len-1]='\0';
  bool generatedSameIdentity=false;
  const bool generatedValid=quarantineLogRecordValid(record,identity,generatedSameIdentity);
  record[len-1]='\n';
  if(!generatedValid || !generatedSameIdentity){
    journalRecoveryRequired=true;
    return false;
  }

  size_t before=0;
  bool alreadyRecorded=false;
  uint32_t prefixCrcBefore=0;
  if(!inspectQuarantineLog(identity,before,alreadyRecorded,prefixCrcBefore)){
    journalRecoveryRequired=true;
    return false;
  }
  // A complete record with the same persisted event identity is the successful
  // side of an earlier ambiguous commit. Reuse it instead of appending twice.
  if(alreadyRecorded) return true;
  if(before>QUARANTINE_MAX_BYTES || (size_t)len>QUARANTINE_MAX_BYTES-before) return false;

  File q=LittleFS.open("/quarantine.log","a");
  if(!q) return false;
  size_t written=q.write((const uint8_t*)record,(size_t)len);
  q.flush();
  q.close();
  if(written!=(size_t)len){
    // The append may have changed flash even when the reported length is short.
    // Freeze all journal mutation until an operator reconciles both records.
    journalRecoveryRequired=true;
    return false;
  }

  File verify=LittleFS.open("/quarantine.log","r");
  if(!verify){
    journalRecoveryRequired=true;
    return false;
  }
  size_t after=verify.size();
  bool verified=after==before+(size_t)len && verify.seek(0,SeekSet);
  uint32_t prefixCrcAfter=0xFFFFFFFFUL;
  for(size_t i=0;verified && i<before;++i){
    int byte=verify.read();
    if(byte<0){ verified=false; break; }
    prefixCrcAfter=quarantineLogCrc32Update(prefixCrcAfter,(uint8_t)byte);
  }
  // CRC32 detects accidental same-size corruption of old records; it is not authentication.
  if(verified && ~prefixCrcAfter!=prefixCrcBefore) verified=false;
  if(verified && !verify.seek(before,SeekSet)) verified=false;
  for(size_t i=0;verified && i<(size_t)len;++i){
    if(verify.read()!=(unsigned char)record[i]) verified=false;
  }
  verify.close();
  // Exact byte readback detects same-size corruption before clearing pending.
  // It is NOT proof of durability across a real flash power cut. Any failed
  // post-write verification is ambiguous and must block retries and deletion.
  if(!verified) journalRecoveryRequired=true;
  return verified;
}

bool quarantinePending(const String &reason){
  if(pendingPulses==0){
    // A verified rejection without its pending event is an inconsistent state.
    // Preserve the one-shot attempt evidence and force a deny latch.
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: quarantine disposition has no pending coin event; operator reconciliation required.");
    return false;
  }
  if(!pendingAttemptMarkerMatches()){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: quarantine disposition denied without a matching durable coin POST attempt marker.");
    return false;
  }
  if(!appendQuarantineRecord(reason)){
    // The controller already rejected this event. If local quarantine
    // persistence is unavailable, block same-boot coin POST retries.
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: quarantine journal commit failed; pending coin retained and relay disabled.");
    return false;
  }
  Serial.println("QUARANTINE: uncredited coin event preserved in flash: "+reason);
  return clearPending();
}

uint16_t boundedTimingMs(uint32_t raw,uint16_t minimum,uint16_t maximum){
  if(raw<minimum) return minimum;
  if(raw>maximum) return maximum;
  return (uint16_t)raw;
}

bool loadLocalOutputPolarity(){
  outputPolarityKnown=false;
  cfg.relayActiveHigh=false;
  cfg.ledActiveHigh=false;
  runRelayActiveHigh=false;
  runLedActiveHigh=false;
  pinConfigSafe=false;
  insertMode=false;
  activeTarget="";
  if(!prefs.isKey("polarityv") ||
     !prefs.isKey("relayhi") ||
     !prefs.isKey("ledhi")){
    Serial.println("CRITICAL: local relay/LED polarity is unconfigured; outputs remain INPUT.");
    return false;
  }
  const uint8_t version=prefs.getUChar("polarityv",0xFF);
  const uint8_t relay=prefs.getUChar("relayhi",0xFF);
  const uint8_t led=prefs.getUChar("ledhi",0xFF);
  if(version!=1 || relay>1 || led>1){
    Serial.println("CRITICAL: local relay/LED polarity marker or values are invalid; outputs remain INPUT.");
    return false;
  }
  cfg.relayActiveHigh=relay!=0;
  cfg.ledActiveHigh=led!=0;
  runRelayActiveHigh=cfg.relayActiveHigh;
  runLedActiveHigh=cfg.ledActiveHigh;
  outputPolarityKnown=true;
  pinConfigSafe=true;
  return true;
}

bool configFieldsMatchStored(const char **failedField);

void loadConfig(){
  if(!prefs.begin("blazevendo",false)){
    // A failed namespace open is not an empty configuration. Do not query or
    // write through an inactive Preferences handle; retain safe defaults.
    cfg=Config{};
    outputPolarityKnown=false;
    runRelayActiveHigh=false;
    runLedActiveHigh=false;
    pinConfigSafe=false;
    insertMode=false;
    activeTarget="";
    char b[17];
    snprintf(b,sizeof(b),"%08lX%08lX",(unsigned long)esp_random(),(unsigned long)esp_random());
    cfg.apPass=String(b);
    Serial.println("CRITICAL: NVS namespace open failed; config unavailable, outputs remain INPUT.");
    return;
  }
  outputPolarityKnown=false;
  cfg.ssid=prefs.getString("ssid","");
  cfg.pass=prefs.getString("pass","");
  cfg.server=prefs.getString("server","10.0.0.1");
  cfg.key=prefs.getString("key","");
  cfg.id=prefs.getString("id","vendo-01");
  cfg.apPass=prefs.getString("appass","");
  cfg.coinPin=prefs.getInt("coinpin",27);
  cfg.insertLedPin=prefs.getInt("ledpin",2);
  cfg.relayPin=prefs.getInt("relaypin",26);
  cfg.coinActiveLow=prefs.getBool("coinlow",true);
  loadLocalOutputPolarity();
  cfg.coinDebounceMs=boundedCoinDebounceMs(prefs.getUInt("debounce",40));
  cfg.pulseGroupMs=boundedTimingMs(prefs.getUInt("groupms",400),10,10000);
  if(cfg.apPass.length()<8){
    char b[17]; snprintf(b,sizeof(b),"%08lX%08lX",(unsigned long)esp_random(),(unsigned long)esp_random());
    cfg.apPass=String(b); prefs.putString("appass",cfg.apPass);
  }

  // A valid local polarity marker is necessary but not sufficient. Preferences
  // returns caller-supplied defaults when an NVS string read fails; verify the
  // just-loaded configuration through the status-bearing readback helper
  // before trusting the persisted polarity on this boot.
  if(outputPolarityKnown){
    const char *failedField=nullptr;
    if(!configFieldsMatchStored(&failedField)){
      cfg.relayActiveHigh=false;
      cfg.ledActiveHigh=false;
      runRelayActiveHigh=false;
      runLedActiveHigh=false;
      outputPolarityKnown=false;
      pinConfigSafe=false;
      insertMode=false;
      activeTarget="";
      Serial.printf("CRITICAL: NVS config readback failed at key '%s'; outputs remain INPUT.\n",
                    failedField?failedField:"unknown");
    }
  }
}

bool persistLocalOutputPolarity(){
  const uint8_t relay=cfg.relayActiveHigh?1:0;
  const uint8_t led=cfg.ledActiveHigh?1:0;
  // Invalidate first; a torn update must never leave a valid-looking profile.
  if(prefs.putUChar("polarityv",0)!=1) return false;
  if(prefs.putUChar("relayhi",relay)!=1) return false;
  if(prefs.putUChar("ledhi",led)!=1) return false;
  // Commit the validity marker last, then read every field back.
  if(prefs.putUChar("polarityv",1)!=1) return false;
  if(!prefs.isKey("polarityv") ||
     !prefs.isKey("relayhi") ||
     !prefs.isKey("ledhi") ||
     prefs.getUChar("polarityv",0xFF)!=1 ||
     prefs.getUChar("relayhi",0xFF)!=relay ||
     prefs.getUChar("ledhi",0xFF)!=led){
    // Best-effort invalidation prevents a mismatched readback being trusted
    // after reboot. Runtime remains on the previous profile, already OFF.
    prefs.putUChar("polarityv",0);
    return false;
  }
  outputPolarityKnown=true;
  runRelayActiveHigh=cfg.relayActiveHigh;
  runLedActiveHigh=cfg.ledActiveHigh;
  return true;
}

bool nvsStringMatchesStored(const char *key,const String &expected){
  // Do not use a fallback sentinel: any String can legally equal that value.
  // The buffer overload returns the exact stored byte count (including NUL),
  // or zero on an NVS read error. Fail closed on length/read/allocation errors.
  if(!prefs.isKey(key)) return false;
  const size_t expectedBytes=expected.length()+1;
  if(prefs.getStringLength(key)!=expectedBytes) return false;
  char *stored=static_cast<char*>(malloc(expectedBytes));
  if(!stored) return false;
  const size_t readBytes=prefs.getString(key,stored,expectedBytes);
  const bool matches=readBytes==expectedBytes &&
                     memcmp(stored,expected.c_str(),expectedBytes)==0;
  free(stored);
  return matches;
}

bool configFieldsMatchStored(const char **failedField){
  if(failedField) *failedField=nullptr;
  if(!nvsStringMatchesStored("ssid",cfg.ssid)){
    if(failedField) *failedField="ssid";
    return false;
  }
  if(!nvsStringMatchesStored("pass",cfg.pass)){
    if(failedField) *failedField="pass";
    return false;
  }
  if(!nvsStringMatchesStored("server",cfg.server)){
    if(failedField) *failedField="server";
    return false;
  }
  if(!nvsStringMatchesStored("key",cfg.key)){
    if(failedField) *failedField="key";
    return false;
  }
  if(!nvsStringMatchesStored("id",cfg.id)){
    if(failedField) *failedField="id";
    return false;
  }
  if(!prefs.isKey("coinpin") || prefs.getInt("coinpin",-1)!=cfg.coinPin){
    if(failedField) *failedField="coinpin";
    return false;
  }
  if(!prefs.isKey("ledpin") || prefs.getInt("ledpin",-1)!=cfg.insertLedPin){
    if(failedField) *failedField="ledpin";
    return false;
  }
  if(!prefs.isKey("relaypin") || prefs.getInt("relaypin",-1)!=cfg.relayPin){
    if(failedField) *failedField="relaypin";
    return false;
  }
  if(!prefs.isKey("coinlow") || prefs.getBool("coinlow",!cfg.coinActiveLow)!=cfg.coinActiveLow){
    if(failedField) *failedField="coinlow";
    return false;
  }
  if(!prefs.isKey("debounce") || prefs.getUInt("debounce",0xFFFFFFFFU)!=cfg.coinDebounceMs){
    if(failedField) *failedField="debounce";
    return false;
  }
  if(!prefs.isKey("groupms") || prefs.getUInt("groupms",0xFFFFFFFFU)!=cfg.pulseGroupMs){
    if(failedField) *failedField="groupms";
    return false;
  }
  return true;
}

bool configFieldsMatchStored(){
  return configFieldsMatchStored(nullptr);
}

bool saveConfig(){
  // Deassert outputs before changing NVS; setup stays inhibited until reboot.
  insertMode=false;
  activeTarget="";
  applyOutputs();
  // Invalidate local polarity before any other configuration write. A cut
  // during the save leaves the next boot in the INPUT-only unknown state.
  if(prefs.putUChar("polarityv",0)!=1) return false;
  prefs.putString("ssid",cfg.ssid); prefs.putString("pass",cfg.pass);
  prefs.putString("server",cfg.server); prefs.putString("key",cfg.key); prefs.putString("id",cfg.id);
  prefs.putInt("coinpin",cfg.coinPin); prefs.putInt("ledpin",cfg.insertLedPin); prefs.putInt("relaypin",cfg.relayPin);
  prefs.putBool("coinlow",cfg.coinActiveLow);
  prefs.putUInt("debounce",cfg.coinDebounceMs); prefs.putUInt("groupms",cfg.pulseGroupMs);
  // Do not publish polarityv=1 unless every configuration field survived NVS
  // readback. A failed or partial save remains INPUT-only after reboot.
  const char *failedField=nullptr;
  if(!configFieldsMatchStored(&failedField)){
    Serial.printf("CRITICAL: NVS config readback failed at key '%s'; outputs remain inhibited.\n",
                  failedField?failedField:"unknown");
    outputPolarityKnown=false;
    pinConfigSafe=false;
    return false;
  }
  // A failed polarity write/readback must leave this boot INPUT-only too.
  outputPolarityKnown=false;
  pinConfigSafe=false;
  return persistLocalOutputPolarity();
}

String jsonString(const String &r,const String &k){
  String n="\""+k+"\":\""; int p=r.indexOf(n); if(p<0) return "";
  p+=n.length(); int e=r.indexOf('"',p); if(e<0) return ""; return r.substring(p,e);
}
bool jsonTrue(const String &r,const String &k){ return r.indexOf("\""+k+"\":1")>=0 || r.indexOf("\""+k+"\":true")>=0; }
int jsonInt(const String &r,const String &k,int def){
  String n="\""+k+"\":"; int p=r.indexOf(n); if(p<0) return def; p+=n.length();
  while(p<(int)r.length() && r[p]==' ') p++;
  int e=p; if(e<(int)r.length() && r[e]=='-') e++;
  while(e<(int)r.length() && isDigit(r[e])) e++;
  if(e==p || (e==p+1 && r[p]=='-')) return def;
  return r.substring(p,e).toInt();
}

bool validInputPullupPin(int pin){
  if(pin<0 || pin>33) return false;
  if(pin>=6 && pin<=11) return false; // connected to module flash
  return pin!=20 && pin!=24 && !(pin>=28 && pin<=31);
}

bool validOutputPin(int pin){
  return validInputPullupPin(pin);
}

bool runtimePinsSafe(int coinPin,int relayPin,int ledPin){
  return validInputPullupPin(coinPin) && validOutputPin(relayPin) &&
         validOutputPin(ledPin) && coinPin!=relayPin &&
         coinPin!=ledPin && relayPin!=ledPin;
}

bool quarantineCoinIngressTransition();

void configureRuntimePins(int coinPin,int relayPin,int ledPin){
  if(!outputPolarityKnown){
    // No default or remote value can establish physical relay/LED polarity.
    // Keep both outputs as high-impedance inputs until local confirmation.
    detachInterrupt(digitalPinToInterrupt(runCoinPin));
    pinMode(runRelayPin,INPUT);
    pinMode(runLedPin,INPUT);
    runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
    pinMode(runCoinPin,INPUT_PULLUP);
    pinMode(runRelayPin,INPUT);
    pinMode(runLedPin,INPUT);
    pinConfigSafe=false;
    insertMode=false;
    activeTarget="";
    attachInterrupt(digitalPinToInterrupt(runCoinPin),coinEdgeISR,runCoinActiveLow?FALLING:RISING);
    quarantineCoinIngressTransition();
    return;
  }
  if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);
  if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);
  detachInterrupt(digitalPinToInterrupt(runCoinPin));
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  // Preload logical OFF before enabling either output driver.
  writeLogical(runRelayPin,false,runRelayActiveHigh);
  writeLogical(runLedPin,false,runLedActiveHigh);
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  attachInterrupt(digitalPinToInterrupt(runCoinPin),coinEdgeISR,runCoinActiveLow?FALLING:RISING);
  writeLogical(runRelayPin,false,runRelayActiveHigh);
  writeLogical(runLedPin,false,runLedActiveHigh);
  quarantineCoinIngressTransition();
}

// Intentionally dormant: register/poll admission signatures do not authenticate
// the returned configuration object. Do not call until CORE defines a separate
// config envelope and QA verifies its exact positive/negative golden vectors.
void applyRemoteConfig(const String &r){
  int rev=jsonInt(r,"config_revision",remoteRevision);
  // Master §6.4 requires a strictly increasing configuration revision.
  // Reject stale, duplicate, and zero initial revisions before mutating any field.
  if(rev<=remoteRevision) return;
  controllerEnabled=jsonInt(r,"enabled",1)!=0;
  coinEnabled=jsonInt(r,"coin_enabled",1)!=0;
  relayEnabled=jsonInt(r,"relay_enabled",1)!=0;
  ledEnabled=jsonInt(r,"led_enabled",1)!=0;
  int cp=jsonInt(r,"coin_pin",-1), rp=jsonInt(r,"relay_pin",-1), lp=jsonInt(r,"led_pin",-1);
  int nextCoin=cp>=0?cp:runCoinPin;
  int nextRelay=rp>=0?rp:runRelayPin;
  int nextLed=lp>=0?lp:runLedPin;
  bool nextPinsSafe=runtimePinsSafe(nextCoin,nextRelay,nextLed);
  bool nextCoinActiveLow=jsonInt(r,"coin_active_low",runCoinActiveLow?1:0)!=0;
  int db=jsonInt(r,"coin_debounce_ms",cfg.coinDebounceMs), pg=jsonInt(r,"pulse_group_ms",cfg.pulseGroupMs), mr=jsonInt(r,"max_wifi_retries",6);
  runDebounceMs=boundedCoinDebounceMs(db); runPulseGroupMs=(uint16_t)constrain(pg,10,10000); maxWifiRetries=constrain(mr,1,60);
  if(nextPinsSafe){
    runCoinActiveLow=nextCoinActiveLow;
    // Publish the validated map before configureRuntimePins(): its local
    // polarity guard must be able to revoke pinConfigSafe when polarity is unknown.
    pinConfigSafe=true;
    configureRuntimePins(nextCoin,nextRelay,nextLed);
  } else {
    pinConfigSafe=false;
    Serial.println("CRITICAL: unsafe or colliding GPIO assignment rejected; outputs disabled.");
  }
  remoteRevision=rev; applyOutputs();
}

bool validSha256Hex(const String &digest){
  if(digest.length()!=64) return false;
  for(size_t i=0;i<64;i++){
    const char c=digest[i];
    if(!((c>='0'&&c<='9') ||
         (c>='a'&&c<='f') ||
         (c>='A'&&c<='F'))) return false;
  }
  return true;
}

String lastSentNonce;

String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  String base=cfg.key+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  String digest=hexDigest(base);
  if(!validSha256Hex(digest)) return String();
  lastSentNonce=n;
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+digest;
}

String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce=""){
  if(WiFi.status()!=WL_CONNECTED) return "";
  String body=signedBody(action,pulses,target,forcedNonce);
  if(!body.length()) return "";
  WiFiClient client; HTTPClient h;
  String url="http://"+cfg.server+":4455/cgi-bin/vendo";
  if(!h.begin(client,url)) return "";
  h.setTimeout(3500); h.addHeader("Content-Type","application/x-www-form-urlencoded");
  int code=h.POST(body);
  String r=code>0?h.getString():""; h.end(); return r;
}

void writeLogical(int pin,bool on,bool activeHigh){ digitalWrite(pin,(on==activeHigh)?HIGH:LOW); }
// Never send a RAM-only pulse if its flash journal failed or is ambiguous.
bool canAttemptCoinPost(){
  return outputPolarityKnown && pinConfigSafe && fsReady && !journalRecoveryRequired && !pendingPostAttempted &&
         pendingReady && pendingPulses>0;
}

bool coinLineIdle(){
  const bool raw=digitalRead(runCoinPin);
  return runCoinActiveLow?raw:!raw;
}

// Synchronous HTTP can block GPIO sampling for 3.5 seconds. Start a poll only
// with no unsettled/owed coin and inhibit the acceptor before network I/O.
bool canStartPoll(){
  return outputPolarityKnown && fsReady && !journalRecoveryRequired && !pendingReady &&
         pendingPulses==0 && coinLineIdle();
}

// Keep configured controller/coin/relay admission identical for sampling and
// output gating. Poll-time suspension remains a separate runtime condition.
bool coinIngressConfigurationAllows(){
  return controllerEnabled && coinEnabled && relayEnabled;
}

void applyOutputs(){
  if(!outputPolarityKnown) return;
  bool accepting=pinConfigSafe && coinIngressConfigurationAllows() && insertMode && activeTarget.length()>0 && fsReady &&
                 !journalRecoveryRequired && !pendingReady && !pollIntakeSuspended &&
                 snapshotCoinEdgeSequence()==lastHandledCoinEdgeSequence;
  if(ledEnabled) writeLogical(runLedPin,accepting,runLedActiveHigh); else writeLogical(runLedPin,false,runLedActiveHigh);

  // The first GPIO write can be interrupted after the admission snapshot.
  // Recheck before the relay write so an unresolved edge cannot power the acceptor.
  if(snapshotCoinEdgeSequence()!=lastHandledCoinEdgeSequence){
    writeLogical(runLedPin,false,runLedActiveHigh);
    writeLogical(runRelayPin,false,runRelayActiveHigh);
    return;
  }

  if(relayEnabled) writeLogical(runRelayPin,accepting,runRelayActiveHigh); else writeLogical(runRelayPin,false,runRelayActiveHigh);

  // An edge may also interrupt the relay write itself. Deassert immediately;
  // the next loop sample persists the unresolved ingress fault.
  if(snapshotCoinEdgeSequence()!=lastHandledCoinEdgeSequence){
    writeLogical(runRelayPin,false,runRelayActiveHigh);
    writeLogical(runLedPin,false,runLedActiveHigh);
  }
}

void latchPollPulseFault(uint32_t pulseEdges){
  journalRecoveryRequired=true;
  insertMode=false;
  activeTarget="";
  // Deassert the physical outputs before any flash persistence can block.
  applyOutputs();
  const bool backupPersisted=writePollFaultBackup(pulseEdges);
  const bool littleFsPersisted=writePollPulseFaultMarker(pulseEdges);
  if(backupPersisted && littleFsPersisted){
    Serial.println("CRITICAL: coin-ingress fault recorded in NVS/EEPROM and LittleFS; operator reconciliation required.");
  } else if(backupPersisted){
    Serial.println("CRITICAL: coin-ingress fault persisted in secondary NVS/EEPROM; LittleFS marker failed; operator reconciliation required.");
  } else if(littleFsPersisted){
    Serial.println("CRITICAL: coin-ingress fault persisted in LittleFS; secondary NVS/EEPROM marker failed; operator reconciliation required.");
  } else {
    Serial.println("CRITICAL: both poll-pulse fault stores failed; current boot remains fail-closed but reboot durability is NOT established.");
  }
}

bool quarantineCoinIngressTransition(){
  const uint32_t observedEdgeSequence=snapshotCoinEdgeSequence();
  const uint32_t unhandledEdges=observedEdgeSequence-lastHandledCoinEdgeSequence;
  const bool lineIdle=coinLineIdle();
  if(journalRecoveryRequired){
    lastHandledCoinEdgeSequence=observedEdgeSequence;
    lastCoin=!lineIdle;
    if(pendingPulses>0U) pendingReady=true;
    applyOutputs();
    return false;
  }
  if(lineIdle && unhandledEdges==0U) return true;
  if(pendingPulses>0U) pendingReady=true;
  lastHandledCoinEdgeSequence=observedEdgeSequence;
  lastCoin=!lineIdle;
  const uint32_t unresolvedEdges=(uint32_t)pendingPulses+
      (unhandledEdges>0U?unhandledEdges:1U);
  latchPollPulseFault(unresolvedEdges);
  Serial.println("CRITICAL: coin ingress was active or an ISR edge crossed pin configuration; operator reconciliation required.");
  return false;
}

bool reconcileUnobservedCoinEdges(){
  const uint32_t observedEdgeSequence=snapshotCoinEdgeSequence();
  const uint32_t unhandledEdges=observedEdgeSequence-lastHandledCoinEdgeSequence;
  if(unhandledEdges==0U) return true;
  lastHandledCoinEdgeSequence=observedEdgeSequence;
  if(pendingPulses>0) pendingReady=true;
  latchPollPulseFault((uint32_t)pendingPulses+unhandledEdges);
  Serial.println("CRITICAL: unobserved coin ISR edge(s) crossed a blocking operation; operator reconciliation required.");
  return false;
}



// Observe a full debounce-width quiet interval after disabling intake.
// A pulse at any point cancels polling and returns to normal journal handling.
bool coinLineQuietAfterInhibit(){
  pollDrainAbortedOnActiveLine=false;
  const uint32_t started=millis();
  // Drain the supported 30–100 ms coin pulse train before blocking HTTP.
  // Preserve a larger configured debounce interval; never shorten it.
  const uint32_t pulseTrainQuietMs=250UL;
  const uint32_t quietMs=runDebounceMs>pulseTrainQuietMs?runDebounceMs:pulseTrainQuietMs;
  while(millis()-started<quietMs){
    if(!coinLineIdle()){
      pollDrainAbortedOnActiveLine=true;
      return false;
    }
    delay(1);
  }
  const bool idle=coinLineIdle();
  if(!idle) pollDrainAbortedOnActiveLine=true;
  return idle;
}

// Close the check-to-inhibit race: after the first idle check, disable intake,
// then require the line to remain idle before any blocking network operation.
bool beginPollWindow(){
  if(!canStartPoll()) return false;
  pollIntakeSuspended=true;
  applyOutputs();
  // The caller must reconcile the ISR sequence before releasing this inhibit,
  // whether the quiet drain succeeds or aborts.
  return coinLineQuietAfterInhibit();
}
 
void sampleCoinPulseEdge(bool active){
  const uint32_t observedEdgeSequence=snapshotCoinEdgeSequence();
  const uint32_t unseenEdges=observedEdgeSequence-lastHandledCoinEdgeSequence;
  // Never collapse a multi-edge ISR delta into one credit-eligible sample.
  const bool exactlyOneUnseenEdge=unseenEdges==1U;
  // A coin edge is credit-eligible only while the controller, coin feature and
  // acceptor relay are configured ON. Poll-time relay suspension is separate:
  // relayEnabled stays true while pollIntakeSuspended temporarily deasserts output.
  const bool coinIngressConfigured=coinIngressConfigurationAllows();
  const bool sampledSingleEdge=exactlyOneUnseenEdge && active && !lastCoin &&
      coinIngressConfigured && fsReady && !journalRecoveryRequired && !pendingReady &&
      insertMode && activeTarget.length()>0 &&
      millis()-lastEdge>runDebounceMs;
  if(unseenEdges>0U && !sampledSingleEdge){
    if(pendingPulses>0) pendingReady=true;
    if(!journalRecoveryRequired){
      latchPollPulseFault((uint32_t)pendingPulses+unseenEdges);
      Serial.println("CRITICAL: ISR coin edge could not be sampled and assigned to a pending event; operator reconciliation required.");
    }
    lastHandledCoinEdgeSequence=observedEdgeSequence;
    lastCoin=active;
    applyOutputs();
    return;
  }
  if(fsReady && !journalRecoveryRequired && active && !lastCoin &&
     millis()-lastEdge>runDebounceMs){
    if(!coinIngressConfigured){
      if(pendingPulses>0U) pendingReady=true;
      latchPollPulseFault((uint32_t)pendingPulses+1U);
      applyOutputs();
      Serial.println("CRITICAL: coin pulse observed while controller, coin, or acceptor relay is disabled; operator reconciliation required.");
    } else if(!pinConfigSafe){
      latchPollPulseFault((uint32_t)pendingPulses+1U);
      pendingReady=true;
      applyOutputs();
      Serial.println("CRITICAL: coin pulse observed with unsafe GPIO mapping; operator reconciliation required.");
    } else if(pendingReady){
      // A pulse after the pending batch is closed cannot be appended or safely
      // assigned to a new event. Preserve the old identity and quarantine it.
      latchPollPulseFault((uint32_t)pendingPulses+1U);
      pendingReady=true;
      applyOutputs();
      Serial.println("CRITICAL: coin pulse arrived after pending batch closed; operator reconciliation required.");
    } else if(insertMode && activeTarget.length()){
      if(pendingPulses==0){ pendingNonce=freshNonce(); pendingTarget=activeTarget; }
      // PendingRecord.pulses is bounded to 20. Never silently discard an edge
      // that cannot fit the record or that belongs to a different target.
      if(pendingTarget!=activeTarget || pendingPulses>=20){
        latchPollPulseFault((uint32_t)pendingPulses+1U);
        pendingReady=true;
        applyOutputs();
        Serial.println("CRITICAL: coin pulse batch overflow or target changed; operator reconciliation required.");
      } else {
        pendingPulses++;
        lastEdge=millis();
        if(!savePending()){
          // Preserve a boot-visible deny latch before declaring LittleFS unavailable.
          latchPollPulseFault(pendingPulses);
          fsReady=false;
          pendingReady=true;
          applyOutputs();
          Serial.println("CRITICAL: pending journal write failed; sticky dual-store fault latch attempted; relay disabled.");
        }
      }
    }
  }
  lastHandledCoinEdgeSequence=observedEdgeSequence;
  lastCoin=active;
}



// Strict, bounded root-object reader for a single root-level "ok":true status.
// It rejects nested/quoted decoys, duplicate keys and trailing bytes; it is structural only,
// not a signature verifier or authenticated financial receipt check.
bool pollJsonSpace(char c){
  return c==' ' || c=='\t' || c=='\r' || c=='\n';
}

bool pollJsonHex(char c){
  return (c>='0' && c<='9') || (c>='a' && c<='f') || (c>='A' && c<='F');
}

bool pollJsonSkipString(const String &r,int &p){
  const int n=(int)r.length();
  if(p>=n || r[p]!='"') return false;
  ++p;
  while(p<n){
    const unsigned char c=(unsigned char)r[p++];
    if(c=='"') return true;
    if(c<0x20) return false;
    if(c=='\\'){
      if(p>=n) return false;
      const char e=r[p++];
      if(e=='u'){
        for(int i=0;i<4;i++){
          if(p>=n || !pollJsonHex(r[p])) return false;
          ++p;
        }
      } else if(e!='"' && e!='\\' && e!='/' && e!='b' &&
                e!='f' && e!='n' && e!='r' && e!='t'){
        return false;
      }
    }
  }
  return false;
}

bool pollJsonSkipComposite(const String &r,int &p){
  const int n=(int)r.length();
  if(p>=n || (r[p]!=123 && r[p]!='[')) return false;
  char closing[16];
  int depth=0;
  const char first=r[p++];
  closing[depth++]=(first==123)?125:']';
  while(depth>0 && p<n){
    const char c=r[p];
    if(c=='"'){
      if(!pollJsonSkipString(r,p)) return false;
      continue;
    }
    if(c==123 || c=='['){
      if(depth>=(int)sizeof(closing)) return false;
      closing[depth++]=(c==123)?125:']';
      ++p;
      continue;
    }
    if(c==125 || c==']'){
      if(closing[depth-1]!=c) return false;
      --depth;
      ++p;
      continue;
    }
    if((unsigned char)c<0x20 && !pollJsonSpace(c)) return false;
    ++p;
  }
  return depth==0;
}

bool pollJsonSkipPrimitive(const String &r,int &p){
  const int n=(int)r.length();
  const int start=p;
  while(p<n && r[p]!=',' && r[p]!=125 && r[p]!=']' && !pollJsonSpace(r[p])) ++p;
  const int end=p;
  if(start==end) return false;
  const int length=end-start;
  if(length==4 && r[start]=='t' && r[start+1]=='r' &&
     r[start+2]=='u' && r[start+3]=='e') return true;
  if(length==5 && r[start]=='f' && r[start+1]=='a' &&
     r[start+2]=='l' && r[start+3]=='s' && r[start+4]=='e') return true;
  if(length==4 && r[start]=='n' && r[start+1]=='u' &&
     r[start+2]=='l' && r[start+3]=='l') return true;

  int q=start;
  if(r[q]=='-') ++q;
  if(q>=end) return false;
  if(r[q]=='0'){
    ++q;
  } else if(r[q]>='1' && r[q]<='9'){
    while(q<end && r[q]>='0' && r[q]<='9') ++q;
  } else {
    return false;
  }
  if(q<end && r[q]=='.'){
    ++q;
    const int fractionStart=q;
    while(q<end && r[q]>='0' && r[q]<='9') ++q;
    if(q==fractionStart) return false;
  }
  if(q<end && (r[q]=='e' || r[q]=='E')){
    ++q;
    if(q<end && (r[q]=='+' || r[q]=='-')) ++q;
    const int exponentStart=q;
    while(q<end && r[q]>='0' && r[q]<='9') ++q;
    if(q==exponentStart) return false;
  }
  return q==end;
}

bool pollJsonSkipValue(const String &r,int &p){
  const int n=(int)r.length();
  if(p>=n) return false;
  if(r[p]=='"') return pollJsonSkipString(r,p);
  if(r[p]==123 || r[p]=='[') return pollJsonSkipComposite(r,p);
  return pollJsonSkipPrimitive(r,p);
}

bool pollJsonTopLevelTrue(const String &r,const char *wanted){
  if(!wanted) return false;
  const int n=(int)r.length();
  int p=0;
  while(p<n && pollJsonSpace(r[p])) ++p;
  if(p>=n || r[p++]!=123) return false;

  int wantedLength=0;
  while(wanted[wantedLength]) ++wantedLength;
  int found=0;
  bool accepted=false;
  bool afterComma=false;

  while(true){
    while(p<n && pollJsonSpace(r[p])) ++p;
    if(p<n && r[p]==125){
      if(afterComma) return false;
      ++p;
      break;
    }
    if(p>=n || r[p]!='"') return false;

    const int keyStart=p+1;
    if(!pollJsonSkipString(r,p)) return false;
    const int keyEnd=p-1;
    // Escaped property names are unnecessary for this protocol and can
    // otherwise alias a duplicate key after JSON escape decoding.
    for(int i=keyStart;i<keyEnd;i++) if(r[i]=='\\') return false;

    bool matches=(keyEnd-keyStart)==wantedLength;
    if(matches){
      for(int i=0;i<wantedLength;i++){
        if(r[keyStart+i]!=wanted[i]){ matches=false; break; }
      }
    }

    while(p<n && pollJsonSpace(r[p])) ++p;
    if(p>=n || r[p++]!=':') return false;
    while(p<n && pollJsonSpace(r[p])) ++p;

    if(matches){
      if(++found!=1) return false;
      if(p+4>n || r[p]!='t' || r[p+1]!='r' ||
         r[p+2]!='u' || r[p+3]!='e') return false;
      p+=4;
      if(p<n && !pollJsonSpace(r[p]) && r[p]!=',' && r[p]!=125) return false;
      accepted=true;
    } else if(!pollJsonSkipValue(r,p)){
      return false;
    }

    afterComma=false;
    while(p<n && pollJsonSpace(r[p])) ++p;
    if(p<n && r[p]==','){
      ++p;
      afterComma=true;
      continue;
    }
    if(p<n && r[p]==125){
      ++p;
      break;
    }
    return false;
  }

  while(p<n && pollJsonSpace(r[p])) ++p;
  return p==n && found==1 && accepted;
}

bool coinPostDispositionVerified(const String &response,const String &nonce,
                                 const String &target,uint8_t pulses){
  // The current endpoint uses plain HTTP and has no approved event-bound signed
  // receipt/disposition contract. Body text, including root ok:true or error
  // strings, is not authority to erase or quarantine an owed coin.
  (void)response;
  (void)nonce;
  (void)target;
  (void)pulses;
  // PHX-CORE must define the receipt contract; PHX-QA must approve its vectors.
  // Until then, preserve the pending journal and one-shot attempt marker.
  return false;
}

void handleCoinPostResponse(const String &response){
  // Keep the response disposition gate separate from the network loop so the
  // exact decision path can be compiled and failure-injected on both boards.
  if(!coinPostDispositionVerified(response,pendingNonce,pendingTarget,pendingPulses)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: coin POST response lacks approved event-bound authentication; pending evidence retained and automatic replay denied.");
    applyOutputs();
    return;
  }
  if(pollJsonTopLevelTrue(response,"ok")){
    if(reconcileUnobservedCoinEdges()) clearPending();
    if(!reconcileUnobservedCoinEdges()) applyOutputs();
    applyOutputs();
  } else if(response.indexOf("coin window expired")>=0 ||
            response.indexOf("coin target mismatch")>=0 ||
            response.indexOf("no active coin window")>=0 ||
            response.indexOf("another vendo selected")>=0){
    quarantinePending(response);
    if(!reconcileUnobservedCoinEdges()) applyOutputs();
    applyOutputs();
  } else {
    // An authenticated but malformed/unknown disposition remains ambiguous.
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: authenticated coin POST disposition was unknown; pending evidence retained for operator reconciliation.");
    if(!reconcileUnobservedCoinEdges()) applyOutputs();
    applyOutputs();
  }
}

bool acceptPollResponse(const String &response){
  // MASTER ARCHITECTURE_CONTRACTS §6.3: the current response_sig expression is
  // a derived candidate, not an approved poll authorization contract. CORE has
  // not published the canonical producer/golden vectors and QA has not approved
  // both sides at pinned SHAs. Never energize coin intake from this candidate.
  (void)response;
  insertMode=false;
  activeTarget="";
  return false;
}

void startSetupAp(){
  if(setupApName.isEmpty()) setupApName="BlazePwifi-Vendo32-"+String((uint32_t)(ESP.getEfuseMac() & 0xffffffffULL),HEX);
  WiFi.mode(WIFI_AP_STA); WiFi.softAP(setupApName.c_str(),cfg.apPass.c_str()); setupApOn=true; configuredApSince=millis();
  Serial.println("BlazePwifi ESP32 setup AP: "+setupApName); Serial.println("Setup code: "+cfg.apPass);
}

bool verifyWifi(const String &ssid,const String &pass){
  if(ssid.isEmpty()) return false;
  WiFi.disconnect(); delay(150); WiFi.begin(ssid.c_str(),pass.c_str());
  uint32_t t=millis(); while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){delay(250);}
  return WiFi.status()==WL_CONNECTED;
}

bool setupRequestAllowed(){
  return setupApOn && web.client().localIP()==WiFi.softAPIP();
}

bool requireSetupApRequest(){
  if(setupRequestAllowed()) return true;
  web.send(403,"text/plain","Setup routes are available only through the active setup AP.\n");
  return false;
}

void setupPortal(){
  startSetupAp();
  web.on("/",[](){
    if(!requireSetupApRequest()) return;
    String relayPolarityValue=outputPolarityKnown?String(cfg.relayActiveHigh?1:0):String("");
    String ledPolarityValue=outputPolarityKnown?String(cfg.ledActiveHigh?1:0):String("");
    String h="<meta name=viewport content='width=device-width'><h2>BlazePwifi ESP32 Vendo</h2><form method=POST action=/save>"
      "SSID <input name=s value='"+htmlEsc(cfg.ssid)+"'><br>WiFi credential <input name=p type=password><br>"
      "Server <input name=server value='"+htmlEsc(cfg.server)+"'><br>Controller key <input name=k type=password><br>"
      "ID <input name=id value='"+htmlEsc(cfg.id)+"'><br>Coin GPIO <input name=coin value='"+String(cfg.coinPin)+"'><br>"
      "LED GPIO <input name=led value='"+String(cfg.insertLedPin)+"'><br>Relay GPIO <input name=relay value='"+String(cfg.relayPin)+"'><br>"
      "Debounce ms <input name=db value='"+String(cfg.coinDebounceMs)+"'><br>Pulse group ms <input name=pg value='"+String(cfg.pulseGroupMs)+"'><br>"
      "Coin active low <input name=cl value='"+String(cfg.coinActiveLow?1:0)+"'><br>"
      "Relay active high <input name=rh value='"+relayPolarityValue+"'><br>"
      "LED active high <input name=lh value='"+ledPolarityValue+"'><br><button>Save & reboot</button></form>"
      "<hr><p><a href='/quarantine'>View Quarantine Log</a></p>";
    web.send(200,"text/html",h);
  });
  web.on("/quarantine",[](){
    if(!requireSetupApRequest()) return;
    if(!fsReady || !LittleFS.exists("/quarantine.log")){
      web.send(200,"text/plain","No quarantine records found.\n");
      return;
    }
    File f=LittleFS.open("/quarantine.log","r");
    if(!f){ web.send(500,"text/plain","Failed to open quarantine log.\n"); return; }
    String s=f.readString(); f.close();
    web.send(200,"text/plain",s);
  });
  web.on("/quarantine/clear",HTTP_POST,[](){
    // Quarantine is unpaid-coin reconciliation evidence. Network clients may
    // read/export it, but firmware must never erase it without an approved
    // durable receipt and authenticated operator recovery contract.
    web.send(403,"text/plain","Quarantine deletion disabled; preserve and reconcile evidence offline.\n");
  });
  web.on("/save",HTTP_POST,[](){
    if(!requireSetupApRequest()) return;
    String newSsid=web.arg("s"), newPass=web.arg("p").length()?web.arg("p"):cfg.pass;
    int nextCoin=web.arg("coin").toInt(), nextLed=web.arg("led").toInt(), nextRelay=web.arg("relay").toInt();
    if(!runtimePinsSafe(nextCoin,nextRelay,nextLed)){
      web.send(400,"text/plain","Unsafe or colliding GPIO assignment. Settings were NOT saved.");
      return;
    }
    String relayPolarity=web.arg("rh"), ledPolarity=web.arg("lh");
    if((relayPolarity!="0" && relayPolarity!="1") ||
       (ledPolarity!="0" && ledPolarity!="1")){
      web.send(400,"text/plain","Relay and LED polarity must both be explicitly selected as 0 or 1. Settings were NOT saved.");
      return;
    }
    // Stop accepting before changing the persisted local output profile.
    insertMode=false; activeTarget="";
    applyOutputs();
    if(!verifyWifi(newSsid,newPass)){
      web.send(400,"text/plain","Wi-Fi verification failed. Settings were NOT saved. Setup mode remains active.");
      if(!cfg.ssid.isEmpty()) WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str());
      startSetupAp(); return;
    }
    cfg.ssid=newSsid; cfg.pass=newPass; cfg.server=web.arg("server"); if(web.arg("k").length()) cfg.key=web.arg("k"); cfg.id=web.arg("id");
    cfg.coinPin=nextCoin; cfg.insertLedPin=nextLed; cfg.relayPin=nextRelay;
    long db=web.arg("db").toInt(), pg=web.arg("pg").toInt(); if(pg<10)pg=10;if(pg>10000)pg=10000;
    cfg.coinDebounceMs=boundedCoinDebounceMs(db); cfg.pulseGroupMs=(uint16_t)pg; cfg.coinActiveLow=web.arg("cl")!="0";
    cfg.relayActiveHigh=relayPolarity=="1"; cfg.ledActiveHigh=ledPolarity=="1";
    if(!saveConfig()){
      web.send(500,"text/plain","Local output polarity commit/readback failed. Outputs remain inhibited; retry setup.");
      return;
    }
    web.send(200,"text/plain","Wi-Fi and local output polarity settings verified and saved. Rebooting..."); delay(700); ESP.restart();
  });
  web.begin(); configuredApSince=millis();
}

void connectSta(){
  if(cfg.ssid.isEmpty()) return;
  WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str());
  uint32_t t=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){ delay(250); }
  if(WiFi.status()==WL_CONNECTED){
    wifiFailures=0;
    String r=post("register");
    // This authenticates only the register tuple, not the returned config.
    bool registerTupleAuthenticated=false;
    if(cfg.key.length()){
      String sig=jsonString(r,"response_sig");
      if(sig.length()){
        int st=jsonInt(r,"server_time",0);
        String expected=hexDigest(cfg.key+"|register|"+cfg.id+"|"+lastSentNonce+"|"+String(st)+"|"+cfg.key);
        registerTupleAuthenticated=sig.equalsIgnoreCase(expected);
      }
    }
    if(!registerTupleAuthenticated)
      Serial.println("Register response unauthenticated; remote configuration remains disabled.");
  }
}

void setup(){
  Serial.begin(115200); loadConfig();
  initPollFaultBackupStore();
  runCoinPin=cfg.coinPin; runLedPin=cfg.insertLedPin; runRelayPin=cfg.relayPin;
  if(!runtimePinsSafe(runCoinPin,runRelayPin,runLedPin)){
    pinConfigSafe=false;
    runCoinPin=27; runLedPin=2; runRelayPin=26;
    Serial.println("CRITICAL: stored GPIO assignment unsafe; using disabled safe defaults until corrected.");
  }
  runCoinActiveLow=cfg.coinActiveLow; runRelayActiveHigh=cfg.relayActiveHigh; runLedActiveHigh=cfg.ledActiveHigh;
  runDebounceMs=cfg.coinDebounceMs; runPulseGroupMs=cfg.pulseGroupMs;
  // NVS fault backup is ready; deassert outputs and attach the coin ISR before
  // LittleFS mount so an early ingress can still persist to the secondary store.
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  initPendingStore();
  setupPortal(); connectSta();
}

void handlePollDrainAbortAfterSample(){
  if(!pollDrainAbortedOnActiveLine) return;
  if(journalRecoveryRequired){
    pollDrainAbortedOnActiveLine=false;
    pollIntakeSuspended=false;
    applyOutputs();
    return;
  }
  if(pendingPulses==0U){
    // The drain saw a pulse but the ordinary sample could not durably queue it.
    latchPollPulseFault(1U);
    pollDrainAbortedOnActiveLine=false;
    pollIntakeSuspended=false;
    applyOutputs();
    lastPoll=millis();
    return;
  }
  // A captured pulse keeps intake inhibited until the input line is idle.
  if(!coinLineIdle()) return;
  pollDrainAbortedOnActiveLine=false;
  pollIntakeSuspended=false;
  applyOutputs();
  lastPoll=millis();
}

void loop(){
  web.handleClient();
  if(WiFi.status()!=WL_CONNECTED && !cfg.ssid.isEmpty() && millis()-lastPoll>8000){
    WiFi.disconnect(); WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str()); wifiFailures++; lastPoll=millis();
    if(wifiFailures>=maxWifiRetries) startSetupAp();
  }
  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500){
    const uint32_t pollEdgeStart=snapshotCoinEdgeSequence();
    if(pollEdgeStart!=lastHandledCoinEdgeSequence){
      const uint32_t unhandledEdges=pollEdgeStart-lastHandledCoinEdgeSequence;
      lastHandledCoinEdgeSequence=pollEdgeStart;
      if(pendingPulses>0) pendingReady=true;
      latchPollPulseFault((uint32_t)pendingPulses+unhandledEdges);
      pollIntakeSuspended=false;
      applyOutputs();
      lastPoll=millis();
    } else {
      const bool pollWindowReady=beginPollWindow();
      // Reconcile ISR edges for both drain outcomes while outputs remain inhibited.
      const uint32_t pollEdgeAfterDrain=snapshotCoinEdgeSequence();
      if(pollEdgeAfterDrain!=pollEdgeStart){
        lastHandledCoinEdgeSequence=pollEdgeAfterDrain;
        if(pendingPulses>0) pendingReady=true;
        latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart);
        pollIntakeSuspended=false;
        applyOutputs();
        lastPoll=millis();
      } else if(pollWindowReady){
        wifiFailures=0;
        String r=post("poll");
        // Keep intake inhibited until this response has been accepted or denied.
        acceptPollResponse(r);
        pollIntakeSuspended=false;
        const uint32_t pollEdgeEnd=snapshotCoinEdgeSequence();
        lastHandledCoinEdgeSequence=pollEdgeEnd;
        if(pollEdgeEnd!=pollEdgeStart){
          if(pendingPulses>0) pendingReady=true;
          latchPollPulseFault(pollEdgeEnd-pollEdgeStart);
        }
        applyOutputs();
        lastPoll=millis();
      } else if(pollIntakeSuspended && !pollDrainAbortedOnActiveLine && coinLineIdle()){
        pollIntakeSuspended=false;
        applyOutputs();
        lastPoll=millis();
      }
    }
  }
  bool raw=digitalRead(runCoinPin);
  bool active=runCoinActiveLow?!raw:raw;
  sampleCoinPulseEdge(active);
  if(pendingPulses && !pendingReady && millis()-lastEdge>runPulseGroupMs){ pendingReady=true; lastSend=0; applyOutputs(); }
  handlePollDrainAbortAfterSample();
  if(canAttemptCoinPost() && WiFi.status()==WL_CONNECTED){
    if(!markPendingPostAttempt()){
      journalRecoveryRequired=true;
      applyOutputs();
      if(!reconcileUnobservedCoinEdges()) applyOutputs();
    } else if(!reconcileUnobservedCoinEdges()){
      applyOutputs();
    } else {
      String r=post("coin",String(pendingPulses),pendingTarget,pendingNonce);
      lastSend=millis();
      if(!reconcileUnobservedCoinEdges()){
        applyOutputs();
      } else {
        handleCoinPostResponse(r);
      }
    }
  }
  if(setupApOn && !cfg.ssid.isEmpty() && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){ WiFi.softAPdisconnect(true); setupApOn=false; }
  delay(2);
}
