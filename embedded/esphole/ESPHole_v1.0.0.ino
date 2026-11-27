/*
  ESPHole
  =======
  Pi-hole-style DNS sinkhole + captive setup portal + ESP8266 Wi-Fi repeater/NAPT.

  Target:
    ESP8266 Arduino Core 3.1.2 (NodeMCU / Wemos D1 mini / ESP-12E class boards)

  Uses ONLY libraries bundled with the ESP8266 Arduino core:
    - ESP8266WiFi
    - ESP8266WebServer
    - WiFiUdp
    - LittleFS
    - lwIP NAPT support when available in the selected core/lwIP build

  Default first-boot access:
    Wi-Fi AP : ESPHole-XXXXXX
    AP key   : esphole123
    Admin    : admin
    Password : esphole

    Open: http://192.168.4.1/

  What it does:
    * AP+STA Wi-Fi range extender using IPv4 NAPT when supported.
    * Advertises ESPHole itself (192.168.4.1) as DNS to AP clients.
    * Parses DNS questions locally.
    * Blocks domains and all their subdomains from /blocklist.txt.
    * Forwards allowed DNS packets to an upstream resolver.
    * First-boot/offline captive DNS sends clients to the setup page.
    * Web UI for Wi-Fi, upstream DNS, blocklist, stats and enable/disable.
    * Stores settings and the blocklist in LittleFS.
    * Accepts plain-domain lists and common hosts-file syntax.
    * EasyMode-inspired dark/cyan web UI.
    * Optional D5/GPIO14 short activity chirp for DNS/admin traffic.

  Important limitations:
    * This is intentionally a small ESP8266 DNS sinkhole, NOT Linux Pi-hole.
    * IPv4 DNS only. NAPT is IPv4 only.
    * DNS-over-HTTPS / Android Private DNS / hard-coded external DNS can bypass it.
    * No recursive resolver, gravity database, regex engine, CNAME deep inspection,
      DHCP lease database, long-term database, TLS admin panel or millions-of-hosts list.
    * MAX_BLOCK_HASHES controls how many unique blocked suffixes are held in RAM.
    * FNV-1a hashes are used in RAM to save memory; source domains stay in LittleFS.

  Recommended Arduino settings:
    Board: NodeMCU 1.0 (ESP-12E Module) or matching ESP8266 board
    Flash: 4 MB where available
    lwIP : an IPv4 lwIP2 configuration with features/NAPT enabled
*/

struct DnsQuestion;  // Arduino .ino prototype-generator guard

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <WiFiUdp.h>
#include <LittleFS.h>

#ifndef ESP8266
  #error "ESPHole requires an ESP8266 target."
#endif

#if LWIP_FEATURES && !LWIP_IPV6
  #include <lwip/napt.h>
  #define ESPHOLE_HAS_NAPT 1
#else
  #define ESPHOLE_HAS_NAPT 0
#endif

// ----------------------------- Version --------------------------------------

static const char* ESPHOLE_VERSION = "1.0.0";

// ----------------------------- Network --------------------------------------

static const IPAddress AP_IP(192, 168, 4, 1);
static const IPAddress AP_GW(192, 168, 4, 1);
static const IPAddress AP_MASK(255, 255, 255, 0);

static const uint16_t DNS_PORT = 53;
static const uint16_t UPSTREAM_LOCAL_PORT = 53053;

static const uint16_t MAX_DNS_PACKET = 1232;
static const uint8_t  MAX_PENDING = 8;
static const uint32_t PENDING_TIMEOUT_MS = 3000;

// Network activity sound. NodeMCU D5 = GPIO14.
// tone() is built into the ESP8266 Arduino core and runs asynchronously.
static const uint8_t ACTIVITY_BUZZER_PIN = 14; // D5 / GPIO14 on NodeMCU and Wemos D1 mini
static const uint16_t DEFAULT_BUZZER_FREQ = 2600;
static const uint16_t DEFAULT_BUZZER_PULSE_MS = 7;
static const uint16_t DEFAULT_BUZZER_GAP_MS = 45;

#if ESPHOLE_HAS_NAPT
static const uint16_t NAPT_ENTRIES = 256;
static const uint8_t  NAPT_PORTMAP_ENTRIES = 16;
#endif

// ----------------------------- Storage --------------------------------------

static const char* CONFIG_FILE = "/config.txt";
static const char* BLOCK_FILE  = "/blocklist.txt";

static const uint16_t MAX_BLOCK_HASHES = 384;
static uint32_t blockHashes[MAX_BLOCK_HASHES];
static uint16_t blockCount = 0;

// Modest starter list. Replace/extend it from the web UI.
static const char DEFAULT_BLOCKLIST[] PROGMEM =
  "# ESPHole starter list\n"
  "# One domain per line. Subdomains are blocked automatically.\n"
  "doubleclick.net\n"
  "googlesyndication.com\n"
  "googleadservices.com\n"
  "googletagmanager.com\n"
  "amazon-adsystem.com\n"
  "adsystem.com\n"
  "scorecardresearch.com\n"
  "app-measurement.com\n"
  "crashlytics.com\n"
  "adjust.com\n"
  "appsflyer.com\n"
  "branch.io\n";

// ----------------------------- Settings -------------------------------------

struct Settings {
  String staSSID;
  String staPass;

  String apSSID;
  String apPass;

  String adminPass;

  bool dnsAuto;
  IPAddress customDNS;

  bool blockingEnabled;
  bool natEnabled;
  bool nullBlocking;     // false = NXDOMAIN, true = 0.0.0.0 for A queries

  bool activityBuzzerEnabled;
  uint16_t activityBuzzerFreq;
  uint16_t activityBuzzerPulseMs;
  uint16_t activityBuzzerMinGapMs;
};

Settings cfg;

// ----------------------------- Runtime --------------------------------------

ESP8266WebServer web(80);
WiFiUDP dnsUdp;
WiFiUDP upstreamUdp;

bool fsReady = false;
bool dnsReady = false;
bool upstreamUdpReady = false;
bool naptInitialized = false;
bool naptActive = false;

uint32_t lastWiFiRetry = 0;
wl_status_t lastWiFiState = WL_IDLE_STATUS;

uint32_t statQueries = 0;
uint32_t statBlocked = 0;
uint32_t statForwarded = 0;
uint32_t statReplies = 0;
uint32_t statErrors = 0;
String lastBlockedDomain;

// Shared packet buffers (global to avoid large stack frames)
uint8_t dnsIn[MAX_DNS_PACKET];
uint8_t dnsOut[MAX_DNS_PACKET + 32];

struct PendingQuery {
  bool used;
  uint16_t internalId;
  uint16_t originalId;
  IPAddress clientIP;
  uint16_t clientPort;
  uint32_t createdAt;
};

PendingQuery pending[MAX_PENDING];
uint16_t nextInternalId = 1;

uint32_t lastActivityBeepMs = 0;
uint32_t statActivityBeeps = 0;

// DNS question type is intentionally declared before any function definitions.
// Arduino IDE 1.x auto-generates prototypes and otherwise sees this type too late.
struct DnsQuestion {
  String domain;
  uint16_t type;
  uint16_t qclass;
  uint16_t questionEnd;
};

// ----------------------------- Utility --------------------------------------

