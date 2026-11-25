#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <LittleFS.h>
#include <mbedtls/sha256.h>
#include <esp_system.h>

struct Config {
  String ssid, pass, server, key, id, apPass;
  int coinPin=27, insertLedPin=2, relayPin=26;
  bool coinActiveLow=true, relayActiveHigh=true, ledActiveHigh=true;
  uint16_t coinDebounceMs=40, pulseGroupMs=400;
};

struct PendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};

static const uint32_t PENDING_MAGIC=0x42504332;
Config cfg;
Preferences prefs;
WebServer web(80);
bool insertMode=false, lastCoin=false, pendingReady=false, fsReady=false;
bool controllerEnabled=false, coinEnabled=false, relayEnabled=false, ledEnabled=false, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
int runCoinPin=27, runLedPin=2, runRelayPin=26, maxWifiRetries=6, wifiFailures=0, remoteRevision=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;
String activeTarget, pendingTarget, pendingNonce, setupApName;

String hexDigest(const String &s){
  unsigned char out[32]; char buf[65];
  mbedtls_sha256_context c;
  mbedtls_sha256_init(&c);
  mbedtls_sha256_starts(&c,0);
  mbedtls_sha256_update(&c,(const unsigned char*)s.c_str(),s.length());
  mbedtls_sha256_finish(&c,out);
  mbedtls_sha256_free(&c);
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
  if(!fsReady || pendingPulses==0 || pendingNonce.isEmpty() || pendingTarget.isEmpty()) return false;
  PendingRecord r{}; r.magic=PENDING_MAGIC; r.pulses=pendingPulses;
  strlcpy(r.nonce,pendingNonce.c_str(),sizeof(r.nonce));
  strlcpy(r.target,pendingTarget.c_str(),sizeof(r.target));
  r.checksum=pendingChecksum(r);
  File f=LittleFS.open("/pending.new","w"); if(!f) return false;
  size_t n=f.write((const uint8_t*)&r,sizeof(r)); f.flush(); f.close();
  if(n!=sizeof(r)){ LittleFS.remove("/pending.new"); return false; }
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

void loadConfig(){
  prefs.begin("blazevendo",false);
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
  cfg.relayActiveHigh=prefs.getBool("relayhi",true);
  cfg.ledActiveHigh=prefs.getBool("ledhi",true);
  cfg.coinDebounceMs=(uint16_t)prefs.getUInt("debounce",40);
  cfg.pulseGroupMs=(uint16_t)prefs.getUInt("groupms",400);
  if(cfg.apPass.length()<8){
    char b[17]; snprintf(b,sizeof(b),"%08lX%08lX",(unsigned long)esp_random(),(unsigned long)esp_random());
    cfg.apPass=String(b); prefs.putString("appass",cfg.apPass);
  }
}

void saveConfig(){
  prefs.putString("ssid",cfg.ssid); prefs.putString("pass",cfg.pass);
  prefs.putString("server",cfg.server); prefs.putString("key",cfg.key); prefs.putString("id",cfg.id);
  prefs.putInt("coinpin",cfg.coinPin); prefs.putInt("ledpin",cfg.insertLedPin); prefs.putInt("relaypin",cfg.relayPin);
  prefs.putBool("coinlow",cfg.coinActiveLow); prefs.putBool("relayhi",cfg.relayActiveHigh); prefs.putBool("ledhi",cfg.ledActiveHigh);
  prefs.putUInt("debounce",cfg.coinDebounceMs); prefs.putUInt("groupms",cfg.pulseGroupMs);
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

void configureRuntimePins(int coinPin,int relayPin,int ledPin){
  if(runLedPin!=ledPin) writeLogical(runLedPin,false,runLedActiveHigh);
  if(runRelayPin!=relayPin) writeLogical(runRelayPin,false,runRelayActiveHigh);
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  writeLogical(runRelayPin,false,runRelayActiveHigh); writeLogical(runLedPin,false,runLedActiveHigh);
}

// Retained for a future separately authenticated configuration envelope only.
// Master Architecture Contracts §6.4 forbids calling this from register/poll.
void applyRemoteConfig(const String &r){
  int rev=jsonInt(r,"config_revision",remoteRevision);
  if(rev==remoteRevision && remoteRevision!=0) return;
  controllerEnabled=jsonInt(r,"enabled",1)!=0;
  coinEnabled=jsonInt(r,"coin_enabled",1)!=0;
  relayEnabled=jsonInt(r,"relay_enabled",1)!=0;
  ledEnabled=jsonInt(r,"led_enabled",1)!=0;
  int cp=jsonInt(r,"coin_pin",-1), rp=jsonInt(r,"relay_pin",-1), lp=jsonInt(r,"led_pin",-1);
  int nextCoin=(cp>=0&&cp<=39)?cp:cfg.coinPin;
  int nextRelay=(rp>=0&&rp<=39)?rp:cfg.relayPin;
  int nextLed=(lp>=0&&lp<=39)?lp:cfg.insertLedPin;
  runCoinActiveLow=jsonInt(r,"coin_active_low",cfg.coinActiveLow?1:0)!=0;
  runRelayActiveHigh=jsonInt(r,"relay_active_high",cfg.relayActiveHigh?1:0)!=0;
  runLedActiveHigh=jsonInt(r,"led_active_high",cfg.ledActiveHigh?1:0)!=0;
  int db=jsonInt(r,"coin_debounce_ms",cfg.coinDebounceMs), pg=jsonInt(r,"pulse_group_ms",cfg.pulseGroupMs), mr=jsonInt(r,"max_wifi_retries",6);
  runDebounceMs=(uint16_t)constrain(db,1,2000); runPulseGroupMs=(uint16_t)constrain(pg,10,10000); maxWifiRetries=constrain(mr,1,60);
  configureRuntimePins(nextCoin,nextRelay,nextLed); remoteRevision=rev; applyOutputs();
}

String lastSentNonce;

String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  lastSentNonce=n;
  String base=cfg.key+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+hexDigest(base);
}

String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce=""){
  // Master §6.6 requires an event-bound authenticated receipt/disposition.
  // Until PHX-CORE publishes it and PHX-QA verifies vectors, only discovery
  // and poll requests may leave this controller; coin/unknown actions are denied.
  if(action!="register" && action!="poll"){
    Serial.println("Denied controller POST action; coin receipt contract is not approved.");
    return "";
  }
  if(WiFi.status()!=WL_CONNECTED) return "";
  WiFiClient client; HTTPClient h;
  String url="http://"+cfg.server+":4455/cgi-bin/vendo";
  if(!h.begin(client,url)) return "";
  h.setTimeout(3500); h.addHeader("Content-Type","application/x-www-form-urlencoded");
  int code=h.POST(signedBody(action,pulses,target,forcedNonce));
  String r=code>0?h.getString():""; h.end(); return r;
}

