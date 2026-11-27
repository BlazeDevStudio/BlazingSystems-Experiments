#pragma once
#include <Arduino.h>
#ifdef ESP8266
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <LittleFS.h>
#include <bearssl/bearssl.h>
extern "C" {
#include <user_interface.h>
}
using BlazeWebServer = ESP8266WebServer;
#else
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <LittleFS.h>
#include <mbedtls/sha256.h>
#include <esp_system.h>
using BlazeWebServer = WebServer;
#endif

#ifndef BLAZE_MAX_DEVICES
#ifdef ESP8266
#define BLAZE_MAX_DEVICES 6
#define BLAZE_MAX_REMOTE_COINS 4
#else
#define BLAZE_MAX_DEVICES 18
#define BLAZE_MAX_REMOTE_COINS 12
#endif
#endif

struct BlazeDevice {
  String id, secret, label, allowed, hidden, preferred, timerMode, quick, adminSalt, adminHash, inventory;
  uint32_t lease=0,lastSeen=0,revision=1,adminRounds=4096,gesture=4000,grace=0;
  bool timerToggle=true,notifications=true,unrestricted=false;
};

struct BlazeRemoteCoin {
  String id, ip, targetDevice, targetNonce, lastCoinNonce;
  uint32_t lastSeen=0,targetUntil=0;
};

class BlazeRentalStandalone {
public:
  BlazeWebServer web{80};
  BlazeDevice devices[BLAZE_MAX_DEVICES];
  BlazeRemoteCoin remoteCoins[BLAZE_MAX_REMOTE_COINS];
  int deviceCount=0,remoteCoinCount=0;

  String mode="rental";
  String staSsid="",staPass="",recoveryApPass="";
  String adminSalt="",adminHash="",session="";
  String vendoKey="";
  String remoteHost="",remoteKey="",controllerId="";
  uint32_t sessionUntil=0,epochBase=0,epochMillis=0,loginLockUntil=0,lastRemotePoll=0,rebootAt=0;
  uint8_t loginFails=0;
  bool setupMode=false,recoveryMode=false,recoveryNextBoot=false;
  bool remoteInsert=false;
  String remoteTarget="";
  uint32_t secondsPerPulse=600,coinWindow=120;
  int coinPin=-1;
  bool coinActiveLow=true,coinLast=true;
  uint32_t coinDebounceMs=60,lastCoinEdge=0;
  String localTargetDevice="",localTargetNonce="";
  uint32_t localTargetUntil=0;
  String enrollId="",enrollSecret="",enrollLabel="Rental phone";
  uint32_t enrollUntil=0;

  void begin(){
    Serial.begin(115200);
    delay(30);
#ifdef ESP8266
    LittleFS.begin();
#else
    LittleFS.begin(true);
#endif
    loadConfig();
    loadDevices();
    if(!vendoKey.length()){ vendoKey=randomHex(18); saveConfig(); }
    if(!controllerId.length()) controllerId="coin-"+chipSuffix();

    routes();
    configureCoinPin();

    if(!adminHash.length() || !staSsid.length() || recoveryNextBoot){
      startSetupAccessPoint(recoveryNextBoot);
      web.begin();
      printSetupInfo();
      return;
    }

    WiFi.mode(WIFI_STA);
    if(connectSavedWifi()){
      recoveryNextBoot=false;
      saveConfig();
      setupMode=false;
      web.begin();
      printServiceInfo();
      return;
    }

    recoveryNextBoot=true;
    saveConfig();
    Serial.println("Saved Wi-Fi failed five connection attempts. Rebooting into recovery AP.");
    delay(800);
    ESP.restart();
  }

  void loop(){
    web.handleClient();
    if(rebootAt && (int32_t)(millis()-rebootAt)>=0){
      delay(100);
      ESP.restart();
    }
    if(WiFi.status()==WL_CONNECTED) syncNtpIfReady();
    if(!setupMode){
      if(mode=="rental_coin") scanLocalCoin();
      if(mode=="coin_interface" && millis()-lastRemotePoll>=1000){
        lastRemotePoll=millis();
        pollRemoteServer();
      }
    }
    delay(2);
  }

private:
  static String json(String s){s.replace("\\","\\\\");s.replace("\"","\\\"");s.replace("\r"," ");s.replace("\n"," ");return s;}
  static String clean(String s){s.replace("\t"," ");s.replace("\r"," ");s.replace("\n"," ");return s;}
  static String fld(const String& line,int idx){int start=0,n=0;for(int i=0;i<=(int)line.length();i++){if(i==(int)line.length()||line[i]=='\t'){if(n==idx)return line.substring(start,i);start=i+1;n++;}}return "";}
  static uint32_t maxu(uint32_t a,uint32_t b){return a>b?a:b;}
  static bool validPkgList(const String&s){if(s.length()>2048)return false;for(size_t i=0;i<s.length();i++){char c=s[i];if(!(isalnum((unsigned char)c)||c=='.'||c=='_'||c=='-'||c==','||c=='*'))return false;}return true;}
  static bool validControllerId(const String&s){if(!s.length()||s.length()>48)return false;for(size_t i=0;i<s.length();i++){char c=s[i];if(!(isalnum((unsigned char)c)||c=='.'||c=='_'||c=='-'))return false;}return true;}

  uint8_t rb(){
#ifdef ESP8266
    return (uint8_t)(os_random()&0xff);
#else
    return (uint8_t)(esp_random()&0xff);
#endif
  }

  String randomHex(int bytes){
    static const char* h="0123456789abcdef";
    String out; out.reserve(bytes*2);
    for(int i=0;i<bytes;i++){uint8_t b=rb();out+=h[b>>4];out+=h[b&15];}
    return out;
  }

  String chipSuffix(){
#ifdef ESP8266
    char b[9]; snprintf(b,sizeof(b),"%06X",ESP.getChipId()); return String(b);
#else
    uint64_t m=ESP.getEfuseMac(); char b[9]; snprintf(b,sizeof(b),"%06X",(uint32_t)(m&0xffffff)); return String(b);
#endif
  }

  void shaRaw(const uint8_t* data,size_t len,uint8_t out[32]){
#ifdef ESP8266
    br_sha256_context c; br_sha256_init(&c); br_sha256_update(&c,data,len); br_sha256_out(&c,out);
#else
    mbedtls_sha256_context c; mbedtls_sha256_init(&c); mbedtls_sha256_starts(&c,0); mbedtls_sha256_update(&c,data,len); mbedtls_sha256_finish(&c,out); mbedtls_sha256_free(&c);
#endif
  }

  String hex32(const uint8_t b[32]){
    static const char* h="0123456789abcdef";
    String out; out.reserve(64);
    for(int i=0;i<32;i++){out+=h[b[i]>>4];out+=h[b[i]&15];}
    return out;
  }

  String sha256(const String&s){uint8_t o[32];shaRaw((const uint8_t*)s.c_str(),s.length(),o);return hex32(o);}
  String msStr(uint32_t sec){char b[24];snprintf(b,sizeof(b),"%llu",(unsigned long long)sec*1000ULL);return String(b);}

