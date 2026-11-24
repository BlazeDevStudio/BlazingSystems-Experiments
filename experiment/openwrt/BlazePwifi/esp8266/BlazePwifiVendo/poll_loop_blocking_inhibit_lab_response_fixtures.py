"""No-edge synchronous poll response-denial scenario.

Run the extracted production loop with no ISR event during HTTP. The relay
must remain off solely because the poll response is not authenticated/accepted.
"""
from poll_loop_blocking_inhibit_lab_scenario_fixtures import MAIN

POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN = MAIN[:MAIN.index("int main(){")] + r"""
int main(){
  resetState();
  if(!relayOn || !ledOn) return 89;
  loop();
  if(pollCalls!=1 || coinPostCalls!=0 || clearCalls!=0 ||
     pollStartAt==0U || pollEndAt-pollStartAt!=3500UL ||
     !pollStartCoinIdle || pollStartRelayOn || !pollStartSuspended ||
     pollEndRelayOn || !pollEndSuspended || !pollHttpReturned ||
     journalRecoveryRequired || LittleFS.exists("/pollpulse.fault") ||
     insertMode || !activeTarget.empty() || pollIntakeSuspended ||
     pollDrainAbortedOnActiveLine || relayOn || ledOn ||
     pendingPulses!=0U || pendingReady || pendingPostAttempted ||
     !pendingTarget.empty() || !pendingNonce.empty() ||
     coinEdgeSequence!=0U || lastHandledCoinEdgeSequence!=0U ||
     saveCalls!=0) return 90;
  std::cout<<"POLL_HTTP_RESPONSE_DENY_NO_EDGE_PASS"<<std::endl;
  return 0;
}
"""


# A keyless controller must remain deny-only even when an untrusted positive
# response includes a response_sig-looking field. This is not a protocol vector.
POLL_HTTP_KEYLESS_RESPONSE_DENY_MAIN = POLL_HTTP_RESPONSE_DENY_NO_EDGE_MAIN.replace(
    "int main(){\n  resetState();",
    "int main(){\n  resetState();\n  clearControllerKey();\n  if(!controllerKeyEmpty()) return 91;",
    1,
).replace(
    "POLL_HTTP_RESPONSE_DENY_NO_EDGE_PASS",
    "POLL_HTTP_KEYLESS_RESPONSE_DENY_PASS",
    1,
)
