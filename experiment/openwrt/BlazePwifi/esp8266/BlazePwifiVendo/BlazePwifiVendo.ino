#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <EEPROM.h>
#include <LittleFS.h>
#include <bearssl/bearssl_hash.h>
#include <v060_pending_sequence.h>

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
bool lastCoin=false, pollIntakeSuspended=false;
// PHX-HW-P0: NO trusted response/freshness authority available in Phase A.
// Deliberate availability lockdown, never an operator override.
static constexpr bool kCoinAdmissionEnabled=false;
bool controllerEnabled=false, coinEnabled=false, relayEnabled=false, ledEnabled=false, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
bool pendingReady=false, fsReady=false;
int runCoinPin=4, runLedPin=14, runRelayPin=5, maxWifiRetries=6, wifiFailures=0, remoteRevision=0;
uint16_t runDebounceMs=40, runPulseGroupMs=400;
String activeTarget, pendingTarget, pendingNonce, setupApName;

struct LegacyPendingRecord {
  uint32_t magic;
  uint8_t pulses;
  char nonce[17];
  char target[33];
  uint32_t checksum;
};
const uint32_t LEGACY_PENDING_MAGIC=0x42504331;
BpPendingSequence pendingSequenceState;

String hexDigest(const String &s){
  br_sha256_context c; uint8_t out[32]; char buf[65];
  br_sha256_init(&c); br_sha256_update(&c,s.c_str(),s.length()); br_sha256_out(&c,out);
  for(int i=0;i<32;i++) sprintf(buf+i*2,"%02x",out[i]); buf[64]=0; return String(buf);
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
  BpPendingSequence r; bool legacy=false;
  const char *chosen=nullptr;
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
  if(strcmp(chosen,"/pending.dat")!=0){
    LittleFS.remove("/pending.dat"); LittleFS.rename(chosen,"/pending.dat");
  }
  if(legacy && !persistPendingSequence(r)) return false;
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
  // Drive OLD outputs OFF with OLD polarity before any pinMode or rebind.
  writeLogical(runRelayPin,false,runRelayActiveHigh);
  writeLogical(runLedPin,false,runLedActiveHigh);
  runCoinPin=coinPin; runRelayPin=relayPin; runLedPin=ledPin;
  pinMode(runCoinPin,INPUT_PULLUP); pinMode(runRelayPin,OUTPUT); pinMode(runLedPin,OUTPUT);
  writeLogical(runRelayPin,false,runRelayActiveHigh); writeLogical(runLedPin,false,runLedActiveHigh);
}

void applyRemoteConfig(const String&r){
  (void)r;
  // PHX-HW-P0: unauthenticated HTTP body MUST NOT grant GPIO/coin authority.
  // Drive OLD relay/LED outputs OFF using OLD polarity. Never rebind here.
  writeLogical(runRelayPin,false,runRelayActiveHigh);
  writeLogical(runLedPin,false,runLedActiveHigh);
  controllerEnabled=coinEnabled=relayEnabled=ledEnabled=false;
  insertMode=false;
  activeTarget="";
  // Preserve remoteRevision and all pending/receipt-journal data unchanged.
}

String signedBody(const String& action,const String& pulses,const String& target,const String& forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
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

void applyOutputs(){
  // Do not energize the coin acceptor if the next physical pulse cannot
  // be associated with the selected target and durably journaled.
  bool accepting=kCoinAdmissionEnabled && controllerEnabled && coinEnabled && insertMode && fsReady &&
    !pendingReady && !pollIntakeSuspended && activeTarget.length()!=0 &&
    pendingPulses<20 && (pendingPulses==0 || pendingTarget==activeTarget);
  if(ledEnabled) writeLogical(runLedPin,accepting,runLedActiveHigh); else writeLogical(runLedPin,false,runLedActiveHigh);
  if(relayEnabled) writeLogical(runRelayPin,accepting,runRelayActiveHigh); else writeLogical(runRelayPin,false,runRelayActiveHigh);
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
  if(WiFi.status()==WL_CONNECTED){wifiFailures=0;String r=post("register");applyRemoteConfig(r);}
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
  // PHX-HW-P0: defer LittleFS mount/recovery that may rewrite pending records.
  // fsReady remains false; customer intake and ACK clearing remain forbidden.
  runCoinPin=cfg.coinPin;runLedPin=cfg.insertLedPin;runRelayPin=cfg.relayPin;runCoinActiveLow=cfg.coinActiveLow;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);setupPortal();connectSta();
}

void loop(){
  web.handleClient();

  if(WiFi.status()!=WL_CONNECTED && strlen(cfg.ssid) && millis()-lastPoll>8000){
    WiFi.disconnect();WiFi.begin(cfg.ssid,cfg.pass);wifiFailures++;lastPoll=millis();
    if(wifiFailures>=maxWifiRetries)startSetupAp();
  }

  // Avoid blocking a coin edge or cutting power while a multi-pulse group is still settling.
  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500 &&
     !(pendingPulses && !pendingReady) &&
     (runCoinActiveLow ? digitalRead(runCoinPin) : !digitalRead(runCoinPin))){
    wifiFailures=0;pollIntakeSuspended=true;applyOutputs();String r=post("poll");pollIntakeSuspended=false;applyRemoteConfig(r);applyOutputs();lastPoll=millis();
  }

  bool raw=digitalRead(runCoinPin);
  bool active=runCoinActiveLow?!raw:raw;
  if(kCoinAdmissionEnabled && insertMode && fsReady && activeTarget.length() && !pendingReady && active && !lastCoin && millis()-lastEdge>runDebounceMs){
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
      // A full journal or failed flash reservation must inhibit intake now,
      // not after the next poll or pulse group timeout.
      if(pendingPulses>=20 || !fsReady || pendingReady) applyOutputs();
    }
  }
  lastCoin=active;

  if(pendingPulses && !pendingReady && millis()-lastEdge>runPulseGroupMs){
    pendingReady=true;
    lastSend=0;
    applyOutputs();
  }

  if(kCoinAdmissionEnabled && pendingPulses && pendingReady && WiFi.status()==WL_CONNECTED && (lastSend==0 || millis()-lastSend>900)){
    String r=post("coin",String(pendingPulses),pendingTarget,pendingNonce);
    lastSend=millis();
    if(r.indexOf("\"ok\":true")>=0){
      clearPending(true);
      applyOutputs();
    } else if(r.indexOf("coin window expired")>=0 || r.indexOf("coin target mismatch")>=0 ||
              r.indexOf("no active coin window")>=0 || r.indexOf("another vendo selected")>=0){
      clearPending(false);
      applyOutputs();
    }
  }

  if(setupApOn && strlen(cfg.ssid) && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){
    WiFi.softAPdisconnect(true);setupApOn=false;
  }

  delay(2);
}
