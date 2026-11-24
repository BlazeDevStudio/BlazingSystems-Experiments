# PHX-HARDWARE handover — current CGI envelope lab shared-runner consolidation

**Checkpoint:** 2026-11-24T20:48:00Z  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`

## Selected owned task

Continue cleanup-first #266 within the Hardware-owned poll-response regression labs. The current CGI envelope lab still duplicated temporary-directory creation, C++ compilation, execution, and timeout handling even though the same branch already has the bounded shared `cpp_fixture_runner.run_cpp_fixture`.

## Concrete source changes

- `poll_current_cgi_envelope_deny_lab.py` now imports and calls `run_cpp_fixture`.
- Removed its local `subprocess` / `tempfile` compile-run implementation.
- Preserved C++17, `-Wall -Wextra -Werror`, `-Wno-unused-parameter`, 30-second compile and 10-second execution bounds, fixture name/prefix, and board-specific diagnostic context.
- Extended `poll_response_failclosed_lab_structure_guard.py` to require the current CGI lab to import and call the shared runner and reject direct `subprocess` / `tempfile` imports or calls.

No production sketch, CGI producer, shared CORE contract, coin authority, financial state, signer, witness, migration, Release workflow, or COE destination changed.

## Test-first evidence

- Structural guard commit: [`53d2e141`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/53d2e1411b8cdfe1db6b2d8840bed53d0d16f4de).
- Expected RED: Quarantine PR [#45483945083](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45483945083), job `138764194350`, failed at the new exact assertion `CURRENT_CGI_LAB_SHARED_RUNNER_IMPORT_MISSING`. The preceding source-extracted quarantine scenarios reported 72/72 pass; the new guard correctly exposed the remaining local runner duplication.

## Corrected source/test SHA

[`8c0626942815f1782211b6be784cf995ac5c5038`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8c0626942815f1782211b6be784cf995ac5c5038)

### Exact-head GitHub Actions

- Quarantine PR [#45484091630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484091630), job `138764702687`: **PASS**. Logs include `CURRENT_CGI_SHARED_RUNNER_GUARD_PASS`, `POLL_RESPONSE_SHARED_RUNNER_PASS`, source mutations rejected 4/4, current CGI envelope denial 3/3 on ESP8266 and 3/3 on ESP32, consumer fail-open mutations rejected 2/2 per board, and 72/72 source-extracted host scenarios PASS.
- Relay PR [#45484090681](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484090681), jobs `138764697907` and `138764698460`: **PASS**. The exact-source poll-response/CGI lab, JSON grammar mutations, poll-window checks, bounded-response checks and board output checks completed.
- Full PR [#45484090822](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484090822), validation job `138764865503`: **FAIL** at inherited `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware target jobs plus Android (14/14) **PASS**; validation-dependent simulation, candidate, signing, import and publication jobs were **SKIPPED**.

All source-extracted host labs are **SIMULATED / CI VERIFIED**, not physical hardware evidence. Local independent execution: **NOT RUN**.

## Ownership and acceptance

- #266 remains OPEN / **0-of-7** role tracks complete; this is one bounded Hardware cleanup contribution only.
- P0 #177 remains OPEN. This refactor does not change the pulse-intake mitigation or claim physical coin-pulse preservation.
- CORE owns the authenticated register/poll and event-bound receipt contract. QA owns independent assertion reconciliation. Keep the consumer deny-default; do not invent `response_sig` or weaken the inherited assertion.
- #239 Phase A deny, #254 ControllerAuthV1Lab, and parallel #283 were revalidated before this change and remain separate OPEN / DRAFT / UNMERGED stacks. No retarget, rebase, cherry-pick or merge occurred.
- Physical coin/relay/electrical acceptance, 150 power cuts, and 30-device 24-hour soak remain **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, reversible v1-to-v2 migration and independent QA/release acceptance remain **NOT ACCEPTED**.
- Private Drive registry v11 remains **NOT RECOVERED** through the authorized Library surface; no Google Drive connector was exposed. No older registry snapshot was substituted.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

Next: CORE publishes the approved authenticated register/poll and event-bound receipt contract; QA reconciles the inherited Full assertion without weakening deny-default; MASTER refreshes its own exact #349 pins after this Hardware docs update.
