# PHX-HARDWARE UTC16 — pending-journal persistence I/O failure guard

**Task:** Hardware subtask under issue [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**PR:** [#363 — Fail closed on pending-journal persistence I/O errors](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/363)  
**State:** OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-pending-persist-io-failure-guard-20261127-utc16\`  
**Base:** PR #362 branch at \`eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd\`  
**Source/test commit:** \`aa49e7fce2739e33171d53ec61149685cf9b0c7a\`  
**Test-first commit:** \`f98c5cb329e647ca48db8efdefe9e0bd065ba0d9\`

## Scope and ownership

Hardware-owned ESP8266/ESP32 pending-sequence persistence and Hardware-owned source-extracted tests/workflow only. No shared CORE API, QA-owned assertion, finance, receipt/disposition, signer/witness, migration, COE, production or release behavior changed.

## Proven defect

Both sketches' \`persistPendingSequence()\` previously ignored return values from stale \`/pending.bak\` removal, \`/pending.dat\` → \`/pending.bak\` rotation, and post-promotion backup removal. The writer could continue and publish in-memory sequence state even when a filesystem cleanup/rotation operation failed.

The existing \`loadPending()\` now rejects multiple candidates on reboot, but the writer also needs to refuse success whenever the journal rotation is incomplete.

## Source correction

Both ESP8266 and ESP32 implementations now:

1. Abort and log if an existing stale backup cannot be removed.
2. Abort and log if canonical-to-backup rename fails; do not attempt new-file promotion.
3. Promote \`/pending.new\` only after the prior canonical rotation succeeds.
4. On failed promotion, attempt backup restoration only when the canonical path is absent; log restore failure and return false either way.
5. Abort and log if post-promotion backup cleanup fails.
6. Update \`pendingSequenceState\` only after all required rotation/cleanup operations succeed.

Callers of \`savePending()\`, initial journal creation, legacy migration and \`clearPending()\` already fail closed on false; this activation re-audited those callsites on both boards. No positive coin admission or relay enable was added.

## Exact CI evidence

### Focused Hardware workflow

- Test-first expected RED at old source: [run #46036796001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46036796001), job \`140634121963\`. New source-contract assertion failed because the old writer did not check both backup-removal results. This is the intended baseline, not a passing result.
- Corrected exact-head focused run: [#46037240744](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46037240744), job \`140635630378\`: **PASS**.
- Append-only ledger prefix guard and its own failure-injection test passed.
- Existing pending recovery lab passed: ESP8266 and ESP32 each \`scenarios=15\`, \`ambiguous_preservation=6\`, 18 total unsafe mutations rejected.
- New persistence lab passed:
  - ESP8266: \`PENDING_PERSIST_FAILURE_PASS scenarios=13\`
  - ESP32: \`PENDING_PERSIST_FAILURE_PASS scenarios=13\`
  - Six unsafe source mutations rejected per board; \`mutations_rejected=12\` total.
- Injected cases include open failure, short write, failed cleanup of \`pending.new\`, stale-backup removal failure, canonical-to-backup rename failure, new-to-canonical promotion failure, successful/failed backup restoration, and final backup-cleanup failure.

### ESP32 Mbed TLS 3/4

[Run #46037240677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46037240677): **3/3 PASS** at source/test SHA \`aa49e7fce2739e33171d53ec61149685cf9b0c7a\`.

- Source contract: job \`140635630633\`
- Arduino ESP32 core 3.3.13: job \`140635630676\`
- Arduino ESP32 core 4.0.0: job \`140635630360\`

### Inherited / pre-sync failures

- Native synthetic [#46037240701](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46037240701), job \`140635630197\`: **FAIL** at QA-owned \`tests/v060_vendo_sequence_contract.py:18\`, which requires the literal \`if(any) return false;\`. Hardware did not modify the QA-owned assertion or weaken the explicit fail-closed branch.
- Full pre-sync [#46037240708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46037240708), validation job \`140635887241\`: **FAIL** at the mandatory handover freshness gate because this source change had not yet been recorded in canonical handovers. This is not a controller-parity or product-validation result. A fresh Full run is required after this documentation commit.

## Limits and acceptance

The C++ fake-LittleFS harness is SIMULATED / CI VERIFIED only. It does not establish actual LittleFS power-loss semantics, flash wear behavior, electrical pulse recovery, relay acceptance, or durable hardware guarantees.

- Physical LittleFS acceptance: NOT TESTED.
- 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Electrical pulse/recovery: NOT TESTED.
- Independent signer/witness, durable accounting/replay and v1→v2 migration: NOT ACCEPTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO-GO.

No flash, reset, customer-money test, migration, merge, release, or deployment was performed.

## Next exact action

- PHX-MASTER records #363 and its #362 → #361 → #359 dependency in role/integration matrices.
- PHX-QA reviews the new source-extracted persistence scenarios and reconciles the inherited PAY-0745 literal assertion semantically.
- PHX-CORE retains ownership of authenticated register/poll and receipt/disposition contracts.
- PHX-HARDWARE keeps coin/relay admission denied and proceeds only with reversible firmware-owned work.