  String hmac(const String&key,const String&msg){
    uint8_t k[64]={0};
    if(key.length()>64){uint8_t kh[32];shaRaw((const uint8_t*)key.c_str(),key.length(),kh);memcpy(k,kh,32);}
    else memcpy(k,key.c_str(),key.length());
    uint8_t in[64],outp[64],inner[32],fin[32];
    for(int i=0;i<64;i++){in[i]=k[i]^0x36;outp[i]=k[i]^0x5c;}
#ifdef ESP8266
    br_sha256_context c;br_sha256_init(&c);br_sha256_update(&c,in,64);br_sha256_update(&c,msg.c_str(),msg.length());br_sha256_out(&c,inner);
    br_sha256_init(&c);br_sha256_update(&c,outp,64);br_sha256_update(&c,inner,32);br_sha256_out(&c,fin);
#else
    mbedtls_sha256_context c;mbedtls_sha256_init(&c);mbedtls_sha256_starts(&c,0);mbedtls_sha256_update(&c,in,64);mbedtls_sha256_update(&c,(const unsigned char*)msg.c_str(),msg.length());mbedtls_sha256_finish(&c,inner);
    mbedtls_sha256_starts(&c,0);mbedtls_sha256_update(&c,outp,64);mbedtls_sha256_update(&c,inner,32);mbedtls_sha256_finish(&c,fin);mbedtls_sha256_free(&c);
#endif
    return hex32(fin);
  }

  String iterHash(const String&pass,const String&salt,uint32_t rounds){
    String v=sha256(salt+"|"+pass+"|"+salt);
    for(uint32_t i=1;i<rounds;i++) v=sha256(v+"|"+pass+"|"+salt);
    return v;
  }

  uint32_t nowSec(){
    time_t t=time(nullptr);
    if(t>1700000000){epochBase=(uint32_t)t;epochMillis=millis();return (uint32_t)t;}
    if(epochBase>1700000000)return epochBase+(millis()-epochMillis)/1000;
    return 0;
  }

  void syncNtpIfReady(){
    static bool started=false;
    if(started||WiFi.status()!=WL_CONNECTED)return;
    configTime(0,0,"pool.ntp.org","time.google.com");
    started=true;
  }

  bool internetDnsOk(){
    if(WiFi.status()!=WL_CONNECTED)return false;
    IPAddress out;
    return WiFi.hostByName("example.com",out)==1;
  }

  bool waitForWifi(uint32_t timeoutMs){
    uint32_t start=millis();
    while(millis()-start<timeoutMs){
      if(WiFi.status()==WL_CONNECTED && WiFi.localIP()!=IPAddress(0,0,0,0)) return true;
      delay(120);
    }
    return false;
  }

  bool connectSavedWifi(){
    for(int attempt=1;attempt<=5;attempt++){
      Serial.printf("Wi-Fi connection attempt %d/5 to %s\n",attempt,staSsid.c_str());
      WiFi.disconnect();
      delay(150);
      WiFi.begin(staSsid.c_str(),staPass.c_str());
      if(waitForWifi(6500)) return true;
    }
    return false;
  }

  void startSetupAccessPoint(bool recovery){
    setupMode=true;
    recoveryMode=recovery;
    WiFi.mode(WIFI_AP_STA);
    String name="BlazeRental-Setup-"+chipSuffix();
    if(recovery && recoveryApPass.length()>=8) WiFi.softAP(name.c_str(),recoveryApPass.c_str());
    else WiFi.softAP(name.c_str());
  }

  void printSetupInfo(){
    Serial.println();
    Serial.println("BlazePwifi Rental setup/recovery mode");
    Serial.println("AP: BlazeRental-Setup-"+chipSuffix());
    Serial.println("Open: http://192.168.4.1/");
  }

  void printServiceInfo(){
    Serial.println();
    Serial.println("BlazePwifi ESP Rental service online");
    Serial.println("IP: "+WiFi.localIP().toString());
    Serial.println("Admin: http://"+WiFi.localIP().toString()+"/");
    if(!internetDnsOk()) Serial.println("Internet/DNS unavailable, but local rental service remains active.");
  }

  void loadConfig(){
    if(!LittleFS.exists("/config.txt"))return;
    File f=LittleFS.open("/config.txt","r");
    while(f&&f.available()){
      String l=f.readStringUntil('\n'); l.trim();
      int p=l.indexOf('='); if(p<1)continue;
      String k=l.substring(0,p),v=l.substring(p+1);
      if(k=="mode")mode=v;
      else if(k=="sta_ssid")staSsid=v;
      else if(k=="sta_pass")staPass=v;
      else if(k=="recovery_ap_pass")recoveryApPass=v;
      else if(k=="admin_salt")adminSalt=v;
      else if(k=="admin_hash")adminHash=v;
      else if(k=="vendo_key")vendoKey=v;
      else if(k=="remote_host")remoteHost=v;
      else if(k=="remote_key")remoteKey=v;
      else if(k=="controller_id")controllerId=v;
      else if(k=="seconds_per_pulse")secondsPerPulse=v.toInt();
      else if(k=="coin_window")coinWindow=v.toInt();
      else if(k=="coin_pin")coinPin=v.toInt();
      else if(k=="coin_active_low")coinActiveLow=v!="0";
      else if(k=="coin_debounce_ms")coinDebounceMs=v.toInt();
      else if(k=="recovery_next_boot")recoveryNextBoot=v=="1";
    }
    if(f)f.close();
    if(mode!="rental"&&mode!="rental_coin"&&mode!="coin_interface")mode="rental";
  }

  void saveConfig(){
    File f=LittleFS.open("/config.txt","w"); if(!f)return;
    f.println("mode="+mode);
    f.println("sta_ssid="+clean(staSsid));
    f.println("sta_pass="+clean(staPass));
    f.println("recovery_ap_pass="+clean(recoveryApPass));
    f.println("admin_salt="+adminSalt);
    f.println("admin_hash="+adminHash);
    f.println("vendo_key="+vendoKey);
    f.println("remote_host="+clean(remoteHost));
    f.println("remote_key="+clean(remoteKey));
    f.println("controller_id="+clean(controllerId));
    f.println("seconds_per_pulse="+String(secondsPerPulse));
    f.println("coin_window="+String(coinWindow));
    f.println("coin_pin="+String(coinPin));
    f.println("coin_active_low="+String(coinActiveLow?1:0));
    f.println("coin_debounce_ms="+String(coinDebounceMs));
    f.println("recovery_next_boot="+String(recoveryNextBoot?1:0));
    f.close();
  }

  void loadDevices(){
    deviceCount=0;
    if(!LittleFS.exists("/devices.tsv"))return;
    File f=LittleFS.open("/devices.tsv","r");
    while(f&&f.available()&&deviceCount<BLAZE_MAX_DEVICES){
      String l=f.readStringUntil('\n');l.trim();if(!l.length())continue;
      BlazeDevice&d=devices[deviceCount++];
      d.id=fld(l,0);d.secret=fld(l,1);d.lease=fld(l,2).toInt();d.label=fld(l,3);d.lastSeen=fld(l,4).toInt();d.revision=maxu(1,(uint32_t)fld(l,5).toInt());
      d.unrestricted=fld(l,6)=="unrestricted";d.allowed=fld(l,7);d.hidden=fld(l,8);d.preferred=fld(l,9);d.timerMode=fld(l,10);d.timerToggle=fld(l,11)!="0";
      d.quick=fld(l,12);d.notifications=fld(l,13)!="0";d.gesture=fld(l,14).toInt();d.grace=fld(l,15).toInt();d.adminSalt=fld(l,16);d.adminHash=fld(l,17);
      d.adminRounds=maxu(1,(uint32_t)fld(l,18).toInt());d.inventory=fld(l,19);
    }
    if(f)f.close();
  }

