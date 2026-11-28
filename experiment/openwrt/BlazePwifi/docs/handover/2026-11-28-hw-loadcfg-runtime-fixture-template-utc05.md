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
