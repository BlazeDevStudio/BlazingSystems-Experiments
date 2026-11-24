# PHX-HARDWARE — poll-window fixture modularization (2026-11-24 UTC13)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / Hardware DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `839c72ac68bb1f0a8fd9a2fc74a166cec15b624e`  
**Workflow/path-filter SHA before this handover:** `7babbc0b6f32a068198ecc9a6d341366033f287a`  
**Master PR #288 read-time HEAD:** `ba356baf4acb3921d2fd5c7373e4dd4decfaabd4`  
**Status:** source cleanup committed; focused CI verified; full integration remains blocked; physical hardware not tested; production NO-GO.

## Scope and source changes

This is a non-behavioral, Hardware-owned test-harness cleanup. The 777-line `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` previously mixed the shared C++ scenario base with poll/ISR timing, race and release-edge programs.

- Moved the 252-line tail beginning at `COIN_POST_ISR_MAIN` into the new `poll_loop_blocking_inhibit_lab_poll_window_fixtures.py` (271 lines including module documentation, import and explicit exports).
- Reduced `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` from 777 to 527 lines; it now exports only the shared `MAIN` base.
- Kept the stable `poll_loop_blocking_inhibit_lab_fixtures.py` facade and redirected its public timing/scenario names to the new module. The runner's import contract is unchanged.
- Updated the Relay Output Polarity workflow's **push and pull_request** path filters for the facade, runtime/scenario/poll-window/edge/response fixture modules and this handover. Removed a duplicate edge-fixture path. This ensures a fixture-only edit is not silently outside the focused workflow trigger.

The extracted source block was reconstructed byte-for-byte before commit. No production `.ino`, CGI producer, controller protocol, credit/ledger, relay policy, financial schema, signer, witness, migration or COE destination file changed.

## Exact-head CI at workflow head `7babbc0b6f32a068198ecc9a6d341366033f287a`

- Relay Output Polarity [run #45407147148](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45407147148):
  - ESP32 boot job `138490814893`: **SUCCESS**.
  - Source/output job `138490814904`: **SUCCESS**.
  - Logs show the poll-loop, source-extracted response, bounded HTTP, poll-window timeline and mutation-rejection suites completed. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0` and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

- Quarantine Byte Readback [run #45407147138](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45407147138):
  - `quarantine-source` job `138490814204`: **SUCCESS**.
  - Its log includes the ESP8266 config-read failure/migration guards, 17/17 coin-pulse capture cases per board and fail-open mutation rejection, plus explicit simulated-only/physical-not-verified markers.

- Full BlazePwifi build [run #45407147127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45407147127):
  - Validation job `138490982969`: **FAILURE** at the existing `tests/controllers.sh` assertion `Missing poll signature check`.
  - At handover creation, 12/13 firmware target jobs had completed SUCCESS; ESP32, ESP8266 and the other completed target jobs were green. Orange Pi PC and Android were still running. No terminal 14/14 matrix claim is made here.
  - Validation-dependent update, simulation, candidate, signing and publication jobs were skipped.

**Local tests:** NOT RUN; no local checkout was available. The focused GitHub Actions results above are the executed tests, not physical acceptance.

## Contract and release boundary

The current register/poll producer still has no approved authenticated `response_sig` envelope for this consumer, while the inherited QA assertion requires one. CORE owns the versioned producer contract and canonical bytes/golden vectors; QA owns independent assertion reconciliation. Hardware did not invent a signature, edit QA-owned tests, or relax default-deny.

The 7-role Master dispatcher and current assignment documents were re-read. Master PR #288 remains the coordination-only DRAFT; this role did not edit Master-owned assignments or shared APIs. Protected Hardware PRs #239, #254 and parallel #283 were revalidated and left untouched. COE #26 remains FROZEN; no migration or bulk copy was attempted.

The owner-uploaded `04_HARDWARE_FIRMWARE(1).txt`, `README_FIRST`, `COMMUNICATION_PROTOCOL` and hourly signal YAML were read. The signal YAML is heartbeat-only and does not wake AI workers. The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not accessible through the available Drive/Library connector surface; older registry snapshots were not substituted.

## Evidence classification and next action

- Test harness: **CI VERIFIED** at the exact workflow head above.
- Board/coin/relay/electrical behavior: **SIMULATED** only; physical acceptance **NOT TESTED**.
- 150 controlled power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, v1-to-v2 financial migration, durable accounting/replay and independent QA/release signoff: **NOT ACCEPTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-MASTER refresh its own #349 source/test/docs pins after this handover commit; PHX-CORE publishes the approved authenticated register/poll contract; PHX-QA independently reconciles the assertion without weakening deny-only behavior; PHX-HARDWARE reruns Full validation at the resulting approved contract SHA.
