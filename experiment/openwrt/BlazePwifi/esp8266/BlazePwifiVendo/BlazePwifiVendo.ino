#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <EEPROM.h>
#include <new>
#include <LittleFS.h>
#include <bearssl/bearssl_hash.h>
#include <v060_pending_sequence.h>

// ESP8266 core 3.1.2 exposes EEPROMClass storage internals but begin() returns void.
// Use a checked allocator/read path so failed allocation or flash read cannot reach get()/put().
class CheckedEEPROMClass : public EEPROMClass {
public:
  bool beginChecked(size_t requested) {
    static const uint32_t kFlashSectorBytes=4096U;
    if(requested==0 || requested>kFlashSectorBytes) return false;
    const size_t aligned=(requested+3U)&~static_cast<size_t>(3U);
    if(aligned==0 || aligned>kFlashSectorBytes) return false;
    if(_data && _size!=aligned){
      delete[] _data;
      _data=nullptr;
      _size=0;
    }
    if(!_data) _data=new (std::nothrow) uint8_t[aligned];
    if(!_data){
      _size=0;
      _dirty=false;
      return false;
    }
    _size=aligned;
    const uint32_t address=static_cast<uint32_t>(_sector*kFlashSectorBytes);
    if(!ESP.flashRead(address,_data,_size)){
      delete[] _data;
      _data=nullptr;
      _size=0;
      _dirty=false;
      return false;
    }
    _dirty=false;
    return true;
  }
};
CheckedEEPROMClass configEeprom;

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
bool configStoreReady=false;

ESP8266WebServer web(80);
const uint32_t MAGIC_V1=0x42505731;
const uint32_t MAGIC=0x42505732;

bool insertMode=false;
bool lastCoin=false;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
bool pendingReady=false, fsReady=false;
int runCoinPin=4, runLedPin=14, runRelayPin=5, maxWifiRetries=6, wifiFailures=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;
String activeTarget, pendingTarget, pendingNonce, setupApName;

struct LegacyPendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};
size_t boundedStringLength(const char *value,size_t capacity){
  if(!value) return capacity;
  for(size_t i=0;i<capacity;i++){
    if(value[i]=='\0') return i;
  }
  return capacity;
}

bool configStringsTerminated(const Config &value){
  return boundedStringLength(value.ssid,sizeof(value.ssid))<sizeof(value.ssid) &&
         boundedStringLength(value.pass,sizeof(value.pass))<sizeof(value.pass) &&
         boundedStringLength(value.server,sizeof(value.server))<sizeof(value.server) &&
         boundedStringLength(value.key,sizeof(value.key))<sizeof(value.key) &&
         boundedStringLength(value.id,sizeof(value.id))<sizeof(value.id) &&
         boundedStringLength(value.apPass,sizeof(value.apPass))<sizeof(value.apPass);
}

bool configV1StringsTerminated(const ConfigV1 &value){
  return boundedStringLength(value.ssid,sizeof(value.ssid))<sizeof(value.ssid) &&
         boundedStringLength(value.pass,sizeof(value.pass))<sizeof(value.pass) &&
         boundedStringLength(value.server,sizeof(value.server))<sizeof(value.server) &&
         boundedStringLength(value.key,sizeof(value.key))<sizeof(value.key) &&
         boundedStringLength(value.id,sizeof(value.id))<sizeof(value.id);
}
const uint32_t LEGACY_PENDING_MAGIC=0x42504331;
BpPendingSequence pendingSequenceState;

String hexDigest(const String &s){
  br_sha256_context c; uint8_t out[32]; char buf[65];
  br_sha256_init(&c); br_sha256_update(&c,s.c_str(),s.length()); br_sha256_out(&c,out);
  for(int i=0;i<32;i++) sprintf(buf+i*2,"%02x",out[i]); buf[64]=0; return String(buf);
}

bool validSha256Hex(const String &digest){
  if(digest.length()!=64) return false;
  for(size_t i=0;i<64;i++){
    char c=digest[i];
    if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F'))) return false;
  }
  return true;
}
String freshNonce(){
  char b[17]; uint32_t a=ESP.random(),c=micros();
  sprintf(b,"%08lx%08lx",(unsigned long)a,(unsigned long)c); return String(b);
}

uint32_t legacyPendingChecksum(const LegacyPendingRecord &r){
  const uint8_t *p=(const uint8_t*)&r; uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(LegacyPendingRecord,checksum);i++){h^=p[i];h*=16777619UL;}
  return h;
}

