"""Literal C++ fixture payloads for the poll-response fail-closed host lab.

Keep embedded C++ scenarios separate from the Python runner. These payloads are
byte-pinned by poll_response_failclosed_lab_structure_guard.py so a cleanup does
not silently alter the tested source or scenario behavior.
"""

STUBS = r"""
#include <cctype>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  String(const std::string &v):std::string(v){}
  String(int v):std::string(std::to_string(v)){}
  size_t length() const { return size(); }
  int indexOf(const char *v) const {
    const auto p=find(v); return p==npos?-1:(int)p;
  }
  bool equalsIgnoreCase(const String &v) const {
    if(size()!=v.size()) return false;
    for(size_t i=0;i<size();++i)
      if(std::tolower((unsigned char)(*this)[i])!=std::tolower((unsigned char)v[i])) return false;
    return true;
  }
};
struct Config {
#ifdef TARGET_ESP32
  String key="test-key", id="vendo-01";
#else
  char key[32]="test-key", id[32]="vendo-01";
#endif
} cfg;
String lastSentNonce="nonce-123";
String activeTarget="old-target";
bool insertMode=true, fsReady=true, journalRecoveryRequired=false;
// This parser/disposition lab starts with no pending ISR edge. The dedicated
// poll-loop lab injects asynchronous edges through the extracted ISR path.
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
bool outputPolarityKnown=true;
bool pendingReady=false, pollIntakeSuspended=true;
bool pinConfigSafe=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true;
bool runRelayActiveHigh=true, runLedActiveHigh=true;
int runRelayPin=26, runLedPin=2;
bool relayOn=false, ledOn=false;
String responseSignature="valid-signature", responseTarget="target-01";
bool responseInsert=true;
int applyRemoteConfigCalls=0;
int remoteRevision=7;
uint16_t runDebounceMs=70;
bool runCoinActiveLow=true;
String jsonString(const String &, const char *key) {
  if(std::string(key)=="response_sig") return responseSignature;
  if(std::string(key)=="target_nonce") return responseTarget;
  return String("");
}
bool jsonTrue(const String &, const char *key) {
  return std::string(key)=="insert" && responseInsert;
}
int jsonInt(const String &, const char *, int fallback) { return fallback==0?123:fallback; }
String hexDigest(const String &) { return String("valid-signature"); }
void applyRemoteConfig(const String &) {
  ++applyRemoteConfigCalls;
  remoteRevision=99;
  runRelayPin=12;
  runCoinActiveLow=false;
  runRelayActiveHigh=false;
  runDebounceMs=1;
}
void writeLogical(int pin, bool on, bool) {
  if(pin==runRelayPin) relayOn=on;
  if(pin==runLedPin) ledOn=on;
}
"""

