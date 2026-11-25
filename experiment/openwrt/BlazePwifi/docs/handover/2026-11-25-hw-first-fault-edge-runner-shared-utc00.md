# PHX-HARDWARE handover — first-fault edge-count lab shared-runner consolidation

Updated: 2026-11-25T00:54:00Z  
Role: PHX-HARDWARE  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
Issue: [#177 — synchronous poll / coin pulse preservation](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
Cleanup gate: [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
PR: [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
Branch: phoenix/hw-json-array-primitive-guard-20261124-utc00  
Base PR #347: 960184670379f01e20f0e7e8bc23b3e5eedacd3f  
Source/test SHA: 80ccb48312cd816fa7f93cdb22ab27210f3a5e35

## Finding and scope

The Hardware-owned poll_fault_latch_edge_count_lab.py still owned its own C++ compile/run lifecycle with subprocess.run and tempfile.TemporaryDirectory even though the same PR already provided cpp_fixture_runner.py and a contract test for the shared runner.

This duplicated temporary-directory, compiler, process-execution and diagnostic behavior in a safety-critical host regression. The selected cleanup was limited to that one lab and its shared-runner contract guard. No production .ino, controller API, persistence implementation, finance, relay configuration, signer, witness, migration or Release workflow was changed.

## Test-first evidence

Test-only commit: cec8f13fe46d2593dc0352f6896e9ee295d9dd07.

The new source guard in cpp_fixture_runner_contract_lab.py requires poll_fault_latch_edge_count_lab.py to:
- import and call cpp_fixture_runner.run_cpp_fixture;
- preserve -pedantic and -O2;
- use explicit 30-second compile and 10-second execution bounds;
- provide fixture context;
- avoid direct subprocess/tempfile imports and calls.

Expected RED was observed on exact source/test SHA:
- Push Quarantine [run #45521119354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45521119354), job 138892918972: FAILED as expected.
- Exact error: poll_fault_latch_edge_count_lab.py duplicates shared runner mechanics: import subprocess.

This failure demonstrates the new guard detects the remaining duplicate implementation.

## Source correction

Commit: 80ccb48312cd816fa7f93cdb22ab27210f3a5e35.

poll_fault_latch_edge_count_lab.py now imports run_cpp_fixture and delegates temporary-file creation, compilation and execution to the shared runner. The fixture-specific C++17, -Wall, -Wextra, -Werror, -pedantic and -O2 flags are preserved; explicit compile_timeout=30 and run_timeout=10 are now applied. Baseline, repeated-ISR-latch mutation and pending-identity-clear mutation still run as separate named fixtures.

The new structural guard remains in cpp_fixture_runner_contract_lab.py so direct process/tempfile duplication cannot silently return to this lab.

## Exact-head CI

Quarantine Byte Readback:
- [PR run #45521336663](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45521336663), job 138893668237: SUCCESS at source/test SHA 80ccb483...
- POLL_FAULT_LATCH_SHARED_RUNNER_GUARD_PASS.
- CPP_FIXTURE_RUNNER_CONTRACT_PASS 8/8.
- First-fault ISR lab PASS for ESP8266 and ESP32.
- Active-high and active-low polarity scenarios PASS on both boards.
- SECOND_ISR_REPEATED_LATCH mutation rejected on both boards.
- PENDING_IDENTITY_CLEAR mutation rejected on both boards.
- The first-fault snapshot remains stable; later ISR evidence does not overwrite it; admission remains denied and outputs remain off.
- Existing quarantine, pending-journal, mount, pulse-capture and config-read failure suites in the same job also completed successfully.

Relay Output Polarity:
- [PR run #45521336668](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45521336668), source-output-polarity job 138893667791: SUCCESS.
- ESP32 boot-polarity job 138893668156: SUCCESS.
- Shared runner contract guard PASS; output, drain-window, poll-loop and pulse-capture regression steps PASS.

Full BlazePwifi:
- Push [run #45521329115](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45521329115), validation job 138893762549: FAILED at the inherited QA-owned assertion Missing poll signature check in tests/controllers.sh.
- ESP8266, ESP32, Ruijie, x86-64 and all required/optional Orange Pi target jobs completed SUCCESS (14/14 firmware/platform targets).
- Android job was still running at this handover checkpoint; downstream simulations/update/candidate/sign/publish stages were skipped after validation failure.
- This failure is not caused by the Python runner refactor. CORE owns the authenticated register/poll producer contract; QA owns independent assertion reconciliation. Do not synthesize response_sig or weaken deny-default to make the Full job green.

## Evidence classification and boundaries

- Shared runner consolidation: CI VERIFIED.
- First-fault edge-count scenarios: SIMULATED / CI VERIFIED host source extraction.
- Local independent execution: NOT RUN.
- Physical ISR timing, electrical pulse conditioning, relay contact state, LittleFS/EEPROM flash physics, power-loss recovery: NOT TESTED.
- 150 controlled power cuts and 30-device/24-hour soak: NOT TESTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO-GO.

## Parallel lineage reconciliation

- PR #340 already contains the pre-poll deny on both sketches and its poll_preflight_inhibit_lab.py; the temporary duplicate PR #350 was closed after this live-stack read. #340 remains OPEN / DRAFT / UNMERGED.
- The primary poll-window/edge-reconciliation line remains the separate #327→#339 stack. Do not collapse it into #283 or #340 without Master sequencing.
- #283 remains an independent deny-only/quarantine candidate; its quarantine helper is not evidence of an active production lifecycle.
- #348 remains blocked on the approved Mbed TLS 4 / PSA provider and stack decision from MASTER/RELEASE. No provider port was made here.
- Master-owned ROLE_ASSIGNMENTS.md and INTEGRATION_MATRIX.md were not edited; Master must refresh the #349 source/test and docs pins.

## Next exact action

After revalidating the live #349 head and workflow results, PHX-HARDWARE should remove one remaining local compile/run implementation from register_config_failclosed_lab.py using the same shared runner, with a test-first structural guard. CORE/QA continue to own the missing authenticated poll contract and its independent assertion review.
