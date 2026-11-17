#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <EEPROM.h>
#include <LittleFS.h>
#include <string.h>
#include <bearssl/bearssl_hash.h>

struct ConfigV1 {
  uint32_t magic;
  char ssid[33];
  char pass[65];
  char server[64];
  char key[65];
  char id[33];
  uint8_t coinPin;
  uint8_t insertLedPin;
  uint8_t relayPin;
  uint8_t coinActiveLow;
};

struct Config {
  uint32_t magic;
  char ssid[33];
  char pass[65];
  char server[64];
  char key[65];
  char id[33];
  char apPass[17];
  uint8_t coinPin;
  uint8_t insertLedPin;
  uint8_t relayPin;
  uint8_t coinActiveLow;
};

Config cfg;
ESP8266WebServer web(80);
const uint32_t MAGIC_V1=0x42505731;
const uint32_t MAGIC=0x42505732;

bool insertMode=false;
bool lastCoin=false;
bool pollIntakeSuspended=false, pinConfigSafe=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
bool pendingReady=false, fsReady=false, journalRecoveryRequired=false, pendingPostAttempted=false;
int runCoinPin=4, runLedPin=14, runRelayPin=5, maxWifiRetries=6, wifiFailures=0, remoteRevision=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;

String activeTarget, pendingTarget, pendingNonce, setupApName;

struct PendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};

// Master Architecture Contracts §2.1: never accept a debounce below 20 ms.
// Apply the same bound to persisted, local-setup, and controller-provided values.
uint16_t boundedCoinDebounceMs(long long requested){
  if(requested<20LL) return 20;
  if(requested>2000LL) return 2000;
  return (uint16_t)requested;
}

const uint32_t PENDING_MAGIC=0x42504331;

String hexDigest(const String &s){
  br_sha256_context c; uint8_t out[32]; char buf[65];
  br_sha256_init(&c); br_sha256_update(&c,s.c_str(),s.length()); br_sha256_out(&c,out);
  for(int i=0;i<32;i++) sprintf(buf+i*2,"%02x",out[i]); buf[64]=0; return String(buf);
}

String freshNonce(){
  char b[17]; uint32_t a=ESP.random(),c=ESP.random();
  sprintf(b,"%08lx%08lx",(unsigned long)a,(unsigned long)c); return String(b);
}

