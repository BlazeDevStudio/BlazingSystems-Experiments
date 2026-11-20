# PHX-HARDWARE — poll-response lab lexical extractor consolidation

**Date:** 2026-11-20 UTC10  
**Task:** [#266 cleanup-first](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) / [#177 pulse-loss P0](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#172 control plane](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `e04f76d7c0e938119605130d7c00f8905896d85d`

## Finding

The Hardware-owned `poll_response_failclosed_lab.py` used a local regex plus byte-wise brace counter. It did not mask braces in ordinary C++ strings, raw strings, or comments. This could truncate an extracted production function and cause the poll-response host lab to compile less than the intended function body.

The lab is already invoked transitively by `quarantine_readback_lab.py`; the quarantine workflow log confirms that call. A temporary direct workflow invocation was removed to avoid running the same lab twice. The final workflow retains its original single invocation path.

## Change

Only the Hardware-owned poll-response lab is behaviorally changed:

- Replaced the local brace counter with the shared `firmware_lab_source.extract_function`.
- Added a lexical regression fixture with a closing brace in an ordinary string, braces in a C++ raw string, and a closing brace in a block comment.
- Removed the now-unused `re` import.
- Preserved the existing source-extracted poll, JSON-root-status, coin POST and output-deny scenarios.

No firmware `.ino`, runtime behavior, GPIO, relay, persistence format, shared API, finance, QA-owned test, Release-owned workflow or COE source changed.

## Test-first evidence

- **RED:** [Quarantine run #44721696323](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44721696323), job `136238787216`, test-only head `a791e9bf578692bcfed9cbff6f2fc837158ec525`: expected failure, `source extractor truncated a C++ literal/comment fixture`.
- **GREEN:** [Quarantine run #44722029510](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722029510), job `136239913962`, exact source/test SHA `e04f76d7c0e938119605130d7c00f8905896d85d`: SUCCESS. Log contains `POLL_RESPONSE_LEXICAL_EXTRACTOR_PASS`; ESP8266 and ESP32 each passed 11/11 poll-response fail-closed cases, 13/13 strict root JSON cases, 4/4 coin POST root-status cases and 4/4 coin-disposition default-deny cases. The existing quarantine suite also passed 36/36 scenarios per board (72/72 total), alongside the other invoked hardware labs.
- **Relay/output:** [run #44722029559](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722029559), jobs `136239914030` and `136239914458`: SUCCESS.
- **Full BlazePwifi:** [run #44722029666](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44722029666), validation job `136239924430`: FAILED at the inherited QA-owned `Missing poll signature check`. The run then terminated CANCELLED: Android PASS, 12/13 firmware target jobs PASS, Orange Pi PC target job `136239924957` CANCELLED, and downstream simulations/update/signing/candidate/publishing gates were skipped or cancelled. This is not a Full validation PASS.

## Evidence limits

- **CI VERIFIED:** shared lexical extraction and source-extracted poll-response/default-deny tests at the exact source/test SHA.
- **SIMULATED:** host C++ fixtures, fake time/GPIO/storage and source ordering.
- **NOT TESTED:** physical coin acceptor, loaded relay, electrical pulse/recovery, actual ESP flash/NVS/EEPROM durability, 150 physical power cuts, and 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO — PRODUCTION NO-GO.

## Coordination / next actions

1. **PHX-QA** owns the inherited positive poll-signature assertion. Replace it only with source-exact default-deny tests until CORE publishes an approved contract; do not weaken firmware deny.
2. **PHX-CORE** publishes canonical authenticated register/poll and event-bound receipt bytes plus positive/negative golden vectors before any positive disposition is enabled.
3. **PHX-MASTER** refreshes #327's live exact head and reconciles the #323/#326 ancestry in the canonical role/stack ledger.
4. **PHX-HARDWARE** reloads all live refs and CI before selecting the next owned task.

The private canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed Library/connector surface. Older snapshots were not substituted; no Drive data or private material was promoted.

No physical flashing, device reset, live money, secret provisioning, production migration, signing, merge, release tagging or deployment was performed.