static uint16_t rd16(const uint8_t* p) {
  return (uint16_t(p[0]) << 8) | uint16_t(p[1]);
}

static void wr16(uint8_t* p, uint16_t v) {
  p[0] = uint8_t(v >> 8);
  p[1] = uint8_t(v & 0xFF);
}

static void wr32(uint8_t* p, uint32_t v) {
  p[0] = uint8_t(v >> 24);
  p[1] = uint8_t(v >> 16);
  p[2] = uint8_t(v >> 8);
  p[3] = uint8_t(v);
}

static String stripCRLF(String s) {
  s.replace("\r", "");
  s.replace("\n", "");
  return s;
}

static String htmlEscape(const String& s) {
  String out;
  out.reserve(s.length() + 24);
  for (size_t i = 0; i < s.length(); ++i) {
    switch (s[i]) {
      case '&': out += F("&amp;");  break;
      case '<': out += F("&lt;");   break;
      case '>': out += F("&gt;");   break;
      case '"': out += F("&quot;"); break;
      case '\'': out += F("&#39;"); break;
      default: out += s[i]; break;
    }
  }
  return out;
}

static String jsonEscape(const String& s) {
  String out;
  out.reserve(s.length() + 16);
  for (size_t i = 0; i < s.length(); ++i) {
    char c = s[i];
    if (c == '"' || c == '\\') {
      out += '\\';
      out += c;
    } else if (c == '\n') {
      out += F("\\n");
    } else if (c == '\r') {
      out += F("\\r");
    } else if (uint8_t(c) >= 0x20) {
      out += c;
    }
  }
  return out;
}

static String humanBytes(uint32_t n) {
  if (n < 1024) return String(n) + F(" B");
  if (n < (1024UL * 1024UL)) return String(n / 1024.0f, 1) + F(" KB");
  return String(n / (1024.0f * 1024.0f), 2) + F(" MB");
}

static bool isZeroIP(const IPAddress& ip) {
  return ip[0] == 0 && ip[1] == 0 && ip[2] == 0 && ip[3] == 0;
}

static bool sameIP(const IPAddress& a, const IPAddress& b) {
  return a[0] == b[0] && a[1] == b[1] && a[2] == b[2] && a[3] == b[3];
}

static String boolWord(bool v) {
  return v ? F("ON") : F("OFF");
}

static uint16_t clampU16Arg(const String& raw, uint16_t fallback, uint16_t lo, uint16_t hi) {
  if (!raw.length()) return fallback;
  long v = raw.toInt();
  if (v < lo) v = lo;
  if (v > hi) v = hi;
  return uint16_t(v);
}

static void activityBeep(bool force) {
  if (!cfg.activityBuzzerEnabled) return;

  uint32_t now = millis();
  if (!force && uint32_t(now - lastActivityBeepMs) < cfg.activityBuzzerMinGapMs) return;

  lastActivityBeepMs = now;
  ++statActivityBeeps;
  tone(ACTIVITY_BUZZER_PIN, cfg.activityBuzzerFreq, cfg.activityBuzzerPulseMs);
}

// ----------------------------- Config ---------------------------------------

static void setDefaults() {
  cfg.staSSID = "";
  cfg.staPass = "";

  char apName[24];
  snprintf(apName, sizeof(apName), "ESPHole-%06X", ESP.getChipId());
  cfg.apSSID = apName;
  cfg.apPass = "esphole123";

  cfg.adminPass = "esphole";

  cfg.dnsAuto = true;
  cfg.customDNS = IPAddress(1, 1, 1, 1);

  cfg.blockingEnabled = true;
  cfg.natEnabled = true;
  cfg.nullBlocking = false;

  cfg.activityBuzzerEnabled = false;
  cfg.activityBuzzerFreq = DEFAULT_BUZZER_FREQ;
  cfg.activityBuzzerPulseMs = DEFAULT_BUZZER_PULSE_MS;
  cfg.activityBuzzerMinGapMs = DEFAULT_BUZZER_GAP_MS;
}

static void loadConfig() {
  setDefaults();
  if (!fsReady || !LittleFS.exists(CONFIG_FILE)) return;

  File f = LittleFS.open(CONFIG_FILE, "r");
  if (!f) return;

  while (f.available()) {
    String line = f.readStringUntil('\n');
    line.trim();
    if (!line.length() || line[0] == '#') continue;

    int eq = line.indexOf('=');
    if (eq < 1) continue;

    String k = line.substring(0, eq);
    String v = line.substring(eq + 1);
    k.trim();
    v.trim();

    if (k == F("sta_ssid")) cfg.staSSID = v;
    else if (k == F("sta_pass")) cfg.staPass = v;
    else if (k == F("ap_ssid")) cfg.apSSID = v;
    else if (k == F("ap_pass")) cfg.apPass = v;
    else if (k == F("admin_pass")) cfg.adminPass = v;
    else if (k == F("dns")) {
      if (v == F("auto")) {
        cfg.dnsAuto = true;
      } else {
        IPAddress ip;
        if (ip.fromString(v)) {
          cfg.dnsAuto = false;
          cfg.customDNS = ip;
        }
      }
    }
    else if (k == F("blocking")) cfg.blockingEnabled = (v != F("0"));
    else if (k == F("nat")) cfg.natEnabled = (v != F("0"));
    else if (k == F("null_blocking")) cfg.nullBlocking = (v == F("1"));
    else if (k == F("activity_buzzer")) cfg.activityBuzzerEnabled = (v == F("1"));
    else if (k == F("buzzer_freq")) cfg.activityBuzzerFreq = clampU16Arg(v, DEFAULT_BUZZER_FREQ, 200, 12000);
    else if (k == F("buzzer_pulse_ms")) cfg.activityBuzzerPulseMs = clampU16Arg(v, DEFAULT_BUZZER_PULSE_MS, 1, 100);
    else if (k == F("buzzer_gap_ms")) cfg.activityBuzzerMinGapMs = clampU16Arg(v, DEFAULT_BUZZER_GAP_MS, 15, 1000);
  }
  f.close();

  if (cfg.apSSID.length() < 1 || cfg.apSSID.length() > 31) {
    char apName[24];
    snprintf(apName, sizeof(apName), "ESPHole-%06X", ESP.getChipId());
    cfg.apSSID = apName;
  }

  if (cfg.apPass.length() && cfg.apPass.length() < 8) {
    cfg.apPass = "esphole123";
  }
  if (cfg.adminPass.length() < 4) {
    cfg.adminPass = "esphole";
  }
}

