# PHX-HARDWARE — poll response-denial matrix modularization (2026-11-24 UTC16)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / Hardware #177 / DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** [`6cfd2e094ad4ec4a546a3d202f2e2cbe1259822d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6cfd2e094ad4ec4a546a3d202f2e2cbe1259822d)  
**Workflow path correction:** [`b950914f20f6b2c3622e8462b31578fc24cdcda9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b950914f20f6b2c3622e8462b31578fc24cdcda9)  
**Starting docs/workflow HEAD for this handover:** `b950914f20f6b2c3622e8462b31578fc24cdcda9`  
**Disposition:** cleanup-only test refactor; focused source-extracted CI PASS at exact source/test SHA; physical hardware NOT TESTED; production NO-GO.

## Selected task and source change

The 727-line `poll_loop_blocking_inhibit_lab.py` still embedded an 88-line no-edge HTTP response-denial matrix in its per-board orchestration loop. The matrix covered hostile-positive and empty-timeout responses, keyless response-looking data, active-high/active-low relay polarity, and fail-open mutations.

The exact scenario block was moved into:

`poll_loop_blocking_inhibit_lab_response_contracts.py`

The runner now calls `run_poll_response_denial_matrix(...)` and passes its board, extracted accept function, support text, timeout fixture, compile/assemble callbacks, active-low fixture transformer, loop and output source explicitly. The runner shrank **727 → 649 lines**; the new module is 116 lines including module documentation/imports/signature.

The module imports only the two response fixture constants it owns. No response bytes, C++ scenario payloads, expected exit codes, mutation anchors or test semantics were intentionally changed. The signature-looking test value remains a non-protocol placeholder.

Relay workflow push and pull-request filters now watch the new module and this handover. Quarantine already watches the ESP8266 lab directory; its push and pull-request filters now also watch this narrow handover. The second workflow commit explicitly corrected both event path arrays.

## Exact source/test-head CI evidence — `6cfd2e09`

**Relay Output Polarity LAB** — [run #45441003768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45441003768)
- Job `138611756674`: **SUCCESS**.
- ESP8266 and ESP32 each passed six no-edge response baselines: hostile-positive and empty-timeout under active-high and active-low relay polarity, plus keyless response under both polarities.
- Six fail-open mutations per board were rejected with expected exit 90 (12/12 total).
- Existing active-low pre-poll inhibit and blocking-poll edge/fault regressions also ran in this job.
- Logs explicitly report `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

**Quarantine Byte Readback LAB** — [run #45441003699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45441003699)
- Job `138611759119`: **SUCCESS**.
- Both boards reported `POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_AFTER_LATER_ISR_PASS`.
- Both boards passed the same six response-denial baselines and rejected all 12 fail-open mutations.
- Existing LittleFS fake-store, pending journal, config-read recovery, pulse capture and boot-polarity failure-injection suites completed successfully.
- Logs explicitly retain `SIMULATED_ONLY=1` and `PHYSICAL_POWER_CUT_VERIFIED=0`.

**Full BlazePwifi build** — [run #45441003701](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45441003701)
- Validation job `138611759041`: **FAIL** at the inherited QA-owned `Missing poll signature check` in the ESP8266 sketch.
- At handover creation, remaining target/platform jobs were still running; no 14/14 target claim is made here. Final docs-head results are recorded in the PR conversation after completion.

Local test execution: **NOT RUN**. The focused evidence is GitHub-hosted source-extracted C++ simulation, not electrical or physical hardware acceptance.

## Scope and safety

No production `.ino`, CGI producer, register/poll API, financial ledger, signer, witness, migration, release workflow, COE destination or device configuration was changed. No positive poll authorization or signature was synthesized. Default-deny remains intact.

The current main CGI producer still emits no approved `response_sig` for `register|ping` or `poll`; the inspected signatures belong to separate member endpoints. PHX-CORE owns the authenticated producer contract and canonical vectors; PHX-QA owns reconciliation of the legacy positive poll-signature assertion. HARDWARE must not weaken the consumer gate.

## Live coordination and blockers

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Master PR #288: `359ef46213e8191c4e6831fd82cc2afca03a0142`, OPEN / DRAFT / UNMERGED. Master-owned `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and architecture status still need refresh to current Hardware pins; Hardware did not edit them.
- Cleanup #266 remains OPEN with 0/7 checklist items complete. Hardware #177 remains P0 and OPEN.
- Protected stacks remain unchanged: #239 at `d83b715b116185107737fef721c2eece8feebf39`, #254 at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, and #283 at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`.
- #283 audit remains: `quarantinePending()` returns false on append failure before `clearPending()`, but is definition-only with no active callsite; current main register/poll replies lack an approved response signature. No source transfer or positive authorization is permitted.
- The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the connected Files Library, and no Google Drive connector is available in this execution. No older registry snapshot was substituted.

## Acceptance status

| Requirement | Status |
|---|---|
| Extracted response-denial matrix | CI VERIFIED |
| Host/source-extracted board scenarios | SIMULATED |
| Local independent test run | NOT RUN |
| Physical coin/relay electrical acceptance | NOT TESTED |
| 150 controlled power cuts | NOT TESTED |
| 30-device / 24-hour soak | NOT TESTED |
| Protected anti-rollback signer/witness | NOT ACCEPTED |
| Durable accounting/replay and v1→v2 migration | NOT ACCEPTED |
| Independent QA / release acceptance | PENDING |

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Next exact action

PHX-HARDWARE: verify both focused workflows on the final handover/docs head and report their exact run/job IDs in the existing UTC16 PR checkpoint. PHX-MASTER: refresh its own Hardware pins. PHX-CORE and PHX-QA: resolve the authenticated register/poll contract and legacy assertion without relaxing default-deny.
