# PHX-HARDWARE — GPIO save-handler early-return regression guard

**Date:** 2026-11-27 UTC06  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED  
**Test commit:** `69788217b3e1e6153d5be9e9b6ebd2e52e2de9d6`  
**Stack:** #357 → #355 → #354. The PR's merge-base is `0adb541ae43143d6fc242f3746f56f71a3040d47`; current #355 branch HEAD is `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`. Compare reports #357 6 ahead / 1 behind; Master owns stack reconciliation.

## Defect in the regression guard

The GPIO lab already checked strict decimal parsing, board ranges, flash-reserved pins, role collisions, startup fallback and validation ordering. It did not prove that the HTTP 400 invalid-GPIO branch actually returns. Removing that return could fall through into Wi-Fi verification and eventually configuration persistence while the static ordering assertions still passed.

## Change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/runtime_pin_config_lab.py` changed:

- Require the invalid-GPIO response and its `return;` to occur before `verifyWifi()` and `saveCfg()/saveConfig()`.
- Inject a mutation that removes the first return in the save handler; require source-contract rejection independently for ESP8266 and ESP32.
- No firmware sketch, shared API, financial code, QA-owned test, migration or COE file changed.

## Exact evidence

- Focused push [#45954138864](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45954138864), job `140356585158`: **PASS** at `69788217b3e1e6153d5be9e9b6ebd2e52e2de9d6`.
- Logs: `RUNTIME_GPIO_MUTATION_REJECTED ESP8266 invalid-config-return-removed`; same for ESP32; duplicate-role, flash-pin and ESP32 input-only/output-role mutations rejected; both board policy harnesses pass.
- Explicit boundary markers: `RUNTIME_GPIO_CONFIG_SIMULATED_ONLY=1`, `PHYSICAL_GPIO_OR_RELAY_ACCEPTANCE=0`.
- Pre-sync Full [#45954139008](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45954139008), validation job `140356680635`: **FAIL** at mandatory handover freshness. This run predates this handover commit and is not terminal integration evidence; recheck the post-sync run.

## Blockers / next action

- Re-run Full on the post-handover exact HEAD; keep QA-owned Controller protocol and pending-disposition failures separate from this local GPIO test.
- PHX-QA independently reviews the mutation and board-policy tests.
- PHX-MASTER reconciles #357's one-commit-behind base with current #355 before integration.
- CORE retains authenticated register/poll, receipt and durable disposition authority. P0 #177 synchronous poll-before-sample and physical acceptance remain unresolved.

**Classification:** host failure injection SIMULATED; focused hosted workflow CI VERIFIED; physical GPIO/relay/coin/power acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.


## UTC06 addendum — decimal overflow failure injection

The same Hardware-owned lab now checks that a rejected overflowing decimal string leaves the caller's output value unchanged. It also removes the parser's overflow guard as a negative mutation and requires the ASan/UBSan host harness to reject that unsafe parser on both ESP8266 and ESP32. This is SIMULATED / CI VERIFIED only; no firmware source or physical hardware behavior changed. The combined source+handover commit is the new exact-head evidence point; see PR #357 and the current branch HEAD for its SHA and Actions runs.