static bool saveConfig() {
  if (!fsReady) return false;

  cfg.staSSID = stripCRLF(cfg.staSSID);
  cfg.staPass = stripCRLF(cfg.staPass);
  cfg.apSSID = stripCRLF(cfg.apSSID);
  cfg.apPass = stripCRLF(cfg.apPass);
  cfg.adminPass = stripCRLF(cfg.adminPass);

  File f = LittleFS.open(CONFIG_FILE, "w");
  if (!f) return false;

  f.println(F("# ESPHole configuration"));
  f.print(F("sta_ssid=")); f.println(cfg.staSSID);
  f.print(F("sta_pass=")); f.println(cfg.staPass);
  f.print(F("ap_ssid=")); f.println(cfg.apSSID);
  f.print(F("ap_pass=")); f.println(cfg.apPass);
  f.print(F("admin_pass=")); f.println(cfg.adminPass);
  f.print(F("dns="));
  f.println(cfg.dnsAuto ? F("auto") : cfg.customDNS.toString());
  f.print(F("blocking=")); f.println(cfg.blockingEnabled ? 1 : 0);
  f.print(F("nat=")); f.println(cfg.natEnabled ? 1 : 0);
  f.print(F("null_blocking=")); f.println(cfg.nullBlocking ? 1 : 0);
  f.print(F("activity_buzzer=")); f.println(cfg.activityBuzzerEnabled ? 1 : 0);
  f.print(F("buzzer_freq=")); f.println(cfg.activityBuzzerFreq);
  f.print(F("buzzer_pulse_ms=")); f.println(cfg.activityBuzzerPulseMs);
  f.print(F("buzzer_gap_ms=")); f.println(cfg.activityBuzzerMinGapMs);
  f.close();
  return true;
}

// ----------------------------- Blocklist ------------------------------------

static uint32_t fnv1a(const String& s) {
  uint32_t h = 2166136261UL;
  for (size_t i = 0; i < s.length(); ++i) {
    h ^= uint8_t(s[i]);
    h *= 16777619UL;
  }
  return h;
}

static bool validDomainChars(const String& s) {
  if (!s.length() || s.length() > 253) return false;
  for (size_t i = 0; i < s.length(); ++i) {
    char c = s[i];
    bool ok =
      (c >= 'a' && c <= 'z') ||
      (c >= '0' && c <= '9') ||
      c == '-' || c == '.' || c == '_';
    if (!ok) return false;
  }
  return true;
}

static String domainFromBlockLine(String line) {
  int hash = line.indexOf('#');
  if (hash >= 0) line = line.substring(0, hash);
  line.trim();
  if (!line.length()) return "";

  line.replace('\t', ' ');
  while (line.indexOf(F("  ")) >= 0) line.replace(F("  "), F(" "));

  // Accept hosts-file syntax: 0.0.0.0 example.com / 127.0.0.1 example.com
  int sp = line.indexOf(' ');
  if (sp > 0) {
    String first = line.substring(0, sp);
    String rest = line.substring(sp + 1);
    rest.trim();

    IPAddress dummy;
    if (dummy.fromString(first)) {
      int sp2 = rest.indexOf(' ');
      line = (sp2 >= 0) ? rest.substring(0, sp2) : rest;
    } else {
      // If it is not hosts syntax, use only first token.
      line = first;
    }
  }

  line.trim();
  line.toLowerCase();

  if (line.startsWith(F("*."))) line.remove(0, 2);
  while (line.startsWith(F("."))) line.remove(0, 1);
  while (line.endsWith(F("."))) line.remove(line.length() - 1);

  if (!validDomainChars(line)) return "";
  return line;
}

static int hashCompare(const void* a, const void* b) {
  uint32_t aa = *(const uint32_t*)a;
  uint32_t bb = *(const uint32_t*)b;
  if (aa < bb) return -1;
  if (aa > bb) return 1;
  return 0;
}

static bool hashExists(uint32_t h) {
  int lo = 0;
  int hi = int(blockCount) - 1;

  while (lo <= hi) {
    int mid = (lo + hi) >> 1;
    uint32_t v = blockHashes[mid];
    if (v == h) return true;
    if (v < h) lo = mid + 1;
    else hi = mid - 1;
  }
  return false;
}

static void ensureDefaultBlocklist() {
  if (!fsReady || LittleFS.exists(BLOCK_FILE)) return;

  File f = LittleFS.open(BLOCK_FILE, "w");
  if (!f) return;
  f.print(FPSTR(DEFAULT_BLOCKLIST));
  f.close();
}

static void loadBlocklist() {
  blockCount = 0;
  if (!fsReady || !LittleFS.exists(BLOCK_FILE)) return;

  File f = LittleFS.open(BLOCK_FILE, "r");
  if (!f) return;

  while (f.available() && blockCount < MAX_BLOCK_HASHES) {
    String d = domainFromBlockLine(f.readStringUntil('\n'));
    if (!d.length()) continue;
    blockHashes[blockCount++] = fnv1a(d);
    yield();
  }
  f.close();

  qsort(blockHashes, blockCount, sizeof(blockHashes[0]), hashCompare);

  // Remove duplicate hashes in place.
  if (blockCount > 1) {
    uint16_t w = 1;
    for (uint16_t r = 1; r < blockCount; ++r) {
      if (blockHashes[r] != blockHashes[w - 1]) {
        blockHashes[w++] = blockHashes[r];
      }
    }
    blockCount = w;
  }
}

static bool saveBlocklistText(const String& raw, uint16_t& accepted) {
  accepted = 0;
  if (!fsReady) return false;

  File f = LittleFS.open(BLOCK_FILE, "w");
  if (!f) return false;

  int start = 0;
  const int n = raw.length();

  while (start <= n && accepted < MAX_BLOCK_HASHES) {
    int end = raw.indexOf('\n', start);
    if (end < 0) end = n;

    String d = domainFromBlockLine(raw.substring(start, end));
    if (d.length()) {
      f.println(d);
      ++accepted;
    }

    if (end >= n) break;
    start = end + 1;
    yield();
  }

  f.close();
  loadBlocklist();
  accepted = blockCount;
  return true;
}

static bool isBlockedDomain(String domain) {
  if (!cfg.blockingEnabled || blockCount == 0) return false;

  domain.trim();
  domain.toLowerCase();
  while (domain.endsWith(F("."))) domain.remove(domain.length() - 1);

  // Check domain and each parent suffix. A block for example.com therefore
  // also blocks ads.cdn.example.com.
  int start = 0;
  while (start < int(domain.length())) {
    String suffix = domain.substring(start);
    if (hashExists(fnv1a(suffix))) return true;

    int dot = domain.indexOf('.', start);
    if (dot < 0) break;
    start = dot + 1;
  }

  return false;
}

// ----------------------------- DNS ------------------------------------------

static bool parseDnsQuestion(const uint8_t* p, uint16_t len, DnsQuestion& q) {
  if (len < 17) return false;
  if (rd16(p + 4) != 1) return false; // exactly one question

  uint16_t pos = 12;
  String name;
  name.reserve(64);

  while (pos < len) {
    uint8_t labelLen = p[pos++];

    if (labelLen == 0) break;

    // Compression pointers are legal in DNS generally, but normal client
    // questions are uncompressed. Reject compressed QNAME instead of risking
    // a malformed parser on a tiny MCU.
    if ((labelLen & 0xC0) != 0) return false;
    if (labelLen > 63 || pos + labelLen > len) return false;

    if (name.length()) name += '.';

    for (uint8_t i = 0; i < labelLen; ++i) {
      char c = char(p[pos++]);
      if (c >= 'A' && c <= 'Z') c = char(c + ('a' - 'A'));
      name += c;
      if (name.length() > 253) return false;
    }
  }

  if (pos + 4 > len) return false;

  q.domain = name;
  q.type = rd16(p + pos);
  q.qclass = rd16(p + pos + 2);
  q.questionEnd = pos + 4;

  return q.domain.length() > 0;
}

