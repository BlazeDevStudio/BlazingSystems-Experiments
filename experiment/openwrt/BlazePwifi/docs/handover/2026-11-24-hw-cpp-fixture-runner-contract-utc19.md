# PHX-HARDWARE handover — shared C++ fixture runner lifecycle contract

**Checkpoint:** 2026-11-24T19:26:00Z  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`

## Exact source and workflow pins

- Test source commit: `133076971ac71565ef9913196768a5578d5986ca`
- Structural-guard cleanup: `c0a84d250c5a3b73a5fae485396816879ff0d41f`
- Relay path-filter commit / pre-handover branch head: `4c99e1c846d315f795901858e94189226723627a`
- Final documentation head: recorded by the handover commit that updates this file.

## Selected owned task

Improve the existing dedicated shared C++ fixture-runner contract suite rather than duplicating process-runner tests inside the poll-response structural guard. The test module is invoked by the existing poll-loop and poll-window labs on the Hardware stack.

## Concrete changes

- Extended `cpp_fixture_runner_contract_lab.py` from 7 to 8 contract tests.
- Added a successful compile/run lifecycle test: verifies the source file exists while executing, C++17 `-Wall -Wextra -Werror` plus caller-supplied `-Wno-unused-parameter` flags are preserved, default 30-second compile and 10-second execution limits remain, and the temporary directory is removed after execution.
- Extended compile-failure injection to prove the binary is not launched and temporary files are removed.
- Extended compile-timeout and execution-timeout injection to prove temporary directories are removed after exceptions.
- Preserved the existing invalid-timeout rejection and bounded stdout/stderr diagnostic-tail tests.
- Restored `poll_response_failclosed_lab_structure_guard.py` to its original structural-only responsibility; the temporary duplicate 6/6 test block was removed.
- Extended Relay workflow path filters to watch the dedicated contract lab, shared runner, structural guard and this handover. Quarantine already watches the board-local tree and now watches this handover explicitly.

No production sketch, CGI producer, shared response API, coin authority, financial ledger, signer, witness, migration, QA-owned assertion or COE destination source changed.

## Exact-head GitHub Actions evidence

All results below are on source/test/workflow SHA `4c99e1c846d315f795901858e94189226723627a`.

- Quarantine [#45469493996](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45469493996), job `138713248978`: **PASS**. Logs include `CPP_FIXTURE_RUNNER_CONTRACT_PASS 8/8` twice, poll-response shared-runner guard PASS and fixture-boundary 4/4. Logs explicitly classify this as simulated; physical coin and power-cut flags remain 0.
- Relay [#45469493976](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45469493976), jobs `138713248559` and `138713249289`: **PASS**. Logs include `CPP_FIXTURE_RUNNER_CONTRACT_PASS 8/8` twice and the current-CGI unsigned register/poll deny and consumer-mutation rejection cases.
- Relay push [#45469483119](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45469483119): **PASS**.
- Full [#45469493967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45469493967): **FAIL** at validation job `138713250781`, exact inherited error `Missing poll signature check` in the ESP8266 sketch. All 14/14 firmware/platform jobs, including ESP32, ESP8266, OpenWrt targets and Android, completed **PASS**. Update, simulation, candidate and release/signing stages were skipped after validation failure.

### Test-first correction history

- Initial duplicate guard test commit `237b0c7bbda6f84ecd65107fbdb6461d2f52a130` produced a red Quarantine run [#45468226510](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45468226510), job `138708784600`: the injected execution-timeout mock returned a `TimeoutExpired` object instead of raising it. This was a test-fixture defect, not a production-code failure.
- Corrected intermediate commit `d2565d9cc85409d93cd68109b14653257b6af944` changed the injection to raise the exception; focused Quarantine [#45468435046](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45468435046) and Relay [#45468435045](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45468435045) passed.
- The duplicate tests were then moved into the existing dedicated contract lab and the structural guard restored. The final 8/8 exact-head results are the runs above.

## Current release and ownership boundaries

- Cleanup-first issue #266 remains OPEN; **0/7 role tracks completed**. This is one bounded Hardware contribution, not completion of the global cleanup gate.
- P0 hardware issue #177 remains OPEN. The current task changes only host-test infrastructure; it does not close the synchronous-poll coin-pulse hazard or establish hardware acceptance.
- #239 Phase A deny: `d83b715b116185107737fef721c2eece8feebf39`, OPEN / DRAFT.
- #254 ControllerAuthV1Lab: `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, OPEN / DRAFT.
- #283 parallel sketches: `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`, OPEN / DRAFT. Current audit confirms append failure returns before clear, but `quarantinePending()` is definition-only in both sketches; main CGI register/poll still emits no approved `response_sig`. The old #6883020442 note is historical context, not a claim that the original append-failure clear remains present.
- #340 remains a separate child candidate; #348 remains a separate #254 child. Their ancestry and test results are not inherited by #349.
- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development `aad3aade72c1156eecba1fed30907c6d0283b2c5`; Master PR #288 `463a600c2ba4843b41bf498614a4fb76fa9f3b05`.
- Master-owned ROLE_ASSIGNMENTS / INTEGRATION_MATRIX still carry older #349 pins; Master must refresh them to the exact current source/test and final docs heads. Hardware did not edit Master-owned files.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` remains FROZEN. No staging, copying, migration or destination write occurred.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered through the connected Files Library; no Google Drive connector is exposed in this run. No older registry was substituted.