void writeLogical(int pin,bool on,bool activeHigh){ digitalWrite(pin,(on==activeHigh)?HIGH:LOW); }
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

void setupPortal(){
  startSetupAp();
  web.on("/",[](){
    String h="<meta name=viewport content='width=device-width'><h2>BlazePwifi ESP32 Vendo</h2><form method=POST action=/save>"
      "SSID <input name=s value='"+htmlEsc(cfg.ssid)+"'><br>WiFi credential <input name=p type=password><br>"
      "Server <input name=server value='"+htmlEsc(cfg.server)+"'><br>Controller key <input name=k type=password><br>"
      "ID <input name=id value='"+htmlEsc(cfg.id)+"'><br>Coin GPIO <input name=coin value='"+String(cfg.coinPin)+"'><br>"
      "LED GPIO <input name=led value='"+String(cfg.insertLedPin)+"'><br>Relay GPIO <input name=relay value='"+String(cfg.relayPin)+"'><br>"
      "Debounce ms <input name=db value='"+String(cfg.coinDebounceMs)+"'><br>Pulse group ms <input name=pg value='"+String(cfg.pulseGroupMs)+"'><br>"
      "Coin active low <input name=cl value='"+String(cfg.coinActiveLow?1:0)+"'><br>"
      "Relay active high <input name=rh value='"+String(cfg.relayActiveHigh?1:0)+"'><br>"
      "LED active high <input name=lh value='"+String(cfg.ledActiveHigh?1:0)+"'><br><button>Save & reboot</button></form>"
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
    String newSsid=web.arg("s"), newPass=web.arg("p").length()?web.arg("p"):cfg.pass;
    if(!verifyWifi(newSsid,newPass)){
      web.send(400,"text/plain","Wi-Fi verification failed. Settings were NOT saved. Setup mode remains active.");
      if(!cfg.ssid.isEmpty()) WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str());
      startSetupAp(); return;
    }
    cfg.ssid=newSsid; cfg.pass=newPass; cfg.server=web.arg("server"); if(web.arg("k").length()) cfg.key=web.arg("k"); cfg.id=web.arg("id");
    cfg.coinPin=web.arg("coin").toInt(); cfg.insertLedPin=web.arg("led").toInt(); cfg.relayPin=web.arg("relay").toInt();
    long db=web.arg("db").toInt(), pg=web.arg("pg").toInt(); if(db<1)db=1;if(db>2000)db=2000;if(pg<10)pg=10;if(pg>10000)pg=10000;
    cfg.coinDebounceMs=(uint16_t)db; cfg.pulseGroupMs=(uint16_t)pg; cfg.coinActiveLow=web.arg("cl")!="0"; cfg.relayActiveHigh=web.arg("rh")!="0"; cfg.ledActiveHigh=web.arg("lh")!="0";
    saveConfig(); web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting..."); delay(700); ESP.restart();
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
    // Register/ping is discovery only. response_sig / the derived |register|
    // tuple does not authenticate the returned configuration object.
    (void)post("register");
    denyRemoteControl();
  }
}

