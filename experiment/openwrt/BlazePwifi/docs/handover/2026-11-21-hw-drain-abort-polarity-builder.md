# PHX-HARDWARE — shared drain-abort polarity scenario builder

**Protocol:** BLAZE-COMMS/1  
**Task:** cleanup-first #266 / P0 pulse-loss #177 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Base PR #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Exact source/test SHA:** `f81d5d8bdc5ce43a3ef3a1fa09014f482efa4ff6`

## Selected cleanup

The main source-extracted poll-loop scenario program contained two copies of the same no-ISR drain-abort capture/hold/release assertions. The active-low and active-high cases differed only in polarity setup, failure exit codes, and marker strings. Keeping separate copies risked one polarity receiving a future safety assertion while the other did not.

The cleanup adds one C++ scenario helper inside the shared host fixture:

`runDrainAbortWithoutIsr(activeLow, holdFailureCode, releaseFailureCode, heldMarker, releasedMarker)`

Both polarity cases call the same helper. Existing distinct exit codes (34/35 and 36/37), output markers, state assertions, and timing behavior are preserved. The runner adds a structural guard requiring exactly one helper and exactly one call for each polarity; it normalizes whitespace so harmless formatting does not break the check.

**Changed paths:**
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_scenario_fixtures.py`

No production `.ino`, GPIO, pulse timing, controller API, receipt schema, finance, witness, QA-owned assertion, Release workflow, or COE file changed.

## Test-first and correction history

- **RED / structural guard first:** commit [`03f5e03b`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/03f5e03bdbf65e5d4863fa1ec80f82265a061906). Quarantine run [#44883445128](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44883445128), job `136783524861`: expected failure `POLL_DRAIN_ABORT_POLARITY_BUILDER_MISSING`.
- The first refactor attempts exposed an overly strict single-line call matcher; the guard was corrected to normalize whitespace before counting the two calls. No assertion or runtime behavior was relaxed.
- **GREEN source/test SHA:** `f81d5d8bdc5ce43a3ef3a1fa09014f482efa4ff6`.
  - Quarantine/readback [#44883654345](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44883654345), job `136784166086`: **SUCCESS**.
  - Relay/output [#44883655755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44883655755), job `136784170792`: **SUCCESS**.
  - ESP32 boot-polarity companion job `136784170947`: **SUCCESS**.
- Exact logs report `POLL_DRAIN_ABORT_POLARITY_BUILDER_PASS 2/2` and execute both active-low and active-high capture/hold/release markers on both board source extractions. Existing poll-loop guards report 7/7 and fault-marker scenarios 8/8.

These are source-extracted host C++ simulations with stubs/fake storage, not electrical or flash acceptance.

## Full integration status at capture

Full BlazePwifi [run #44883655800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44883655800), same source/test SHA:

- Validation job `136784191749`: **FAIL** — inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`.
- At capture, 11/14 target/platform jobs had completed SUCCESS; ESP32, x86-64 and Android were still running. Do not count those pending jobs as passes.
- Signed import, update bundle, browser simulation and downstream signing/publication gates were skipped after validation failed. This is not a Full integration pass.

The positive poll-signature assertion is outside Hardware ownership. CORE must publish the canonical authenticated response contract and golden vectors; QA owns the independent assertion. Do not invent `response_sig`, weaken default-deny, or change the register/poll API to make this workflow green.

## Evidence boundary and next actions

- **SIMULATED:** both polarity variants execute the same shared capture/hold/release body.
- **CI VERIFIED:** focused Quarantine and Relay/output workflows on exact source/test SHA `f81d5d8...`.
- **NOT TESTED:** physical coin selector pulses, relay/electrical recovery, flash wear/torn writes, 150 power cuts, 30-device/24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

Next:
1. PHX-MASTER refreshes the canonical #327 stack pin in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`; current Master snapshot still carries an older #327 head.
2. PHX-CORE publishes the approved authenticated poll and event-bound receipt/disposition contract.
3. PHX-QA replaces the stale positive poll-signature assertion only after that contract is approved and preserves negative/default-deny cases.
4. PHX-HARDWARE revalidates the live stack before the next scoped task; physical acceptance remains a separate owner-approved noncustomer test.

No Codex, flash, reset, live money, production migration, signer provisioning, merge, release tag, deployment, or cutover was performed.
