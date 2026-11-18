# PHX-HARDWARE handover — inhibit outputs before poll-fault persistence

**Date:** 2026-11-18  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hardware-fault-latch-output-inhibit-20261118  
**Draft PR:** #324 — child of #322  
**Base:** #322 exact HEAD `50d93e0de3d682550b6f02fb43484e76ad9c7e08`  
**Current PR/source-test HEAD:** `1b9c7ef244e045573c7aa7d779ad8f8313f4ebc3`

## Proven defect

Both board sketches' `loop()` keep the poll window inhibited while the synchronous HTTP call runs. After the response handler returns, the loop clears `pollIntakeSuspended`, compares the ISR edge sequence, and calls `latchPollPulseFault()` if a coin-line edge occurred.

Before this correction, `latchPollPulseFault()` set the RAM deny flags and cleared the active target, but attempted `writePollPulseFaultMarker()` before calling `applyOutputs()`. The marker path can block on LittleFS open/write/flush/readback. If the relay was accepting immediately before the edge was reconciled, it could remain at its previous state during that persistence attempt.

The current poll consumer remains hard-deny, which masks this path in the existing full-loop fixture. The new regression therefore calls the extracted production latch directly with relay and LED initially energized and records their state at the exact `/pollpulse.fault` open boundary.

## Test-first evidence

- Test-only RED source/test commit: `ba91137baa1fc7f728a69705638d7eb345e516bc`.
- Workflow wiring commit: `6c4c8549dbf0c39c6762534a75750dd641ba830a`.
- Expected RED: [Actions #44289046434](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44289046434), job `134749164608`, head `6c4c8549...`. Existing polarity, output-enable and poll-window tests passed; the new extracted latch test failed with expected exit `23` on ESP8266. The harness exits at the first board failure, so this RED is **not** claimed as two-board execution.

## Firmware correction

Both sketches now call `applyOutputs()` immediately after setting `journalRecoveryRequired=true`, `insertMode=false`, and clearing `activeTarget`, **before** calling `writePollPulseFaultMarker()`. The existing post-persistence output application remains as a final confirmation.

- ESP32 source commit: `697f348de89f9a1bc86b32d079357bf0db91715f`.
- ESP8266 source commit: `5d7f0cab9781ad7cf83ff9546e704fed42fc5e4b`.
- Final test mutation correction: `1b9c7ef244e045573c7aa7d779ad8f8313f4ebc3`.

The lab now also removes the pre-persistence `applyOutputs()` call as a deliberate mutation and requires that mutation to fail on both board extractions.

## Exact-head CI

- Focused relay/output/poll-latch [#44289412623](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44289412623), job `134750412371`: **SUCCESS** at head `1b9c7ef...`. Both ESP8266 and ESP32 poll-blocking labs pass; `defer-fault-output-inhibit` mutation is rejected on both boards with expected exit `23`. Existing poll-loop, ISR, boot-latch, pulse-capture, response-default-deny, poll-window, relay-polarity and output-enable checks pass.
- Quarantine/readback [#44289412633](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44289412633), job `134750412166`: **SUCCESS**.
- Full BlazePwifi build [#44289412659](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44289412659): overall **CANCELLED** after validation job `134750553515` **FAILED** at inherited QA-owned `Missing poll signature check`. ESP8266, Ruijie, x86_64, Orange Pi PC2 and Zero2 jobs completed SUCCESS; ESP32, Android and the remaining target jobs were CANCELLED. This is a partial matrix, not full target acceptance. Downstream simulations/import/signing/publishing were skipped. Do not weaken the deny-only consumer to satisfy the stale assertion.

## Scope and limitations

Changed only the two PHX-HARDWARE sketches, the hardware-owned `poll_loop_blocking_inhibit_lab.py`, the existing hardware-specific relay/output workflow, and this handover. No QA-owned tests, CORE ledger, shared API, financial schema, Master coordination, Release signing/publishing, COE destination, or customer state changed.

This is host-simulated ordering evidence. It does not measure GPIO voltage, relay contact release, LittleFS blocking duration under real flash contention, brown-out behavior, physical coin pulse recovery, or power-cut durability.

- Focused source tests: **CI VERIFIED / SIMULATED**
- Physical GPIO/relay acceptance: **NOT TESTED**
- 150 power cuts: **NOT TESTED**
- 30-device 24-hour soak: **NOT TESTED**
- Independent anti-rollback witness and financial migration: **BLOCKED**
- Production: **NO-GO**

## Next exact actions

1. PHX-QA independently reviews the exact PR source/test SHA and adds this ordering vector to the independent QA suite.
2. PHX-MASTER confirms #324's child placement after canonical #322; do not merge or rebase this stack automatically.
3. PHX-CORE reviews only if the persistent poll-fault hold changes the event-disposition/reconciliation contract.
4. Continue with hardware-owned work only after refreshing all live branch heads and assignments.

No flashing, reset, real coin, live money, migration, signer provisioning, merge, release or deployment occurred.