## Evidence classification and next exact action

- Shared fixture-runner contract: **CI VERIFIED**.
- Firmware/parser/poll/quarantine labs: **SIMULATED / CI VERIFIED** only.
- Local independent test execution: **NOT RUN**.
- Physical coin pulse, relay/electrical recovery, LittleFS power-loss, 150 controlled power cuts, and 30-device 24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, reversible v1-to-v2 migration and independent QA/release acceptance: **NOT ACCEPTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

Next exact action: PHX-MASTER refresh its coordination pins; PHX-CORE publish the approved authenticated register/poll and event-bound receipt contract; PHX-QA reconcile the inherited Full assertion without weakening deny-default. PHX-HARDWARE revalidates all live heads on the next activation before choosing another owned task.

No Codex, merge, force-push, physical flash, device reset, live-money operation, production migration, signer provisioning, release tag or deployment occurred.


---

## PHX-HARDWARE UTC20 — request-digest lab shared-runner consolidation (2026-11-24T20:15Z)

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `639635c282a88133a715e921e4dc37e6febde87e`

### One bounded cleanup-first change

`request_digest_failure_lab.py` now uses the established `cpp_fixture_runner.run_cpp_fixture` instead of maintaining its own `TemporaryDirectory`, `g++` command, `subprocess.run` calls and timeout handling.

- Removed direct `subprocess` and `tempfile` imports and local compile/run code.
- Preserved C++17, `-Wall -Wextra -Werror`, `-Wno-unused-parameter`, 30-second compile and 10-second execution bounds.
- Preserved source extraction of `validSha256Hex`, `signedBody`, `readBoundedControllerResponse` and `post` from both sketches.
- Preserved failure injection: empty, short and non-hex digests must dispatch zero HTTP requests; a valid 64-character hexadecimal digest dispatches one request.
- The shared runner owns temporary-file lifecycle, bounded process execution and bounded diagnostics. No production sketch, CGI, wire contract, coin/finance, signer, witness or migration source changed.

### Exact-head CI

- Quarantine PR [#45478127449](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45478127449), job `138743697596`: **SUCCESS**. Logs show `REQUEST_DIGEST_FAILURE_DENY_PASS` for ESP8266 and ESP32; empty/short/non-hex digest paths dispatch zero HTTP requests and valid SHA-256 dispatches one. The wider quarantine, pulse-capture and boot-polarity labs also pass.
- Relay PR [#45478127630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45478127630), jobs `138743697824` and `138743698353`: **SUCCESS**.
- Full PR [#45478127804](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45478127804): **FAILURE** at validation job `138743700087`, inherited `Missing poll signature check` in the ESP8266 controller source. 14 jobs succeeded, 1 failed, 12 downstream jobs skipped. This is the existing CORE producer / QA assertion contract blocker; this Hardware cleanup did not weaken deny-default or invent a signature.
- Push Quarantine [#45478114685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45478114685), job `138743648705`: **SUCCESS**.

All runs checked out literal source/test SHA `639635c282a88133a715e921e4dc37e6febde87e`. The workflow logs explicitly report `SIMULATED_ONLY=1`, physical coin/relay/power-cut acceptance flags zero, and financial production authorization zero.

### Ownership and acceptance

- Cleanup-first #266 remains OPEN; **0/7 role tracks complete**. This is one bounded Hardware contribution only.
- P0 #177 remains OPEN; this change does not fix the synchronous-poll pulse-loss hazard.
- #239 Phase A deny, #254 ControllerAuthV1Lab, and parallel #283 remain OPEN / DRAFT / UNMERGED. Their source and ancestry were revalidated this activation; no retarget, rebase or cherry-pick occurred.
- #283 audit comment [#6883020442](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283#issuecomment-6883020442) remains an audit lead: append-failure clear is not present at the current #283 head, but `quarantinePending()` has no active callsite and register/poll still lacks the approved `response_sig` contract.
- Master #288 owns `coordination/phoenix/`; its ROLE_ASSIGNMENTS / INTEGRATION_MATRIX pins remain behind the live #349 head and require Master refresh.
- Private Drive registry v11 remains **NOT RECOVERED** through authorized Library search; no Google Drive connector is exposed. No older registry snapshot was substituted.

### Status and next exact action

- Shared-runner cleanup: **CI VERIFIED**.
- Digest, poll, quarantine and pulse labs: **SIMULATED / CI VERIFIED** only.
- Local independent execution: **NOT RUN**.
- Physical coin, relay/electrical recovery, 150 power cuts and 30-device 24-hour soak: **NOT TESTED**.
- Durable accounting/replay, protected anti-rollback signer/witness, reversible v1-to-v2 migration and independent QA/release signoff: **NOT ACCEPTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

Next: PHX-CORE publishes the approved authenticated register/poll response and event-bound receipt contract; PHX-QA reconciles the Full validation assertion without weakening deny-default; PHX-MASTER refreshes its exact #349 pins. Hardware revalidates all heads before the next owned task.

No Codex, merge, force-push, physical flash, device reset, live-money operation, production migration, secret provisioning, release tag or deployment occurred.
