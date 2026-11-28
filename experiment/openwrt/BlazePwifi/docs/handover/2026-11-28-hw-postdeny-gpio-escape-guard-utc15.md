# PHX-HARDWARE UTC15 — post-deny direct GPIO escape regression

**Task:** `PHX-HW-177-POSTDENY-GPIO-ESCAPE-20261128T15Z`  
**Issue:** [P0 #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Parent candidate:** [PR #377](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/377) at `95e54790ab986dab3c1b3723ea9603a3d125c0d6`  
**Branch:** `phoenix/hw-postdeny-gpio-escape-guard-20261128-utc15`  
**Updated:** 2026-11-28T15:36:06Z  
**Status:** IN PROGRESS; source/test CI not yet run.

## Scope and reason

The current deny-only poll lab exercises an untrusted positive response that briefly re-enables outputs before the normal post-poll deny. The additional case will inject a direct `writeLogical(runRelayPin, true, runRelayActiveHigh)` after the final deny and before `lastPoll`. This bypasses the ordinary `applyOutputs()` path and checks that the host GPIO write-history latch rejects a post-deny physical relay re-enable on both ESP8266-shaped and ESP32-shaped fixtures.

Only the Hardware-owned source-extracted test case file is to change. No production sketch or shared API is to change. No QA-owned test/assertion is to change.

## Planned verification

- Run the existing Poll Intake Deny workflow on the exact PR head.
- Require the new `POST_POLL_DENY_DIRECT_GPIO_REENABLE_MUTATION_REJECTED` marker for both boards.
- Record Native and Full outcomes separately; do not treat target compilation as overall validation.
- Preserve all failures and skipped release stages.

## Safety boundary

SIMULATED / CI only. Physical relay terminal polarity, actual acceptor inhibit, pulse retention, EEPROM/NVS brown-out, LittleFS power-loss, 150 power cuts, 30-device/24-hour soak and electrical recovery remain NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO. No flash, reset, live money, migration, signing, release, merge or deployment.


## Source/test commit and first exact-head CI readback — 2026-11-28T15:54:00Z

Source/test commit: `6c22c7ebef3eaa9082735511f4cf3e525731085c`. PR [#378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/378) OPEN / DRAFT / UNMERGED.

- Poll [#46161956366](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46161956366), job `141031014911`: **PASS** on the exact source/test SHA. Both ESP8266 and ESP32 fixtures emitted `POST_POLL_DENY_DIRECT_GPIO_REENABLE_MUTATION_REJECTED`; the existing five-outcome × four-polarity matrix passed, 8/8 board/polarity output scenarios passed, and 14/14 injected regressions were rejected.
- Mbed [#46161956391](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46161956391): source-contract job `141031015239` PASS; both target builds IN_PROGRESS at this read.
- Full [#46161956393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46161956393): validation job `141031061284` failed only at handover freshness because the source commit followed the IN PROGRESS checkpoint. This ordering failure is being corrected by this docs commit; target matrix was still running and no overall Full result is claimed.

The new test is host/source-extracted simulation only. No production sketch or shared API changed. Physical electrical and all #34 acceptance remain NOT TESTED; HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.
