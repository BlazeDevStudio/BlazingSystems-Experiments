# PHX-HARDWARE — active-low relay cross-product for blocking poll

**Date:** 2026-11-24 UTC12  
**Task:** [#177 — synchronous poll coin-pulse loss](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** `PHX-HARDWARE`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #349 stacked on #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `bb064e1cd0548a476ab2b685f0f8c2b625df0cf5`  
**PR:** [#349 — JSON grammar and first-fault snapshot regressions](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED

## Why this increment

The current #349 blocking-poll lab exercises the original 1501/1600/1680 ms missed-pulse timeline and the 3.5-second synchronous HTTP path using the default active-high relay fixture. A separate source-extracted relay-polarity lab already tests active-high/active-low `applyOutputs()` gates in isolation. This increment composes the configured **active-low relay** with the actual blocking-poll scenarios so the #177 path is checked end-to-end at the host/source-extracted level.

## Changes

- Added `with_active_low_relay()` to `poll_loop_blocking_inhibit_lab_scenario_fixtures.py`. It changes the reset fixture before `configureRuntimePins()`, verifies the logical relay starts ON at physical LOW, and then runs the unchanged extracted production loop.
- Exported the helper through `poll_loop_blocking_inhibit_lab_fixtures.py`.
- Extended `poll_loop_blocking_inhibit_lab.py` to run:
  - The original 1501/1600/1680 ms pulse during pre-poll quiet drain with an active-low relay.
  - The 3.5-second blocked HTTP poll with ISR edge injection and an active-low relay.
  - A mutation removing `beginPollWindow()`, expected exit 47.
  - A mutation ignoring `pollIntakeSuspended` in `applyOutputs()`, expected exit 88.
- No production `.ino`, CGI producer, controller contract, financial code, signer, witness, migration or release workflow was changed.

## Exact-head CI — source/test SHA `bb064e1cd0548a476ab2b685f0f8c2b625df0cf5`

- Quarantine PR [run #45392521851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45392521851), job `138439673139`: **PASS**.
  - ESP8266 and ESP32 both emit `PHX_177_ACTIVE_LOW_RELAY_1501_1600_1680_TIMING_PASS`.
  - Both reject missing pre-poll inhibit (exit 47).
  - Both emit `POLL_HTTP_ACTIVE_LOW_RELAY_INHIBIT_PASS`.
  - Both reject the ignored-`pollIntakeSuspended` output-gate mutation (exit 88).
- Relay Output Polarity PR [run #45392521885](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45392521885): source/output job `138439672030` **PASS**; ESP32 boot-polarity job `138439671506` **PASS**.
- Full PR [run #45392521816](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45392521816): validation job `138439832989` **FAIL** at inherited QA-owned `tests/controllers.sh` assertion `Missing poll signature check`. Firmware target jobs were still finishing at handover capture; no total target count is claimed here. Validation-dependent simulation, update, signing and publication stages were skipped.
- Initial test attempt at `c4b109b9d556cf2692c56bffe25b79b9ddec7f63`: Quarantine [run #45392093421](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45392093421), job `138438178987`, **FAIL** because the helper's Python fixture anchor was double-escaped. The literal was corrected in `bb064e1cd0548a476ab2b685f0f8c2b625df0cf5`; final exact-head Quarantine and Relay runs above pass.

## Evidence classification and limits

- Active-low relay + blocking-poll source-extracted regression: **SIMULATED / CI VERIFIED**.
- Physical relay polarity, acceptor contact state, electrical pulse conditioning and coin insertion during poll: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device 24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

The test does not prove the acceptor's physical relay contacts are open, nor does it establish pulse preservation through real electrical transients. The production mitigation remains on the unmerged #345/#347/#349 stack.

## Coordination and blockers

- PHX-CORE still owns the authenticated register/poll response contract and canonical golden vectors.
- PHX-QA owns the inherited `Missing poll signature check` assertion and independent reconciliation.
- PHX-MASTER must refresh the #349 source/test pin to `bb064e1cd0548a476ab2b685f0f8c2b625df0cf5` and record the final docs head.
- PHX-HARDWARE must retain default-deny coin disposition and request noncustomer physical acceptance only after the software stack is independently reviewed.

## Next exact action

PHX-MASTER: refresh #349 assignment/integration pins to source/test SHA `bb064e1cd0548a476ab2b685f0f8c2b625df0cf5` and this handover. PHX-CORE/PHX-QA: publish and independently reconcile the authenticated register/poll contract. PHX-HARDWARE: rerun Full integration at the approved contract SHA, then prepare the noncustomer relay/pulse acceptance plan. No flash, reset, live coin, production migration, merge, release tag or deployment was performed.
