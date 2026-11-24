# PHX-HARDWARE — dual-store lab shared C++ runner

**Checkpoint:** 2026-11-24T22:14:37Z  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** [`213c39942eb0c0a611655c5edd52bdee56249a78`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/213c39942eb0c0a611655c5edd52bdee56249a78)

## Selected owned task

Continue cleanup-first #266 in the Hardware-owned source-extracted dual-store poll-fault lab. The lab still used its own unbounded `g++` compile and executable subprocess calls for the baseline and three failure-injection variants. Those C++ processes had no compile or execution timeout, unlike other labs already using the shared bounded runner.

## Concrete source changes

- Added `_compile_and_run()` to delegate C++ source writing, compilation and execution to `cpp_fixture_runner.run_cpp_fixture()`.
- Replaced the four C++ compile/run paths: ESP32/ESP8266 baseline, missing-NVS-commit mutation, pre-commit-persistence mutation, and first-fault-snapshot-overwrite mutation.
- Preserved `-std=c++17 -Wall -Wextra -Werror`, source extraction, expected exit codes, stdout/stderr marker checks, board-specific prefixes, and all existing mutation payloads.
- Added explicit 30-second compile and 10-second execution bounds.
- Retained `subprocess` and `tempfile` only for the Python child-process external-CWD and temporary root-sentinel tests; those are not C++ fixture compilation paths.
- Added `poll_fault_dual_store_runner_guard.py`. It requires the shared import/helper, verifies both timeout bounds and all four callsites, and rejects direct `subprocess.run(["g++", ...])` calls.
- Updated `.github/workflows/phx-hardware-quarantine-byte-readback.yml` to run the structural guard and the existing `cpp_fixture_runner_contract_lab.py` before the dual-store lab. The existing contract lab contains eight timeout/diagnostic/temp-cleanup assertions.

No ESP8266/ESP32 sketch, CGI producer, CORE contract, QA-owned assertion, financial state, signer, witness, migration, release workflow or COE destination was modified.

## Validation and exact limitations

- GitHub source readback at PR head `213c39942eb0c0a611655c5edd52bdee56249a78`: static checks confirmed the shared import, 30s/10s bounds, four helper callsites, absence of direct C++ compiler subprocess calls, and both workflow invocations.
- The structural guard's expected RED condition is encoded as `POLL_FAULT_SHARED_RUNNER_IMPORT_MISSING`; **no RED Actions result is claimed** because no new PR-triggered Actions run was returned for the test/workflow commits.
- No new exact-head Quarantine, Relay or Full run was returned for `213c39942eb0c0a611655c5edd52bdee56249a78`. Combined commit status returned no statuses. The prior `8dbb2015` run is not transferable to this new source head.
- Local execution: **NOT RUN**. The available container could not resolve `github.com` for a local checkout. No local C++ or Python test result is claimed.
- Existing contract lab is wired into the workflow, but its 8/8 result is **NOT RUN on this head**.

## Prior-head evidence (not transferred)

At prior PR head `8dbb2015b11651f6d9864f53bb1368b5baa26790`:
- Quarantine [#45497219145](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45497219145) — SUCCESS.
- Relay [#45497219207](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45497219207) — SUCCESS.
- Full [#45497219108](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45497219108) — FAILURE at inherited `tests/controllers.sh` / `Missing poll signature check`; all 14 firmware/platform + Android jobs succeeded, validation failed, and dependent simulations/signing/publication were skipped.

These results validate only the previous SHA, not the new dual-store runner refactor.

## Ownership / release status

- #239 Phase A deny remains OPEN / DRAFT / UNMERGED.
- #254 ControllerAuthV1Lab remains OPEN / DRAFT / UNMERGED, stacked on #239.
- #283 remains a separate OPEN / DRAFT / UNMERGED parallel stack.
- #349 remains OPEN / DRAFT / UNMERGED, child of #347. No retarget, rebase, cherry-pick, merge or force-push.
- CORE owns the authenticated register/poll and event-bound receipt contract. QA owns reconciliation of the inherited poll-signature assertion. Keep poll/coin admission deny-default.
- Physical coin/relay/electrical acceptance, 150 controlled power cuts and 30-device 24-hour soak remain **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release acceptance remain **NOT ACCEPTED**.

**Source change status:** committed; CI verification pending.  
**SIMULATED:** no new simulation run on this head.  
**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## BLAZE-COMMS/1

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261124T22-DUAL-STORE-SHARED-RUNNER",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-QA"],
  "type": "PROGRESS",
  "priority": "P2",
  "task_id": "#172/#177/#266/#349",
  "branch": "phoenix/hw-json-array-primitive-guard-20261124-utc00",
  "base_sha": "960184670379f01e20f0e7e8bc23b3e5eedacd3f",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_runner_guard.py",
    ".github/workflows/phx-hardware-quarantine-byte-readback.yml"
  ],
  "status": "IN_PROGRESS",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4bebcf21d9f56ad59ad3168d4c9ae4492413b918",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/940403f472568f2bae9a6d4586146f4d6bc9b0f9",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/213c39942eb0c0a611655c5edd52bdee56249a78"
  ],
  "blockers": [
    "No exact-head GitHub Actions run/status was returned for the new source SHA.",
    "Local clone/test execution is unavailable because the container cannot resolve github.com.",
    "CORE/QA register-poll response-signature contract mismatch remains an inherited Full validation blocker."
  ],
  "next_action": "Trigger Quarantine, Relay and Full workflows at exact head 213c39942eb0c0a611655c5edd52bdee56249a78; then inspect terminal jobs and request QA review.",
  "updated_utc": "2026-11-24T22:14:37Z"
}
```
