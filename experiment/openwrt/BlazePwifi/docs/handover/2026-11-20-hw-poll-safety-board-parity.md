# PHX-HARDWARE — poll-safety cross-board parity guard

**Date:** 2026-11-20 UTC17 (2026-11-21 Asia/Manila)  
**Role:** PHX-HARDWARE  
**Tasks:** #177 / cleanup-first #266 / active child PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Stack:** #323 → #326 → #327; #327 base is #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `d4f7df4e8d286fcc52bbb4a38af9aa9aff4ad3c1`  
**PR state at source verification:** OPEN / DRAFT / UNMERGED.

## Selected bounded task

The ESP8266 and ESP32 poll/coin-ingress control-flow labs already compile the same safety functions independently from each board sketch. They did not have a single explicit cross-board parity gate for that critical helper set. A future board-only edit could therefore pass its own host scenario while silently diverging from the other board.

This change adds a parity guard to the existing Hardware-owned poll-loop lab. It reuses the shared `firmware_lab_source.extract_function`; no second C++ parser was introduced.

## Source change

Only this source/test file changed in the source commit:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

The lab now compares normalized extracted bodies for 11 shared helpers:

- `coinEdgeISR`
- `snapshotCoinEdgeSequence`
- `boundedCoinDebounceMs`
- `canStartPoll`
- `applyOutputs`
- `beginPollWindow`
- `sampleCoinPulseEdge`
- `latchPollPulseFault`
- `quarantineCoinIngressTransition`
- `handlePollDrainAbortAfterSample`
- `reconcileUnobservedCoinEdges`

Whitespace is normalized; comments and executable tokens remain part of the comparison. The check fails with the exact divergent helper names.

A built-in failure injection mutates the ESP32 `applyOutputs()` journal-fault guard from `!journalRecoveryRequired` to `journalRecoveryRequired`. The parity gate must reject that simulated fail-open drift.

No production `.ino`, relay/coin behavior, GPIO, API, finance, persistence format, schema, QA-owned test, signing, or Release workflow changed.

## Exact GitHub Actions evidence

All runs below use exact source/test SHA `d4f7df4e8d286fcc52bbb4a38af9aa9aff4ad3c1`.

- Quarantine push [#44786335271](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786335271), job `136462068315`: **SUCCESS**. Logs contain:
  - `POLL_SAFETY_BOARD_PARITY_PASS 11/11 normalized helpers`
  - `POLL_SAFETY_BOARD_PARITY_MUTATION_REJECTED ESP32_applyOutputs_journal_fault_guard`
- Quarantine PR [#44786347758](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786347758), job `136462110901`: **SUCCESS**.
- Relay/output PR [#44786347933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786347933):
  - job `136462111525`: **SUCCESS**
  - ESP32 boot-polarity job `136462112148`: **SUCCESS**
- Full BlazePwifi PR [#44786347685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44786347685): **QUEUED** at handover creation; no terminal result is claimed here.

## Evidence limits and release status

- Shared poll-helper parity regression: **CI VERIFIED**.
- Poll-loop and failure-injection scenarios: **SIMULATED / CI VERIFIED**.
- Physical coin acceptor, relay contacts, electrical pulse/recovery and actual board behavior: **NOT TESTED**.
- 150 controlled power cuts and 30-device / 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer / independent witness: **NOT ESTABLISHED**.
- Financial v1→v2 migration and durable accounting/replay: **NOT TESTED / NOT ESTABLISHED**.
- Independent QA and release signoff: **PENDING**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Coordination / next exact actions

1. **PHX-QA:** retain ownership of the inherited positive poll-signature assertion; replace it with source-exact default-deny validation after CORE publishes the approved contract. Do not ask Hardware to add a fake positive signature.
2. **PHX-CORE:** publish canonical authenticated register/poll response bytes and event-bound receipt golden vectors.
3. **PHX-MASTER:** refresh the stale #327 active-head row in `coordination/phoenix/ROLE_ASSIGNMENTS.md` to the live PR head after this handover commit; preserve #323 → #326 → #327 ancestry.
4. **PHX-HARDWARE:** keep the parity gate in the existing focused workflow and continue only with owned firmware/lab work.
5. Keep physical acceptance, signing, finance migration, release, merge and deployment gates closed pending independent evidence and authorization.

No Codex was used. No physical flashing, reset, live money, production migration, merge, signing, release tag, or deployment was performed.
