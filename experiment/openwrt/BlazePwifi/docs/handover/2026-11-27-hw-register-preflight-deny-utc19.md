# PHX-HARDWARE UTC19 — startup register fail-closed guard coverage

**Role:** PHX-HARDWARE  
**Task:** hardware #177 / cleanup-first #266 / existing stacked DRAFT PR #355  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent/base:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05@fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test SHA:** `caeea7f30bc959c3264b785592b8e53f28d040b6`  
**Pre-sync branch HEAD:** `caeea7f30bc959c3264b785592b8e53f28d040b6`  
**Status:** SCOPED CI VERIFIED · Full handover freshness sync required · HARDWARE NOT TESTED · PRODUCTION NO-GO.

## Completed bounded task

The two sketches already deny outputs before the synchronous startup `post("register")`, explicitly discard the register response, and deny again after registration. The modular poll-preflight lab did not protect those startup invariants.

Added source-extracted assertions to the Hardware-owned lab requiring:
- exactly one executable register POST, only inside the Wi-Fi-connected `connectSta()` branch;
- explicit response discard and no startup `applyRemoteConfig()` consumer;
- unconditional startup deny before `connectSta()` and unconditional post-register deny;
- comment/string decoys ignored.

Failure injection rejects **8/8** unsafe mutations on each board, including missing/conditional startup deny, moving register outside the Wi-Fi-connected branch, missing/conditional post-register deny, consuming/applying the response, and a duplicate register POST outside `connectSta()`. The two response-use variants are separately **2/2 rejected**.

No production `.ino`, GPIO logic, shared API, QA/CORE/Master files, finance, signer, witness, migration or COE destination changed.

## Exact evidence

- Focused [#45882710658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710658), job `140125732751`: **PASS** at `caeea7f30bc959c3264b785592b8e53f28d040b6`. Both ESP8266 and ESP32 pass the new startup register guard; 8/8 mutations rejected per board, 2/2 response-use variants rejected, decoys ignored. Existing poll model reports 3500 ms, 80 ms pulse, zero samples and zero accepted pulses, four independent relay/LED polarity combinations. SIMULATED / CI VERIFIED only.
- Full [#45882710608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710608): CI-0701 `140125802015` PASS; 13 firmware targets + Android (14 jobs) PASS; validation `140125877416` FAIL at handover freshness because canonical docs last checkpoint was `57b69a4bff7fd15f93c5ba2e0de7d367ff2bdec5`. This docs sync is the required post-source update. Production import, update, simulations, candidate, signing and publication skipped.
- Mbed TLS [#45882710626](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710626): source-contract `140126409598` PASS; target builds 3.3.13 and 4.0.0 IN PROGRESS at this checkpoint.

## Release and ownership boundary

QA owns deny-only controller assertion reconciliation; CORE owns authenticated register/poll and receipt/disposition; MASTER owns global role assignments and branch pins. Master role files at `ed6bb786c08d360a611e0e6c5c0505fa90d9b477` do not yet list #355. Cleanup #266 remains OPEN / 0-of-7; financial #31/#32, safety #34 and witness #43 remain open.

Host/source-extracted results are SIMULATED / CI VERIFIED only. Physical GPIO/relay, real coin acceptor, electrical pulse/recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO. Private Drive registry v11 was not available; no older registry was substituted.

## Next exact action

Rerun Full after canonical sync to pass handover freshness and reveal the inherited QA-owned controller assertion. Keep PR #355 DRAFT, parent #354 unchanged, and coin/relay admission denied.

**Updated UTC:** 2026-11-26T19:20:00Z
