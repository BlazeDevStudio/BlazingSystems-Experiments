# PHX-HARDWARE UTC21 — active-high pulse ended before the next sample

**Protocol:** BLAZE-COMMS/1  
**Task:** #177 / cleanup-first #266 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `b29de082fd847c5873aa99b1e05bbde28428a8c4`  
**Scope:** Hardware-owned host regression only; no production firmware or shared API changed.

## Gap

The poll-drain suite already exercised the active-low case where the input briefly becomes active during the quiet-drain read, then returns idle before the ordinary `loop()` sample. That case must not disappear silently: because no pending pulse can be durably attributed, firmware must latch an unresolved-ingress fault and keep outputs denied.

The active-high path had coverage for a pulse that remained visible through the ordinary sample, and for an ISR edge during drain, but not this exact no-ISR / ended-before-sample combination.

## Change

`poll_loop_blocking_inhibit_lab.py` now adds a dedicated active-high scenario using the actual extracted board `loop()`, `coinLineIdle()`, drain, fault-latch and output helpers:

- The active-high GPIO reads HIGH for the drain observation, then the pulse ends before the ordinary sample.
- No ISR edge is injected; the test isolates the GPIO-sampled path.
- The poll must not start, no pending coin may be fabricated, and the unresolved pulse must be persisted as `COIN_INGRESS_UNRESOLVED pulses=1`.
- Relay and LED must be OFF before either persistence writer is entered and remain OFF.
- The test executes against both ESP8266 and ESP32 source extraction.

A fail-open mutation makes the active-high line appear idle regardless of the raw pin. The test must reject that mutation at expected exit 57 on both board builds.

The assembler now accepts an explicit extracted `idle_source` so the mutation exercises the production helper rather than changing the test stub.

## Evidence boundary

This is a source-extracted host simulation. It is not a physical coin-slot, electrical pulse, relay, LittleFS power-loss, 150-power-cut or 30-device soak test.

- Source/test commit: `b29de082fd847c5873aa99b1e05bbde28428a8c4`
- Exact-head GitHub Actions: pending observation at handover creation; record only returned terminal job IDs in the PR/checkpoint.
- No production `.ino`, CORE contract, financial ledger, witness, QA-owned fixture, release workflow or COE migration was changed.
- No flash, reset, customer device, live money, migration, merge, signing, tag or deployment was performed.

## Next action

Verify the focused quarantine workflow at the exact source/test SHA and latest documentation head. PHX-QA may independently review the new negative mutation; PHX-MASTER should refresh the canonical #327 head and #323 → #326 → #327 pins. Keep Full validation, physical acceptance and production gates separate.
