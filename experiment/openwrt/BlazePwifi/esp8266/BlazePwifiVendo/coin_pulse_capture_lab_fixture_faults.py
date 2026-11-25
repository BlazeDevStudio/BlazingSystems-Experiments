"""Pulse limit, target-drift and post-finalization fault scenarios.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_FAULTS = r'''static bool runPulseLimitBoundary(){
  resetState(141U);
  lastEdge=100U;
  pendingPulses=19U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  sampleCoinPulseEdge(true);
  if(pendingPulses!=20U || saveCalls!=1 || nonceCalls!=0 ||
     pendingNonce!="nonce-existing" || pendingTarget!="target-01")
    return fail("pulse-limit-20","supported twentieth pulse was not durably queued with its existing identity");
  if(journalRecoveryRequired || pendingReady || !relayOn || !ledOn ||
     backupCalls!=0 || markerCalls!=0)
    return fail("pulse-limit-20","valid twentieth pulse was incorrectly faulted or inhibited");
  return true;
}
static bool runUnrepresentablePulseFault(const char*name,uint8_t existing,
                                         const String&storedTarget){
  resetState(141U);
  lastEdge=100U;
  pendingPulses=existing;
  pendingNonce="nonce-existing";
  pendingTarget=storedTarget;
  sampleCoinPulseEdge(true);
  const uint32_t unresolvedEdges=(uint32_t)existing+1U;
  if(saveCalls!=0 || pendingPulses!=existing ||
     pendingNonce!="nonce-existing" || pendingTarget!=storedTarget || nonceCalls!=0)
    return fail(name,"unrepresentable pulse mutated or appended to the existing pending identity");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail(name,"overflow/target drift did not latch deny and force outputs OFF");
  if(backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=unresolvedEdges || markerEdges!=unresolvedEdges)
    return fail(name,"fault latch did not persist the complete unresolved edge count");
  if(!backupSawRelayOff || !backupSawLedOff ||
     !markerSawRelayOff || !markerSawLedOff)
    return fail(name,"fault persistence began before output inhibition");
  sampleCoinPulseEdge(false);
  fakeNow=200U;
  sampleCoinPulseEdge(true);
  if(saveCalls!=0 || pendingPulses!=existing ||
     backupCalls!=1 || markerCalls!=1)
    return fail(name,"later pulse retried or mutated the unresolved batch");
  return true;
}
static bool runUnrepresentablePulseCases(){
  if(!runUnrepresentablePulseFault("pulse-overflow-21",20U,"target-01")) return false;
  if(!runUnrepresentablePulseFault("pending-target-changed",1U,"other-target")) return false;
  return true;
}
static bool runLatePulseAfterReady(){
  resetState(141U);
  lastEdge=100U;
  insertMode=false;
  activeTarget.clear();
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  applyOutputs();
  if(relayOn || ledOn)
    return fail("late-pulse-after-ready","pending-ready state did not keep outputs OFF");
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail("late-pulse-after-ready","late edge after finalization did not latch unresolved batch and keep outputs OFF");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" || pendingTarget!="target-01" ||
     saveCalls!=0 || nonceCalls!=0)
    return fail("late-pulse-after-ready","late edge mutated or replaced the already-finalized pending identity");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=5U || markerEdges!=5U)
    return fail("late-pulse-after-ready","late edge was not persisted as one additional unresolved pulse");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail("late-pulse-after-ready","fault persistence began before output inhibition");
  return true;
}
'''
