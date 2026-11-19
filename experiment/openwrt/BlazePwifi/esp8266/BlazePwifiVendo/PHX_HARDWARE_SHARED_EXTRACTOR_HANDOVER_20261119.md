# PHX-HARDWARE handover — shared lexical source extraction

**Date:** 2026-11-19 UTC12  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hardware-prepoll-edge-abort-20261119  
**Parent/base:** PR #326 at 58c558fb6a237935214621adc3dee65a10fe1a51  
**Latest exact source/test commit:** 7db41068f9471565471982030f4c119880908291  
**Disposition:** shared extractor and raw-string/phase-2 regression focused CI VERIFIED on ESP32/ESP8266; Full validation FAILED at inherited QA-owned poll-signature assertion; 13/13 firmware/platform targets plus Android compiled; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## Task and rationale

The hardware-owned coin/poll host labs duplicated raw-brace C/C++ function extractors. Those parsers counted braces inside string literals and comments as real syntax, so a source fixture could be truncated or mis-extracted while the host lab still appeared structurally valid. These labs are used to validate the actual ESP8266/ESP32 function bodies for coin capture, poll-window draining, blocking-poll inhibition and request-digest default-deny behavior.

This was a cleanup-first test-integrity task. No firmware runtime behavior, wire contract, journal schema, finance behavior, relay policy, GPIO assignment or production state was changed.

## Changes

The following four hardware-owned labs now use the single lexical helper firmware_lab_source.extract_function():

- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_drain_lab.py
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/request_digest_failure_lab.py

Their duplicate local regex/raw-brace extractors were removed.

The shared helper firmware_lab_source.py now recognizes both attribute orders used by the two MCU toolchains, including return-type-then-attribute forms such as void ICACHE_RAM_ATTR coinEdgeISR() and void IRAM_ATTR coinEdgeISR(). This keeps the ISR body available to the poll-loop host lab.

The coin-pulse lab now has a shared-extractor regression fixture covering braces inside a C++ string, a line comment and a block comment, plus post-return ICACHE_RAM_ATTR and IRAM_ATTR declarations.

## Test-first history and correction transparency

