# PHX-HARDWARE handover — shared lexical source extraction

**Date:** 2026-11-19 UTC11  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hardware-prepoll-edge-abort-20261119  
**Parent/base:** PR #326 at 58c558fb6a237935214621adc3dee65a10fe1a51  
**Exact source/test commit:** 19166d46be2f8a61db69901d7c62d63106644c04  
**Disposition:** focused source-extracted CI VERIFIED; Full validation FAILED at inherited QA-owned poll-signature assertion; physical acceptance NOT TESTED; PRODUCTION NO-GO.

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
- PHX-MASTER owns stack sequencing and coordination docs. The live PR/CI table in ROLE_ASSIGNMENTS.md is dated 2026-11-16 and still lists older hardware PR #314; the current #327 stack is acknowledged in the newer #172 UTC10 checkpoint but the table should be refreshed. Root README.md still contains old BlazingSystems organization links although the repository owner is BlazeDevStudio.
- Current parallel heads were revalidated: #239 d83b715b116185107737fef721c2eece8feebf39; #254 4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84; #283 830c355376380f9b5533d5cda2558beed41a593a; Master #288 9a7a8f855913e6a74cdead136631a1b317a62eb1; Release #291 1ec8dde1b188be310b5daf38d21c26ed812b0361.
- #283's original unconditional clear-after-failed-append path appears guarded in its current source, but quarantinePending() has no active callsite and the register/poll response_sig contract remains absent/unapproved. Keep #283 separate and deny-only.
- Issues #31/#32 financial crash atomicity and replay remain open. Issue #43's independent witness remains unresolved. Issue #34's physical power-cut/soak/electrical acceptance remains open. No migration or witness provisioning was attempted.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not read or modified. The Library search found older registry v7 snapshots only; the available tool set exposed no Google Drive connector. The 2026-11-09 checkpoint identifies the canonical v11 Drive ID as 1ZtHT5ZprK2gX-zlZWwdyAf2Ki6ylgpkm, but no Drive bytes were available in this activation.

## Readiness

SIMULATED / CI VERIFIED only. HARDWARE ACCEPTED is NOT ESTABLISHED. The 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback witness, durable accounting/replay, financial migration and independent QA/release signoff remain NOT TESTED or BLOCKED. PRODUCTION NO-GO.

No Codex, physical flashing, device reset, live money, production migration, signer provisioning, merge, release tag or deployment occurred.

## Next exact actions

1. PHX-QA: independently review exact source/test SHA 19166d46be2f8a61db69901d7c62d63106644c04 and correct the QA-owned poll-signature assertion without adding a positive unauthenticated response.
2. PHX-MASTER: reconcile the #326/#327 stack and refresh the stale live hardware PR table and old organization links.
3. PHX-HARDWARE: on the next activation, reload all branch heads and review responses before selecting the next owned task.