  void saveDevices(){
    File f=LittleFS.open("/devices.tsv","w"); if(!f)return;
    for(int i=0;i<deviceCount;i++){
      BlazeDevice&d=devices[i];
      f.printf("%s\t%s\t%lu\t%s\t%lu\t%lu\t%s\t%s\t%s\t%s\t%s\t%d\t%s\t%d\t%lu\t%lu\t%s\t%s\t%lu\t%s\n",
        d.id.c_str(),d.secret.c_str(),(unsigned long)d.lease,clean(d.label).c_str(),(unsigned long)d.lastSeen,(unsigned long)d.revision,
        d.unrestricted?"unrestricted":"rental",clean(d.allowed).c_str(),clean(d.hidden).c_str(),clean(d.preferred).c_str(),clean(d.timerMode).c_str(),
        d.timerToggle?1:0,clean(d.quick).c_str(),d.notifications?1:0,(unsigned long)d.gesture,(unsigned long)d.grace,d.adminSalt.c_str(),d.adminHash.c_str(),
        (unsigned long)d.adminRounds,clean(d.inventory).c_str());
    }
    f.close();
  }

  int findDevice(const String&id){for(int i=0;i<deviceCount;i++)if(devices[i].id==id)return i;return -1;}
  void removeDevice(int n){if(n<0||n>=deviceCount)return;for(int i=n;i<deviceCount-1;i++)devices[i]=devices[i+1];deviceCount--;saveDevices();}

  void event(const String&s){
    File f=LittleFS.open("/events.log","a");
    if(f){f.println(String(nowSec())+"\t"+clean(s));f.close();}
  }

  int findRemoteCoin(const String&id){for(int i=0;i<remoteCoinCount;i++)if(remoteCoins[i].id==id)return i;return -1;}
  int ensureRemoteCoin(const String&id){
    int i=findRemoteCoin(id); if(i>=0)return i;
    if(remoteCoinCount>=BLAZE_MAX_REMOTE_COINS)return -1;
    remoteCoins[remoteCoinCount].id=id;
    return remoteCoinCount++;
  }

  String remotesJson(){
    String s="[";
    for(int i=0;i<remoteCoinCount;i++){
      if(i)s+=",";
      BlazeRemoteCoin&r=remoteCoins[i];
      s+="{\"id\":\""+json(r.id)+"\",\"ip\":\""+json(r.ip)+"\",\"last_seen\":"+String(r.lastSeen)+",\"busy\":"+(r.targetUntil>nowSec()?"true":"false")+"}";
    }
    s+="]";
    return s;
  }

  bool sessionOk(){
    String t=web.header("X-Blaze-Session");
    return session.length()&&t==session&&(int32_t)(sessionUntil-millis())>0;
  }

  void jsonSend(const String&s){web.send(200,"application/json",s);}
  void fail(const String&e){jsonSend("{\"ok\":false,\"error\":\""+json(e)+"\"}");}

  void routes(){
#ifdef ESP8266
    web.collectHeaders("X-Blaze-Session");
#else
    const char* headers[]={"X-Blaze-Session"}; web.collectHeaders(headers,1);
#endif
    web.on("/",HTTP_GET,[this](){web.send_P(200,"text/html",ADMIN_HTML);});
    web.on("/api/public",HTTP_GET,[this](){publicApi();});
    web.on("/api/scan",HTTP_GET,[this](){scanApi();});
    web.on("/api/setup",HTTP_POST,[this](){setupApi();});
    web.on("/api/login",HTTP_POST,[this](){loginApi();});
    web.on("/api/admin",HTTP_POST,[this](){adminApi();});
    web.on("/cgi-bin/rental",HTTP_POST,[this](){rentalApi();});
    web.on("/cgi-bin/vendo",HTTP_POST,[this](){vendoApi();});
    web.onNotFound([this](){web.send(404,"text/plain","BlazePwifi ESP Rental Server");});
  }

  void publicApi(){
    String ip=setupMode?WiFi.softAPIP().toString():WiFi.localIP().toString();
    String s=String("{\"ok\":true,\"setup_mode\":")+(setupMode?"true":"false")+",\"recovery_mode\":"+(recoveryMode?"true":"false")+
      ",\"configured\":"+(adminHash.length()?"true":"false")+",\"ip\":\""+ip+"\",\"ssid\":\""+json(staSsid)+"\",\"mode\":\""+mode+"\"}";
    jsonSend(s);
  }

  void scanApi(){
    if(!setupMode){fail("scan available only in setup/recovery mode");return;}
    int n=WiFi.scanNetworks();
    String s="{\"ok\":true,\"networks\":[";
    for(int i=0;i<n;i++){
      if(i)s+=",";
      s+="{\"ssid\":\""+json(WiFi.SSID(i))+"\",\"rssi\":"+String(WiFi.RSSI(i))+",\"secure\":"+(WiFi.encryptionType(i)==0?"false":"true")+"}";
    }
    s+="]}";
    WiFi.scanDelete();
    jsonSend(s);
  }

  void setupApi(){
    if(!setupMode){fail("not in setup mode");return;}
    String ssid=clean(web.arg("ssid")),pass=clean(web.arg("wifi_password")),admin=web.arg("admin_password"),rap=clean(web.arg("recovery_ap_password"));
    if(!ssid.length()){fail("select a Wi-Fi network");return;}
    if(!adminHash.length() && admin.length()<12){fail("administrator password must be at least 12 characters");return;}
    if(rap.length() && rap.length()<8){fail("recovery AP password must be at least 8 characters");return;}

    WiFi.mode(WIFI_AP_STA);
    WiFi.disconnect();
    delay(100);
    WiFi.begin(ssid.c_str(),pass.c_str());
    if(!waitForWifi(15000)){
      WiFi.disconnect();
      fail("Wi-Fi rejected credentials, was not found, or DHCP failed. Nothing was saved.");
      return;
    }

    staSsid=ssid;staPass=pass;recoveryApPass=rap;
    if(admin.length()>=12){adminSalt=randomHex(8);adminHash=iterHash(admin,adminSalt,2048);}
    recoveryNextBoot=false;
    saveConfig();

    String ip=WiFi.localIP().toString();
    bool inet=internetDnsOk();
    rebootAt=millis()+6000;
    jsonSend("{\"ok\":true,\"ip\":\""+ip+"\",\"internet\":"+(inet?"true":"false")+",\"reboot_in\":6}");
  }

  void loginApi(){
    if(setupMode){fail("finish Wi-Fi setup first");return;}
    if(!adminHash.length()){fail("setup required");return;}
    if((int32_t)(loginLockUntil-millis())>0){fail("temporarily locked");return;}
    String p=web.arg("password");
    if(iterHash(p,adminSalt,2048)!=adminHash){
      loginFails++;
      if(loginFails>=5){loginFails=0;loginLockUntil=millis()+300000UL;event("admin login lockout");}
      delay(650);
      fail("invalid credentials");
      return;
    }
    loginFails=0;loginLockUntil=0;session=randomHex(24);sessionUntil=millis()+1800000UL;
    jsonSend("{\"ok\":true,\"session\":\""+session+"\"}");
  }

