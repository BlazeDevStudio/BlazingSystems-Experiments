#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <EEPROM.h>
#include <LittleFS.h>
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
bool controllerEnabled=false, coinEnabled=false, relayEnabled=false, ledEnabled=false, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
bool pendingReady=false, fsReady=false;
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
  File f=LittleFS.open(path,"r");
  if(!f) return false;
  const size_t storedSize=f.size();
  const size_t n=f.readBytes((char*)&r,sizeof(r));
  f.close();

  if(storedSize!=sizeof(r) || n!=sizeof(r) ||
     r.magic!=PENDING_MAGIC || r.pulses==0 || r.pulses>20 ||
     r.checksum!=pendingChecksum(r)) return false;

  const char *nonceEnd=(const char*)memchr(r.nonce,'\0',sizeof(r.nonce));
  const char *targetEnd=(const char*)memchr(r.target,'\0',sizeof(r.target));
  if(!nonceEnd || !targetEnd) return false;

  const size_t nonceLength=(size_t)(nonceEnd-r.nonce);
  const size_t targetLength=(size_t)(targetEnd-r.target);
  if(nonceLength<8 || targetLength<8) return false;

  for(const char *p=nonceEnd+1;p<r.nonce+sizeof(r.nonce);++p){
    if(*p!='\0') return false;
  }
  for(const char *p=targetEnd+1;p<r.target+sizeof(r.target);++p){
    if(*p!='\0') return false;
  }
  return true;
}

bool savePending(){
  if(!fsReady || pendingPulses==0 || !pendingNonce.length() || !pendingTarget.length()) return false;
  PendingRecord r; memset(&r,0,sizeof(r)); r.magic=PENDING_MAGIC; r.pulses=pendingPulses;
  strlcpy(r.nonce,pendingNonce.c_str(),sizeof(r.nonce));
  strlcpy(r.target,pendingTarget.c_str(),sizeof(r.target));
  r.checksum=pendingChecksum(r);
  File f=LittleFS.open("/pending.new","w"); if(!f) return false;
  size_t n=f.write((const uint8_t*)&r,sizeof(r)); f.flush(); f.close();
  if(n!=sizeof(r)){LittleFS.remove("/pending.new");return false;}
  LittleFS.remove("/pending.bak");
  if(LittleFS.exists("/pending.dat")) LittleFS.rename("/pending.dat","/pending.bak");
  if(!LittleFS.rename("/pending.new","/pending.dat")){
    if(LittleFS.exists("/pending.bak")) LittleFS.rename("/pending.bak","/pending.dat");
    return false;
  }
  LittleFS.remove("/pending.bak");
  return true;
}

void loadPending(){
  if(!fsReady) return;

  const char *paths[]={"/pending.dat","/pending.new","/pending.bak"};
  const char *candidate=nullptr;
  size_t candidateCount=0;
  for(const char *path:paths){
    if(LittleFS.exists(path)){
      candidate=path;
      ++candidateCount;
    }
  }
  if(candidateCount==0) return;
  if(candidateCount!=1){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: multiple pending journal candidates; preserving all files and denying intake until reconciliation.");
    return;
  }

  PendingRecord r{};
  if(!readPendingFile(candidate,r)){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: pending journal candidate is invalid; preserving file and denying intake until reconciliation.");
    return;
  }

  pendingPulses=r.pulses;
  pendingNonce=String(r.nonce);
  pendingTarget=String(r.target);
  pendingReady=true;
  lastSend=0;
  Serial.println("Recovered unacknowledged coin event from flash; source candidate retained.");
}

