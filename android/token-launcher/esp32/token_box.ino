#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>

// CHANGE ALL THREE VALUES BEFORE DEPLOYMENT.
const char* AP_SSID = "TokenBox-Setup";
const char* AP_PASS = "CHANGE_ME_AP_PASSWORD";
const char* ADMIN_PASSWORD = "CHANGE_ME_ADMIN_PASSWORD";
const char* TOKEN_API_KEY = "CHANGE_ME_TOKEN_API_KEY";

WebServer server(80);
Preferences prefs;

void sendJson(int code, const String& body){ server.send(code,"application/json",body); }
bool adminOK(){ return server.arg("p") == ADMIN_PASSWORD; }
bool tokenOK(){ return server.arg("k") == TOKEN_API_KEY; }

void handleRoot(){
 String html = R"HTML(
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>Token Box</title></head>
<body><h2>ESP32 Token Box</h2>
<p>Configure token duration and dispense test time.</p>
<form action='/admin/set' method='post'>Admin password <input name='p' type='password'><br>Seconds <input name='s' type='number' min='1' max='86400' value='1800'><button>Save</button></form>
<hr>
<form action='/admin/test' method='post'>Admin password <input name='p' type='password'><button>Dispense test token</button></form>
</body></html>)HTML";
 server.send(200,"text/html",html);
}

void handleSet(){
 if(!adminOK()){server.send(403,"text/plain","Forbidden");return;}
 uint32_t s=server.arg("s").toInt();
 if(s<1||s>86400) s=1800;
 prefs.putUInt("seconds",s);
 server.send(200,"text/plain","Saved");
}

void handleTest(){
 if(!adminOK()){server.send(403,"text/plain","Forbidden");return;}
 uint32_t s=prefs.getUInt("seconds",1800);
 prefs.putUInt("credit",s);
 server.send(200,"text/plain",String("Credit loaded: ")+s+" seconds");
}

void handleToken(){
 if(!tokenOK()){sendJson(403,"{\"error\":\"forbidden\"}");return;}
 uint32_t s=prefs.getUInt("credit",0);
 if(s==0){sendJson(200,"{\"seconds\":0}");return;}
 prefs.putUInt("credit",0);
 sendJson(200,String("{\"seconds\":")+s+"}");
}

void setup(){
 Serial.begin(115200);
 prefs.begin("tokenbox",false);
 if(!prefs.getUInt("seconds",0)) prefs.putUInt("seconds",1800);

 WiFi.mode(WIFI_AP);
 if(!WiFi.softAP(AP_SSID,AP_PASS)){
   Serial.println("AP start failed");
 }
 Serial.print("Token Box IP: ");
 Serial.println(WiFi.softAPIP());

 server.on("/",HTTP_GET,handleRoot);
 server.on("/admin/set",HTTP_POST,handleSet);
 server.on("/admin/test",HTTP_POST,handleTest);
 server.on("/api/token",HTTP_POST,handleToken);
 server.begin();
}

void loop(){ server.handleClient(); }