  void adminApi(){
    if(!sessionOk()){fail("unauthorized");return;}
    sessionUntil=millis()+1800000UL;
    String a=web.arg("action");

    if(a=="time"){uint32_t t=web.arg("epoch").toInt();if(t>1700000000){epochBase=t;epochMillis=millis();}jsonSend("{\"ok\":true}");return;}

    if(a=="status"){
      String s="{\"ok\":true,\"mode\":\""+mode+"\",\"ip\":\""+WiFi.localIP().toString()+"\",\"ssid\":\""+json(WiFi.SSID())+
        "\",\"rssi\":"+String(WiFi.RSSI())+",\"internet\":"+(internetDnsOk()?"true":"false")+",\"devices\":"+String(deviceCount)+
        ",\"remote_coins\":"+String(remoteCoinCount)+",\"remote_coin_list\":"+remotesJson()+",\"coin_pin\":"+String(coinPin)+
        ",\"seconds_per_pulse\":"+String(secondsPerPulse)+",\"coin_window\":"+String(coinWindow)+",\"binding_key\":\""+vendoKey+
        "\",\"remote_host\":\""+json(remoteHost)+"\",\"controller_id\":\""+json(controllerId)+"\",\"heap\":"+String(ESP.getFreeHeap())+"}";
      jsonSend(s);return;
    }

    if(a=="list"){
      String s="{\"ok\":true,\"devices\":[";
      for(int i=0;i<deviceCount;i++){
        if(i)s+=",";
        BlazeDevice&d=devices[i];
        s+="{\"device_id\":\""+d.id+"\",\"label\":\""+json(d.label)+"\",\"lease_until\":"+String(d.lease)+",\"last_seen\":"+String(d.lastSeen)+
          ",\"policy_revision\":"+String(d.revision)+",\"launcher_mode\":\""+String(d.unrestricted?"unrestricted":"rental")+"\",\"allowed_packages\":\""+
          json(d.allowed)+"\",\"hidden_packages\":\""+json(d.hidden)+"\",\"preferred_vendo\":\""+json(d.preferred)+"\",\"timer_mode\":\""+json(d.timerMode)+
          "\",\"timer_user_toggle\":"+String(d.timerToggle?1:0)+",\"quick_controls\":\""+json(d.quick)+"\",\"notifications_enabled\":"+String(d.notifications?1:0)+
          ",\"admin_password_set\":"+(d.adminHash.length()?"true":"false")+",\"inventory\":\""+json(d.inventory)+"\"}";
      }
      s+="]}";jsonSend(s);return;
    }

    if(a=="enroll"){
      if(mode=="coin_interface"){fail("local rental server is inactive in Coin Slot Interface mode");return;}
      if(deviceCount>=BLAZE_MAX_DEVICES){fail("device capacity reached");return;}
      uint32_t n=nowSec();if(!n){fail("server time not synchronized");return;}
      enrollId=randomHex(6);enrollSecret=randomHex(18);enrollLabel=clean(web.arg("label"));if(!enrollLabel.length())enrollLabel="Rental phone";
      enrollUntil=n+600;String tok=enrollId+"."+enrollSecret;
      jsonSend("{\"ok\":true,\"token\":\""+tok+"\",\"expires\":600}");return;
    }

    if(a=="add_time"||a=="set_time"||a=="expire"){
      int i=findDevice(web.arg("device_id"));if(i<0){fail("unknown device");return;}
      uint32_t n=nowSec();if(!n){fail("server time not synchronized");return;}
      if(a=="expire")devices[i].lease=n;
      else{uint32_t sec=web.arg("seconds").toInt();if(sec>2592000UL){fail("duration too large");return;}devices[i].lease=(a=="add_time"?maxu(devices[i].lease,n):n)+sec;}
      saveDevices();event(a+" "+devices[i].id);jsonSend("{\"ok\":true,\"lease_until\":"+String(devices[i].lease)+"}");return;
    }

    if(a=="revoke"){int i=findDevice(web.arg("device_id"));if(i<0){fail("unknown device");return;}event("revoke "+devices[i].id);removeDevice(i);jsonSend("{\"ok\":true}");return;}
    if(a=="rename"){int i=findDevice(web.arg("device_id"));if(i<0){fail("unknown device");return;}devices[i].label=clean(web.arg("label")).substring(0,64);saveDevices();jsonSend("{\"ok\":true}");return;}

    if(a=="policy"){
      int i=findDevice(web.arg("device_id"));if(i<0){fail("unknown device");return;}
      String al=web.arg("allowed"),hi=web.arg("hidden");if(!validPkgList(al)||!validPkgList(hi)){fail("invalid package list");return;}
      BlazeDevice&d=devices[i];d.unrestricted=web.arg("launcher_mode")=="unrestricted";d.allowed=al.length()?al:"*";d.hidden=hi;d.preferred=clean(web.arg("preferred"));
      d.timerMode=clean(web.arg("timer_mode"));if(d.timerMode!="overlay"&&d.timerMode!="always"&&d.timerMode!="off")d.timerMode="overlay";
      d.timerToggle=web.arg("timer_toggle")!="0";d.quick=clean(web.arg("quick"));d.notifications=web.arg("notifications")!="0";d.grace=web.arg("grace").toInt();d.revision++;
      saveDevices();event("policy "+d.id+" rev="+String(d.revision));jsonSend("{\"ok\":true,\"policy_revision\":"+String(d.revision)+"}");return;
    }

    if(a=="device_admin"){
      int i=findDevice(web.arg("device_id"));if(i<0){fail("unknown device");return;}
      String p=web.arg("password");if(p.length()<8){fail("device admin password too short");return;}
      BlazeDevice&d=devices[i];d.adminSalt=randomHex(12);d.adminRounds=4096;d.adminHash=iterHash(p,d.adminSalt,d.adminRounds);d.revision++;saveDevices();
      jsonSend("{\"ok\":true}");return;
    }

    if(a=="settings"){
      String m=web.arg("mode");
      if(m!="rental"&&m!="rental_coin"&&m!="coin_interface"){fail("invalid operating mode");return;}
      mode=m;
      uint32_t spp=web.arg("seconds_per_pulse").toInt();if(spp<1||spp>86400){fail("invalid seconds per pulse");return;}secondsPerPulse=spp;
      uint32_t cw=web.arg("coin_window").toInt();if(cw<5||cw>3600){fail("invalid coin window");return;}coinWindow=cw;
      if(web.hasArg("coin_pin"))coinPin=web.arg("coin_pin").toInt();
      if(web.hasArg("coin_active_low"))coinActiveLow=web.arg("coin_active_low")!="0";
      if(web.hasArg("coin_debounce_ms")){uint32_t d=web.arg("coin_debounce_ms").toInt();if(d<10||d>2000){fail("invalid debounce");return;}coinDebounceMs=d;}
      remoteHost=clean(web.arg("remote_host"));remoteKey=clean(web.arg("remote_key"));controllerId=clean(web.arg("controller_id"));
      if(!controllerId.length())controllerId="coin-"+chipSuffix();
      if(!validControllerId(controllerId)){fail("invalid controller id");return;}
      saveConfig();configureCoinPin();jsonSend("{\"ok\":true,\"reboot_recommended\":false}");return;
    }

    if(a=="change_wifi"){
      String ssid=clean(web.arg("ssid")),pass=clean(web.arg("wifi_password"));
      if(!ssid.length()){fail("missing Wi-Fi SSID");return;}
      WiFi.mode(WIFI_STA);WiFi.disconnect();delay(100);WiFi.begin(ssid.c_str(),pass.c_str());
      if(!waitForWifi(15000)){WiFi.begin(staSsid.c_str(),staPass.c_str());fail("new Wi-Fi failed; old configuration preserved");return;}
      staSsid=ssid;staPass=pass;recoveryNextBoot=false;saveConfig();String ip=WiFi.localIP().toString();rebootAt=millis()+6000;
      jsonSend("{\"ok\":true,\"ip\":\""+ip+"\",\"reboot_in\":6}");return;
    }

    if(a=="change_password"){
      String p=web.arg("password");if(p.length()<12){fail("password must be at least 12 characters");return;}
      adminSalt=randomHex(8);adminHash=iterHash(p,adminSalt,2048);saveConfig();session="";sessionUntil=0;jsonSend("{\"ok\":true,\"reauth_required\":true}");return;
    }

    if(a=="events"){
      String s="{\"ok\":true,\"events\":[";
      if(LittleFS.exists("/events.log")){
        File f=LittleFS.open("/events.log","r");String lines[30];int n=0;
        while(f&&f.available()){lines[n%30]=f.readStringUntil('\n');n++;}
        if(f)f.close();int count=n<30?n:30,start=n-count;
        for(int j=0;j<count;j++){if(j)s+=",";String l=lines[(start+j)%30];s+="\""+json(l)+"\"";}
      }
      s+="]}";jsonSend(s);return;
    }

    fail("unknown action");
  }

