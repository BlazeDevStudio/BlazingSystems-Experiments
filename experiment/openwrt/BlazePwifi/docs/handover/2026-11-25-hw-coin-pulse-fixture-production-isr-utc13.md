# PHX-HARDWARE — coin pulse fixtures exercise the extracted production ISR

**Date:** 2026-11-25  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** [#352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/352) — OPEN / DRAFT / UNMERGED  
**Parent:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED  
**Working branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Parent #349 HEAD:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`  
**Source/test HEAD:** `d3e36ae444e262bcd8ac37e087c9d98358e7a168`
**Exact PR/docs HEAD revalidated before this handover-only update:** `c2179ef1cd28b732fb9026946d04882aca521d8a`

## One Hardware-owned test-fidelity defect corrected

The source-extracted coin-pulse fixture previously incremented or assigned `coinEdgeSequence` directly in several pulse scenarios. Those operations bypassed the actual extracted `coinEdgeISR()`. The suite therefore did not exercise the production ISR for every simulated edge and could give misleading confidence about the pulse-capture path.

The correction is test-only:

- Added `emitCoinEdges(count)`, which invokes the extracted production `coinEdgeISR()` for each simulated edge.
- Routed late coin-POST, blocking-work, single-edge, multi-edge, ingress-transition and rollover scenarios through that helper.
- Retained explicit counter seeding only for rollover baseline setup.
- Added a fixture contract that rejects direct volatile-counter increments and requires the relevant scenarios to call `emitCoinEdges()`.
- Updated the no-op ISR mutation's expected first-failure marker to `late-coin-post-edge`, because the late-POST scenario now actually exercises the ISR.

**Scope clarification:** The UTC13 fixture-only conversion did not modify either `.ino` sketch. However, PR #352 as a whole includes the earlier production-source commit [`ec9547f8`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ec9547f8e97b815db705d5aa65382f171b5eade9) in both sketches: `coinEdgeSequence++` was replaced with `coinEdgeSequence = coinEdgeSequence + 1U` to keep the unsigned modulo-2^32 increment explicit and avoid the deprecated volatile-`++` warning. This is a production ISR source change and is included in the exact-core build evidence below. The UTC13 test-fidelity conversion itself changes only the fixture/harness. No pin, polarity, debounce, relay, credit, accounting, controller API, signer, witness, replay, downgrade or migration behavior was changed by these commits.

## Test-first history and intermediate failure

1. Test-first guard commit [`c089dc93`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c089dc93a5f93afd780dd25c4acd195cb45fa44e) added the fixture contract before changing the fixture.
   - Quarantine [run #45627440215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45627440215), job `139251294492`: expected RED; rejected direct `coinEdgeSequence` mutation.
   - Relay [run #45627440160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45627440160), job `139251294221`: same expected RED.

2. Initial fixture conversion [`521871a1`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/521871a1410aca61a6f2626ded20350f74c3f935) exposed a rollover-fixture ordering error: two ISR edges were emitted before asserting the first transition to `UINT32_MAX`.
   - Quarantine [run #45628059527](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628059527), job `139253468926`: FAIL at `isr-sequence-did-not-wrap`.
   - Relay [run #45628059558](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628059558), job `139253468083`: same failure on ESP8266 and ESP32.

3. Rollover correction [`d3e36ae4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d3e36ae444e262bcd8ac37e087c9d98358e7a168) now emits one edge, asserts `UINT32_MAX`, emits the second edge, then asserts wrap to zero.

## Exact source/test CI on `d3e36ae444e262bcd8ac37e087c9d98358e7a168`

| Workflow | Run / job | Result |
|---|---|---|
| Quarantine Byte Readback LAB | [#45628472254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628472254), job `139254924064` | **PASS** |
| Relay Output Polarity LAB | [#45628472317](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628472317), job `139254924563` | **PASS** |
| ESP8266 Arduino core 3.1.2 | [#45628472547](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628472547), job `139255009912` | **PASS** |
| ESP32 Arduino core 3.3.13 / 4.0.0 | [#45628472351](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628472351), jobs `139254926272` / `139254925518` | **PASS / PASS** |

Both focused lab logs report:

- ESP8266 coin pulse capture: **18/18 PASS**.
- ESP32 coin pulse capture: **18/18 PASS**.
- All 17 source mutations rejected on each board, including `missing-isr-sequence-increment`.
- Fixture module-boundary guard passed.
- The test harness's no-op ISR mutation is now detected through a scenario that invokes the extracted production ISR.
- Output explicitly retains `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

The exact Arduino builds passed on this source/test SHA. The ESP8266 compiler still emits the existing non-fatal `ICACHE_RAM_ATTR` deprecation warning; it was not changed in this task.

## Exact current-PR-head revalidation on `c2179ef1cd28b732fb9026946d04882aca521d8a`

GitHub Actions associated with the exact PR/docs head `c2179ef1...` completed the focused workflows again:

| Workflow | Run / job | Result |
|---|---|---|
| Quarantine Byte Readback LAB | [#45629285893](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45629285893), job `139257837448` | **PASS** |
| Relay Output Polarity LAB | [#45629285974](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45629285974), jobs `139257837555` / `139257842598` | **PASS / PASS** |
| ESP8266 Arduino core 3.1.2 | [#45629286016](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45629286016), job `139257838230` | **PASS** |
| ESP32 Arduino core 3.3.13 / 4.0.0 | [#45629286022](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45629286022), jobs `139257838056` / `139257837855` | **PASS / PASS** |

The exact-head Full workflow [#45629285971](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45629285971) completed with 14/14 firmware/platform and Android build jobs passing, but validation job `139257838741` **FAILED** at the inherited `Missing poll signature check` in the ESP8266 sketch. The downstream update bundle, simulations, candidate gate, signing and publication jobs were skipped. The validate log confirms the exact failing assertion; no response signature was fabricated and deny-default was not weakened.

The current focused results are CI evidence for the source/workflow content present at `c2179ef1...`. The handover correction now being committed is documentation-only; it does not change firmware, fixture or workflow paths. No new source test is claimed for that documentation-only commit.

## Full integration blocker

Full BlazePwifi [run #45628472260](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45628472260), validation job `139255096795`, **FAILS** at:

`Missing poll signature check in .../esp8266/BlazePwifiVendo.ino`

All 14/14 firmware/platform plus Android build jobs passed. Update bundle, simulations, candidate gate, signing and publication jobs were skipped after validation failure.

This remains the CORE/QA producer-consumer contract blocker. Current main register/poll responses do not provide an approved `response_sig`; member-snapshot signatures are not interchangeable. CORE owns the authenticated producer contract and golden vectors; QA owns independent assertion reconciliation. Hardware retains deny-default and does not invent a signature.

## Revalidated ownership and release boundary

- Experiments main: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- #239 remains OPEN / DRAFT at `d83b715b116185107737fef721c2eece8feebf39`.
- #254 remains OPEN / DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, stacked on #239; cleanup commit `3692ddf889470da8a002e9a16bf0ac2f37f1a9d0` is unchanged.
- #283 remains OPEN / DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`; quarantine helpers remain definition-only and the current register/poll producer lacks the approved response signature.
- #340 remains OPEN / DRAFT at `fd1dbaa89e4267e53df22e73be73af80c6e61be8`, based on the older cleanup branch `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`; Master owns ancestry reconciliation.
- #347 remains OPEN / DRAFT at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`; #349 remains OPEN / DRAFT at `2a5c997add4f49fcd74f753101d3a9daac0040bf`; #352 stays stacked on #349.
- CoinOperatedEcosystem main remains scaffold at `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 and #45 remain OPEN / DRAFT. No COE source was changed or promoted.
- Cleanup-first #266 remains OPEN; this is one narrow Hardware test-fidelity contribution, not completion of the seven-role cleanup gate.

## Evidence classification

- Source/test fixture and failure-injection behavior: **CI VERIFIED / SIMULATED**.
- ESP8266/ESP32 exact-source target builds: **CI VERIFIED**.
- Physical coin acceptor pulse capture: **NOT TESTED**.
- Relay electrical/load behavior: **NOT TESTED**.
- LittleFS/EEPROM physical power-loss recovery: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device, 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay and v1-to-v2 financial migration: **NOT ACCEPTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact actions

1. PHX-MASTER refreshes the #352 source/test pin and reconciles the #340/#283 ancestry without retargeting or merging.
2. PHX-CORE publishes the authenticated register/poll producer contract and canonical golden vectors.
3. PHX-QA independently reconciles the Full validation assertion without weakening deny-default.
4. PHX-HARDWARE revalidates all live heads on the next activation and selects one new unblocked Hardware-owned task.

No local device flashing, reset, live-money test, signer provisioning, production migration, release tag, merge, deployment or force-push occurred.
