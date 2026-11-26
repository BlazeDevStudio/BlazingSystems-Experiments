## PHX-HARDWARE UTC20 — 2026-11-27 UTC20 — EEPROM config integrity guard IN PROGRESS

**Role:** PHX-HARDWARE · **Task:** #177 / #355 · **PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18` · **Parent:** #354 `fc842342596786e072630179acfbbc4feeb2ba02`  
**Test-first commit:** `1f7af928c9ecf51454e262e3b45483c6488f22d8`  
**Expected RED:** [run #45892727658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892727658), job `140159081554`, failed at the new lab because the bounded validator is not yet implemented. Existing poll/register/auth/output tests completed before that expected failure.

### Proven defect under correction

ESP8266 `Config` and `ConfigV1` contain fixed-size EEPROM character arrays. The current `loadCfg()` checks `strlen(cfg.apPass)` before proving the EEPROM field is NUL-terminated, and the legacy migration copies old fixed arrays before proving each source is terminated. A corrupt but magic-matching EEPROM record can therefore trigger an out-of-bounds read during configuration validation/migration.

### Bounded task

Add a capacity-limited string-length helper and explicit current/legacy record validators. Reject unterminated current or legacy records before any string copy; retain existing config layout, defaults, migration behavior for valid records, pin values, and deny-only startup. Add a host C++ harness compiled with AddressSanitizer/UBSan and source mutations for missing current/legacy validation and reintroducing unbounded AP-password length.

### Current evidence and limitations

- Test-only commit: `1f7af928c9ecf51454e262e3b45483c6488f22d8`.
- Expected RED log: [#45892727658 / job 140159081554](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892727658).
- No production source correction is committed yet.
- No EEPROM image, live device, flash, filesystem migration, financial state, or customer data was touched.
- Physical boot/GPIO behavior, electrical acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

**Next exact action:** implement the bounded validators in the ESP8266-owned sketch, then require exact-head focused CI GREEN and re-run the mutation harness.
