# PHX-HARDWARE — dual-store poll-fault fixture modularization

**Date:** 2026-11-21  
**Task:** cleanup-first #266  
**PR:** #330 (DRAFT, stacked child of #327)  
**Branch:** phoenix/hardware-dual-store-fixture-modules-20261121  
**Base / parent:** #327 at 827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8  
**Source/test commit:** 5133def2a358b6c3c0f0d18f31b9a483018a3a60

## Why

The single 512-line poll_fault_dual_store_lab_fixtures.py mixed shared C++ scenarios, ESP32 NVS modeling, ESP8266 EEPROM/flash modeling, and source-extraction composition. That made it harder to review a board-specific persistence failure without navigating unrelated fixture responsibilities.

## Change

The fixture is now divided by responsibility:

- poll_fault_dual_store_lab_fixtures_common.py — 251 lines; shared constants extraction, common C++ prelude/scenario driver, and ESP8266 raw-flash read-failure scenario text
- poll_fault_dual_store_lab_fixtures_esp32.py — 134 lines; NVS durable/pending model and ESP32-specific failure controls
- poll_fault_dual_store_lab_fixtures_esp8266.py — 106 lines; EEPROM/flash model and ESP8266-specific failure controls
- poll_fault_dual_store_lab_fixtures.py — 58 lines; source extraction and board-backend composition

The C++ prelude, common scenario driver, raw-flash scenario, ESP32 backend/control block, and ESP8266 backend/control block were read back from the parent and compared byte-for-byte with the extracted new module payloads. All five comparisons passed. The board-specific helper order was preserved.

No ESP sketch, persistence layout, C++ scenario semantics, workflow, API, financial code, signer, witness, or production path changed. This is a Python lab organization change only.

## Exact-head evidence

- Source/test HEAD: 5133def2a358b6c3c0f0d18f31b9a483018a3a60
- Focused workflow: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44893481023
- Job: 136814086645 — quarantine-source — SUCCESS
- Exact log markers:
  - POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32
  - POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266
  - ESP32_NVS_SET_BLOB_NOT_DURABLE_BEFORE_COMMIT_PASS
  - MUTATION_REJECTED ESP32_NVS_SET_BLOB_PREMATURE_DURABILITY exit=60
  - MUTATION_REJECTED ESP32_NVS_COMMIT_OMITTED exit=61
  - ESP8266_RAW_FLASH_READ_ERROR_WRITE_DENY_PASS
  - DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY on both board models

These are host-side source-extracted simulations and GitHub CI only. They do not establish flash physics, power-cut durability, electrical recovery, or hardware acceptance.

## Integration result and remaining blockers

- Full BlazePwifi run https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44893480924: validation job 136814086457 FAILED at the existing QA-owned tests/controllers.sh assertion Missing poll signature check. The failure is the known CORE/QA authenticated poll-contract gate, not a failure in the fixture split. Remaining target build jobs were still running at this checkpoint; no full-workflow success is claimed.
- PHYSICAL coin/relay acceptance: NOT TESTED.
- 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Protected anti-rollback signer and independent witness: NOT ESTABLISHED.
- v1-to-v2 durable financial migration/replay: NOT ESTABLISHED.
- Independent QA/release signoff: PENDING.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json: unavailable through the current connected tool surface; no older registry snapshot was substituted.

## Disposition

SIMULATED + FOCUSED CI VERIFIED only. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO. PR #330 remains OPEN / DRAFT / UNMERGED and must not be merged independently of parent #327.

## Next exact action

PHX-QA/PHX-CORE must resolve the canonical authenticated poll/receipt contract and replace the stale positive signature assertion with source-linked negative/default-deny tests. PHX-MASTER must preserve the #322 → #323 → #326 → #327 → #330 stack. PHX-HARDWARE must revalidate the live heads on the next activation before selecting another owned task.