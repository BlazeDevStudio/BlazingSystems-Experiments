## PHX-HARDWARE UTC20 — 2026-11-27 UTC20 — EEPROM fixed-array guard CI verified; production remains NO-GO

**Role:** PHX-HARDWARE · **Task:** #177 / #266 / PR #355 · **PR:** OPEN / DRAFT / UNMERGED  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments · **Branch:** phoenix/hw-poll-preflight-lab-modules-20261127-utc18 · **Parent #354:** fc842342596786e072630179acfbbc4feeb2ba02  
**Exact source/test SHA:** ec70269ddc052351606165f06e4a3c6586616c04  
**Firmware correction:** 5aa21736213c609398f1f1c4a42f41c106cf7e84 · **Test/report correction:** ec70269ddc052351606165f06e4a3c6586616c04  
**Test-first RED:** 1f7af928c9ecf51454e262e3b45483c6488f22d8.

### Proven defect and firmware correction

ESP8266 EEPROM Config/ConfigV1 contain fixed-size char arrays. The previous loadCfg() used unbounded strlen(cfg.apPass) on raw EEPROM bytes and migrated ConfigV1 strings with strlcpy before proving that each source array contained a NUL terminator. A corrupt but magic-matching EEPROM record could cause an out-of-bounds read during validation or migration.

The firmware now uses boundedStringLength(value, capacity), configStringsTerminated(), and configV1StringsTerminated(). Current records are accepted only when all six fixed arrays are terminated and the AP password length is at least eight. Legacy records are copied only after all five legacy arrays pass the bounded validation. Invalid records take the existing defaults path.

The helper block is placed after LegacyPendingRecord so Arduino prototype generation can resolve the legacy type. The lab now protects that ordering. No EEPROM layout, field size, magic, valid-record migration, pin mapping, pending journal, network contract, coin/relay admission, or financial behavior changed. ESP32 source was not changed because it stores these settings as Preferences String values.

### Exact-source test evidence

- Expected RED: [#45892727658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892727658), job 140159081554: new lab failed because the bounded helper did not yet exist.
- Intermediate source/test failures were preserved: [#45892930825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892930825) failed on an incorrectly escaped NUL literal; [#45893091506](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893091506) failed because the source masker erased the character literal before the source assertion. Both were corrected.
- Exact latest focused run [#45894193755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894193755), job 140163917362: PASS at source/test SHA ec70269d. Logs report current arrays 6/6, legacy arrays 5/5, and 5/5 unsafe mutations rejected.
- Previous exact focused run [#45893670177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893670177), job 140162187552: PASS after moving helpers below LegacyPendingRecord. It caught the Arduino prototype-order compile issue before the ordering correction.
- ESP32 Mbed TLS matrix [#45893670154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893670154): source contract job 140162234337, core 3.3.13 job 140162234916 and core 4.0.0 job 140162234941 all PASS at the preceding source/test SHA a2d4ab0b. The later ec70269 change only corrected the test's printed mutation count.
- Full run [#45893670193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893670193): ESP8266 job 140162296409 PASS, ESP32 job 140162296305 PASS, and all 13/13 target/platform build jobs PASS before the run was cancelled by a newer PR update; Android was still running. Validation job 140162296365 failed the handover freshness gate because the checkpoint predated the source/test commits.
- Latest exact-head Full [#45894193923](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894193923): running at this handover checkpoint; a fresh docs-head run is required after this commit.
- Native synthetic [#45894193808](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894193808): FAIL at QA-owned active clearPending(true/false) assertion. Hardware did not add a disposition callsite.

### Current coordination and blockers

Main HEAD: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5. Active v0.6 audit-foundation: 2fbd2475e9f54878c316fa7cea2f228386b0e859. Master PR #288 head: 0e8a59a0463d522ddff95371a60cf271d4c752bc. PR #239 head d83b715b, #254 head 84c442a4, and #283 head 4dd0b01b remain OPEN / DRAFT / UNMERGED. COE main remains a6513ab4; COE PR #26 remains frozen at b382d233. Cleanup-first #266 remains OPEN / 0-of-7. Issues #31/#32/#34/#43 remain open.

The repository README on main still has historical BlazingSystems organization links; Master should reconcile those with the verified BlazeDevStudio owner. The private Drive registry v11 was not accessible through the current connector surface or Library search; no older checkpoint was substituted. The owner-uploaded hourly-signal README confirms that the YAML creates an issue/comment only and is not an AI worker.

### Status

EEPROM helper source contract: SIMULATED / CI VERIFIED. ESP8266 target build: CI VERIFIED at the preceding source/test head. ESP32 Mbed TLS 3/4 matrix: CI VERIFIED at the preceding source/test head. Physical EEPROM corruption/recovery, GPIO voltage, relay contact, real coin pulse, electrical recovery, 150 power cuts and 30-device/24-hour soak: NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No physical flash, reset, customer data, live money, signer, migration, deployment, merge, force-push or release tag was used.

**Next exact action:** finish the current exact-head Full run; after this handover commit, require the fresh docs-head validation to reach the QA-owned deny-only assertions. Request CORE/QA reconciliation without enabling positive coin admission.