static uint16_t makeBaseResponse(const uint8_t* query,
                                 const DnsQuestion& q,
                                 uint8_t rcode,
                                 uint16_t answerCount) {
  if (q.questionEnd > MAX_DNS_PACKET) return 0;

  memcpy(dnsOut, query, q.questionEnd);

  uint16_t queryFlags = rd16(query + 2);
  uint16_t flags = 0x8000;             // QR = response
  flags |= (queryFlags & 0x0100);       // preserve RD
  flags |= 0x0080;                     // RA = recursion available
  flags |= (rcode & 0x000F);

  wr16(dnsOut + 2, flags);
  wr16(dnsOut + 4, 1);
  wr16(dnsOut + 6, answerCount);
  wr16(dnsOut + 8, 0);
  wr16(dnsOut + 10, 0);

  return q.questionEnd;
}

static void sendDnsRaw(const IPAddress& ip, uint16_t port,
                       const uint8_t* data, uint16_t len) {
  dnsUdp.beginPacket(ip, port);
  dnsUdp.write(data, len);
  dnsUdp.endPacket();
}

static void replyDnsError(const IPAddress& ip, uint16_t port,
                          const uint8_t* query, const DnsQuestion& q,
                          uint8_t rcode) {
  uint16_t len = makeBaseResponse(query, q, rcode, 0);
  if (len) sendDnsRaw(ip, port, dnsOut, len);
}

static void replyDnsNoAnswer(const IPAddress& ip, uint16_t port,
                             const uint8_t* query, const DnsQuestion& q) {
  uint16_t len = makeBaseResponse(query, q, 0, 0);
  if (len) sendDnsRaw(ip, port, dnsOut, len);
}

static void replyDnsA(const IPAddress& ip, uint16_t port,
                      const uint8_t* query, const DnsQuestion& q,
                      const IPAddress& answer) {
  // For AAAA or other non-A types, return NOERROR with no answers. This causes
  // normal dual-stack clients to continue with A while avoiding bogus IPv6.
  if (q.type != 1 && q.type != 255) {
    replyDnsNoAnswer(ip, port, query, q);
    return;
  }

  uint16_t len = makeBaseResponse(query, q, 0, 1);
  if (!len || len + 16 > sizeof(dnsOut)) return;

  // NAME pointer -> original QNAME at byte 12
  dnsOut[len++] = 0xC0;
  dnsOut[len++] = 0x0C;

  // TYPE A, CLASS IN
  dnsOut[len++] = 0x00; dnsOut[len++] = 0x01;
  dnsOut[len++] = 0x00; dnsOut[len++] = 0x01;

  // TTL 60 s
  wr32(dnsOut + len, 60); len += 4;

  // RDLENGTH 4
  dnsOut[len++] = 0x00; dnsOut[len++] = 0x04;

  dnsOut[len++] = answer[0];
  dnsOut[len++] = answer[1];
  dnsOut[len++] = answer[2];
  dnsOut[len++] = answer[3];

  sendDnsRaw(ip, port, dnsOut, len);
}

static int allocPending() {
  for (uint8_t i = 0; i < MAX_PENDING; ++i) {
    if (!pending[i].used) return i;
  }
  return -1;
}

static int findPendingByInternalId(uint16_t id) {
  for (uint8_t i = 0; i < MAX_PENDING; ++i) {
    if (pending[i].used && pending[i].internalId == id) return i;
  }
  return -1;
}

static uint16_t newInternalId() {
  do {
    ++nextInternalId;
    if (nextInternalId == 0) ++nextInternalId;
  } while (findPendingByInternalId(nextInternalId) >= 0);
  return nextInternalId;
}

static IPAddress selectedUpstreamDNS() {
  IPAddress result;

  if (cfg.dnsAuto && WiFi.status() == WL_CONNECTED) {
    result = WiFi.dnsIP(0);
    if (isZeroIP(result)) result = WiFi.dnsIP(1);
  } else if (!cfg.dnsAuto) {
    result = cfg.customDNS;
  }

  // Safe fallback.
  if (isZeroIP(result) || sameIP(result, AP_IP)) {
    result = IPAddress(1, 1, 1, 1);
  }
  return result;
}

static bool isLocalAdminName(const String& d) {
  return d == F("esphole") ||
         d == F("esphole.lan") ||
         d == F("esphole.home") ||
         d == F("setup.esphole");
}

static bool setupCaptiveMode() {
  return cfg.staSSID.length() == 0 || WiFi.status() != WL_CONNECTED;
}

static void forwardDns(const IPAddress& clientIP, uint16_t clientPort,
                       uint8_t* packet, uint16_t len,
                       const DnsQuestion& q) {
  int slot = allocPending();
  if (slot < 0 || !upstreamUdpReady) {
    ++statErrors;
    replyDnsError(clientIP, clientPort, packet, q, 2); // SERVFAIL
    return;
  }

  uint16_t originalId = rd16(packet);
  uint16_t internalId = newInternalId();

  pending[slot].used = true;
  pending[slot].internalId = internalId;
  pending[slot].originalId = originalId;
  pending[slot].clientIP = clientIP;
  pending[slot].clientPort = clientPort;
  pending[slot].createdAt = millis();

  wr16(packet, internalId);

  IPAddress upstream = selectedUpstreamDNS();
  bool ok =
    upstreamUdp.beginPacket(upstream, DNS_PORT) == 1 &&
    upstreamUdp.write(packet, len) == len &&
    upstreamUdp.endPacket() == 1;

  // Restore the local copy's original transaction id.
  wr16(packet, originalId);

  if (!ok) {
    pending[slot].used = false;
    ++statErrors;
    replyDnsError(clientIP, clientPort, packet, q, 2);
    return;
  }

  ++statForwarded;
}

static void processUpstreamReplies() {
  int packetSize = upstreamUdp.parsePacket();
  while (packetSize > 0) {
    uint16_t readLen = uint16_t(min(packetSize, int(MAX_DNS_PACKET)));
    int got = upstreamUdp.read(dnsOut, readLen);

    // Drain any oversized remainder.
    while (upstreamUdp.available()) upstreamUdp.read();

    if (got >= 12) {
      uint16_t internalId = rd16(dnsOut);
      int slot = findPendingByInternalId(internalId);

      if (slot >= 0) {
        activityBeep(false);
        wr16(dnsOut, pending[slot].originalId);
        sendDnsRaw(pending[slot].clientIP,
                   pending[slot].clientPort,
                   dnsOut,
                   uint16_t(got));
        pending[slot].used = false;
        ++statReplies;
      }
    }

    yield();
    packetSize = upstreamUdp.parsePacket();
  }
}

static void expirePending() {
  uint32_t now = millis();
  for (uint8_t i = 0; i < MAX_PENDING; ++i) {
    if (pending[i].used &&
        uint32_t(now - pending[i].createdAt) > PENDING_TIMEOUT_MS) {
      pending[i].used = false;
      ++statErrors;
    }
  }
}