  void rentalApi(){
    if(mode=="coin_interface"){fail("local rental server is inactive in Coin Slot Interface mode");return;}
    String a=web.arg("action"),nonce=web.arg("nonce"),sig=web.arg("sig");uint32_t n=nowSec();
    if(!n){fail("server time not synchronized");return;}
    if(!nonce.length()||!sig.length()){fail("missing authentication");return;}

    if(a=="enroll"){
      String eid=web.arg("enroll_id");
      if(eid!=enrollId||n>enrollUntil||!enrollSecret.length()){fail("enrollment invalid or used");return;}
      String tok=enrollId+"."+enrollSecret;
      if(hmac(tok,"enroll|"+nonce+"|"+tok)!=sig){fail("authentication failed");return;}
      if(deviceCount>=BLAZE_MAX_DEVICES){fail("device capacity reached");return;}
      BlazeDevice&d=devices[deviceCount++];d.id=randomHex(12);d.secret=randomHex(24);d.label=enrollLabel;d.lease=n;d.lastSeen=n;d.allowed="*";d.hidden="";
      d.preferred="";d.timerMode="overlay";d.quick="volume_down,volume_up,floating_timer,network_status,battery_status,bluetooth_status,flashlight";d.revision=1;
      saveDevices();enrollId="";enrollSecret="";
      jsonSend("{\"ok\":true,\"device_id\":\""+d.id+"\",\"device_secret\":\""+d.secret+"\",\"server_time_ms\":"+msStr(n)+",\"lease_until_ms\":"+msStr(n)+"}");
      return;
    }

    String did=web.arg("device_id");int i=findDevice(did);if(i<0){fail("unknown device");return;}BlazeDevice&d=devices[i];

    if(a=="status"||a=="policy_get"){
      if(hmac(d.secret,a+"|"+nonce+"|"+d.secret)!=sig){fail("authentication failed");return;}
      String inv=clean(web.arg("inventory"));if(inv.length()&&inv.length()<=2048&&validPkgList(inv))d.inventory=inv;
      d.lastSeen=n;saveDevices();
      uint32_t report=maxu(d.lease,n);String lm=d.unrestricted?"unrestricted":"rental",salt=d.adminSalt,hash=d.adminHash;
      String legacy=did+"|"+nonce+"|"+msStr(n)+"|"+msStr(report)+"|"+d.allowed+"|"+salt+"|"+hash+"|"+String(d.adminRounds)+"|"+d.preferred+"|"+String(secondsPerPulse);
      String v2="v2|"+did+"|"+nonce+"|"+msStr(n)+"|"+msStr(report)+"|"+String(d.revision)+"|"+lm+"|"+d.allowed+"|"+d.hidden+"|"+salt+"|"+hash+"|"+String(d.adminRounds)+"|"+d.preferred+"|"+String(secondsPerPulse);
      String v3="v3|"+did+"|"+nonce+"|"+msStr(n)+"|"+msStr(report)+"|"+String(d.revision)+"|"+lm+"|"+d.allowed+"|"+d.hidden+"|"+salt+"|"+hash+"|"+String(d.adminRounds)+"|"+d.preferred+"|"+String(secondsPerPulse)+"|"+d.timerMode+"|"+String(d.timerToggle?1:0)+"|"+d.quick+"|"+String(d.notifications?1:0)+"|hold|"+String(d.gesture)+"|"+String(d.grace);
      String out="{\"ok\":true,\"device_id\":\""+did+"\",\"server_time_ms\":"+msStr(n)+",\"lease_until_ms\":"+msStr(report)+",\"policy_revision\":"+String(d.revision)+
        ",\"launcher_mode\":\""+lm+"\",\"allowed_packages\":\""+json(d.allowed)+"\",\"hidden_packages\":\""+json(d.hidden)+"\",\"admin_salt\":\""+salt+"\",\"admin_hash\":\""+hash+
        "\",\"admin_rounds\":"+String(d.adminRounds)+",\"preferred_vendo\":\""+json(d.preferred)+"\",\"rental_seconds_per_pulse\":"+String(secondsPerPulse)+
        ",\"timer_mode\":\""+d.timerMode+"\",\"timer_user_toggle\":"+String(d.timerToggle?1:0)+",\"quick_controls\":\""+json(d.quick)+"\",\"notifications_enabled\":"+
        String(d.notifications?1:0)+",\"admin_gesture_type\":\"hold\",\"admin_gesture_value\":"+String(d.gesture)+",\"offline_grace\":"+String(d.grace)+
        ",\"policy_sig\":\""+hmac(d.secret,legacy)+"\",\"policy_sig_v2\":\""+hmac(d.secret,v2)+"\",\"policy_sig_v3\":\""+hmac(d.secret,v3)+"\"}";
      jsonSend(out);return;
    }

    if(a=="inventory_update"||a=="device_capabilities"){
      String payload=clean(web.arg(a=="inventory_update"?"inventory":"capabilities"));
      if(hmac(d.secret,a+"|"+nonce+"|"+payload+"|"+d.secret)!=sig){fail("authentication failed");return;}
      if(a=="inventory_update"){if(payload.length()>2048||!validPkgList(payload)){fail("invalid app inventory");return;}d.inventory=payload;d.lastSeen=n;saveDevices();}
      jsonSend("{\"ok\":true}");return;
    }

    if(a=="policy_patch"){
      String expected=web.arg("expected_revision"),modeNew=web.arg("launcher_mode"),allowedNew=web.arg("allowed_packages"),hiddenNew=web.arg("hidden_packages"),
        preferredNew=web.arg("preferred_vendo"),timerNew=web.arg("timer_user_toggle"),notifyNew=web.arg("notifications_enabled"),quickNew=web.arg("quick_controls"),
        gestureNew=web.arg("admin_gesture_value"),adminNew=web.arg("admin_password");
      String canonical="policy_patch|"+nonce+"|"+did+"|"+expected+"|"+modeNew+"|"+allowedNew+"|"+hiddenNew+"|"+preferredNew+"|"+timerNew+"|"+notifyNew+"|"+quickNew+"|"+gestureNew+"|"+adminNew;
      if(hmac(d.secret,canonical)!=sig){fail("authentication failed");return;}
      uint32_t er=(uint32_t)expected.toInt();if(er!=d.revision){jsonSend("{\"ok\":false,\"error\":\"stale policy revision\",\"current_revision\":"+String(d.revision)+"}");return;}
      if(modeNew!="@keep"){if(modeNew!="rental"&&modeNew!="unrestricted"){fail("invalid launcher mode");return;}d.unrestricted=modeNew=="unrestricted";}
      if(allowedNew!="@keep"){if(allowedNew=="-")allowedNew="";if(!validPkgList(allowedNew)){fail("invalid allowed packages");return;}d.allowed=allowedNew;}
      if(hiddenNew!="@keep"){if(hiddenNew=="-")hiddenNew="";if(!validPkgList(hiddenNew)){fail("invalid hidden packages");return;}d.hidden=hiddenNew;}
      if(preferredNew!="@keep")d.preferred=clean(preferredNew);
      if(timerNew!="@keep"){if(timerNew!="0"&&timerNew!="1"){fail("invalid timer toggle");return;}d.timerToggle=timerNew=="1";}
      if(notifyNew!="@keep"){if(notifyNew!="0"&&notifyNew!="1"){fail("invalid notifications flag");return;}d.notifications=notifyNew=="1";}
      if(quickNew!="@keep"){if(quickNew=="-")quickNew="";if(!validPkgList(quickNew)){fail("invalid quick controls");return;}d.quick=quickNew;}
      if(gestureNew!="@keep"){uint32_t g=(uint32_t)gestureNew.toInt();if(g<1500||g>15000){fail("invalid admin gesture");return;}d.gesture=g;}
      if(adminNew.length()&&adminNew!="@keep"){if(adminNew.length()<8){fail("admin password too short");return;}d.adminSalt=randomHex(12);d.adminRounds=4096;d.adminHash=iterHash(adminNew,d.adminSalt,d.adminRounds);}
      d.revision++;saveDevices();event("policy_patch "+d.id+" rev="+String(d.revision));
      jsonSend("{\"ok\":true,\"policy_revision\":"+String(d.revision)+"}");return;
    }

    if(a=="coin_start"){
      if(hmac(d.secret,"coin_start|"+nonce+"|"+d.secret)!=sig){fail("authentication failed");return;}
      String requested=clean(web.arg("vendo"));if(!requested.length())requested=d.preferred;
      String chosen=selectCoinInterface(requested,n);
      if(!chosen.length()){fail("no coin interface available");return;}
      String target=randomHex(8);
      if(chosen=="local"){localTargetDevice=d.id;localTargetNonce=target;localTargetUntil=n+coinWindow;}
      else{
        int ri=findRemoteCoin(chosen);if(ri<0){fail("selected coin interface unavailable");return;}
        remoteCoins[ri].targetDevice=d.id;remoteCoins[ri].targetNonce=target;remoteCoins[ri].targetUntil=n+coinWindow;
      }
      jsonSend("{\"ok\":true,\"vendo\":\""+json(chosen)+"\",\"target_nonce\":\""+target+"\",\"expires\":"+String(n+coinWindow)+"}");
      return;
    }

    fail("unknown rental action");
  }

