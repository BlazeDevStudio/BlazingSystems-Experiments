#!/usr/bin/env python3
"""PHX-HARDWARE exact-source C++17 coin POST admission/disposition LAB.

Validates pending dispatch authority and response-to-journal routing from the
actual ESP32/ESP8266 helpers. Includes authentication-gate failure injection.
NO real backend, money or hardware.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "esp8266/BlazePwifiVendo"))
from firmware_lab_source import extract_function
BOARDS = [
    ("ESP32", ROOT/"esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT/"esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
]

TEMPLATE=r'''
#include <cstdint>
#include <iostream>
bool fsReady=false, journalRecoveryRequired=false, pendingReady=false, pendingPostAttempted=false;
bool outputPolarityKnown=true, pinConfigSafe=true;
uint8_t pendingPulses=0;
@@FUNCTION@@
struct Case{
  bool fs, recovery, ready, pinSafe, polarityKnown;
  uint8_t pulses;
  bool expected;
};
int main(){
  const Case cases[]={
    {true,false,true,true,true,3,true},
    {true,false,true,true,true,1,true},
    {true,false,true,true,true,20,true},
    {true,false,false,true,true,3,false},
    {false,false,true,true,true,3,false},
    {true,true,true,true,true,3,false},
    {true,false,true,true,true,0,false},
    {false,true,true,true,true,3,false},
    {false,false,false,true,true,0,false},
    {true,false,true,false,true,3,false},
    // Unknown output polarity must deny coin dispatch even with a valid journal and pin map.
    {true,false,true,true,false,3,false},
  };
  for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i){
    fsReady=cases[i].fs;
    journalRecoveryRequired=cases[i].recovery;
    pendingReady=cases[i].ready;
    pinConfigSafe=cases[i].pinSafe;
    outputPolarityKnown=cases[i].polarityKnown;
    pendingPulses=cases[i].pulses;
    const bool actual=canAttemptCoinPost();
    if(actual!=cases[i].expected){
      std::cerr<<"COIN_POST_GATE_FAIL case "<<i<<": got "<<actual<<"\n";
      return 1;
    }
  }
  outputPolarityKnown=true;
  pendingPostAttempted=true;
  pinConfigSafe=true;
  fsReady=true; journalRecoveryRequired=false; pendingReady=true; pendingPulses=3;
  if(canAttemptCoinPost()){
    std::cerr<<"COIN_POST_GATE_FAIL attempt marker must block dispatch\\n";
    return 2;
  }
  std::cout<<"COIN_POST_GATE_PASS 12/12 exact helper scenarios, not hardware evidence\n";
  return 0;
}
'''
for board,path in BOARDS:
    source=path.read_text(encoding="utf-8")
    func=extract_function(source,"canAttemptCoinPost")
    if "outputPolarityKnown" not in func or "pinConfigSafe" not in func or "fsReady" not in func or "!journalRecoveryRequired" not in func or "!pendingPostAttempted" not in func or "pendingReady" not in func or "pendingPulses>0" not in func:
        raise SystemExit(f"{board}: missing required pending dispatch condition")
    loop=extract_function(source,"loop")
    if "if(canAttemptCoinPost() && WiFi.status()==WL_CONNECTED" not in loop:
        raise SystemExit(f"{board}: coin post bypasses journal guard")
    if 'post("coin"' not in loop:
        raise SystemExit(f"{board}: unexpected coin post call site")
    pulse_capture=extract_function(source,"sampleCoinPulseEdge")
    if "if(!savePending())" not in pulse_capture or "fsReady=false;" not in pulse_capture or "pendingReady=true;" not in pulse_capture:
        raise SystemExit(f"{board}: failed journal write handling missing from pulse-capture helper")
    if "sampleCoinPulseEdge(active)" not in loop:
        raise SystemExit(f"{board}: loop does not call the guarded pulse-capture helper")
    code=TEMPLATE.replace("@@FUNCTION@@",func)
    with tempfile.TemporaryDirectory(prefix="phx-post-gate-") as tmp:
        sourcepath=Path(tmp)/"gate.cpp"
        outputpath=Path(tmp)/"gate"
        sourcepath.write_text(code,encoding="utf-8")
        subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O2",
                        str(sourcepath),"-o",str(outputpath)],check=True)
        subprocess.run([str(outputpath)],check=True)
    print(f"{board}: actual canAttemptCoinPost() compiled and tested")

    # Failure-inject removal of the polarity-known guard. The new case above
    # must reject this mutant before any coin POST could be attempted.
    mutated = func.replace("outputPolarityKnown && ", "", 1)
    if mutated == func:
        raise SystemExit(f"{board}: output-polarity guard mutation anchor missing")
    mutant_code = TEMPLATE.replace("@@FUNCTION@@", mutated)
    with tempfile.TemporaryDirectory(prefix="phx-post-gate-mutant-") as tmp:
        sourcepath = Path(tmp) / "gate-mutant.cpp"
        outputpath = Path(tmp) / "gate-mutant"
        sourcepath.write_text(mutant_code, encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
                        str(sourcepath), "-o", str(outputpath)], check=True)
        mutant = subprocess.run([str(outputpath)], capture_output=True, text=True, timeout=10)
        if mutant.returncode != 1:
            raise SystemExit(
                f"{board}: remove-output-polarity-guard mutation survived; "
                f"exit={mutant.returncode}; stdout={mutant.stdout}; stderr={mutant.stderr}"
            )
    print(f"{board}: MUTATION_REJECTED remove-output-polarity-guard (exit=1)")
DISPATCH_TEMPLATE = r'''
#include <cstdint>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  String(const std::string &value):std::string(value){}
  int indexOf(const char *needle) const {
    const auto pos=find(needle);
    return pos==npos?-1:static_cast<int>(pos);
  }
};
bool journalRecoveryRequired=false;
uint8_t pendingPulses=3;
String pendingNonce("nonce12345678"), pendingTarget("target12345678");
bool verifierResult=false, rootOk=false, reconcileResult=true;
unsigned clearCalls=0, quarantineCalls=0, reconcileCalls=0, outputCalls=0;
struct SerialStub { void println(const char*) const {} } Serial;
bool coinPostDispositionVerified(const String &response,const String &nonce,
                                 const String &target,uint8_t pulses) {
  (void)response; (void)nonce; (void)target; (void)pulses;
  return verifierResult;
}
bool pollJsonTopLevelTrue(const String &response,const char *key) {
  (void)response;
  return key && std::string(key)=="ok" && rootOk;
}
bool reconcileUnobservedCoinEdges(){++reconcileCalls;return reconcileResult;}
bool clearPending(){++clearCalls;return true;}
bool quarantinePending(const String &response){(void)response;++quarantineCalls;return true;}
void applyOutputs(){++outputCalls;}
@@FUNCTION@@
static void reset(bool verified,bool accepted,bool reconcile) {
  journalRecoveryRequired=false;
  verifierResult=verified; rootOk=accepted; reconcileResult=reconcile;
  clearCalls=quarantineCalls=reconcileCalls=outputCalls=0;
  pendingPulses=3;
  pendingNonce=String("nonce12345678");
  pendingTarget=String("target12345678");
}
int main() {
  reset(false,true,true);
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(!journalRecoveryRequired || clearCalls || quarantineCalls || reconcileCalls || outputCalls!=1) return 11;
  reset(false,false,true);
  handleCoinPostResponse(String("coin window expired"));
  if(!journalRecoveryRequired || clearCalls || quarantineCalls || reconcileCalls || outputCalls!=1) return 12;
  reset(false,false,true);
  handleCoinPostResponse(String("coin target mismatch"));
  if(!journalRecoveryRequired || clearCalls || quarantineCalls || reconcileCalls || outputCalls!=1) return 13;
  reset(true,true,true);
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(journalRecoveryRequired || clearCalls!=1 || quarantineCalls || reconcileCalls!=2 || outputCalls!=1) return 21;
  reset(true,false,true);
  handleCoinPostResponse(String("coin window expired"));
  if(journalRecoveryRequired || clearCalls || quarantineCalls!=1 || reconcileCalls!=1 || outputCalls!=1) return 22;
  reset(true,false,true);
  handleCoinPostResponse(String("network timeout"));
  if(!journalRecoveryRequired || clearCalls || quarantineCalls || reconcileCalls!=1 || outputCalls!=1) return 23;
  reset(true,true,false);
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(clearCalls || quarantineCalls || reconcileCalls!=2 || outputCalls!=2) return 24;
  std::cout<<"COIN_POST_DISPOSITION_DISPATCH_PASS 7/7; fake boundaries only\n";
  return 0;
}
'''
CLEAR_RACE_TEMPLATE = r'''
#include <cstdint>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  String(const std::string &value):std::string(value){}
  int indexOf(const char *needle) const {
    const auto pos=find(needle);
    return pos==npos?-1:static_cast<int>(pos);
  }
};
bool journalRecoveryRequired=false, pendingReady=false;
uint8_t pendingPulses=3;
String pendingNonce("nonce12345678"), pendingTarget("target12345678");
bool verifierResult=true, rootOk=true, injectEdgeDuringClear=false, outputsOff=false;
uint32_t coinEdgeSequence=0, lastHandledCoinEdgeSequence=0, faultPulseCount=0;
unsigned snapshotCalls=0, faultCalls=0, clearCalls=0, quarantineCalls=0, outputCalls=0;
struct SerialStub {
  template<class T> void println(const T&) const {}
} Serial;
bool coinPostDispositionVerified(const String&,const String&,const String&,uint8_t){
  return verifierResult;
}
bool pollJsonTopLevelTrue(const String&,const char *key){
  return key && std::string(key)=="ok" && rootOk;
}
uint32_t snapshotCoinEdgeSequence(){ ++snapshotCalls; return coinEdgeSequence; }
void latchPollPulseFault(uint32_t pulseEdges){
  ++faultCalls;
  faultPulseCount+=pulseEdges;
  journalRecoveryRequired=true;
}
bool clearPending(){
  ++clearCalls;
  pendingPulses=0;
  pendingReady=false;
  if(injectEdgeDuringClear) ++coinEdgeSequence;
  return true;
}
bool quarantinePending(const String&){ ++quarantineCalls; return true; }
void applyOutputs(){ ++outputCalls; outputsOff=journalRecoveryRequired; }
@@RECONCILE@@
@@FUNCTION@@
static void reset(){
  journalRecoveryRequired=false;
  pendingReady=false;
  pendingPulses=3;
  pendingNonce=String("nonce12345678");
  pendingTarget=String("target12345678");
  verifierResult=true;
  rootOk=true;
  injectEdgeDuringClear=false;
  outputsOff=false;
  coinEdgeSequence=0;
  lastHandledCoinEdgeSequence=0;
  faultPulseCount=0;
  snapshotCalls=faultCalls=clearCalls=quarantineCalls=outputCalls=0;
}
int main(){
  // Inject an ISR edge while clearPending() performs its filesystem work.
  // This is first so the no-second-snapshot mutation fails on this race itself.
  reset();
  injectEdgeDuringClear=true;
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(clearCalls!=1 || snapshotCalls!=2 || faultCalls!=1 ||
     faultPulseCount!=1 || !journalRecoveryRequired || !outputsOff ||
     outputCalls!=2 || pendingPulses!=0) return 32;

  // Control: no edge during durable pending clear; both snapshots remain clean.
  reset();
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(clearCalls!=1 || snapshotCalls!=2 || faultCalls!=0 ||
     journalRecoveryRequired || outputCalls!=1 || outputsOff) return 31;

  // An edge already present before the first snapshot blocks clear entirely.
  reset();
  coinEdgeSequence=1U;
  handleCoinPostResponse(String("{\"ok\":true}"));
  if(clearCalls!=0 || snapshotCalls!=2 || faultCalls!=1 ||
     faultPulseCount!=4 || !journalRecoveryRequired || !pendingReady ||
     pendingPulses!=3 || outputCalls!=1 || !outputsOff) return 33;

  std::cout<<"POST_CLEAR_ISR_RECHECK_PASS 3/3; simulated source boundary only\n";
  return 0;
}
'''

GUARD = '''  if(!coinPostDispositionVerified(response,pendingNonce,pendingTarget,pendingPulses)){
    journalRecoveryRequired=true;
    Serial.println("CRITICAL: coin POST response lacks approved event-bound authentication; pending evidence retained and automatic replay denied.");
    applyOutputs();
    return;
  }
'''
for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    helper = extract_function(source, "handleCoinPostResponse")
    if helper.count(GUARD) != 1:
        raise SystemExit(f"{board}: event-bound authentication guard changed unexpectedly")

    def compile_and_run(function_source, label):
        code = DISPATCH_TEMPLATE.replace("@@FUNCTION@@", function_source)
        with tempfile.TemporaryDirectory(prefix="phx-coin-disposition-") as tmp:
            cpp = Path(tmp) / "dispatch.cpp"
            binary = Path(tmp) / "dispatch"
            cpp.write_text(code, encoding="utf-8")
            built = subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-O2", str(cpp), "-o", str(binary)],
                capture_output=True, text=True, timeout=30
            )
            if built.returncode:
                raise RuntimeError(f"{board} {label} compile failed:\n{built.stderr[-3000:]}")
            return subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)

    normal = compile_and_run(helper, "dispatch")
    if normal.returncode:
        raise SystemExit(f"{board}: dispatch scenarios failed exit={normal.returncode}: {normal.stderr}")
    print(f"{board}: {normal.stdout.strip()}")

    mutated = helper.replace(GUARD, "  // injected mutation: bypass event-bound authorization gate\n", 1)
    mutant = compile_and_run(mutated, "auth-gate-mutation")
    if mutant.returncode != 11:
        raise SystemExit(
            f"{board}: bypass-auth-gate mutation was not rejected at case 11; "
            f"exit={mutant.returncode}; stdout={mutant.stdout}; stderr={mutant.stderr}"
        )
    print(f"{board}: MUTATION_REJECTED bypass-event-bound-authentication (exit=11)")

    # Compile the real edge-reconciliation helper with the real disposition handler.
    # Inject an ISR edge during clearPending() and require the post-clear snapshot
    # to latch a durable-deny decision before the handler returns.
    reconcile = extract_function(source, "reconcileUnobservedCoinEdges")
    if "snapshotCoinEdgeSequence()" not in reconcile or "latchPollPulseFault(" not in reconcile:
        raise SystemExit(f"{board}: source reconciliation helper lost its edge/fault boundary")

    def compile_clear_race(function_source, label):
        code = CLEAR_RACE_TEMPLATE.replace("@@RECONCILE@@", reconcile).replace(
            "@@FUNCTION@@", function_source
        )
        with tempfile.TemporaryDirectory(prefix="phx-post-clear-race-") as tmp:
            cpp = Path(tmp) / "race.cpp"
            binary = Path(tmp) / "race"
            cpp.write_text(code, encoding="utf-8")
            built = subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-O2", str(cpp), "-o", str(binary)],
                capture_output=True, text=True, timeout=30
            )
            if built.returncode:
                raise RuntimeError(f"{board} {label} compile failed:\n{built.stderr[-3000:]}")
            return subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)

    race = compile_clear_race(helper, "post-clear-isr-recheck")
    if race.returncode:
        raise SystemExit(
            f"{board}: post-clear ISR race failed exit={race.returncode}: "
            f"stdout={race.stdout}; stderr={race.stderr}"
        )
    print(f"{board}: {race.stdout.strip()}")

    recheck = "if(!reconcileUnobservedCoinEdges()) applyOutputs();"
    mutated_race_handler = helper.replace(
        recheck, "// injected mutation: omit the post-clear ISR snapshot", 1
    )
    if mutated_race_handler == helper:
        raise SystemExit(f"{board}: post-clear reconciliation mutation anchor missing")
    mutant_race = compile_clear_race(mutated_race_handler, "removed-post-clear-recheck")
    if mutant_race.returncode != 32:
        raise SystemExit(
            f"{board}: removed post-clear ISR recheck mutation survived; "
            f"exit={mutant_race.returncode}; stdout={mutant_race.stdout}; stderr={mutant_race.stderr}"
        )
    print(f"{board}: MUTATION_REJECTED remove-post-clear-isr-recheck (exit=32)")


print("PHX-HARDWARE: 24/24 coin POST gate + 14/14 disposition dispatch cases PASS; actual money NOT TESTED")
