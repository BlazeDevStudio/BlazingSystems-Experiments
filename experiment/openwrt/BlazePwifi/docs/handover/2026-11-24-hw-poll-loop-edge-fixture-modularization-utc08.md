# PHX-HARDWARE UTC08 — blocking-poll scenario fixture modularization

**Role:** PHX-HARDWARE  
**Tasks:** #177 / #266 / #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**PR:** [#349 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Parent/base:** #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** `6ce423783b306411bdb7e7217081c050cb4cbec4`  
**Handover timestamp:** `2026-11-24T08:19:29.828Z`

## One bounded cleanup task

The blocking-poll host lab had accumulated C++ scenario strings and board-parity contracts inside its orchestration file. The task moves those definitions into:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_edge_fixtures.py`

Moved without editing their contents:

- `ACTIVE_HIGH_MISSED_SAMPLE_MAIN` / `ACTIVE_LOW_MISSED_SAMPLE_MAIN`
- `STICKY_FAULT_LATER_ISR_MAIN`
- `ATTEMPTED_EVIDENCE_MAIN`
- `disabled_ingress_gate_main()`
- `pre_poll_active_line_main()`
- `POLL_SAFETY_PARITY`
- `REQUIRED_COIN_AUTHORITY_PARITY` and its import-time completeness guard

The orchestration file now imports those fixture builders and retains the compile/run, source extraction, parity execution, assertions and failure-injection orchestration.

- Runner: **1,080 → 880 lines** (200 lines removed from orchestration).
- Extracted original scenario/parity block: **205 lines**.
- New fixture module: **227 lines**, including module contract and explicit exports.
- Remote read-back reconstructed the moved block from the pre-change `dff053bb8fe276d3f0ba9764e845d61ebe640539` runner and confirmed byte-for-byte equality with the new module's extracted content.
- The Relay workflow's `pull_request` path filter includes the new fixture module. This handover commit also adds both the runner and new fixture path to the Relay workflow's `push` filter, so direct branch pushes to either file trigger the same focused suite.
- The Quarantine workflow already watches the entire ESP8266 board directory, so no Quarantine workflow edit was needed.

## Exact source/test CI evidence

All three runs below are associated with source/test SHA `6ce423783b306411bdb7e7217081c050cb4cbec4`.

### Quarantine Byte Readback

[Run #45354176204](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45354176204), job `138307756777`: **SUCCESS**.

The exact log includes:

- Pending-clear lab: 17/17 source-extracted cases per board; physical tests explicitly NOT RUN.
- First-fault snapshot stability on ESP32 and ESP8266.
- Poll safety board parity: 19/19 normalized helpers.
- Eight ESP32 coin-authority fail-open mutations rejected.
- Pending-clear remove-failure injections: 4/4 plus success control; precondition failures: 7/7.
- Disabled-ingress attempted-evidence preservation: 6/6.
- Active-high and active-low pre-poll capture-once cases pass on both boards.
- `SIMULATED_ONLY=1`; `PHYSICAL_POWER_CUT_VERIFIED=0`.

### Relay Output Polarity

[Run #45354176057](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45354176057):

- Source/output job `138307756400`: **SUCCESS**.
- ESP32 boot-polarity job `138307755807`: **SUCCESS**.
- The source/output log confirms `poll_loop_blocking_inhibit_lab.py` imported the new module and executed the extracted poll-loop cases.
- It also records JSON primitive/composite grammar negative controls, bounded HTTP response tests and poll-window mutation rejection.

### Full BlazePwifi

[Run #45354176294](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45354176294):

- Validation job `138307757722`: **FAIL** at the inherited `Missing poll signature check` in the ESP8266 sketch.
- All 14 firmware/platform jobs, including ESP8266, ESP32, Ruijie, x86_64, Orange Pi targets and Android, completed **SUCCESS**.
- Validation-dependent simulation, update bundle, candidate, production-sign handoff and publication jobs were **SKIPPED**.

This is the existing CORE producer / QA consumer-contract blocker. Hardware did not invent `response_sig`, weaken default-deny, or change the shared register/poll API.

## Scope and safety boundary

No production `.ino`, GPIO order, coin admission, relay behavior, controller API, financial schema, signer, witness, migration, replay policy or release workflow behavior changed. The Relay workflow change only closes the path-trigger gap for this runner and its new fixture module.

All positive evidence is host/source-extracted simulation and CI. Physical coin acceptor, electrical relay/recovery, LittleFS power-loss, 150 controlled power cuts and 30-device/24-hour soak remain **NOT TESTED**. **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

## Revalidated ownership and blockers

- #239 remains OPEN/DRAFT at `d83b715b116185107737fef721c2eece8feebf39`.
- #254 remains OPEN/DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`.
- #283 remains OPEN/DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`; its quarantine append guard and definition-only quarantine callsite remain separate audit facts, not a completed lifecycle.
- #348 remains a separate child of #254 at `eb7afcb2ba0d1e84054c052c8b129cb51a91d062`; no ESP32 provider/API work was taken over.
- Master PR #288 remains OPEN/DRAFT/UNMERGED at `3282a7c3060b404000972084825767d40145e3d5`; Master owns global pins and assignments.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete; this is a partial Hardware cleanup contribution, not track completion.
- P0 #34 physical acceptance, #31/#32 financial atomicity/replay and #43 independent witness remain open.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains OPEN/DRAFT/FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No destination migration or promotion occurred.
- Canonical repository owner is `BlazeDevStudio`; old `BlazingSystems` owner resolves to the renamed repository. Historical profile links in root README were left untouched because they are outside Hardware ownership.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the exposed tools. No Google Drive connector is exposed in this run; older v3/v4 Library registry snapshots were not substituted.

## Next exact action

PHX-MASTER refreshes the #349 source/docs pins and keeps it stacked/unmerged on #347. PHX-QA independently reviews the moved fixture contract and focused logs. PHX-CORE publishes the approved authenticated register/poll response envelope and canonical golden vectors; PHX-QA reconciles the inherited assertion against that contract. PHX-HARDWARE then reruns Full at the approved exact SHA while preserving coin/relay default-deny.
