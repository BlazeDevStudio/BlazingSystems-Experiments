"""Default executable scenario for the blocking-poll regression lab.

Keep the default scenario program separate from shared setup and board-specific
poll-window variants. The combined public MAIN fixture remains byte-identical.
"""

DEFAULT_MAIN = r"""int main(){

  // A prior persistent journal fault must abort even with an idle line and no new ISR edge.
  resetState();
  journalRecoveryRequired=true;
  lastCoin=true;
  relayOn=true;
  ledOn=true;
  const bool idleFaultAccepted=quarantineCoinIngressTransition();
  if(idleFaultAccepted || !journalRecoveryRequired || relayOn || ledOn || lastCoin) return 48;
  std::cout<<"POLL_INGRESS_PRIOR_JOURNAL_FAULT_IDLE_LINE_DENY_PASS\n";

  // A normal blocked poll remains inhibited and default-deny when no edge occurs.
  resetState(); loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollStartRelayOn ||
     !pollStartSuspended || !pollStartCoinIdle ||
     pollEndAt-pollStartAt!=3500 || pollEndRelayOn || !pollEndSuspended ||
     pollIntakeSuspended || relayOn || ledOn || insertMode ||
     !activeTarget.empty() || pendingPulses!=0 || journalRecoveryRequired ||
     LittleFS.exists("/pollpulse.fault") || lastPoll!=pollEndAt ||
     fakeNow!=pollEndAt+2) return 10;

  // Verify the latch requests OFF before either persistent store is entered.
  // The first hook is the secondary NVS/EEPROM writer; the second is LittleFS open.
  resetState();
  relayOn=true; ledOn=true; insertMode=true; activeTarget="target-01";
  latchPollPulseFault(1);
  if(backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn || relayOn || ledOn ||
     !journalRecoveryRequired || insertMode || !activeTarget.empty()) return 23;
  std::cout<<"POLL_FAULT_PRE_PERSISTENCE_OUTPUT_OFF_PASS backup-write and LittleFS-open\\n";

  // A pulse edge during the 3.5 s synchronous poll must be captured by the
  // production ISR, latched to LittleFS, and never interpreted as a credit.
  resetState(); injectDuringHttp=true; loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollStartAt-2000<250 ||
     pollStartRelayOn || !pollStartSuspended || !pollStartCoinIdle ||
     pollEndAt-pollStartAt!=3500 || pollEndRelayOn || !pollEndSuspended ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     pollIntakeSuspended || relayOn || ledOn || insertMode ||
     !activeTarget.empty() || pendingPulses!=0 || lastPoll!=pollEndAt ||
     fakeNow!=pollEndAt+2) return 11;
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 12;
  const std::string marker=LittleFS.files["/pollpulse.fault"];
  if(marker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     marker.find("pulses=1")==std::string::npos) return 13;

  // A reboot must restore the persistent fault latch before any output can energize.
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  applyOutputs();
  if(!relayOn) return 14;
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn) return 15;

  // The ISR edge counter is uint32_t: an edge during the blocked poll must
  // remain visible when the sequence wraps from UINT32_MAX to zero.
  resetState();
  coinEdgeSequence=0xFFFFFFFFUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFFUL;
  injectDuringHttp=true;
  loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollEndAt-pollStartAt!=3500 ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || lastPoll!=pollEndAt || fakeNow!=pollEndAt+2) return 50;
  const std::string rolloverMarker=LittleFS.files["/pollpulse.fault"];
  if(rolloverMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     rolloverMarker.find("pulses=1")==std::string::npos) return 50;
  std::cout<<"POLL_BLOCKED_ISR_SEQUENCE_ROLLOVER_DENY_PASS\\n";

  // Two ISR edges crossing UINT32_MAX must retain the exact modulo delta, not collapse to one.
  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  injectDuringHttpEdgeCount=2;
  injectDuringHttp=true;
  loop();
  if(pollCalls!=1 || pollStartAt!=2250 || pollEndAt-pollStartAt!=3500 ||
     !pollPulseObservedDuringHttp || !pollPulseRelayOff || !pollPulseSuspended ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pendingPulses!=0U || lastPoll!=pollEndAt || fakeNow!=pollEndAt+2) return 51;
  const std::string multiEdgeRolloverMarker=LittleFS.files["/pollpulse.fault"];
  if(multiEdgeRolloverMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     multiEdgeRolloverMarker.find("pulses=2")==std::string::npos) return 51;
  std::cout<<"POLL_BLOCKED_ISR_MULTI_EDGE_ROLLOVER_DENY_PASS\\n";

  // Active-high input polarity must attach the opposite edge and fail closed too.
  resetState(); runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDuringHttp=true; loop();
  if(attachedMode!=RISING || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 16;

  // A short write leaves a path that boot treats as a fault even when readback fails.
  resetState(); fakeShortWrite=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 17;
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || relayOn) return 18;

  // Readback corruption is rejected; existence alone remains a boot-time deny latch.
  resetState(); fakeCorruptReadback=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault")) return 19;
  journalRecoveryRequired=false; insertMode=true; activeTarget="target-01";
  initPendingStore(); applyOutputs();
  if(!journalRecoveryRequired || relayOn) return 20;

  // If marker creation itself is unavailable, the current boot still remains denied.
  resetState(); fakeOpenFail=true; injectDuringHttp=true; loop();
  if(!journalRecoveryRequired || LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 21;

  // A pulse can abort the drain and end before the next ordinary loop sample.
  // The ISR sequence must be reconciled and the deny marker persisted before release.
  resetState(); injectDuringDrainAbort=true; loop();
  if(!drainAbortInjected || drainAbortSawRelayOn || drainAbortSampleSawRelayOn ||
     drainAbortReenabledBeforeLatch || pollCalls!=0 || pollStartAt!=0 || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || lastPoll+2!=fakeNow ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 25;
  const std::string abortMarker=LittleFS.files["/pollpulse.fault"];
  if(abortMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     abortMarker.find("pulses=1")==std::string::npos) return 27;
  std::cout<<"POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS\\n";
  std::cout<<"POLL_ABORTED_DRAIN_ISR_EDGE_PERSISTED_PASS\\n";

  // The same drain-abort edge must be caught for active-high coin wiring.
  resetState(); runCoinActiveLow=false;
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  injectDuringDrainAbort=true; loop();
  if(!drainAbortInjected || drainAbortSawRelayOn || drainAbortSampleSawRelayOn ||
     drainAbortReenabledBeforeLatch || pollCalls!=0 || !journalRecoveryRequired ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || lastPoll+2!=fakeNow ||
     backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 28;
  std::cout<<"POLL_ABORTED_DRAIN_ISR_EDGE_ACTIVE_HIGH_PASS\\n";

  // An ISR edge can arrive after the pre-release snapshot but during the first
  // GPIO writes that re-enable the acceptor. It must be reconciled before the
  // next ordinary sample can turn that in-flight edge into a new pending coin.
  resetState(); injectDuringPollRelease=true; loop();
  if(!pollReleaseEdgeInjected || !pollReleaseEdgeSawRelayOff || pollCalls!=1 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() || pendingPulses!=0 ||
     pollIntakeSuspended || backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 29;
  const std::string releaseMarker=LittleFS.files["/pollpulse.fault"];
  if(releaseMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     releaseMarker.find("pulses=1")==std::string::npos) return 30;
  std::cout<<"POLL_RELEASE_WINDOW_ISR_EDGE_PERSISTED_PASS\\n";

  // One shared scenario body keeps active-low and active-high capture/hold/release
  // assertions identical while retaining distinct failure codes and log markers.
  const int activeLowDrainResult=runDrainAbortWithoutIsr(
      true, 34, 35,
      "POLL_ABORT_ACTIVE_LINE_WITHOUT_ISR_CAPTURED_HELD_PASS",
      "POLL_ABORT_ACTIVE_LINE_RELEASES_AFTER_IDLE_PASS");
  if(activeLowDrainResult!=0) return activeLowDrainResult;
  const int activeHighDrainResult=runDrainAbortWithoutIsr(
      false, 36, 37,
      "POLL_ABORT_ACTIVE_HIGH_WITHOUT_ISR_CAPTURED_HELD_PASS",
      "POLL_ABORT_ACTIVE_HIGH_RELEASES_AFTER_IDLE_PASS");
  if(activeHighDrainResult!=0) return activeHighDrainResult;

  // If the observed pulse disappears before the normal sample, the ingress
  // cannot be assigned to a durable pending event and must latch a fault.
  resetState(); injectDrainAbortWithoutIsr=true;
  injectDrainAbortPulseEndsBeforeSample=true; loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || insertMode || !activeTarget.empty() ||
     pollIntakeSuspended || pollDrainAbortedOnActiveLine || pendingPulses!=0U ||
     saveCalls!=0 || backupWriteSawRelayOn || backupWriteSawLedOn ||
     markerOpenSawRelayOn || markerOpenSawLedOn) return 40;
  const std::string missedSampleMarker=LittleFS.files["/pollpulse.fault"];
  if(missedSampleMarker.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     missedSampleMarker.find("pulses=1")==std::string::npos) return 41;
  std::cout<<"POLL_ABORT_PULSE_ENDED_BEFORE_SAMPLE_FAIL_CLOSED_PASS\\n";

  // A prior persistent journal fault must dominate stale positive controller
  // state when the temporary active-line drain hold is cleared.
  resetState();
  journalRecoveryRequired=true;
  pollIntakeSuspended=true;
  pollDrainAbortedOnActiveLine=true;
  insertMode=true;
  activeTarget="stale-target";
  relayOn=true;
  ledOn=true;
  handlePollDrainAbortAfterSample();
  if(!journalRecoveryRequired || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine || !insertMode ||
     activeTarget!="stale-target" || relayOn || ledOn) return 47;
  std::cout<<"POLL_ABORT_PRIOR_JOURNAL_FAULT_REMAINS_DENY_PASS\\n";

  // Existing pulse-drain behavior remains intact for a pulse observed before poll.
  resetState(); pulseStart=2050; pulseEnd=2130; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 31;
  resetState(); runCoinActiveLow=false; configureRuntimePins(runCoinPin,runRelayPin,runLedPin);
  pulseStart=2200; pulseEnd=2280; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 32;
  resetState(); pulseStart=2250; pulseEnd=2330; loop();
  if(!recordedPulseState() || !releaseRecordedPulseAfterIdle()) return 33;

  // Existing pending/recovery/FS guards remain fail-closed.
  resetState(); pendingReady=true; pendingPulses=1; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 41;
  resetState(); journalRecoveryRequired=true; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 42;
  resetState(); fsReady=false; applyOutputs(); loop();
  if(pollCalls!=0 || relayOn || ledOn || pollIntakeSuspended) return 43;

  // An ISR edge already present before poll admission must abort before HTTP.
  resetState(); coinEdgeSequence=1U; loop();
  if(pollCalls!=0 || !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || pollIntakeSuspended || lastPoll!=2000U || fakeNow!=2002U) return 44;
  std::cout<<"POLL_UNOBSERVED_PRE_POLL_EDGE_ABORT_PASS\\n";

  // A coin pulse captured by the ISR while the synchronous coin POST blocks
  // must be persisted before a success disposition can clear the pending record.
  resetState(); allowCoinPost=true; pendingReady=true; pendingPulses=4U;
  pendingNonce="nonce-existing"; pendingTarget="target-01";
  insertMode=false; activeTarget=""; injectDuringCoinPost=true; loop();
  if(coinPostCalls!=1 || clearCalls!=0 || pendingPulses!=4U || !pendingReady ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn) return 45;
  std::cout<<"COIN_POST_BLOCKED_ISR_EDGE_RETAINED_PASS\\n";

  // With no intervening ISR edge, the existing authenticated success path may clear.
  resetState(); allowCoinPost=true; pendingReady=true; pendingPulses=4U;
  pendingNonce="nonce-existing"; pendingTarget="target-01";
  insertMode=false; activeTarget=""; loop();
  if(coinPostCalls!=1 || clearCalls!=1 || pendingPulses!=0U || pendingReady ||
     journalRecoveryRequired || LittleFS.exists("/pollpulse.fault")) return 46;
  std::cout<<"COIN_POST_NO_EDGE_CLEAR_CONTROL_PASS\\n";

  std::cout<<"POLL_BLOCKED_EDGE_FAULT_PASS 8/8 fault-marker scenarios; existing poll-loop guards 7/7\n";
  std::cout<<"SIMULATED_ONLY=1 PHYSICAL_COIN_ACCEPTOR_VERIFIED=0 PHYSICAL_POWER_CUT_VERIFIED=0\n";
  // Disabled controller/coin/relay configurations must quarantine sampled edges.
  int disabledIngressResult=runDisabledIngressCase(false,false,true,false,60,
      "POLL_EDGE_WHILE_RELAY_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressCase(false,false,true,true,61,
      "POLL_ISR_EDGE_WHILE_RELAY_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressCase(false,true,false,false,62,
      "POLL_EDGE_WHILE_COIN_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressCase(false,true,false,true,63,
      "POLL_ISR_EDGE_WHILE_COIN_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressCase(true,false,false,false,64,
      "POLL_EDGE_WHILE_CONTROLLER_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressCase(true,false,false,true,65,
      "POLL_ISR_EDGE_WHILE_CONTROLLER_DISABLED_DENY_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(false,false,true,false,66,
      "POLL_DISABLED_RELAY_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(false,false,true,true,67,
      "POLL_DISABLED_RELAY_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(false,true,false,false,68,
      "POLL_DISABLED_COIN_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(false,true,false,true,69,
      "POLL_DISABLED_COIN_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(true,false,false,false,70,
      "POLL_DISABLED_CONTROLLER_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  disabledIngressResult=runDisabledIngressPendingCase(true,false,false,true,71,
      "POLL_DISABLED_CONTROLLER_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(disabledIngressResult) return disabledIngressResult;
  std::cout<<"POLL_DISABLED_INGRESS_PENDING_IDENTITY_PRESERVATION_PASS 6/6"<<std::endl;
  return 0;
}

"""

__all__ = ["DEFAULT_MAIN"]