void initPendingStore(){
  // A mount failure can hide an uncredited pending event. Never format here.
  // Keep the journal unavailable and outputs denied until an explicit recovery.
  fsReady=LittleFS.begin();
  if(fsReady) loadPending();
  else Serial.println("CRITICAL: LittleFS mount failed; automatic format is disabled to preserve pending coin evidence; relay remains disabled.");
}

void setup(){
  Serial.begin(115200); loadConfig();
  initPendingStore();
  runCoinPin=cfg.coinPin; runLedPin=cfg.insertLedPin; runRelayPin=cfg.relayPin;
  runCoinActiveLow=cfg.coinActiveLow; runRelayActiveHigh=cfg.relayActiveHigh; runLedActiveHigh=cfg.ledActiveHigh;
  runDebounceMs=cfg.coinDebounceMs; runPulseGroupMs=cfg.pulseGroupMs;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  denyRemoteControl();
  setupPortal(); connectSta();
}

void loop(){
  web.handleClient();
  if(WiFi.status()!=WL_CONNECTED && !cfg.ssid.isEmpty() && millis()-lastPoll>8000){
    WiFi.disconnect(); WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str()); wifiFailures++; lastPoll=millis();
    if(wifiFailures>=maxWifiRetries) startSetupAp();
  }
  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500){
    wifiFailures=0;
    // Suspend intake before the synchronous request; the loop cannot sample
    // coin edges while HTTPClient is blocked. Keep the post-poll deny as well.
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
    if(pendingPulses==0){ pendingNonce=freshNonce(); pendingTarget=activeTarget; }
    if(pendingTarget==activeTarget && pendingPulses<20){
      pendingPulses++; lastEdge=millis();
      if(!savePending()){ fsReady=false; pendingReady=true; Serial.println("CRITICAL: pending journal write failed; relay disabled."); }
    }
  }
  lastCoin=active;
  if(pendingPulses && !pendingReady && millis()-lastEdge>runPulseGroupMs){ pendingReady=true; lastSend=0; applyOutputs(); }
  // No automatic coin POST, retry, or clear is permitted until the
  // event-bound authenticated receipt/disposition contract is approved.
  // Keep recovered/pending journal evidence for operator/CORE reconciliation.
  if(setupApOn && !cfg.ssid.isEmpty() && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){ WiFi.softAPdisconnect(true); setupApOn=false; }
  delay(2);
}
