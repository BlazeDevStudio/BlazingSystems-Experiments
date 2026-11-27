/*
  =========================================================================
  ESP8266 Standalone Access Point + Web-Based LED Controller
  =========================================================================
  What this does:
    - Turns the ESP8266 into its own WiFi hotspot (Access Point / "AP" mode).
    - Serves a small control webpage directly over raw TCP sockets
      (WiFiServer / WiFiClient) - NOT the ESP8266WebServer library.
    - The page lets you tune the onboard LED's behaviour:
        * Enabled   - on/off
        * Mode      - Blink / Fade (breathing) / Solid
        * Speed     - how fast it blinks/fades       (ms)
        * Amount    - how many blinks/fades per burst
        * Pause     - rest time between bursts        (ms)
        * Intensity - brightness while "on"           (0-100%, PWM)

  Why (almost) no libraries:
    The ONLY library used is <ESP8266WiFi.h> - the core driver for the
    chip's WiFi radio. There is no way to do networking on this chip
    without it. Everything else (HTTP parsing, HTML building, PWM
    fading, non-blocking timing) is written by hand with plain C++ and
    core Arduino functions (millis(), analogWrite(), String), so there
    is nothing extra to install beyond the standard "esp8266" board
    package - no ESP8266WebServer, ArduinoJson, Ticker, or WiFiManager.

  How to use:
    1. Edit AP_SSID / AP_PASSWORD / LED_PIN below if you want to.
    2. Flash this to your ESP8266 board.
    3. On your phone or laptop, connect to the WiFi network AP_SSID.
    4. Open a browser to  http://192.168.4.1/
    5. Adjust the sliders, hit Apply.

  Board notes:
    - GPIO2 (silkscreen "D4" on NodeMCU / Wemos D1 mini) is the most
      common onboard LED pin and is used by default. It is almost
      always wired ACTIVE-LOW (LOW = LED on), hence LED_ACTIVE_LOW=true.
    - If your onboard LED doesn't react, flip LED_ACTIVE_LOW, or change
      LED_PIN to match your specific board.
  =========================================================================
*/

#include <ESP8266WiFi.h>

// Compatibility: some ESP8266 core versions do not expose PWMRANGE
#ifndef PWMRANGE
#define PWMRANGE 1023
#endif

// Explicit prototypes (keeps compilation reliable with different Arduino IDE/core versions)
void handleClient();
String getQueryParam(const String& query, const String& key);
void applySettings(const String& query);
void sendRedirect(WiFiClient& client, const String& location);
void send404(WiFiClient& client);
void sendPage(WiFiClient& client);
int percentToPwm(unsigned int pct);
void writeLed(int pwmValue);
void updateLed();

// ------------------------- USER CONFIGURATION -------------------------
const char*   AP_SSID        = "ESP8266-LED"; // hotspot name
const char*   AP_PASSWORD    = "CHANGE_ME";    // public placeholder; replace before flashing
const uint8_t LED_PIN        = 2;              // GPIO2 = onboard LED on most boards
const bool    LED_ACTIVE_LOW = true;           // true: LOW turns the LED on
// ------------------------------------------------------------------------

WiFiServer server(80);

// ---------------------- Settings (changed from the web page) ----------------------
enum LedMode : uint8_t { MODE_BLINK = 0, MODE_FADE = 1, MODE_SOLID = 2 };

bool          ledEnabled   = true;
LedMode       ledMode      = MODE_BLINK;
unsigned long speedMs      = 500;   // 10-5000 ms
unsigned int  amountBlinks = 3;     // 0-100 blinks/fades per burst
unsigned long pauseMs      = 1000;  // 0-20000 ms
unsigned int  intensityPct = 100;   // 0-100 %

// ---------------------------- LED state machine -----------------------------------
bool          inBurstPause = false;
unsigned long phaseStart   = 0;
unsigned int  cycleCount   = 0;
bool          blinkOn      = false;
int           fadeVal      = 0;
int           fadeDir      = 1;
unsigned long lastStepTime = 0;

void setup() {
  Serial.begin(115200);
  delay(50);

  pinMode(LED_PIN, OUTPUT);
  analogWriteRange(1023);
  analogWriteFreq(1000);
  writeLed(0);

  WiFi.persistent(false);
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);

  Serial.println();
  Serial.print(F("Access Point started. SSID: "));
  Serial.println(AP_SSID);
  Serial.print(F("Connect a browser to: http://"));
  Serial.println(WiFi.softAPIP());

  server.begin();
}

void loop() {
  handleClient();
  updateLed();
}

// ================================================================
//  Tiny hand-rolled HTTP server (GET only, no external libraries)
// ================================================================

