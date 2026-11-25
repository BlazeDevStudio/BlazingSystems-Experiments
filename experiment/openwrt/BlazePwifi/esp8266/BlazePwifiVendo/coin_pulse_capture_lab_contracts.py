"""Production helper anchors and fail-open mutation matrix for coin pulse capture.

This module owns the declarative contract surface; the runner owns execution.
"""
FUNCTION_SPECS = (
    ("coinLineIdle", "bool coinLineIdle(){"),
    ("canStartPoll", "bool canStartPoll(){"),
    ("canAttemptCoinPost", "bool canAttemptCoinPost(){"),
    ("coinIngressConfigurationAllows", "bool coinIngressConfigurationAllows(){"),
    ("applyOutputs", "void applyOutputs(){"),
    ("coinLineQuietAfterInhibit", "bool coinLineQuietAfterInhibit(){"),
    ("beginPollWindow", "bool beginPollWindow(){"),
    ("latchPollPulseFault", "void latchPollPulseFault(uint32_t pulseEdges){"),
    ("quarantineCoinIngressTransition", "bool quarantineCoinIngressTransition(){"),
    ("sampleCoinPulseEdge", "void sampleCoinPulseEdge(bool active){"),
    ("handlePollDrainAbortAfterSample", "void handlePollDrainAbortAfterSample(){"),
)

FUNCTION_INDEX_BY_NAME = {
    name: index for index, (name, _) in enumerate(FUNCTION_SPECS)
}
if len(FUNCTION_INDEX_BY_NAME) != len(FUNCTION_SPECS):
    raise RuntimeError("coin pulse helper spec contains duplicate names")
if len({signature for _, signature in FUNCTION_SPECS}) != len(FUNCTION_SPECS):
    raise RuntimeError("coin pulse helper spec contains duplicate signatures")

MUTATIONS = (
    ("missing-edge-latch", "sampleCoinPulseEdge",
     "  lastHandledCoinEdgeSequence=observedEdgeSequence;" + "\n" + "  lastCoin=active;" + "\n" + "}",
     "  lastHandledCoinEdgeSequence=observedEdgeSequence;" + "\n" + "}", "sustained high level"),
    ("inclusive-debounce", "sampleCoinPulseEdge",
     "if(fsReady && !journalRecoveryRequired && active && !lastCoin &&\n     millis()-lastEdge>runDebounceMs){",
     "if(fsReady && !journalRecoveryRequired && active && !lastCoin &&\n     millis()-lastEdge>=runDebounceMs){", "deny-case-9"),
    ("missing-pulse-overflow-guard", "sampleCoinPulseEdge",
     "pendingPulses>=20", "pendingPulses>20", "pulse-overflow-21"),
    ("missing-target-drift-guard", "sampleCoinPulseEdge",
     "pendingTarget!=activeTarget", "false", "pending-target-changed"),
    ("missing-pending-ready-late-edge-latch", "sampleCoinPulseEdge",
     "if(pendingReady){", "if(false){", "late edge after finalization did not latch unresolved batch"),
    ("missing-overflow-fault-latch", "sampleCoinPulseEdge",
     "if(pendingTarget!=activeTarget || pendingPulses>=20){\n        latchPollPulseFault((uint32_t)pendingPulses+1U);",
     "if(pendingTarget!=activeTarget || pendingPulses>=20){\n        // overflow fault latch removed",
     "overflow/target drift did not latch deny"),
    ("ignored-save-failure", "sampleCoinPulseEdge",
     "fsReady=false;\n          pendingReady=true;", "",
     "failed durable write did not disable filesystem/intake"),
    ("missing-persistent-fault-latch", "sampleCoinPulseEdge",
     "latchPollPulseFault(pendingPulses);", "",
     "fault latch did not attempt both stores"),
    ("missing-latch-output-inhibit", "latchPollPulseFault",
     "  applyOutputs();\n  const bool backupPersisted",
     "  const bool backupPersisted",
     "storage attempt occurred before outputs were logically OFF"),
             ("missing-ingress-transition-quarantine", "quarantineCoinIngressTransition",
      "if(lineIdle && unhandledEdges==0U) return true;", "if(true) return true;",
      "active line at pin-configuration completion was accepted"),
     ("missing-transition-edge-ack", "quarantineCoinIngressTransition",
      "  if(pendingPulses>0U) pendingReady=true;\n  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
      "  if(pendingPulses>0U) pendingReady=true;\n  lastCoin=!lineIdle;",
      "edge multiplicity or handled baseline was not preserved"),
     ("missing-pending-event-ready", "quarantineCoinIngressTransition",
      "  if(pendingPulses>0U) pendingReady=true;\n  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
      "  lastHandledCoinEdgeSequence=observedEdgeSequence;\n  lastCoin=!lineIdle;",
      "existing pending identity was not preserved and denied"),
     # Keep sampledSingleEdge referenced so -Werror tests the runtime deny path, not an unused-variable compile error.
    ("missing-isr-edge-reconciliation", "sampleCoinPulseEdge",
     "if(unseenEdges>0U && !sampledSingleEdge){", "if(false && !sampledSingleEdge){",
     "late coin POST pulse was not fail-closed"),
    ("multiple-isr-edges-accepted-as-one", "sampleCoinPulseEdge",
     "unseenEdges==1U", "unseenEdges<=3U",
     "multiple ISR edges were not quarantined"),
    ("missing-unsafe-pin-sample-deny", "sampleCoinPulseEdge",
     "if(!pinConfigSafe){\n      latchPollPulseFault((uint32_t)pendingPulses+1U);",
     "if(false){\n      latchPollPulseFault((uint32_t)pendingPulses+1U);",
     "unsafe pin mapping did not latch unresolved ingress"),
    ("missing-unsafe-pin-post-gate", "canAttemptCoinPost",
     "outputPolarityKnown && pinConfigSafe && fsReady",
     "outputPolarityKnown && fsReady",
     "coin POST remained eligible with an unsafe pin mapping"),
    ("missing-isr-sequence-increment", "coinEdgeISR",
     "coinEdgeSequence++;", "coinEdgeSequence=coinEdgeSequence;",
     "isr-sequence-did-not-wrap"),
)
