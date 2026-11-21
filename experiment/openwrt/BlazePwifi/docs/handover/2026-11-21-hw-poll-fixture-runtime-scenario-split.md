# PHX-HARDWARE handover — poll-loop fixture runtime/scenario split

**Updated:** 2026-11-21T00:42:35.615Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `177312434b60509638427cec79bf2d4e11d89d97`

## One owned cleanup task

The 779-line `poll_loop_blocking_inhibit_lab_fixtures.py` was still a single mixed module after the prior runner/fixture separation. It combined fake C++ runtime I/O semantics and individual fault-injection scenario programs.

The source/test commit splits those responsibilities while preserving the runner's existing import surface:

- `poll_loop_blocking_inhibit_lab_runtime_fixtures.py` — 287 lines; `STUBS` and `SUPPORT`.
- `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` — 499 lines; `MAIN`, race/timing/release fixtures, and active-high/active-low scenario builders.
- `poll_loop_blocking_inhibit_lab_fixtures.py` — 29-line compatibility facade that re-exports the same public names used by the unchanged runner.

The original embedded fixture payload was sliced at the `MAIN = r"""` boundary. A pre-commit byte-preservation assertion confirmed that the runtime payload plus scenario payload exactly equals the original fixture payload. The Python orchestration runner remains unchanged (447 lines). No embedded C++ test logic or production firmware was rewritten.

## Exact-source CI — source/test SHA `177312434b60509638427cec79bf2d4e11d89d97`

- Quarantine push [run #44845321371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845321371), job `136663473634`: **SUCCESS**.
- Quarantine PR [run #44845326974](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845326974), job `136663494900`: **SUCCESS**.
- Relay/output PR [run #44845327017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845327017), jobs `136663494994` and `136663495323`: **SUCCESS**.

The Quarantine job imported and executed the new facade/modules. Logs show:

- `POLL_LOOP_BLOCKING_INHIBIT_WORKFLOW_WIRING=PASS`
- `POLL_LOOP_BLOCKING_INHIBIT_RUN_ONCE=PASS`
- `MUTATION_REJECTED nested-poll-loop-lab-runner`
- ESP8266 and ESP32 coin-pulse capture: 16/16 each, with missing-edge, debounce, overflow, target-drift, save-failure, fault-latch and ISR-reconciliation mutations rejected.
- Poll-response default-deny: 11/11 per board; strict root JSON: 13/13 per board; coin disposition default-deny: 4/4 per board.
- Poll-window timeline guard passed; the missing final quiet-sample mutation was rejected (exit 25).
- Existing poll-fault marker and boot/recovery fault-injection cases executed in the same job.

These are host/fake-I/O SIMULATED tests, not physical electrical acceptance.

## Full validation remains blocked

- Full PR build [run #44845327084](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845327084), validation job `136663496550`: **FAILURE** at the QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`.
- The companion Full push [run #44845321368](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44845321368) has the same validation failure (job `136663474782`). At the last poll, 13 firmware target jobs had completed SUCCESS and Android was still running; no overall Full workflow pass is claimed.
- The Full PR target matrix was still running when this handover was written. No final matrix result is claimed.
- Signed APK import, update bundle and V04 simulation gates were skipped after validation failed.

The assertion is QA-owned and expects a positive poll signature that the current main register/poll producer does not emit. Firmware remains default-deny. No QA assertion, shared API or response contract was changed.

## Ownership and safety

Only the Hardware-owned host-lab fixture module boundary and this narrow handover changed. No production `.ino`, GPIO/polarity, register/poll API, financial ledger, QA-owned test, Release workflow, COE destination, secret, physical device or customer state changed. No Codex, physical flashing, live money, production migration, signing, merge or deployment was used.

Evidence classification: **SIMULATED / CI VERIFIED** for the host-lab module split and focused tests. Physical coin/electrical/relay acceptance, 150 power cuts and the 30-device/24-hour soak remain **NOT TESTED**. **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Next exact action

PHX-CORE must publish the approved authenticated register/poll and coin-disposition contract with canonical bytes/vectors; PHX-QA must replace the stale positive poll-signature assertion with source-exact default-deny tests until that contract is approved. PHX-MASTER must refresh the stale Hardware active-branch/PR pins in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`. PHX-HARDWARE revalidates the live stack before the next owned firmware change.
