"""Admission-deny and unsafe-pin configuration scenarios.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_GATES = r'''static bool runDeniedGates(){
  for(int scenario=0;scenario<10;++scenario){
    if(scenario==5 || scenario==6) continue; // explicit fault cases below
    resetState(141U);
    lastEdge=100U;
    bool active=true;
    switch(scenario){
      case 0:insertMode=false;break;
      case 1:fsReady=false;break;
      case 2:journalRecoveryRequired=true;break;
      case 3:pendingReady=true;active=false;break; // idle after finalization remains a no-op
      case 4:activeTarget.clear();break;
      case 7:lastCoin=true;break;
      case 8:active=false;break;
      case 9:fakeNow=140U;break; // exactly the configured debounce boundary
    }
    sampleCoinPulseEdge(active);
    if(saveCalls!=0 || pendingPulses!=0){
      std::cerr<<"FAIL deny-case-"<<scenario<<" saves="<<saveCalls
               <<" pulses="<<(unsigned)pendingPulses<<"\n";
      return false;
    }
  }
  return true;
}
static bool runInvalidPinConfig(){
  // An unsafe GPIO map must never turn a sampled fallback-pin edge into a coin event.
  resetState(1000U);
  pinConfigSafe=false;
  sampleCoinPulseEdge(true);
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn){
    std::cerr<<"UNSAFE_PIN_DEBUG journal="<<journalRecoveryRequired
             <<" insert="<<insertMode<<" target="<<activeTarget
             <<" relay="<<relayOn<<" led="<<ledOn
             <<" pin="<<pinConfigSafe<<" now="<<millis()
             <<" last="<<lastEdge<<" debounce="<<runDebounceMs<<"\\n";
    return fail("unsafe-pin-sample","unsafe pin mapping did not latch unresolved ingress");
  }
  if(pendingPulses!=0 || saveCalls!=0 || nonceCalls!=0)
    return fail("unsafe-pin-sample","unsafe pin mapping was assigned to a coin batch");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=1U || markerEdges!=1U)
    return fail("unsafe-pin-sample","unsafe pin mapping did not persist one unresolved edge");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail("unsafe-pin-sample","fault persistence began before outputs were OFF");

  // Even an older pending batch must not be dispatched while the pin map is unsafe.
  resetState();
  pinConfigSafe=false;
  pendingReady=true;
  pendingPulses=1U;
  if(canAttemptCoinPost())
    return fail("unsafe-pin-post-gate","coin POST remained eligible with an unsafe pin mapping");
  return true;
}

'''
