# PHX-HARDWARE — C/C++ phase-2 preprocessor line-splice guard

**Date:** 2026-11-22 UTC09  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** #327 OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hardware-prepoll-edge-abort-20261119  
**Base:** #326 at 58c558fb6a237935214621adc3dee65a10fe1a51

## Scope and defect

The dual-store host fixture extracts selected static constants from the ESP32/ESP8266 sketches. Its literal preprocessor evaluator previously split physical lines before recognizing directives. C/C++ translation phase 2 removes backslash-newline pairs before preprocessing-token recognition, so the old parser missed:

- a continued literal-zero expression: #if followed by a backslash-newline and then 0;
- a directive keyword formed across a splice: #el followed by a backslash-newline and then if 0.

An inactive constant could therefore be included in the generated host harness. This was a Hardware-owned verification-infrastructure defect; it was not a demonstrated runtime firmware defect.

## Changes

Files changed:

- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab_fixtures.py

The fixture module now has _logical_preprocessor_lines(), which recognizes LF, CRLF and CR backslash-newline splices while retaining each logical line's original physical source range. _mask_inactive_preprocessor_branches() parses the logical line but blanks inactive physical ranges without changing source offsets or newline positions.

The evaluator remains intentionally conservative: literal #if/#elif 0/1 is handled; unknown macro conditions remain visible. This is not a full C/C++ preprocessor and does not claim arbitrary macro evaluation.

The runner adds:
- LF continued #if 0 expression regression;
- CRLF spliced #elif 0 keyword regression.

No production .ino, GPIO, relay, poll/coin API, financial code, signer/witness, QA-owned source or Release workflow changed.

## Test-first evidence

- Initial test authoring commit fd9be74333398e94ca51e7d5941423d65e9c60f5 contained an incorrectly escaped fixture and failed with got=[]; this was a test construction error, not accepted RED evidence.
- Corrected test-only commit fdd80841ced327b02c6524592a6a914023464671.
- Meaningful RED: [Quarantine #45006451995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006451995), job 137159024048, exact test-only SHA fdd80841... The old parser selected both the inactive decoy and active declaration, so the assertion failed as intended.
- Source fix / exact source-test SHA: 4019851a62262c43bc8d958124ee3803fd61eac4.

## Exact-SHA CI

- [Quarantine push #45006585734](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006585734), job 137159437317: SUCCESS.
- [Quarantine PR #45006590545](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006590545), job 137159452308: SUCCESS.
- The PR log includes:
  - POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_IF_SPLICE_REJECTED 1/1
  - POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_ELIF_SPLICE_REJECTED 1/1
  - SIMULATED_ONLY=1
  - PHYSICAL_POWER_CUT_ACCEPTANCE=0
- [Relay Output Polarity PR #45006590534](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006590534), jobs 137159452337 and 137159452675: SUCCESS.

## Full integration disposition

[Full push #45006585689](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006585689) on the same exact source/test SHA failed at validation job 137159504894:

Missing poll signature check in experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino.

All 14 target/platform jobs completed successfully, but validation failed and downstream simulations, candidate, signing and publication jobs were skipped. Full PR run [#45006590525](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45006590525) was still in progress at the last readback. No Full integration acceptance is claimed.

The poll signature blocker remains a shared CORE/QA contract issue. Hardware must not invent response_sig, add positive coin admission or weaken default-deny.

## Evidence classification

- Phase-2 line-splice extractor regression: CI VERIFIED.
- Existing dual-store/poll/pulse host labs: SIMULATED + CI VERIFIED.
- Target/platform builds: CI VERIFIED on this SHA; not release acceptance.
- Physical EEPROM/flash durability: NOT TESTED.
- Physical coin selector and relay/electrical recovery: NOT TESTED.
- 150 real power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO-GO.

## BLAZE-COMMS/1

UTC09 role lock / progress checkpoint: issue #172 comment 7077064849.

Next exact action: CORE publishes the canonical authenticated register/poll and event-bound receipt contract; QA independently reconciles the inherited positive poll-signature assertion; Hardware then revalidates all current PR heads and reruns Full on the approved contract. Preserve fail-closed behavior until that occurs.

No merge, rebase, force-push, flash, device reset, signer provisioning, live financial operation, production migration, release tag or deployment was performed.