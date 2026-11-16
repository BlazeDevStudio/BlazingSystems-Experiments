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
bool pollIntakeSuspended=false;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
bool runCoinActiveLow=true, runRelayActiveHigh=true, runLedActiveHigh=true;
uint32_t lastPoll=0, lastEdge=0, lastSend=0, configuredApSince=0;
uint8_t pendingPulses=0;
bool pendingReady=false, fsReady=false, journalRecoveryRequired=false;
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
  File f=LittleFS.open(path,"r"); if(!f) return false;
  size_t n=f.readBytes((char*)&r,sizeof(r)); f.close();
  if(n!=sizeof(r) || r.magic!=PENDING_MAGIC || r.pulses==0 || r.pulses>20 ||
     r.checksum!=pendingChecksum(r)) return false;
  // A corrupt record may not terminate either fixed-size string. Never use strlen here.
  const char *nonceEnd=(const char*)memchr(r.nonce,'\0',sizeof(r.nonce));
  const char *targetEnd=(const char*)memchr(r.target,'\0',sizeof(r.target));
  return nonceEnd && targetEnd && (size_t)(nonceEnd-r.nonce)>=8 && (size_t)(targetEnd-r.target)>=8;
}

bool savePending(){
  if(!fsReady || journalRecoveryRequired || pendingPulses==0 || !pendingNonce.length() || !pendingTarget.length()) return false;
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
  const bool hasDat=LittleFS.exists("/pending.dat");
  const bool hasNew=LittleFS.exists("/pending.new");
  const bool hasBak=LittleFS.exists("/pending.bak");
  const unsigned journalCount=(unsigned)hasDat+(unsigned)hasNew+(unsigned)hasBak;
  if(!journalCount) return;
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
  pendingPulses=r.pulses; pendingNonce=String(r.nonce); pendingTarget=String(r.target);
  pendingReady=true; lastSend=0;
  // Do not rename or delete evidence at boot. Clear only after authorized receipt ACK.
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
  return fsReady && !journalRecoveryRequired && pendingReady && pendingPulses>0;
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
  bool accepting=controllerEnabled && coinEnabled && insertMode && fsReady &&
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


bool acceptPollResponse(const String &response){
  bool signatureOk=true;
  if(String(cfg.key).length()){
    String signature=jsonString(response,"response_sig");
    if(signature.length()){
      int insert=jsonTrue(response,"insert")?1:0;
      String target=jsonString(response,"target_nonce");
      int expires=jsonInt(response,"expires",0);
      String expected=hexDigest(String(cfg.key)+"|poll|"+String(cfg.id)+"|"+lastSentNonce+"|"+String(insert)+"|"+target+"|"+String(expires)+"|"+String(cfg.key));
      signatureOk=signature.equalsIgnoreCase(expected);
    } else {
      signatureOk=false;
    }
  }
  if(!signatureOk || response.indexOf("\\"ok\\":true")<0){
    // Never reuse the previous positive poll after an empty, rejected or
    // unauthenticated reply. Keep the acceptor disabled until a fresh poll
    // explicitly authorizes intake.
    insertMode=false;
    activeTarget="";
    return false;
  }
  insertMode=jsonTrue(response,"insert");
  activeTarget=jsonString(response,"target_nonce");
  applyRemoteConfig(response);
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
    if(fsReady && LittleFS.exists("/quarantine.log")) LittleFS.remove("/quarantine.log");
    web.send(200,"text/plain","Quarantine log cleared.\n");
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
  if(WiFi.status()==WL_CONNECTED){
    wifiFailures=0;String r=post("register");
    bool sigOk=true;
    if(strlen(cfg.key)){
      String sig=jsonString(r,"response_sig");
      if(sig.length()){
        int st=jsonInt(r,"server_time",0);
        String expected=hexDigest(String(cfg.key)+"|register|"+String(cfg.id)+"|"+lastSentNonce+"|"+String(st)+"|"+String(cfg.key));
        sigOk=sig.equalsIgnoreCase(expected);
      } else {
        sigOk=false;
      }
    }
    if(sigOk && r.indexOf("\"ok\":true")>=0) applyRemoteConfig(r);
  }
}

void clearPending(){
  if(journalRecoveryRequired) return; // Never erase ambiguous unpaid coin evidence.
  pendingPulses=0; pendingReady=false; pendingNonce=""; pendingTarget=""; lastSend=0;
  if(fsReady){
    LittleFS.remove("/pending.dat");
    LittleFS.remove("/pending.new");
    LittleFS.remove("/pending.bak");
  }
}

static const size_t QUARANTINE_MAX_BYTES=32768;

bool appendQuarantineRecord(const String &reason){
  if(!fsReady || pendingPulses==0) return false;

  char record[320];
  int len=snprintf(record,sizeof(record),
                   "TIME=%lu PULSES=%u NONCE=%s TARGET=%s REASON=%s\n",
                   (unsigned long)millis(), (unsigned int)pendingPulses,
                   pendingNonce.c_str(), pendingTarget.c_str(), reason.c_str());
  if(len<=0 || (size_t)len>=sizeof(record)) return false;

  size_t before=0;
  if(LittleFS.exists("/quarantine.log")){
    File prior=LittleFS.open("/quarantine.log","r");
    if(!prior) return false;
    before=prior.size();
    prior.close();
  }
  if(before+(size_t)len>QUARANTINE_MAX_BYTES) return false;

  File q=LittleFS.open("/quarantine.log","a");
  if(!q) return false;
  size_t written=q.write((const uint8_t*)record,(size_t)len);
  q.flush();
  q.close();
  if(written!=(size_t)len) return false;

  File verify=LittleFS.open("/quarantine.log","r");
  if(!verify) return false;
  size_t after=verify.size();
  bool verified=after==before+(size_t)len &&
                verify.seek(before,SeekSet);
  for(size_t i=0;verified && i<(size_t)len;++i){
    if(verify.read()!=(unsigned char)record[i]) verified=false;
  }
  verify.close();
  // Exact byte readback detects same-size corruption before clearing pending.
  // It is NOT proof of durability across a real flash power cut.
  return verified;
}

bool quarantinePending(const String &reason){
  if(!appendQuarantineRecord(reason)){
    Serial.println("CRITICAL: quarantine journal commit failed; pending coin retained and relay disabled.");
    return false;
  }
  Serial.println("QUARANTINE: uncredited coin event preserved in flash: "+reason);
  clearPending();
  return true;
}

void setup(){
  Serial.begin(115200); loadCfg(); initPendingStore();
  runCoinPin=cfg.coinPin;runLedPin=cfg.insertLedPin;runRelayPin=cfg.relayPin;runCoinActiveLow=cfg.coinActiveLow;
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

  if(canAttemptCoinPost() && WiFi.status()==WL_CONNECTED && (lastSend==0 || millis()-lastSend>900)){
    String r=post("coin",String(pendingPulses),pendingTarget,pendingNonce);
    lastSend=millis();
    if(r.indexOf("\"ok\":true")>=0){
      clearPending();
      applyOutputs();
    } else if(r.indexOf("coin window expired")>=0 || r.indexOf("coin target mismatch")>=0 ||
              r.indexOf("no active coin window")>=0 || r.indexOf("another vendo selected")>=0){
      quarantinePending(r);
      applyOutputs();
    }
  }

  if(setupApOn && strlen(cfg.ssid) && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){
    WiFi.softAPdisconnect(true);setupApOn=false;
  }

  delay(2);
}
