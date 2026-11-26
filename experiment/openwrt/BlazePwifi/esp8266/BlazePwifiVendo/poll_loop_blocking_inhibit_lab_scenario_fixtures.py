"""Shared C++ setup for the blocking-poll regression lab.

The default executable scenario is kept in a separate fixture module so the
shared prelude and its test program can be reviewed independently.
"""

from poll_loop_blocking_inhibit_lab_default_main_fixtures import DEFAULT_MAIN

MAIN = r"""
void resetState(){
  fakeNow=2000; pulseStart=-1; pulseEnd=-1;
  coinEdgeSequence=0; lastHandledCoinEdgeSequence=0; interruptAttached=false; attachedPin=-1; attachedMode=-1; attachedIsr=nullptr;
  fakeShortWrite=false; fakeCorruptReadback=false; fakeOpenFail=false; LittleFS.files.clear();
  relayOn=false; ledOn=false; backupWriteSawRelayOn=false; backupWriteSawLedOn=false;
  backupFirstFaultPulseEdges=0; backupWriteAttempts=0;
  markerOpenSawRelayOn=false; markerOpenSawLedOn=false; relayLevelHigh=false; ledLevelHigh=false;
  injectDuringHttp=false; injectDuringHttpEdgeCount=1; injectTimedPollPulse=false; timedPulseIsrInjected=false;
  injectAfterDrainEdge=false; injectAfterDrainEdgeCount=1; injectDuringDrainAbort=false;
  injectDrainAbortWithoutIsr=false; injectDrainAbortPulseEndsBeforeSample=false;
  injectDuringPollRelease=false; injectDuringPollReleaseAtRelayWrite=false;
  pollReleaseEdgeInjected=false; pollReleaseEdgeSawRelayOff=false;
  pollReleaseRelayEnergizedBeforeLatch=false; pollReleaseRelayClearedBeforeLatch=false;
  allowCoinPost=false; injectDuringCoinPost=false; injectDuringClear=false; coinPostCalls=0; clearCalls=0; injectDuringCoinPostEdgeCount=1;
  drainAbortReadCount=0; drainAbortInjected=false; drainAbortSawRelayOn=false;
  drainAbortSampleSawRelayOn=false; drainAbortReenabledBeforeLatch=false;
  drainAbortActiveLineReenabled=false;
  pollCalls=0; saveCalls=0;
  pollStartAt=0; pollEndAt=0; pollStartRelayOn=true; pollStartSuspended=false;
  pollStartCoinIdle=false; pollEndRelayOn=true; pollEndSuspended=false;
  pollPulseObservedDuringHttp=false; pollPulseRelayOff=false; pollPulseSuspended=false;
  pollHttpReturned=false; pollPostHttpSampleObserved=false;
  pollPostHttpFaultLatchedBeforeSample=false;
  pollPostHttpMarkerPresentBeforeSample=false;
  pollPostHttpOutputsOffBeforeSample=false;
  insertMode=true; lastCoin=false; pollIntakeSuspended=false; pollDrainAbortedOnActiveLine=false; pinConfigSafe=true; outputPolarityKnown=true;
  controllerEnabled=true; coinEnabled=true; relayEnabled=true; ledEnabled=true;
  setupApOn=false; runCoinActiveLow=true; runRelayActiveHigh=true; runLedActiveHigh=true;
  pendingReady=false; fsReady=true; journalRecoveryRequired=false; pendingPostAttempted=false;
  lastPoll=0; lastEdge=0; lastSend=0; configuredApSince=0;
  pendingPulses=0; runCoinPin=4; runLedPin=2; runRelayPin=26;
  maxWifiRetries=6; wifiFailures=0; runDebounceMs=40; runPulseGroupMs=400;
  activeTarget="target-01"; pendingTarget=""; pendingNonce="";
  configureRuntimePins(runCoinPin,runRelayPin,runLedPin,runCoinActiveLow);
  applyOutputs();
}
bool recordedPulseState(){
  return pollCalls==0 && pendingPulses==1 && !pendingReady &&
         pendingTarget=="target-01" && pendingNonce=="nonce12345678" &&
         lastCoin && !relayOn && !ledOn && pollIntakeSuspended &&
         pollDrainAbortedOnActiveLine && saveCalls==1;
}
bool releaseRecordedPulseAfterIdle(){
  fakeNow=(uint32_t)pulseEnd;
  loop();
  return !pollIntakeSuspended && !pollDrainAbortedOnActiveLine &&
         relayOn && ledOn && pendingPulses==1U && !journalRecoveryRequired;
}
int runDrainAbortWithoutIsr(bool activeLow, int holdFailureCode, int releaseFailureCode,
                            const char *heldMarker, const char *releasedMarker){
  resetState();
  if(!activeLow){
    runCoinActiveLow=false;
    configureRuntimePins(runCoinPin,runRelayPin,runLedPin,runCoinActiveLow);
  }
  injectDrainAbortWithoutIsr=true;
  loop();
  if(!drainAbortInjected || drainAbortActiveLineReenabled || pollCalls!=0 ||
     !pollIntakeSuspended || !pollDrainAbortedOnActiveLine ||
     relayOn || ledOn || journalRecoveryRequired || pendingPulses!=1U ||
     pendingReady || pendingTarget!="target-01" || pendingNonce!="nonce12345678" ||
     saveCalls!=1 || !lastCoin) return holdFailureCode;
  std::cout<<heldMarker<<"\\n";
  fakeNow=(uint32_t)pulseEnd;
  loop();
  if(pollIntakeSuspended || pollDrainAbortedOnActiveLine || !relayOn || !ledOn ||
     pendingPulses!=1U || saveCalls!=1 || journalRecoveryRequired) return releaseFailureCode;
  std::cout<<releasedMarker<<"\\n";
  return 0;
}
int runDisabledIngressCase(bool disableController, bool disableCoin, bool disableRelay,
                           bool injectIsrEdge, int failureCode, const char *passMarker){
  resetState();
  if(disableController) controllerEnabled=false;
  if(disableCoin) coinEnabled=false;
  if(disableRelay) relayEnabled=false;
  applyOutputs();
  if(relayOn || ledOn){
    std::cout<<"POLL_DISABLED_INGRESS_OUTPUTS_OFF_FAIL\\n";
    return failureCode+20;
  }
  if(injectIsrEdge) coinEdgeSequence=1U;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || pendingPulses!=0U || saveCalls!=0 ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty()) return failureCode;
  const std::string fault=LittleFS.files["/pollpulse.fault"];
  if(fault.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     fault.find("pulses=1")==std::string::npos) return failureCode;
  std::cout<<passMarker<<"\\n";
  return 0;
}

const std::string PENDING_JOURNAL_FIXTURE_BYTES =
    "PHX-PENDING-JOURNAL-OPAQUE-v1|pulses=2|target=pending-target|nonce=pending-nonce";

std::string seedPendingJournalFixture() {
  LittleFS.files["/pending.dat"] = PENDING_JOURNAL_FIXTURE_BYTES;
  return PENDING_JOURNAL_FIXTURE_BYTES;
}

bool pendingJournalFixturePreserved(const std::string &expectedBytes) {
  const auto found = LittleFS.files.find("/pending.dat");
  return found != LittleFS.files.end() && found->second == expectedBytes;
}

const std::map<std::string,std::string> PENDING_EVIDENCE_FIXTURE_FILES = {
  {"/pending.dat","PHX-PENDING-DAT-OPAQUE-v1|pulses=2|target=pending-target|nonce=pending-nonce"},
  {"/pending.new","PHX-PENDING-NEW-OPAQUE-v1|candidate=uncommitted"},
  {"/pending.bak","PHX-PENDING-BAK-OPAQUE-v1|candidate=previous"},
  {"/pending.attempt","PHX-PENDING-ATTEMPT-OPAQUE-v1|attempted=1|target=pending-target|nonce=pending-nonce"}
};

std::map<std::string,std::string> seedPendingEvidenceFixture() {
  for (const auto &entry : PENDING_EVIDENCE_FIXTURE_FILES) {
    LittleFS.files[entry.first] = entry.second;
  }
  return PENDING_EVIDENCE_FIXTURE_FILES;
}

bool pendingEvidenceFixturePreserved(
    const std::map<std::string,std::string> &expectedFiles) {
  for (const auto &expected : expectedFiles) {
    const auto found = LittleFS.files.find(expected.first);
    if (found == LittleFS.files.end() || found->second != expected.second) return false;
  }
  return true;
}

int runDisabledIngressPendingCase(bool disableController, bool disableCoin, bool disableRelay,
                                  bool injectIsrEdge, int failureCode, const char *passMarker){
  resetState();
  // Model the existing RAM identity plus opaque pending-journal bytes. This
  // loop lab checks byte preservation; it does not parse the on-disk record format.
  const std::string pendingJournalBytes=seedPendingJournalFixture();
  pendingPulses=2U;
  pendingReady=false;
  pendingTarget="pending-target";
  pendingNonce="pending-nonce";
  pendingPostAttempted=false;
  if(disableController) controllerEnabled=false;
  if(disableCoin) coinEnabled=false;
  if(disableRelay) relayEnabled=false;
  applyOutputs();
  // Check the configured output interlock before the fault handler can mask a bad initial state.
  if(relayOn || ledOn) return failureCode+14; // reserved exit range for configured-output interlock mutation
  if(injectIsrEdge) coinEdgeSequence=1U;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || pendingPulses!=2U || !pendingReady ||
     pendingTarget!="pending-target" || pendingNonce!="pending-nonce" ||
     pendingPostAttempted || saveCalls!=0 ||
     !pendingJournalFixturePreserved(pendingJournalBytes) ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty()) return failureCode;
  const std::string fault=LittleFS.files["/pollpulse.fault"];
  if(fault.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     fault.find("pulses=3")==std::string::npos) return failureCode;
  std::cout<<passMarker<<std::endl;
  return 0;
}


int runDisabledIngressPendingMultiEdgeCase(bool disableController, bool disableCoin, bool disableRelay,
                                           uint32_t initialSequence, uint32_t edgeDelta,
                                           uint32_t expectedFaultPulses, int failureCode,
                                           const char *passMarker){
  resetState();
  // RAM identity and opaque pending-journal bytes must survive a multi-edge
  // delta, including uint32 rollover; the journal's serialized format is not parsed here.
  const std::string pendingJournalBytes=seedPendingJournalFixture();
  pendingPulses=2U;
  pendingReady=false;
  pendingTarget="pending-target";
  pendingNonce="pending-nonce";
  pendingPostAttempted=false;
  if(disableController) controllerEnabled=false;
  if(disableCoin) coinEnabled=false;
  if(disableRelay) relayEnabled=false;
  applyOutputs();
  // Check the configured output interlock before sampling or fault handling.
  if(relayOn || ledOn) return failureCode+14; // reserved exit range for configured-output interlock mutation
  lastHandledCoinEdgeSequence=initialSequence;
  coinEdgeSequence=initialSequence+edgeDelta;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || pendingPulses!=2U || !pendingReady ||
     pendingTarget!="pending-target" || pendingNonce!="pending-nonce" ||
     pendingPostAttempted || saveCalls!=0 ||
     !pendingJournalFixturePreserved(pendingJournalBytes) ||
     lastHandledCoinEdgeSequence!=coinEdgeSequence || !lastCoin ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty()) return failureCode;
  const std::string fault=LittleFS.files["/pollpulse.fault"];
  if(fault.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     fault.find("pulses="+std::to_string(expectedFaultPulses))==std::string::npos)
    return failureCode;
  std::cout<<passMarker<<std::endl;
  return 0;
}


int runAttemptedPendingEvidenceCase(bool disableController, bool disableCoin, bool disableRelay,
                                    bool injectIsrEdge, int failureCode, const char *passMarker){
  resetState();
  // Deliberately model opaque recovery evidence for an already-attempted event,
  // including alternate journal candidates. This checks preservation only; it
  // does not parse or bless any PendingRecord serialization or recovery choice.
  const auto pendingEvidenceFiles=seedPendingEvidenceFixture();
  pendingPulses=2U;
  pendingReady=true;
  pendingTarget="pending-target";
  pendingNonce="pending-nonce";
  pendingPostAttempted=true;
  if(disableController) controllerEnabled=false;
  if(disableCoin) coinEnabled=false;
  if(disableRelay) relayEnabled=false;
  applyOutputs();
  if(relayOn || ledOn) return failureCode+14;
  if(injectIsrEdge) coinEdgeSequence=1U;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || pendingPulses!=2U || !pendingReady ||
     !pendingPostAttempted || pendingTarget!="pending-target" ||
     pendingNonce!="pending-nonce" || saveCalls!=0 ||
     !pendingEvidenceFixturePreserved(pendingEvidenceFiles) ||
     !LittleFS.exists("/pollpulse.fault") || relayOn || ledOn ||
     insertMode || !activeTarget.empty()) return failureCode;
  const std::string fault=LittleFS.files["/pollpulse.fault"];
  if(fault.find("COIN_INGRESS_UNRESOLVED")==std::string::npos ||
     fault.find("pulses=3")==std::string::npos) return failureCode;
  std::cout<<passMarker<<std::endl;
  return 0;
}

""" + DEFAULT_MAIN

__all__ = ["MAIN"]
