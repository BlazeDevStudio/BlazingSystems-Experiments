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

---

## PHX-HARDWARE UTC05 — EEPROM fixture marker failure injection (#373) — SCOPED CI VERIFIED / FULL REFRESH REQUIRED

**PR #373:** OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-loadcfg-runtime-fixture-template-20261128-utc05`  
**Parent:** #372 at `96a22ba3af1411a016478eee56c5f0fdbbc2b512`  
**Source/test commit:** `e411a99c23485f4f92720aa38cf29dca757b5190`  
**Updated UTC:** 2026-11-28T05:47:00.633Z

### Actual source changes

- Centralized the four required C++ fixture marker names in `RUNTIME_FIXTURE_MARKERS`.
- Extracted the pure `render_runtime_fixture()` path so the same exact-once/unresolved-marker checks are used by the production test runner and mutation tests.
- Added `expect_runtime_fixture_rejected()` with expected-error matching, so a malformed template cannot pass merely because it failed for an unrelated reason.
- Added nine failure injections: each of four markers missing, each duplicated, and one unknown unresolved `PHX_CONFIG_` marker. A valid four-marker render is the positive control.
- Kept the source-extracted EEPROM runtime fixture, production sketches, controller API, persistence schema, and QA-owned assertions unchanged.

### Exact source-head evidence

- Focused [run #46113449436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113449436), job `140881884708`: **PASS**. Log: `EEPROM_RUNTIME_TEMPLATE_FAILURE_INJECTION_PASS 9/9`; current config 1/1, current invalid fields 6/6, legacy migration 1/1, legacy invalid fields 5/5, commit-failure retry 2/2, existing source mutations 7/7, and append-only ledger guard PASS (base 1,132,798 bytes; appended 56,991 bytes).
- Mbed [run #46113449427](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113449427): source-contract job `140881885041` PASS; ESP32 core 3.3.13 job `140881885126` and core 4.0.0 job `140881884923` were still running at this handover checkpoint.
- Initial Full [run #46113449515](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113449515): CI-0701 job `140881886000` PASS; validation job `140881928595` failed the mandatory handover freshness gate because this record had not yet been updated after source commit `e411a99`. This is a pre-refresh run, not a controller-parity result. Target jobs were still running; downstream update/simulation/signing/publication stages were skipped. Full must be rerun on the refreshed docs head.

### Safety and ownership

This is a host-test contract improvement only. No production .ino, active v0.6 deny candidate, CORE API, finance, receipt/disposition, signer/witness, migration runtime, QA-owned assertion, COE destination, or physical device was changed. Template failure injection is **SIMULATED / CI VERIFIED**, not physical EEPROM/NVS acceptance. Physical GPIO/relay, EEPROM/NVS brown-out, LittleFS power loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

### Coordination / next exact action

- PHX-QA still owns `tests/controllers.sh:21` controller-parity semantics; do not add a fake `config_revision` field.
- PHX-CORE still owns the authenticated register/poll/receipt/disposition contract.
- PHX-MASTER's current #288 role/integration matrices pin through #371 and need a refresh for #372/#373.
- PHX-HARDWARE: confirm terminal Mbed results, rerun Full after this handover refresh, and record exact docs-head outcomes. Keep #373 DRAFT / UNMERGED.


---

## PHX-HARDWARE UTC05 correction — append-only ledger restored after bounded-read failure

PR #373 remains OPEN / DRAFT / UNMERGED. Source/test commit `e411a99c23485f4f92720aa38cf29dca757b5190` has Focused PASS (9/9 new template mutations; existing EEPROM matrix PASS) and Mbed 3/3 PASS. The first docs refresh `36a910f0` used a bounded file-content response for the large ledger; exact docs-head Focused run #46113667258 job `140882561193` failed the append-only guard with candidate size 3,497 bytes versus 1,132,798-byte base. This was a documentation update error, not a source/test failure.

The full original ledger was recovered from immutable parent blob `4d1590ed144e399f552e403c30b971c0bf3d022f` (1,188,219 characters), not from a partial fetch. Its prefix matches the exact #354 base blob `b950f7be47f79d71e6cb8b721801c1bae128df45` (1,131,320 characters) byte-for-byte after GitHub's UTF-8 representation. The complete prior history is restored and the UTC05 record is appended. Final append-only verification is pending on the repair head.

## 2026-11-28 UTC05 — PR #373 template-marker tests and ledger restoration

- Hardware source/test commit: `e411a99c23485f4f92720aa38cf29dca757b5190`; PR #373 remains OPEN / DRAFT / UNMERGED.
- Focused source-head run [#46113449436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113449436), job `140881884708`: PASS; the new runtime-template mutation suite reports 9/9 rejected, while the existing EEPROM current/legacy/commit-retry matrix and 7/7 source mutations pass.
- Mbed source-head run [#46113449427](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113449427): source-contract `140881885041`, ESP32 core 3.3.13 `140881885126`, and core 4.0.0 `140881884923` all PASS.
- Docs refresh commit `36a910f065fa506febf4134e6d7909cfca1c8d86` accidentally used the bounded `fetch_file` response for the 1.18M-character ledger. Docs-head Focused run [#46113667258](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46113667258), job `140882561193`, correctly FAILED: `CHANGE_LEDGER_APPEND_ONLY_FAIL candidate does not preserve the base byte-for-byte (common_prefix_bytes=0 base_bytes=1132798 candidate_bytes=3497)`. This is a handover-writing error, not a firmware/test regression.
- Recovery: fetched the complete immutable parent ledger blob `4d1590ed144e399f552e403c30b971c0bf3d022f` (1,188,219 characters) and exact #354 base blob `b950f7be47f79d71e6cb8b721801c1bae128df45` (1,131,320 characters). Verified `fullLedger.startsWith(historicalBase) === true`; the full prior history is restored below with this record appended. No historical entry was reconstructed from snippets.
- The docs-head Full run #46113667260 had not reached terminal state at this correction checkpoint. Its result must be re-read after this repair.
- Updated UTC: 2026-11-28T05:49:14.868Z.

**Disposition:** retain PR #373 DRAFT / UNMERGED. Re-run the focused append-only guard on the repaired docs head, then verify the final Full/Mbed results. Physical hardware acceptance remains NOT TESTED; HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

