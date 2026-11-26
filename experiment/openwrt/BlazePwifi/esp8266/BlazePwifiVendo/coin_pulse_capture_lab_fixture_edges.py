"""Blocking-window, ISR-edge and ingress-transition scenarios.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_EDGES = r'''static bool runMissedPulseAfterBlockingPost(){
  resetState(500U);
  lastEdge=400U;
  insertMode=false;
  activeTarget.clear();
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  relayOn=false;ledOn=false;
  emitCoinEdges(1U); // ISR fires while coin POST blocks; pulse ends before the next GPIO sample.
  sampleCoinPulseEdge(false);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !pendingReady || relayOn || ledOn)
    return fail("late-coin-post-edge","late coin POST pulse was not fail-closed");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" ||
     pendingTarget!="target-01" || saveCalls!=0 || nonceCalls!=0)
    return fail("late-coin-post-edge","finalized pending identity was mutated");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=5U || markerEdges!=5U)
    return fail("late-coin-post-edge","late edge was not persisted with the existing pending count");
  if(lastHandledCoinEdgeSequence!=1U)
    return fail("late-coin-post-edge","ISR sequence was not acknowledged after latching");
  return true;
}
static bool runMissedPulseDuringBlockingWork(){
  resetState(500U);
  lastEdge=400U;
  emitCoinEdges(1U); // Pulse starts and ends while a synchronous handler owns the loop.
  sampleCoinPulseEdge(false);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail("missed-blocking-pulse","missed blocking pulse was not fail-closed");
  if(pendingPulses!=0U || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=1U || markerEdges!=1U)
    return fail("missed-blocking-pulse","unobserved pulse was not durably marked as unresolved");
  return true;
}
static bool runMultipleUnobservedEdges(){
  resetState(500U);
  lastEdge=400U;
  emitCoinEdges(3U);
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail("multiple-unobserved-edges","multiple ISR edges were not quarantined");
  if(pendingPulses!=0U || saveCalls!=0 || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=3U || markerEdges!=3U)
    return fail("multiple-unobserved-edges","edge multiplicity was collapsed into a single pending pulse");
  return true;
}
static bool runSingleObservedEdge(){
  resetState(100U);
  emitCoinEdges(1U);
  sampleCoinPulseEdge(true);
  if(journalRecoveryRequired || pendingPulses!=1U || saveCalls!=1 ||
     lastHandledCoinEdgeSequence!=1U)
    return fail("single-observed-edge","one sampled ISR edge was not attributed exactly once");
  sampleCoinPulseEdge(true);
  if(journalRecoveryRequired || pendingPulses!=1U || saveCalls!=1)
    return fail("single-observed-edge","sustained active level duplicated an already handled ISR edge");
  return true;
}
static bool runIngressTransitionCases(){
  resetState();
  if(!quarantineCoinIngressTransition() || journalRecoveryRequired ||
     backupCalls!=0 || markerCalls!=0)
    return fail("boot-idle-control","idle line with no unhandled ISR edge was quarantined");

  resetState();
  journalRecoveryRequired=true;
  if(quarantineCoinIngressTransition() || !journalRecoveryRequired ||
     backupCalls!=0 || markerCalls!=0 || relayOn || ledOn)
    return fail("prior-journal-fault","an existing journal fault was reported as a safe ingress transition");

  resetState(50U);
  insertMode=false;
  activeTarget.clear();
  pulseEnabled=true;pulseStart=0U;pulseEnd=100U;
  if(quarantineCoinIngressTransition())
    return fail("boot-active-line","active line at pin-configuration completion was accepted");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() ||
     !lastCoin || relayOn || ledOn || backupCalls!=1 || markerCalls!=1 ||
     backupEdges!=1U || markerEdges!=1U)
    return fail("boot-active-line","active line was not persisted as unresolved with outputs OFF");

  resetState();
  emitCoinEdges(2U);
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-unhandled-edges","unhandled ISR edges after pin attachment were ignored");
  if(lastHandledCoinEdgeSequence!=2U || backupEdges!=2U || markerEdges!=2U)
    return fail("reconfigure-unhandled-edges","edge multiplicity or handled baseline was not preserved");

  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  emitCoinEdges(3U);
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-counter-wrap","wrapped ISR sequence was accepted as idle");
  if(lastHandledCoinEdgeSequence!=1U || backupEdges!=3U || markerEdges!=3U)
    return fail("reconfigure-counter-wrap","unsigned edge delta did not preserve three wrapped edges");

  resetState(50U);
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  activeTarget="target-01";
  pulseEnabled=true;pulseStart=0U;pulseEnd=100U;
  if(quarantineCoinIngressTransition())
    return fail("reconfigure-pending-event","active ingress with an existing pending batch was accepted");
  if(pendingPulses!=4U || pendingNonce!="nonce-existing" ||
     pendingTarget!="target-01" || !pendingReady || backupEdges!=5U ||
     markerEdges!=5U || relayOn || ledOn)
    return fail("reconfigure-pending-event","existing pending identity was not preserved and denied");
  return true;
}

static bool runIsrSequenceWraparound(){
  resetState();
  coinEdgeSequence=0xFFFFFFFEUL;
  lastHandledCoinEdgeSequence=0xFFFFFFFEUL;
  emitCoinEdges(1U);
  if(snapshotCoinEdgeSequence()!=0xFFFFFFFFUL)
    return fail("isr-sequence-did-not-wrap","first ISR edge did not advance to UINT32_MAX");
  emitCoinEdges(1U);
  if(snapshotCoinEdgeSequence()!=0U)
    return fail("isr-sequence-did-not-wrap","second ISR edge did not wrap to zero");
  if(quarantineCoinIngressTransition())
    return fail("isr-sequence-did-not-wrap","two wrapped unhandled ISR edges were accepted as idle");
  if(lastHandledCoinEdgeSequence!=0U || backupEdges!=2U || markerEdges!=2U)
    return fail("isr-sequence-did-not-wrap","wrapped ISR delta was not preserved in both fault stores");
  return true;
}

'''
