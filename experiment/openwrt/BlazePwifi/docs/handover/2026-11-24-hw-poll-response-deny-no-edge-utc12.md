# PHX-HARDWARE — no-edge poll response-denial regression

**Date:** 2026-11-24 UTC12  
**Task:** [#177 — synchronous poll coin-pulse loss](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** `PHX-HARDWARE`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Base:** PR #349 stacked on #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test SHA:** `dce158b3eb6c0d953900284207f349518205f1d2`  
**PR:** [#349 — JSON grammar and first-fault snapshot regressions](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349) — OPEN / DRAFT / UNMERGED

## Why this increment

The existing blocking-poll test injects an ISR edge during the 3.5-second HTTP call. That scenario correctly proves durable first-fault handling, but the fault latch itself also keeps outputs denied. The separate poll-response lab exercises `acceptPollResponse()` without running the full production loop.

This follow-up closes that evidence gap: run the exact extracted production loop with **no ISR edge and no journal fault** during HTTP. The relay must remain OFF solely because an unauthenticated positive-looking response or an empty timeout response is denied.

## Changes

- Added `poll_loop_blocking_inhibit_lab_response_fixtures.py` with a compact no-edge 3.5-second poll scenario.
- Extended `poll_loop_blocking_inhibit_lab.py` to run the scenario against both ESP8266 and ESP32, with:
  - Hostile positive-looking JSON response and empty timeout response.
  - Active-high and active-low relay reset configurations.
  - A fail-open mutation that sets `insertMode=true`, assigns a spoof target and returns success regardless of response bytes.
- The baseline asserts no ISR edge, no `/pollpulse.fault` marker, no journal-recovery latch, no coin POST/clear, and relay/LED OFF after response denial.
- Each board passes all four baseline combinations and rejects all four fail-open mutations (expected exit 90).
- No production `.ino`, CGI producer, controller API, financial state, signer, witness, migration or release workflow was changed.

## Exact-source CI — source/test SHA `dce158b3eb6c0d953900284207f349518205f1d2`

- Quarantine [run #45398283765](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283765), job `138459811729`: **PASS**.
  - ESP8266: 4/4 no-edge baseline combinations PASS; 4/4 fail-open mutations rejected.
  - ESP32: 4/4 no-edge baseline combinations PASS; 4/4 fail-open mutations rejected.
- Relay Output Polarity [run #45398283830](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283830):
  - Source/output job `138459812511`: **PASS**, same 8 baseline + 8 mutation results.
  - ESP32 boot-polarity job `138459812956`: **PASS**.
- Full [run #45398283752](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283752):
  - Validation job `138459962150`: **FAIL** at inherited QA-owned `Missing poll signature check`.
  - Firmware/Android matrix: **14/14 PASS** (ESP8266, ESP32, 11 OpenWrt/board platform jobs and Android).
  - 12 validation-dependent simulation, update, signing and publication jobs: **SKIPPED**.

Local tests were **NOT RUN**; evidence above is from exact-SHA GitHub Actions.

## Evidence classification and limits

- No-edge response-denial regression: **SIMULATED / CI VERIFIED**.
- Active-high/active-low software output behavior: **SIMULATED / CI VERIFIED**.
- Physical coin acceptor, relay contacts, pulse waveform/conditioning and electrical recovery: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device 24-hour soak: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

This test proves the host-extracted loop's default-deny behavior under the stated fixtures; it does not prove physical relay contact state or durable coin credit.

## Coordination and blockers

- PHX-CORE owns the authenticated register/poll response contract and canonical golden vectors.
- PHX-QA owns independent reconciliation of the inherited `Missing poll signature check` assertion.
- PHX-MASTER owns `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and the global release decision. The current Master snapshot still has older #349 pins.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed file/Drive tools; no older snapshot was substituted.

## Next exact action

PHX-MASTER: refresh #349 source/test and handover pins. PHX-CORE/PHX-QA: publish and independently reconcile the authenticated register/poll contract. PHX-HARDWARE: rerun Full only after the approved contract SHA is available, retaining default-deny behavior. Physical acceptance remains gated on explicit owner approval and isolated noncustomer equipment.