MAIN = r"""
int main(){
  // Root-only ok parsing: nested objects, arrays and quoted text are not authority.
  if(!pollJsonTopLevelTrue(String("{\"ok\":true}"),"ok")) return 31;
  if(pollJsonTopLevelTrue(String("{\"ok\":false,\"controller\":{\"ok\":true}}"),"ok")) return 32;
  if(pollJsonTopLevelTrue(String("{\"controller\":{\"ok\":true},\"ok\":false}"),"ok")) return 33;
  if(!pollJsonTopLevelTrue(String("{\"controller\":{\"ok\":false},\"ok\":true}"),"ok")) return 34;
  if(pollJsonTopLevelTrue(String("{\"ok\":true,\"ok\":true}"),"ok")) return 35;
  if(pollJsonTopLevelTrue(String("{\"controller\":[{\"ok\":true}]}"),"ok")) return 36;
  if(pollJsonTopLevelTrue(String("{\"message\":\"\\\"ok\\\":true\",\"ok\":false}"),"ok")) return 37;
  if(pollJsonTopLevelTrue(String("{\"ok\":true,}"),"ok")) return 38;
  if(pollJsonTopLevelTrue(String("{\"ok\":true}trailing"),"ok")) return 39;
  // Coin POST acknowledgement must use the same unique root-level status rule.
  if(pollJsonTopLevelTrue(String("{\"ok\":false,\"detail\":{\"ok\":true}}"),"ok")) return 46;
  if(pollJsonTopLevelTrue(String("{\"ok\":false,\"detail\":[{\"ok\":true}]}"),"ok")) return 47;
  if(pollJsonTopLevelTrue(String("{\"ok\":true,\"ok\":false}"),"ok")) return 48;
  if(!pollJsonTopLevelTrue(String("{\"ok\":true,\"receipt\":{\"ok\":false}}"),"ok")) return 49;
  // No approved event-bound receipt contract exists. All raw HTTP dispositions deny.
  if(coinPostDispositionVerified(String("{\"ok\":true}"),String("nonce-123"),String("target-01"),3)) return 50;
  if(coinPostDispositionVerified(String("{\"ok\":false,\"error\":\"coin window expired\"}"),String("nonce-123"),String("target-01"),3)) return 51;
  if(coinPostDispositionVerified(String("{\"ok\":false,\"receipt\":{\"ok\":true}}"),String("nonce-123"),String("target-01"),3)) return 52;
  if(coinPostDispositionVerified(String(""),String("nonce-123"),String("target-01"),3)) return 53;
  if(!pollJsonTopLevelTrue(String(" { \"ok\" : true, \"controller\":{\"ok\":false} } "),"ok")) return 40;
  if(pollJsonTopLevelTrue(String("{\"o\\u006b\":true}"),"ok")) return 41;
  if(pollJsonTopLevelTrue(String("{\"controller\":bad,\"ok\":true}"),"ok")) return 42;
  if(pollJsonTopLevelTrue(String("{\"controller\":{\"x\":1],\"ok\":true}"),"ok")) return 43;
  // Empty / timed-out poll after a previously positive poll must stay OFF.
  insertMode=true; responseTarget="old-target"; responseSignature="";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("")) || !pollIntakeSuspended || insertMode || !activeTarget.empty() || relayOn) return 11;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn || applyRemoteConfigCalls!=0) return 12;

  // Explicit controller denial also clears stale permission.
  insertMode=true; activeTarget="old-target"; responseSignature="valid-signature";
  responseInsert=false; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":false}")) || insertMode || !activeTarget.empty() || relayOn) return 13;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 14;

  // A positive-looking reply with a bad signature cannot restore intake.
  insertMode=true; activeTarget="old-target"; responseSignature="bad-signature";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 15;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 16;

  // A positive-looking reply without a required signature must stay OFF.
  insertMode=true; activeTarget="old-target"; responseSignature="";
  responseInsert=true; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 22;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 23;

  // Keyless setup/bootstrap is not coin authority, even when a response_sig-shaped
  // value is present but cannot be verified without a provisioned key.
#ifdef TARGET_ESP32
  cfg.key="";
#else
  cfg.key[0]='\0';
#endif
  insertMode=true; activeTarget="old-target"; responseSignature="valid-signature";
  responseTarget="target-keyless"; responseInsert=true;
  pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 29;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 30;
#ifdef TARGET_ESP32
  cfg.key="test-key";
#else
  std::strcpy(cfg.key,"test-key");
#endif

  // MASTER §6.3: the current response_sig construction is only a derived candidate.
  // Until CORE publishes the canonical producer and QA approves exact vectors,
  // even a provisioned-key positive-looking response must remain denied.
  insertMode=false; activeTarget=""; responseSignature="valid-signature";
  responseTarget="target-unapproved"; responseInsert=true;
  pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  if(acceptPollResponse(String(R"({"ok":true})")) || insertMode ||
     !activeTarget.empty() || relayOn) return 54;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 55;

  // A positive-looking candidate response remains denied until the canonical
  // producer/consumer contract and independent golden vectors are approved.
  insertMode=false; activeTarget=""; responseSignature="valid-signature";
  responseTarget="target-02"; responseInsert=true;
  pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  if(acceptPollResponse(String(R"({"ok":true})")) || insertMode || !activeTarget.empty()) return 17;
  if(relayOn) return 18;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn || applyRemoteConfigCalls!=0 || remoteRevision!=7 ||
     runRelayPin!=26 || !runCoinActiveLow || !runRelayActiveHigh || runDebounceMs!=70) return 19;

  // A candidate admission signature must not authorize configuration fields either.
  responseInsert=true; responseSignature="valid-signature"; responseTarget="target-02b";
  insertMode=false; activeTarget=""; pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  const String configInjection("{\"ok\":true,\"insert\":true,\"target_nonce\":\"target-02b\",\"expires\":123,\"response_sig\":\"valid-signature\",\"config_revision\":99,\"enabled\":1,\"coin_enabled\":1,\"relay_enabled\":1,\"led_enabled\":1,\"coin_pin\":4,\"relay_pin\":12,\"led_pin\":2,\"coin_active_low\":0,\"relay_active_high\":0,\"led_active_high\":1,\"coin_debounce_ms\":1,\"pulse_group_ms\":10,\"max_wifi_retries\":60}");
  if(acceptPollResponse(configInjection) || insertMode || !activeTarget.empty()) return 44;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn || applyRemoteConfigCalls!=0 || remoteRevision!=7 ||
     runRelayPin!=26 || !runCoinActiveLow || !runRelayActiveHigh || runDebounceMs!=70) return 45;

  // A candidate negative response is denied and clears stale target state.
  responseInsert=false; responseSignature="valid-signature"; responseTarget="target-03";
  insertMode=true; activeTarget="stale-target"; pollIntakeSuspended=true; relayOn=true; applyOutputs();
  if(acceptPollResponse(String(R"({"ok":true})")) || insertMode || !activeTarget.empty()) return 20;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 21;

  // A positive insert response without a target nonce must be rejected.
  insertMode=true; activeTarget="old-target"; responseTarget="";
  responseSignature="valid-signature"; responseInsert=true;
  pollIntakeSuspended=true; relayOn=true; ledOn=true; applyOutputs();
  if(acceptPollResponse(String("{\"ok\":true}")) || insertMode || !activeTarget.empty() || relayOn) return 24;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 25;

  // Defense in depth: a stale positive flag without a target cannot energize output.
  insertMode=true; activeTarget=""; pollIntakeSuspended=false;
  relayOn=true; ledOn=true; applyOutputs();
  if(relayOn || ledOn) return 26;

  // A nested ok:true cannot override an explicit top-level denial.
  insertMode=true; activeTarget="old-target"; responseSignature="valid-signature";
  responseTarget="target-04"; responseInsert=true; pollIntakeSuspended=true; relayOn=true;
  applyOutputs();
  if(acceptPollResponse(String("{\"ok\":false,\"controller\":{\"ok\":true}}")) ||
     insertMode || !activeTarget.empty() || relayOn) return 27;
  pollIntakeSuspended=false; applyOutputs();
  if(relayOn || ledOn) return 28;

  std::cout << "poll-response fail-closed cases: 11/11 PASS; strict root JSON cases: 13/13 PASS; coin POST ACK root status: 4/4 PASS; coin disposition default-deny: 4/4 PASS\n";
  return 0;
}
"""