bool readPendingFile(const char *path, BpPendingSequence &state, bool &legacy){
  if(!fsReady || !LittleFS.exists(path)) return false;
  File f=LittleFS.open(path,"r"); if(!f) return false;
  size_t size=f.size();
  if(size==sizeof(state)){
    size_t n=f.readBytes((char*)&state,sizeof(state)); f.close(); legacy=false;
    return n==sizeof(state) && bp_pending_sequence_valid(&state);
  }
  if(size==sizeof(LegacyPendingRecord)){
    LegacyPendingRecord old; memset(&old,0,sizeof(old));
    size_t n=f.readBytes((char*)&old,sizeof(old)); f.close();
    if(n!=sizeof(old) || old.magic!=LEGACY_PENDING_MAGIC || old.pulses==0 ||
       old.pulses>20 || old.checksum!=legacyPendingChecksum(old) ||
       !bp_pending_sequence_hex_token(old.nonce,8,16) ||
       !bp_pending_sequence_hex_token(old.target,8,32)) return false;
    bp_pending_sequence_init(&state);
    legacy=true;
    return bp_pending_sequence_reserve(&state,old.pulses,old.nonce,old.target);
  }
  f.close(); return false;
}

bool persistPendingSequence(const BpPendingSequence &state){
  if(!fsReady || !bp_pending_sequence_valid(&state)) return false;
  File f=LittleFS.open("/pending.new","w"); if(!f) return false;
  size_t n=f.write((const uint8_t*)&state,sizeof(state)); f.flush(); f.close();
  if(n!=sizeof(state)){LittleFS.remove("/pending.new");return false;}
  LittleFS.remove("/pending.bak");
  if(LittleFS.exists("/pending.dat")) LittleFS.rename("/pending.dat","/pending.bak");
  if(!LittleFS.rename("/pending.new","/pending.dat")){
    if(LittleFS.exists("/pending.bak")) LittleFS.rename("/pending.bak","/pending.dat");
    return false;
  }
  LittleFS.remove("/pending.bak");
  pendingSequenceState=state;
  return true;
}

bool savePending(){
  if(!fsReady || pendingPulses==0 || !pendingNonce.length() || !pendingTarget.length()) return false;
  BpPendingSequence next=pendingSequenceState;
  if(!bp_pending_sequence_reserve(&next,pendingPulses,pendingNonce.c_str(),pendingTarget.c_str())) return false;
  return persistPendingSequence(next);
}

bool loadPending(){
  if(!fsReady) return false;
  BpPendingSequence r{}; bool legacy=false;
  const char *chosen=nullptr;
  const bool hasCanonical=LittleFS.exists("/pending.dat");
  const bool hasFresh=LittleFS.exists("/pending.new");
  const bool hasBackup=LittleFS.exists("/pending.bak");
  const uint8_t candidateCount=(hasCanonical?1:0)+(hasFresh?1:0)+(hasBackup?1:0);
  const bool any=candidateCount!=0;
  // Any coexisting candidates may represent different crash commit points.
  // Do not prefer canonical/new/backup by filename: preserve every file and hold intake.
  if(candidateCount > 1){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: multiple pending journal candidates; preserving all files and denying intake.");
    return false;
  }
  if(readPendingFile("/pending.dat",r,legacy)) chosen="/pending.dat";
  else if(readPendingFile("/pending.new",r,legacy)) chosen="/pending.new";
  else if(readPendingFile("/pending.bak",r,legacy)) chosen="/pending.bak";

  if(!chosen){
    if(any){
      fsReady=false;
      pendingReady=true;
      Serial.println("CRITICAL: no valid pending journal candidate; preserving files and denying intake.");
      return false;
    }
    bp_pending_sequence_init(&pendingSequenceState);
    if(!persistPendingSequence(pendingSequenceState)){
      fsReady=false;
      pendingReady=true;
      Serial.println("CRITICAL: initial pending journal write failed; denying intake.");
      return false;
    }
    return true;
  }

  if(strcmp(chosen,"/pending.dat")!=0){
    // A corrupt canonical file plus a fallback is ambiguous. Preserve both;
    // automatic deletion could destroy the only evidence of an older event.
    if(LittleFS.exists("/pending.dat")){
      fsReady=false;
      pendingReady=true;
      Serial.println("CRITICAL: canonical journal conflicts with fallback; preserving all files and denying intake.");
      return false;
    }
    if(!LittleFS.rename(chosen,"/pending.dat")){
      fsReady=false;
      pendingReady=true;
      Serial.println("CRITICAL: pending journal recovery promotion failed; preserving fallback and denying intake.");
      return false;
    }
  }

  // Publish the recovered state only after the canonical file is confirmed.
  pendingSequenceState=r;
  pendingPulses=r.pulses; pendingNonce=String(r.nonce); pendingTarget=String(r.target);
  pendingReady=r.sequence!=0; lastSend=0;
  if(legacy && !persistPendingSequence(r)){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: legacy pending journal migration failed; preserving event and denying intake.");
    return false;
  }
  Serial.println("Recovered unacknowledged coin event from flash.");
  return true;
}