static void processDnsQueries() {
  int packetSize = dnsUdp.parsePacket();

  while (packetSize > 0) {
    IPAddress clientIP = dnsUdp.remoteIP();
    uint16_t clientPort = dnsUdp.remotePort();

    uint16_t readLen = uint16_t(min(packetSize, int(MAX_DNS_PACKET)));
    int got = dnsUdp.read(dnsIn, readLen);
    while (dnsUdp.available()) dnsUdp.read();

    ++statQueries;
    activityBeep(false);

    DnsQuestion q;
    if (got < 12 || !parseDnsQuestion(dnsIn, uint16_t(got), q)) {
      ++statErrors;
      // Cannot safely construct a response without a parsed question.
      yield();
      packetSize = dnsUdp.parsePacket();
      continue;
    }

    if (packetSize > MAX_DNS_PACKET) {
      ++statErrors;
      replyDnsError(clientIP, clientPort, dnsIn, q, 2);
      yield();
      packetSize = dnsUdp.parsePacket();
      continue;
    }

    // First boot or lost upstream: behave like a captive setup portal.
    if (setupCaptiveMode()) {
      replyDnsA(clientIP, clientPort, dnsIn, q, AP_IP);
      yield();
      packetSize = dnsUdp.parsePacket();
      continue;
    }

    // Friendly local admin aliases.
    if (isLocalAdminName(q.domain)) {
      replyDnsA(clientIP, clientPort, dnsIn, q, AP_IP);
      yield();
      packetSize = dnsUdp.parsePacket();
      continue;
    }

    // DNS sinkhole.
    if (isBlockedDomain(q.domain)) {
      ++statBlocked;
      lastBlockedDomain = q.domain;

      if (cfg.nullBlocking) {
        replyDnsA(clientIP, clientPort, dnsIn, q, IPAddress(0, 0, 0, 0));
      } else {
        replyDnsError(clientIP, clientPort, dnsIn, q, 3); // NXDOMAIN
      }

      yield();
      packetSize = dnsUdp.parsePacket();
      continue;
    }

    forwardDns(clientIP, clientPort, dnsIn, uint16_t(got), q);

    yield();
    packetSize = dnsUdp.parsePacket();
  }

  processUpstreamReplies();
  expirePending();
}

// ----------------------------- NAPT -----------------------------------------

static void applyNatSetting() {
#if ESPHOLE_HAS_NAPT
  if (!cfg.natEnabled) {
    if (naptInitialized) {
      ip_napt_enable_no(SOFTAP_IF, 0);
    }
    naptActive = false;
    return;
  }

  if (!naptInitialized) {
    err_t r = ip_napt_init(NAPT_ENTRIES, NAPT_PORTMAP_ENTRIES);
    if (r != ERR_OK) {
      Serial.printf("[NAPT] init failed: %d\n", int(r));
      naptActive = false;
      return;
    }
    naptInitialized = true;
  }

  err_t r = ip_napt_enable_no(SOFTAP_IF, 1);
  naptActive = (r == ERR_OK);
  Serial.printf("[NAPT] %s (result=%d)\n",
                naptActive ? "enabled" : "enable failed",
                int(r));
#else
  naptInitialized = false;
  naptActive = false;
  Serial.println(F("[NAPT] not available in this selected lwIP/core build"));
#endif
}

// ----------------------------- Wi-Fi ----------------------------------------

static void beginStation() {
  if (!cfg.staSSID.length()) return;

  Serial.printf("[STA] connecting to %s\n", cfg.staSSID.c_str());
  WiFi.begin(cfg.staSSID.c_str(), cfg.staPass.c_str());
}

static void setupWiFi() {
  WiFi.persistent(false);
  WiFi.mode(WIFI_AP_STA);
  WiFi.setAutoReconnect(true);
  WiFi.hostname("ESPHole");

  // Tell AP DHCP clients that the ESP itself is their DNS resolver.
  auto& dhcp = WiFi.softAPDhcpServer();
  dhcp.setDns(AP_IP);

  WiFi.softAPConfig(AP_IP, AP_GW, AP_MASK);

  bool apOK;
  if (cfg.apPass.length() >= 8) {
    apOK = WiFi.softAP(cfg.apSSID.c_str(), cfg.apPass.c_str());
  } else {
    apOK = WiFi.softAP(cfg.apSSID.c_str());
  }

  Serial.printf("[AP] %s, IP %s, result=%s\n",
                cfg.apSSID.c_str(),
                WiFi.softAPIP().toString().c_str(),
                apOK ? "OK" : "FAIL");

  beginStation();
  applyNatSetting();
}

static void maintainWiFi() {
  wl_status_t s = WiFi.status();

  if (s != lastWiFiState) {
    lastWiFiState = s;
    if (s == WL_CONNECTED) {
      Serial.printf("[STA] connected, IP=%s DNS=%s\n",
                    WiFi.localIP().toString().c_str(),
                    selectedUpstreamDNS().toString().c_str());
    } else {
      Serial.printf("[STA] status=%d\n", int(s));
    }
  }

  if (cfg.staSSID.length() &&
      s != WL_CONNECTED &&
      uint32_t(millis() - lastWiFiRetry) > 15000UL) {
    lastWiFiRetry = millis();
    WiFi.begin(cfg.staSSID.c_str(), cfg.staPass.c_str());
  }
}

// ----------------------------- Web UI ---------------------------------------

static bool requireAdmin() {
  if (cfg.staSSID.length() == 0) {
    // First boot remains easy to configure from the protected AP.
    return true;
  }

  if (!web.authenticate("admin", cfg.adminPass.c_str())) {
    web.requestAuthentication(BASIC_AUTH, "ESPHole");
    return false;
  }
  return true;
}