- RED test-only commit 388a7e72c89d25baebbf72afa7e6295d16461b73: push run [#44517327040](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44517327040), job 135536621891, FAILED as expected because the old raw-brace extractor stopped at the brace inside a C++ string/comment fixture.
- Initial shared-helper attempt 9e95a8b34b48acf40cb96e35cf8482083116dd20 failed its own fixture with an unbalanced-block error: the fixture had an incorrectly escaped newline. This was a test-fixture construction error, not a firmware defect. The fixture was corrected in 19166d46be2f8a61db69901d7c62d63106644c04; the final exact-head tests below pass.
- Refactor commit 2a91457223f30d1c6b433a610b51744ded2f1327 removed the four duplicate extractors and routed the labs through the shared helper.
- Helper attribute-order correction was committed in 9e95a8b34b48acf40cb96e35cf8482083116dd20; final newline/attribute regression fixture correction is in 19166d46be2f8a61db69901d7c62d63106644c04.

## Final exact-source CI at 19166d46be2f8a61db69901d7c62d63106644c04

Focused quarantine/readback:
- Push [#44518282442](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44518282442), job 135539924868: SUCCESS.
- PR [#44518290664](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44518290664), job 135539953297: SUCCESS.
- Logs include SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS, SHARED_EXTRACTOR_ISR_ATTRIBUTE_ORDER_PASS, ESP8266_COIN_PULSE_CAPTURE_PASS 11/11, ESP32_COIN_PULSE_CAPTURE_PASS 11/11, POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS, ESP8266_POLL_WINDOW_DRAIN_PASS 11/11, ESP32_POLL_WINDOW_DRAIN_PASS 11/11, and REQUEST_DIGEST_FAILURE_DENY_PASS on both boards.
- Existing quarantine, pending-journal, readback, poll-response deny, digest and persistence host labs also completed successfully. These are source-extracted/fake-I/O simulations, not physical hardware proof.

Relay/output:
- PR [#44518290697](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44518290697): ESP32 boot-polarity job 135539953193 SUCCESS; source-output-polarity job 135539953902 SUCCESS.

Full BlazePwifi build:
- Push [#44518282416](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44518282416), validation job 135540058447: FAILURE — Missing poll signature check in the ESP8266 sketch.
- PR [#44518290715](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44518290715), validation job 135540086568: same FAILURE.
- Despite validation failure, both runs completed all 13 firmware/platform target jobs successfully and Android successfully. ESP32 and ESP8266 compilation passed. Update bundle, simulations, signing, candidate gate and publishing were skipped.
- The failing assertion remains in the inherited QA-owned tests/controllers.sh contract fixture. The current main register/poll producer does not supply the positive response_sig required by that legacy presence assertion. No signature was fabricated and no firmware authentication/default-deny behavior was weakened.

## Coordination and outstanding gates

- PR #327 remains OPEN / DRAFT / UNMERGED, child of #326. No merge, rebase, force-push or cross-role source modification occurred.
- PHX-QA owns the poll-signature fixture and independent same-SHA review. Request QA to replace the obsolete positive-presence assertion with source-exact negative/default-deny tests and independently review the shared extractor change.
- PHX-MASTER owns stack sequencing and coordination docs. Current ROLE_ASSIGNMENTS.md blob `fe20ddb48b856f068beffc88253a4a48db6ed974` lists hardware PRs #317–#324 but omits the active #326/#327 stack; the table needs a Master-owned refresh. Root README.md still contains old `BlazingSystems` organization links although the repository owner is `BlazeDevStudio`.
- Current parallel heads were revalidated: #239 `d83b715b116185107737fef721c2eece8feebf39`; #254 `4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84`; #283 `830c355376380f9b5533d5cda2558beed41a593a`; Master #288 `edfbcc3ef13f9afce37eb7d7bc453179329966b5`; Release #291 `af144e2c44c2a66959dd0ce088694c08ab415639`; parent #326 `58c558fb6a237935214621adc3dee65a10fe1a51`; current #327 docs HEAD `98b7da66b003d26ddd470929ae793cfe3c9fdd1f`.
- #283's original unconditional clear-after-failed-append path appears guarded in its current source, but quarantinePending() has no active callsite and the register/poll response_sig contract remains absent/unapproved. Keep #283 separate and deny-only.
- Issues #31/#32 financial crash atomicity and replay remain open. Issue #43's independent witness remains unresolved. Issue #34's physical power-cut/soak/electrical acceptance remains open. No migration or witness provisioning was attempted.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not read or modified. The Library search found older registry v7 snapshots only; the available tool set exposed no Google Drive connector. The 2026-11-09 checkpoint identifies the canonical v11 Drive ID as 1ZtHT5ZprK2gX-zlZWwdyAf2Ki6ylgpkm, but no Drive bytes were available in this activation.

## Readiness

SIMULATED / CI VERIFIED only. HARDWARE ACCEPTED is NOT ESTABLISHED. The 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback witness, durable accounting/replay, financial migration and independent QA/release signoff remain NOT TESTED or BLOCKED. PRODUCTION NO-GO.

No Codex, physical flashing, device reset, live money, production migration, signer provisioning, merge, release tag or deployment occurred.

## Next exact actions

1. PHX-QA: independently review exact source/test SHA 19166d46be2f8a61db69901d7c62d63106644c04 and correct the QA-owned poll-signature assertion without adding a positive unauthenticated response.
2. PHX-MASTER: reconcile the #326/#327 stack and refresh the stale live hardware PR table and old organization links.
3. PHX-HARDWARE: on the next activation, reload all branch heads and review responses; coordinate with MASTER before applying the shared extractor to any remaining parallel #283 labs.


## UTC12 follow-on — raw strings and phase-2 comment-splice coverage

The shared lexical helper already handled C++ raw strings and translation-phase-2 backslash-newline comment delimiters, but the first consolidation fixture only covered ordinary strings/comments and ISR attribute ordering. This follow-on adds explicit source-extraction assertions without changing firmware runtime behavior.

- Source/test commit: [7db41068f9471565471982030f4c119880908291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7db41068f9471565471982030f4c119880908291).
- Changed file: \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py\` only.
- The fixture covers a \`u8R"tag(... )tag"\` raw string containing braces/comment tokens, an escaped ordinary string, a character literal, a split \`//\` opener, a continued line comment, and a split \`*/\` terminator. It also checks the mask preserves source length/newline positions and proves a naive raw-brace counter truncates this fixture.
- Initial fixture-construction commit [876c5bacc421b6c2d728b662c95b26d32bf71dde](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/876c5bacc421b6c2d728b662c95b26d32bf71dde) encoded literal backslash-n sequences instead of physical newlines. Focused quarantine [#44521252075](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521252075), job 135550141073, and relay/output [#44521251887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521251887), job 135550140995, failed at the new fixture with \`unbalanced C/C++ block\`. This was a test-fixture construction error, not a firmware or helper regression.
- Corrected in [7db41068](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7db41068f9471565471982030f4c119880908291), using actual backslash-newline pairs in the Python-built C++ probe.

### Exact-source CI at 7db41068

Focused quarantine/readback:
- Push [#44521440358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521440358), job 135550773174: SUCCESS.
- PR [#44521451085](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521451085), job 135550810376: SUCCESS.
- Logs include \`SHARED_EXTRACTOR_RAW_STRING_PHASE2_PASS\`, \`SHARED_EXTRACTOR_ISR_ATTRIBUTE_ORDER_PASS\`, \`ESP8266_COIN_PULSE_CAPTURE_PASS 11/11\`, \`ESP32_COIN_PULSE_CAPTURE_PASS 11/11\`, \`POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS\`, and both boards' poll-window, persistence and mutation checks.

Relay/output:
- PR [#44521450941](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521450941): ESP32 boot-polarity job 135550809272 SUCCESS; source-output/poll-inhibit job 135550809709 SUCCESS.

Full build:
- Push [#44521440354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521440354), validation job 135550925556: FAILURE.
- PR [#44521450962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44521450962), validation job 135550963831: FAILURE.
- Both exact-head Full runs completed all 13 firmware/platform target jobs and Android successfully. Validation fails in the inherited QA-owned \`tests/controllers.sh\` assertion: \`Missing poll signature check\`. Update bundle, simulations, signing handoff, candidate gate and publishing were skipped. No positive unauthenticated response signature was added.

No firmware sketch, API, journal schema, financial path, GPIO, relay policy, release workflow or production state changed in this follow-on.



## UTC13 follow-on — execute ESP8266 cold-boot polarity lab in quarantine CI

The source-exact `esp8266_boot_polarity_lab.py` already existed on this hardware branch, but the quarantine workflow did not invoke it. The lab therefore could pass when run manually while the standard hardware quarantine check silently omitted the ESP8266 boot-polarity/migration gate. This activation added a workflow-wiring regression guard and made the workflow execute the existing lab.

No firmware sketch, runtime GPIO behavior, config layout, wire/API contract, finance path, journal schema, or production state changed. The ESP8266 lab continues to classify itself as host-only: it does not establish physical relay polarity or power-cut safety.

### Test-first and correction

- Guard file commit [eb9520b](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/eb9520bfb6bc7eb1402c3b0ea84d2c4ce46f3db7): added `boot_polarity_workflow_wiring_lab.py`. It requires the guard and boot-polarity lab to be invoked exactly once, preserves fail-fast execution, and checks the SIMULATED / physical-not-certified / financial-not-authorized markers.
- Expected RED commit [984ea8f](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/984ea8ff65a93b7da6e22fc2e1943acaf56100ca): wired the guard before adding the boot-polarity invocation. PR run [#44530905721](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44530905721), job `135583633175`, failed exactly at `ESP8266 boot-polarity lab must be invoked exactly once`. Earlier quarantine labs completed successfully; fail-fast correctly skipped later steps.
- Fix commit [dc26466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dc264660942612d577e9eef4e2f6536bb4671bd1): added a dedicated workflow step to run `esp8266_boot_polarity_lab.py` on the exact checked-out PR head.

### Exact-head GREEN evidence

- Quarantine PR [#44531136592](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136592), job `135584442602`: **SUCCESS**. Logs confirm `ESP8266_BOOT_POLARITY_WORKFLOW_WIRING=PASS`, `ESP8266_BOOT_POLARITY_LAB=PASS`, `ESP8266_BOOT_POLARITY_CONFIG_V3=PASS`, `V1_V2_MIGRATION_REMAINS_UNCONFIGURED=PASS`, `UNKNOWN_POLARITY_OUTPUTS_REMAIN_INPUT=PASS`, and `ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_PRELOAD=PASS`. The workflow also emitted `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.
- Relay/output PR [#44531136572](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136572): **SUCCESS**. ESP32 boot-polarity job `135584442131` and source-output-polarity job `135584442633` both passed.
- Full BlazePwifi PR [#44531136753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136753): **COMPLETED FAILURE** at validation job `135584596753`, exact inherited QA-owned assertion `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware/platform target jobs and Android completed **SUCCESS**. Simulation, update bundle, signing handoff, candidate gate and publishing remained skipped. This is not Full CI acceptance.

### Exact refs and disposition

- PR #327 remains OPEN / DRAFT / UNMERGED; current test/workflow source SHA `dc264660942612d577e9eef4e2f6536bb4671bd1`; parent #326/base `58c558fb6a237935214621adc3dee65a10fe1a51`.
- Existing ESP8266 and ESP32 firmware source blobs were unchanged in this follow-on: `aa021588b610f928f7af4f5fefb3f32114e6b5ae` and `528187f68aaad7d76a690bbf1cbe338165ad3839`.
- PHX-QA owns the stale poll-signature assertion and independent review. No positive unauthenticated signature was added.
- Physical relay polarity, electrical pulse/recovery, 150 power cuts, 30-device/24-hour soak, protected witness, financial migration, durable accounting/replay, and independent release acceptance remain NOT TESTED / NOT ESTABLISHED. PRODUCTION NO-GO.


## UTC13 follow-on — wire ESP8266 config-read failure lab into quarantine CI

### Audit finding

The exact PR #327 tree at `ebc387a0e6d0770d93829c0961b0d85d53198563` contained the hardware-owned `config_load_read_failure_lab.py`, but a scan of all 32 workflow YAML blobs in that exact tree found **zero invocations** of the lab. The three PHX-HARDWARE workflows and the main BlazePwifi build workflow did not run it. The source-extracted lab therefore existed but its EEPROM full-image read-failure and local config-recovery assertions were not part of CI.

The lab uses the production ESP8266 `loadCfg` / EEPROM functions with a deterministic fake-flash model of ESP8266 Arduino core 3.1.2. It covers full-image read failure, malformed V1/V2 and unknown config records, setup-save denial, local V1/V2-to-V3 config migration, poll-fault marker preservation, and failed migration commit followed by cold-boot retry. **This is local firmware-config migration only; it is not the financial v1-to-v2 ledger migration.**

### Test-first and correction

- Guard commit [054651f](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/054651f8754e9404569d0a2eba9e5c9f1ad127e6) extended `boot_polarity_workflow_wiring_lab.py` to require the config-read failure command exactly once and not commented out.
- Expected RED: quarantine push [#44534284422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44534284422), job `135595482328`, completed **FAILURE** exactly at `ESP8266 config-read failure lab must be invoked exactly once`. The preceding quarantine, pending-write, coin POST, poll-window, digest, mbedTLS and NVS labs passed before the fail-fast guard stopped the job.
- Workflow fix commit [ef541fc](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ef541fc5a37296f9c39a7b5351e87c54db098f6e) added a separate, named step: `Verify ESP8266 EEPROM config-read failure and local config migration recovery`.
- Exact-head GREEN: quarantine push [#44534458661](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44534458661), job `135596083262`, exact checked-out SHA `ef541fc5a37296f9c39a7b5351e87c54db098f6e`: **SUCCESS**. The wiring guard emitted `ESP8266_CONFIG_READ_FAILURE_WORKFLOW_WIRING=PASS`; the dedicated lab step completed SUCCESS and emitted:
  - `VALID_V3_IMAGE_READ_FAILURE_PRESERVE_COLD_BOOT_PASS`
  - `ESP8266_EEPROM_BEGIN_READ_FAIL_THEN_FULL_READ_RECOVER_MARKER_PRESERVED_PASS`
  - `ESP8266_EEPROM_RECOVERED_IMAGE_COLD_BOOT_DENY_PASS`
  - `ESP8266_EEPROM_FULL_READ_FAIL_MARKER_ONLY_RECOVERY_NO_COMMIT_PASS`
  - `ESP8266_EEPROM_FULL_READ_PERSISTENT_FAILURE_NO_COMMIT_PASS`
  - `MALFORMED_V1_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
  - `MALFORMED_V2_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
  - `UNKNOWN_SCHEMA_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
  - `VALID_V1_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS`
  - `VALID_V2_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS`
  - `V2_MIGRATION_COMMIT_FAILURE_SAME_BOOT_DENY_COLD_BOOT_RETRY_PASS`
- The same exact-head run also passed the pulse-capture and ESP8266 boot-polarity steps. Final markers explicitly state `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

### Full-build boundary and current refs

- Full BlazePwifi push [#44534284363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44534284363) was on the preceding test-only commit `054651f8754e9404569d0a2eba9e5c9f1ad127e6`. Validation job `135595483156` failed at the inherited QA-owned `tests/controllers.sh` assertion `Missing poll signature check`; all 13 firmware/platform target jobs and Android completed SUCCESS. Downstream simulation, update bundle, signing, candidate gate and publishing jobs were skipped. This is not a Full CI pass and is not an exact Full run on the later workflow-only head.
- Current PR #327: `phoenix/hardware-prepoll-edge-abort-20261119@` + `ef541fc5a37296f9c39a7b5351e87c54db098f6e`; parent #326/base `58c558fb6a237935214621adc3dee65a10fe1a51`. PR remains OPEN / DRAFT / UNMERGED.
- Workflow blob: `8b34f4905a1c8ce639ef47c9a1981291d20474b8`; wiring guard blob: `a0fd9c217e7b58242b6195c42ad531c418cf5849`; config lab blob: `a669da02e66220cdf68245aeadf47b74bda25e51`.
- No firmware sketch, GPIO, relay, financial schema, API, pending-journal format or production behavior changed. All test evidence is host-simulated/CI only. Physical EEPROM behavior, power-cut durability, financial migration, witness, coin acceptance and production remain NOT TESTED / NOT ESTABLISHED.

**Next exact action:** PHX-QA independently review the config-read lab at exact workflow head `ef541fc5a37296f9c39a7b5351e87c54db098f6e`; PHX-MASTER refresh the #327 pin in `coordination/phoenix/ROLE_ASSIGNMENTS.md`: the current #288 snapshot does include #327 but still records the older `e90c51d733635a891e0f1a8cd875586b43998069` head; then PHX-HARDWARE revalidates the branch and reviewer responses before selecting another owned task.


## UTC17 — keep ISR-reconciliation mutation compile-clean

**Role:** PHX-HARDWARE  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Exact source/test commit:** `ad421e48b2908fab48dc85b40c169450d9c0239c`  
**Test file blob:** `b3bb627005ca106f51529ff3750253d90f0b20c8`

### Defect reproduced at prior test head

At `3ff2745707ba40760a40e557c608b03aab6c92c3`, the `missing-isr-edge-reconciliation` mutation replaced the production condition with `if(false){`. That removed the only syntactic use of `sampledSingleEdge`, so the host C++ harness stopped at `-Werror=unused-variable` instead of reaching the intended runtime negative assertion. This was a regression in the test mutation, not a firmware runtime defect.

- Quarantine push [#44572189080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44572189080), job `135729991897`: **FAIL** at the ESP8266 mutation compile, `sampledSingleEdge` unused.
- Relay/output PR [#44572189120](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44572189120), job `135729992527`: **FAIL** at the same host-lab compile error.

### Correction

The mutation now substitutes `if(false && !sampledSingleEdge){`. This keeps the variable referenced for strict compilation while deliberately bypassing ISR-edge reconciliation. The lab must then fail at its expected runtime assertion, `late coin POST pulse was not fail-closed`. A source comment explains why the variable must remain referenced.

Only `coin_pulse_capture_lab.py` changed. No ESP32/ESP8266 runtime sketch, ISR, debounce policy, relay, journal, persistence schema, poll API, coin admission, finance path or shared interface changed.

### Exact-head evidence

On exact source/test SHA `ad421e48b2908fab48dc85b40c169450d9c0239c`:

- Quarantine push [#44573673364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44573673364), job `135735257163`: **SUCCESS**.
- Quarantine PR [#44573689545](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44573689545), job `135735309681`: **SUCCESS**.
- Relay/output PR [#44573689526](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44573689526): ESP32 boot-polarity job `135735309850` and source-output-polarity job `135735310432`: **SUCCESS**.
- Logs show `ESP8266_COIN_PULSE_CAPTURE_PASS 15/15` and `ESP32_COIN_PULSE_CAPTURE_PASS 15/15`; both boards reject `inclusive-debounce` and `missing-isr-edge-reconciliation` mutations. The blocking-poll fault lab passes 7/7 scenarios on both boards. Output/polarity and EEPROM config-read recovery steps also pass.
- Full push [#44573673614](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44573673614): validation job `135735258677` **FAILED** at the QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 13 firmware/platform target jobs and Android completed **SUCCESS**; simulation, update-bundle, signing, candidate-gate and publishing jobs were skipped. This is not Full CI acceptance.
- Full PR [#44573689537](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44573689537): validation job `135735311027` failed at the same QA-owned assertion; remaining matrix jobs were still running at this handover update.

All hardware evidence remains **SIMULATED / CI VERIFIED only**. Physical coin acceptor, relay under load, electrical pulse conditioning, power cuts, independent witness, financial migration, durable accounting/replay, and production acceptance remain NOT TESTED / NOT ESTABLISHED. `PRODUCTION NO-GO`.

### Next exact action

PHX-QA owns the stale positive poll-signature fixture and must replace it with source-exact negative/default-deny checks after coordinating the producer/consumer contract with CORE and MASTER. PHX-MASTER should reconcile the #326/#327 stack and refresh #327's exact head in the canonical role assignment. PHX-HARDWARE continues only with an owned, reversible firmware/test task after another live-head check.