void handleClient() {
  WiFiClient client = server.available();
  if (!client) return;

  unsigned long waitStart = millis();
  while (!client.available()) {
    if (millis() - waitStart > 1000) { client.stop(); return; }
    delay(1);
  }

  String requestLine = client.readStringUntil('\n');
  requestLine.trim();

  // Discard the remaining request headers - we don't need them here.
  while (client.connected()) {
    String line = client.readStringUntil('\n');
    line.trim();
    if (line.length() == 0) break;
  }

  // requestLine looks like: "GET /set?speed=200&amount=3 HTTP/1.1"
  int sp1 = requestLine.indexOf(' ');
  int sp2 = requestLine.indexOf(' ', sp1 + 1);
  if (sp1 == -1 || sp2 == -1) { client.stop(); return; }
  String fullPath = requestLine.substring(sp1 + 1, sp2);

  int q = fullPath.indexOf('?');
  String route = (q == -1) ? fullPath : fullPath.substring(0, q);
  String query = (q == -1) ? ""       : fullPath.substring(q + 1);

  if (route == "/") {
    sendPage(client);
  } else if (route == "/set") {
    applySettings(query);
    sendRedirect(client, "/");
  } else {
    send404(client);
  }

  delay(1);
  client.stop();
}

// Returns the LAST value for `key` in an "a=1&b=2" style query string.
// Reading the last match lets a hidden fallback + checkbox share one
// name, which is how the "Enabled" checkbox below always sends a real
// 0/1 value even when unchecked.
String getQueryParam(const String& query, const String& key) {
  String result = "";
  int start = 0;
  while (start < (int)query.length()) {
    int amp = query.indexOf('&', start);
    if (amp == -1) amp = query.length();
    String pair = query.substring(start, amp);
    int eq = pair.indexOf('=');
    if (eq != -1 && pair.substring(0, eq) == key) {
      result = pair.substring(eq + 1);
    }
    start = amp + 1;
  }
  return result;
}

void applySettings(const String& query) {
  String v;

  v = getQueryParam(query, "enabled");
  ledEnabled = (v == "1");

  v = getQueryParam(query, "mode");
  if (v == "fade")       ledMode = MODE_FADE;
  else if (v == "solid") ledMode = MODE_SOLID;
  else                   ledMode = MODE_BLINK;

  v = getQueryParam(query, "speed");
  if (v.length()) speedMs = constrain(v.toInt(), 10L, 5000L);

  v = getQueryParam(query, "amount");
  if (v.length()) amountBlinks = constrain(v.toInt(), 0L, 100L);

  v = getQueryParam(query, "pause");
  if (v.length()) pauseMs = constrain(v.toInt(), 0L, 20000L);

  v = getQueryParam(query, "intensity");
  if (v.length()) intensityPct = constrain(v.toInt(), 0L, 100L);

  // Restart the pattern cleanly.
  inBurstPause = false;
  cycleCount   = 0;
  blinkOn      = false;
  fadeVal      = 0;
  fadeDir      = 1;
  phaseStart   = millis();
  lastStepTime = millis();

  // Apply the new state immediately instead of waiting for the next tick.
  if (!ledEnabled || amountBlinks == 0) {
    writeLed(0);
  } else if (ledMode == MODE_SOLID) {
    writeLed(percentToPwm(intensityPct));
  } else {
    writeLed(0);
  }
}

void sendRedirect(WiFiClient& client, const String& location) {
  client.print(F("HTTP/1.1 302 Found\r\n"));
  client.print("Location: " + location + "\r\n");
  client.print(F("Connection: close\r\n\r\n"));
}

void send404(WiFiClient& client) {
  String body = F("<h3>404 Not Found</h3>");
  client.print(F("HTTP/1.1 404 Not Found\r\n"));
  client.print(F("Content-Type: text/html\r\n"));
  client.print("Content-Length: " + String(body.length()) + "\r\n");
  client.print(F("Connection: close\r\n\r\n"));
  client.print(body);
}