void initPendingStore(){
  fsReady=LittleFS.begin();
  if(!fsReady){
    Serial.println("LittleFS mount failed; preserving Vendo journal and disabling coin relay.");
  }
  if(fsReady && !loadPending()){
    fsReady=false;
    Serial.println("CRITICAL: Vendo sequence journal is corrupt; coin relay will stay disabled.");
  } else if(!fsReady) Serial.println("CRITICAL: coin journal unavailable; coin relay will stay disabled.");
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

// configEeprom.commit() is the persistence result; callers must not report success or reboot on false.
bool beginConfigStore(){
  if(configStoreReady) return true;
  configStoreReady=configEeprom.beginChecked(sizeof(Config));
  return configStoreReady;
}

// EEPROM writes are not usable until begin succeeds; failed commits keep intake denied.
bool saveCfg(){
  if(!beginConfigStore()) return false;
  configEeprom.put(0,cfg);
  if(!configEeprom.commit()){
    configStoreReady=false;
    return false;
  }
  return true;
}

void loadCfg(){
  if(!beginConfigStore()){
    defaults();
    Serial.println("CRITICAL: EEPROM initialization failed; configuration unavailable; coin intake remains denied.");
    return;
  }
  configEeprom.get(0,cfg);
  if(cfg.magic==MAGIC && configStringsTerminated(cfg) &&
     boundedStringLength(cfg.apPass,sizeof(cfg.apPass))>=8) return;

  ConfigV1 oldCfg;
  configEeprom.get(0,oldCfg);
  if(oldCfg.magic==MAGIC_V1 && configV1StringsTerminated(oldCfg)){
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
    if(!saveCfg()) Serial.println("CRITICAL: EEPROM configuration migration write failed; retrying on next boot.");
    else Serial.println("Migrated BlazePwifi Vendo v1 configuration.");
    return;
  }

  defaults();
  if(!saveCfg()) Serial.println("CRITICAL: EEPROM defaults write failed; setup remains available.");
}

void writeLogical(int pin,bool on,bool activeHigh){ digitalWrite(pin,(on==activeHigh)?HIGH:LOW); }

void configureRuntimePins(int coinPin,int relayPin,int ledPin){
  if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);
  if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  // Preload logical OFF before enabling output drivers; LOW can energize active-low relays.
  writeLogical(runRelayPin,false,runRelayActiveHigh);
  writeLogical(runLedPin,false,runLedActiveHigh);
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  writeLogical(runRelayPin,false,runRelayActiveHigh); writeLogical(runLedPin,false,runLedActiveHigh);
}

void denyRemoteControl();
void applyRemoteConfig(const String &response){
  (void)response;
  denyRemoteControl();
}

String signedBody(const String& action,const String& pulses,const String& target,const String& forcedNonce=""){
  if(!strlen(cfg.key) || !strlen(cfg.id)) return String();
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  String base=String(cfg.key)+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  String digest=hexDigest(base);
  if(!validSha256Hex(digest)) return String();
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+digest;
}

String post(const String& action,const String& pulses="0",const String& target="",const String& forcedNonce=""){
  if(action!="register" && action!="poll") return "";
  if(!strlen(cfg.key) || !strlen(cfg.id)) return "";
  if(WiFi.status()!=WL_CONNECTED) return "";
  String body=signedBody(action,pulses,target,forcedNonce);
  if(!body.length()) return "";
  WiFiClient client; HTTPClient h;
  String url="http://"+String(cfg.server)+":4455/cgi-bin/vendo";
  if(!h.begin(client,url)) return "";
  h.setTimeout(3500);
  h.addHeader("Content-Type","application/x-www-form-urlencoded");
  int code=h.POST(body);
  String r=code>0?h.getString():""; h.end(); return r;
}

void pollDenyOnly(){
  // Keep the only synchronous poll boundary deny-only until CORE/QA approve
  // the authenticated response contract. Never return or consume poll data.
  wifiFailures=0;
  denyRemoteControl();
  (void)post("poll");
  denyRemoteControl();
  lastPoll=millis();
}

void applyOutputs(){
  bool accepting=configStoreReady && controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;
  if(ledEnabled) writeLogical(runLedPin,accepting,runLedActiveHigh); else writeLogical(runLedPin,false,runLedActiveHigh);
  if(relayEnabled) writeLogical(runRelayPin,accepting,runRelayActiveHigh); else writeLogical(runRelayPin,false,runRelayActiveHigh);
}

