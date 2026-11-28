## PHX-HARDWARE UTC05 — externalize EEPROM loadCfg runtime fixture (#373)

**PR #373: OPEN / DRAFT / UNMERGED**, child of #372. Parent base: `96a22ba3af1411a016478eee56c5f0fdbbc2b512`.
**Branch:** `phoenix/hw-loadcfg-runtime-fixture-template-20261128-utc05`. **Task:** `PHX-HW-LOADCFG-FIXTURE-TEMPLATE-20261128T05Z`.

### Cleanup-first change

The source-extracted C++11 runtime fixture was previously embedded as a roughly 280-line Python raw string inside `config_storage_integrity_lab_harness.py`. It is now a standalone `config_loadcfg_runtime_fixture.cpp.in` template so firmware declarations and native test logic can be inspected with normal C++ syntax highlighting and without scrolling through a large Python string.

The Python harness now:
- extracts the real `ConfigV1`, `Config`, `MAGIC_V1`, `MAGIC`, validation helpers, `defaults()`, `saveCfg()` and `loadCfg()` from the sketch;
- reads the adjacent C++ fixture template;
- substitutes four named markers, requiring each marker to occur exactly once;
- rejects any unresolved marker before compilation.

The C++ fixture body and its runtime assertions were moved verbatim; only four insertion markers replace the previous Python concatenation points. Existing command entry point and test semantics are retained. The focused workflow now watches the template and this child branch.

### Verification plan and limits

- Focused exact-source run: pending on this commit.
- Mbed TLS 3.3.13 / 4.0.0: pending on this commit.
- Full integration: pending on this commit; the inherited QA-owned `tests/controllers.sh:21` `config_revision` assertion remains a separate known blocker.
- Local checkout unavailable in this runtime; no local test result is claimed. GitHub Actions is the execution authority for this branch.

No production `.ino`, controller API, config schema, finance/receipt state, QA-owned assertion, signer/witness, migration runtime, COE destination or physical device changed. This remains host simulation/CI evidence only. Physical EEPROM/NVS brown-out, GPIO/relay, LittleFS power-loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

**Rollback:** close/revert only this child PR; parent #372 and earlier stack remain unchanged.
**Next:** verify exact-head Focused and Mbed results, then Full; append terminal job evidence without rewriting historical records.

Updated UTC: 2026-11-28T05:08:53Z.

## UTC05 exact-head terminal evidence — PR #373

Source/test commit `8d33f53396a9357f4e2d2dd931e66ce2bfc91765` on `phoenix/hw-loadcfg-runtime-fixture-template-20261128-utc05`; PR #373 remains OPEN / DRAFT / UNMERGED.

- Focused PR [run #46111352698](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111352698), job `140875370614`: **PASS**. The EEPROM runtime output is `EEPROM_LOADCFG_RUNTIME_PASS current=1/1 current_invalid=6/6 legacy=1/1 legacy_invalid=5/5 commit_retry=2/2`; seven source mutations rejected (7/7). The same exact-source job passed the append-only ledger guard: base 1,132,798 bytes; appended 55,989 bytes. Push exact-head Focused [#46111347759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111347759) also PASS.
- Mbed [run #46111352724](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111352724): **3/3 PASS** — source-contract job `140875370853`, ESP32 core 3.3.13 job `140875370794`, core 4.0.0 job `140875370653`.
- Full PR [run #46111352710](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111352710): **TERMINAL FAILURE** at validation job `140875418595`. CI-0701 and mandatory handover freshness passed; QA-owned `tests/controllers.sh:21` fails on the literal `config_revision` presence assertion. All 14/14 target/platform jobs passed: ESP8266, ESP32, Android, Ruijie, x86_64, Orange Pi PC/One/Zero3, and optional PC2/PC+/One+/Zero/Zero2/Zero2W. Downstream update bundle, simulations, candidate, signing and publication were skipped. Exact-head push Full [#46111347820](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111347820) has the same terminal validation failure and 14/14 target/platform PASS.
- This confirms the template extraction executes in the existing native C++11 ASan/UBSan test; it does not change the inherited controller-parity blocker.

No production `.ino`, controller API, config schema, finance/receipt state, QA-owned assertion, signer/witness, COE destination or physical device changed. Physical EEPROM/NVS brown-out and all required electrical/hardware acceptance remain **NOT TESTED**. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.
