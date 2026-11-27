# PHX-HARDWARE UTC10 — pending-journal recovery promotion guard

**Role:** PHX-HARDWARE  
**Task:** hardware #177 / cleanup-first #266  
**PR:** [#359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/359), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-pending-recovery-promotion-guard-20261127-utc10`  
**Base:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18@9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Source/test SHA:** `bdad70fa77f51421cb7a6f01d89bd2b7ea9bdc3f`  
**Focused exact-head run:** [#45986402635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45986402635), job `140463042542`, PASS.

## Defect and change

Both ESP8266 and ESP32 `loadPending()` previously selected a valid `/pending.new` or `/pending.bak` fallback, removed `/pending.dat` without preserving it, ignored the promotion rename result, published recovered state to RAM before promotion was known to succeed, and could report success despite a failed promotion.

The Hardware-owned correction:

- Treats an existing canonical `/pending.dat` plus a selected fallback as ambiguous; preserves both files, sets `fsReady=false` and `pendingReady=true`, and returns false.
- Checks fallback rename success. A failed promotion preserves the fallback and fails closed.
- Publishes `pendingSequenceState` only after successful promotion.
- Fails closed when journal files exist but none validate, when initial empty-journal persistence fails, and when legacy journal migration persistence fails.
- Does not add a clear/disposition callsite, response consumer, coin admission, relay admission, financial state, or shared API.

## Exact test evidence

The new `pending_recovery_promotion_lab.py` extracts the actual `loadPending()` function from both board sketches, compiles it with a deterministic LittleFS stub, and injects failures.

At exact source/test SHA `bdad70fa77f51421cb7a6f01d89bd2b7ea9bdc3f`, focused run #45986402635 passed:

- 11 recovery scenarios per board.
- Two rename-failure cases per board.
- Canonical/fallback ambiguity preserved without deleting either candidate.
- Invalid-only journal fails closed.
- Empty-journal initial write failure fails closed.
- Legacy migration persistence failure fails closed.
- Eight source mutations rejected per board; 16 total.

Log marker: `PENDING_RECOVERY_PROMOTION_LAB_PASS boards=ESP8266,ESP32 mutations_rejected=16`.

### Test-first and harness history

- [#45985812211](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45985812211) failed against the original unguarded source at the new invalid-candidate guard assertion; this was the expected source RED.
- Intermediate runs [#45985936904](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45985936904), [#45985941053](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45985941053), and [#45986064897](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45986064897) exposed test-harness source-matcher defects. Those tooling failures are retained, not reclassified as firmware failures.
- Corrected harness passed at [#45986201309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45986201309), then final exact source/test SHA passed at #45986402635.

## Integration status

Push Full [#45986402891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45986402891) passed CI-0701 but validation stopped at the mandatory handover-freshness gate because canonical handovers had not yet been synchronized. Its ESP8266 target job passed; other target jobs were still running at the last read. A post-handover exact-head Full rerun is required. No target-count claim is made.

The active v0.6 poll-before-sample P0 remains unresolved. This task improves journal recovery safety; it does not fix the 3,500 ms synchronous poll pulse-loss path. PHX-CORE owns authenticated register/poll and receipt/disposition semantics, PHX-QA owns independent semantic tests, and PHX-MASTER owns global assignments and integration sequencing.

## Evidence boundary

Host/source-extracted tests are SIMULATED / CI VERIFIED only. Physical LittleFS recovery, electrical pulse/recovery, relay contact behavior, 150 power cuts, 30-device/24-hour soak, protected signer/witness, durable accounting/replay, and v1-to-v2 migration remain NOT TESTED or NOT ACCEPTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No physical flashing, device reset, live money, production migration, merge, release tag, deployment, or COE source change occurred.

## Next exact action

Synchronize this exact source/test SHA into the canonical project handover and live state, rerun the Full workflow on the resulting documentation HEAD, then request independent QA review of the new failure-injection lab. Keep PR #359 DRAFT and unmerged.