  String selectCoinInterface(const String&requested,uint32_t n){
    if(requested=="local"){
      if(mode=="rental_coin"&&coinPin>=0&&(localTargetUntil<=n||!localTargetDevice.length()))return "local";
      return "";
    }
    if(requested.length()){
      int r=findRemoteCoin(requested);
      if(r>=0&&remoteCoins[r].lastSeen+30>=n&&(remoteCoins[r].targetUntil<=n||!remoteCoins[r].targetDevice.length()))return requested;
      return "";
    }
    if(mode=="rental_coin"&&coinPin>=0&&(localTargetUntil<=n||!localTargetDevice.length()))return "local";
    for(int i=0;i<remoteCoinCount;i++)if(remoteCoins[i].lastSeen+30>=n&&(remoteCoins[i].targetUntil<=n||!remoteCoins[i].targetDevice.length()))return remoteCoins[i].id;
    return "";
  }

  void configureCoinPin(){
    if(coinPin<0)return;
    pinMode(coinPin,INPUT_PULLUP);
    coinLast=digitalRead(coinPin);
  }

  void scanLocalCoin(){
    if(coinPin<0)return;
    bool v=digitalRead(coinPin);
    bool active=coinActiveLow?!v:v;
    bool wasActive=coinActiveLow?!coinLast:coinLast;
    if(!wasActive&&active&&millis()-lastCoinEdge>=coinDebounceMs){
      lastCoinEdge=millis();
      uint32_t n=nowSec();
      if(n&&localTargetUntil>n&&localTargetDevice.length()){
        int d=findDevice(localTargetDevice);
        if(d>=0){
          devices[d].lease=maxu(devices[d].lease,n)+secondsPerPulse;
          saveDevices();
          event("local coin "+localTargetDevice);
        }
      }
    }
    coinLast=v;
  }

  String vendoSig(const String&key,const String&a,const String&id,const String&nonce,const String&pulses,const String&target){
    return sha256(key+"|"+a+"|"+id+"|"+nonce+"|"+pulses+"|"+target+"|"+key);
  }

  void vendoApi(){
    if(mode=="coin_interface"){fail("controller endpoint disabled in Coin Slot Interface mode");return;}
    String a=web.arg("action"),id=clean(web.arg("id")),nonce=web.arg("nonce"),pulses=web.arg("pulses"),target=web.arg("target"),sig=web.arg("sig");
    if(!validControllerId(id)){fail("invalid vendo id");return;}
    if(!nonce.length()||nonce.length()>32){fail("invalid nonce");return;}
    if(!pulses.length())pulses="0";
    if(vendoSig(vendoKey,a,id,nonce,pulses,target)!=sig){fail("bad signature");return;}
    uint32_t n=nowSec();if(!n){fail("server time not synchronized");return;}
    int ri=ensureRemoteCoin(id);if(ri<0){fail("remote coin capacity reached");return;}
    BlazeRemoteCoin&r=remoteCoins[ri];r.lastSeen=n;r.ip=web.client().remoteIP().toString();

    if(a=="register"||a=="ping"){
      jsonSend("{\"ok\":true,\"server_time\":"+String(n)+",\"controller\":{\"enabled\":1,\"coin_enabled\":1,\"config_revision\":1}}");return;
    }

    if(a=="poll"){
      if(r.targetUntil<=n){r.targetDevice="";r.targetNonce="";r.targetUntil=0;}
      int insert=(r.targetUntil>n&&r.targetDevice.length())?1:0;
      jsonSend("{\"ok\":true,\"insert\":"+String(insert)+",\"target_nonce\":\""+json(r.targetNonce)+"\",\"expires\":"+String(r.targetUntil)+",\"controller\":{\"enabled\":1,\"coin_enabled\":1,\"config_revision\":1}}");
      return;
    }

    if(a=="coin"){
      int pc=pulses.toInt();if(pc<1||pc>20){fail("pulse count out of range");return;}
      if(!r.targetDevice.length()||r.targetUntil<=n){r.targetDevice="";r.targetNonce="";r.targetUntil=0;fail("no active coin window");return;}
      if(target!=r.targetNonce){fail("coin target mismatch");return;}
      if(r.lastCoinNonce==nonce){jsonSend("{\"ok\":true,\"duplicate\":true,\"rental\":true,\"target_nonce\":\""+target+"\"}");return;}
      int di=findDevice(r.targetDevice);if(di<0){fail("rental target not found");return;}
      devices[di].lease=maxu(devices[di].lease,n)+(secondsPerPulse*(uint32_t)pc);
      saveDevices();r.lastCoinNonce=nonce;event("remote coin "+id+" "+r.targetDevice+" pulses="+String(pc));
      jsonSend("{\"ok\":true,\"duplicate\":false,\"rental\":true,\"lease_until\":"+String(devices[di].lease)+",\"target_nonce\":\""+target+"\"}");
      return;
    }

    fail("unknown vendo action");
  }

