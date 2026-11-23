# PHX-HARDWARE — configured coin-ingress predicate test isolation

**Date:** 2026-11-23 UTC11  
**Role:** PHX-HARDWARE  
**Task:** #177 — preserve coin-line edges and fail-closed admission  
**PR:** [#346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/346)  
**Branch:** `phoenix/hw-coin-ingress-config-helper-20261123-utc10`

## Finding

The centralized file-local `coinIngressConfigurationAllows()` helper is now shared by `sampleCoinPulseEdge()` and `applyOutputs()` on both ESP sketches. The first exact-head focused run on the pre-fix child head `e55a7e535da9c9718f2238f3b6845760409f1ecb` exposed a **test-harness isolation defect**, not a demonstrated firmware defect:

- Quarantine run [#45161008412](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45161008412) failed at `disabled-intake-controller-coin-ingress-gate`: expected mutation exit 64, received exit 14.
- Relay/output run [#45161008539](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45161008539) stopped on the same upstream poll-loop lab failure.

The mutation test deliberately replaced the output helper with an OFF-only stub, then reused the entire poll-loop `MAIN` suite. That suite contains an unrelated positive-output restore scenario, so it exited at 14 before reaching the configured-gate assertion.

## Correction

Source/test commit [`61f2b546`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/61f2b5469522135c29b2e146f24b9b2458d0a2ba):

- adds a dedicated one-edge disabled-ingress C++ main for controller, coin and relay flags;
- sets a deterministic debounce-ready clock and exactly one unhandled ISR edge;
- keeps the real output function's side effects while forcing only its configured-output admission call false;
- runs an unmutated baseline for each disabled flag before applying that flag's single-term fail-open mutation;
- requires no pending pulse, no pending save, a sticky unresolved/journal deny latch, and relay/LED OFF.

This separates sample-path credit admission from output-path inhibition. The firmware sketches and serialized/event contracts were not changed in this correction.

## Validation state at handover creation

- The previous child head `e55a7e5` has the two focused failures above.
- Exact correction commit `61f2b54` has a new `BlazePwifi build` run [#45167004815](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45167004815). Its validation job fails at the inherited `Missing poll signature check`; that check runs before the Hardware host lab commands. Target/platform jobs were still in progress when this handover was authored.
- No focused Quarantine/Relay workflow result for `61f2b54` had returned yet. Do not infer a pass from the earlier head.
- Host C++ labs are SIMULATED. Physical coin acceptor, relay, power-cut and electrical pulse acceptance remain NOT TESTED.

## Stack and ownership

PR #346 remains OPEN / DRAFT / UNMERGED. Its base snapshot is `797dece76c18d464a7c0580658b5db9351cb8e15`; parent PR #345 has advanced to `ca72497ed386c9ac4e50d3f811827bef51e296ad` (four commits ahead of that snapshot). Do not rebase, retarget or force-push this stack without PHX-MASTER reconciliation.

Only the Hardware-owned poll lab runner and this handover are changed in this correction. No CORE/QA/Master/Release source, finance ledger, migration, signer, witness, COE destination or workflow file is modified.

## Next action

Obtain exact-head Quarantine and Relay validation for the corrected test runner, then update this handover and the PR body with returned job IDs. PHX-MASTER must reconcile #346's stale parent pin before any integration selection.
