"""Scenario fixture builders for the blocking-poll host regression lab.

Keep C++ fixture text and board-parity contracts separate from orchestration.
These cases execute extracted production helpers with host stubs only.
"""

from poll_loop_blocking_inhibit_lab_fixtures import MAIN, missed_sample_main

ACTIVE_HIGH_MISSED_SAMPLE_MAIN = missed_sample_main(active_low=False, failure_code=57)
ACTIVE_LOW_MISSED_SAMPLE_MAIN = missed_sample_main(active_low=True, failure_code=58)

# Exercise the production sampleCoinPulseEdge() after the first sticky fault.
# Later ISR edges must not rewrite the first-fault snapshot or reopen admission.
STICKY_FAULT_LATER_ISR_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  allowCoinPost=true;
  pendingPulses=2U;
  pendingReady=false;
  pendingTarget="pending-target";
  pendingNonce="pending-nonce";
  pendingPostAttempted=false;
  coinEdgeSequence=2U;
  lastHandledCoinEdgeSequence=0U;
  relayOn=true;
  ledOn=true;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || backupFirstFaultPulseEdges!=4U ||
     backupWriteAttempts!=1U || pendingPulses!=2U || !pendingReady ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty()) return 89;
  const std::string firstMarker=LittleFS.files["/pollpulse.fault"];
  if(firstMarker.find("pulses=4")==std::string::npos) return 89;
  const uint8_t firstPendingPulses=pendingPulses;
  const std::string firstPendingTarget=pendingTarget;
  const std::string firstPendingNonce=pendingNonce;
  const int firstSaveCalls=saveCalls;
  const int firstCoinPostCalls=coinPostCalls;

  coinEdgeISR();
  coinEdgeISR();
  coinEdgeISR();
  sampleCoinPulseEdge(false);
  applyOutputs();

  if(backupFirstFaultPulseEdges!=4U || backupWriteAttempts!=1U ||
     LittleFS.files["/pollpulse.fault"]!=firstMarker) return 90;
  if(pendingPulses!=firstPendingPulses || !pendingReady ||
     pendingTarget!=firstPendingTarget || pendingNonce!=firstPendingNonce ||
     pendingPostAttempted) return 91;
  if(saveCalls!=firstSaveCalls || coinPostCalls!=firstCoinPostCalls || clearCalls!=0) return 92;
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     relayOn || ledOn || canAttemptCoinPost() ||
     coinEdgeSequence!=lastHandledCoinEdgeSequence) return 93;
  std::cout<<"POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_AFTER_LATER_ISR_PASS"<<std::endl;
  return 0;
}
"""


ATTEMPTED_EVIDENCE_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  int result=runAttemptedPendingEvidenceCase(false,false,true,false,82,
      "POLL_DISABLED_RELAY_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  result=runAttemptedPendingEvidenceCase(false,false,true,true,83,
      "POLL_DISABLED_RELAY_ISR_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  result=runAttemptedPendingEvidenceCase(false,true,false,false,84,
      "POLL_DISABLED_COIN_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  result=runAttemptedPendingEvidenceCase(false,true,false,true,85,
      "POLL_DISABLED_COIN_ISR_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  result=runAttemptedPendingEvidenceCase(true,false,false,false,86,
      "POLL_DISABLED_CONTROLLER_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  result=runAttemptedPendingEvidenceCase(true,false,false,true,87,
      "POLL_DISABLED_CONTROLLER_ISR_ATTEMPTED_EVIDENCE_PRESERVED_PASS");
  if(result) return result;
  std::cout<<"POLL_DISABLED_INGRESS_ATTEMPTED_EVIDENCE_PRESERVATION_PASS 6/6"<<std::endl;
  return 0;
}
"""


def disabled_ingress_gate_main(disabled_flag: str, failure_code: int) -> str:
    """Build a single-edge deny case that isolates sample admission from output gating."""
    if disabled_flag not in {"controllerEnabled", "coinEnabled", "relayEnabled"}:
        raise ValueError("unknown configured coin-ingress gate")
    return MAIN[:MAIN.index("int main(){")] + f"""
int main(){{
  resetState();
  fakeNow=100U;
  lastEdge=0U;
  runDebounceMs=40U;
  lastCoin=false;
  insertMode=true;
  activeTarget="target-01";
  fsReady=true;
  journalRecoveryRequired=false;
  pendingReady=false;
  pendingPulses=0U;
  saveCalls=0U;
  coinEdgeSequence=1U;
  lastHandledCoinEdgeSequence=0U;
  {disabled_flag}=false;
  relayOn=false;
  ledOn=false;
  sampleCoinPulseEdge(true);
  applyOutputs();
  if(pendingPulses!=0U || saveCalls!=0U || !pendingNonce.empty() ||
     !pendingTarget.empty() || insertMode || !activeTarget.empty() ||
     !journalRecoveryRequired || relayOn || ledOn) return {failure_code};
  std::cout<<"DISABLED_INGRESS_BASELINE_DENY_PASS"<<std::endl;
  return 0;
}}
"""

