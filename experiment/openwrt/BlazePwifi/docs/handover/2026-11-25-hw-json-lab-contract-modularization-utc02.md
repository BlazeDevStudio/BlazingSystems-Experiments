# PHX-HARDWARE UTC02 — strict poll JSON lab contract modularization

**Updated:** 2026-11-25T02:53:47Z  
**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 contribution, hardware issue #177 evidence  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** #349 OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-json-array-primitive-guard-20261124-utc00\`  
**Base PR:** #347 at \`960184670379f01e20f0e7e8bc23b3e5eedacd3f\`

## Source change

Source/test commit: [\`b8f535d9af17fc4f4dfdf94ce0802ecd9d8adfb4\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b8f535d9af17fc4f4dfdf94ce0802ecd9d8adfb4)

The 286-line strict poll-JSON lab was separated into three responsibility modules while preserving the same extracted firmware functions, baseline fixtures, mutation payloads, expected exit codes and pass markers:

- \`poll_json_array_primitive_lab_root_contracts.py\`: duplicate root status and trailing-document rejection
- \`poll_json_array_primitive_lab_composite_contracts.py\`: array/object separators, depth cap, control characters, supported/unsupported escapes and Unicode hex
- \`poll_json_array_primitive_lab_primitive_contracts.py\`: array primitive terminator, leading-zero, fraction, exponent and exact boolean literal rules
- \`poll_json_array_primitive_lab.py\`: baseline compilation and ordered orchestration only
- \`poll_json_array_primitive_lab_structure_guard.py\`: prevents the orchestration module from absorbing domain mutation logic again; imported by \`poll_response_failclosed_lab.py\`

No production \`.ino\`, CGI, shared register/poll API, financial state, coin admission, relay actuation, signer, witness or migration code changed.

## Test-first evidence

Test-only commit: [\`c148e55d11c2a12f698690cfef4bafe30e87f5d3\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c148e55d11c2a12f698690cfef4bafe30e87f5d3)

The new structural guard was wired before the modules existed. Expected RED:

- Quarantine push [#45535432153](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535432153), job \`138940750805\`: FAIL at missing root-envelope contract module
- Quarantine PR [#45535438840](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535438840), job \`138940775764\`: same expected RED
- Relay push [#45535432130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535432130), job \`138940751430\`: expected structural-guard failure
- Relay PR [#45535438843](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535438843), job \`138940776318\`: expected structural-guard failure

## Corrected exact-source CI

- Quarantine push [#45535612707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612707), job \`138941347155\`: PASS
- Quarantine PR [#45535620400](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620400), job \`138941371759\`: PASS
- Relay push [#45535612720](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612720), jobs \`138941347029\` and \`138941347446\`: PASS
- Relay PR [#45535620317](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620317), jobs \`138941371412\` and \`138941371706\`: PASS

Exact Relay logs show \`POLL_JSON_LAB_MODULE_BOUNDARY_PASS\`, root-envelope, composite and primitive grammar pass markers, and all deliberate mutations rejected on ESP8266 and ESP32. Quarantine also passed its full focused job. This is source-extracted host simulation / CI evidence only.

## Full candidate boundary

Full push [#45535612715](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535612715), validation job \`138941449711\`: FAIL at the inherited \`Missing poll signature check\` in \`tests/controllers.sh\`. Thirteen firmware target jobs plus Android passed; validation-dependent simulations, candidate, signing and publication stages were skipped. Full PR run [#45535620372](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45535620372) was still running at this checkpoint.

CORE owns the authenticated register/poll producer contract. QA owns independent assertion reconciliation. Keep unsigned poll responses and coin admission deny-by-default; do not add synthetic signatures or relax the assertion.

## Status and next action

- #266 remains OPEN / 0-of-7 role tracks complete; this is one bounded Hardware cleanup contribution.
- #177 remains OPEN / P0.
- #239, #254, #283, #340 and #349 remain separate OPEN DRAFT stacks; no merge, rebase, retarget or force-push.
- Physical coin/relay/electrical acceptance, 150 controlled power cuts and 30-device 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance: NOT ACCEPTED.
- Local independent execution: NOT RUN.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

**Next exact action:** PHX-CORE publishes the canonical authenticated register/poll contract and golden vectors; PHX-QA independently reconciles the inherited assertion without weakening deny-default; PHX-MASTER refreshes its exact #349 pins. PHX-HARDWARE then revalidates all branch heads before the next owned task.


## UTC03 exact-head correction — 2026-11-25T03:42Z

**Current PR / source-test head:** `bd91e9b8496c0d274bb0779fd4a75b5de28dbc33`  
**PR:** [#349 OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`

### Follow-on source and guard commits

- Test-only boundary commit [`e70668379e19fd30807b7fa50af8712209fe6f5d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e70668379e19fd30807b7fa50af8712209fe6f5d) added the requirement that the dual-store source-contract module exist and be called by the orchestrator.
- Source modularization commit [`5211490a497387a3e534232422ea978dfc7bcb4e`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5211490a497387a3e534232422ea978dfc7bcb4e) moved repository-root, board-sentinel, unknown-board, extractor and active-constant self-tests into `poll_fault_dual_store_lab_source_contracts.py`. The main lab now owns board-specific C++ scenarios and delegates source self-tests through `run_source_contracts()`.
- Guard correction [`bd91e9b8496c0d274bb0779fd4a75b5de28dbc33`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bd91e9b8496c0d274bb0779fd4a75b5de28dbc33) changed the structural guard to inspect the parsed orchestrator tree (`tree`) rather than the removed `lab_tree` name.

### Test-first and correction evidence

- Expected test-only RED at `e706683`: Quarantine [#45539921947](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45539921947), job `138955659799`, failed at `POLL_FAULT_SOURCE_CONTRACT_MODULE_MISSING`. Relay [#45539921909](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45539921909) succeeded; Full [#45539922025](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45539922025) was cancelled.
- Intermediate refactor at `5211490`: Quarantine [#45540153548](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540153548), job `138956423984`, exposed a guard implementation error (`NameError: lab_tree is not defined`). This was a test-harness failure, not a firmware/product regression. Relay [#45540153557](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540153557) succeeded; Full [#45540153507](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540153507) was cancelled.
- Corrected exact-head Quarantine [#45540305031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540305031), job `138956933072`: **PASS**, including `POLL_FAULT_SOURCE_CONTRACT_BOUNDARY_PASS` and `POLL_FAULT_SHARED_RUNNER_STRUCTURE_PASS`.
- Corrected exact-head Relay [#45540305104](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540305104), jobs `138956933784` and `138956933934`: **PASS**.
- Exact-head Full [#45540305058](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45540305058), validation job `138957038055`: **FAIL** at the existing `Missing poll signature check` in `tests/controllers.sh`. All 14/14 firmware/platform plus Android build jobs passed; 12 dependent simulation/update/signing/publication jobs were skipped.

### Scope and disposition

No production `.ino`, CGI producer, register/poll contract, finance, relay admission, signer, witness, migration, release workflow or COE destination changed. The moved tests are host-side source contracts; their success is **SIMULATED / CI VERIFIED**, not physical flash durability or electrical acceptance. Local independent execution: **NOT RUN**. Physical coin/relay/electrical recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak: **NOT TESTED**. HARDWARE ACCEPTED: **NO**. PRODUCTION READY: **NO-GO**.

**Next:** PHX-CORE publishes the approved authenticated register/poll contract and golden vectors; PHX-QA independently reconciles the inherited signature assertion without weakening deny-default; PHX-MASTER refreshes its own exact #349 pins. PHX-HARDWARE revalidates live heads before the next owned task.
