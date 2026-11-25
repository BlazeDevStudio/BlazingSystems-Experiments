# PHX-HARDWARE — shared C++ fixture stem containment

**Observed:** 2026-11-25T01:16:01.202Z  
**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / P0 hardware regression infrastructure #177 / existing DRAFT PR #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test head:** `d5b5cd10ae7ab655639b011c442b6968b32c2398`

## Proven defect

The shared `cpp_fixture_runner.run_cpp_fixture()` accepted an unchecked `stem` and used it in both `Path(folder) / f"{stem}.cpp"` and `Path(folder) / stem`. Empty, dot/dot-dot, absolute, slash/backslash, NUL, and non-string values were not rejected before temporary-file/process setup. This allowed the shared helper's output path to escape its temporary-directory boundary for path-like stems, or fail later with incidental TypeError.

## Test-first evidence

Test-only commit `e96d994e2e70f4ed0047ea42aa037243dc89822c` added eight invalid-stem cases and asserted rejection occurs before temporary-directory creation, file writes, or process launch.

- Quarantine RED [run #45523781786](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45523781786), job `138901937894`: expected contract failure; six invalid-string cases raised no ValueError and non-string cases produced TypeError.
- Relay RED [run #45523781833](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45523781833), job `138901937162`: same expected contract failure.
- The test patched file writes and process execution; no outside path was written or compiled.

## Correction

Source/test commit `d5b5cd10ae7ab655639b011c442b6968b32c2398` adds `_validate_stem()` and calls it before creating a temporary directory. It rejects non-string/empty values, `.`, `..`, absolute paths, either path separator and NUL. The contract suite now reports 9/9.

## Exact-source CI

- Quarantine push [run #45523939534](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45523939534), job `138902469520`: SUCCESS. Logs contain `POLL_FAULT_LATCH_SHARED_RUNNER_GUARD_PASS` and `CPP_FIXTURE_RUNNER_CONTRACT_PASS 9/9`; both-board source-extracted labs completed.
- Relay push [run #45523939484](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45523939484), jobs `138902468624` and `138902468959`: SUCCESS. Logs also show the shared-runner guard and 9/9 contract marker.
- Full exact-source [run #45523947813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45523947813), validation job `138902614042`: FAILED at the inherited `Missing poll signature check` in `tests/controllers.sh`. At this checkpoint the firmware/platform build matrix was still completing; no complete matrix pass is claimed.

## Scope and evidence boundary

Only `cpp_fixture_runner.py` and `cpp_fixture_runner_contract_lab.py` changed in the source/test commit. No production .ino, CGI, wire/API contract, finance, signer, witness, replay, migration or COE destination changed. Host tests are SIMULATED / CI VERIFIED, not physical acceptance. Local independent execution NOT RUN.

#177 remains OPEN/P0. #266 remains OPEN / 0-of-7. #239, #254 and #283 remain separate OPEN DRAFT stacks. CORE owns the authenticated register/poll contract; QA owns assertion reconciliation. Keep unsigned poll responses and coin admission deny-by-default.

Physical pulse/relay/electrical recovery, 150 power cuts, 30-device 24-hour soak, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance remain NOT TESTED or NOT ACCEPTED. **HARDWARE ACCEPTED: NO; PRODUCTION NO-GO.**

## Next exact action

Revalidate all live heads, obtain CORE/QA resolution of the authenticated register/poll response contract, and continue only on the next highest-impact unblocked Hardware-owned task. Keep PR #349 DRAFT and unmerged.
