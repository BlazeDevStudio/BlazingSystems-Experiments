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
