# PHX-HARDWARE handover — pending-clear output ordering

**Checkpoint:** 2026-11-18 UTC13  
**Role:** PHX-HARDWARE  
**PR:** [#325](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/325) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-clear-pending-remove-verify-20261118`  
**Parent:** PR #283 at `830c355376380f9b5533d5cda2558beed41a593a`  
**Exact source/test head:** `59250fd65c1b1ad721af3f6d81e7e1b721f28fd0`

## Proven defect

Both sketches set `pendingReady=true` at the start of `clearPending()`, but did not apply the resulting OFF output state before the first LittleFS `exists()` / `remove()` operation. The function can therefore enter blocking filesystem work while the relay/LED retain their previous logical ON state if called from a state where outputs were enabled.

This is a latent future-disposition hazard. In the current #283 deny-only candidate, positive coin admission is not implemented and `quarantinePending()` has no active runtime callsite.

## Correction

In both ESP32 and ESP8266:

1. Assert `pendingReady=true`.
2. Immediately call `applyOutputs()` before any LittleFS access.
3. Preserve pulse count, nonce, target and pending-ready state unless every existing candidate removal reports success and all three candidate paths are subsequently absent.
4. On any unverified removal, keep the pending state and reapply OFF.

No GPIO polarity, journal layout, quarantine format, server/API, response signature, CORE ledger or QA-owned test file changed.

## Test-first evidence

- Test-only RED commit: `c757cc5b329b4f47b6dcb99560bd6c15a96aa6f4`.
- Expected failure: [focused run #44310490239](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44310490239), job `134823032595`. The new filesystem-access ordering assertion failed on the first `/pending.dat` removal scenario; quarantine append and pending-boot suites passed.
- Firmware corrections: `fcf616e4c9b1503498e9993fc9b6d78a68817291` (ESP32) and `00d55e4ea4c1b2a5e4bda22b3fc8eb38ec8185e7` (ESP8266).
- Test diagnostic update: `59250fd65c1b1ad721af3f6d81e7e1b721f28fd0`.
- Exact-head focused CI: [run #44310755253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44310755253), job `134823962332`, checked out exact source/test SHA `59250fd...`: **SUCCESS**.
  - Quarantine append/readback: 13/13 per board.
  - Pending boot recovery: 14/14 per board.
  - Pending removal/readback: 11/11 per board.
  - ESP32 and ESP8266 source-extracted host fixtures both passed.

All three suites are **SIMULATED**. They are not physical LittleFS, GPIO, relay-contact, coin-pulse or power-cut acceptance.

## Full-build limitation

[Full build #44310490203](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44310490203) ran at the earlier test-only RED head, not the corrected source/test SHA. It was cancelled after the QA-owned controller validation failed at the legacy `Missing poll signature check`; ESP8266 compiled successfully, while ESP32 and remaining targets were cancelled. This is not full-matrix evidence and no final-head ESP target compile is claimed.

## Remaining blockers

- PHX-QA must independently review these source-linked failure vectors and replace the stale positive poll-signature assertion with negative deny-behavior tests. Firmware remains deny-only.
- PHX-MASTER must keep #325 separate from the #322 → #323 review-candidate stack unless explicitly selecting a canonical composition.
- LittleFS `exists()` still cannot distinguish every absent-path result from lower-level metadata I/O failure; this correction does not prove physical flash durability.
- Physical electrical pulse/recovery, relay polarity/contact release, 150 power cuts, 30-device/24-hour soak, independent anti-rollback witness, durable accounting/replay and reversible v1→v2 migration remain **NOT TESTED / BLOCKED**.

No flash, reset, coin, payment, signer, migration, merge, release or deployment occurred. **PRODUCTION NO-GO.**
