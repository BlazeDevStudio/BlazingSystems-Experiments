# PHX-HARDWARE handover — strict JSON composite nesting-depth boundary (UTC10)

**Updated:** 2026-11-24T10:24Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#349 — JSON grammar and first-fault snapshot regressions](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test head:** `7903137ec903bd9aad3e275993f517d27146f311`  
**Status:** OPEN / DRAFT / UNMERGED; focused CI verified; Full integration blocked; production NO-GO.

## One bounded task

Add an exact boundary regression for the source-extracted JSON composite parser's maximum nesting depth. The firmware parser has a depth guard of 16; before this increment, the grammar lab did not exercise the exact 16/17 boundary for both arrays and objects.

Only these Hardware-owned board-local lab files changed in the source/test increment:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_json_array_primitive_lab_fixtures.py`

No production `.ino`, CGI producer, protocol/API, financial, signer, witness, migration, QA-owned test, or Release workflow changed.

## Concrete test changes

- Added a separate C++ fixture `DEPTH_MAIN` in the fixture module; the runner remains responsible for extraction, compilation, execution and mutation checks.
- For both nested arrays and nested objects, depth 16 must parse fully and depth 17 must be rejected.
- Added two source-derived fail-open mutations:
  1. Remove the `depth>16` guard.
  2. Raise the boundary to `depth>17`.
- Both mutations must cause the 17-level array fixture to be accepted and therefore fail the regression program at expected exit 122. The unmutated parser must accept 16 and reject 17 for arrays and objects.
- The test runs against the actual parser functions extracted independently from the ESP8266 and ESP32 sketches.

## Exact-head GitHub Actions evidence

All runs checked out literal source/test SHA `7903137ec903bd9aad3e275993f517d27146f311`.

- Relay focused [run #45373856754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45373856754):
  - Source/output job `138374718225`: **SUCCESS**.
  - ESP32 boot-polarity job `138374718691`: **SUCCESS**.
  - Both boards print `POLL_JSON_COMPOSITE_DEPTH_PASS max=16 rejected=17 arrays=1 objects=1`.
  - Both boards reject `remove-composite-depth-cap` and `allow-depth-17` mutations at expected exit 122.
- Quarantine focused [run #45373856706](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45373856706), job `138374718142`: **SUCCESS**.
  - Same 16/17 array/object boundary and both mutation rejections on ESP8266 and ESP32.
  - Existing quarantine, journal, pending-clear, pulse-capture, poll-inhibit and bounded-HTTP labs also pass.
- Full [run #45373856711](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45373856711): **FAILURE**.
  - Validation job `138374881351`: **FAIL** at inherited `tests/controllers.sh` assertion `Missing poll signature check` in the ESP8266 sketch.
  - All 13/13 firmware target jobs and Android completed **SUCCESS**.
  - Validation-dependent update, simulation, candidate, signing and publication stages were **SKIPPED**.
  - The failure is the existing CORE producer / QA consumer-contract mismatch; this Hardware change did not modify it.

## Ownership, integration and safety boundaries

- The #177 blocking-poll coin-intake inhibit and ISR reconciliation remain on the unmerged #345/#347 stack. This increment adds parser-boundary regression evidence only; it does not claim physical pulse-loss acceptance.
- PR #239 remains OPEN / DRAFT at `d83b715b116185107737fef721c2eece8feebf39`; #254 remains OPEN / DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; parallel #283 remains OPEN / DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`.
- The original #283 unconditional-clear audit lead is not present in the current #283 source: failed append returns before clear; however `quarantinePending()` is definition-only, so no end-to-end lifecycle is accepted. Current main register/poll still lacks an approved `response_sig`; firmware remains deny-only.
- #348 remains a separate #254 child with an ESP32 core 4.0.0 Mbed TLS header blocker. The separate #340 PSA provider candidate is not a substitute for #348 evidence. No provider port was made; Master approval/stack decision remains outstanding.
- Master PR #288 current head is `08345f148162d83c2558e7823aa478be0cb7d3da`. Its `ROLE_ASSIGNMENTS.md` still pins #349 to source/test `6ce423783b306411bdb7e7217081c050cb4cbec4` and docs `a994f7048673677651449eeb0a04d2bf9e91737c`; the integration matrix also contains older #349 pins. Master-owned files were not edited; refresh requested.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No staging or source migration occurred.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the accessible Library. No Google Drive connector is exposed in this execution; older registry versions were not substituted.

## Evidence classification

- JSON nesting-depth boundary and mutation tests: **CI VERIFIED / SIMULATED**.
- Firmware target builds: **CI VERIFIED** in the Full run; overall integration validation remains failed.
- Physical coin acceptor, relay/electrical pulse recovery, LittleFS power-loss, 150 controlled power cuts and 30-device 24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact action

PHX-MASTER refresh the #349 source/test/docs pins in `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and the #172 current-state summary to the new exact head. PHX-CORE must publish the approved authenticated register/poll response envelope and golden vectors; PHX-QA must independently reconcile the inherited assertion against that contract. PHX-HARDWARE will keep coin admission deny-only and rerun Full only against the approved exact contract SHA.

No merge, force-push, physical flash, device reset, live-money operation, production migration, release tag or deployment occurred.
