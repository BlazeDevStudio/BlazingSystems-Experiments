"""Poll/ISR timing and release-edge scenarios for the blocking-poll host lab.

Keep timing, race and release-edge programs out of the shared production-source
fixture. These scenarios still execute extracted board code with host stubs.
"""

from poll_loop_blocking_inhibit_lab_scenario_fixtures import MAIN

COIN_POST_ISR_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  allowCoinPost=true;
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  insertMode=false;
  activeTarget="";
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectDuringCoinPost=true;
  injectDuringCoinPostEdgeCount=2U;
  loop();
  if(coinPostCalls!=1 || clearCalls!=0 || pendingPulses!=4U ||
     !pendingReady || !pendingPostAttempted || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U ||
     pendingTarget!="target-01" || pendingNonce!="nonce-existing") return 45;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=6")==std::string::npos) return 45;
  std::cout<<"COIN_POST_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS\\n";
  return 0;
}
"""


POLL_HTTP_ISR_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectDuringHttp=true;
  injectDuringHttpEdgeCount=2U;
  loop();
  if(pollCalls!=1 || coinPostCalls!=0 || clearCalls!=0 ||
     pollStartAt==0U || pollEndAt-pollStartAt!=3500UL ||
     !pollStartCoinIdle || pollStartRelayOn || !pollStartSuspended ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     pollEndRelayOn || !pollEndSuspended || !pollHttpReturned ||
     !pollPostHttpSampleObserved || !pollPostHttpFaultLatchedBeforeSample ||
     !pollPostHttpMarkerPresentBeforeSample || !pollPostHttpOutputsOffBeforeSample ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine ||
     pendingPulses!=0U || pendingReady || pendingPostAttempted ||
     !pendingTarget.empty() || !pendingNonce.empty() ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U) return 88;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=2")==std::string::npos) return 88;
  std::cout<<"POLL_HTTP_ISR_MULTI_EDGE_ROLLOVER_RETAINED_PASS"<<std::endl;
  return 0;
}
"""


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
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin,runCoinActiveLow);
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
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin,runCoinActiveLow);
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


TIMING_MAIN = MAIN.replace(
    "int main(){",
    """int main(){
  resetState();
  fakeNow=1501U;
  pulseStart=1600;
  pulseEnd=1680;
  injectTimedPollPulse=true;
  loop();
  if(!timedPulseIsrInjected || pollCalls!=0 || pollStartAt!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine) return 47;
  const std::string timingMarker=LittleFS.files["/pollpulse.fault"];
  if(timingMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     timingMarker.find("pulses=1")==std::string::npos) return 49;
  std::cout<<"PHX_177_ORIGINAL_1501_1600_1680_PULSE_ABORTED_BEFORE_HTTP_PASS\\n";
  return 0;
""",
    1,
)


RELEASE_EDGE_MAIN = r"""
void resetReleaseEdgeState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  coinEdgeSequence=0; lastHandledCoinEdgeSequence=0;
  interruptAttached=true; attachedPin=4; attachedMode=FALLING; attachedIsr=coinEdgeISR;
  relayOn=false; ledOn=false; relayLevelHigh=false; ledLevelHigh=false;
  pollCalls=0; pollIntakeSuspended=false; journalRecoveryRequired=false;
  pendingReady=false; pendingPulses=0; pendingPostAttempted=false; fsReady=true;
  outputPolarityKnown=true; pinConfigSafe=true; controllerEnabled=true;
  coinEnabled=true; relayEnabled=true; ledEnabled=true; insertMode=true;
  runCoinActiveLow=true; runRelayActiveHigh=true; runLedActiveHigh=true;
  runCoinPin=4; runRelayPin=26; runLedPin=2; activeTarget="target-01";
  pollReleaseEdgeInjected=false; pollReleaseEdgeSawRelayOff=false;
  pollReleaseRelayEnergizedBeforeLatch=false; pollReleaseRelayClearedBeforeLatch=false;
  injectDuringPollRelease=false; injectDuringPollReleaseAtRelayWrite=false;
}
int main(){
  // This isolated output-gate build does not use the poll-drain hook.
  (void)injectAfterDrainEdge;
  // Isolate the output gate with a previously valid positive local state.
  // The poll response itself remains default-deny in the production sketch.
  resetReleaseEdgeState();
  pollIntakeSuspended=true;
  applyOutputs();
  pollIntakeSuspended=false;
  pollCalls=1;
  injectDuringPollRelease=true;
  applyOutputs();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff ||
     pollReleaseRelayEnergizedBeforeLatch || !pollReleaseRelayClearedBeforeLatch ||
     relayOn || ledOn || journalRecoveryRequired ||
     coinEdgeSequence==lastHandledCoinEdgeSequence) return 52;
  std::cout<<"POLL_RELEASE_LED_WRITE_ISR_EDGE_BLOCKS_RELAY_PASS\n";

  resetReleaseEdgeState();
  pollIntakeSuspended=true;
  applyOutputs();
  pollIntakeSuspended=false;
  pollCalls=1;
  injectDuringPollReleaseAtRelayWrite=true;
  applyOutputs();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff ||
     !pollReleaseRelayEnergizedBeforeLatch || !pollReleaseRelayClearedBeforeLatch ||
     relayOn || ledOn || journalRecoveryRequired ||
     coinEdgeSequence==lastHandledCoinEdgeSequence) return 53;
  std::cout<<"POLL_RELEASE_RELAY_WRITE_ISR_EDGE_DEASSERTED_PASS\n";
  return 0;
}
"""





def with_active_low_relay(main_source: str) -> str:
    """Run a blocking-poll scenario with the acceptor relay active-low from reset.

    The reset fixture configures and energizes the logical relay before loop().
    The poll inhibit must then de-energize it using the configured active-low OFF
    level before the synchronous HTTP call can begin.
    """
    polarity_anchor = "runRelayActiveHigh=true;"
    if main_source.count(polarity_anchor) != 1:
        raise AssertionError("active-low relay reset anchor is not unique")
    main_source = main_source.replace(polarity_anchor, "runRelayActiveHigh=false;", 1)
    startup_anchor = "int main(){\n  resetState();"
    if main_source.count(startup_anchor) != 1:
        raise AssertionError("active-low relay main startup anchor is not unique")
    return main_source.replace(
        startup_anchor,
        "int main(){\n  resetState();\n  if(!relayOn || relayLevelHigh) return 46;",
        1,
    )

__all__ = [
    "COIN_POST_ISR_MAIN",
    "POLL_HTTP_ISR_MAIN",
    "RACE_MAIN",
    "post_drain_rollover_main",
    "missed_sample_main",
    "TIMING_MAIN",
    "RELEASE_EDGE_MAIN",
    "with_active_low_relay",
]
