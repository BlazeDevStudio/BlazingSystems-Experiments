/*
  BlazeSystems ESP8266 Arcade — Public-Safe Shell
  ------------------------------------------------
  Reconstructed public derivative of an earlier private ESP8266 arcade study.

  Public edition intentionally excludes:
    - commercial ROMs / BIOS files
    - third-party emulator cores
    - copied game assets
    - private Wi-Fi credentials

  Features:
    - ESP8266 access point
    - captive DNS redirect
    - local HTTP portal
    - optional STA + NAPT Internet sharing when supported by the selected core
    - original browser mini-game served from PROGMEM

  Validation status:
    Source-ready experiment. Compile and target-board validation are still required.
*/

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <DNSServer.h>

#if LWIP_FEATURES && !LWIP_IPV6
  #include <lwip/napt.h>
  #include <lwip/dns.h>
  #define BLAZE_NAPT_SUPPORTED 1
#else
  #define BLAZE_NAPT_SUPPORTED 0
#endif

ESP8266WebServer server(80);
DNSServer dns;

static const uint8_t DNS_PORT = 53;
static const IPAddress AP_IP(192, 168, 4, 1);
static const IPAddress AP_MASK(255, 255, 255, 0);

// Optional upstream Wi-Fi. Keep blank in public source.
static const char* STA_SSID = "";
static const char* STA_PASSWORD = "";

String apSsid;
String apPassword;
bool staConnected = false;
bool naptEnabled = false;

String chipSuffix() {
  char buf[7];
  snprintf(buf, sizeof(buf), "%06X", ESP.getChipId() & 0xFFFFFF);
  return String(buf);
}

void buildCredentials() {
  String suffix = chipSuffix();
  apSsid = "BlazeArcade-" + suffix;
  apPassword = "BA-" + suffix + "-Play";
}