void initPendingStore(){
  // A mount failure can hide an uncredited pending event. Never format here.
  // Keep the journal unavailable and outputs denied until an explicit recovery.
  fsReady=LittleFS.begin();
  if(fsReady) loadPending();
  else Serial.println("CRITICAL: LittleFS mount failed; automatic format is disabled to preserve pending coin evidence; relay remains disabled.");
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

void loadCfg(){
  EEPROM.begin(sizeof(Config));
  EEPROM.get(0,cfg);
  if(cfg.magic==MAGIC && strlen(cfg.apPass)>=8) return;

  ConfigV1 oldCfg;
  EEPROM.get(0,oldCfg);
  if(oldCfg.magic==MAGIC_V1){
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

void configureRuntimePins(int coinPin,int relayPin,int ledPin){
  if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);
  if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  writeLogical(runRelayPin,false,runRelayActiveHigh); writeLogical(runLedPin,false,runLedActiveHigh);
}

// Retained for a future separately authenticated configuration envelope only.
// Master Architecture Contracts §6.4 forbids calling this from register/poll.
void applyRemoteConfig(const String&r){
  int rev=jsonInt(r,"config_revision",remoteRevision);
  if(rev==remoteRevision && remoteRevision!=0)return;
  controllerEnabled=jsonInt(r,"enabled",1)!=0; coinEnabled=jsonInt(r,"coin_enabled",1)!=0;
  relayEnabled=jsonInt(r,"relay_enabled",1)!=0; ledEnabled=jsonInt(r,"led_enabled",1)!=0;
  int cp=jsonInt(r,"coin_pin",-1),rp=jsonInt(r,"relay_pin",-1),lp=jsonInt(r,"led_pin",-1);
  int nextCoin=(cp>=0&&cp<=16)?cp:cfg.coinPin, nextRelay=(rp>=0&&rp<=16)?rp:cfg.relayPin, nextLed=(lp>=0&&lp<=16)?lp:cfg.insertLedPin;
  runCoinActiveLow=jsonInt(r,"coin_active_low",cfg.coinActiveLow?1:0)!=0;
  runRelayActiveHigh=jsonInt(r,"relay_active_high",1)!=0; runLedActiveHigh=jsonInt(r,"led_active_high",1)!=0;
  runDebounceMs=(uint16_t)constrain(jsonInt(r,"coin_debounce_ms",40),1,2000);
  runPulseGroupMs=(uint16_t)constrain(jsonInt(r,"pulse_group_ms",400),10,10000);
  maxWifiRetries=constrain(jsonInt(r,"max_wifi_retries",6),1,60);
  configureRuntimePins(nextCoin,nextRelay,nextLed); remoteRevision=rev; applyOutputs();
}

String lastSentNonce;

String signedBody(const String& action,const String& pulses,const String& target,const String& forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  lastSentNonce=n;
  String base=String(cfg.key)+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+hexDigest(base);
}

String post(const String& action,const String& pulses="0",const String& target="",const String& forcedNonce=""){
  // Master §6.6 requires an event-bound authenticated receipt/disposition.
  // Until PHX-CORE publishes it and PHX-QA verifies vectors, only discovery
  // and poll requests may leave this controller; coin/unknown actions are denied.
  if(action!="register" && action!="poll"){
    Serial.println("Denied controller POST action; coin receipt contract is not approved.");
    return "";
  }
  if(WiFi.status()!=WL_CONNECTED) return "";
  WiFiClient client; HTTPClient h;
  String url="http://"+String(cfg.server)+":4455/cgi-bin/vendo";
  if(!h.begin(client,url)) return "";
  h.setTimeout(3500);
  h.addHeader("Content-Type","application/x-www-form-urlencoded");
  int code=h.POST(signedBody(action,pulses,target,forcedNonce));
  String r=code>0?h.getString():""; h.end(); return r;
}

void applyOutputs(){
  bool accepting=controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;
  if(ledEnabled) writeLogical(runLedPin,accepting,runLedActiveHigh); else writeLogical(runLedPin,false,runLedActiveHigh);
  if(relayEnabled) writeLogical(runRelayPin,accepting,runRelayActiveHigh); else writeLogical(runRelayPin,false,runRelayActiveHigh);
}

// No poll/register response currently carries an approved control envelope.
// Keep every actuation flag denied until PHX-CORE publishes the contract and
// PHX-QA verifies its positive/negative vectors at the exact shared source SHAs.
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
    // Master Architecture Contracts §6.5: quarantine evidence is not remotely deletable.
    web.send(403,"text/plain","Quarantine records are retained until authenticated reconciliation.\n");
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
    saveCfg();web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting...");delay(700);ESP.restart();
  });
  web.begin();
  configuredApSince=millis();
}

void connectSta(){
  if(!strlen(cfg.ssid)) return;
  WiFi.begin(cfg.ssid,cfg.pass);
  uint32_t t=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){ delay(250);yield(); }
  if(WiFi.status()==WL_CONNECTED){
    wifiFailures=0;
    // Register/ping is discovery only. response_sig / the derived |register|
    // tuple does not authenticate the returned configuration object.
    (void)post("register");
    denyRemoteControl();
  }
}

bool clearPending(){
  if(!fsReady || pendingPulses==0 || pendingPulses>20 ||
     pendingNonce.length()<8 || pendingNonce.length()>16 ||
     pendingTarget.length()<8 || pendingTarget.length()>32){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: pending clear preconditions are invalid; event retained and intake disabled.");
    return false;
  }

  const char *paths[]={"/pending.dat","/pending.new","/pending.bak"};
  const char *candidatePath=nullptr;
  unsigned candidateCount=0;
  for(const char *path:paths){
    if(LittleFS.exists(path)){
      candidatePath=path;
      ++candidateCount;
    }
  }
  if(candidateCount!=1 || !candidatePath){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: exactly one pending journal is required before quarantine clear; preserving all candidates.");
    return false;
  }

  PendingRecord durable{};
  if(!readPendingFile(candidatePath,durable) ||
     durable.pulses!=pendingPulses ||
     strcmp(durable.nonce,pendingNonce.c_str())!=0 ||
     strcmp(durable.target,pendingTarget.c_str())!=0){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: pending journal does not match the quarantined RAM event; preserving evidence.");
    return false;
  }

  if(!LittleFS.remove(candidatePath) || LittleFS.exists(candidatePath)){
    fsReady=false;
    pendingReady=true;
    Serial.println("CRITICAL: pending journal deletion was not verified; preserving RAM event and disabling intake.");
    return false;
  }

  pendingPulses=0;
  pendingReady=false;
  pendingNonce="";
  pendingTarget="";
  lastSend=0;
  return true;
}

