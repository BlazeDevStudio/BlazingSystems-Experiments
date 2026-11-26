## PHX-HARDWARE UTC20 — 2026-11-27 UTC20 — EEPROM fixed-array validation CI verified; integration still blocked

**Role:** PHX-HARDWARE · **Task:** #177 / cleanup-first #266 / PR #355 · **PR:** OPEN / DRAFT / UNMERGED  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` · **Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18` · **Parent #354:** `fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test SHA:** `93e850db847760f51a4470c4bda1c46bfc730278` · **Firmware fix:** `106aabb007b7b4c2aee1978645d07214cf668e87`  
**Test-first RED:** `1f7af928c9ecf51454e262e3b45483c6488f22d8`.

### Proven defect and correction

ESP8266 `Config` and `ConfigV1` contain fixed-size EEPROM character arrays. The previous `loadCfg()` used unbounded `strlen(cfg.apPass)` on raw EEPROM bytes and migrated legacy strings with `strlcpy` before proving that the source arrays contained NUL terminators.

The firmware now uses `boundedStringLength(value, capacity)`, `configStringsTerminated()`, and `configV1StringsTerminated()`. Current records are accepted only when all six fixed arrays are terminated and the AP password is at least eight bytes. Legacy records are copied only after all five legacy arrays pass the bounded check. Invalid records follow the existing defaults path.

No EEPROM layout, field size, magic, valid-record migration, pin mapping, journal format, network protocol, relay/coin admission or financial behavior was changed. ESP32 uses Preferences `String` fields and was not modified for this ESP8266-specific defect.

### Exact test evidence

- Test-first RED: [#45892727658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892727658), job `140159081554`: failed because the new lab could not find the not-yet-implemented bounded validator.
- Initial implementation attempt: [#45892930825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892930825), job `140159758106`: failed in sanitizer harness compilation; the first helper draft encoded the NUL character literal incorrectly. Corrected in `106aabb`.
- Test assertion iteration: [#45893091506](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893091506), job `140160286995`: failed because the source masker blanked the character literal before the assertion inspected it. The test now inspects raw source for the NUL token and uses masked source only for structural checks.
- Exact source/test GREEN: [#45893204086](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204086), job `140160658946`: PASS. AddressSanitizer/UBSan C++ harness reports `EEPROM_CONFIG_BOUNDED_VALIDATION_PASS current=6/6 legacy=5/5`; all three unsafe mutations are rejected.
- Current-head ESP32 Mbed TLS matrix [#45893204195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204195): pending at this documentation checkpoint.
- Native synthetic [#45893204123](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204123), job `140160659781`: FAIL at QA-owned active `clearPending(true/false)` assertion; no Hardware-side bypass added.
- Full [#45893204180](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893204180), validation job `140160838183`: FAIL at the mandatory handover freshness gate because the last checkpoint was `382f8ea` and source/test commits followed it. This is a documentation-sync failure, not a new firmware compile result. A fresh docs-head Full run is required after this commit.

### Boundaries and physical status

The new lab is `config_storage_integrity_lab.py`, included in the focused workflow path filters and exact-source job. It compiles extracted production helper/struct code under `-fsanitize=address,undefined`, checks every current and legacy fixed array, and injects removal of current validation, legacy validation, the NUL comparison and the bounded AP-password check.

No EEPROM was read from a physical device; no flash, reset, filesystem migration, payment, secret or customer data was touched. Host/sanitizer evidence is **SIMULATED / CI VERIFIED**, not hardware acceptance. Electrical boot behavior, physical GPIO/relay, coin pulses, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next exact action:** run a fresh Full validation at the post-sync docs HEAD, retain the QA-owned pending-disposition failure, and request CORE/QA contract reconciliation without adding positive coin admission.
