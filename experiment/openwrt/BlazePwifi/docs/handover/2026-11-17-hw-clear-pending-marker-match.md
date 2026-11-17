# PHX-HARDWARE — exact pending-clear evidence fence

**Date:** 2026-11-17 UTC09  
**Branch:** `phoenix/hardware-clear-pending-marker-match-20261117`  
**Base:** PR #315 exact HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`  
**Source commits:** ESP32 `0750633062aa5ed6b82cd4fc7ccc05833c2f7288`; ESP8266 `ab055040395500763a17541af2ff2183c0b39fe4`  
**Status:** DRAFT / SIMULATED / CI PENDING / PRODUCTION NO-GO

## Why this change exists

The previous `clearPending()` rejected multiple journal candidates but did not reject zero candidates. An orphan `/pending.attempt` marker with no pending journal could therefore be removed and reported as a successful clear. The marker was the only remaining durable evidence of an ambiguous coin POST attempt.

## Required invariant

Pending evidence may be cleared only when all of these conditions hold:

1. LittleFS is mounted and recovery is not already required.
2. `pendingAttemptMarkerMatches()` confirms the attempt marker binds the current RAM pulse count, nonce and target.
3. Exactly one of `/pending.dat`, `/pending.new`, `/pending.bak` exists.
4. That candidate passes the existing bounded record validator and matches the attempt marker's complete record (including checksum).
5. The pending journal removal is verified before the attempt marker is removed and verified last.

Any failure latches `journalRecoveryRequired`, leaves RAM state intact, and preserves all remaining evidence.

## Reproduction and local verification

The test-first RED used the exact old `clearPending()` body from parent PR #315 HEAD `84fe6b790139d147f330f13a40b3ae3e89a7042d`, with `fsReady=true`, `journalRecoveryRequired=false`, an attempted pending RAM event, and only `/pending.attempt` present. The old function returned success, deleted the marker, zeroed the pulse count, and left recovery false.

The patched function passed a local C++ fake-filesystem harness, 7/7:

- orphan marker only: deny, preserve marker and RAM;
- exactly one matching pending record plus marker: clear pending first, then marker;
- duplicate pending candidates: deny, preserve all;
- mismatched pending record: deny, preserve all;
- mismatched attempt marker: deny, preserve all;
- pending deletion failure: preserve marker and RAM, latch recovery;
- marker deletion failure: preserve marker, latch recovery.

This host harness is **SIMULATED**, not a repository QA suite or physical flash test. QA owns the canonical `tests/` directory and must add independent exact-source regression cases.

## Scope and boundaries

Only the ESP32 and ESP8266 firmware-owned `clearPending()` implementations changed. No shared API, financial server, schema, migration, signing, QA test, release workflow, destination COE firmware, or hardware configuration changed. `coinPostDispositionVerified()` and `acceptPollResponse()` remain default-deny. No coin admission is authorized.

## Required review and next action

- **PHX-QA:** add the listed negative/positive cases to the canonical pending-clear lab and run the exact PR head.
- **PHX-MASTER:** confirm the additional deletion precondition is consistent with Architecture Contracts §2.3.1 and §6.6.
- **PHX-CORE:** no receipt contract is assumed or changed; pending authenticated event-bound receipt/disposition work remains CORE-owned.

New exact-head GitHub Actions results are pending. The parent PR #315 focused quarantine job [#44054778537](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054778537) passed, but its Full workflow [#44054768998](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44054768998) failed at QA-owned Controller protocol parity. That failure remains an integration blocker and must not be represented as green.

Physical flash/power-cut acceptance, 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED/BLOCKED. **PRODUCTION NO-GO.**


## Follow-up: exact-one pending candidate required before POST marker (2026-11-17 UTC10)

A second source audit found that **markPendingPostAttempt()** accepted any matching candidate among **/pending.dat**, **/pending.new**, and **/pending.bak**. It did not reject a second conflicting, duplicate, or corrupt candidate. Although normal boot recovery already denies multiple candidates, the dispatch boundary must independently reject an ambiguous journal set before writing the one-shot marker and sending a coin POST.

### Test-first and correction

- Test-only commit: [dbffa86](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dbffa86cbbaa2edc7f454dd4e756f8f3216c2cfa).
- Expected RED: [focused run #44064000610](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064000610), job **133972839735**. The exact-source harness failed at **conflicting extra pending candidate denies POST marker** because the old helper found one matching **/pending.dat** and still created **/pending.attempt**.
- Firmware fix: [6100a74](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6100a74f8a94f314d99420917d51c28c75b5847d). Both boards now count all three candidate paths and require exactly one. The sole candidate must pass **readPendingFile()** and **samePendingRecord()** before the attempt marker can be written. Any missing, duplicate, conflicting, or corrupt candidate latches **journalRecoveryRequired** and denies dispatch.
- Positive recovery coverage: [f2bf146](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f2bf1465ddb95cc17a9d814cf68ba556000b9a8d) verifies a sole valid **/pending.new** or **/pending.bak** remains eligible after interrupted rotation; the exact-one rule does not incorrectly require **/pending.dat**.
- Final focused exact-head CI: [run #44064230539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064230539), job **133973625675**, **SUCCESS** at **f2bf1465ddb95cc17a9d814cf68ba556000b9a8d**. The marker lab passed **28/28 per board (56/56 total)**. Inherited quarantine 23/23 per board, poll/config, poll-window, mount/output 14/14, boot recovery 32/32, pending clear 34/34, pending write/readback 22/22 per board, and coin POST gate 10/10 per board also passed.

### Evidence limits and next action

All results are exact-source C++ host tests with fake LittleFS. They are **SIMULATED / CI VERIFIED**, not physical flash or power-cut acceptance. The full BlazePwifi build at the final head is still being evaluated; no overall Full success is claimed. PHX-QA must repair the canonical controller extractor / stale poll-signature expectation and independently rerun Full validation. PHX-CORE/MASTER review remains required for the provisional one-shot marker contract. No financial receipt authority, coin admission, migration, hardware flash, or production permission is created by this fix.


## Final Full-workflow reconciliation (2026-11-17 UTC10)

At final PR HEAD **9f6a7141fa10cd5ed90f267f389cb6212e2e7d1a**, Full run [#44064436567](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064436567) completed with overall **FAILURE**.

- Validation job **133974480063 FAILED** in the inherited controller-parity check: it still requires an active poll signature in the ESP sketches. Master PR #288 at **8bffe20f4a0ff5b722766c42d7dd3f03e97bee78**, Architecture Contracts §6.3, keeps poll admission denied until PHX-CORE publishes the canonical producer/consumer contract and PHX-QA approves exact vectors. Do not re-enable the unapproved poll formula to satisfy this stale assertion.
- All **14 target/platform jobs completed SUCCESS**: ESP8266, ESP32, Android, x86_64, Ruijie, Orange Pi Zero 3, One, PC, Zero, Zero 2, Zero 2W, PC Plus, PC2 and One Plus.
- Production APK import, production sign handoff, update bundle, v0.4 browser/Android/x86/Orange Pi/Ruijie/ESP simulations, candidate gate and prerelease/release publishing were **SKIPPED**.
- Focused hardware lab [#44064436574](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44064436574), job **133974328430**, remained **SUCCESS** at the same exact PR head: 28/28 pending-attempt marker cases per board (56/56 total), with inherited source-extracted hardware suites passing.

The Full run is not green. The target builds are CI evidence only; they do not establish physical flash durability, coin pulse acceptance, financial correctness or release readiness. No QA-owned file was changed.