WINDOW_STUBS = r"""
#include <cstdint>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  size_t length() const { return size(); }
};
bool fsReady=true, journalRecoveryRequired=false, pendingReady=false;
// This window-only fixture does not deliver ISR edges; the dedicated poll-loop
// lab owns edge injection. Keep applyOutputs()'s sequence guard idle here.
volatile uint32_t coinEdgeSequence=0;
uint32_t lastHandledCoinEdgeSequence=0;
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
bool outputPolarityKnown=true;
bool pollIntakeSuspended=false, pollDrainAbortedOnActiveLine=false, pinConfigSafe=true;
bool controllerEnabled=true, coinEnabled=true, relayEnabled=true, ledEnabled=true;
bool insertMode=true, runRelayActiveHigh=true, runLedActiveHigh=true, runCoinActiveLow=true;
int pendingPulses=0, runCoinPin=4, runRelayPin=26, runLedPin=2;
uint16_t runDebounceMs=40;
String activeTarget="target-01";
bool relayOn=false, ledOn=false, relayOffObservedWhileSuspended=false;
uint32_t fakeNow=0;
int pulseStart=-1, pulseEnd=-1;
int digitalRead(int) {
    const bool active=pulseStart>=0 && fakeNow>=(uint32_t)pulseStart && fakeNow<(uint32_t)pulseEnd;
    if(runCoinActiveLow) return active?0:1;
    return active?1:0;
}
uint32_t millis(){ return fakeNow; }
void delay(int ms){ fakeNow+=(uint32_t)ms; }
void writeLogical(int pin,bool on,bool) {
    if(pin==runRelayPin){
        relayOn=on;
        if(!on && pollIntakeSuspended) relayOffObservedWhileSuspended=true;
    }
    if(pin==runLedPin) ledOn=on;
}
"""

