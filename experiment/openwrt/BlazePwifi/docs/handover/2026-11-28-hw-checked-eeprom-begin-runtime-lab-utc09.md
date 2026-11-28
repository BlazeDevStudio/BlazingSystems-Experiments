## PHX-HARDWARE UTC09 — CheckedEEPROMClass runtime allocation/flash-read matrix (#374) — IN PROGRESS

**Task:** PHX-HW-CHECKED-EEPROM-BEGIN-RUNTIME-LAB-20261128T09Z  
**PR #374:** OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-eeprom-begin-failclosed-20261128-utc07  
**Parent #373:** 3783654a3c9862598bbb714268c536fb8b34578b  
**Source/test SHA:** f8865fb40e2811c74c5364e6075379692597fadd  
**Documentation status:** source/test evidence recorded; terminal docs-head reruns pending.

### Scope and concrete changes

The prior EEPROM write-result fixture substituted a boolean `beginChecked()` result and did not execute the actual ESP8266 `CheckedEEPROMClass::beginChecked()` implementation. Added a separate contract/harness/runner module that extracts the real class definition and compiles it against a fake EEPROM base/flash interface. The existing focused EEPROM persistence runner now invokes the new lab.

- `checked_eeprom_begin_lab_contract.py`: class/function extraction and source safety contract.
- `checked_eeprom_begin_lab_harness.py`: native fake-flash harness, deterministic allocation-failure injection, read-failure injection, sector/alignment/reuse/resize checks.
- `checked_eeprom_begin_lab.py`: source and runtime mutation matrix.
- Existing `config_persistence_write_result_lab.py` invokes the new lab.
- Focused workflow path filters include the new lab and narrow handover.
- New narrow handover: `2026-11-28-hw-checked-eeprom-begin-runtime-lab-utc09.md`.

### Exact source/test evidence

- Focused Poll Intake Deny push [#46132067080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132067080), job `140939195350`: **PASS** on exact SHA `f8865fb40e2811c74c5364e6075379692597fadd`.
- Append-only ledger guard: historical base 1,132,798 bytes; existing appended tail 64,351 bytes; **PASS**.
- Runtime markers: invalid-size deny, allocation failure fail-closed, flash-read failure cleanup, aligned sector read/reuse, resize reinitialize, invalid retry preservation — all PASS.
- Source mutations: 5/5 rejected (aligned-sector cap, allocation null guard, flash-read result, sector-derived address, read-failure pointer reset).
- Runtime mutations: 5/5 rejected (oversized sector, allocation guard removed, ignored flash-read failure, wrong sector address, stale pointer after failed read).
- Final marker: `CHECKED_EEPROM_BEGIN_RUNTIME_AND_MUTATION_MATRIX_PASS`.
- Existing EEPROM load/migration runtime matrix also passed: current 1/1, invalid current 6/6, legacy 1/1, invalid legacy 5/5, commit retry 2/2, begin failure 1/1, flash-read failure 1/1.

### Other workflow evidence and blockers

- Mbed run [#46131685056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46131685056) passed 3/3 on adjacent source/test SHA `44334e37ad516815b3fa5f2c478a057d31327e3b`; the ESP firmware source did not change in `f8865fb40e2811c74c5364e6075379692597fadd`. Exact docs-head Mbed rerun is pending.
- Full run [#46132067088](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132067088) on `f8865fb40e2811c74c5364e6075379692597fadd`: CI-0701 passed, but mandatory handover freshness failed because root `PROJECT_HANDOVER.md`, `CURRENT_STATE.md` and `CHANGE_LEDGER.md` had not yet been updated for this task. Platform builds were still running at this checkpoint; this is **not** a Full pass.
- Native Synthetic run [#46131685065](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46131685065) failed at QA-owned `tests/v060_vendo_sequence_contract.py:18`, which requires literal `if(any) return false;`. Hardware did not add decoy text or modify QA-owned tests.

### Safety and disposition

The new EEPROM beginChecked lab is **CI VERIFIED**. It is host simulation only. No production `.ino`, controller/API, financial schema, receipts, migration, signer, witness, COE destination, QA-owned test, physical device or production state was changed. Physical EEPROM/NVS brown-out, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Coin/relay admission remains denied. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

**Next exact action:** complete the append-only root handover/ledger sync in this commit, then re-run Focused, Mbed and Full on the resulting exact docs HEAD; QA must replace the literal pending-state assertion with source-linked semantic vectors; Master must refresh #374's role and integration pins from its stale `bdd69c75` entry.

---

