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
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true, setupApOn=false;
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

uint32_t pendingChecksum(const PendingRecord &r){
  const uint8_t *p=(const uint8_t*)&r; uint32_t h=2166136261UL;
  for(size_t i=0;i<offsetof(PendingRecord,checksum);i++){ h^=p[i]; h*=16777619UL; }
  return h;
}

bool readPendingFile(const char *path, PendingRecord &r){
  if(!fsReady || !LittleFS.exists(path)) return false;
  File f=LittleFS.open(path,"r"); if(!f) return false;
  size_t n=f.readBytes((char*)&r,sizeof(r)); f.close();
  return n==sizeof(r) && r.magic==PENDING_MAGIC && r.pulses>0 && r.pulses<=20 &&
         r.checksum==pendingChecksum(r) && strlen(r.nonce)>=8 && strlen(r.target)>=8;
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
  PendingRecord r{}; const char *chosen=nullptr;
  if(readPendingFile("/pending.dat",r)) chosen="/pending.dat";
  else if(readPendingFile("/pending.new",r)) chosen="/pending.new";
  else if(readPendingFile("/pending.bak",r)) chosen="/pending.bak";
  if(!chosen) return;
  pendingPulses=r.pulses; pendingNonce=String(r.nonce); pendingTarget=String(r.target);
  pendingReady=true; lastSend=0;
  if(strcmp(chosen,"/pending.dat")!=0){ LittleFS.remove("/pending.dat"); LittleFS.rename(chosen,"/pending.dat"); }
  Serial.println("Recovered unacknowledged coin event from flash.");
}

void clearPending(){
  pendingPulses=0; pendingReady=false; pendingNonce=""; pendingTarget=""; lastSend=0;
  if(fsReady){ LittleFS.remove("/pending.dat"); LittleFS.remove("/pending.new"); LittleFS.remove("/pending.bak"); }
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

String signedBody(const String &action,const String &pulses,const String &target,const String &forcedNonce=""){
  String n=forcedNonce.length()?forcedNonce:freshNonce();
  String base=cfg.key+"|"+action+"|"+cfg.id+"|"+n+"|"+pulses+"|"+target+"|"+cfg.key;
  return "action="+action+"&id="+esc(cfg.id)+"&nonce="+n+"&pulses="+pulses+"&target="+esc(target)+"&sig="+hexDigest(base);
}

String post(const String &action,const String &pulses="0",const String &target="",const String &forcedNonce=""){
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
    saveConfig(); web.send(200,"text/plain","Wi-Fi verified and settings saved. Rebooting..."); delay(700); ESP.restart();
  });
  web.begin(); configuredApSince=millis();
}

void connectSta(){
  if(cfg.ssid.isEmpty()) return;
  WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str());
  uint32_t t=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-t<12000){ delay(250); }
  if(WiFi.status()==WL_CONNECTED){ wifiFailures=0; String r=post("register"); applyRemoteConfig(r); }
}

void setup(){
  Serial.begin(115200); loadConfig();
  fsReady=LittleFS.begin(true); if(fsReady) loadPending();
  else Serial.println("CRITICAL: LittleFS unavailable; relay remains disabled.");
  runCoinPin=cfg.coinPin; runLedPin=cfg.insertLedPin; runRelayPin=cfg.relayPin;
  runCoinActiveLow=cfg.coinActiveLow; runRelayActiveHigh=cfg.relayActiveHigh; runLedActiveHigh=cfg.ledActiveHigh;
  runDebounceMs=cfg.coinDebounceMs; runPulseGroupMs=cfg.pulseGroupMs;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  setupPortal(); connectSta();
}

void loop(){
  web.handleClient();
  if(WiFi.status()!=WL_CONNECTED && !cfg.ssid.isEmpty() && millis()-lastPoll>8000){
    WiFi.disconnect(); WiFi.begin(cfg.ssid.c_str(),cfg.pass.c_str()); wifiFailures++; lastPoll=millis();
    if(wifiFailures>=maxWifiRetries) startSetupAp();
  }
  if(WiFi.status()==WL_CONNECTED && millis()-lastPoll>1500){
    wifiFailures=0; String r=post("poll"); insertMode=jsonTrue(r,"insert"); activeTarget=jsonString(r,"target_nonce"); applyRemoteConfig(r);
    applyOutputs(); lastPoll=millis();
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
  if(pendingPulses && pendingReady && WiFi.status()==WL_CONNECTED && (lastSend==0 || millis()-lastSend>900)){
    String r=post("coin",String(pendingPulses),pendingTarget,pendingNonce); lastSend=millis();
    if(r.indexOf("\"ok\":true")>=0 ||
       r.indexOf("coin window expired")>=0 || r.indexOf("coin target mismatch")>=0 ||
       r.indexOf("no active coin window")>=0 || r.indexOf("another vendo selected")>=0){
      clearPending(); applyOutputs();
    }
  }
  if(setupApOn && !cfg.ssid.isEmpty() && WiFi.status()==WL_CONNECTED && millis()-configuredApSince>600000UL){ WiFi.softAPdisconnect(true); setupApOn=false; }
  delay(2);
}
