# PHX-HARDWARE UTC19 — startup register fail-closed guard coverage

**Role:** PHX-HARDWARE  
**Task:** hardware #177 / cleanup-first #266 / existing stacked DRAFT PR #355  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05@fc842342596786e072630179acfbbc4feeb2ba02`  
**Starting branch HEAD:** `57b69a4bff7fd15f93c5ba2e0de7d367ff2bdec5`  
**Starting source/test SHA:** `e21f5e70695f3fdd6ee349e385fda69210034826`  
**Status:** IN_PROGRESS · deny-only · SIMULATED/CI only · HARDWARE NOT TESTED · PRODUCTION NO-GO.

## Selected bounded task

The current poll lab proves the 3.5-second poll request is surrounded by unconditional deny calls and that its response is discarded. The two sketches also perform a synchronous startup `post("register")` from `connectSta()`. At current source, `setup()` denies outputs before calling `connectSta()`, the register response is explicitly discarded, and `connectSta()` denies again after registration. These startup invariants are not currently covered by the poll-preflight lab.

Add source-extracted, mutation-tested assertions for those existing startup invariants on both ESP8266 and ESP32. This is a Hardware-owned test/lab change only; it does not change production sketches, API/schema, QA-owned assertions, CORE financial logic, signing, witness or destination migration.

## Planned scope

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_contract.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab_cases.py`
- This narrow handover only.

The existing focused workflow already watches both lab modules; verify this against the live branch before relying on it.

## Planned negative mutations

- Remove or conditionally nest the startup `denyRemoteControl()` before `connectSta()`.
- Remove or conditionally nest the post-register deny.
- Consume the register response or call `applyRemoteConfig` before the approved authenticated contract.
- Add a second register POST outside the bounded startup function.

Expected: both board suites reject every mutation while the unmodified source passes. The existing poll-deny, output polarity, pending preservation, and Mbed TLS evidence remain separate.

## Evidence boundary

All source-extracted host checks are SIMULATED / CI VERIFIED only. Real GPIO/relay polarity, electrical pulse behavior, LittleFS power-loss, 150 physical power cuts, and 30-device/24-hour soak remain NOT TESTED. No merge, flash, reset, live money, signer, migration, release or deployment is authorized.

## Next exact action

Implement the register-startup source contract and mutation cases, run the exact focused workflow on the resulting PR head, inspect the Full workflow's exact-head result, then update this handover and the existing #355 PR description. Keep #355 DRAFT and preserve the deny-only parent stack.

**Updated UTC:** 2026-11-26T19:10:38Z
