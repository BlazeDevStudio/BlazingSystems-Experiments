# PHX-HARDWARE — quarantine equal-size corruption checkpoint (LAB / NO-GO)

**2026-11-15 (Asia/Manila)**

Role: PHX-HARDWARE. Task: fail-closed firmware quarantine after partial, corrupt, or absent storage (issue #266 / #34). Working branch: `phoenix/hardware-quarantine-byte-readback-20261115`, based on unmerged [draft PR #283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) at `a87567291e80006f3f30cea81fc20e8b299b95e8`. Older exploratory branch `phoenix/hardware-quarantine-failclosed-20261115@e2aa3dec` was superseded by PR #283's upstream correction; do not merge both.

## Changes
- Firmware source commit [`18d577ebacc8`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/18d577ebacc81912ad025b76ee89eb31952f836c): both ESP32 and ESP8266 append `record` to LittleFS quarantine log, close/reopen and verify the **exact new bytes** in addition to checking file size. Any byte mismatch returns failure before `clearPending()`. This closes the size-equal corruption case remaining in PR #283's implementation.
- New host harness `esp32/BlazePwifiVendo32/quarantine_readback_lab.py` extracts the actual two firmware function bodies and compiles against a fake in-memory LittleFS with C++17. Intended scenarios per board: valid append, filesystem missing, zero pending, prior-open failure, append-open failure, short-write, verify-open failure, truncated close, same-length corruption, bit-flipped readback, full log. Passing tests must be proven by literal job logs, not inferred.
- Workflow commit [`bdbb02e505b5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bdbb02e505b50a2efd00a1625a96fb507b7361d5) runs focused tests for reviewable PR heads; no production signing, hardware activation or deployment.
- Dedicated operator/debug notes: `esp32/BlazePwifiVendo32/QUARANTINE_BYTE_READBACK.md`.

## Test classification
At checkpoint creation, the focused native test and full post-change CI are **NOT YET RUN / NO RESULT**. A successful compilation or fake filesystem check is NOT physical flash power-cut evidence. PHX-QA and PHX-RELEASE must independently review the helper and temporary workflow. Do not claim production readiness from a green badge alone.

## Branch provenance
The PR #283 line originated from default `main` and contains `PROJECT_HANDOVER.md` but not the full development-branch `docs/handover/CURRENT_STATE.md` and `CHANGE_LEDGER.md`. This work does not fabricate those files or rewrite another branch's 1+ MB audit ledger; MASTER must decide rebase/integration into the active Phoenix development source and sync canonical handovers there.

## Remaining P0
The current router/backend register/poll response signature contract differs from PR #283's expected `response_sig`. A protected cold-start revision witness, signed event ACK/financial consistency and migration remain outstanding. Real ESP hardware electrical confirmation, 150 controlled noncustomer-device power cuts and 30-device 24-hour soak #34 have **not** happened. Keep coin/relay admission fail closed pending approval.

**Next:** open a stacked DRAFT PR against PR #283's branch, inspect exact native host job logs, classify both board build jobs and regression, request independent QA/RELEASE/CORE review. No automatic merges, flashing or releases.