static String pageTop(const String& title) {
  String s;
  s.reserve(3300);
  s += F("<!doctype html><html data-theme='dark'><head><meta charset='utf-8'>"
         "<meta name='viewport' content='width=device-width,initial-scale=1'>"
         "<meta name='theme-color' content='#09131c'><title>");
  s += htmlEscape(title);
  s += F("</title><style>"
         ":root{--bg:#09131c;--panel:#101f2a;--panel2:#142733;--text:#e9f4fa;--muted:#91a7b6;--line:#243a48;--accent:#24b8dc;--ok:#54d4ae;--warn:#ffca79;--danger:#ff6b78;--shadow:0 18px 48px rgba(0,0,0,.24)}"
         "*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;min-height:100vh;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:radial-gradient(circle at 80% -10%,rgba(36,184,220,.14),transparent 36%),var(--bg);color:var(--text)}"
         "header{position:sticky;top:0;z-index:4;display:flex;align-items:center;gap:24px;padding:16px max(18px,calc((100vw - 980px)/2));background:rgba(9,19,28,.91);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}"
         ".brand{font-weight:800;letter-spacing:.02em;white-space:nowrap}.brand span{color:var(--accent)}nav{display:flex;gap:6px;overflow:auto}nav a{color:var(--muted);text-decoration:none;padding:8px 11px;border-radius:9px;font-size:13px;white-space:nowrap}nav a:hover{color:var(--text);background:var(--panel2)}"
         "main{max-width:980px;margin:auto;padding:30px 18px 46px}.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:800}.pagehead{display:flex;align-items:end;justify-content:space-between;gap:18px;margin:8px 0 22px}.pagehead h1{font-size:34px;margin:0;line-height:1.05}.pagehead p{margin:7px 0 0;color:var(--muted)}"
         ".grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.card{background:linear-gradient(180deg,var(--panel),rgba(16,31,42,.92));border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:var(--shadow);margin:12px 0;min-width:0}.card.wide{grid-column:1/-1}.stat{margin:0}.stat b{display:block;font-size:25px;margin-top:7px;overflow:hidden;text-overflow:ellipsis}.stat small,.muted{color:var(--muted)}"
         ".pill{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--panel2);border-radius:999px;padding:6px 10px;font-size:11px;font-weight:750}.dot{width:7px;height:7px;border-radius:50%;background:var(--muted)}.dot.ok{background:var(--ok);box-shadow:0 0 12px rgba(84,212,174,.6)}.dot.bad{background:var(--danger)}"
         "h2{font-size:17px;margin:0 0 12px}label{display:block;color:var(--muted);font-size:12px;margin-top:12px}input,textarea,select,button{font:inherit;width:100%;padding:11px 12px;margin:5px 0;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--text);outline:none}input:focus,textarea:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(36,184,220,.1)}textarea{resize:vertical;min-height:280px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px}button{background:var(--accent);border-color:transparent;color:#032630;font-weight:800;cursor:pointer}button:hover{filter:brightness(1.08)}button.ghost{background:var(--panel2);color:var(--text);border-color:var(--line)}button.danger{background:#8e2c37;color:#fff}"
         "table{width:100%;border-collapse:collapse}td{padding:9px 3px;border-bottom:1px solid rgba(36,58,72,.8);vertical-align:top}td:first-child{color:var(--muted);width:42%}tr:last-child td{border-bottom:0}.ok{color:var(--ok)}.bad{color:var(--danger)}code{background:var(--bg);border:1px solid var(--line);padding:2px 6px;border-radius:7px;color:#bfeffc}.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}.check{display:flex;align-items:flex-start;gap:9px;color:var(--text);font-size:13px}.check input{width:auto;margin-top:2px}.notice{border-left:3px solid var(--accent);padding-left:12px;color:var(--muted)}footer{max-width:980px;margin:auto;padding:0 18px 28px;color:var(--muted);font-size:11px}"
         "@media(max-width:760px){header{flex-wrap:wrap;gap:8px;padding:14px 16px}.brand{flex:1}nav{order:3;width:100%}main{padding:24px 14px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.pagehead{align-items:start}.pagehead h1{font-size:29px}.two{grid-template-columns:1fr}}"
         "@media(max-width:430px){.grid{grid-template-columns:1fr}.card{border-radius:15px;padding:15px}}"
         "</style></head><body><header><div class='brand'>ESP<span>Hole</span></div><nav>"
         "<a href='/'>Dashboard</a><a href='/blocklist'>Blocklist</a><a href='/settings'>Settings</a>"
         "</nav></header><main>");
  return s;
}

static String pageBottom() {
  return F("</main><footer>ESPHole &middot; tiny DNS sinkhole + repeater &middot; EasyMode-inspired UI</footer></body></html>");
}

static String readBlocklistForTextarea() {
  if (!fsReady || !LittleFS.exists(BLOCK_FILE)) return "";

  File f = LittleFS.open(BLOCK_FILE, "r");
  if (!f) return "";

  String out;
  size_t size = f.size();
  if (size > 18000) size = 18000;
  out.reserve(size + 16);

  while (f.available() && out.length() < 18000) {
    out += char(f.read());
    yield();
  }
  f.close();
  return out;
}

static void handleRoot() {
  if (!requireAdmin()) return;

  String s = pageTop(F("ESPHole"));
  s += F("<div class='eyebrow'>Network utility</div><div class='pagehead'><div><h1>ESPHole</h1><p>DNS sinkhole, captive setup and tiny Wi-Fi repeater.</p></div><span class='pill'><span class='dot ");
  if (WiFi.status() == WL_CONNECTED) {
    s += F("ok'></span>ONLINE");
  } else {
    s += F("bad'></span>SETUP / OFFLINE");
  }
  s += F("</span></div>");

  s += F("<div class='grid'>");
  s += F("<div class='card stat'><small>DNS queries</small><b>"); s += String(statQueries); s += F("</b></div>");
  s += F("<div class='card stat'><small>Blocked</small><b>"); s += String(statBlocked); s += F("</b></div>");
  s += F("<div class='card stat'><small>Block entries</small><b>"); s += String(blockCount); s += F("</b></div>");
  s += F("<div class='card stat'><small>Free heap</small><b>"); s += humanBytes(ESP.getFreeHeap()); s += F("</b></div>");
  s += F("</div>");

  s += F("<div class='two'><div class='card'><h2>Connection</h2><table>");
  s += F("<tr><td>Upstream</td><td>");
  if (WiFi.status() == WL_CONNECTED) {
    s += F("<span class='ok'>Connected</span><br><span class='muted'>");
    s += htmlEscape(WiFi.SSID()); s += F(" &middot; "); s += WiFi.localIP().toString(); s += F("</span>");
  } else {
    s += F("<span class='bad'>Offline / setup mode</span>");
  }
  s += F("</td></tr><tr><td>DNS upstream</td><td>"); s += selectedUpstreamDNS().toString();
  s += cfg.dnsAuto ? F(" <span class='muted'>(auto)</span>") : F(" <span class='muted'>(manual)</span>");
  s += F("</td></tr><tr><td>AP clients</td><td>"); s += String(WiFi.softAPgetStationNum());
  s += F("</td></tr><tr><td>Repeater NAT</td><td>");
#if ESPHOLE_HAS_NAPT
  s += cfg.natEnabled ? (naptActive ? F("<span class='ok'>Active</span>") : F("<span class='bad'>Requested / inactive</span>")) : F("Disabled");
#else
  s += F("<span class='bad'>Unavailable in lwIP build</span>");
#endif
  s += F("</td></tr></table></div>");

  s += F("<div class='card'><h2>Protection</h2><table><tr><td>DNS blocking</td><td>"); s += boolWord(cfg.blockingEnabled);
  s += F("</td></tr><tr><td>Last blocked</td><td>"); s += htmlEscape(lastBlockedDomain.length() ? lastBlockedDomain : String(F("None yet")));
  s += F("</td></tr><tr><td>Forwarded</td><td>"); s += String(statForwarded);
  s += F("</td></tr><tr><td>Errors / timeouts</td><td>"); s += String(statErrors);
  s += F("</td></tr><tr><td>Activity sound</td><td>"); s += cfg.activityBuzzerEnabled ? F("D5 / ON") : F("OFF");
  s += F("</td></tr></table><form method='post' action='/toggle'><button class='ghost'>");
  s += cfg.blockingEnabled ? F("Pause DNS blocking") : F("Enable DNS blocking");
  s += F("</button></form></div></div>");

  if (cfg.staSSID.length() == 0) {
    s += F("<div class='card'><div class='eyebrow'>First run</div><h2>Connect ESPHole upstream</h2>"
           "<p class='notice'>Your ESPHole access point stays available while the station interface connects to your internet Wi-Fi.</p>"
           "<form method='post' action='/quicksetup'><label>Upstream Wi-Fi SSID</label><input name='ssid' maxlength='32' required>"
           "<label>Wi-Fi password</label><input type='password' name='pass' maxlength='64'><button>Save &amp; reboot</button></form></div>");
  }

  s += F("<div class='card'><h2>Client access</h2><p>Join <code>"); s += htmlEscape(cfg.apSSID);
  s += F("</code>. DHCP advertises <code>192.168.4.1</code> as DNS. Open <code>http://192.168.4.1/</code> or <code>esphole.lan</code> for administration.</p>"
         "<p class='muted'>The D5 activity sound represents traffic ESPHole can directly observe (DNS and its own web service). Raw NAPT packets are intentionally not sniffed because that would make the repeater less stable.</p></div>");

  s += pageBottom();
  web.send(200, "text/html", s);
}

