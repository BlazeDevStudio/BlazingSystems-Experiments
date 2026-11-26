#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <LittleFS.h>
#include <mbedtls/version.h>
#if MBEDTLS_VERSION_MAJOR == 4
#include <psa/crypto.h>
#elif MBEDTLS_VERSION_MAJOR == 3
#include <mbedtls/sha256.h>
#else
#error "Unsupported Mbed TLS major version: BlazePwifi ESP32 supports 3.x and 4.x only"
#endif
#include <esp_system.h>
#include <v060_pending_sequence.h>

struct Config {
  String ssid, pass, server, key, id, apPass;
  int coinPin=27, insertLedPin=2, relayPin=26;
  bool coinActiveLow=true, relayActiveHigh=true, ledActiveHigh=true;
  uint16_t coinDebounceMs=40, pulseGroupMs=400;
};

struct LegacyPendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};

static const uint32_t LEGACY_PENDING_MAGIC=0x42504332;
BpPendingSequence pendingSequenceState;
Config cfg;
Preferences prefs;
WebServer web(80);
bool insertMode=false, lastCoin=false, pendingReady=false, fsReady=false;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
int runCoinPin=27, runLedPin=2, runRelayPin=26, maxWifiRetries=6, wifiFailures=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;
String activeTarget, pendingTarget, pendingNonce, setupApName;

String hexDigest(const String &s){
  unsigned char out[32]; char buf[65];
#if MBEDTLS_VERSION_MAJOR == 4
  // Mbed TLS 4 removes the legacy SHA module API; use the supported PSA one-shot provider.
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

bool validSha256Hex(const String &digest){
  if(digest.length()!=64) return false;
  for(size_t i=0;i<64;i++){
    char c=digest[i];
    if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F'))) return false;
  }
  return true;
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

uint32_t legacyPendingChecksum(const LegacyPendingRecord &r){
  const uint8_t *p=(const uint8_t*)&r; uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(LegacyPendingRecord,checksum);i++){ h^=p[i]; h*=16777619UL; }
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
    LegacyPendingRecord old{}; size_t n=f.readBytes((char*)&old,sizeof(old)); f.close();
    if(n!=sizeof(old) || old.magic!=LEGACY_PENDING_MAGIC || old.pulses==0 ||
       old.pulses>20 || old.checksum!=legacyPendingChecksum(old) ||
       !bp_pending_sequence_hex_token(old.nonce,8,16) ||
       !bp_pending_sequence_hex_token(old.target,8,32)) return false;
    bp_pending_sequence_init(&state); legacy=true;
    return bp_pending_sequence_reserve(&state,old.pulses,old.nonce,old.target);
  }
  f.close(); return false;
}

bool persistPendingSequence(const BpPendingSequence &state){
  if(!fsReady || !bp_pending_sequence_valid(&state)) return false;
  File f=LittleFS.open("/pending.new","w"); if(!f) return false;
  size_t n=f.write((const uint8_t*)&state,sizeof(state)); f.flush(); f.close();
  if(n!=sizeof(state)){ LittleFS.remove("/pending.new"); return false; }
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
  if(!fsReady || pendingPulses==0 || pendingNonce.isEmpty() || pendingTarget.isEmpty()) return false;
  BpPendingSequence next=pendingSequenceState;
  if(!bp_pending_sequence_reserve(&next,pendingPulses,pendingNonce.c_str(),pendingTarget.c_str())) return false;
  return persistPendingSequence(next);
}

