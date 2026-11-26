2026-11-27 UTC19 | PHX-HARDWARE | PR #355 | test-first RED 39aa77e56806df3c1febae0f0a097b0f661ca2c6 (run #45886210859/job 140137430702: both boards rejected unsafe startup order); firmware correction 6bb8eafe03e5a2548524b7c693a37a95638c140e moves ESP8266 initPendingStore and ESP32 LittleFS mount/recovery after configured pin OFF preload + denyRemoteControl. Exact-head GREEN pending; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## 2026-11-27 UTC19 — exact-head startup output latch evidence

- Source/test HEAD: `6b4f7a873dd72663c00c4e08f23131d58e662584`; firmware correction: `6bb8eafe03e5a2548524b7c693a37a95638c140e`.
- Expected RED: run `45886210859`, job `140137430702`, both boards rejected the unsafe pre-fix order.
- Focused GREEN: run `45886748490`, job `140139222908`, both boards pass startup output-before-LittleFS and reject the early-mount mutation.
- ESP32 Mbed TLS matrix: run `45886748407`; source-contract `140139828100`, core 3.3.13 `140139827987`, core 4.0.0 `140139827660` all PASS.
- Full run `45886748466`: CI-0701 `140140022161`, ESP8266 `140140135665`, ESP32 `140140135695`, and 13 OpenWrt/target jobs PASS; Android `140140135671` in progress at last check. Validation `140140135720` failed only because this ledger lacked the required dated `## 2026-` heading. Fresh Full required after this documentation commit.
- Native synthetic `45886748463` remains FAIL on QA-owned active-`clearPending` assertion; no QA source changed.
- Physical acceptance remains NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## 2026-11-27 UTC19 — post-sync Full gate and QA contract result

- Final docs head before this update: `d4a35e5e12b8abd85b6a45fa6902d09471c84e4d`; exact source/test SHA: `6b4f7a873dd72663c00c4e08f23131d58e662584`.
- Focused docs-head run `45887618603`, job `140142163199`: PASS.
- Mbed exact-source run `45886748407`: source-contract `140139828100`, core 3.3.13 `140139827987`, core 4.0.0 `140139827660`: PASS.
- Full run `45887618795`: CI-0701 `140142273647` and mandatory handover freshness/history gates PASS; QA-owned `tests/controllers.sh:21` fails because the deny-only sketches intentionally have no `config_revision` response consumer. ESP8266 and 13 OpenWrt target jobs PASS; ESP32/Android still running at last check.
- Native run `45887618600` fails QA-owned active-`clearPending` assertion; current sketches have definition-only clear helper and no disposition callsite.
- Production/HARDWARE ACCEPTED = NO; physical acceptance NOT TESTED; PRODUCTION READY = NO-GO.


2026-11-27 UTC20 | PHX-HARDWARE | PR #355 | Test-first EEPROM config integrity guard committed at `1f7af928c9ecf51454e262e3b45483c6488f22d8`; new source-extracted lab fails as expected because bounded current/legacy validators are not implemented. Expected RED #45892727658/job 140159081554. No firmware fix yet; source remains deny-only; physical acceptance NOT TESTED; PRODUCTION NO-GO.


2026-11-27 UTC20 | PHX-HARDWARE | PR #355 | EEPROM fixed-array validation: test-first RED #45892727658/job 140159081554; initial helper compilation failed #45892930825/job 140159758106 due incorrect NUL literal; test assertion failed #45893091506/job 140160286995 because mask_non_code erased the char literal; both defects corrected. Exact source/test GREEN #45893204086/job 140160658946: current=6/6 and legacy=5/5 unterminated-array checks pass under ASan/UBSan; 3/3 injected unsafe mutations rejected. Native #45893204123 remains FAIL at QA-owned active-clear assertion. Full #45893204180 validation fails only the handover freshness gate pending this docs sync. Physical acceptance NOT TESTED; PRODUCTION NO-GO.


2026-11-27 UTC20 | PHX-HARDWARE | PR #355 | Exact focused EEPROM guard #45893204086/job 140160658946 PASS (current=6/6, legacy=5/5, 3/3 mutations rejected). Full #45893204180 also exposed an ESP8266 compile failure at LegacyPendingRecord because helper placement precedes the struct and Arduino prototype generation cannot resolve the type; move helpers below the struct and add order guard. Native #45893204123 remains QA-owned active-clear failure. No hardware acceptance; PRODUCTION NO-GO.


