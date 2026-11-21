"""Poll timing and output-release window scenarios.

Keep C++ scenario payloads literal and independent of the runner."""

from poll_loop_blocking_inhibit_lab_scenario_main import MAIN

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
