## PHX-HARDWARE UTC11 follow-up — ordered precondition markers for EEPROM mutations (#374)

**Task:** PHX-HW-EEPROM-RUNTIME-MUTATION-MARKERS-20261128T11Z  
**Role:** PHX-HARDWARE · **PR:** [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374) OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-eeprom-begin-failclosed-20261128-utc07` · **Source/test HEAD:** `b8e2077eebfbb4eed500ce954b535298d67e1f10` · **Prior docs HEAD:** `659249d05d7f118b411863d288104ba7d3281db0`

### Why this follow-up was required

Exact exit codes alone did not prove the fixture had reached the intended preceding scenario. The earlier stdout-marker assertion was attached to the wrong point: the oversized-size marker was emitted only *after* the oversized mutation target. The corrected fixture now emits a separate zero-size precondition marker before that target and flushes every marker immediately.

The runner again requires both the exact expected exit and the expected preceding marker for all five runtime mutations. The marker ordering is:
- oversized sector: `CHECKED_EEPROM_ZERO_SIZE_DENY_PASS`
- allocation failure: `CHECKED_EEPROM_INVALID_SIZE_DENY_PASS`
- ignored flash-read result: `CHECKED_EEPROM_ALLOCATION_FAILURE_FAIL_CLOSED_PASS`
- wrong sector address: `CHECKED_EEPROM_FLASH_READ_FAILURE_CLEANUP_PASS`
- stale buffer after read failure: allocation-failure marker above

### Exact-source result

- Corrected Poll Intake Deny [#46140271750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46140271750), job `140964436965`: **PASS**. Logs confirm all five precondition markers, all five source mutations rejected, and all five runtime mutations rejected at the expected exit with the expected preceding marker. Final marker: `CHECKED_EEPROM_BEGIN_RUNTIME_AND_MUTATION_MATRIX_PASS`.
- Full [#46140271763](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46140271763), validation job `140964488070`: **FAIL at handover freshness** because this source/test commit postdated the prior root handover `659249d`. This commit synchronizes the root handover and ledger; Full must be rerun on this synchronized head. Target builds were still running when the validation gate stopped.
- Mbed run [#46140109953](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46140109953) is on prior docs head `659249d`, not this source/test head; source-contract and core 3.3.13 passed, core 4.0.0 was still running at the last read. No Mbed result is claimed for `b8e2077eebfbb4eed500ce954b535298d67e1f10`.

### Scope and safety

Only the Hardware-owned native runner/harness files changed in the source/test correction. No production `.ino`, CORE API, QA assertion, controller contract, finance, receipt/disposition, signer, witness, migration, COE destination, or device changed. Coin/relay admission remains denied. Host simulation / CI only; physical EEPROM/NVS, power cuts, GPIO/relay and electrical acceptance remain NOT TESTED.

**Disposition:** EEPROM runtime mutation contract = CI VERIFIED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.  
**Next:** run Full on the synchronized docs head; QA owns the stale literal pending-state assertion; Master owns refreshing the exact #374 head in role/integration matrices.
---

## PHX-HARDWARE UTC11 — checked EEPROM runtime mutation runner correction (#374)

**Task:** PHX-HW-EEPROM-RUNTIME-MUTATION-RUNNER-FIX-20261128T11Z  
**Role:** PHX-HARDWARE  
**PR:** [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-eeprom-begin-failclosed-20261128-utc07`  
**Parent #373:** `3783654a3c9862598bbb714268c536fb8b34578b`  
**Prior docs HEAD:** `76dfffbffad9ba68ce5f1d3ea397b9701e698a7d`  
**Source/test HEAD:** `20cb46b02e2885438c42f53d8990b3da87ff7fd0`

### Proven test-runner defect and correction

The helper `expect_runtime_rejected(label, source, expected_return_code)` accepts three arguments. Four mutation call sites still passed a fourth, obsolete stdout-marker argument after the earlier helper change. Exact Poll workflow #46138676580 / job 140959565121 reproduced the defect as a `TypeError` at `checked_eeprom_begin_lab.py:102`. The previous test therefore did not complete its intended mutation matrix.

The current source removes the four obsolete arguments. The five runtime mutations now require their exact invariant exits: oversized sector=3, allocation failure=13, ignored flash-read failure=5, wrong sector=8, and stale buffer after failed read=6. Compiler failures remain fatal; arbitrary nonzero exits are not accepted as mutation evidence.

### Exact-head evidence