2026-11-27 UTC20 | PHX-HARDWARE | PR #355 | ESP8266 EEPROM fixed-array validator and legacy migration guard implemented. Source/test SHA ec70269ddc052351606165f06e4a3c6586616c04; firmware ordering correction 5aa21736213c609398f1f1c4a42f41c106cf7e84. Focused #45894193755/job 140163917362 PASS: current 6/6, legacy 5/5, failure injection 5/5. Mbed TLS matrix #45893670154 all 3 jobs PASS at preceding source/test SHA. Full #45893670193: 13/13 target builds PASS, ESP8266 and ESP32 PASS, Android still running when canceled; validation failed stale handover gate. Native #45894193808 fails QA-owned active clearPending assertion. No physical acceptance; PRODUCTION NO-GO.


2026-11-27 UTC20 | PHX-HARDWARE | PR #355 | Exact docs-head focused #45894378940/job 140164527129 PASS: current 6/6, legacy 5/5, 5/5 unsafe mutations rejected. Exact source/test Mbed TLS #45894193769 source-contract + ESP32 core 3.3.13/4.0.0 PASS. Full docs-head #45894378927: handover freshness + CI-0701 PASS, all 13/13 target/platform jobs PASS, Android still running; validation FAIL at QA-owned tests/controllers.sh:21 config_revision assertion. Native #45894379001 FAIL at QA-owned active clearPending assertion. Physical acceptance NOT TESTED; PRODUCTION NO-GO.


## 2026-11-27 UTC21 — ESP configuration persistence write-result guard

- Firmware correction: `26a28c763168e2881d5b8e36d859a0a72d704524`; exact focused source/test SHA: `835017d95c129fb52b8fdca82032f1fb9a83ac33`.
- ESP8266 now propagates `EEPROM.commit()`; ESP32 checks all 13 Preferences write results. Both setup-save handlers deny outputs, return HTTP 500 and do not reboot on storage failure. ESP32 multi-key writes remain non-atomic.
- Expected RED: [#45896260968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896260968), job `140170795839`. Focused GREEN: [#45896670130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896670130), job `140172158275`, PASS; EEPROM failure propagation, 13/13 Preferences write checks and 4/4 injected regressions.
- Test-authoring failures #45896421871 and #45896529929 were corrected; they were not firmware failures.
- Full #45896670128 CI-0701 passed but validation stopped at the stale handover freshness gate before this sync; target jobs were still running. Native #45896670074 fails QA-owned PAY-0745. Mbed #45896670138 pending.
- Physical storage/power-cut/relay acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.

- Source-comment clarification: EEPROM commit result must be honored; ESP32 Preferences multi-key writes are not atomic. Comment-only source sync is included with this documentation refresh.


## 2026-11-27 UTC21 — final exact-head reconciliation

- Exact focused source/test head `facf4cd7efee2df199475e6ae2e135429210eb87`, job `140173655648` in run `45897118576`: PASS. EEPROM commit failure and 13/13 Preferences write results propagated; 4/4 injected config-persistence regressions rejected.
- Full run `45897118594`: CI-0701 + handover freshness PASS; validation job `140173820395` fails QA-owned `tests/controllers.sh:21` (`config_revision`). Full target jobs were still running.
- Mbed matrix `45897118552`: source-contract PASS; core 3.3.13 and 4.0.0 builds still running. Native `45897118723` job `140173656134` FAIL at QA-owned PAY-0745 pending sequence/corruption assertion.
- Master coordination HEAD `0e8a59a0463d522ddff95371a60cf271d4c752bc` records #355 in both role assignment and integration matrix. #177 remains unresolved; #266 OPEN / 0-of-7; #31/#32/#34/#43 open.
- Physical acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.


## 2026-11-27 UTC21 — terminal target and Mbed evidence

- Exact focused source/test head `facf4cd7efee2df199475e6ae2e135429210eb87`: run `45897118576`, job `140173655648`, PASS; EEPROM commit result and 13/13 Preferences write results propagated; 4/4 injected config-persistence regressions rejected.
- Full `45897118594`: CI-0701 + handover freshness PASS; validation `140173820395` FAIL at QA-owned `tests/controllers.sh:21` (`config_revision`). All 14/14 target/platform build jobs PASS (ESP8266, ESP32, Android and 11 firmware targets). Production import, simulation, candidate, signing and publication skipped.
- ESP32 Mbed matrix `45897118552`: 3/3 PASS — source-contract `140174115684`, core 3.3.13 `140174116287`, core 4.0.0 `140174115903`.
- Native synthetic `45897118723`, job `140173656134`, FAIL at QA-owned PAY-0745. #177 remains unresolved; #266 OPEN / 0-of-7; #31/#32/#34/#43 open.
- Physical acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.
