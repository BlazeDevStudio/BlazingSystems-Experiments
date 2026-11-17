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
