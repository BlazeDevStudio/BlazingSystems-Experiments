# PHX-HARDWARE — blocking-poll scenario fixture modularization

**Date:** 2026-11-21 UTC11  
**Task:** cleanup-first #266 / hardware pulse safety #177  
**PR:** [#333 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/333), child of #332  
**Branch:** `phoenix/hardware-poll-scenario-modules-20261121-utc11`  
**Base:** #332 at `9f1d9ebf9c7256da2e8eace4bc0be510f6566daa`  
**Source/test commit:** `5dfc00eeffa2575be329a46f941c61186205948f`  
**PR docs head before this evidence update:** `9230a0c7591fa89eccd9d14b168b275d0a771422`

## Why

The 485-line `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` combined the primary C++ scenario program, ISR/drain edge builders, timing mutations and output-release cases. That made it harder to review one failure boundary without navigating unrelated scenario definitions.

## Change

The stable fixture module now exports the same six names from three responsibility modules:

- `poll_loop_blocking_inhibit_lab_scenario_main.py` — primary C++ scenario program
- `poll_loop_blocking_inhibit_lab_scenario_edges.py` — pre-poll edge race, post-drain rollover and missed-sample builders
- `poll_loop_blocking_inhibit_lab_scenario_timing.py` — original 1501/1600/1680 timing scenario and relay-release edge scenarios
- `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` — 22-line stable import/export layer consumed by the existing runner

Before writing the files, the six extracted payload segments (`MAIN`, `RACE_MAIN`, `post_drain_rollover_main`, `missed_sample_main`, `TIMING_MAIN`, `RELEASE_EDGE_MAIN`) were compared byte-for-byte with their original source slices. All six comparisons passed. The runner's public import names are preserved.

No production `.ino`, GPIO, poll/receipt contract, finance, signer, witness, QA-owned assertion, Release workflow or production behavior changed. This is a Hardware-owned host-lab organization change only.

## Verification

- Source/test commit: `5dfc00eeffa2575be329a46f941c61186205948f`.
- Payload preservation: 6/6 exact string comparisons PASS.
- Exact-head Quarantine Byte Readback [run #44900894666](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44900894666), job `136836358747`, on PR head `9230a0c7591fa89eccd9d14b168b275d0a771422`: **SUCCESS**. Both ESP8266 and ESP32 blocking-poll suites ran; original 1501/1600/1680 timing case, edge/drain/rollover/release-window cases and negative mutations completed. `POLL_LOOP_BLOCKING_INHIBIT_WORKFLOW_WIRING=PASS` and `POLL_LOOP_BLOCKING_INHIBIT_RUN_ONCE=PASS`.
- Full BlazePwifi PR [run #44900894655](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44900894655), validation job `136836359201`: **FAILURE** at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 14 target/platform jobs completed SUCCESS (ESP32, ESP8266, x86_64, Ruijie, Orange Pi variants and Android); production import, update bundle, v0.4 simulations, sign handoff, candidate and publication jobs were SKIPPED.
- Push Full run #44900891736 had no jobs at last read; no result is claimed for it.
- Full BlazePwifi integration: known blocker is the inherited QA-owned `Missing poll signature check`; this refactor does not add a signature or weaken default-deny.
- Physical coin/relay/power behavior: NOT TESTED.

## Next exact action

Run the exact-source Quarantine Byte Readback workflow through this DRAFT PR. Inspect the logs for both ESP32 and ESP8266 blocking-poll scenarios, including timing, edge-abort and release-window mutation cases. Keep this PR DRAFT / UNMERGED and stacked on #332; do not merge, flash, migrate, sign, tag, deploy or cut over.
