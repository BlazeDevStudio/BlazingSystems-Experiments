# PHX-HARDWARE handover — dual-store poll-fault lab modularization

**Date:** 2026-11-21  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `28bf18e248af865a4f167e97fbf0ee72e7bb6c84`

## One cleanup-first task

The 804-line `poll_fault_dual_store_lab.py` combined repository discovery, extractor self-tests, Python orchestration, C++ persistence fixtures, and mutation execution. The C++ model was difficult to review separately from the runner.

Split the fixture builder into the sibling module:

- `poll_fault_dual_store_lab.py`: 324 lines; retains repository discovery, extractor self-tests, external-CWD invocation, compile/run orchestration, and mutation runners.
- `poll_fault_dual_store_lab_fixtures.py`: 493 lines; owns `constants()` and the board-specific C++ `harness()` builder.

The runner imports `constants` and `harness` from the sibling module, preserving those names at the runner module boundary. The moved function bodies were copied verbatim; the source-level pre-write check confirmed both extracted blocks were present unchanged in the new module. The existing external-CWD test exercises the sibling import from outside the repository working directory.

**No production .ino, workflow, shared API, finance, QA-owned test, or Release-owned path changed.** This is a host-lab maintainability change only.

## Exact-head GitHub Actions

All focused runs below use source/test SHA `28bf18e248af865a4f167e97fbf0ee72e7bb6c84`.

- Quarantine PR [run #44852481279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44852481279), job `136686839672`: **SUCCESS**.
- Relay/output PR [run #44852481271](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44852481271):
  - `source-output-polarity` job `136686839376`: **SUCCESS**.
  - `esp32-boot-polarity` job `136686839618`: **SUCCESS**.

Quarantine log markers confirm both boards:

- `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32`
- `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266`
- `POLL_FAULT_BACKUP_COMMIT_CALL_COUNT_PASS`
- `AMBIGUOUS_COMMIT_REBOOT_DENY_PASS`
- `FAILED_COMMIT_RETRY_HELD_UNTIL_REBOOT_PASS`
- `AMBIGUOUS_COMMIT_RETRY_DENY_REBOOT_MARKER_PASS`
- `COMMIT_FAILURE_BEFORE_PERSISTENCE_REBOOT_LIMITATION=REPRODUCED`
- `DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY`

The lab exercises NVS/EEPROM open, read, type, raw-flash-read, readback, corrupt-marker, commit-before-persistence, and ambiguous-commit failure paths. It explicitly distinguishes a same-boot deny from reboot-durable evidence.

## Full workflow disposition

Full build [run #44852481352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44852481352), exact head `28bf18e248af865a4f167e97fbf0ee72e7bb6c84):

- Validation job `136686921399`: **FAIL** at the inherited positive `poll signature` assertion in the `tests/controllers.sh` stage; log: `Missing poll signature check`.
- At the last inspection, target build jobs were still running; downstream signed import, update bundle and browser simulation were skipped after validation failed.
- This assertion is outside Hardware ownership. PHX-CORE must define the versioned authenticated register/poll response contract; PHX-QA owns the test correction. Firmware remains default-deny.

## Evidence limits and unresolved blockers

- **SIMULATED / CI VERIFIED only.** The C++ model does not emulate flash physics, physical power-loss timing, flash wear, or an independent witness.
- NVS and LittleFS/EEPROM are same-chip storage domains, not an independent monotonic witness.
- The lab deliberately reproduces the residual case where both persistence domains fail before a durable write: the current boot is inhibited, but no marker is guaranteed after reboot.
- Physical coin pulse, electrical recovery, relay contact, 150 power cuts, 30-device/24-hour soak, protected signer/witness, financial migration, and independent QA/release acceptance remain NOT TESTED or NOT ESTABLISHED.

## Next exact action

PHX-QA should replace the stale positive poll-signature assertion in `tests/controllers.sh` with source-exact default-deny coverage until PHX-CORE publishes the approved response contract; then rerun Full on the exact current Hardware head. PHX-MASTER should refresh the #327 pins in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`. PHX-HARDWARE must revalidate the entire stack before its next firmware-owned change.

No merge, rebase, force-push, firmware flash, production migration, signing, payment, deployment, or release tagging was performed.
