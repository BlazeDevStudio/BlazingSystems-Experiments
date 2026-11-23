# PHX-HARDWARE UTC21 — active-high pulse ended before the next sample

**Protocol:** BLAZE-COMMS/1  
**Task:** #177 / cleanup-first #266 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `d68c141592689fcca40051d16cddfc0ecb3a5f58`  
**Scope:** Hardware-owned host regression only; no production firmware or shared API changed.

## Gap

The poll-drain suite already exercised the active-low case where the input briefly becomes active during the quiet-drain read, then returns idle before the ordinary `loop()` sample. Because no pending pulse can be durably attributed, firmware must latch an unresolved-ingress fault and keep outputs denied.

The active-high path had coverage for a pulse that remained visible through the ordinary sample, and for an ISR edge during drain, but not this exact no-ISR / ended-before-sample combination.

## Change

`poll_loop_blocking_inhibit_lab.py` now adds a dedicated active-high scenario using the actual extracted board `loop()`, `coinLineIdle()`, drain, fault-latch and output helpers:

- The active-high GPIO reads HIGH for the drain observation, then the pulse ends before the ordinary sample.
- No ISR edge is injected; the test isolates the GPIO-sampled path.
- The poll must not start, no pending coin may be fabricated, and the unresolved pulse must be persisted as `COIN_INGRESS_UNRESOLVED pulses=1`.
- Relay and LED must be OFF before either persistence writer is entered and remain OFF.
- The test executes against both ESP8266 and ESP32 source extraction.

A fail-open mutation makes the active-high line appear idle regardless of the raw pin. The test rejects that mutation at expected exit 57 on both board builds.

The assembler accepts an explicit extracted `idle_source` for the mutation. Its optional parameter was placed last to preserve all existing positional mutation calls.

## Exact CI evidence

At source/test SHA `d68c141592689fcca40051d16cddfc0ecb3a5f58`:

- Quarantine PR [run #44823079264](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44823079264), job `136588658066`: **SUCCESS**.
- Relay/output PR [run #44823079237](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44823079237):
  - job `136588658414`: **SUCCESS**;
  - ESP32 boot-polarity job `136588658917`: **SUCCESS**.
- Both focused logs contain `POLL_ABORT_ACTIVE_HIGH_PULSE_ENDED_BEFORE_SAMPLE_PASS` and `MUTATION_REJECTED active-high-pulse-misread-as-idle expected_exit=57` for ESP8266 and ESP32.
- Both focused workflows explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0` and `PHYSICAL_POWER_CUT_VERIFIED=0`.

### Corrected first attempt

The first source/test commit `b29de082fd847c5873aa99b1e05bbde28428a8c4` passed the new active-high case on ESP8266, then exposed a lab-harness regression: adding `idle_source` as the third positional argument shifted existing mutation calls, causing compile errors before the rest of the suite. The failed focused jobs were quarantine run [#44822883874](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44822883874), job `136587998148`, and relay run [#44822884668](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44822884668), job `136587994759`. The correction moved `idle_source` to the final optional parameter in source/test commit `d68c1415...`; the exact-head focused jobs above then passed.

### Full validation

Full build [run #44823079422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44823079422), validation job `136588797410`: **FAILURE** at the inherited QA-owned controller assertion:

`Missing poll signature check`

The current main register/poll producer does not emit the approved controller `response_sig`. In Full run #44823079422, 11 of 14 target/Android jobs completed successfully; ESP32, x86_64 and Android were cancelled after the validation failure. No overall Full-matrix pass is claimed. Do not weaken default-deny or invent a signature to satisfy the stale assertion.

## Evidence boundary

This is a source-extracted host simulation. It is not a physical coin-slot, electrical pulse, relay, LittleFS power-loss, 150-power-cut or 30-device soak test.

- No production `.ino`, CORE contract, financial ledger, witness, QA-owned fixture, release workflow or COE migration was changed.
- No flash, reset, customer device, live money, migration, merge, signing, tag or deployment was performed.

## Next action

PHX-QA should replace the stale positive poll-signature assertion with source-exact negative/default-deny tests until CORE publishes the authenticated response contract. PHX-MASTER should reconcile exact #323 → #326 → #327 heads in the canonical assignment and integration matrix. Keep Full validation, physical acceptance and production gates separate.


## UTC22 follow-up — active-low missed-sample failure injection

The full poll-loop suite already contained a positive active-low pulse-ended-before-sample case, but only the dedicated active-high scenario had a polarity-specific fail-open mutation. This left the active-low idle mapping without an isolated sensitivity check for the same P0 ingress path.

Added a dedicated active-low scenario using the extracted production `loop()`, drain, `coinLineIdle()`, fault-latch and output helpers. It requires no HTTP poll, no fabricated pending coin, a durable `COIN_INGRESS_UNRESOLVED pulses=1` marker, and relay/LED OFF before either persistence writer is entered.

The paired failure injection changes the active-low idle mapping to always report idle. The test must reject that mutation with expected exit `58`. The same positive and negative cases run against both ESP8266 and ESP32 source extraction.

**Scope:** test-only in `poll_loop_blocking_inhibit_lab.py`; no production `.ino`, GPIO, receipt contract, finance, QA-owned fixture, or release workflow changed. Exact-head Actions evidence is pending at the source/test commit; this note does not claim a pass before those jobs complete.