bool loadPending(){
  BpPendingSequence r{}; bool legacy=false; const char *chosen=nullptr;
  bool any=LittleFS.exists("/pending.dat") || LittleFS.exists("/pending.new") || LittleFS.exists("/pending.bak");
  if(readPendingFile("/pending.dat",r,legacy)) chosen="/pending.dat";
  else if(readPendingFile("/pending.new",r,legacy)) chosen="/pending.new";
  else if(readPendingFile("/pending.bak",r,legacy)) chosen="/pending.bak";
  if(!chosen){
    if(any) return false;
    bp_pending_sequence_init(&pendingSequenceState);
    return persistPendingSequence(pendingSequenceState);
  }
  pendingSequenceState=r;
  pendingPulses=r.pulses; pendingNonce=String(r.nonce); pendingTarget=String(r.target);
  pendingReady=r.sequence!=0; lastSend=0;
  if(strcmp(chosen,"/pending.dat")!=0){ LittleFS.remove("/pending.dat"); LittleFS.rename(chosen,"/pending.dat"); }
  if(legacy && !persistPendingSequence(r)) return false;
  Serial.println("Recovered unacknowledged coin event from flash.");
  return true;
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

// Preferences put* return zero on failure; this multi-key write is not atomic.
bool saveConfig(){
  bool ok=true;
  if(prefs.putString("ssid",cfg.ssid)==0) ok=false;
  if(prefs.putString("pass",cfg.pass)==0) ok=false;
  if(prefs.putString("server",cfg.server)==0) ok=false;
  if(prefs.putString("key",cfg.key)==0) ok=false;
  if(prefs.putString("id",cfg.id)==0) ok=false;
  if(prefs.putInt("coinpin",cfg.coinPin)==0) ok=false;
  if(prefs.putInt("ledpin",cfg.insertLedPin)==0) ok=false;
  if(prefs.putInt("relaypin",cfg.relayPin)==0) ok=false;
  if(prefs.putBool("coinlow",cfg.coinActiveLow)==0) ok=false;
  if(prefs.putBool("relayhi",cfg.relayActiveHigh)==0) ok=false;
  if(prefs.putBool("ledhi",cfg.ledActiveHigh)==0) ok=false;
  if(prefs.putUInt("debounce",cfg.coinDebounceMs)==0) ok=false;
  if(prefs.putUInt("groupms",cfg.pulseGroupMs)==0) ok=false;
  return ok;
}

void denyRemoteControl();
void applyRemoteConfig(const String &response){
  (void)response;
  denyRemoteControl();
}

String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce=""){
  if(cfg.key.isEmpty() || cfg.id.isEmpty()) return String();
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  String base=cfg.key+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  String digest=hexDigest(base);
  if(!validSha256Hex(digest)) return String();
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+digest;
}

String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce=""){
  if(action!="register" && action!="poll") return "";
  if(cfg.key.isEmpty() || cfg.id.isEmpty()) return "";
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

void applyOutputs(){
  bool accepting=controllerEnabled && coinEnabled && insertMode && fsReady && !pendingReady;
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
      "SSID <input name=s value='"+cfg.ssid+"'><br>WiFi credential <input name=p type=password><br>"
      "Server <input name=server value='"+cfg.server+"'><br>Controller key <input name=k type=password><br>"
      "ID <input name=id value='"+cfg.id+"'><br>Coin GPIO <input name=coin value='"+String(cfg.coinPin)+"'><br>"
      "LED GPIO <input name=led value='"+String(cfg.insertLedPin)+"'><br>Relay GPIO <input name=relay value='"+String(cfg.relayPin)+"'><br>"
      "Debounce ms <input name=db value='"+String(cfg.coinDebounceMs)+"'><br>Pulse group ms <input name=pg value='"+String(cfg.pulseGroupMs)+"'><br>"
      "Coin active low <input name=cl value='"+String(cfg.coinActiveLow?1:0)+"'><br>"
      "Relay active high <input name=rh value='"+String(cfg.relayActiveHigh?1:0)+"'><br>"
      "LED active high <input name=lh value='"+String(cfg.ledActiveHigh?1:0)+"'><br><button>Save & reboot</button></form>";
    web.send(200,"text/html",h);
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
    if(!saveConfig()){
      denyRemoteControl();
      web.send(500,"text/plain","Preferences write failed; settings were not confirmed. Setup mode remains active.");
      return;
    }
    web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting..."); delay(700); ESP.restart();
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
    (void)post("register");
    denyRemoteControl();
  }
}

void setup(){
  Serial.begin(115200); loadConfig();
  runCoinPin=cfg.coinPin; runLedPin=cfg.insertLedPin; runRelayPin=cfg.relayPin;
  runCoinActiveLow=cfg.coinActiveLow; runRelayActiveHigh=cfg.relayActiveHigh; runLedActiveHigh=cfg.ledActiveHigh;
  runDebounceMs=cfg.coinDebounceMs; runPulseGroupMs=cfg.pulseGroupMs;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  denyRemoteControl();

  // Keep relay/LED outputs OFF before LittleFS mount and pending-journal recovery.
  fsReady=LittleFS.begin(false);
  if(fsReady && !loadPending()){
    fsReady=false;
    Serial.println("CRITICAL: Vendo sequence journal is corrupt; coin relay will stay disabled.");
  } else if(!fsReady) Serial.println("CRITICAL: LittleFS unavailable; relay remains disabled.");
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
    // P0: disable the physical coin acceptor before the blocking 3.5s HTTP wait.
    // Keep the poll response discarded until CORE's authenticated contract is approved.
    denyRemoteControl();
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
  // Keep unresolved coin journal entries durable. No automatic coin POST, retry,
  // or clear is allowed until CORE's authenticated receipt/disposition contract
  // is approved and independently verified.
  if(setupApOn && !cfg.ssid.isEmpty() && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){ WiFi.softAPdisconnect(true); setupApOn=false; }
  delay(2);
}
