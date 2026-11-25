# PHX-HARDWARE handover — quarantine evidence deletion-deny workflow coverage

**Updated:** 2026-11-21T18:40:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Workflow/source-test commit:** `8af8506349780c4a9cff44cb15ff019626e48538`

## Bounded task

The current #283 ESP32 and ESP8266 sketches already implement Master Architecture Contracts §6.5: unauthenticated `POST /quarantine/clear` returns HTTP 403 and does not remove `/quarantine.log`.

The Hardware-owned `quarantine_clear_deny_lab.py` already extracts the actual handler body from both sketches and compiles it against a fake web/filesystem boundary. However, the focused Hardware quarantine workflow did not invoke this lab. This left the explicit non-deletable-evidence contract outside the exact-head focused workflow.

## Change

Updated only `.github/workflows/phx-hw-quarantine-append-readback.yml`:

- Added `quarantine_clear_deny_lab.py` to the pull-request path filter.
- Added an explicit step to compile and run the source-extracted quarantine-clear denial regression after append/readback and pending-clear commit tests.
- Retained exact-PR-head checkout verification, read-only token permissions and the existing five-minute job timeout.

No firmware sketch, HTTP handler, API, finance, signer, witness, QA-owned test, migration, or Release workflow was changed.

## Exact-head CI

- Workflow: [PHX-HARDWARE Quarantine Append Readback run #44936757318](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44936757318)
- Job: `136944963487` — SUCCESS.
- Exact checkout: `8af8506349780c4a9cff44cb15ff019626e48538`.

Observed output:

- Quarantine append/readback: **13/13 per board**, including prior-log open failure, append-open failure, short write, readback open/read failure, post-close truncation, prefix/suffix corruption, capacity exhaustion and unavailable filesystem.
- Pending-journal boot recovery: **14/14 per board**.
- Quarantine clear/commit: **10/10 per board**; ignored-clear-result mutation rejected on both boards.
- New quarantine-clear denial: **6 repeated POST attempts per board** denied; log-presence state unchanged for both present and absent cases; `QUARANTINE_CLEAR_DENY_LAB=PASS`.

The new lab's result is **SIMULATED / CI VERIFIED only**. It compiles the extracted route handler against fake web/filesystem objects; it does not touch physical LittleFS or prove flash durability.

## Remaining blockers

- The quarantine handler remains deny-only until an authenticated operator reconciliation contract, immutable export/readback, durable receipt linkage, replay/idempotency and independent QA vectors are approved under Master §6.5.
- `quarantinePending()` remains definition-only; no active callsite or positive coin disposition was added.
- Current main register/poll responses still lack the approved authenticated controller response contract. Do not invent `response_sig`, weaken default-deny, or enable coin admission.
- Physical LittleFS power-cut durability, electrical pulse/relay acceptance, 150 power cuts, 30-device/24-hour soak, signer/witness, financial migration and independent release acceptance remain NOT TESTED / NOT ESTABLISHED.

## Next exact actions

1. PHX-QA independently review the exact handler extraction and negative behavior at source/test SHA `8af8506349780c4a9cff44cb15ff019626e48538`.
2. PHX-MASTER retain §6.5's non-deletable evidence requirement and reconcile the parallel #283 branch with the canonical #327 stack before integration.
3. PHX-CORE publish the approved authenticated receipt/reconciliation contract before any quarantine lifecycle callsite or positive admission is considered.

**Disposition:** narrow Hardware workflow coverage added; focused CI PASS; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
