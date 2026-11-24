# PHX-HARDWARE handover — poll-response shared runner consolidation

**Checkpoint:** 2026-11-24T18:54:03Z  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base:** PR #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Exact source/test SHA:** [`4dfdcd8a6ede411fafae2cfe2fb99acc696bc55f`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4dfdcd8a6ede411fafae2cfe2fb99acc696bc55f)

## Selected owned task

Cleanup-first consolidation of the remaining duplicate C++ compile/run lifecycle in the ESP8266 poll-response fail-closed host lab. This is Hardware-owned test infrastructure; no production sketch, shared API, CGI producer, ledger, signer or migration source changed.

## Exact source changes

Files changed by the source/test commits:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab_structure_guard.py`

The poll-response lab now imports the existing sibling `cpp_fixture_runner.run_cpp_fixture` and routes all three C++ fixture executions through one small `compile_and_run()` wrapper:

1. primary poll-response / consumer-deny fixture;
2. poll-window source-order fixture;
3. exact-boundary mutation that removes the final quiet-line sample.

The duplicated `subprocess` / `tempfile` imports, temporary-directory handling, compiler invocation and process execution were removed from this lab. The same `-std=c++17 -Wall -Wextra -Werror -Wno-unused-parameter` flags and 30-second compile / 10-second execution limits are preserved. The shared helper centralizes bounded diagnostics and timeout handling.

The structure guard now rejects reintroduction of direct `subprocess` / `tempfile` imports or process calls and requires the shared-runner import. It still checks the four fixture payload hashes. The runner reports 329 logical lines to the guard.

## Commit sequence and correction

- `462783d317132f85003afeb6eed839a640775c3a` — shared-runner refactor and structural guard.
- `53f3faddb54fd7f987bd744ed6d00debd9e3f430` — boundary threshold correction.
- The first exact-head Quarantine attempt on `53f3fadd` exposed an `IndentationError` after removal of the old nested temporary-directory block. This was not hidden or treated as a pass.
- `4dfdcd8a6ede411fafae2cfe2fb99acc696bc55f` — corrected the result-check block indentation. The final exact-head focused workflows below pass.

## Exact-head GitHub Actions evidence

All final source/test results below use `4dfdcd8a6ede411fafae2cfe2fb99acc696bc55f`.

### Focused Quarantine

[PR run #45463582720](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45463582720) — **SUCCESS**  
Job `138692426033` — PASS.

Exact log markers include:

- `POLL_RESPONSE_SHARED_RUNNER_PASS`
- `POLL_RESPONSE_FIXTURE_BOUNDARY_PASS 4/4; RUNNER_LINES=329`
- ESP8266 and ESP32 strict JSON primitive grammar: valid 9/9, invalid 16/16; four mutations rejected per board.
- Composite grammar: valid 6/6, invalid 12/12 per board; depth 16 accepted / 17 rejected.
- Duplicate-root-status and trailing-data denial.
- Quarantine source lab: 36/36 scenarios per board.
- Coin-post disposition dispatch: 7/7 per board.
- Poll-window drain: 11/11 per board; short-debounce, unsafe deadline rollover and missing active-line-abort mutations rejected.
- Physical coin, relay and power-cut acceptance explicitly remain 0.

### Focused Relay

[PR run #45463582760](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45463582760) — **SUCCESS**  
Jobs `138692427294` (ESP32 boot polarity) and `138692427521` (source/output polarity) — PASS.

The source/output log confirms the shared-runner and fixture-boundary markers, current CGI poll without a signature remains denied, response-positive consumer bypass mutations are rejected, and bounded HTTP response cases pass on both boards.

### Full BlazePwifi build / integration

[PR run #45463582772](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45463582772) — **FAILURE**.

- Validation job `138692606934` fails in `tests/controllers.sh` at `Missing poll signature check` in the ESP8266 sketch.
- All 14 target/platform jobs (13 firmware targets plus Android) completed PASS.
- Release/signing/publication-dependent stages were skipped.
- This is the existing CORE/QA register-poll contract mismatch; this cleanup did not modify the producer, consumer sketch or assertion.

## Evidence classification

- Shared-runner integration and structural guard: **CI VERIFIED**.
- JSON, poll-window, quarantine and relay behavior: **SIMULATED / CI VERIFIED**.
- Local independent execution: **NOT RUN**.
- Physical coin pulse / relay electrical acceptance: **NOT TESTED**.
- 150 controlled power cuts and 30-device 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay and v1-to-v2 migration: **NOT ACCEPTED**.
- **PRODUCTION NO-GO.**

## Coordination and next exact action

- PHX-MASTER: refresh Master-owned `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and Control Plane active-head pins to the new source/test SHA and this PR's final docs HEAD. Hardware did not edit Master-owned files.
- PHX-CORE: publish the approved versioned register/poll response contract and canonical vectors.
- PHX-QA: reconcile the inherited `Missing poll signature check` assertion without weakening deny-default.
- PHX-HARDWARE: on the next activation, re-read all live heads and assignments before selecting another owned task.

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected Files Library; no Google Drive connector was exposed in this runtime. Older v5–v7 snapshots were not substituted.

No Codex, merge, force-push, flash, device reset, live-money operation, production migration, signer provisioning, release tag, deployment or COE destination write occurred.
