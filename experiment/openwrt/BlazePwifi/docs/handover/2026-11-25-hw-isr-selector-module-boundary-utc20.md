# PHX-HARDWARE UTC20 — board-conditioned ISR selector module boundary

**Date:** 2026-11-25 UTC  
**Role:** PHX-HARDWARE  
**Task references:** [#172 CONTROL PLANE](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172), [#266 cleanup-first](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266), [#177 hardware pulse loss](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#353](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/353), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-board-conditional-isr-selector-20261125-utc17`  
**Source/test SHA:** [`4f361e032c30faa368105775e3646c570f9760a8`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4f361e032c30faa368105775e3646c570f9760a8)  
**PR base captured at:** `6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec`  
**Live parent #352 HEAD at inspection:** `0e984e267b3a8fb10c314800d1a7f120806354b7`

## One bounded Hardware-owned task

Separate the board-conditioned C++ preprocessor/ISR selection contract from the coin-pulse scenario runner. This is host-lab maintainability work only; it does not change firmware behavior or a shared controller API.

## Source changes

- Added `coin_pulse_capture_lab_isr.py`, owning six helpers: `_condition_board_gate`, `_active_board_isr_definition`, `extract_board_coin_edge_isr`, `mutate_active_isr_attribute`, `verify_board_specific_isr_selection`, and `verify_inactive_isr_source_decoy_tolerance`.
- Reduced `coin_pulse_capture_lab.py` from 17,768 to 10,262 bytes (7,506 bytes moved out); the runner retains pulse scenarios, persistence mutations and shared-source checks.
- Extended `coin_pulse_capture_lab_structure_guard.py` to require the selector module, verify the runner's four public imports, enforce the shared parser dependency, and prove the six selector helpers are owned only by the selector module.
- Added the new module path and this child branch to the focused Hardware workflow filters so subsequent branch changes can run the same exact-source labs.

No production `.ino`, GPIO/polarity logic, CGI producer, controller contract, financial source, migration, signer, witness, updater or release path was modified.

## Test-first evidence

**RED — expected missing-module failure**

- [Quarantine RED run #45698045060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698045060), job `139500521412`, step 6: `COIN_PULSE_CAPTURE_MODULE_BOUNDARY_FAIL: required module is missing: coin_pulse_capture_lab_isr.py`.
- [Relay RED run #45698045073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698045073), job `139500521485`, step 8: same explicit missing-module failure. Earlier source/polarity/poll-inhibit tests passed before the guard stopped the run.

**GREEN — exact source/test SHA `4f361e032c30faa368105775e3646c570f9760a8`**

- [Quarantine GREEN run #45698465435](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465435), job `139501979087`: PASS. Module-boundary guard reports `FUNCTION_SPECS=11 MUTATIONS=17 ISR_SELECTOR_HELPERS=6`; source quarantine reports 36/36 scenarios for each board (72/72 total); pulse capture reports 18/18 for ESP8266 and 18/18 for ESP32; poll-abort, strict JSON, config-read failure and fail-closed checks pass.
- [Relay GREEN run #45698465398](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465398), job `139501978886`: PASS. Module-boundary guard and both-board pulse capture pass; inactive ISR decoys are ignored; active-branch selection and deprecated-attribute mutation checks pass. Separate ESP32 boot-polarity job `139501979189`: PASS.
- Both focused workflows explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Full integration result — still blocked

- [Full build run #45698465506](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45698465506), validation job `139501980615`: FAIL at `Controller protocol parity` — `Missing poll signature check` in the ESP8266 sketch.
- All 13 firmware target jobs and the Android job PASS on the same SHA. The downstream update bundle, browser/device simulations, candidate gate, signing and publication stages are SKIPPED.
- This task changed no producer/consumer signature contract. PHX-CORE must publish the canonical authenticated register/poll contract; PHX-QA must reconcile the assertion without weakening deny-default.

## P0 hardware issue remains

The active development branch `blazepwifi-v0.6.0-audit-foundation` still performs synchronous `post("poll")` before sampling `digitalRead(runCoinPin)` in both sketches:

- ESP8266 blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`
- ESP32 blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`

The unmerged #349/#352 hardware stack contains the poll-intake suspension/drain-window mitigation, but it is not integrated into the active development branch. This UTC20 task does not claim to fix #177.

## Stack and coordination blockers

- PR #353 remains DRAFT and unmerged. Its captured base `6d743ae...` is behind the live #352 parent HEAD `0e984e...`; no rebase, retarget or force-push was performed. PHX-MASTER must reconcile the stacked ancestry.
- #239, #254 and #283 remain separate open DRAFT hardware work; no source was taken from or merged across those branches.
- #172, #266, #177, #34, #31, #32 and #43 remain open; physical acceptance, anti-rollback witness/signer, v1-to-v2 migration, durable accounting/replay and independent QA/release acceptance remain unproven.
- No Google Drive connector was available in this activation, and the accessible Files Library did not return `BLAZE_PROJECT_REGISTRY_v11_20261027.json`. An older registry snapshot was not substituted or promoted.

## Evidence classification and next action

**CI VERIFIED / SIMULATED ONLY. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

Next: PHX-MASTER reconciles #352/#353 ancestry and the #349 stack; PHX-CORE publishes the authenticated poll/register contract; PHX-QA reconciles the full parity assertion; then PHX-HARDWARE reruns the exact-head matrix after the parent is resolved and continues noncustomer hardware acceptance planning. No flashing, device reset, live-money action, production migration, deployment, merge or release tagging is authorized by this handover.
