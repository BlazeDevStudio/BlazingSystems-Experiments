

## PHX-HARDWARE UTC03 — config-persistence lab module split (#370)

**PR #370: OPEN / DRAFT / UNMERGED**, stacked on #366 at `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9`.  
**Branch:** `phoenix/hw-config-persistence-lab-modules-20261128-utc03`  
**Source/test commit:** `c8ca5e5a4a50de3a725eb742cdc99838974c38b3`  
**Scope:** Hardware-owned host-lab maintainability only; no production firmware or shared interface changed.

The 438-line `config_persistence_write_result_lab.py` mixed source-contract assertions, mutation helpers, C++ EEPROM/Preferences fixtures, compiler execution, and board orchestration. It is now split into:

- `config_persistence_write_result_lab_contract.py` — source invariants, failure-gate checks, board validators, and mutation rejection helper.
- `config_persistence_write_result_lab_harness.py` — native C++ EEPROM/Preferences fixtures and compile/run helper.
- `config_persistence_write_result_lab.py` — thin runner preserving the original command and all existing cases.

The Hardware workflow now watches both new modules and this isolated child branch. Existing function bodies and the original runner's test sequence were moved without changing the contract or mutation set.

### Exact source/test CI

- Focused [run #46104154160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46104154160), job `140853023938`: **PASS** at exact source/test SHA `c8ca5e5a4a50de3a725eb742cdc99838974c38b3`.
- The lab reports `CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32`; EEPROM commit-failure propagation PASS; ESP32 invalid-marker safe-default, legacy-config compatibility, Preferences.begin retry, and 14-field/two-marker-failure matrix PASS.
- All seven existing unsafe persistence mutations were rejected: ignored EEPROM commit result, ignored ESP8266 setup failure, ignored Preferences write result, ignored ESP32 setup failure, ignored invalid marker, invalid-config network connect, and invalid-config controller poll.
- The same focused job passed EEPROM bounded validation/failure injection 5/5, pending recovery 15 scenarios per board / 18 mutations rejected, and the append-only ledger guard. Guard result: `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=44730`; its failure-injection test was run.
- Initial Full [run #46104154060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46104154060): CI-0701 job `140853024132` PASS; validation job `140853070277` FAILED only because source/workflow changes were newer than `PROJECT_HANDOVER.md`. All 14/14 target/platform jobs (ESP8266, ESP32, Android, Ruijie and Orange Pi/x86 variants) completed PASS. Update-bundle, simulations, signing and publication were skipped. This was the expected pre-handover freshness failure; a fresh docs-head Full run is required.

### Preservation and acceptance

Only the host lab runner/modules and Hardware workflow path filters changed. No production ESP8266/ESP32 sketch, controller API, finance, receipt/disposition, QA-owned assertion, migration, signer/witness, release workflow, or COE source changed. This is source-extracted host simulation/CI only; physical EEPROM/NVS brown-out, GPIO/relay voltage, LittleFS recovery, electrical pulse retention, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** rerun Full on the refreshed documentation head; keep the inherited QA controller-parity assertion and CORE authenticated-response contract as separate blockers. No flash, reset, live coin/money, secret provisioning, signing, migration, merge, release or deployment.
