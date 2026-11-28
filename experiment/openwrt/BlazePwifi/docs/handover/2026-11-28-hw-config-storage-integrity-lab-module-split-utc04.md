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

## UTC04 evidence correction

- Focused PR run #46105780778 / job 140858075446: PASS; 5/5 mutations rejected; Config 6/6 and ConfigV1 5/5.
- Mbed PR run #46105780822: source-contract + ESP32 core 3.3.13 + 4.0.0 all PASS (3/3).
- Initial Full #46105780768 validation job 140858135917 failed only at the mandatory handover freshness gate because CHANGE_LEDGER.md was not yet appended after source/workflow commit 40860925d0150f5de49f310678d32e0c23f6f9a6. The append-only record is added in this commit; fresh Full rerun required.
- The initial Full failure occurred before controller parity and before downstream simulation/update/signing/publication; do not misclassify it as a QA API failure.
- No physical hardware tests performed. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## UTC04 terminal evidence

- Focused #46106079097 / job 140859006487: PASS; current Config 6/6, legacy ConfigV1 5/5, five mutation rejections, C++11 ASan/UBSan harness and append-only ledger guard.
- Mbed #46106079120: PASS 3/3 (source-contract + ESP32 3.3.13 + 4.0.0).
- Full #46106079194: terminal FAILURE at QA-owned controller parity `tests/controllers.sh:21`; the literal `config_revision` assertion is absent from both exact PR-head sketches. Mandatory handover freshness passed; all 14/14 target/platform builds including Android passed; downstream simulation/update/signing/publication skipped.
- QA owns the assertion replacement; CORE owns authenticated register/poll/receipt/disposition. Do not add a decoy config_revision field.
- Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.