WINDOW_MAIN = r"""
void resetState(){
    fsReady=true; journalRecoveryRequired=false; pendingReady=false; pendingPulses=0;
    coinEdgeSequence=0; lastHandledCoinEdgeSequence=0;
    pollIntakeSuspended=false; pollDrainAbortedOnActiveLine=false; pinConfigSafe=true; controllerEnabled=true; coinEnabled=true;
    relayEnabled=true; ledEnabled=true; insertMode=true; runRelayActiveHigh=true;
    runLedActiveHigh=true; runCoinActiveLow=true; runCoinPin=4; runRelayPin=26; runLedPin=2;
    runDebounceMs=40; activeTarget="target-01"; relayOn=false; ledOn=false;
    relayOffObservedWhileSuspended=false; fakeNow=0; pulseStart=-1; pulseEnd=-1;
    applyOutputs();
}
int main(){
    if(boundedCoinDebounceMs(-100)!=20 || boundedCoinDebounceMs(0)!=20 ||
       boundedCoinDebounceMs(1)!=20 || boundedCoinDebounceMs(19)!=20 ||
       boundedCoinDebounceMs(20)!=20 || boundedCoinDebounceMs(40)!=40 ||
       boundedCoinDebounceMs(2000)!=2000 || boundedCoinDebounceMs(2001)!=2000){
        std::cerr<<"DEBOUNCE_FLOOR_FAIL\n"; return 1;
    }
    resetState(); pulseStart=0; pulseEnd=80;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn || relayOffObservedWhileSuspended) return 11;
    resetState(); pendingPulses=1;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn) return 12;
    resetState(); pendingReady=true; applyOutputs();
    if(beginPollWindow() || pollIntakeSuspended || relayOn) return 13;
    resetState(); journalRecoveryRequired=true; applyOutputs();
    if(beginPollWindow() || pollIntakeSuspended || relayOn) return 14;
    resetState(); fsReady=false; applyOutputs();
    if(beginPollWindow() || pollIntakeSuspended || relayOn) return 15;
    resetState(); runDebounceMs=boundedCoinDebounceMs(1); pulseStart=19; pulseEnd=49;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=19) return 16;
    resetState(); runDebounceMs=boundedCoinDebounceMs(1);
    if(!beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=250) return 17;
    resetState(); runCoinActiveLow=false; runDebounceMs=boundedCoinDebounceMs(1);
    pulseStart=19; pulseEnd=49;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=19) return 18;

    // A pulse can still be propagating from the acceptor output stage after
    // relay de-energization. The 100 ms contract maximum plus 20 ms margin
    // must be observed before the blocking poll may start.
    resetState(); runDebounceMs=boundedCoinDebounceMs(1); pulseStart=80; pulseEnd=180;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=80 || coinLineIdle()) return 22;
    resetState(); runDebounceMs=40; pulseStart=80; pulseEnd=180;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=80 || coinLineIdle()) return 23;
    // A second pulse 200 ms after inhibit is still inside the 250 ms
    // inter-coin quiet boundary and must cancel the blocking poll.
    resetState(); runDebounceMs=40; pulseStart=200; pulseEnd=280;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=200 || coinLineIdle()) return 24;

    // A pulse beginning exactly at the 250 ms quiet boundary must cancel the poll.
    resetState(); runDebounceMs=40; pulseStart=250; pulseEnd=330;
    if(beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=250 || coinLineIdle()) return 25;

    // Model the complete synchronous HTTP timeout after the real loop has
    // entered its poll window. A pulse can appear on the input while the
    // CPU is blocked, but the acceptor output must remain inhibited until
    // the response is checked and the loop releases pollIntakeSuspended.
    resetState();
    if(!beginPollWindow() || !pollIntakeSuspended || relayOn || ledOn) return 19;
    const uint32_t pollStartedAt=fakeNow;
    if(pollStartedAt!=250) return 26;
    pulseStart=300; pulseEnd=380;
    if(pulseStart<(int)pollStartedAt) return 24;
    fakeNow=pollStartedAt+70; // pulse is active after the 250 ms quiet window
    if(coinLineIdle() || relayOn || ledOn || !pollIntakeSuspended) return 20;
    fakeNow=pollStartedAt+3500; // complete synchronous HTTP timeout has elapsed
    if(fakeNow-pollStartedAt!=3500) return 27;
    if(!coinLineIdle() || relayOn || ledOn || !pollIntakeSuspended ||
       !relayOffObservedWhileSuspended) return 21;

    std::cout<<"DEBOUNCE_FLOOR_PASS 8/8; POLL_WINDOW_GUARD_PASS 13/13; BLOCKING_POLL_RELAY_INHIBIT_PASS 1/1\n";
    std::cout<<"PHYSICAL_COIN_ACCEPTOR_VERIFIED=0\n";
    return 0;
}
"""

__all__ = ["STUBS", "MAIN", "WINDOW_STUBS", "WINDOW_MAIN"]