const char PAGE[] PROGMEM = R"HTML(
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>BlazeSystems ESP8266 Arcade</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:#08101a;color:#eef6ff;font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:820px;margin:auto;padding:22px}
header,.card{background:#111c29;border:1px solid #27394c;border-radius:16px;padding:18px;margin-bottom:14px}
.tag{font-size:11px;color:#73b5ff;letter-spacing:.12em;text-transform:uppercase;font-weight:800}
h1{margin:.25em 0}.muted{color:#91a6bb}.grid{display:grid;grid-template-columns:1fr 240px;gap:14px}
canvas{width:100%;aspect-ratio:16/9;background:#05090e;border-radius:12px;display:block}
button{border:1px solid #35506b;background:#1769aa;color:white;border-radius:10px;padding:10px 14px;font:inherit;font-weight:700;cursor:pointer}
.stat{padding:9px 0;border-bottom:1px solid #263748}.stat:last-child{border:0}
kbd{background:#07111a;border:1px solid #33485e;border-radius:5px;padding:1px 5px}
@media(max-width:680px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body><main>
<header>
<div class="tag">ESP8266 · Public-Safe Experiment</div>
<h1>BlazeSystems Arcade</h1>
<p class="muted">Captive arcade shell running entirely from the ESP8266. No ROMs, BIOS files, emulator cores, or third-party game assets are bundled.</p>
</header>
<div class="grid">
<section class="card">
<canvas id="game" width="640" height="360"></canvas>
<p><button id="restart">Start / Restart</button></p>
<p class="muted">Move with <kbd>←</kbd> <kbd>→</kbd> or <kbd>A</kbd> <kbd>D</kbd>. Avoid the falling blocks.</p>
</section>
<aside class="card">
<h3>Device</h3>
<div class="stat">Portal: <b>local</b></div>
<div class="stat">Game: <b>original demo</b></div>
<div class="stat">Storage: <b>none required</b></div>
<div class="stat">External runtime: <b>none</b></div>
<p class="muted">This edition demonstrates the embedded web/captive-portal architecture without redistributing third-party runtime content.</p>
</aside>
</div>
<script>
const c=document.getElementById('game'),x=c.getContext('2d'),scoreEl={v:0};
let px=300,blocks=[],score=0,running=false,last=0,left=false,right=false;
function reset(){px=300;blocks=[];score=0;running=true;last=performance.now();requestAnimationFrame(loop)}
function loop(t){
 if(!running)return;
 const dt=Math.min(.04,(t-last)/1000);last=t;
 if(left)px=Math.max(0,px-260*dt);if(right)px=Math.min(600,px+260*dt);
 if(Math.random()<dt*2.1)blocks.push({x:Math.random()*610,y:-25,s:18+Math.random()*22,v:100+Math.random()*150});
 x.fillStyle='#07101a';x.fillRect(0,0,640,360);
 x.fillStyle='#18283b';for(let i=0;i<14;i++)x.fillRect(i*50,310,32,50);
 x.fillStyle='#67b4ff';x.fillRect(px,320,40,22);
 for(const b of blocks){
   b.y+=b.v*dt;x.fillStyle='#ff6f7c';x.fillRect(b.x,b.y,b.s,b.s);
   if(b.y>300&&b.y<345&&b.x<px+40&&b.x+b.s>px)running=false;
   if(b.y>380)score++;
 }
 blocks=blocks.filter(b=>b.y<390);
 x.fillStyle='#fff';x.font='bold 16px system-ui';x.fillText('Score: '+score,14,25);
 if(running)requestAnimationFrame(loop);else{x.font='bold 28px system-ui';x.fillText('GAME OVER',235,180)}
}
addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')left=true;if(k==='arrowright'||k==='d')right=true});
addEventListener('keyup',e=>{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')left=false;if(k==='arrowright'||k==='d')right=false});
restart.onclick=reset;reset();
</script>
</main></body></html>
)HTML";

void redirectToPortal() {
  server.sendHeader("Location", String("http://") + AP_IP.toString() + "/", true);
  server.send(302, "text/plain", "");
}

void setupRoutes() {
  server.on("/", HTTP_GET, []() {
    server.send_P(200, "text/html; charset=utf-8", PAGE);
  });

  server.on("/status", HTTP_GET, []() {
    String json = "{";
    json += "\"ap_ssid\":\"" + apSsid + "\",";
    json += "\"sta_connected\":" + String(staConnected ? "true" : "false") + ",";
    json += "\"napt_enabled\":" + String(naptEnabled ? "true" : "false") + ",";
    json += "\"free_heap\":" + String(ESP.getFreeHeap());
    json += "}";
    server.send(200, "application/json", json);
  });

  server.on("/generate_204", HTTP_ANY, redirectToPortal);
  server.on("/gen_204", HTTP_ANY, redirectToPortal);
  server.on("/hotspot-detect.html", HTTP_ANY, redirectToPortal);
  server.on("/connecttest.txt", HTTP_ANY, redirectToPortal);
  server.on("/ncsi.txt", HTTP_ANY, redirectToPortal);
  server.onNotFound(redirectToPortal);
}

void connectUpstream() {
  if (!STA_SSID || strlen(STA_SSID) == 0) return;

  WiFi.begin(STA_SSID, STA_PASSWORD);
  uint32_t started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 10000UL) {
    delay(50);
    yield();
  }

  staConnected = WiFi.status() == WL_CONNECTED;

#if BLAZE_NAPT_SUPPORTED
  if (staConnected) {
    ip_napt_init(512, 8);
    naptEnabled = ip_napt_enable_no(SOFTAP_IF, 1) == 0;
  }
#endif
}

void setup() {
  Serial.begin(115200);
  delay(20);

  buildCredentials();

  WiFi.persistent(false);
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAPConfig(AP_IP, AP_IP, AP_MASK);
  WiFi.softAP(apSsid.c_str(), apPassword.c_str());

  dns.setErrorReplyCode(DNSReplyCode::NoError);
  dns.start(DNS_PORT, "*", AP_IP);

  connectUpstream();
  setupRoutes();
  server.begin();

  Serial.println();
  Serial.println("BlazeSystems ESP8266 Arcade public shell");
  Serial.println("AP SSID: " + apSsid);
  Serial.println("AP password: " + apPassword);
  Serial.println("Portal: http://" + AP_IP.toString());
}

void loop() {
  dns.processNextRequest();
  server.handleClient();
  yield();
}
