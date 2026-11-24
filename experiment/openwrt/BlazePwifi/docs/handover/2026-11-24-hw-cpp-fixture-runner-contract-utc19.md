# PHX-HARDWARE handover — shared C++ fixture runner contract tests

**Checkpoint:** 2026-11-24T19:05:21Z  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test/workflow SHA:** 3551da26e57d5273b54f434fe312ab2fc02bc22f

## Selected owned task

Add failure-injection contract tests for the shared Hardware C++ fixture runner now used by multiple board labs. The tests remain in the Hardware-owned poll-response structure guard and execute through the existing Relay/Quarantine lab workflows.

## Concrete changes

- Reject booleans, zero, negative, non-finite, string and null timeout values before any subprocess invocation.
- Verify bounded text/byte diagnostics and invalid UTF-8 replacement.
- Inject compile failure and assert the binary is not run, diagnostic output is bounded, and temporary files are cleaned.
- Inject compile and execution timeouts and assert both stdout/stderr tails are retained within the diagnostic cap and temporary directories are removed.
- Verify the successful compile/run path preserves C++17 warning/error flags, extra flags, default 30-second compile / 10-second execution bounds, and temporary-directory cleanup.
- Extend Relay and Quarantine path filters so changes to the shared runner, its contract guard, and this handover trigger exact-head validation.

No production sketch, CGI producer, shared response API, financial ledger, signer, witness, migration, QA-owned assertion, or COE destination source is changed.

## Evidence classification

The new runner-contract tests are host-side failure-injection tests. They validate the test infrastructure only; they do not prove coin, relay, power-loss or financial behavior.

- Local independent execution: NOT RUN.
- GitHub Actions exact-head results: pending at handover creation; record returned run/job IDs in the PR and control-plane checkpoint.
- Physical coin pulse / relay electrical acceptance: NOT TESTED.
- 150 controlled power cuts and 30-device 24-hour soak: NOT TESTED.
- Protected anti-rollback signer/witness, durable accounting/replay and v1-to-v2 migration: NOT ACCEPTED.
- PRODUCTION NO-GO.

## Coordination / next exact action

- PHX-MASTER: refresh the #349 source/test and docs-head pins in Master-owned coordination files; do not retarget the stack without reconciling #347.
- PHX-CORE: publish the approved authenticated register/poll contract and event-bound receipt/disposition vectors.
- PHX-QA: reconcile the inherited Full-build `Missing poll signature check` assertion independently; do not weaken deny-default.
- PHX-HARDWARE: verify the exact-head focused workflows and preserve the #349 DRAFT stack; next work requires fresh live-head and assignment checks.

Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the connected Files Library, and no Google Drive connector is exposed. No older registry snapshot was substituted.

No Codex, merge, force-push, flash, device reset, live-money operation, production migration, signer provisioning, release tag, deployment or COE destination write occurred.