def pre_poll_active_line_main(*, active_low: bool, failure_code: int) -> str:
    """Prove a pre-existing active line is sampled and journaled before poll admission."""
    polarity = "true" if active_low else "false"
    label = "ACTIVE_LOW" if active_low else "ACTIVE_HIGH"
    return MAIN[:MAIN.index("int main(){")] + rf"""
int main(){{
  resetState();
  runCoinActiveLow={polarity};
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin,runCoinActiveLow);
  // Re-establish the normal accepting output state after the helper's
  // safe-pin initialization, then make the line active without an ISR edge.
  applyOutputs();
  pulseStart=(int)fakeNow;
  pulseEnd=(int)fakeNow+80;
  loop();
  if(pollCalls!=0 || coinPostCalls!=0 || pollStartAt!=0 ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U ||
     pendingPulses!=1U || pendingReady ||
     pendingTarget!="target-01" || pendingNonce!="nonce12345678" ||
     saveCalls!=1 || journalRecoveryRequired || !lastCoin ||
     !relayOn || !ledOn || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine){{
    std::cerr<<"PRESTART_FIRST_STATE_FAIL poll="<<pollCalls
             <<" coinPost="<<coinPostCalls<<" edges="<<coinEdgeSequence
             <<" handled="<<lastHandledCoinEdgeSequence
             <<" pending="<<(unsigned)pendingPulses<<" ready="<<pendingReady
             <<" save="<<saveCalls<<" fault="<<journalRecoveryRequired
             <<" lastCoin="<<lastCoin<<" relay="<<relayOn<<" led="<<ledOn
             <<" suspended="<<pollIntakeSuspended
             <<" abort="<<pollDrainAbortedOnActiveLine<<"\\n";
    return {failure_code};
  }}
  fakeNow=(uint32_t)pulseEnd;
  loop();
  if(pollCalls!=0 || coinPostCalls!=0 || pendingPulses!=1U ||
     pendingReady || pendingTarget!="target-01" ||
     pendingNonce!="nonce12345678" || saveCalls!=1 ||
     journalRecoveryRequired || lastCoin || !relayOn || !ledOn ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine){{
    std::cerr<<"PRESTART_RELEASE_STATE_FAIL poll="<<pollCalls
             <<" coinPost="<<coinPostCalls<<" pending="<<(unsigned)pendingPulses
             <<" ready="<<pendingReady<<" save="<<saveCalls
             <<" fault="<<journalRecoveryRequired<<" lastCoin="<<lastCoin
             <<" relay="<<relayOn<<" led="<<ledOn
             <<" suspended="<<pollIntakeSuspended
             <<" abort="<<pollDrainAbortedOnActiveLine<<"\\n";
    return {failure_code};
  }}
  std::cout<<"POLL_PRESTART_{label}_NO_ISR_CAPTURED_ONCE_PASS\\n";
  return 0;
}}
"""

def late_poll_baseline_main() -> str:
    """Isolate an ISR edge that arrives after the quiet drain but before poll dispatch."""
    return MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  injectAfterDrainEdge=true;
  loop();
  if(pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() || pollIntakeSuspended ||
     pendingPulses!=0U || lastPoll+2!=fakeNow ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 22;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return 24;
  std::cout<<"POLL_PRE_DRAIN_BASELINE_EDGE_CONTROL_PASS"<<std::endl;
  return 0;
}
"""


POLL_SAFETY_PARITY = (
    "coinEdgeISR",
    "snapshotCoinEdgeSequence",
    "boundedCoinDebounceMs",
    "canStartPoll",
    "applyOutputs",
    "coinIngressConfigurationAllows",
    "beginPollWindow",
    "sampleCoinPulseEdge",
    "latchPollPulseFault",
    "quarantineCoinIngressTransition",
    "handlePollDrainAbortAfterSample",
    "reconcileUnobservedCoinEdges",
    # Shared trust, receipt and pending-evidence authority must not drift by board.
    "acceptPollResponse",
    "coinPostDispositionVerified",
    "canAttemptCoinPost",
    "markPendingPostAttempt",
    "pendingAttemptMarkerMatches",
    "clearPending",
    "quarantinePending",
)


REQUIRED_COIN_AUTHORITY_PARITY = (
    "acceptPollResponse",
    "coinPostDispositionVerified",
    "canAttemptCoinPost",
    "markPendingPostAttempt",
    "pendingAttemptMarkerMatches",
    "clearPending",
    "quarantinePending",
)
missing_coin_authority_helpers = [
    name for name in REQUIRED_COIN_AUTHORITY_PARITY
    if name not in POLL_SAFETY_PARITY
]
if missing_coin_authority_helpers:
    raise SystemExit(
        "POLL_COIN_AUTHORITY_PARITY_REQUIRED_HELPERS_MISSING: "
        + ", ".join(missing_coin_authority_helpers)
    )

__all__ = [
    "ACTIVE_HIGH_MISSED_SAMPLE_MAIN",
    "ACTIVE_LOW_MISSED_SAMPLE_MAIN",
    "ATTEMPTED_EVIDENCE_MAIN",
    "POLL_SAFETY_PARITY",
    "REQUIRED_COIN_AUTHORITY_PARITY",
    "STICKY_FAULT_LATER_ISR_MAIN",
    "disabled_ingress_gate_main",
    "pre_poll_active_line_main",
    "late_poll_baseline_main",
    "missing_coin_authority_helpers",
]