- Corrected exact-source Poll Intake Deny [#46139742888](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46139742888), job `140962803936`: **PASS**. All five runtime mutation cases emitted their expected exit codes (3, 13, 5, 8, 6); all five source mutations were rejected; the valid bounds/allocation/read-failure/resize/reuse scenarios passed. Existing EEPROM config failure injection remained 17/17 and pending-recovery promotion passed 15 scenarios per board.
- Full [#46139739101](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46139739101), validation job `140962844258`: **FAIL at handover freshness**, because this source/test commit was newer than `PROJECT_HANDOVER.md`; the gate identified `checked_eeprom_begin_lab.py` and prior checkpoint `76dfffb`. This record synchronizes the handover; Full must be rerun on the new docs head. The same run's 14/14 target/platform + Android builds passed (ESP8266, ESP32, Android, x86_64, Ruijie and supported Orange Pi targets).
- Mbed TLS matrix [#46138676583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46138676583): 3/3 PASS on prior docs head `76dfffb`; no separate Mbed matrix was triggered on `20cb46b02e2885438c42f53d8990b3da87ff7fd0`. The corrected commit changes only the native test runner, not either production sketch.
- Native Synthetic [#46138676568](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46138676568), job `140959565383`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py:18`, which requires literal `if(any) return false;`. Hardware did not edit the QA assertion or add decoy source text.

### Scope and safety

Only `checked_eeprom_begin_lab.py` changed in the source/test correction. No production `.ino`, CORE API, controller schema, finance, accounting, pending disposition, signer, witness, migration, COE destination, QA-owned assertion, or physical device changed. Coin/relay admission remains denied. This is host simulation / CI evidence only. EEPROM/NVS brown-out and all physical acceptance remain NOT TESTED.

**Disposition:** scoped runtime mutation harness = CI VERIFIED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.  
**Next:** rerun Full on the synchronized docs head; QA owns replacing the stale literal pending-state assertion with source-linked semantic vectors; Master owns refreshing #374's exact head in role/integration matrices.
---

## PHX-HARDWARE UTC10 correction — runtime mutation failure attribution (#374)

**Task:** PHX-HW-EEPROM-RUNTIME-MUTATION-ATTRIBUTION-20261128T10Z  
**Correction source/test SHA:** `3515000ccf117a547bfe9d44e1b3e2cb110ed976`  
**Parent source/test SHA:** `2f1496ac98011f00ee2168118b0c8698b2ca82b5`  
**Initial docs HEAD:** `e424de2ba9424da091e699a3fa5182ba122ad523`

### First exact-head result and correction

Focused run [#46138392550](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46138392550), job `140958701627`, **FAILED** at the first oversized-sector mutation. The C++ fixture returned the expected exit code `3`, but captured stdout was empty, so the additional preceding-marker assertion itself was invalid under the captured-process execution path. The intended mutation was rejected at the expected harness exit; the new marker requirement caused a false-negative test failure.

Correction: remove stdout-marker requirements and retain exact expected process exit codes for all five mutations. Compiler errors still fail during the compile step and cannot be counted as successful mutation rejection. The test-only `std::_Exit(6)` remains only for the deliberate dangling-pointer mutation to avoid destructor double-free.

The five expected invariant exits remain `3, 13, 5, 8, 6`. Exact corrected-source CI is pending.

No production sketch or controller/financial interface changed. Coin/relay admission remains denied; physical EEPROM/NVS acceptance remains NOT TESTED.

**Next:** push the correction with append-only handover/ledger synchronization, then read exact-head Focused/Mbed/Full/Native outcomes.

---

## PHX-HARDWARE UTC10 — Exact EEPROM runtime-mutation failure attribution (#374) — IN PROGRESS

**Task:** PHX-HW-EEPROM-RUNTIME-MUTATION-ATTRIBUTION-20261128T10Z  
**Role:** PHX-HARDWARE  
**PR:** [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-eeprom-begin-failclosed-20261128-utc07`  
**Parent #373:** `3783654a3c9862598bbb714268c536fb8b34578b`  
**Prior branch HEAD:** `09374c8b232f925424d15bce830b1c375e11e024`  
**Source/test commit:** `2f1496ac98011f00ee2168118b0c8698b2ca82b5`  
**Documentation commit:** this additive handover update; final branch HEAD is read back after push.

### Selected bounded task

The existing CheckedEEPROMClass runtime mutation runner treated any nonzero fixture exit as a successful rejection. That could misclassify an unrelated assertion, abort, or crash as evidence that the intended invariant caught the mutation.

### Actual changes

- Added `compile_and_run_result()` to the shared Hardware-owned native fixture helper. Compilation still fails the test on compiler errors; runtime status/stdout/stderr are returned for explicit inspection.
- Kept `compile_and_run()` behavior fail-fast for existing callers by raising `CalledProcessError` on nonzero runtime exit.
- Changed the five CheckedEEPROMClass runtime mutations to require their exact expected invariant exit code and the expected preceding baseline marker.
- The failed-read-buffer mutation uses a test-process-only `std::_Exit(6)` after flushing output, preventing the fake base destructor from double-freeing a deliberately dangling mutation fixture. This does not alter production firmware.

### Baseline at prior exact HEAD

At prior docs/branch HEAD `09374c8b232f925424d15bce830b1c375e11e024`:
- Focused Poll Intake Deny [#46132251089](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132251089): PASS.
- Mbed TLS 3/4 [#46132251056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132251056): 3/3 PASS.
- Full [#46132251064](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132251064): FAIL in QA-owned `tests/controllers.sh:21`, literal `config_revision` presence assertion.
- Native Synthetic [#46132251066](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46132251066): FAIL in QA-owned `tests/v060_vendo_sequence_contract.py:18`, literal `if(any) return false;` assertion.

These are baseline results, not results for the new source/test commit. New exact-head CI is pending.

### Safety and ownership

Only Hardware-owned test/harness files changed. No production `.ino`, CORE API, controller schema, finance, accounting, pending receipt/disposition, QA-owned assertions, signer, witness, migration, COE destination, or hardware device changed. Coin/relay admission remains denied. This is host simulation/test-contract evidence only; EEPROM/NVS brown-out and physical power-cut behavior remain NOT TESTED.

**Next exact action:** run Focused, Mbed and Full on the pushed docs HEAD; verify all five mutations fail at their intended exit/marker, then report QA/Master-owned blockers without editing their files.

---

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

