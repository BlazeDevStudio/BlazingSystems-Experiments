# PHX-HARDWARE UTC18 — poll preflight lab modularization

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / hardware #177 / stacked draft #355  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05@fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test SHA:** `e21f5e70695f3fdd6ee349e385fda69210034826`  
**Status:** FOCUSED CI VERIFIED · Full docs-sync rerun pending · SIMULATED ONLY · HARDWARE NOT TESTED · PRODUCTION NO-GO.

## Scope

The Hardware-owned 776-line `poll_preflight_inhibit_lab.py` was separated into three single-responsibility modules:
- `poll_preflight_inhibit_lab_contract.py`: source extraction and poll-guard contract.
- `poll_preflight_inhibit_lab_harness.py`: deterministic C++ harness construction, compilation and mutation execution.
- `poll_preflight_inhibit_lab_cases.py`: ESP8266/ESP32 cases and failure injection.
- `poll_preflight_inhibit_lab.py`: stable command entry point.

The original function bodies and test vectors were moved without changing behavior. The focused workflow path filters now include all three modules for both push and pull-request events. No production sketch, GPIO, relay, coin-admission, shared API, QA, CORE, financial or COE source changed.

## Exact test history

1. Refactor commit `8d893f6c913ff0b90a0ebe13af902718a0bfb653`: [run #45878977604](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45878977604), job `140113163508`, FAILED at Python syntax because the extracted `SKETCHES` mapping lacked its closing brace. This was an implementation error, not a test RED.
2. Correction `68a3281c1405bfe51434f7d9b9b9a142ce5ca3e9`: [run #45879096653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45879096653), job `140113559453`, FAILED with `NameError: _poll_call_matches` in the case module. This was an import-boundary error, not a test RED.
3. Final source/test `e21f5e70695f3fdd6ee349e385fda69210034826`: [focused exact-source run #45879218178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45879218178), job `140113978484`, PASS. Both board suites ran. Both logs show `BLOCKING_POLL_WAIT_PASS 3500ms pulse_ticks=80 samples_during_wait=0 accepted=0 polarity_combinations=4`; output-enable tests report 8/8 scenarios and 14/14 injected regressions rejected. Remote-config deny and request-auth guards also pass.

## Full workflow and cross-role boundary

Full PR [#45879218268](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45879218268) and push [#45879211901](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45879211901) failed the mandatory handover freshness gate because canonical handover docs predated `e21f5e70695f3fdd6ee349e385fda69210034826`. This checkpoint updates the canonical records; a new exact-docs-head Full run is required. Earlier #354 exact-head Full/Native failures at QA-owned `config_revision` and active `clearPending(true/false)` assertions remain separate blockers. PHX-QA owns those assertions; PHX-CORE owns the authenticated register/poll and receipt/disposition contract; PHX-MASTER owns global assignments and branch pins. Hardware will not edit those files or enable positive coin admission.

## Status

Host/source-extracted tests: **SIMULATED / CI VERIFIED**. Physical GPIO/relay, real coin acceptor, electrical pulse/recovery, LittleFS power loss, 150 controlled power cuts and 30-device/24-hour soak: **NOT TESTED**. Signer/witness, durable accounting/replay and v1→v2 migration: **NOT ACCEPTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

Private Google Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not accessible through this runtime. No registry-derived promotion or migration occurred.

## Process deviation

The required IN-PROGRESS handover was not staged before the first source commit. The two failed attempts are preserved above. Future source edits must stage the IN-PROGRESS handover before changing code.

## NEXT EXACT ACTION

Recheck the docs-head Full workflow after this sync. If it reaches the inherited QA assertion, request QA's deny-only reconciliation and CORE's approved authenticated poll/receipt contract. Keep PR #355 DRAFT and unmerged.
