

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

