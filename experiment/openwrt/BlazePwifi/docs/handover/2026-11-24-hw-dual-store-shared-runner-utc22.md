# PHX-HARDWARE — dual-store lab shared C++ runner

**Checkpoint:** 2026-11-24T22:29:29Z  
**Role:** PHX-HARDWARE  
**Tasks:** #172 / #177 / #266 / PR #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Base #347:** `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Current source/test commit:** [`0aba4cd66deae4c358dec950ace1e86be3241674`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0aba4cd66deae4c358dec950ace1e86be3241674)

## Selected owned task

Continue cleanup-first #266 in the Hardware-owned source-extracted dual-store poll-fault lab. The lab had four local C++ compile/run paths with no compile or execution timeout. The repository already had a shared bounded runner, so this duplicated process lifecycle was unnecessary and could leave CI blocked indefinitely.

## Concrete source changes

- Added `_compile_and_run()` to delegate C++ source writing, compilation and execution to `cpp_fixture_runner.run_cpp_fixture()`.
- Replaced the four C++ compile/run paths: baseline, missing-NVS-commit mutation, pre-commit-persistence mutation, and first-fault-snapshot-overwrite mutation.
- Preserved C++17, `-Wall -Wextra -Werror`, source extraction, expected exit codes, stdout/stderr marker checks, board-specific prefixes, and mutation payloads.
- Set explicit 30-second compilation and 10-second execution bounds.
- Retained `subprocess` and `tempfile` only for the Python external-CWD and root-sentinel self-tests.
- Added `poll_fault_dual_store_runner_guard.py`, which requires the shared import/helper, all four callsites and timeout bounds, and rejects direct C++ compiler subprocess calls.
- Updated `.github/workflows/phx-hardware-quarantine-byte-readback.yml` to run the structural guard and existing `cpp_fixture_runner_contract_lab.py` before the dual-store lab.

No ESP8266/ESP32 production sketch, CGI producer, CORE contract, QA-owned assertion, financial state, signer, witness, migration, Release workflow or COE destination was modified.

## Exact-source validation

<badge>CI VERIFIED — source-extracted only</badge>

At exact source/test SHA `0aba4cd66deae4c358dec950ace1e86be3241674`:

