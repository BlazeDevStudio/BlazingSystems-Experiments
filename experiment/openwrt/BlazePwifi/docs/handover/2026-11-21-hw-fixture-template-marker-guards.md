# PHX-HARDWARE — fail-closed dual-store fixture template substitutions

**Date:** 2026-11-21  
**Task:** cleanup-first #266 / Hardware test infrastructure  
**PR:** [#331](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/331) — OPEN / DRAFT / UNMERGED  
**Parent:** [#330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/330) at `1a1e5e25834748fbba95d6253eb668f29b6c82f8`  
**Branch:** `phoenix/hardware-fixture-template-guards-20261121`  
**Current source/test HEAD:** `e455869bfe3f95fe8770b0977a8bb9f599406740`

## Defect

The Hardware-owned dual-store fixture composer used a sequence of unchecked Python `str.replace()` calls to inject board-specific snippets into the shared C++ scenario template. A missing or duplicated marker was silently accepted at the composition boundary. That could produce a malformed or semantically incomplete host fixture and make a source-lab failure harder to diagnose.

## Test-first evidence

- Test-only commit: `862a05758781ed1a9279a100bd2eddfbf7efaa90`.
- Quarantine RED: [run #44896317385](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44896317385), job `136822629063`, expected failure:
  `AssertionError: fixture composition accepted a missing NO_MARKER_RESET marker`.
- The first fix attempt `a2a4b90e20b0a9da35d34f86974a750e1406088c` was malformed and failed focused CI with an ImportError because the `harness` export was accidentally omitted. It was not hidden or rewritten; the subsequent correction restored the composer and added the guard.

## Correction

The composition module now has a small `_render_main()` boundary that:

1. Verifies the board backend supplies every required fixture value.
2. Checks exact occurrence counts for each substitution marker, including intentional repeated setup/clear markers.
3. Checks the exact `BOARD_NAME` substitution count.
4. Replaces markers only after the count checks pass.
5. Rejects any unresolved marker after rendering.

The lab adds a missing-marker and duplicate-marker mutation against the real imported template module. Both must raise a marker-specific `ValueError`.

Only the Hardware-owned dual-store fixture composer and its existing Hardware-owned lab runner changed. No production sketch, persistence format, controller/API, finance, signer/witness, QA-owned assertion, Release workflow or COE destination changed.

## Exact-head evidence

- Corrected source/test SHA: `e455869bfe3f95fe8770b0977a8bb9f599406740`.
- Quarantine focused run: [#44896623794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44896623794), job `136823550065`: **SUCCESS**.
- Exact log markers:
  - `POLL_FAULT_FIXTURE_MARKER_CONTRACT_PASS`
  - `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32`
  - `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266`
  - Existing NVS premature-durability/omitted-commit and ESP8266 raw-flash-read failure injections remain in the same focused suite.

- Full BlazePwifi run: [#44896623789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44896623789).
- Validation job `136823614537`: **FAILURE** at the existing QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. This task does not change or weaken that assertion and does not invent a positive poll signature.
- At this handover snapshot, 13/14 target/platform jobs had completed successfully and x86-64 was still in progress. No full-workflow success is claimed.

## Classification and limits

- Fixture mutation testing: **SIMULATED**.
- Exact focused GitHub Actions: **CI VERIFIED**.
- Full integration: **BLOCKED** by the inherited QA-owned poll-signature assertion.
- Physical flash/power-cut behavior: **NOT TESTED**.
- 150 real power cuts, 30-device/24-hour soak, electrical pulse/recovery: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO**.

No merge, rebase, force-push, flash, reset, production migration, signing, release tag, deployment, payment, or cutover occurred.

## Next exact action

PHX-QA/PHX-CORE must resolve the canonical authenticated register/poll/receipt contract and replace the stale positive signature-presence assertion with source-linked negative/default-deny verification. PHX-MASTER must preserve the #322 → #323 → #326 → #327 → #330 → #331 stack and reconcile its canonical active-head pins. PHX-HARDWARE must revalidate live heads and terminal target jobs before selecting another owned task.
