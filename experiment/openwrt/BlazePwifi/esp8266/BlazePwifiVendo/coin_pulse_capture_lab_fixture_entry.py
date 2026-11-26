"""Top-level scenario ordering and host fixture entry point.

The C++ bytes are kept as a literal section so concatenation remains deterministic.
"""
CPP_ENTRY = r'''int main(){
  int passed=0;
  if(!runDrainCapture("delayed-100ms-active-low",0U,100U,130U,0U,40U,true)) return 1;
  ++passed;
  if(!runDrainCapture("delayed-100ms-active-high",0U,100U,200U,0U,40U,false)) return 2;
  ++passed;
  if(!runDrainCapture("exact-250ms-boundary",0U,250U,330U,0U,40U,true)) return 3;
  ++passed;
  if(!runDrainCapture("configured-300ms-debounce",1000U,1280U,1360U,600U,300U,true)) return 4;
  ++passed;
  if(!runDrainCapture("millis-rollover",0xFFFFFFF0UL,0x20UL,0x50UL,
                      0xFFFFFFC0UL,40U,true)) return 5;
  ++passed;
  if(!runNoPulseControl()) return 6;
  ++passed;
  if(!runSaveFailure()) return 7;
  ++passed;
  if(!runDeniedGates()) return 8;
  ++passed;
  if(!runInvalidPinConfig()) return 17;
  ++passed;
  if(!runPulseLimitBoundary()) return 9;
  ++passed;
  if(!runUnrepresentablePulseCases()) return 10;
  ++passed;
  if(!runLatePulseAfterReady()) return 11;
  ++passed;
  if(!runMissedPulseAfterBlockingPost()) return 12;
  ++passed;
  if(!runMissedPulseDuringBlockingWork()) return 13;
  ++passed;
  if(!runMultipleUnobservedEdges()) return 14;
  ++passed;
  if(!runSingleObservedEdge()) return 15;
  ++passed;
  if(!runIngressTransitionCases()) return 16;
  ++passed;
  if(!runIsrSequenceWraparound()) return 18;
  ++passed;
  std::cout<<"COIN_PULSE_CAPTURE_PASS "<<passed<<"/18 top-level scenarios\n";
  return 0;
}'''
