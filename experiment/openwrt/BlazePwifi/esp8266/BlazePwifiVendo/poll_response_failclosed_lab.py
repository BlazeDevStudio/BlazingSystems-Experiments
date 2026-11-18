#!/usr/bin/env python3
"""Source-exact host lab for fail-closed ESP poll-response handling.

Compiles the production poll-status parser, acceptPollResponse(), and applyOutputs() functions from both board sketches. This is simulated control-flow evidence only.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}

def extract(source, name):
    match = re.search(r"\b(?:void|bool|uint16_t)\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{", source)
    assert match, f"missing production function: {name}"
    depth = 0
    for pos in range(match.end() - 1, len(source)):
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start():pos + 1]
    raise AssertionError(f"unbalanced production function: {name}")

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

failed=[]
for board,path in BOARDS.items():
    source=path.read_text(encoding="utf-8")
    loop=extract(source,"loop")
    pre_poll_guard=loop.index("if(pollEdgeAfterDrain!=pollEdgeStart)")
    pre_poll_latch=loop.index("latchPollPulseFault(pollEdgeAfterDrain-pollEdgeStart)",pre_poll_guard)
    pre_poll_release=loop.index("pollIntakeSuspended=false",pre_poll_latch)
    poll_call=loop.index('String r=post("poll")')
    accept=loop.index("acceptPollResponse(r)",poll_call)
    post_release=loop.index("pollIntakeSuspended=false",accept)
    outputs=loop.index("applyOutputs();",post_release)
    last_poll=loop.index("lastPoll=millis()",outputs)
    assert pre_poll_guard < pre_poll_latch < pre_poll_release < poll_call < accept < post_release < outputs < last_poll, board+": poll release ordering changed"
    parser="\n".join(extract(source,name) for name in ("pollJsonSpace","pollJsonHex","pollJsonSkipString","pollJsonSkipComposite","pollJsonSkipPrimitive","pollJsonSkipValue","pollJsonTopLevelTrue","coinPostDispositionVerified"))
    code=("#define TARGET_ESP32\n" if board=="ESP32" else "")+STUBS+parser+extract(source,"acceptPollResponse")+extract(source,"applyOutputs")+MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-response-") as folder:
        cpp=Path(folder)/"test.cpp"; binary=Path(folder)/"test"
        cpp.write_text(code,encoding="utf-8")
        built=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-Wno-unused-parameter",str(cpp),"-o",str(binary)],capture_output=True,text=True,timeout=30)
        if built.returncode:
            print(board,"COMPILE FAIL",built.stderr[-2000:]); failed.append(board); continue
        ran=subprocess.run([str(binary)],capture_output=True,text=True,timeout=10)
        print(board,"PASS" if ran.returncode==0 else "FAIL",ran.stdout.strip(),ran.stderr.strip())
        if ran.returncode: failed.append(board)
        coin_post = loop.find('String r=post("coin"')
        if coin_post < 0:
            print(board, "COIN_POST_ACK_GUARD RED: missing production coin POST")
            failed.append(board)
        else:
            coin_branch = loop[coin_post:]
            auth_guard = coin_branch.find("if(!coinPostDispositionVerified(r,pendingNonce,pendingTarget,pendingPulses))")
            coin_success = coin_branch.find('if(pollJsonTopLevelTrue(r,"ok"))')
            clear_pending = coin_branch.find("clearPending();")
            quarantine = coin_branch.find("quarantinePending(r);")
            if auth_guard < 0 or (clear_pending >= 0 and clear_pending < auth_guard) or (quarantine >= 0 and quarantine < auth_guard):
                print(board, "COIN_POST_DISPOSITION RED: no authenticated-disposition deny guard before journal disposition")
                failed.append(board)
            elif coin_success < auth_guard or clear_pending < coin_success:
                print(board, "COIN_POST_DISPOSITION RED: positive ACK path is not ordered after the deny guard")
                failed.append(board)
            elif coin_branch.find("r.indexOf(", 0, clear_pending) >= 0:
                print(board, "COIN_POST_DISPOSITION RED: substring-based success check remains before clearPending")
                failed.append(board)
            else:
                print(board, "COIN_POST_DISPOSITION PASS: unauthenticated response denied before clear/quarantine")
if failed: sys.exit("poll-response fail-closed lab failed: "+",".join(failed))
print("PHYSICAL_COIN_ACCEPTOR_VERIFIED=0")
print("PRODUCTION_FINANCIAL_AUTHORIZED=0")


# PHX-HARDWARE pulse-window and debounce-floor regression.
# This compiles the actual clamp, line-state, poll-window and output-gate functions
# from both sketches. It is host simulation, not electrical or coin-acceptor proof.
WINDOW_STUBS = r"""
#include <cstdint>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  size_t length() const { return size(); }
};
bool fsReady=true, journalRecoveryRequired=false, pendingReady=false;
bool outputPolarityKnown=true;
bool pollIntakeSuspended=false, pinConfigSafe=true;
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
    pollIntakeSuspended=false; pinConfigSafe=true; controllerEnabled=true; coinEnabled=true;
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
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=19) return 16;
    resetState(); runDebounceMs=boundedCoinDebounceMs(1);
    if(!beginPollWindow() || !pollIntakeSuspended || relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=250) return 17;
    resetState(); runCoinActiveLow=false; runDebounceMs=boundedCoinDebounceMs(1);
    pulseStart=19; pulseEnd=49;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=19) return 18;

    // A pulse can still be propagating from the acceptor output stage after
    // relay de-energization. The 100 ms contract maximum plus 20 ms margin
    // must be observed before the blocking poll may start.
    resetState(); runDebounceMs=boundedCoinDebounceMs(1); pulseStart=80; pulseEnd=180;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=80 || coinLineIdle()) return 22;
    resetState(); runDebounceMs=40; pulseStart=80; pulseEnd=180;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=80 || coinLineIdle()) return 23;
    // A second pulse 200 ms after inhibit is still inside the 250 ms
    // inter-coin quiet boundary and must cancel the blocking poll.
    resetState(); runDebounceMs=40; pulseStart=200; pulseEnd=280;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
       !relayOffObservedWhileSuspended || fakeNow!=200 || coinLineIdle()) return 24;

    // A pulse beginning exactly at the 250 ms quiet boundary must cancel the poll.
    resetState(); runDebounceMs=40; pulseStart=250; pulseEnd=330;
    if(beginPollWindow() || pollIntakeSuspended || !relayOn ||
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
for board, path in BOARDS.items():
    source = path.read_text(encoding="utf-8")
    minimum_calls = 2 if board == "ESP8266" else 4
    if source.count("boundedCoinDebounceMs(") < minimum_calls:
        raise RuntimeError(f"{board}: not all debounce configuration paths use the 20 ms clamp")
    loop = extract(source, "loop")
    order = [
        loop.find("beginPollWindow()"),
        loop.find('String r=post("poll")'),
        loop.find("acceptPollResponse(r)"),
        loop.find("pollIntakeSuspended=false"),
    ]
    if any(pos < 0 for pos in order) or order != sorted(order):
        raise RuntimeError(f"{board}: poll guard/response/release ordering changed: {order}")
    functions = "\n".join([
        extract(source, "boundedCoinDebounceMs"),
        extract(source, "applyOutputs"),
        extract(source, "coinLineIdle"),
        extract(source, "canStartPoll"),
        extract(source, "coinLineQuietAfterInhibit"),
        extract(source, "beginPollWindow"),
    ])
    code = WINDOW_STUBS + functions + WINDOW_MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-window-") as folder:
        cpp = Path(folder) / "poll_window.cpp"
        binary = Path(folder) / "poll_window"
        cpp.write_text(code, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board}: poll-window compile failed:\n{built.stderr[-3000:]}")
        ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        if ran.returncode:
            raise RuntimeError(f"{board}: poll-window scenarios failed ({ran.returncode}): {ran.stderr}")
        print(f"{board}: {ran.stdout.strip()}; source ordering PASS")

    # Failure injection: removing the final idle sample must be caught by the
    # pulse that begins exactly at the 250 ms quiet boundary.
    quiet = extract(source, "coinLineQuietAfterInhibit")
    if quiet.count("return coinLineIdle();") != 1:
        raise RuntimeError(f"{board}: expected one final coinLineIdle() sample to mutate")
    mutated_quiet = quiet.replace("return coinLineIdle();", "return true;", 1)
    mutated_functions = "\n".join([
        extract(source, "boundedCoinDebounceMs"),
        extract(source, "applyOutputs"),
        extract(source, "coinLineIdle"),
        extract(source, "canStartPoll"),
        mutated_quiet,
        extract(source, "beginPollWindow"),
    ])
    mutated_code = WINDOW_STUBS + mutated_functions + WINDOW_MAIN
    with tempfile.TemporaryDirectory(prefix="phx-poll-window-mutation-") as folder:
        cpp = Path(folder) / "poll_window_mutated.cpp"
        binary = Path(folder) / "poll_window_mutated"
        cpp.write_text(mutated_code, encoding="utf-8")
        built = subprocess.run(
            [ "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
              "-Wno-unused-parameter", str(cpp), "-o", str(binary) ],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(f"{board}: mutated poll-window compile failed:\n{built.stderr[-3000:]}")
        mutated = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
        if mutated.returncode != 25:
            raise RuntimeError(
                f"{board}: remove-final-quiet-sample mutation was not rejected at exact-boundary case 25; "
                f"exit={mutated.returncode}; stdout={mutated.stdout}; stderr={mutated.stderr}"
            )
        print(f"{board}: MUTATION_REJECTED remove-final-quiet-sample (exit=25)")