  String extractJson(const String&s,const String&key){
    String q="\""+key+"\"";int p=s.indexOf(q);if(p<0)return"";p=s.indexOf(':',p);if(p<0)return"";p++;
    while(p<(int)s.length()&&(s[p]==' '||s[p]=='\"'))p++;
    int e=p;while(e<(int)s.length()&&s[e]!='\"'&&s[e]!=','&&s[e]!='}')e++;
    return s.substring(p,e);
  }

  bool remotePostUrl(const String&base,const String&body,String&resp){
    WiFiClient c;HTTPClient h;String url=base;if(!url.endsWith("/"))url+="/";url+="cgi-bin/vendo";
    if(!h.begin(c,url))return false;
    h.addHeader("Content-Type","application/x-www-form-urlencoded");
    int code=h.POST(body);resp=code>0?h.getString():"";h.end();
    return code==200;
  }

  bool remotePost(const String&body,String&resp){
    if(WiFi.status()!=WL_CONNECTED||!remoteHost.length()||!remoteKey.length())return false;
    String base=remoteHost;if(!base.startsWith("http://"))base="http://"+base;
    int scheme=base.indexOf("://"),slash=base.indexOf('/',scheme+3),colon=base.indexOf(':',scheme+3);
    bool explicitPort=colon>=0&&(slash<0||colon<slash);
    if(explicitPort)return remotePostUrl(base,body,resp);
    if(remotePostUrl(base+":4455",body,resp))return true;
    return remotePostUrl(base,body,resp);
  }

  void pollRemoteServer(){
    if(coinPin<0)return;
    if(!validControllerId(controllerId))return;
    String nonce=randomHex(8),sig=vendoSig(remoteKey,"poll",controllerId,nonce,"0",""),resp;
    String body="action=poll&id="+controllerId+"&nonce="+nonce+"&pulses=0&target=&sig="+sig;
    if(remotePost(body,resp)){
      remoteInsert=extractJson(resp,"insert")=="1";
      remoteTarget=extractJson(resp,"target_nonce");
    }else{
      remoteInsert=false;remoteTarget="";
    }
    scanInterfaceCoin();
  }

  void scanInterfaceCoin(){
    if(coinPin<0)return;
    bool v=digitalRead(coinPin);
    bool active=coinActiveLow?!v:v;
    bool wasActive=coinActiveLow?!coinLast:coinLast;
    if(!wasActive&&active&&millis()-lastCoinEdge>=coinDebounceMs){
      lastCoinEdge=millis();
      if(remoteInsert&&remoteTarget.length()){
        String nonce=randomHex(8),sig=vendoSig(remoteKey,"coin",controllerId,nonce,"1",remoteTarget),resp;
        String body="action=coin&id="+controllerId+"&nonce="+nonce+"&pulses=1&target="+remoteTarget+"&sig="+sig;
        remotePost(body,resp);
        event("forwarded coin "+controllerId);
      }
    }
    coinLast=v;
  }

  static const char ADMIN_HTML[] PROGMEM;
};