static void handleQuickSetup() {
  activityBeep(true);
  cfg.staSSID = stripCRLF(web.arg("ssid"));
  cfg.staPass = stripCRLF(web.arg("pass"));
  saveConfig();

  web.send(200, "text/html",
           pageTop(F("Saved")) +
           F("<div class='card'><h2>Saved</h2><p>ESPHole is rebooting.</p></div>") +
           pageBottom());
  delay(350);
  ESP.restart();
}

static void handleBlocklist() {
  if (!requireAdmin()) return;

  String list = readBlocklistForTextarea();

  String s = pageTop(F("ESPHole Blocklist"));
  s += F("<h1>Blocklist</h1><div class='card'>"
         "<p>One domain per line. Blocking <code>example.com</code> also blocks its subdomains. "
         "Hosts-file lines such as <code>0.0.0.0 example.com</code> are accepted.</p>"
         "<p>RAM capacity: ");
  s += String(MAX_BLOCK_HASHES);
  s += F(" unique domain hashes. Loaded now: ");
  s += String(blockCount);
  s += F(".</p><form method='post' action='/saveblocklist'>"
         "<textarea name='list' rows='22' spellcheck='false'>");
  s += htmlEscape(list);
  s += F("</textarea><button>Save blocklist</button></form></div>");
  s += pageBottom();

  web.send(200, "text/html", s);
}

static void handleSaveBlocklist() {
  if (!requireAdmin()) return;
  activityBeep(true);

  uint16_t accepted = 0;
  bool ok = saveBlocklistText(web.arg("list"), accepted);

  String s = pageTop(F("Blocklist saved"));
  s += F("<div class='card'><h2>");
  s += ok ? F("Saved") : F("Save failed");
  s += F("</h2><p>Loaded unique entries: ");
  s += String(accepted);
  s += F("</p><a href='/blocklist'>Back to blocklist</a></div>");
  s += pageBottom();
  web.send(ok ? 200 : 500, "text/html", s);
}

static void handleSettings() {
  if (!requireAdmin()) return;

  String s = pageTop(F("ESPHole Settings"));
  s += F("<h1>Settings</h1><div class='card'><form method='post' action='/savesettings'>");

  s += F("<label>Upstream Wi-Fi SSID</label><input name='ssid' maxlength='32' value='");
  s += htmlEscape(cfg.staSSID);
  s += F("'>");

  s += F("<label>Upstream Wi-Fi password</label>"
         "<input type='password' name='stapass' maxlength='64' placeholder='Leave unchanged if blank'>");

  s += F("<hr><label>ESPHole AP name</label><input name='apssid' maxlength='31' value='");
  s += htmlEscape(cfg.apSSID);
  s += F("'>");

  s += F("<label>ESPHole AP password (8+ chars)</label>"
         "<input type='password' name='appass' maxlength='63' placeholder='Leave unchanged if blank'>");

  s += F("<hr><label>Admin password (user is admin)</label>"
         "<input type='password' name='adminpass' maxlength='63' placeholder='Leave unchanged if blank'>");

  s += F("<hr><label>Upstream DNS</label><select name='dnsmode'>"
         "<option value='auto'");
  if (cfg.dnsAuto) s += F(" selected");
  s += F(">Automatic from upstream router</option><option value='manual'");
  if (!cfg.dnsAuto) s += F(" selected");
  s += F(">Manual IPv4 DNS</option></select>");

  s += F("<input name='dnsip' value='");
  s += cfg.customDNS.toString();
  s += F("' placeholder='1.1.1.1'>");

  s += F("<hr><label class='check'><input type='checkbox' name='blocking' value='1'");
  if (cfg.blockingEnabled) s += F(" checked");
  s += F("><span>Enable DNS blocking</span></label>");

  s += F("<label class='check'><input type='checkbox' name='nat' value='1'");
  if (cfg.natEnabled) s += F(" checked");
  s += F("><span>Enable Wi-Fi repeater/NAPT</span></label>");

  s += F("<label class='check'><input type='checkbox' name='nullblock' value='1'");
  if (cfg.nullBlocking) s += F(" checked");
  s += F("><span>Return 0.0.0.0 instead of NXDOMAIN for blocked A queries</span></label>");

  s += F("<hr><div class='eyebrow'>Activity sound</div><label class='check'><input type='checkbox' name='activitybuzzer' value='1'");
  if (cfg.activityBuzzerEnabled) s += F(" checked");
  s += F("><span>Beep on ESPHole-observed network activity using D5 / GPIO14</span></label>");
  s += F("<div class='two'><div><label>Buzzer frequency (Hz)</label><input type='number' name='buzzfreq' min='200' max='12000' value='");
  s += String(cfg.activityBuzzerFreq);
  s += F("'></div><div><label>Pulse length (ms)</label><input type='number' name='buzzpulse' min='1' max='100' value='");
  s += String(cfg.activityBuzzerPulseMs);
  s += F("'></div></div><label>Minimum gap between beeps (ms)</label><input type='number' name='buzzgap' min='15' max='1000' value='");
  s += String(cfg.activityBuzzerMinGapMs);
  s += F("'><p class='muted'>Default 2600 Hz / 7 ms / 45 ms keeps it LAN-LED-like instead of continuously chirping.</p>");

  s += F("<button>Save and reboot</button></form></div>");

  s += F("<div class='card'><form method='post' action='/reboot'><button>Reboot ESPHole</button></form>"
         "<form method='post' action='/factory' onsubmit=\"return confirm('Erase ESPHole settings and blocklist?')\">"
         "<button class='danger'>Factory reset</button></form></div>");

  s += pageBottom();
  web.send(200, "text/html", s);
}

static void handleSaveSettings() {
  if (!requireAdmin()) return;
  activityBeep(true);

  cfg.staSSID = stripCRLF(web.arg("ssid"));

  String staPass = web.arg("stapass");
  if (staPass.length()) cfg.staPass = stripCRLF(staPass);

  String apSSID = stripCRLF(web.arg("apssid"));
  if (apSSID.length() >= 1 && apSSID.length() <= 31) cfg.apSSID = apSSID;

  String apPass = stripCRLF(web.arg("appass"));
  if (apPass.length() >= 8) cfg.apPass = apPass;

  String adminPass = stripCRLF(web.arg("adminpass"));
  if (adminPass.length() >= 4) cfg.adminPass = adminPass;

  cfg.dnsAuto = (web.arg("dnsmode") != F("manual"));
  IPAddress parsed;
  if (parsed.fromString(web.arg("dnsip"))) cfg.customDNS = parsed;

  cfg.blockingEnabled = web.hasArg("blocking");
  cfg.natEnabled = web.hasArg("nat");
  cfg.nullBlocking = web.hasArg("nullblock");

  cfg.activityBuzzerEnabled = web.hasArg("activitybuzzer");
  cfg.activityBuzzerFreq = clampU16Arg(web.arg("buzzfreq"), cfg.activityBuzzerFreq, 200, 12000);
  cfg.activityBuzzerPulseMs = clampU16Arg(web.arg("buzzpulse"), cfg.activityBuzzerPulseMs, 1, 100);
  cfg.activityBuzzerMinGapMs = clampU16Arg(web.arg("buzzgap"), cfg.activityBuzzerMinGapMs, 15, 1000);

  bool ok = saveConfig();

  web.send(ok ? 200 : 500, "text/html",
           pageTop(F("Settings saved")) +
           String(F("<div class='card'><h2>")) +
           (ok ? F("Saved") : F("Save failed")) +
           F("</h2><p>ESPHole is rebooting to apply network settings.</p></div>") +
           pageBottom());

  delay(350);
  ESP.restart();
}