// Register/poll replies are not an approved authenticated control envelope.
// Keep coin, relay and LED outputs denied until CORE publishes that contract
// and QA independently validates the exact producer/consumer vectors.
void denyRemoteControl(){
  controllerEnabled=false;
  coinEnabled=false;
  relayEnabled=false;
  ledEnabled=false;
  insertMode=false;
  activeTarget="";
  applyOutputs();
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

void setupPortal(){
  startSetupAp();

  web.on("/",[](){
    String h="<meta name=viewport content='width=device-width'><h2>BlazePwifi Vendo</h2>"
      "<p>Setup AP is WPA2 protected. Save changes to reboot.</p>"
      "<form method=POST action=/save>SSID <input name=s value='"+String(cfg.ssid)+"'><br>"
      "Password <input name=p type=password><br>Server <input name=server value='"+String(cfg.server)+"'><br>"
      "Vendo key <input name=k type=password><br>ID <input name=id value='"+String(cfg.id)+"'><br>"
      "Coin GPIO <input name=coin value='"+String(cfg.coinPin)+"'><br>"
      "LED GPIO <input name=led value='"+String(cfg.insertLedPin)+"'><br>"
      "Relay GPIO <input name=relay value='"+String(cfg.relayPin)+"'><br><button>Save & reboot</button></form>"
      "<p>STA: "+WiFi.localIP().toString()+"</p>";
    web.send(200,"text/html",h);
  });

  web.on("/save",HTTP_POST,[](){
    String newSsid=web.arg("s"),newPass=web.arg("p").length()?web.arg("p"):String(cfg.pass);
    if(!verifyWifi(newSsid,newPass)){
      web.send(400,"text/plain","Wi-Fi verification failed. Settings were NOT saved. Setup mode remains active.");
      if(strlen(cfg.ssid))WiFi.begin(cfg.ssid,cfg.pass); startSetupAp(); return;
    }
    strlcpy(cfg.ssid,newSsid.c_str(),sizeof(cfg.ssid));strlcpy(cfg.pass,newPass.c_str(),sizeof(cfg.pass));
    strlcpy(cfg.server,web.arg("server").c_str(),sizeof(cfg.server));if(web.arg("k").length())strlcpy(cfg.key,web.arg("k").c_str(),sizeof(cfg.key));strlcpy(cfg.id,web.arg("id").c_str(),sizeof(cfg.id));
    cfg.coinPin=web.arg("coin").toInt();cfg.insertLedPin=web.arg("led").toInt();cfg.relayPin=web.arg("relay").toInt();
    if(!saveCfg()){
      denyRemoteControl();
      web.send(500,"text/plain","EEPROM storage unavailable or commit failed; settings were not confirmed. Setup mode remains active.");
      return;
    }
    web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting...");delay(700);ESP.restart();
  });
  web.begin();
  configuredApSince=millis();
}

void connectSta(){
  if(!configStoreReady || !strlen(cfg.ssid)) return;
  WiFi.begin(cfg.ssid,cfg.pass);
  uint32_t t=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){ delay(250);yield(); }
  if(WiFi.status()==WL_CONNECTED){
    wifiFailures=0;
    (void)post("register");
    denyRemoteControl();
  }
}

bool clearPending(bool committed){
  BpPendingSequence next=pendingSequenceState;
  int ok=committed?bp_pending_sequence_commit(&next):bp_pending_sequence_abandon(&next);
  if(!ok || !persistPendingSequence(next)){
    fsReady=false; pendingReady=true;
    Serial.println("CRITICAL: sequence acknowledgment state failed; coin relay disabled.");
    return false;
  }
  pendingPulses=0; pendingReady=false; pendingNonce=""; pendingTarget=""; lastSend=0;
  return true;
}

void setup(){
  Serial.begin(115200); loadCfg();
  runCoinPin=cfg.coinPin;runLedPin=cfg.insertLedPin;runRelayPin=cfg.relayPin;runCoinActiveLow=cfg.coinActiveLow;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  denyRemoteControl();
  // Keep relay/LED outputs OFF before LittleFS mount and pending-journal recovery.
  initPendingStore();
  setupPortal();connectSta();
}

void loop(){
  web.handleClient();

  if(WiFi.status()!=WL_CONNECTED && configStoreReady && strlen(cfg.ssid) && millis()-lastPoll>8000){
    WiFi.disconnect();WiFi.begin(cfg.ssid,cfg.pass);wifiFailures++;lastPoll=millis();
    if(wifiFailures>=maxWifiRetries)startSetupAp();
  }

  if(WiFi.status()==WL_CONNECTED && configStoreReady && millis()-lastPoll>1500){
    pollDenyOnly();
  }

  bool raw=digitalRead(runCoinPin);
  bool active=runCoinActiveLow?!raw:raw;
  if(insertMode && fsReady && activeTarget.length() && !pendingReady && active && !lastCoin && millis()-lastEdge>runDebounceMs){
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

  // Keep unresolved coin journal entries durable. No automatic coin POST, retry,
  // or clear is allowed until CORE's authenticated receipt/disposition contract
  // is approved and independently verified.

  if(setupApOn && strlen(cfg.ssid) && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){
    WiFi.softAPdisconnect(true);setupApOn=false;
  }

  delay(2);
}
