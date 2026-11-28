# PHX-HARDWARE UTC04 — Config-storage integrity lab module split

**Role:** PHX-HARDWARE
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`
**Parent PR:** #370 at `b0fed471b00b88bdc03e0721547667db5edc5ec0`
**Branch:** `phoenix/hw-config-storage-integrity-modules-20261128-utc04`
**Source/test commit:** `40860925d0150f5de49f310678d32e0c23f6f9a6`
**Scope:** host-test maintainability; no production firmware or shared API changes

## Change

Split the bounded EEPROM configuration-integrity lab into:

- `config_storage_integrity_lab_contract.py` — source contract, field/termination checks, legacy migration ordering, and mutation rejection.
- `config_storage_integrity_lab_harness.py` — extracted C++11 fixture and ASan/UBSan compile/run helper.
- `config_storage_integrity_lab.py` — thin CLI preserving the existing invocation and five failure-injection cases.

The Hardware workflow now includes both modules in push/PR path filters and the child branch in its push allowlist.

## Preservation

- Original `.ino` source remains unchanged.
- Existing mutation labels and checks are preserved: Arduino prototype order, current-config guard, legacy-config guard, NUL terminator, and bounded AP-password length.
- C++ sanitizer flags and current/legacy field matrices are retained.
- `CHANGE_LEDGER.md` is not modified; the historical ledger remains identical to parent #370.

## Verification

- Exact-head GitHub Actions: pending.
- No physical EEPROM/NVS, GPIO, relay, power-cut, soak, or electrical pulse testing performed.
- HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Next action

Run exact-head focused Hardware lab and Mbed/Full matrices; distinguish inherited QA controller-parity failure from any new source/workflow regression.
