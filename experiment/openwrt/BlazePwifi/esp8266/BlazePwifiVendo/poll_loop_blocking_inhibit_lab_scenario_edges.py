"""ISR edge, drain-abort, rollover, and missed-sample scenarios.

Keep C++ scenario payloads literal and independent of the runner."""

from poll_loop_blocking_inhibit_lab_scenario_main import MAIN

RACE_MAIN = MAIN.replace(
    "  // Existing pulse-drain behavior remains intact for a pulse observed before poll.",
    "  // An ISR edge after the final quiet sample must be persisted before HTTP begins.\n"
    "  resetState(); injectAfterDrainEdge=true; loop();\n"
    "  if(pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||\n"
    "     !LittleFS.exists(\"/pollpulse.fault\") || relayOn || ledOn ||\n"
    "     insertMode || !activeTarget.empty() || pollIntakeSuspended ||\n"
    "     pendingPulses!=0 || lastPoll+2!=fakeNow ||\n"
    "     backupWriteSawRelayOn || backupWriteSawLedOn ||\n"
    "     markerOpenSawRelayOn || markerOpenSawLedOn) return 22;\n"
    "  const std::string prePollMarker=LittleFS.files[\"/pollpulse.fault\"];\n"
    "  if(prePollMarker.find(\"COIN_INGRESS_UNRESOLVED\")==std::string::npos ||\n"
    "     prePollMarker.find(\"pulses=1\")==std::string::npos) return 24;\n\n"
    "  // Two ISR edges after the final quiet sample must retain modulo count across wrap.\n"
    "  resetState();\n"
    "  coinEdgeSequence=0xFFFFFFFEUL;\n"
    "  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;\n"
    "  injectAfterDrainEdgeCount=2;\n"
    "  injectAfterDrainEdge=true;\n"
    "  loop();\n"
    "  if(pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||\n"
    "     !LittleFS.exists(\"/pollpulse.fault\") || relayOn || ledOn ||\n"
    "     insertMode || !activeTarget.empty() || pollIntakeSuspended ||\n"
    "     pendingPulses!=0 || coinEdgeSequence!=0U ||\n"
    "     lastHandledCoinEdgeSequence!=0U || lastPoll+2!=fakeNow) return 54;\n"
    "  const std::string wrappedPrePollMarker=LittleFS.files[\"/pollpulse.fault\"];\n"
    "  if(wrappedPrePollMarker.find(\"COIN_INGRESS_UNRESOLVED\")==std::string::npos ||\n"
    "     wrappedPrePollMarker.find(\"pulses=2\")==std::string::npos) return 55;\n"
    "  std::cout<<\"POLL_POST_DRAIN_MULTI_EDGE_ROLLOVER_DENY_PASS\\\\n\";\n\n"

    "  // Existing pulse-drain behavior remains intact for a pulse observed before poll.",
    1,
)
def post_drain_rollover_main(active_low: bool) -> str:
    """Build the same rollover regression for either physical input polarity."""
    polarity = "true" if active_low else "false"
    interrupt_mode = "FALLING" if active_low else "RISING"
    scenario = "ACTIVE_LOW" if active_low else "ACTIVE_HIGH"
    failure_code = 59 if active_low else 56
    return MAIN[:MAIN.index("int main(){")] + rf"""
int main(){{
  resetState();
  runCoinActiveLow={polarity};
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectAfterDrainEdgeCount=2;
  injectAfterDrainEdge=true;
  loop();
  if(attachedMode!={interrupt_mode} || pollCalls!=0 || pollStartAt!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pendingPulses!=0U ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U ||
     lastPoll+2!=fakeNow) return {failure_code};
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=2")==std::string::npos) return {failure_code};
  std::cout<<"POLL_POST_DRAIN_{scenario}_MULTI_EDGE_ROLLOVER_DENY_PASS\\n";
  return 0;
}}
"""
def missed_sample_main(*, active_low: bool, failure_code: int) -> str:
    """Build the same missed-sample regression for either electrical input polarity."""
    polarity = "true" if active_low else "false"
    label = "LOW" if active_low else "HIGH"
    return MAIN[:MAIN.index("int main(){")] + rf"""
int main(){{
  resetState();
  runCoinActiveLow={polarity};
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDrainAbortWithoutIsr=true;
  injectDrainAbortPulseEndsBeforeSample=true;
  loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine ||
     pendingPulses!=0U || saveCalls!=0 ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return {failure_code};
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return {failure_code};
  std::cout<<"POLL_ABORT_ACTIVE_{label}_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS\\n";
  return 0;
}}
"""
