# PHX-HARDWARE handover — C++ digraph-aware inactive-constant extraction

**Date:** 2026-11-22 UTC19  
**Task:** PHX-HW-DIGRAPH-PREPROCESSOR-20261122T19Z  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments (repository ID 1389289885)  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hardware-339-fixture-lexical-port-20261122-utc10`  
**PR:** [#341 — Port lexical-safe dual-store constant extraction](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/341) — OPEN / DRAFT / UNMERGED  
**Parent:** #339 exact HEAD `b3e1558845ae2cd508e42d0d4722fdcd28293e32`; #339 is a child of #338 exact HEAD `1a6a7cacf95722a78330d70de057e858143520f2`.

## Scope and defect

The Hardware-owned `constants()` fixture extractor already masks comments, literals, identifier-substring decoys and literal inactive `#if/#elif` branches. Its directive recognizer accepted only `#`, but C++ also permits the `%:` digraph as the preprocessing directive marker. A `static const` declaration inside a `%:if 0` branch could therefore be selected as an active persistence constant by the host harness.

No production sketch or shared controller/financial API was changed.

## Test-first evidence

- **RED test-only commit:** `8205b21e08230249983dcea2a8115c8627151435`.
- **Expected RED:** [Quarantine run #45059942489](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45059942489), job `137323393071`, FAILURE at the new assertion. The extractor returned both inactive `0xBAD` and active `0x1234` constants from a `%:if 0 / %:else` fixture.
- **Source/test commit:** `da4c7bd3114a2793b37e1a66cb90bde52a331e6f`.
- **Focused GREEN:** [Quarantine run #45060073589](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060073589), job `137323794134`, SUCCESS.
- Exact markers: `POLL_FAULT_CONSTANT_EXTRACTION_DIGRAPH_INACTIVE_REJECTED 1/1`; `POLL_FAULT_CONSTANT_EXTRACTION_PHASE2_DIGRAPH_SPLICE_REJECTED 1/1`; `POLL_FAULT_EXTRACTOR_SELFTEST=PASS`.
- Existing source-extracted dual-store, quarantine, pending-attempt, journal-mount, poll-window, pulse-capture and mutation-rejection labs also passed. The log reports `PHX-HARDWARE: 72/72 source-extracted host scenarios PASS`.

## Implementation

In `poll_fault_dual_store_lab_fixtures.py`, the inactive-branch recognizer now accepts either `#` or `%:` at the start of a logical preprocessing line. It continues to process phase-2 line splicing before matching directive keywords, so a spliced `%:elif` is also recognized. The regex does not match the longer `%:%:` digraph because the next token after `%:` is not a directive keyword.

In `poll_fault_dual_store_lab.py`, two regressions prove:
1. `%:if 0` excludes its inactive constant and retains only the `%:else` constant.
2. A phase-2-spliced `%:elif 0` remains inactive after a taken `%:if 1`.

## Safety and evidence limits

The Quarantine workflow explicitly reports `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`. These are host-side source-extraction and fault-injection results only.

No ESP32/ESP8266 runtime, GPIO, relay, coin admission, controller/API, CORE ledger, QA-owned assertion, Release workflow, signing, migration, or production state changed. No hardware was flashed or reset.

The Full build for exact source/test SHA `da4c7bd3114a2793b37e1a66cb90bde52a331e6f` ended **CANCELLED**: [run #45060073651](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060073651), validation job `137323871590` **FAILED** at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. The run finished with 9 jobs SUCCESS, 1 FAILURE, 12 CANCELLED and 5 SKIPPED; ESP32 and several downstream target/simulation jobs did not complete. This is not a regression from the digraph parser change, and no positive poll signature was fabricated.

## Next exact action

PHX-MASTER must refresh the Master-owned role/integration pins for the #338 → #339 → #341 cleanup line and preserve it as a separate Hardware candidate until an explicit stack decision. PHX-QA/PHX-CORE continue to own the authenticated poll/register contract and the inherited positive poll-signature fixture. Keep coin admission and remote configuration fail-closed.

**Disposition:** focused CI verified; full integration pending; hardware acceptance NOT TESTED; PRODUCTION NO-GO.