uint32_t pendingChecksum(const PendingRecord &r){
  const uint8_t *p=(const uint8_t*)&r; uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(PendingRecord,checksum);i++){h^=p[i];h*=16777619UL;}
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
  PendingRecord r; memset(&r,0,sizeof(r)); r.magic=PENDING_MAGIC; r.pulses=pendingPulses;
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
  PendingRecord verify; memset(&verify,0,sizeof(verify));
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
  bool durablePendingMatches=false;
  for(size_t i=0;i<sizeof(pendingPaths)/sizeof(pendingPaths[0]);++i){
    if(LittleFS.exists(pendingPaths[i])){
      PendingRecord durable{};
      if(readPendingFile(pendingPaths[i],durable) &&
         samePendingRecord(record,durable)) durablePendingMatches=true;
    }
  }
  if(!durablePendingMatches){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: no matching durable pending record; coin POST denied.");
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

void initPendingStore(){
  // Never format a failed-to-mount payment journal. It may contain coin evidence.
  fsReady=LittleFS.begin();
  if(!fsReady){
    Serial.println("CRITICAL: LittleFS mount failed; preserving journal for recovery. Coin intake disabled.");
    return;
  }
  loadPending();
}

String esc(const String &s){
  String o;
  for(unsigned i=0;i<s.length();i++){
    char c=s[i];
    if(isalnum(c)||c=='-'||c=='_'||c=='.') o+=c;
    else {char b[4];sprintf(b,"%%%02X",(unsigned char)c);o+=b;}
  }
  return o;
}

String htmlEsc(const String &s){
  String o;
  for(unsigned i=0;i<s.length();i++){
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

void makeSetupPassword(){
  uint32_t a=ESP.random(), b=ESP.random();
  snprintf(cfg.apPass,sizeof(cfg.apPass),"%08lX%08lX",(unsigned long)a,(unsigned long)b);
}

void defaults(){
  memset(&cfg,0,sizeof(cfg)); cfg.magic=MAGIC;
  strcpy(cfg.server,"10.0.0.1"); strcpy(cfg.id,"vendo-01");
  cfg.coinPin=4; cfg.insertLedPin=14; cfg.relayPin=5; cfg.coinActiveLow=1;
  makeSetupPassword();
}

void saveCfg(){ EEPROM.put(0,cfg); EEPROM.commit(); }

bool fixedStringTerminated(const char *value,size_t capacity){
  return memchr(value,'\0',capacity)!=nullptr;
}

bool configStringsTerminated(const Config &c){
  return fixedStringTerminated(c.ssid,sizeof(c.ssid)) &&
         fixedStringTerminated(c.pass,sizeof(c.pass)) &&
         fixedStringTerminated(c.server,sizeof(c.server)) &&
         fixedStringTerminated(c.key,sizeof(c.key)) &&
         fixedStringTerminated(c.id,sizeof(c.id)) &&
         fixedStringTerminated(c.apPass,sizeof(c.apPass));
}

bool configStringsTerminated(const ConfigV1 &c){
  return fixedStringTerminated(c.ssid,sizeof(c.ssid)) &&
         fixedStringTerminated(c.pass,sizeof(c.pass)) &&
         fixedStringTerminated(c.server,sizeof(c.server)) &&
         fixedStringTerminated(c.key,sizeof(c.key)) &&
         fixedStringTerminated(c.id,sizeof(c.id));
}

void loadCfg(){
  EEPROM.begin(sizeof(Config));
  EEPROM.get(0,cfg);
  if(cfg.magic==MAGIC && configStringsTerminated(cfg) &&
     strnlen(cfg.apPass,sizeof(cfg.apPass))>=8) return;
  if(cfg.magic==MAGIC){
    Serial.println("CRITICAL: malformed current configuration; discarding unterminated EEPROM fields.");
  }

  ConfigV1 oldCfg;
  EEPROM.get(0,oldCfg);
  if(oldCfg.magic==MAGIC_V1 && configStringsTerminated(oldCfg)){
    defaults();
    strlcpy(cfg.ssid,oldCfg.ssid,sizeof(cfg.ssid));
    strlcpy(cfg.pass,oldCfg.pass,sizeof(cfg.pass));
    strlcpy(cfg.server,oldCfg.server,sizeof(cfg.server));
    strlcpy(cfg.key,oldCfg.key,sizeof(cfg.key));
    strlcpy(cfg.id,oldCfg.id,sizeof(cfg.id));
    cfg.coinPin=oldCfg.coinPin;
    cfg.insertLedPin=oldCfg.insertLedPin;
    cfg.relayPin=oldCfg.relayPin;
    cfg.coinActiveLow=oldCfg.coinActiveLow;
    saveCfg();
    Serial.println("Migrated BlazePwifi Vendo v1 configuration.");
    return;
  }
  if(oldCfg.magic==MAGIC_V1){
    Serial.println("CRITICAL: malformed v1 configuration; migration refused.");
  }

  defaults();
  saveCfg();
}

String jsonString(const String&r,const String&k){
  String needle="\""+k+"\":\""; int p=r.indexOf(needle); if(p<0)return "";
  p+=needle.length(); int e=r.indexOf('\"',p); if(e<0)return ""; return r.substring(p,e);
}

bool jsonTrue(const String&r,const String&k){
  return r.indexOf("\""+k+"\":1")>=0 || r.indexOf("\""+k+"\":true")>=0;
}
int jsonInt(const String&r,const String&k,int def){
  String needle="\""+k+"\":"; int p=r.indexOf(needle); if(p<0)return def; p+=needle.length();
  while(p<(int)r.length() && r[p]==' ')p++;
  int e=p; if(e<(int)r.length() && r[e]=='-')e++;
  while(e<(int)r.length() && isDigit(r[e]))e++;
  if(e==p || (e==p+1 && r[p]=='-'))return def;
  return r.substring(p,e).toInt();
}

void writeLogical(int pin,bool on,bool activeHigh){ digitalWrite(pin,(on==activeHigh)?HIGH:LOW); }

bool validInputPullupPin(int pin){
  return (pin>=0 && pin<=5) || (pin>=12 && pin<=15);
}

bool validOutputPin(int pin){
  return (pin>=0 && pin<=5) || (pin>=12 && pin<=16);
}

bool runtimePinsSafe(int coinPin,int relayPin,int ledPin){
  return validInputPullupPin(coinPin) && validOutputPin(relayPin) &&
         validOutputPin(ledPin) && coinPin!=relayPin &&
         coinPin!=ledPin && relayPin!=ledPin;
}

void configureRuntimePins(int coinPin,int relayPin,int ledPin){
  if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);
  if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  writeLogical(runRelayPin,false,runRelayActiveHigh); writeLogical(runLedPin,false,runLedActiveHigh);
}

// Intentionally dormant: register/poll admission signatures do not authenticate
// the returned configuration object. Do not call until CORE defines a separate
// config envelope and QA verifies its exact positive/negative golden vectors.
void applyRemoteConfig(const String&r){
  int rev=jsonInt(r,"config_revision",remoteRevision);
  if(rev==remoteRevision && remoteRevision!=0)return;
  controllerEnabled=jsonInt(r,"enabled",1)!=0; coinEnabled=jsonInt(r,"coin_enabled",1)!=0;
  relayEnabled=jsonInt(r,"relay_enabled",1)!=0; ledEnabled=jsonInt(r,"led_enabled",1)!=0;
  int cp=jsonInt(r,"coin_pin",-1),rp=jsonInt(r,"relay_pin",-1),lp=jsonInt(r,"led_pin",-1);
  int nextCoin=cp>=0?cp:runCoinPin, nextRelay=rp>=0?rp:runRelayPin, nextLed=lp>=0?lp:runLedPin;
  bool nextPinsSafe=runtimePinsSafe(nextCoin,nextRelay,nextLed);
  bool nextCoinActiveLow=jsonInt(r,"coin_active_low",runCoinActiveLow?1:0)!=0;
  bool nextRelayActiveHigh=jsonInt(r,"relay_active_high",runRelayActiveHigh?1:0)!=0;
  bool nextLedActiveHigh=jsonInt(r,"led_active_high",runLedActiveHigh?1:0)!=0;
  runDebounceMs=boundedCoinDebounceMs(jsonInt(r,"coin_debounce_ms",40));
  runPulseGroupMs=(uint16_t)constrain(jsonInt(r,"pulse_group_ms",400),10,10000);
  maxWifiRetries=constrain(jsonInt(r,"max_wifi_retries",6),1,60);
  if(nextPinsSafe){
    runCoinActiveLow=nextCoinActiveLow;
    runRelayActiveHigh=nextRelayActiveHigh;
    runLedActiveHigh=nextLedActiveHigh;
    configureRuntimePins(nextCoin,nextRelay,nextLed);
    pinConfigSafe=true;
  } else {
    pinConfigSafe=false;
    Serial.println("CRITICAL: unsafe or colliding GPIO assignment rejected; outputs disabled.");
  }
  remoteRevision=rev; applyOutputs();
}

String lastSentNonce;

String signedBody(const String& action,const String& pulses,const String& target,const String& forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  lastSentNonce=n;
  String base=String(cfg.key)+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+hexDigest(base);
}

String post(const String& action,const String& pulses="0",const String& target="",const String& forcedNonce=""){
  if(WiFi.status()!=WL_CONNECTED) return "";
  WiFiClient client; HTTPClient h;
  String url="http://"+String(cfg.server)+":4455/cgi-bin/vendo";
  if(!h.begin(client,url)) return "";
  h.setTimeout(3500);
  h.addHeader("Content-Type","application/x-www-form-urlencoded");
  int code=h.POST(signedBody(action,pulses,target,forcedNonce));
  String r=code>0?h.getString():""; h.end(); return r;
}

// Never send a RAM-only pulse if its flash journal failed or is ambiguous.
bool canAttemptCoinPost(){
  return fsReady && !journalRecoveryRequired && !pendingPostAttempted &&
         pendingReady && pendingPulses>0;
}

bool coinLineIdle(){
  const bool raw=digitalRead(runCoinPin);
  return runCoinActiveLow?raw:!raw;
}

// Synchronous HTTP can block GPIO sampling for 3.5 seconds. Start a poll only
// with no unsettled/owed coin and inhibit the acceptor before network I/O.
bool canStartPoll(){
  return fsReady && !journalRecoveryRequired && !pendingReady &&
         pendingPulses==0 && coinLineIdle();
}

void applyOutputs(){
  bool accepting=pinConfigSafe && controllerEnabled && coinEnabled && insertMode && activeTarget.length()>0 && fsReady &&
                 !journalRecoveryRequired && !pendingReady && !pollIntakeSuspended;
  if(ledEnabled) writeLogical(runLedPin,accepting,runLedActiveHigh); else writeLogical(runLedPin,false,runLedActiveHigh);
  if(relayEnabled) writeLogical(runRelayPin,accepting,runRelayActiveHigh); else writeLogical(runRelayPin,false,runRelayActiveHigh);
}

// Observe a full debounce-width quiet interval after disabling intake.
// A pulse at any point cancels polling and returns to normal journal handling.
bool coinLineQuietAfterInhibit(){
  const uint32_t started=millis();
  while(millis()-started<runDebounceMs){
    if(!coinLineIdle()) return false;
    delay(1);
  }
  return coinLineIdle();
}

// Close the check-to-inhibit race: after the first idle check, disable intake,
// then require the line to remain idle before any blocking network operation.
bool beginPollWindow(){
  if(!canStartPoll()) return false;
  pollIntakeSuspended=true;
  applyOutputs();
  if(coinLineQuietAfterInhibit()) return true;
  pollIntakeSuspended=false;
  applyOutputs();
  return false;
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
  while(p<n && r[p]!=',' && r[p]!=125 && !pollJsonSpace(r[p])) ++p;
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

bool acceptPollResponse(const String &response){
  bool insertAllowed=jsonTrue(response,"insert");
  String target=jsonString(response,"target_nonce");
  // PHX-MASTER ARCHITECTURE_CONTRACTS §6.1: keyless bootstrap is never coin authority; require a provisioned key and valid response signature.
  bool signatureOk=false;
  if(String(cfg.key).length()){
    String signature=jsonString(response,"response_sig");
    if(signature.length()){
      int insert=insertAllowed?1:0;
      int expires=jsonInt(response,"expires",0);
      String expected=hexDigest(String(cfg.key)+"|poll|"+String(cfg.id)+"|"+lastSentNonce+"|"+String(insert)+"|"+target+"|"+String(expires)+"|"+String(cfg.key));
      signatureOk=signature.equalsIgnoreCase(expected);
    } else {
      signatureOk=false;
    }
  }
  if(!signatureOk || !pollJsonTopLevelTrue(response,"ok") ||
     (insertAllowed && !target.length())){
    // An unauthenticated, rejected or targetless positive response must not
    // reuse stale permission or energize an acceptor without a bound target.
    insertMode=false;
    activeTarget="";
    return false;
  }
  insertMode=insertAllowed;
  activeTarget=target;
  // The admission signature binds only the poll tuple, not remote pin/config fields.
  // Keep poll authorization separate until CORE/MASTER approve a distinct config signature.
  return true;
}

void startSetupAp(){
  if(!setupApName.length()) setupApName="BlazePwifi-Vendo-"+String(ESP.getChipId(),HEX);
  WiFi.mode(WIFI_AP_STA); WiFi.softAP(setupApName.c_str(),cfg.apPass); setupApOn=true; configuredApSince=millis();
  Serial.println(); Serial.println("BlazePwifi setup AP: "+setupApName); Serial.println("Setup password: "+String(cfg.apPass));
}

bool verifyWifi(const String&ssid,const String&pass){
  if(!ssid.length())return false;
  WiFi.disconnect(); delay(150); WiFi.begin(ssid.c_str(),pass.c_str());
  uint32_t t=millis(); while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){delay(250);yield();}
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
    String h="<meta name=viewport content='width=device-width'><h2>BlazePwifi Vendo</h2>"
      "<p>Setup AP is WPA2 protected. Save changes to reboot.</p>"
      "<form method=POST action=/save>SSID <input name=s value='"+htmlEsc(String(cfg.ssid))+"'><br>"
      "Password <input name=p type=password><br>Server <input name=server value='"+htmlEsc(String(cfg.server))+"'><br>"
      "Vendo key <input name=k type=password><br>ID <input name=id value='"+htmlEsc(String(cfg.id))+"'><br>"
      "Coin GPIO <input name=coin value='"+String(cfg.coinPin)+"'><br>"
      "LED GPIO <input name=led value='"+String(cfg.insertLedPin)+"'><br>"
      "Relay GPIO <input name=relay value='"+String(cfg.relayPin)+"'><br><button>Save & reboot</button></form>"
      "<p>STA: "+WiFi.localIP().toString()+"</p>"
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
    String newSsid=web.arg("s"),newPass=web.arg("p").length()?web.arg("p"):String(cfg.pass);
    int nextCoin=web.arg("coin").toInt(),nextLed=web.arg("led").toInt(),nextRelay=web.arg("relay").toInt();
    if(!runtimePinsSafe(nextCoin,nextRelay,nextLed)){
      web.send(400,"text/plain","Unsafe or colliding GPIO assignment. Settings were NOT saved.");
      return;
    }
    if(!verifyWifi(newSsid,newPass)){
      web.send(400,"text/plain","Wi-Fi verification failed. Settings were NOT saved. Setup mode remains active.");
      if(strlen(cfg.ssid))WiFi.begin(cfg.ssid,cfg.pass); startSetupAp(); return;
    }
    strlcpy(cfg.ssid,newSsid.c_str(),sizeof(cfg.ssid));strlcpy(cfg.pass,newPass.c_str(),sizeof(cfg.pass));
    strlcpy(cfg.server,web.arg("server").c_str(),sizeof(cfg.server));if(web.arg("k").length())strlcpy(cfg.key,web.arg("k").c_str(),sizeof(cfg.key));strlcpy(cfg.id,web.arg("id").c_str(),sizeof(cfg.id));
    cfg.coinPin=nextCoin;cfg.insertLedPin=nextLed;cfg.relayPin=nextRelay;
    saveCfg();web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting...");delay(700);ESP.restart();
  });
  web.begin();
  configuredApSince=millis();
}