- Quarantine [run #45500875662](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875662), job `138823500132`: **SUCCESS**.
  - `POLL_FAULT_SHARED_RUNNER_STRUCTURE_PASS`.
  - `CPP_FIXTURE_RUNNER_CONTRACT_PASS 8/8`.
  - `POLL_FAULT_DUAL_STORE_LAB=PASS` on ESP32 and ESP8266.
  - Existing first-fault snapshot, NVS commit failure, poll-drain and persistence mutation checks passed.
  - Remaining Quarantine job steps, including EEPROM/config recovery, pulse-capture and boot-polarity checks, also completed SUCCESS.
- Relay [run #45500875749](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875749): **SUCCESS**.
  - Source/output job `138823500384` and ESP32 boot-polarity job `138823501283` both SUCCESS.
  - Relay output polarity: 48/48 source-extracted scenarios per board.
  - Bounded HTTP response: both boards PASS.
  - Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

### Failure and correction

The first Quarantine run at prior head `a3bfae23e038865126e82a6e4dee0d104927c12f`, [run #45500156896](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500156896), failed in the new guard's AST parse because the initial `run()` replacement left the required-marker block over-indented (`IndentationError`, line 373). This was a real failure introduced by the first refactor, not an expected RED. It was corrected in [commit `0aba4cd`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0aba4cd66deae4c358dec950ace1e86be3241674); the exact-source Quarantine and Relay runs above passed after that correction.

### Full integration status

[Full run #45500875722](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875722) checked out merge commit `35a4eab` for prior PR head `a3bfae23`, not source SHA `0aba4cd`. Its validation job `138823501834` failed at `tests/controllers.sh` with **`Missing poll signature check`**. All 13 firmware/platform target jobs completed SUCCESS; Android was still in progress at last poll. Simulations, signed import, signing and publication were skipped. This Full result is prior-head evidence and does not transfer to `0aba4cd`.

No exact-source Full run on `0aba4cd` has been verified yet. CORE owns the authenticated register/poll response contract; QA owns reconciliation of the inherited assertion. Do not synthesize `response_sig`, weaken the assertion, or enable positive poll/coin admission.

## Other live stack audits

- #239 Phase A deny: OPEN / DRAFT / UNMERGED at `d83b715b116185107737fef721c2eece8feebf39`.
- #254 ControllerAuthV1Lab: OPEN / DRAFT / UNMERGED at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, stacked on #239. Focused exact-head sanitizer run #44683629378 PASS; Full #44683629491 FAIL at ESP32 core 4.0.0 missing `mbedtls/sha256.h` and validation CHANGE_LEDGER freshness. Helper remains non-actuating and unwired.
- #283 parallel sketches: OPEN / DRAFT / UNMERGED at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. The original unconditional-clear lead from comment #6883020442 is **not present**: failed quarantine append returns false before `clearPending()`; `quarantinePending()` is definition-only with no active callsite. Current main CGI `register|ping` and `poll` still lack the approved `response_sig`; member endpoint signatures do not authenticate controller poll. Physical LittleFS torn-write/power-loss recovery remains NOT TESTED.
- Parent #347 remains the base for #349 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`; no cross-stack cherry-pick, retarget, rebase or merge.

## Ownership / release status

- #266 remains OPEN / **0-of-7** role tracks complete; this is one bounded Hardware contribution.
- #177 P0 synchronous poll/coin-pulse loss remains open. These lab checks do not certify physical coin capture.
- #31 durable prepaid event idempotency / crash-atomic member transfer, #32 rental lease/receipt consistency, #43 independent freshness witness, and #34 physical acceptance remain release blockers.
- 150 controlled power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff remain NOT TESTED or NOT ACCEPTED.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the accessible Library search/list; only an older v7 registry was visible. No Google Drive connector is exposed in this activation. The older registry was not substituted.

**Source change:** committed.  
**Focused Quarantine / Relay:** CI VERIFIED (SIMULATED source-extracted tests only).  
**Full integration:** FAILED at inherited QA-owned poll-signature assertion on prior merge head; current-source Full pending.  
**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## BLAZE-COMMS/1

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261124T22-DUAL-STORE-SHARED-RUNNER",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-CORE", "PHX-QA"],
  "type": "PROGRESS",
  "priority": "P2",
  "task_id": "#172/#177/#266/#349",
  "branch": "phoenix/hw-json-array-primitive-guard-20261124-utc00",
  "base_sha": "960184670379f01e20f0e7e8bc23b3e5eedacd3f",
  "source_test_sha": "0aba4cd66deae4c358dec950ace1e86be3241674",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_runner_guard.py",
    ".github/workflows/phx-hardware-quarantine-byte-readback.yml"
  ],
  "status": "VERIFIED",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0aba4cd66deae4c358dec950ace1e86be3241674",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875662",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45500875749",
    "POLL_FAULT_SHARED_RUNNER_STRUCTURE_PASS",
    "CPP_FIXTURE_RUNNER_CONTRACT_PASS 8/8",
    "POLL_FAULT_DUAL_STORE_LAB=PASS on ESP32 and ESP8266"
  ],
  "blockers": [
    "Full integration validation still fails at the inherited Missing poll signature check on prior merge head.",
    "Exact-source Full run after the source correction is not yet verified.",
    "Physical coin, relay, power-cut and 30-device soak acceptance remain NOT TESTED.",
    "Protected witness, durable accounting/replay and v1-to-v2 migration remain NOT ACCEPTED.",
    "Google Drive registry v11 is not accessible through the available connector surface."
  ],
  "next_action": "Refresh the exact-source Full result after handover pinning; Master to update its coordination pins; CORE/QA to publish and reconcile the authenticated register/poll contract without weakening deny-default.",
  "updated_utc": "2026-11-24T22:29:29Z"
}
```
