"""Pending-journal recovery scenarios for the blocking-poll host lab.

Keep recovery/clear-window entry points separate from general poll-loop
scenarios while reusing the exact shared production-source harness.
"""

from poll_loop_blocking_inhibit_lab_scenario_fixtures import MAIN

PENDING_PRESERVATION_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  int result=runDisabledIngressPendingCase(false,false,true,false,66,
      "POLL_DISABLED_RELAY_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingCase(false,false,true,true,67,
      "POLL_DISABLED_RELAY_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingCase(false,true,false,false,68,
      "POLL_DISABLED_COIN_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingCase(false,true,false,true,69,
      "POLL_DISABLED_COIN_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingCase(true,false,false,false,70,
      "POLL_DISABLED_CONTROLLER_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingCase(true,false,false,true,71,
      "POLL_DISABLED_CONTROLLER_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingMultiEdgeCase(false,false,true,0xFFFFFFFEUL,3U,5U,72,
      "POLL_DISABLED_RELAY_MULTI_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingMultiEdgeCase(false,true,false,100U,2U,4U,73,
      "POLL_DISABLED_COIN_MULTI_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  result=runDisabledIngressPendingMultiEdgeCase(true,false,false,200U,4U,6U,74,
      "POLL_DISABLED_CONTROLLER_MULTI_ISR_PENDING_IDENTITY_PRESERVED_PASS");
  if(result) return result;
  std::cout<<"POLL_DISABLED_INGRESS_PENDING_IDENTITY_PRESERVATION_PASS 9/9"<<std::endl;
  return 0;
}
"""


CLEAR_WINDOW_ISR_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  allowCoinPost=true;
  pendingReady=true;
  pendingPulses=4U;
  pendingNonce="nonce-existing";
  pendingTarget="target-01";
  insertMode=false;
  activeTarget="";
  // Test-only disposition override reaches the otherwise deny-only response
  // path. Inject the actual extracted ISR during the pending-clear window.
  injectDuringClear=true;
  loop();
  if(coinPostCalls!=1 || clearCalls!=1 ||
     !journalRecoveryRequired || !LittleFS.exists("/pollpulse.fault") ||
     relayOn || ledOn || pendingPulses!=0U || pendingReady ||
     coinEdgeSequence!=lastHandledCoinEdgeSequence ||
     LittleFS.files["/pollpulse.fault"].find("pulses=1")==std::string::npos) return 54;
  std::cout<<"COIN_POST_CLEAR_WINDOW_ISR_EDGE_LATCHED_PASS\n";
  return 0;
}
"""


__all__ = ["PENDING_PRESERVATION_MAIN", "CLEAR_WINDOW_ISR_MAIN"]
