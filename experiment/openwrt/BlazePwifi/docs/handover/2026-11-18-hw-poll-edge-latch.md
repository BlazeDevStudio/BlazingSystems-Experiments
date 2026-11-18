# PHX-HARDWARE — blocking-poll coin-edge fault latch handover

**Date:** 2026-11-18  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hardware-poll-edge-latch-20261118  
**Draft PR:** #320 — child of #317  
**Parent base at branch creation:** fce915c1167fc43c6936f3594ae9efce376b711f  
**Last source/test HEAD before this handover:** bbbab4317a758851d50d8ab90597be1c264f3117

## Scope

This child ports only the hardware-owned ISR edge-capture and persistent poll-fault latch from the divergent #318 candidate onto the current #317 parent. It does not rebase or cherry-pick #318. The existing 250 ms post-inhibit quiet window, pending attempt marker, exact pending-record matching, output gate and default-deny poll response remain inherited from #317.

## Firmware changes

Both sketches now:

- Declare a volatile 32-bit active-edge sequence counter before the ISR.
- Use `ICACHE_RAM_ATTR` on ESP8266 and `IRAM_ATTR` on ESP32; ISR work is limited to incrementing the counter.
- Detach the prior coin-pin interrupt and attach the configured active edge after runtime pin changes.
- Snapshot the edge sequence before the poll window and compare after synchronous poll response handling.
- On any observed edge, set `journalRecoveryRequired`, clear insert/target state, and inhibit outputs.
- Write `/pollpulse.fault` with edge count and timestamp, flush/close, and read back exact size and bytes.
- Treat marker presence at boot as a deny latch; partial/corrupt marker contents are not auto-cleared.

The marker is not a financial receipt, replay token or authorization. No positive poll or coin POST disposition was enabled.

## Exact source commits

- ESP32 ISR/latch source: 4c3ddcfcd67aa4d3870486e1554af491bf8b6c64
- ESP8266 ISR/latch source: 1bf8de1c3965ab4ac18c1daff29b768b1a51bc6f
- ESP8266 pending-record declaration fix: e88c2b5c98a005bfc0f594b7d0cf741b3fdaaac7
- ESP32 pending-record declaration fix: b6e9cfa75105e6cd29c29b93266255d3110c8296
- Poll-loop lab now extracts actual `sampleCoinPulseEdge()`: bf7e8b470a7e8ad34dae37ca9b6be1a3d3176c7e
- Mount lab now extracts actual `loadPollPulseFaultLatch()` and tests its boot deny behavior: bbbab4317a758851d50d8ab90597be1c264f3117

## CI evidence

### Focused poll-edge workflow

[Run #44225475672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225475672)  
Exact source/test SHA: `b6e9cfa75105e6cd29c29b93266255d3110c8296`  
Result: **PASS — SIMULATED ONLY**

Verified on ESP8266 and ESP32:

- Poll-window timeline guard passed.
- 7/7 fault-marker scenarios and 7/7 existing poll-loop guard scenarios.
- ISR edge-snapshot race test passed.
- 11 targeted mutations rejected per board, including missing interrupt attachment, no-op ISR, ignored edge delta, missing marker write and missing boot latch.
- Poll response 11/11; strict root JSON 13/13; coin POST ACK root-status 4/4; coin disposition default-deny 4/4.
- Debounce floor 8/8; 250 ms poll-window 13/13; blocking-poll relay inhibit 1/1.
- The final-quiet-sample mutation was rejected at the exact 250 ms boundary.

The branch HEAD later advanced only for the independent mount-lab harness correction; firmware and poll-lab inputs were unchanged after this tested source SHA.

### Quarantine/readback workflow

- Earlier run [#44225479563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225479563) failed because the existing mount lab did not extract the newly called `loadPollPulseFaultLatch()`. The lab was corrected at `bbbab431...`; replacement run [#44225565795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225565795) was still running at handover.
- Its exact-source quarantine compile step passed; pulse-capture step was still in progress.

### Full build and validation

[Run #44225566023](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44225566023) was running at handover. Its QA validation job failed with the inherited assertion:

`Missing poll signature check`

This is the known stale positive poll-signature expectation. Do not reintroduce a positive or keyless poll path to satisfy it. PHX-QA must replace it with exact-source default-deny assertions. ESP32/ESP8266 build jobs were still running.

The earlier full run at `bf7e8b4...` also exposed a missing semicolon around the inserted `PendingRecord` declaration; both board declarations were corrected at `e88c2b5...` and `b6e9cfa...`. The corrected full compile has not yet completed at this handover.

## Important unresolved durability limitation

If `/pollpulse.fault` cannot be created/read back (for example, filesystem unavailable or storage failure), the current boot remains fail-closed through `journalRecoveryRequired`, but there is no independent persistent fallback in this child. A reboot could lose that RAM-only hold if no marker and no pending record survive. This is explicitly **not** accepted as durable fault recovery. PHX-MASTER/PHX-CORE must approve a separate durable fallback/witness design, and PHX-QA must failure-inject it before production acceptance.

## Proposed stack direction — awaiting Master ACK

Proposed canonical hardware sequence: #314 → #315 → #317 → #320.

- Keep #283 separate as an audit candidate; its unique mount/clear labs and QA-owned test edits need PHX-QA review before selective port.
- Keep #318 as a divergent historical candidate; do not rebase, cherry-pick or merge it wholesale.
- #239 and #254 remain separate deny/auth labs.
- No shared poll/receipt API was changed.

## Evidence classification

- Focused host regressions: **CI VERIFIED / SIMULATED**
- Full current build: **INCOMPLETE**
- Full validation: **FAILED** at stale QA poll-signature assertion
- Physical coin acceptor / relay / electrical behavior: **NOT TESTED**
- 150 power cuts: **NOT TESTED**
- 30-device, 24-hour soak: **NOT TESTED**
- Hardware accepted: **NO**
- Production ready: **NO-GO**

No flashing, resets, live money, customer coins, signing, production migration, release, merge or deployment occurred.

## Next exact actions

1. Finish current quarantine and target-build workflows on the latest branch head.
2. PHX-QA replaces the stale positive poll-signature assertion with default-deny source assertions and independently reviews this child.
3. PHX-MASTER ACKs or revises the proposed #314 → #315 → #317 → #320 sequence.
4. PHX-CORE/MASTER define the durable fallback for marker-write failure; PHX-QA adds reset/power-loss failure injection.
5. Do not promote this branch to hardware accepted until physical pulse/recovery and full release gates are independently evidenced.