void sendPage(WiFiClient& client) {
  client.print(F("HTTP/1.1 200 OK\r\n"));
  client.print(F("Content-Type: text/html\r\n"));
  client.print(F("Connection: close\r\n\r\n"));

  client.print(F("<!DOCTYPE html><html><head>"));
  client.print(F("<meta name='viewport' content='width=device-width,initial-scale=1'>"));
  client.print(F("<title>ESP8266 LED Control</title>"));
  client.print(F("<style>"));
  client.print(F("body{font-family:sans-serif;background:#111;color:#eee;padding:20px;max-width:420px;margin:auto}"));
  client.print(F("h2{color:#4fc3f7;margin-bottom:4px}"));
  client.print(F("label{display:block;margin-top:18px;font-size:14px;color:#aaa}"));
  client.print(F("input[type=range]{width:100%;margin-top:6px}"));
  client.print(F("select{width:100%;padding:8px;margin-top:4px;background:#222;color:#eee;border:1px solid #444;border-radius:4px}"));
  client.print(F(".row{display:flex;justify-content:space-between;align-items:center}"));
  client.print(F("button{margin-top:26px;width:100%;padding:12px;background:#4fc3f7;color:#000;border:none;border-radius:6px;font-size:16px;font-weight:bold}"));
  client.print(F(".val{color:#4fc3f7;font-weight:bold}"));
  client.print(F("input[type=checkbox]{width:20px;height:20px}"));
  client.print(F("</style></head><body>"));
  client.print(F("<h2>ESP8266 LED Control</h2>"));
  client.print(F("<form action='/set' method='GET'>"));

  // Enabled
  client.print(F("<div class='row'><label style='margin:0'>LED Enabled</label><input type='hidden' name='enabled' value='0'><input type='checkbox' name='enabled' value='1'"));
  if (ledEnabled) client.print(F(" checked"));
  client.print(F("></div>"));

  // Mode
  client.print(F("<label>Mode</label><select name='mode'>"));
  client.print(F("<option value='blink'"));
  if (ledMode == MODE_BLINK) client.print(F(" selected"));
  client.print(F(">Blink</option>"));
  client.print(F("<option value='fade'"));
  if (ledMode == MODE_FADE) client.print(F(" selected"));
  client.print(F(">Fade (breathing)</option>"));
  client.print(F("<option value='solid'"));
  if (ledMode == MODE_SOLID) client.print(F(" selected"));
  client.print(F(">Solid</option>"));
  client.print(F("</select>"));

  // Speed
  client.print(F("<label>Speed <span class='val' id='speedVal'>"));
  client.print(speedMs);
  client.print(F(" ms</span></label>"));
  client.print(F("<input type='range' name='speed' min='10' max='3000' value='"));
  client.print(speedMs);
  client.print(F("' oninput=\"speedVal.textContent=this.value+' ms'\">"));

  // Amount
  client.print(F("<label>Amount <span class='val' id='amtVal'>"));
  client.print(amountBlinks);
  client.print(F(" per burst</span></label>"));
  client.print(F("<input type='range' name='amount' min='0' max='100' value='"));
  client.print(amountBlinks);
  client.print(F("' oninput=\"amtVal.textContent=this.value+' per burst'\">"));

  // Pause
  client.print(F("<label>Pause between bursts <span class='val' id='pauseVal'>"));
  client.print(pauseMs);
  client.print(F(" ms</span></label>"));
  client.print(F("<input type='range' name='pause' min='0' max='5000' step='50' value='"));
  client.print(pauseMs);
  client.print(F("' oninput=\"pauseVal.textContent=this.value+' ms'\">"));

  // Intensity
  client.print(F("<label>Intensity <span class='val' id='intVal'>"));
  client.print(intensityPct);
  client.print(F("%</span></label>"));
  client.print(F("<input type='range' name='intensity' min='0' max='100' value='"));
  client.print(intensityPct);
  client.print(F("' oninput=\"intVal.textContent=this.value+'%'\">"));

  client.print(F("<button type='submit'>Apply</button>"));
  client.print(F("</form></body></html>"));
}

// ================================================================
//  LED pattern engine (non-blocking, millis()-based)
// ================================================================

int percentToPwm(unsigned int pct) {
  if (pct > 100) pct = 100;
  return (int)((uint32_t)pct * PWMRANGE / 100);
}

void writeLed(int pwmValue) {
  if (pwmValue < 0) pwmValue = 0;
  if (pwmValue > PWMRANGE) pwmValue = PWMRANGE;
  if (LED_ACTIVE_LOW) pwmValue = PWMRANGE - pwmValue;
  analogWrite(LED_PIN, pwmValue);
}

void updateLed() {
  unsigned long now = millis();

  if (!ledEnabled || amountBlinks == 0) {
    writeLed(0);
    return;
  }

  if (ledMode == MODE_SOLID) {
    writeLed(percentToPwm(intensityPct));
    return;
  }

  if (inBurstPause) {
    writeLed(0);
    if (now - phaseStart >= pauseMs) {
      inBurstPause = false;
      cycleCount   = 0;
      blinkOn      = false;
      fadeVal      = 0;
      fadeDir      = 1;
      lastStepTime = now;
    }
    return;
  }

  const int maxPwm = percentToPwm(intensityPct);

  if (ledMode == MODE_BLINK) {
    if (now - lastStepTime >= speedMs) {
      lastStepTime = now;
      blinkOn = !blinkOn;
      writeLed(blinkOn ? maxPwm : 0);

      // Count one completed ON+OFF blink.
      if (!blinkOn) {
        cycleCount++;
        if (cycleCount >= amountBlinks) {
          inBurstPause = true;
          phaseStart = now;
        }
      }
    }
  }
  else { // MODE_FADE
    // speedMs is approximately the full fade-in time.
    unsigned long stepInterval = speedMs / 40UL;
    if (stepInterval < 5UL) stepInterval = 5UL;

    if (now - lastStepTime >= stepInterval) {
      lastStepTime = now;

      int step = maxPwm / 40;
      if (step < 1) step = 1;

      fadeVal += fadeDir * step;

      if (fadeVal >= maxPwm) {
        fadeVal = maxPwm;
        fadeDir = -1;
      }
      else if (fadeVal <= 0) {
        fadeVal = 0;
        fadeDir = 1;

        cycleCount++;
        if (cycleCount >= amountBlinks) {
          inBurstPause = true;
          phaseStart = now;
        }
      }

      writeLed(fadeVal);
    }
  }
}
