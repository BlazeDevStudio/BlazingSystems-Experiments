# PHX-HARDWARE handover — attempt-marker fault lab wired into exact-head CI

**Date:** 2026-11-20 UTC02  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent/base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Exact source/workflow/test head:** `326e864794ce826f474d2fab9da6e9af9003e1dd`

## Finding

The hardware-owned `pending_attempt_marker_lab.py` already compiles the actual ESP32 and ESP8266 pending-journal, one-shot attempt-marker, clear and POST-gate functions against fault-injected fake LittleFS. It covers marker-open/write/readback failures, one-shot replay denial, conflicting journal candidates, pending-file removal failure, attempt-marker removal failure, and reboot after a partial clear. The source lab reports 28 cases per board (56 total).

The #327 quarantine workflow invoked `pending_journal_recovery_lab.py` but did not invoke this complementary one-shot/attempt-marker lab. The existing tests were therefore present in the branch but absent from the focused CI gate.

## Change

Added the explicit workflow command:

`python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py`

It runs immediately after the pending-journal recovery lab in `.github/workflows/phx-hardware-quarantine-byte-readback.yml`. The lab itself covers both board sketches; no duplicate test framework or second board-specific copy was added.

## Exact-head validation

- Quarantine/readback PR run [#44663186737](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44663186737), job `136046085508`: **COMPLETED SUCCESS** at exact commit `326e864794ce826f474d2fab9da6e9af9003e1dd`. The job verified literal checkout SHA. The quarantine-source step passed, and its log contains `PENDING_ATTEMPT_MARKER_PASS 28/28` for ESP32 and ESP8266 plus `PHX-HARDWARE: 28/28 source-extracted cases per board (56/56 total) PASS; actual flash NOT TESTED`.
- The same quarantine job also completed the pending-journal recovery, source-quarantine, dual-store, poll-window, config-read, pulse-capture and boot-polarity labs successfully.
- Relay/output polarity PR run [#44663186747](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44663186747): **COMPLETED SUCCESS**.
- Full BlazePwifi PR run [#44663186728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44663186728): **TERMINAL CANCELLED** after validation job `136046085997` **FAILED** at QA-owned `Controller protocol parity`; exact log: `Missing poll signature check` in the ESP8266 controller sketch. All 13 firmware/platform target jobs, including ESP32 and ESP8266, completed successfully; Android was cancelled. Downstream simulations, update bundle, production sign handoff, candidate gate and publishers were cancelled or skipped. This is not Full validation acceptance.

## Scope and evidence limits

- Changed: one hardware-owned workflow invocation and this narrow handover.
- Unchanged: both runtime sketches, pending journal schema, event/receipt contract, CORE APIs, financial state, Release-owned workflow and Master/QA-owned paths.
- The lab uses host C++ and fake LittleFS. It is **SIMULATED / CI VERIFIED** source-extracted failure injection, not real flash durability, power-cut or electrical evidence.
- Physical coin pulse/relay acceptance, 150 power cuts, 30-device 24-hour soak, protected signer/witness, durable accounting/replay, financial v1-to-v2 migration and independent release signoff remain open. **PRODUCTION NO-GO.**

## Next exact action

PHX-QA must replace the stale positive poll-signature assertion with source-exact default-deny tests and rerun Full validation at the selected exact head. PHX-MASTER must reconcile #327/current head in its canonical active-PR ledger. PHX-HARDWARE continues only in owned ESP32/ESP8266 paths and hardware-owned handovers; do not change shared APIs or COE destination source without an explicit route/assignment.
