"""Poll-drain, no-pulse and dual-store save-failure scenarios.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_POLL = r'''static bool runDrainCapture(const char*name,uint32_t startAt,uint32_t pulseAt,
                            uint32_t pulseUntil,uint32_t priorEdge,
                            uint16_t debounce,bool activeLow){
  resetState(startAt,activeLow);
  runDebounceMs=debounce;lastEdge=priorEdge;
  pulseEnabled=true;pulseStart=pulseAt;pulseEnd=pulseUntil;
  if(beginPollWindow()) return fail(name,"poll unexpectedly started");
  if(!pollIntakeSuspended || !pollDrainAbortedOnActiveLine || relayOn || ledOn)
    return fail(name,"drain abort did not retain inhibit for active line");
  const int raw=digitalRead(runCoinPin);
  const bool active=runCoinActiveLow?(raw==LOW):(raw==HIGH);
  if(!active) return fail(name,"drain abort did not leave an active pulse sample");
  sampleCoinPulseEdge(active);
  handlePollDrainAbortAfterSample();
  if(pendingPulses!=1 || saveCalls!=1 || nonceCalls!=1 ||
     pendingNonce!="nonce-1" || pendingTarget!=activeTarget || lastEdge!=fakeNow ||
     !pollIntakeSuspended || !pollDrainAbortedOnActiveLine || relayOn || ledOn)
    return fail(name,"first post-abort sample was not durably queued under inhibit");
  sampleCoinPulseEdge(active);
  fakeNow+=static_cast<uint32_t>(runDebounceMs)+1U;
  sampleCoinPulseEdge(active);
  if(pendingPulses!=1 || saveCalls!=1)
    return fail(name,"sustained high level was counted as another pulse");
  pulseEnabled=false;
  sampleCoinPulseEdge(false);
  handlePollDrainAbortAfterSample();
  if(pollIntakeSuspended || pollDrainAbortedOnActiveLine || !relayOn || !ledOn)
    return fail(name,"drain abort inhibit did not release after line became idle");
  fakeNow+=static_cast<uint32_t>(runDebounceMs)+1U;
  sampleCoinPulseEdge(true);
  if(pendingPulses!=2 || saveCalls!=2 || nonceCalls!=1 ||
     pendingNonce!="nonce-1" || pendingTarget!=activeTarget)
    return fail(name,"released second edge did not reuse the pending event identity");
  return true;
}
static bool runNoPulseControl(){
  resetState();
  if(!beginPollWindow()) return fail("no-pulse-control","quiet poll window was rejected");
  if(!pollIntakeSuspended || relayOn || ledOn || fakeNow!=250U)
    return fail("no-pulse-control","poll admission did not retain output inhibit");
  return true;
}
static bool runSaveFailureCase(const char*name,bool backupOk,bool markerOk){
  resetState(100U);
  saveResult=false;
  backupResult=backupOk;
  markerResult=markerOk;
  sampleCoinPulseEdge(true);
  if(pendingPulses!=1 || saveCalls!=1 || fsReady || !pendingReady)
    return fail(name,"failed durable write did not disable filesystem/intake");
  if(backupCalls!=1 || markerCalls!=1 || backupEdges!=1 || markerEdges!=1)
    return fail(name,"fault latch did not attempt both stores with the unresolved pulse count");
  if(!backupSawFsReady || !markerSawFsReady)
    return fail(name,"fault latch attempted persistence after LittleFS was marked unavailable");
  if(!backupSawRelayOff || !backupSawLedOff || !markerSawRelayOff || !markerSawLedOff)
    return fail(name,"storage attempt occurred before outputs were logically OFF");
  if(!journalRecoveryRequired || insertMode || !activeTarget.empty() || relayOn || ledOn)
    return fail(name,"failed journal write did not retain the deny latch and output inhibit");
  if(!backupOk && !markerOk &&
     (Serial.messages.find("both poll-pulse fault stores failed")==std::string::npos ||
      Serial.messages.find("reboot durability is NOT established")==std::string::npos))
    return fail(name,"dual-store failure was not classified as current-boot-only");
  sampleCoinPulseEdge(false);
  fakeNow=200U;
  sampleCoinPulseEdge(true);
  if(saveCalls!=1 || pendingPulses!=1 || backupCalls!=1 || markerCalls!=1)
    return fail(name,"another pulse or persistence retry was accepted after failed journal write");
  return true;
}
static bool runSaveFailure(){
  if(!runSaveFailureCase("both-stores-pass",true,true)) return false;
  if(!runSaveFailureCase("nvs-only",true,false)) return false;
  if(!runSaveFailureCase("littlefs-only",false,true)) return false;
  if(!runSaveFailureCase("both-stores-fail-current-boot-only",false,false)) return false;
  return true;
}
'''