void connectSta(){
  if(!strlen(cfg.ssid))return;
  WiFi.begin(cfg.ssid,cfg.pass);
  uint32_t t=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){delay(250);yield();}
  if(WiFi.status()==WL_CONNECTED){
    wifiFailures=0;
    String r=post("register");
    // This authenticates only the register tuple, not the returned config.
    bool registerTupleAuthenticated=false;
    if(strlen(cfg.key)){
      String sig=jsonString(r,"response_sig");
      if(sig.length()){
        int st=jsonInt(r,"server_time",0);
        String expected=hexDigest(String(cfg.key)+"|register|"+String(cfg.id)+"|"+lastSentNonce+"|"+String(st)+"|"+String(cfg.key));
        registerTupleAuthenticated=sig.equalsIgnoreCase(expected);
      }
    }
    if(!registerTupleAuthenticated)
      Serial.println("Register response unauthenticated; remote configuration remains disabled.");
  }
}

bool clearPending(){
  if(journalRecoveryRequired) return false;
  if(!fsReady){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: cannot clear pending journal while LittleFS is unavailable.");
    return false;
  }
  const char *paths[]={"/pending.dat","/pending.new","/pending.bak"};
  unsigned candidateCount=0;
  for(size_t i=0;i<sizeof(paths)/sizeof(paths[0]);++i){
    if(LittleFS.exists(paths[i])) ++candidateCount;
  }
  if(candidateCount>1){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: multiple pending journals at clear; preserving all evidence.");
    return false;
  }
  bool removed=true;
  for(size_t i=0;i<sizeof(paths)/sizeof(paths[0]);++i){
    if(LittleFS.exists(paths[i]) && !LittleFS.remove(paths[i])) removed=false;
    if(LittleFS.exists(paths[i])) removed=false;
  }
  if(!removed){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: pending journal deletion failed; preserving RAM event and disabling relay.");
    return false;
  }
  // Remove the attempt marker LAST. A power cut after pending deletion but
  // before marker deletion leaves an orphan marker that blocks boot admission.
  if(LittleFS.exists("/pending.attempt") &&
     (!LittleFS.remove("/pending.attempt") || LittleFS.exists("/pending.attempt"))){
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
    if(escaped){
      if(out.length()+2>maxLen) break;
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

bool inspectQuarantineLog(const char *identity,size_t &bytes,bool &alreadyRecorded){
  bytes=0; alreadyRecorded=false;
  if(!LittleFS.exists("/quarantine.log")) return true;
  File prior=LittleFS.open("/quarantine.log","r");
  if(!prior) return false;
  bytes=prior.size();
  char line[320];
  size_t lineLength=0,readCount=0;
  bool valid=true;
  while(valid && prior.available()){
    int next=prior.read();
    if(next<0){ valid=false; break; }
    ++readCount;
    if(next=='\n'){
      if(lineLength==0){ valid=false; break; }
      line[lineLength]='\0';
      const char *payload=strchr(line,' ');
      bool timestampValid=strncmp(line,"TIME=",5)==0 &&
                          payload && payload>line+5;
      if(timestampValid){
        const size_t timestampLength=(size_t)(payload-(line+5));
        if(timestampLength>10 || (timestampLength>1 && line[5]=='0'))
          timestampValid=false;
      }
      unsigned long parsedTimestamp=0;
      for(const char *digit=line+5;timestampValid && digit<payload;++digit){
        if(*digit<'0' || *digit>'9'){
          timestampValid=false;
          break;
        }
        const unsigned long value=(unsigned long)(*digit-'0');
        if(parsedTimestamp>(0xFFFFFFFFUL-value)/10UL){
          timestampValid=false;
          break;
        }
        parsedTimestamp=parsedTimestamp*10UL+value;
      }
      // Only canonical uint32 millis timestamps generated by this firmware
      // may participate in dedupe. Corrupt TIME text is not a receipt.
      if(!timestampValid ||
         !strstr(line," PULSES=") || !strstr(line," NONCE=") ||
         !strstr(line," TARGET=") || !strstr(line," REASON=")){
        valid=false; break;
      }
      if(payload && strncmp(payload+1,identity,strlen(identity))==0){
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
  return valid && readCount==bytes && lineLength==0;
}

bool appendQuarantineRecord(const String &reason){
  if(!fsReady || journalRecoveryRequired || pendingPulses==0) return false;

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

  size_t before=0;
  bool alreadyRecorded=false;
  if(!inspectQuarantineLog(identity,before,alreadyRecorded)){
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
  bool verified=after==before+(size_t)len &&
                verify.seek(before,SeekSet);
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
  if(pendingPulses==0) return false;
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

void setup(){
  Serial.begin(115200); loadCfg(); initPendingStore();
  runCoinPin=cfg.coinPin;runLedPin=cfg.insertLedPin;runRelayPin=cfg.relayPin;runCoinActiveLow=cfg.coinActiveLow;
  if(!runtimePinsSafe(runCoinPin,runRelayPin,runLedPin)){
    pinConfigSafe=false;
    runCoinPin=4;runLedPin=14;runRelayPin=5;
    Serial.println("CRITICAL: stored GPIO assignment unsafe; using disabled safe defaults until corrected.");
  }
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);setupPortal();connectSta();
}

void loop(){
  web.handleClient();

  if(WiFi.status()!=WL_CONNECTED && strlen(cfg.ssid) && millis()-lastPoll>8000){
    WiFi.disconnect();WiFi.begin(cfg.ssid,cfg.pass);wifiFailures++;lastPoll=millis();
    if(wifiFailures>=maxWifiRetries)startSetupAp();
  }

  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500 && beginPollWindow()){
    wifiFailures=0;
    String r=post("poll");
    // Keep intake inhibited until this response has been accepted or denied.
    acceptPollResponse(r);
    pollIntakeSuspended=false;
    applyOutputs();lastPoll=millis();
  }

  bool raw=digitalRead(runCoinPin);
  bool active=runCoinActiveLow?!raw:raw;
  if(insertMode && fsReady && !journalRecoveryRequired && activeTarget.length() && !pendingReady && active && !lastCoin && millis()-lastEdge>runDebounceMs){
    if(pendingPulses==0){
      pendingNonce=freshNonce();
      pendingTarget=activeTarget;
    }
    if(pendingTarget==activeTarget && pendingPulses<20){
      pendingPulses++;
      lastEdge=millis();
      if(!savePending()){
        fsReady=false;
        pendingReady=true;
        Serial.println("CRITICAL: failed to persist coin journal; relay disabled.");
      }
    }
  }
  lastCoin=active;

  if(pendingPulses && !pendingReady && millis()-lastEdge>runPulseGroupMs){
    pendingReady=true;
    lastSend=0;
    applyOutputs();
  }

  if(canAttemptCoinPost() && WiFi.status()==WL_CONNECTED){
    if(!markPendingPostAttempt()){
      journalRecoveryRequired=true;
      applyOutputs();
    } else {
      String r=post("coin",String(pendingPulses),pendingTarget,pendingNonce);
      lastSend=millis();
      if(!coinPostDispositionVerified(r,pendingNonce,pendingTarget,pendingPulses)){
        journalRecoveryRequired=true;
        Serial.println("CRITICAL: coin POST response lacks approved event-bound authentication; pending evidence retained and automatic replay denied.");
        applyOutputs();
      } else if(pollJsonTopLevelTrue(r,"ok")){
        clearPending();
        applyOutputs();
      } else if(r.indexOf("coin window expired")>=0 ||
                r.indexOf("coin target mismatch")>=0 ||
                r.indexOf("no active coin window")>=0 ||
                r.indexOf("another vendo selected")>=0){
        quarantinePending(r);
        applyOutputs();
      } else {
        // An authenticated but malformed/unknown disposition remains ambiguous.
        journalRecoveryRequired=true;
        Serial.println("CRITICAL: authenticated coin POST disposition was unknown; pending evidence retained for operator reconciliation.");
        applyOutputs();
      }
    }
  }

  if(setupApOn && strlen(cfg.ssid) && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){
    WiFi.softAPdisconnect(true);setupApOn=false;
  }

  delay(2);
}
