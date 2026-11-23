# PHX-HARDWARE — quarantine append-failure preservation regression

**Date:** 2026-11-23 UTC11  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#345](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/345), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-intake-armed-gate-20261122-utc23`  
**Parent:** PR #343 at `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`  
**Source/test head:** `6aa139491cd87e9f7641e088c54aadcf5c9831dc`

## One bounded task

Added source-extracted failure-injection coverage for the existing `quarantinePending()` helper on ESP8266 and ESP32. The current production helper already returns before `clearPending()` when `appendQuarantineRecord(reason)` fails and sets `journalRecoveryRequired`; this change protects that behavior against regression. It does not claim a new firmware fix.

Changed only:

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_clear_failure_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

The lab now extracts the exact production `quarantinePending()` function from both sketches, includes it in the normalized ESP8266/ESP32 authority-parity set, and runs a FakeLittleFS/host-C++ adapter matrix:

1. Quarantine append failure: pending RAM identity, `/pending.dat`, and `/pending.attempt` remain; recovery-required latch is set.
2. Append-success control: the helper may clear pending only after the append succeeds.
3. Missing pending event: deny before append.
4. Mismatched attempt marker: deny before append.
5. Failure injection rejects three unsafe mutations: bypass append-failure guard (expected exit 110), omit recovery latch (110), and bypass matching attempt marker (113).
6. An ESP32-only `quarantinePending` drift mutation is rejected by the cross-board parity guard.

The test adapter does **not** model actual LittleFS serialization, flash wear, physical power loss, or durability. It is SIMULATED / CI VERIFIED only.

## CI evidence at exact source/test head

- Quarantine [run #45163252713](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45163252713), job `137653677198`: SUCCESS. Logs show all four baseline/control markers on both boards, the three expected-exit mutation rejections on both boards, and the ESP32 authority-parity mutation rejection.
- Relay/output [run #45163252737](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45163252737), jobs `137653677273` and `137653677727`: SUCCESS.
- Full integration [run #45163252730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45163252730), validation job `137653827040`: FAILURE at the inherited QA-owned `Missing poll signature check`. All 14/14 configured target/platform jobs and Android job `137653827092` completed SUCCESS; validation-dependent simulations, candidate, signing and publication stages were skipped.

## Correction transparency

Initial source/test commit `0a2a237e030a2a37f19b5dc8fa12f29ff6e809e9` encoded literal backslash-n separators in the generated host C++ source; its Quarantine run [#45163007008](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45163007008) and Relay run [#45163007278](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45163007278) failed at compilation. The fixture separators were corrected in `6aa139491cd87e9f7641e088c54aadcf5c9831dc`; the exact-head focused runs above passed. The initial failure was a test-harness construction error, not a firmware defect.

## Live ownership and blockers revalidated

- #239: `d83b715b116185107737fef721c2eece8feebf39`, OPEN / DRAFT.
- #254: `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, OPEN / DRAFT.
- #283: `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`, OPEN / DRAFT.
- #343: `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`, OPEN / DRAFT.
- #344: `3bfa530c94a929191d7b3335c085dbd7f99e1e18`, OPEN / DRAFT.
- Master PR #288: `8eb2475c9dbfa2f53d9f11786c3f3d7503cb7132`, OPEN / DRAFT.

Master `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` still list the earlier #327→#342→#343 firmware stack and #338→#339→#341→#344 host-lab stack, omitting this active #345 child. The Control Plane body records #345 at its prior head. Master-owned files were not edited; request a Master pin refresh.

#266 remains OPEN / 0-of-7 cleanup-first tracks. #177 remains OPEN. Financial/replay issues #31/#32, safety/physical acceptance #34, and witness #43 remain OPEN. The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not accessible through this run's Library/connector surface; no older checkpoint was substituted.

## Scope boundary

No production `.ino` sketch, shared protocol/API, CORE producer, QA-owned assertion, financial ledger, signer, witness, migration, Release workflow, or COE destination was changed. No live money, physical flash, reset, production migration, merge, tag, deployment, or cutover occurred.

**Classification:** SIMULATED + CI VERIFIED regression only; physical hardware acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION READY NO.

**Next exact action:** PHX-QA independently reviews the new append-failure regression and reconciles the stale poll-signature assertion against CORE's approved register/poll contract. PHX-MASTER refreshes the #345 exact-head assignment/integration pins. PHX-HARDWARE revalidates every live branch before the next bounded firmware task.