static void handleToggle() {
  if (!requireAdmin()) return;
  activityBeep(true);
  cfg.blockingEnabled = !cfg.blockingEnabled;
  saveConfig();

  web.sendHeader("Location", "/", true);
  web.send(303, "text/plain", "");
}

static void handleApiStatus() {
  if (!requireAdmin()) return;

  String s;
  s.reserve(700);
  s += F("{\"version\":\""); s += ESPHOLE_VERSION;
  s += F("\",\"blocking\":"); s += cfg.blockingEnabled ? F("true") : F("false");
  s += F(",\"block_count\":"); s += String(blockCount);
  s += F(",\"queries\":"); s += String(statQueries);
  s += F(",\"blocked\":"); s += String(statBlocked);
  s += F(",\"forwarded\":"); s += String(statForwarded);
  s += F(",\"errors\":"); s += String(statErrors);
  s += F(",\"wifi_connected\":"); s += WiFi.status() == WL_CONNECTED ? F("true") : F("false");
  s += F(",\"sta_ip\":\""); s += WiFi.localIP().toString();
  s += F("\",\"ap_ip\":\""); s += WiFi.softAPIP().toString();
  s += F("\",\"upstream_dns\":\""); s += selectedUpstreamDNS().toString();
  s += F("\",\"ap_clients\":"); s += String(WiFi.softAPgetStationNum());
  s += F(",\"heap\":"); s += String(ESP.getFreeHeap());
  s += F(",\"napt\":"); s += naptActive ? F("true") : F("false");
  s += F(",\"activity_buzzer\":"); s += cfg.activityBuzzerEnabled ? F("true") : F("false");
  s += F(",\"activity_beeps\":"); s += String(statActivityBeeps);
  s += F(",\"last_blocked\":\""); s += jsonEscape(lastBlockedDomain);
  s += F("\"}");

  web.send(200, "application/json", s);
}

static void handleReboot() {
  if (!requireAdmin()) return;
  web.send(200, "text/html",
           pageTop(F("Reboot")) +
           F("<div class='card'><h2>Rebooting ESPHole</h2></div>") +
           pageBottom());
  delay(350);
  ESP.restart();
}

static void handleFactoryReset() {
  if (!requireAdmin()) return;

  if (fsReady) {
    LittleFS.remove(CONFIG_FILE);
    LittleFS.remove(BLOCK_FILE);
  }

  web.send(200, "text/html",
           pageTop(F("Factory reset")) +
           F("<div class='card'><h2>Factory reset complete</h2><p>Rebooting.</p></div>") +
           pageBottom());
  delay(350);
  ESP.restart();
}

static void captiveRedirect() {
  web.sendHeader("Location", String(F("http://")) + AP_IP.toString() + F("/"), true);
  web.send(302, "text/plain", "");
}

static void setupWeb() {
  web.on("/", HTTP_GET, handleRoot);

  web.on("/quicksetup", HTTP_POST, handleQuickSetup);

  web.on("/blocklist", HTTP_GET, handleBlocklist);
  web.on("/saveblocklist", HTTP_POST, handleSaveBlocklist);

  web.on("/settings", HTTP_GET, handleSettings);
  web.on("/savesettings", HTTP_POST, handleSaveSettings);

  web.on("/toggle", HTTP_POST, handleToggle);
  web.on("/api/status", HTTP_GET, handleApiStatus);

  web.on("/reboot", HTTP_POST, handleReboot);
  web.on("/factory", HTTP_POST, handleFactoryReset);

  // Common captive-portal probe paths.
  web.on("/generate_204", HTTP_ANY, []() {
    if (setupCaptiveMode()) captiveRedirect();
    else web.send(204, "text/plain", "");
  });
  web.on("/gen_204", HTTP_ANY, []() {
    if (setupCaptiveMode()) captiveRedirect();
    else web.send(204, "text/plain", "");
  });
  web.on("/hotspot-detect.html", HTTP_ANY, []() {
    if (setupCaptiveMode()) captiveRedirect();
    else web.send(200, "text/html", "<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>");
  });
  web.on("/connecttest.txt", HTTP_ANY, []() {
    if (setupCaptiveMode()) captiveRedirect();
    else web.send(200, "text/plain", "Microsoft Connect Test");
  });
  web.on("/ncsi.txt", HTTP_ANY, []() {
    if (setupCaptiveMode()) captiveRedirect();
    else web.send(200, "text/plain", "Microsoft NCSI");
  });

  web.onNotFound([]() {
    if (setupCaptiveMode()) {
      captiveRedirect();
      return;
    }
    web.send(404, "text/plain", "ESPHole: not found");
  });

  web.begin();
  Serial.println(F("[WEB] http://192.168.4.1/"));
}

// ----------------------------- Startup --------------------------------------

static void setupDns() {
  dnsReady = dnsUdp.begin(DNS_PORT);
  upstreamUdpReady = upstreamUdp.begin(UPSTREAM_LOCAL_PORT);

  Serial.printf("[DNS] listener=%s upstream_socket=%s\n",
                dnsReady ? "OK" : "FAIL",
                upstreamUdpReady ? "OK" : "FAIL");
}

void setup() {
  Serial.begin(115200);
  delay(50);
  Serial.println();
  Serial.println(F("===================================="));
  Serial.printf(" ESPHole %s\n", ESPHOLE_VERSION);
  Serial.println(F(" ESP8266 DNS sinkhole + Wi-Fi NAPT"));
  Serial.println(F("===================================="));

  pinMode(ACTIVITY_BUZZER_PIN, OUTPUT);
  digitalWrite(ACTIVITY_BUZZER_PIN, LOW);

  for (uint8_t i = 0; i < MAX_PENDING; ++i) pending[i].used = false;

  fsReady = LittleFS.begin();
  Serial.printf("[FS] LittleFS=%s\n", fsReady ? "OK" : "FAIL");

  loadConfig();

  if (fsReady) {
    ensureDefaultBlocklist();
    loadBlocklist();
  }

  Serial.printf("[BLOCK] loaded=%u / %u\n", blockCount, MAX_BLOCK_HASHES);

  setupWiFi();
  setupDns();
  setupWeb();

  Serial.printf("[AP] password: %s\n", cfg.apPass.c_str());
  Serial.println(F("[ADMIN] user: admin"));
  Serial.printf("[ADMIN] password: %s\n", cfg.adminPass.c_str());

#if ESPHOLE_HAS_NAPT
  Serial.println(F("[BUILD] NAPT support detected"));
#else
  Serial.println(F("[BUILD] NAPT support NOT detected; DNS sinkhole still works"));
#endif
}

void loop() {
  maintainWiFi();

  if (dnsReady) processDnsQueries();

  web.handleClient();

  yield();
}