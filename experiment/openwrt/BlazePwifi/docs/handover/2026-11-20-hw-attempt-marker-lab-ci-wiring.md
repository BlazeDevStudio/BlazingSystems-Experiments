# PHX-HARDWARE handover — attempt-marker fault lab wired into exact-head CI

**Date:** 2026-11-20 UTC02  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent/base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Pre-change head:** `a2b7903b4009fd7182247e11a7d2954a79cb9bbd`

## Finding

The hardware-owned `pending_attempt_marker_lab.py` already compiles the actual ESP32 and ESP8266 pending-journal, one-shot attempt-marker, clear and POST-gate functions against fault-injected fake LittleFS. It covers marker-open/write/readback failures, one-shot replay denial, conflicting journal candidates, pending-file removal failure, attempt-marker removal failure, and reboot after a partial clear. The source lab reports 28 cases per board (56 total).

The current #327 quarantine workflow invoked `pending_journal_recovery_lab.py` but did not invoke this complementary one-shot/attempt-marker lab. A repository search for the lab filename returned no default-branch workflow match. Consequently, those existing source-extracted failure cases were not part of the recurring #327 focused CI gate.

## Change

Added the explicit workflow command:

`python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py`

It runs immediately after the pending-journal recovery lab in `.github/workflows/phx-hardware-quarantine-byte-readback.yml`. The lab itself covers both board sketches; no second copy or new test framework was added.

## Validation status at commit creation

The workflow is configured to run on the exact #327 branch push and PR synchronization. Its result is **PENDING** until GitHub Actions returns a run tied to the resulting commit SHA. No PASS is claimed here before that result is read back.

## Scope and evidence limits

- Changed: one hardware-owned workflow invocation and this narrow handover.
- Unchanged: both runtime sketches, pending journal schema, event/receipt contract, CORE APIs, financial state, release workflow and Master/QA-owned paths.
- The lab uses host C++ and fake LittleFS. It is **SIMULATED** source-extracted failure injection, not real flash durability, power-cut or electrical evidence.
- Physical coin pulse/relay acceptance, 150 power cuts, 30-device 24-hour soak, protected signer/witness, durable accounting/replay, financial v1-to-v2 migration and independent release signoff remain open. **PRODUCTION NO-GO.**

## Next exact action

Read the quarantine workflow result for the new commit and verify that the new lab executes for both ESP32 and ESP8266. If it fails, fix only the hardware-owned harness/source path and retain the failed run as evidence; do not weaken any fail-closed gate.