static const size_t QUARANTINE_MAX_BYTES=32768;

uint32_t quarantineCrc32Update(uint32_t crc,uint8_t value){
  crc^=value;
  for(uint8_t bit=0;bit<8;bit++)
    crc=(crc&1U)?((crc>>1)^0xEDB88320UL):(crc>>1);
  return crc;
}

// CRC32 detects accidental same-size corruption only; it is not authentication,
// a protected freshness witness, or proof of flash durability across power loss.
bool fingerprintQuarantinePrefix(size_t &length,uint32_t &fingerprint){
  length=0;
  fingerprint=0;
  if(!LittleFS.exists("/quarantine.log")) return true;
  File prior=LittleFS.open("/quarantine.log","r");
  if(!prior) return false;
  length=prior.size();
  if(length>QUARANTINE_MAX_BYTES){ prior.close(); return false; }
  uint32_t crc=0xFFFFFFFFUL;
  for(size_t i=0;i<length;i++){
    int value=prior.read();
    if(value<0){ prior.close(); return false; }
    crc=quarantineCrc32Update(crc,(uint8_t)value);
  }
  bool complete=prior.available()==0;
  prior.close();
  if(!complete) return false;
  fingerprint=~crc;
  return true;
}

bool verifyQuarantineAppend(size_t before,uint32_t beforeFingerprint,
                            const char *record,size_t len){
  File verify=LittleFS.open("/quarantine.log","r");
  if(!verify) return false;
  size_t after=verify.size();
  if(!(after==before+(size_t)len)){ verify.close(); return false; }
  uint32_t crc=0xFFFFFFFFUL;
  for(size_t i=0;i<before;i++){
    int value=verify.read();
    if(value<0){ verify.close(); return false; }
    crc=quarantineCrc32Update(crc,(uint8_t)value);
  }
  if((~crc)!=beforeFingerprint){ verify.close(); return false; }
  for(size_t i=0;i<len;i++){
    int value=verify.read();
    if(value<0 || (uint8_t)value!=(uint8_t)record[i]){
      verify.close();
      return false;
    }
  }
  bool complete=verify.available()==0;
  verify.close();
  return complete;
}

bool appendQuarantineRecord(const String &reason){
  if(!fsReady || pendingPulses==0) return false;

  char record[320];
  int len=snprintf(record,sizeof(record),
                   "TIME=%lu PULSES=%u NONCE=%s TARGET=%s REASON=%s\n",
                   (unsigned long)millis(),(unsigned int)pendingPulses,
                   pendingNonce.c_str(),pendingTarget.c_str(),reason.c_str());
  if(len<=0 || (size_t)len>=sizeof(record)) return false;

  size_t before=0;
  uint32_t beforeFingerprint=0;
  if(!fingerprintQuarantinePrefix(before,beforeFingerprint)) return false;
  if(before+(size_t)len>QUARANTINE_MAX_BYTES) return false;

  File q=LittleFS.open("/quarantine.log","a");
  if(!q) return false;
  size_t written=q.write((const uint8_t*)record,(size_t)len);
  q.flush();
  q.close();
  if(written!=(size_t)len) return false;
  return verifyQuarantineAppend(before,beforeFingerprint,record,(size_t)len);
}

bool quarantinePending(const String &reason){
  if(!appendQuarantineRecord(reason)){
    Serial.println("CRITICAL: quarantine journal commit failed; pending coin retained and relay disabled.");
    return false;
  }
  Serial.println("QUARANTINE: uncredited coin event preserved in flash: "+reason);
  return clearPending();
}

void setup(){
  Serial.begin(115200); loadCfg(); initPendingStore();
  runCoinPin=cfg.coinPin;runLedPin=cfg.insertLedPin;runRelayPin=cfg.relayPin;runCoinActiveLow=cfg.coinActiveLow;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);denyRemoteControl();setupPortal();connectSta();
}

void loop(){
  web.handleClient();

  if(WiFi.status()!=WL_CONNECTED && strlen(cfg.ssid) && millis()-lastPoll>8000){
    WiFi.disconnect();WiFi.begin(cfg.ssid,cfg.pass);wifiFailures++;lastPoll=millis();
    if(wifiFailures>=maxWifiRetries)startSetupAp();
  }

  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500){
    wifiFailures=0;
    // HW-P0: de-energize the coin acceptor before the synchronous HTTP wait.
    // Keep this deny-only until CORE's authenticated poll contract is approved.
    denyRemoteControl();
    // Current main poll replies have no response_sig. The derived |poll|
    // candidate is not an approved producer/consumer contract; ignore all fields.
    (void)post("poll");
    denyRemoteControl();
    lastPoll=millis();
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

  // No automatic coin POST, retry, or clear is permitted until the
  // event-bound authenticated receipt/disposition contract is approved.
  // Keep recovered/pending journal evidence for operator/CORE reconciliation.

  if(setupApOn && strlen(cfg.ssid) && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){
    WiFi.softAPdisconnect(true);setupApOn=false;
  }

  delay(2);
}
