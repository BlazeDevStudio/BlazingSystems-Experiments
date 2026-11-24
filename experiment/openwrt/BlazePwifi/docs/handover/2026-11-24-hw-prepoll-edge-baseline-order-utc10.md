# PHX-HARDWARE — pre-poll ISR baseline ordering regression

**Date:** 2026-11-24 UTC10  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent stack:** DRAFT PR #349 → parent PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `0f067aad4937454a662c245743e37e9ec1e65820`  
**Status:** focused source-extracted CI verified; full integration blocked; simulated only; hardware not accepted; production no-go.

## One bounded task

Added a source-order assertion and a focused failure-injection regression for the initial ISR edge-sequence baseline used by the blocking-poll inhibit path.

The firmware loop must snapshot `coinEdgeSequence` **before** `beginPollWindow()` starts the 250 ms quiet drain. If that baseline is moved until after the drain, an ISR edge that arrives during the drain is absorbed into the new baseline; the later post-drain comparison can then miss it and incorrectly proceed to synchronous HTTP polling.

Changes are test-only:

- `poll_loop_blocking_inhibit_lab.py` now asserts that `pollEdgeStart` is captured before `beginPollWindow()`.
- `poll_loop_blocking_inhibit_lab_edge_fixtures.py` adds an isolated control main for an ISR edge injected after the final quiet sample and before poll dispatch.
- The control proves the real extracted loop persists the unresolved-ingress marker, keeps relay/LED OFF and does not start HTTP polling.
- A mutation moves the baseline snapshot after `beginPollWindow()`; the test expects exit 22 and rejects that regression on both ESP8266 and ESP32.

No production `.ino`, GPIO, relay, coin admission, controller API, financial schema, signer, witness, migration, workflow definition or COE destination was changed.

## Exact CI evidence at source/test SHA

- Quarantine push [run #45379723746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45379723746), job `138395294912`: **PASS**.
- Quarantine PR [run #45379732970](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45379732970), job `138395325414`: **PASS**.
- Relay/output push [run #45379723831](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45379723831), jobs `138395294852` and `138395295336`: **PASS**.
- Relay/output PR [run #45379732917](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45379732917), jobs `138395325315` and `138395325762`: **PASS**.

Both board logs include:

- `POLL_PRE_DRAIN_BASELINE_EDGE_CONTROL_PASS`
- `MUTATION_REJECTED late-poll-edge-baseline-after-drain expected_exit=22`

The broader existing poll-loop regressions, CGI envelope deny cases and output-polarity source checks also pass in the focused runs.

## Full integration remains blocked

Full BlazePwifi push [run #45379723630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45379723630):

- Validation job `138395442423`: **FAIL** at the inherited QA-owned `Missing poll signature check` in the ESP8266 controller sketch.
- All 13 firmware/platform target jobs: **PASS**.
- Android build: **PASS**.
- Update, simulations, candidate gate, signing and publication: **SKIPPED** after validation failure.

This is not a Full integration pass. Hardware does not invent a `response_sig` contract or weaken default-deny. PHX-CORE must publish the approved authenticated register/poll envelope and canonical vectors; PHX-QA must reconcile its independent assertion/extractor against that contract.

## Evidence classification and blockers

- Source-extracted host behavior: **SIMULATED**.
- Focused GitHub Actions: **CI VERIFIED**.
- Physical coin acceptor / relay / electrical pulse recovery: **NOT TESTED**.
- 150 real power cuts: **NOT TESTED**.
- 30-device, 24-hour soak: **NOT TESTED**.
- Independent QA / Master release acceptance: **PENDING**.
- `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`.

Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the accessible Library search, and no Google Drive connector is exposed in this runtime. Older registry snapshots were not substituted.

## Next exact action

PHX-MASTER refreshes the live #349 source/test and final handover pins in its coordination documents. PHX-CORE publishes the approved signed register/poll response contract and golden vectors. PHX-QA reconciles the inherited `Missing poll signature check` without relaxing negative/default-deny coverage. PHX-HARDWARE then reruns Full integration against the approved exact contract SHA.

No merge, force-push, physical flash, device reset, live-money operation, migration, release tag or deployment is authorized by this handover.
