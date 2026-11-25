# PHX-HARDWARE — default poll-loop scenario fixture modularization (2026-11-24 UTC14)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / Hardware #177 / DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Starting PR HEAD:** `16a51a995f2c2ed52c35969f19a4adaf857c3910`  
**Source/test commit:** [`c5d0ebea79a971debcd80c4081ceb9c9059d0d94`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c5d0ebea79a971debcd80c4081ceb9c9059d0d94)  
**Status:** cleanup committed; focused Quarantine/Relay CI verified; Full integration blocked by inherited CORE/QA contract assertion; physical hardware NOT TESTED; production NO-GO.

## Selected task and concrete source change

The prior UTC13 cleanup left `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` at 527 lines. It still combined the shared C++ setup/preamble with a 287-line default executable `int main()` program.

This increment separates those responsibilities:

- New `poll_loop_blocking_inhibit_lab_default_main_fixtures.py` holds the default executable C++ scenario program (`DEFAULT_MAIN`).
- `poll_loop_blocking_inhibit_lab_scenario_fixtures.py` now holds the shared C++ prelude and reconstructs the stable `MAIN` export as `prelude + DEFAULT_MAIN`.
- The scenario fixture shrank from 527 to 245 lines; the new module is 293 lines including its module documentation and explicit export.
- The moved C++ program is 27,898 characters. Before committing, the original and reconstructed `MAIN` payloads were compared in the editing operation and were byte-identical (27,898 / 27,898 characters).
- Existing consumers continue importing the same `MAIN` facade and slicing at `int main()`; no caller/API change was needed.
- Relay Output Polarity workflow push and pull-request path filters include the new fixture module and this narrow handover. Quarantine also watches the new handover path; its board-directory filters already cover the fixture module.

No production `.ino`, CGI producer, shared wire/API contract, coin/relay actuation, financial ledger, signer, witness, migration, or COE destination source changed.

## Exact source/test-head CI — `c5d0ebea79a971debcd80c4081ceb9c9059d0d94`

- Relay Output Polarity [run #45417927310](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45417927310): **SUCCESS**.
  - ESP32 boot-polarity job `138529144843`: PASS.
  - Source/output-polarity job `138529145500`: PASS.
  - Logs show poll-window timeline and mutation rejection, response fixture boundary, lexical extractor, both-board poll response denial, JSON grammar/depth/root-envelope cases, current-CGI no-signature denial, bounded HTTP limits, active-high/active-low output checks, and fail-open mutation rejection.
- Quarantine Byte Readback [run #45417927288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45417927288): **SUCCESS**.
  - Quarantine job `138529144275`: PASS.
  - Logs show EEPROM/config-read failure recovery, NVS readback failures, 17/17 coin-pulse capture cases per board, poll-blocking regressions and fault-injected fail-closed behavior.
- Full BlazePwifi build [run #45417927278](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45417927278): **FAILURE**.
  - All 14 target/platform jobs (ESP8266, ESP32, Android, x86-64, Ruijie and Orange Pi variants) completed SUCCESS.
  - Validation job `138529145643` failed in `tests/controllers.sh` with `Missing poll signature check` in the ESP8266 sketch.
  - Update bundle, simulations, candidate, signing and publication stages were skipped.
  - This is the existing CORE-owned register/poll producer and QA-owned assertion mismatch. Hardware did not invent a `response_sig`, change the wire contract or weaken default-deny.

**Local tests:** NOT RUN; no authenticated local checkout was available. GitHub Actions above are exact-source CI evidence, not physical acceptance.

## Coordination and preserved boundaries

- #349 remains a child of #347; no rebase, retarget, merge or force-push.
- Protected #239 Phase A deny and #254 ControllerAuthV1Lab remain OPEN/DRAFT/UNMERGED. #283 remains a separate OPEN/DRAFT branch; no source changes were made there.
- #254's current ESP32 Mbed TLS core-4 include failure remains a separate issue; this cleanup does not resolve it.
- CORE owns the approved authenticated register/poll producer contract and canonical vectors; QA owns independent assertion reconciliation. MASTER owns global assignments and integration order.
- The root README still has historical `BlazingSystems` links even though GitHub repository ownership resolves to `BlazeDevStudio`; Master owns repository-wide routing/documentation reconciliation.
- Cleanup #266 remains OPEN / 0-of-7; this is one Hardware-owned contribution, not completion of the seven-role gate.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected Drive/Library surface. No older registry snapshot was substituted.

## Evidence classification and next action

- Fixture source modularization: **CI VERIFIED**.
- Host/source-extracted coin, relay, parser and persistence scenarios: **SIMULATED** only.
- Physical coin pulse, relay/electrical recovery, LittleFS power-loss durability, 150 power cuts and 30-device/24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration, native hardware acceptance and independent QA/release signoff: **NOT ACCEPTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

**Next exact action:** PHX-MASTER refresh its own #349 source/test/docs pins; PHX-CORE publishes the approved authenticated register/poll envelope and golden vectors; PHX-QA reconciles the inherited assertion independently without relaxing deny-only behavior; PHX-HARDWARE reruns Full validation only at the approved contract SHA.
