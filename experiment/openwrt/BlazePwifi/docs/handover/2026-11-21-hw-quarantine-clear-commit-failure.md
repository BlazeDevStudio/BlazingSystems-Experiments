# PHX-HARDWARE handover — quarantine clear commit verification

**Updated:** 2026-11-21T12:52:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Exact source/test SHA:** `cfdf2053b50c54d8c0fe52b1338e9790dff8f327`

## Finding

The older #283 sketches had a weak pending-clear transition even though `quarantinePending()` already returned before clearing when the quarantine append failed:

- `clearPending()` was `void`.
- It cleared RAM state before attempting to remove LittleFS pending candidates.
- It removed `/pending.dat`, `/pending.new`, and `/pending.bak` without checking the remove result or verifying absence.
- `quarantinePending()` called `clearPending(); return true;`, so it could report successful quarantine even when pending-journal deletion failed.
- The old append/readback lab stub always made clear succeed and did not exercise this failure boundary.

This was a source-level helper defect in the parallel #283 draft. `quarantinePending()` still has no active callsite in either sketch; this change does not wire or authorize a quarantine lifecycle.

## Correction

Both ESP32 and ESP8266 sketches now have identical `bool clearPending()` behavior:

1. Require a ready filesystem and bounded, nonempty pending identity.
2. Require exactly one of `/pending.dat`, `/pending.new`, or `/pending.bak`.
3. Read and validate that candidate through the existing `readPendingFile()` helper and match pulses, nonce, and target to the current RAM event.
4. Remove only that exact candidate and verify it is absent.
5. Clear RAM state only after verified deletion.
6. On ambiguity, read failure, remove failure, or failed absence verification, retain the RAM event, set `fsReady=false`, keep `pendingReady=true`, and return false.

`quarantinePending()` now returns the `clearPending()` result rather than reporting success unconditionally. Append failure still returns before any pending clear.

## Exact CI and failure injection

- Test-first RED: [run #44905663283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44905663283), job `136850563625`, failed because the production helper was still `void clearPending()` and the required bool commit contract was absent.
- Exact source/test GREEN: [run #44905914542](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44905914542), job `136851325578`, **SUCCESS** at `cfdf2053b50c54d8c0fe52b1338e9790dff8f327`.
- Existing append/readback lab: 13/13 scenarios on each board.
- Existing pending-journal boot lab: 14/14 scenarios on each board.
- New clear/commit lab: 10/10 scenarios on each board.
- Failure injection: append denied; pending delete failure; remove falsely reports success while file remains; missing/multiple candidates; mismatched record; read failure; filesystem unavailable; zero-pulse state.
- Mutation: changing `return clearPending();` to `clearPending(); return true;` is rejected on both boards (expected exit 3).

The new lab source-extracts the actual `clearPending()` and `quarantinePending()` bodies. Its `readPendingFile()` and `appendQuarantineRecord()` boundaries are controlled test doubles; the existing labs separately exercise the production parser and append/readback helpers. All results are **SIMULATED / CI VERIFIED**, not flash durability evidence.

The first two post-fix attempts exposed test-harness compatibility mistakes (a stale void stub, then a stub copied with out-of-scope marker variables); both were corrected before the final exact-head green run.

## Scope and boundaries

- Changed both Hardware-owned firmware sketches, the existing append/readback lab stub, the new clear/commit lab, and its focused workflow wiring.
- No active quarantine callsite was added.
- No automatic coin POST/retry/replay, positive poll admission, controller response signature, relay enablement, financial API, ledger migration, signer, witness, or production format was changed.
- PR #283 remains a separate main-based parallel draft. It is not part of the #327 → #330 → #332 → #333 stack; no cherry-pick, rebase, merge, or cross-branch transplant was performed.
- No physical flashing, device reset, coin, relay, customer, or production operation was performed.

## Next exact actions

1. PHX-QA independently review the source-extracted clear/commit failure cases at the exact source/test SHA above.
2. PHX-MASTER refresh the stale #283 pointer in `ROLE_ASSIGNMENTS.md` and keep #283 separate from the #327 lineage until an explicit stack decision.
3. PHX-CORE must publish the approved event-bound register/poll/coin receipt contract and canonical vectors before any quarantine callsite or positive admission is considered.
4. PHX-HARDWARE must obtain new noncustomer LittleFS power-cut evidence before claiming hardware durability.

**Disposition:** focused CI verified; Full integration and physical durability remain separate gates; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO.