const char BlazeRentalStandalone::ADMIN_HTML[] PROGMEM = R"HTML(
<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>BlazePwifi Rental</title>
<style>
:root{color-scheme:dark;font:14px system-ui;background:#07111d;color:#eef}*{box-sizing:border-box}body{margin:0;background:#07111d}.w{max-width:980px;margin:auto;padding:14px}.c{background:#0d1b2b;border:1px solid #284057;border-radius:12px;padding:14px;margin:10px 0}.r{display:flex;gap:7px;flex-wrap:wrap;align-items:center}.g{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.m{color:#9ab}.good{color:#6eebac}.bad{color:#ff7f94}.mono{font-family:monospace;word-break:break-all}input,select,button{font:inherit;padding:9px;border-radius:8px;border:1px solid #35536d;background:#081522;color:#fff}input,select{min-width:130px;flex:1}button{cursor:pointer}.p{background:#148fd0}.danger{background:#4a1e27}.d{border-top:1px solid #20394e;padding:10px 0}.hide{display:none}.net{padding:7px;border:1px solid #20394e;border-radius:8px;margin:5px 0;cursor:pointer}@media(max-width:700px){.g{grid-template-columns:1fr}}
</style></head><body><div class="w">
<h2>BlazePwifi <span class="m">ESP Standalone Rental Server</span></h2>
<div id="setup" class="c hide"><h3 id="setupTitle">Initial setup</h3><div class="m">Connect this ESP to the Wi-Fi/LAN used by your rental phones. Settings are saved only after Wi-Fi association and DHCP succeed.</div>
<button onclick="scanWifi()">Scan Wi-Fi</button><div id="nets"></div>
<div class="g"><input id="ssid" placeholder="Wi-Fi SSID"><input id="wpass" type="password" placeholder="Wi-Fi password"><input id="adminpass" type="password" placeholder="Admin password 12+"><input id="recoverypass" type="password" placeholder="Recovery AP password 8+ (optional)"></div>
<button class="p" onclick="saveSetup()">Test, save and reboot</button><div id="setupMsg" class="m"></div></div>

<div id="login" class="c hide"><input id="pw" type="password" placeholder="Administrator password"><button class="p" onclick="loginNow()">Sign in</button><span id="loginMsg" class="m"></span></div>

<div id="app" class="hide">
<div class="c"><div class="r"><button onclick="refresh()">Dashboard</button><button onclick="enroll()">New enrollment</button><button onclick="events()">Events</button></div><div id="status" class="m"></div><div id="token"></div></div>
<div id="rentalBox" class="c"><h3>Rental devices</h3><div id="devices"></div></div>
<div class="c"><h3>Operating mode / Coin interfaces</h3>
<div class="g"><select id="mode"><option value="rental">1. Rental Server</option><option value="rental_coin">2. Rental Server + Local Coin Slot</option><option value="coin_interface">3. Remote Coin Slot Interface</option></select>
<input id="coinpin" type="number" placeholder="Local coin GPIO">
<input id="spp" type="number" value="600" placeholder="Seconds per pulse">
<input id="debounce" type="number" value="60" placeholder="Debounce ms">
<input id="remote" placeholder="Remote server IP / URL">
<input id="rkey" placeholder="Remote server binding key">
<input id="controller" placeholder="Controller ID"></div>
<div class="m">Mode 1 and 2 can also accept separate remote ESP coin interfaces. Give those ESPs this server IP plus the binding key below.</div>
<div class="mono" id="binding"></div>
<button onclick="saveSettings()">Save mode / coin settings</button><div id="remotes"></div></div>

<div class="c"><h3>Network / System</h3><div class="g"><input id="newssid" placeholder="New Wi-Fi SSID"><input id="newwifi" type="password" placeholder="New Wi-Fi password"><input id="newadmin" type="password" placeholder="New admin password 12+"></div>
<div class="r"><button onclick="changeWifi()">Test and change Wi-Fi</button><button onclick="changeAdmin()">Change admin password</button></div></div>
</div></div>
<script>
let S=sessionStorage.s||'';const q=s=>document.querySelector(s),form=o=>{let p=new URLSearchParams;Object.entries(o||{}).forEach(([k,v])=>p.append(k,v==null?'':v));return p};
async function post(u,o,auth=true){let h={'Content-Type':'application/x-www-form-urlencoded'};if(auth)h['X-Blaze-Session']=S;let r=await fetch(u,{method:'POST',headers:h,body:form(o)});return r.json()}
async function boot(){let p=await fetch('/api/public').then(r=>r.json());if(p.setup_mode){q('#setup').classList.remove('hide');q('#setupTitle').textContent=p.recovery_mode?'Wi-Fi recovery':'Initial setup';if(p.ssid)q('#ssid').value=p.ssid;return}q('#login').classList.remove('hide');if(S)show()}
async function scanWifi(){q('#nets').innerHTML='Scanning...';let j=await fetch('/api/scan').then(r=>r.json());q('#nets').innerHTML=(j.networks||[]).map(n=>'<div class=net onclick="q(\\'#ssid\\').value=this.dataset.s" data-s="'+n.ssid.replace(/"/g,'&quot;')+'"><b>'+n.ssid+'</b> <span class=m>'+n.rssi+' dBm '+(n.secure?'secured':'open')+'</span></div>').join('')}
async function saveSetup(){q('#setupMsg').textContent='Testing Wi-Fi...';let j=await post('/api/setup',{ssid:q('#ssid').value,wifi_password:q('#wpass').value,admin_password:q('#adminpass').value,recovery_ap_password:q('#recoverypass').value},false);if(!j.ok){q('#setupMsg').textContent=j.error;return}q('#setupMsg').innerHTML='<span class=good>Connected. Assigned IP: <b>'+j.ip+'</b>. Saved. Rebooting in '+j.reboot_in+' seconds.</span>'}
async function loginNow(){let j=await post('/api/login',{password:q('#pw').value},false);if(!j.ok){q('#loginMsg').textContent=j.error;return}S=j.session;sessionStorage.s=S;show()}
async function show(){q('#login').classList.add('hide');q('#app').classList.remove('hide');await post('/api/admin',{action:'time',epoch:Math.floor(Date.now()/1000)});refresh()}
async function refresh(){let s=await post('/api/admin',{action:'status'});if(!s.ok){sessionStorage.removeItem('s');location.reload();return}q('#status').innerHTML='<b>'+s.mode+'</b> · IP '+s.ip+' · '+s.ssid+' · '+s.rssi+' dBm · '+(s.internet?'<span class=good>Internet OK</span>':'<span class=m>Internet unavailable; local service active</span>')+' · heap '+s.heap;q('#mode').value=s.mode;q('#coinpin').value=s.coin_pin;q('#spp').value=s.seconds_per_pulse;q('#remote').value=s.remote_host||'';q('#controller').value=s.controller_id||'';q('#binding').textContent='Remote coin binding key: '+s.binding_key;q('#rentalBox').classList.toggle('hide',s.mode==='coin_interface');q('#remotes').innerHTML='<h4>Remote coin interfaces</h4>'+(s.remote_coin_list||[]).map(x=>'<div class=d><b>'+x.id+'</b> · '+x.ip+' · last seen '+x.last_seen+(x.busy?' · BUSY':' · available')+'</div>').join('')||'<span class=m>No remote ESP coin interface seen yet.</span>';let j=await post('/api/admin',{action:'list'});q('#devices').innerHTML=(j.devices||[]).map(d=>'<div class=d><b>'+d.label+'</b> <span class=mono>'+d.device_id+'</span><br>lease '+new Date(d.lease_until*1000).toLocaleString()+' · '+d.launcher_mode+' · preferred '+(d.preferred_vendo||'automatic')+'<div class=r><button onclick="add(\\''+d.device_id+'\\',600)">+10m</button><button onclick="add(\\''+d.device_id+'\\',3600)">+1h</button><button onclick="setTime(\\''+d.device_id+'\\')">Set</button><button onclick="policy(\\''+d.device_id+'\\',\\''+encodeURIComponent(d.allowed_packages)+'\\',\\''+encodeURIComponent(d.hidden_packages)+'\\',\\''+encodeURIComponent(d.preferred_vendo||'')+'\\')">Policy</button><button onclick="devpass(\\''+d.device_id+'\\')">Device admin</button><button onclick="expire(\\''+d.device_id+'\\')">Expire</button><button class=danger onclick="revoke(\\''+d.device_id+'\\')">Revoke</button></div></div>').join('')||'<span class=m>No enrolled devices.</span>'}
async function enroll(){let label=prompt('Device label','Rental phone');if(!label)return;let j=await post('/api/admin',{action:'enroll',label});if(j.ok)q('#token').innerHTML='<div class=c><b>Server:</b> http://'+location.host+'<br><b>Token:</b> <span class=mono>'+j.token+'</span><br>Valid 10 minutes.</div>';else alert(j.error)}
async function add(id,s){let j=await post('/api/admin',{action:'add_time',device_id:id,seconds:s});if(!j.ok)alert(j.error);refresh()}
async function setTime(id){let m=prompt('Remaining minutes','60');if(m==null)return;let j=await post('/api/admin',{action:'set_time',device_id:id,seconds:Math.max(0,Math.round(Number(m)*60))});if(!j.ok)alert(j.error);refresh()}
async function expire(id){await post('/api/admin',{action:'expire',device_id:id});refresh()}
async function revoke(id){if(confirm('Revoke this device?')){await post('/api/admin',{action:'revoke',device_id:id});refresh()}}
async function policy(id,a,h,p){a=prompt('Allowed package IDs (* for all)',decodeURIComponent(a));if(a==null)return;h=prompt('Hidden package IDs',decodeURIComponent(h));if(h==null)return;p=prompt('Preferred coin interface ID (blank = automatic, local = onboard slot)',decodeURIComponent(p));if(p==null)return;let j=await post('/api/admin',{action:'policy',device_id:id,launcher_mode:'rental',allowed:a,hidden:h,preferred:p,timer_mode:'overlay',timer_toggle:1,quick:'volume_down,volume_up,floating_timer,network_status,battery_status,bluetooth_status,flashlight',notifications:1,grace:0});if(!j.ok)alert(j.error);refresh()}
async function devpass(id){let p=prompt('Device administrator password 8+');if(!p)return;let j=await post('/api/admin',{action:'device_admin',device_id:id,password:p});if(!j.ok)alert(j.error);refresh()}
async function saveSettings(){let j=await post('/api/admin',{action:'settings',mode:q('#mode').value,coin_pin:q('#coinpin').value||-1,coin_active_low:1,coin_debounce_ms:q('#debounce').value||60,seconds_per_pulse:q('#spp').value||600,coin_window:120,remote_host:q('#remote').value,remote_key:q('#rkey').value,controller_id:q('#controller').value});alert(j.ok?'Saved.':j.error);refresh()}
async function changeWifi(){let j=await post('/api/admin',{action:'change_wifi',ssid:q('#newssid').value,wifi_password:q('#newwifi').value});if(!j.ok)return alert(j.error);alert('Connected. New IP: '+j.ip+'. Rebooting in '+j.reboot_in+' seconds.')}
async function changeAdmin(){let p=q('#newadmin').value;if(p.length<12)return alert('Use at least 12 characters');let j=await post('/api/admin',{action:'change_password',password:p});if(j.ok){sessionStorage.removeItem('s');location.reload()}else alert(j.error)}
async function events(){let j=await post('/api/admin',{action:'events'});alert((j.events||[]).join('\\n'))}
boot();
</script></body></html>
)HTML";
