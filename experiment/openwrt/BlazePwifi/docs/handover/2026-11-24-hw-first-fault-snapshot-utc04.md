# PHX-HARDWARE — first-fault snapshot regression (UTC04)

**Date:** 2026-11-24  
**Role:** PHX-HARDWARE  
**Task:** #177 / Master Architecture Contracts §6.50  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f` (#347)  
**Source/test SHA:** `8dd8b12c3c32da76c7a087c44f3cbb32d5ac6a64`  
**Final documentation SHA:** pending this handover commit.

## Scope and finding

Master §6.50 identifies a verification gap: the dual-store lab did not exercise the source-extracted `sampleCoinPulseEdge()` path, and the poll-loop lab did not explicitly assert that later ISR edges leave the already-persisted first-fault snapshot unchanged.

The production sketches already implement the intended sticky behavior in this source stack. This task adds regression coverage; it does **not** claim a newly discovered production firmware defect.

## Changes at source/test SHA

No ESP8266 or ESP32 `.ino` file, persistence schema, financial API, relay policy, coin authority or shared contract was changed.

1. **Poll-loop source extraction**
   - Added a two-board scenario that calls the actual source-extracted `sampleCoinPulseEdge()`.
   - First fault uses `pendingPulses + unseenEdges`, persists the initial marker, and turns relay/LED outputs off.
   - Injects three later ISR edges and samples again after `journalRecoveryRequired` is already sticky.
   - Asserts the LittleFS first-fault marker and backup first-write observation remain unchanged; pending pulse count/target/nonce stay preserved; no save, POST or clear is attempted; output remains off and `canAttemptCoinPost()` remains false.
   - Failure injection removes the sticky-latch guard. The scenario must reject the mutation with exit 90 on both boards.

2. **Actual dual-store source extraction**
   - The dual-store lab now reads the persisted `PollFaultRecord` from the ESP32 NVS blob or ESP8266 EEPROM image.
   - Latches a first snapshot of 4, then attempts a later latch with 9.
   - Asserts the original record bytes and `pulseEdges` remain unchanged, no additional commit occurs, and journal recovery/output admission remain denied.
   - Board-specific overwrite mutations must be rejected with exit 74 on both boards.

3. **Fixture reset**
   - Added first-write observation state to the poll-loop fixture and reset it with the existing scenario reset helper. The actual EEPROM/NVS persistence helper remains source-extracted and is tested separately by the dual-store lab.

## Exact-head CI evidence

All runs below use source/test SHA `8dd8b12c3c32da76c7a087c44f3cbb32d5ac6a64`.

- Quarantine push [run #45328971371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45328971371), job `138225236386`: **PASS**.
- Quarantine PR [run #45328981016](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45328981016), job `138225265588`: **PASS**.
  - Dual-store first-latch snapshot stable on ESP32 and ESP8266.
  - Both first-latch overwrite mutations rejected (exit 74).
  - Poll-loop later-ISR snapshot stable on ESP32 and ESP8266.
  - Both sticky-latch re-entry mutations rejected (exit 90).
- Relay PR [run #45328980994](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45328980994):
  - `source-output-polarity`, job `138225264985`: **PASS**.
  - `esp32-boot-polarity`, job `138225265252`: **PASS**.
- Full BlazePwifi PR [run #45328980967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45328980967):
  - 13 firmware target jobs plus Android: **14/14 PASS**.
  - Validation job `138225364556`: **FAIL**, exact error `Missing poll signature check`.
  - Signing, candidate, simulation-dependent and publication stages were skipped. This remains the CORE producer / QA assertion contract blocker; no signature was invented and no default-deny check was weakened.

The older failed test-harness attempts at intermediate commits are not the final result. The exact-head runs above are the accepted evidence for this source/test SHA.

## Interpretation and safety boundary

The V1 `PollFaultRecord.pulseEdges` value is a **first-latch snapshot / lower bound**, not a live cumulative counter or exact total. Later ISR edges may be absent from the stored value. It must never be used to credit time, settle/refund a coin, infer denomination, or clear pending evidence. No completeness flag or schema change is introduced.

This is hosted source-extracted simulation / CI only. Physical coin acceptor, relay, electrical pulse, LittleFS power-cut, 150 controlled power cuts, and 30-device/24-hour soak remain **NOT TESTED**. The new tests do not establish HARDWARE ACCEPTED or PRODUCTION READY.

## Coordination requests

- **PHX-QA:** independently review the two-board first-latch and mutation assertions at the exact source/test SHA.
- **PHX-CORE:** confirm the V1 `pulseEdges` diagnostic is never interpreted as a financial quantity or used for settlement/credit.
- **PHX-MASTER:** refresh `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` to pin this #349 source/test SHA and the handover docs SHA; keep #349 as an unmerged child of #347 and reconcile its stack ancestry before integration.

## Next exact action

PHX-MASTER refreshes the #349 source/test/docs pins; PHX-QA and PHX-CORE return independent reviews. Full integration remains blocked until CORE publishes the authenticated register/poll response envelope and QA approves matching golden vectors. Hardware stays deny-only.
