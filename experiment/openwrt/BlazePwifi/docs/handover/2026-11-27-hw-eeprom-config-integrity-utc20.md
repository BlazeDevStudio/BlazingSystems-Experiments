## PHX-HARDWARE UTC20 — 2026-11-27 UTC20 — EEPROM fixed-array guard CI verified; Full integration blocked by QA contract

**Role:** PHX-HARDWARE · **Task:** #177 / #266 / PR #355 · **PR:** OPEN / DRAFT / UNMERGED  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments · **Branch:** phoenix/hw-poll-preflight-lab-modules-20261127-utc18 · **Parent #354:** fc842342596786e072630179acfbbc4feeb2ba02  
**Exact source/test SHA:** ec70269ddc052351606165f06e4a3c6586616c04  
**Firmware correction:** 5aa21736213c609398f1f1c4a42f41c106cf7e84 · **Current docs HEAD before this update:** b2707114c45e8e5bfbed38429cdc3b60551bdc4f.

### Proven defect and correction

ESP8266 EEPROM Config/ConfigV1 contain fixed-size character arrays. The previous loadCfg() used unbounded strlen(cfg.apPass) on raw EEPROM bytes and migrated legacy strings with strlcpy before proving that each source array contained a NUL terminator. A corrupt but magic-matching EEPROM record could cause an out-of-bounds read during validation or migration.

The firmware now uses boundedStringLength(value, capacity), configStringsTerminated(), and configV1StringsTerminated(). Current records are accepted only when all six fixed arrays are terminated and the AP password is at least eight bytes. Legacy records are copied only after all five legacy arrays pass bounded validation. Invalid records take the existing defaults path.

The helper block follows LegacyPendingRecord to preserve Arduino prototype generation. The lab protects this ordering. No EEPROM layout, field size, magic, valid-record migration, pin mapping, pending journal, network API, coin/relay admission or financial behavior changed. ESP32 source was not changed because its configuration uses Preferences String values.

### Exact-source and target evidence

- Test-first RED: [#45892727658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892727658), job 140159081554; failed before the bounded helper existed.
- Intermediate source/test failures preserved: [#45892930825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45892930825) caught the first incorrectly escaped NUL literal; [#45893091506](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45893091506) caught the test's use of masked source for a character-literal assertion. Both corrected.
- Exact docs-head focused [#45894378940](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894378940), job 140164527129: PASS. Current arrays 6/6; legacy arrays 5/5; 5/5 unsafe mutations rejected.
- Exact-source Mbed TLS [#45894193769](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894193769): source-contract, ESP32 core 3.3.13 and 4.0.0 all PASS at source/test SHA ec70269d.
- Docs-head Mbed TLS [#45894378942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894378942): source-contract PASS; 3.3.13 and 4.0.0 target builds still running at this checkpoint.
- Full docs-head [#45894378927](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894378927): mandatory handover freshness + CI-0701 PASS; all 13/13 firmware/platform target jobs PASS, including ESP8266 job 140164701393 and ESP32 job 140164701316. Android job 140164701273 was still running. Full validation fails at QA-owned tests/controllers.sh:21 because the deny-only sketches intentionally have no config_revision consumer. Production import, update, simulation, candidate, signing and publication stages are skipped.
- Native synthetic [#45894379001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45894379001): FAIL at QA-owned active clearPending(true/false) assertion. Hardware did not add a disposition callsite.

### Coordination

Experiments main HEAD: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5. Active v0.6 audit-foundation: 2fbd2475e9f54878c316fa7cea2f228386b0e859. Master coordination HEAD: 0e8a59a0463d522ddff95371a60cf271d4c752bc; Master now lists #355 in ROLE_ASSIGNMENTS and INTEGRATION_MATRIX. Root README still contains historical BlazingSystems organization links; Master should reconcile those to BlazeDevStudio.

PR #239 head d83b715b, #254 head 84c442a4 and #283 head 4dd0b01b remain OPEN / DRAFT / UNMERGED. COE main remains a6513ab4; COE PR #26 remains frozen at b382d233. Cleanup-first #266 remains OPEN / 0-of-7. Issues #31/#32/#34/#43 remain OPEN.

The private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json is not accessible through the exposed connector or Library search; no older checkpoint was substituted. The owner-uploaded hourly signal README describes a signal-only issue/comment workflow, not an AI worker.

### Acceptance status

EEPROM helper host harness = SIMULATED / CI VERIFIED. ESP8266/ESP32/OpenWrt target builds = CI VERIFIED at this docs-head Full run. ESP32 Mbed TLS 3.3.13/4.0.0 = CI VERIFIED at exact source/test SHA; docs-head matrix still running. Full controller integration = FAIL / BLOCKED by QA-owned deny-only assertion. Android job = NOT COMPLETE at this checkpoint.

Physical EEPROM corruption/recovery, GPIO voltage, relay contact, real coin pulse, electrical recovery, 150 power cuts and 30-device/24-hour soak = NOT TESTED. Protected signer/witness, durable accounting/replay, v1→v2 migration and independent QA/release signoff = NOT ACCEPTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No flash, reset, customer data, live money, migration, deployment, merge, force-push or release tag.

**Next exact action:** QA reconciles controllers.sh:21 and the Native pending-disposition assertion with the deny-only candidate; CORE publishes the authenticated register/poll and pending-disposition contract; Hardware waits for those shared contracts before any response consumer or clearPending callsite.
