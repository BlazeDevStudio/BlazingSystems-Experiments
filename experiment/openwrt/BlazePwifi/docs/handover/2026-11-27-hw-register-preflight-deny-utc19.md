# PHX-HARDWARE UTC19 — startup register fail-closed guard coverage

**Role:** PHX-HARDWARE  
**Task:** hardware #177 / cleanup-first #266 / existing stacked DRAFT PR #355  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent/base:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05@fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test SHA:** `caeea7f30bc959c3264b785592b8e53f28d040b6`  
**Prior canonical docs-sync HEAD:** `375bbd4824f12e0c6ffe513432c988f95394ca45`  
**Current PR state:** OPEN / DRAFT / UNMERGED · **PRODUCTION:** NO-GO.

## Completed bounded task

Added source-extracted assertions to the Hardware-owned poll-preflight lab for the synchronous startup register exchange on both ESP8266 and ESP32. The contract requires exactly one register POST inside the Wi-Fi-connected `connectSta()` branch, explicit response discard, no startup `applyRemoteConfig()` consumer, unconditional deny before `connectSta()`, and unconditional deny after registration. Comment/string decoys are ignored.

Failure injection rejects **8/8** unsafe mutations per board, including missing/conditional startup deny, moving register outside the Wi-Fi-connected branch, missing/conditional post-register deny, consuming/applying the response, and duplicate register POST outside `connectSta()`. The two response-use variants are separately **2/2 rejected**.

No production `.ino`, GPIO logic, shared API, QA/CORE/Master source, finance, signer, witness, migration or COE destination changed.

## Exact evidence

- Focused source/test [#45882710658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710658), job `140125732751`: **PASS** at `caeea7f30bc959c3264b785592b8e53f28d040b6`.
- Focused docs-head [#45883295366](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45883295366), job `140127681438`: **PASS**; both boards 8/8 mutations rejected, 2/2 response-use variants rejected, decoys ignored; poll 4/4 polarity and blocking-wait model PASS.
- Mbed TLS [#45882710626](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710626): source-contract `140126409598`, core 3.3.13 `140126410030`, core 4.0.0 `140126410147`: **PASS** at exact source/test SHA.
- Full pre-sync [#45882710608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710608): 13 firmware targets + Android PASS; validation failed stale handover, superseded by the post-sync run.
- Full post-sync [#45883295442](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45883295442): CI-0701 and handover gate PASS; validation `140127752453` fails at QA-owned `tests/controllers.sh:21` because `config_revision` is absent. Both sketches contain `applyRemoteConfig` only as a deny-only stub (`(void)response; denyRemoteControl();`) and have no callsite. Thirteen firmware target jobs PASS; Android `140127752382` IN_PROGRESS at last check. Production import/update/simulation/candidate/signing/publication skipped.

## Release and ownership boundary

QA owns the deny-only-incompatible `config_revision` assertion; CORE owns authenticated register/poll and receipt/disposition; MASTER owns global assignments and branch pins. Master role files at `ed6bb786c08d360a611e0e6c5c0505fa90d9b477` still do not list #355. Cleanup #266 remains OPEN / 0-of-7; financial #31/#32, safety #34 and witness #43 remain open.

Host/source-extracted results are SIMULATED / CI VERIFIED only. Physical GPIO/relay, real coin acceptor, electrical pulse/recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO. Private Drive registry v11 and hourly signal YAML were not available; no older registry substituted.

## Next exact action

Request QA/CORE/Master reconciliation, preserve deny-only behavior, and continue Hardware work only after the authenticated contract is approved. Keep PR #355 DRAFT and parent #354 unchanged.

**Updated UTC:** 2026-11-26T19:25:00Z
