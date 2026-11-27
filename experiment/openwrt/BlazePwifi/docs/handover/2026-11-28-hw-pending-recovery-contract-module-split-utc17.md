# PHX-HARDWARE — Pending recovery contract lab module split

**Date:** 2026-11-28 UTC17  
**Parent:** [PR #362](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/362), exact parent head `eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd`  
**Branch:** `phoenix/hw-pending-recovery-contract-module-split-20261128-utc17`  
**Source/test commit:** `d4f65ab7f72fabc6160cf70609a9258f1f757120`  
**Role:** PHX-HARDWARE · **Task:** cleanup-first #266 / recovery evidence maintainability.

## Change

Extracted source-contract assertions, guard-block parsing, fail-closed assertions and source mutation helpers from the 211-line `pending_recovery_promotion_lab.py` runner into the new `pending_recovery_promotion_lab_contract.py` module.

The runner now owns only orchestration: board sketch paths, source loading, mutation case invocation, C++ harness insertion, compile/run and summary output. The C++ fixture remains in `pending_recovery_promotion_lab_harness.hpp`.

No firmware sketch, runtime behavior, controller/API contract, financial state, QA-owned assertion, signer/witness, migration, COE destination or release behavior changed. The existing 15-scenario-per-board and 18-mutation matrix is intended to remain identical.

## Workflow

The Hardware workflow now includes the new module in push/PR path filters and includes this role branch in its push branch list. The new handover path is also watched. `CHANGE_LEDGER.md` is unchanged; the existing append-only guard remains in the workflow.

## Evidence

The source/test commit is `d4f65ab7f72fabc6160cf70609a9258f1f757120`. Exact-head Actions for this child are pending and must be checked before claiming CI VERIFIED. Parent #362's focused/Mbed results are not transferred to this child SHA. Full controller parity and QA-owned Native assertion blockers remain unresolved on the parent stack.

## Status and safety

- Host lab: SIMULATED until child exact-head CI passes.
- Physical LittleFS/electrical/relay acceptance: NOT TESTED.
- 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO-GO.

No physical flash/reset, live coin or money, production migration, signer provisioning, merge, release or deployment occurred.

## Next action

Run the child PR's exact-head focused Hardware workflow; inspect the named jobs and verify the runner still executes both board harnesses and all 18 unsafe mutations. Then request QA review of the semantic assertions without modifying QA-owned tests.
