# PHX-HARDWARE — quarantine lab lexical-aware source extraction

**Date:** 2026-11-20 UTC09  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Task:** [#266 cleanup-first](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) / [#177 hardware pulse ingress](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#172 control plane](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test fix:** `28b44466809a68008ba93d71db1a6fa5a0b2bc05`  
**Test-first RED:** `40e43b7a40bd1b96720f8ba36adcd7949f48dace`

## Finding

The Hardware-owned `quarantine_readback_lab.py` still contained a local brace counter that treated every physical `{` / `}` byte as C++ syntax. It did not mask comments, ordinary string literals or raw strings. A harmless diagnostic string/comment containing a brace could therefore truncate an extracted production helper and make the host lab compile the wrong body.

The regression fixture contains a closing brace in an ordinary string, braces in a C++ raw string, and a closing brace in a block comment. The legacy extractor returned early, before the function body ended.

## Change

Only `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab.py` changed:

- Added the existing shared `firmware_lab_source.extract_function` import from the ESP8266 lab directory.
- Replaced the local naive brace counter with a small signature-prefix adapter that delegates to the shared lexical-aware extractor.
- Added a regression fixture covering ordinary strings, raw strings and block comments.

No `.ino` runtime, persistence format, GPIO, relay, coin admission, controller protocol, CORE API, financial path, QA-owned test, Release workflow or COE file changed. The 22-function ESP32/ESP8266 parity set was preserved.

## Test-first evidence

- **RED:** [Quarantine run #44713614755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44713614755), job `136211270346`, exact SHA `40e43b7a40bd1b96720f8ba36adcd7949f48dace`: expected failure, `source extractor truncated a C++ literal/comment fixture`.
- **GREEN:** [Quarantine PR run #44713787790](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44713787790), job `136211861582`, exact SHA `28b44466809a68008ba93d71db1a6fa5a0b2bc05`: SUCCESS. The new lexical fixture passed (the script continued), shared board parity remained `22/22`, and source-extracted quarantine scenarios passed `36/36` per board / `72/72` total. The same job continued through the existing pending journal, attempt-marker, POST gate, poll-window, pulse, EEPROM/NVS and poll-loop labs.
- **Relay/output:** [run #44713787410](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44713787410), jobs `136211859585` and `136211860004`: SUCCESS.
- **Full BlazePwifi:** [run #44713787932](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44713787932), validation job `136211996821`: FAILED at the existing QA-owned `Missing poll signature check` in the ESP8266 controller sketch. All 13 firmware/platform target jobs and Android completed SUCCESS; downstream simulations, update bundle, signing, candidate gate and publishing were SKIPPED. This is not a Full validation PASS.

## Evidence classification and limits

- **CI VERIFIED:** lexical-aware source extraction, board parity and focused source-extracted regression suite at the exact source/test SHA.
- **SIMULATED:** C++ host fixtures and fake storage/GPIO/time; no physical coin or money was used.
- **NOT TESTED:** actual ESP32/ESP8266 flash/NVS/EEPROM durability, physical coin acceptor, relay under load, electrical pulse/recovery, 150 controlled power cuts, and 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO — PRODUCTION NO-GO.

## Coordination and next actions

1. **PHX-QA** owns the inherited positive poll-signature assertion. Replace it only with source-exact default-deny tests after CORE publishes the authenticated register/poll contract. Do not add a synthetic `response_sig` or weaken firmware deny.
2. **PHX-CORE** must publish the canonical authenticated register/poll and event-bound receipt bytes plus golden vectors before any positive disposition is enabled.
3. **PHX-MASTER** must refresh the canonical Hardware active-PR head for #327 and reconcile the live #323/#326 ancestry against PR metadata. Hardware did not edit Master-owned coordination files.
4. **PHX-HARDWARE** reloads the live branch and exact CI on the next activation before selecting another owned task.

The private canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed Library/connector surface. Older registry snapshots were not substituted. No Drive data or private material was promoted.

No physical flashing, device reset, live money, secret provisioning, production migration, signing, merge, release tagging or deployment was performed.
