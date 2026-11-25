# PHX-HARDWARE — poll edge-race and fail-closed mutation modularization (2026-11-24 UTC17)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / P0 Hardware #177 / existing DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent/base:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** [`aa9ac766ee5316b35dfdb2942247127641647d2b`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/aa9ac766ee5316b35dfdb2942247127641647d2b)  
**Disposition:** cleanup-only host/source-extracted lab refactor; focused CI VERIFIED; Full validation remains blocked; physical acceptance NOT TESTED; production NO-GO.

## Selected task and concrete source changes

The 649-line `poll_loop_blocking_inhibit_lab.py` still contained a 396-line per-board block covering the original 1501/1600/1680 ms pulse timeline, active-low relay behavior, poll-release ISR races, drain ordering, first-fault stability and fail-closed mutation matrices.

The exact scenario blocks were extracted into two responsibility-specific modules:

- `poll_loop_blocking_inhibit_lab_edge_race_contracts.py` — 239 source lines moved; 281 module lines including documentation/imports/signature.
- `poll_loop_blocking_inhibit_lab_failclosed_mutation_contracts.py` — 156 source lines moved; 187 module lines including documentation/imports/signature.

The runner now delegates to `run_poll_edge_race_contracts(...)` and `run_poll_failclosed_mutation_contracts(...)`, passing board source, assembly/compile callbacks and the required extracted helpers explicitly. The runner is now **289 lines** (649 → 289). The active-low output mutation is passed explicitly to the edge contract rather than relying on a runner local/global.

The Relay workflow push and pull-request filters now watch both new modules and the previously extracted pending-identity module. Both Relay and Quarantine push/PR filters watch this narrow handover. Quarantine already watches the ESP8266 lab directory for source modules.

No C++ fixture payload, expected exit code, mutation anchor or scenario order was intentionally changed. No production `.ino`, CGI producer, shared response contract, ledger, signer, witness, migration, release pipeline or COE destination file changed.

## Test-first failure and correction

The first extraction commit [`fa1e1fa5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/fa1e1fa5913635fa421cbcf64aa9089895a6f98a) exposed a missing captured dependency: Relay [run #45452591447](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45452591447), job `138653405953`, failed with `NameError: poll_output_mutation is not defined`.

The dependency was made explicit in the edge-contract function signature and its single call site. The correction is source/test commit `aa9ac766`; the exact-head focused runs below pass. The initial failure is retained as a test-first regression, not hidden or represented as a pass.

## Exact source/test-head CI — `aa9ac766`

**Relay Output Polarity LAB** — [run #45453000020](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45453000020)
- Source/output job `138654845879`: **SUCCESS**.
- ESP32 boot-polarity job `138654845132`: **SUCCESS**.
- Both ESP8266 and ESP32 report `PHX_177_ORIGINAL_1501_1600_1680_TIMING_PASS` and `PHX_177_ACTIVE_LOW_RELAY_1501_1600_1680_TIMING_PASS`.
- Both boards report `POLL_HTTP_ACTIVE_LOW_RELAY_INHIBIT_PASS`, `POLL_RELEASE_LED_WRITE_ISR_EDGE_BLOCKS_RELAY_PASS`, and `POLL_RELEASE_RELAY_WRITE_ISR_EDGE_DEASSERTED_PASS`.
- Current-CGI register/poll no-signature deny and fail-open consumer mutations remain rejected. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

**Quarantine Byte Readback LAB** — [run #45452999974](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45452999974)
- Job `138654844964`: **SUCCESS**.
- Both boards report `POLL_FAULT_FIRST_LATCH_SNAPSHOT_STABLE_AFTER_LATER_ISR_PASS`; the first fault snapshot remains stable after later ISR edges.
- Both boards pass the extracted timing/active-low release cases and existing pulse-capture, quarantine, pending-clear, boot-polarity and fake-store failure-injection suites.
- Logs explicitly retain `SIMULATED_ONLY=1` and physical coin/relay/power-cut acceptance flags at zero.

**Full BlazePwifi build** — [run #45452999881](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45452999881)
- Validation job `138655025225`: **FAIL** at the inherited `Missing poll signature check` in the ESP8266 sketch, during Controller protocol parity.
- All **13 firmware target/platform jobs plus Android (14/14)** completed **SUCCESS**.
- Validation-dependent browser/device simulations, candidate gate, update bundle, signing handoff and publication jobs were **SKIPPED**. This is not a Full validation or release pass.

Local test execution: **NOT RUN**. Focused evidence is GitHub-hosted host/source-extracted simulation, not electrical or physical hardware acceptance.

## Contract and protected-stack audit

- Current main CGI producer still has no approved `response_sig` in `register|ping` or `poll`. PHX-CORE owns the versioned authenticated producer contract and canonical vectors; PHX-QA owns independent reconciliation of the legacy positive assertion. HARDWARE did not invent a signature or weaken default-deny.
- PR #283 remains OPEN/DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. Its `quarantinePending()` helper returns false when append fails before `clearPending()`, but is definition-only with no active callsite. This audit lead is not treated as a production fix or authorization to add a callsite without the agreed disposition contract.
- Protected PR #239 remains OPEN/DRAFT at `d83b715b116185107737fef721c2eece8feebf39`; #254 remains OPEN/DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`. Neither stack was edited.
- Cleanup #266 remains OPEN / 0-of-7; Hardware #177 remains OPEN / P0. No checklist completion is claimed.

## Coordination and provenance

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; development: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master PR #288: `359ef46213e8191c4e6831fd82cc2afca03a0142`, OPEN/DRAFT/UNMERGED. Its Master-owned `ROLE_ASSIGNMENTS.md` still pins Hardware #349 to older source/test `4d36d08b` and docs `7eab7194`; `INTEGRATION_MATRIX.md` still pins `7eab7194`. Hardware requests Master refresh its own assignment/matrix/architecture records to source/test `aa9ac766` and the final handover/docs head.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains frozen at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No destination migration or source promotion occurred.
- The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the connected Files Library, and no Google Drive connector is exposed in this execution. The older `BLAZE_PRODUCTION_CHECKPOINT_20261109_v2.json` only points to the historical v11 Drive ID; it is not a substitute for the canonical registry. No older registry was promoted as current provenance.

## Acceptance status

| Requirement | Status |
|---|---|
| Edge-race and fail-closed lab modularization | CI VERIFIED |
| Host/source-extracted poll/relay/persistence scenarios | SIMULATED |
| Full firmware target/platform + Android matrix | CI VERIFIED (14/14) |
| Full controller protocol validation | FAILED — inherited CORE/QA contract assertion |
| Local independent test execution | NOT RUN |
| Physical coin/relay/electrical acceptance | NOT TESTED |
| 150 controlled power cuts | NOT TESTED |
| 30-device / 24-hour soak | NOT TESTED |
| Protected anti-rollback signer/witness | NOT ACCEPTED |
| Durable accounting/replay and v1→v2 migration | NOT ACCEPTED |
| Independent QA / release signoff | PENDING |

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Next exact actions

1. PHX-MASTER refreshes its own Hardware #349 role/integration/architecture pins.
2. PHX-CORE publishes the approved versioned authenticated register/poll response contract and golden vectors.
3. PHX-QA independently reconciles `Missing poll signature check` without weakening deny-default.
4. PHX-HARDWARE verifies the final handover/docs-head focused workflows, then re-reads all live heads/assignments before selecting the next owned reversible task.

No Codex, force-push, merge, flash, reset, live-money operation, financial migration, signer provisioning, release tagging or deployment occurred.
