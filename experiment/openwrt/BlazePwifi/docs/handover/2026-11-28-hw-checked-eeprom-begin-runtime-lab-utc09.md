## PHX-HARDWARE UTC09 — CheckedEEPROMClass runtime failure-injection lab (IN PROGRESS)

**Task:** PHX-HW-CHECKED-EEPROM-BEGIN-RUNTIME-LAB-20261128T09Z  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-eeprom-begin-failclosed-20261128-utc07  
**Base head before this task:** 10c8284467a130e8328d1875b059ddcc4bbf53c5  
**Source/test SHA:** pending commit readback  
**State:** IN PROGRESS; no device operations.

### Selected task

Exercise the actual extracted ESP8266 `CheckedEEPROMClass::beginChecked()` implementation. The prior write-result harness only substituted a fake `beginChecked()` boolean; it did not execute the custom allocator/flash-read implementation.

### Intended coverage

- Zero and over-sector requests deny without flash reads.
- Four-byte alignment and inherited EEPROM sector address are checked.
- Flash-read failure must release/null the buffer, reset size/dirty state and return false.
- Same-size reuse and changed-size reinitialization are exercised.
- Source mutations cover bounds, allocation guard, flash-read result, sector address and failure cleanup.
- Runtime mutations cover oversized sector, ignored flash-read failure, wrong sector address and stale pointer after failed read.

### Safety boundary

No production sketch, controller/API, finance, receipt/disposition, signer, witness, migration, QA-owned assertion, COE destination or physical device is changed by this task. This is host simulation only. Physical EEPROM/NVS brown-out and power-cut acceptance remain NOT TESTED. Coin/relay admission remains denied.

### Verification

Exact source/test commit and terminal Focused/Mbed/Full workflow IDs will be appended after GitHub Actions completes. No test result is claimed in this IN PROGRESS record.
