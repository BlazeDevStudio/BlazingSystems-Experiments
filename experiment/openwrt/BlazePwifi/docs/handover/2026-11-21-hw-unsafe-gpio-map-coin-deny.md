# PHX-HARDWARE handover — unsafe GPIO map coin-ingress deny

Date: 2026-11-21 (UTC03)
Role: PHX-HARDWARE
Repository: `BlazeDevStudio/BlazingSystems-Experiments`
Branch: `phoenix/hardware-prepoll-edge-abort-20261119`
Draft PR: [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED
Base: PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`
Exact source/test head: `69a21b9ed6ebe490750f625e053b77166fc131df`

## Scope

Prevent coin ingress and dispatch while the persisted GPIO mapping is unsafe. This is a Hardware-owned firmware safety guard on both ESP8266 and ESP32; no shared API or other-role file was changed.

## Source changes

Implementation commit: `4e6142756704d8912bc4a08aed96d76a444d22c6`

Both sketches now:

- Treat a sampled coin line while `pinConfigSafe == false` as unresolved ingress, not as a new credit batch.
- Latch the poll fault, preserve the unresolved edge count, keep the pending state closed, apply outputs OFF, and attempt the existing secondary-store plus LittleFS fault-marker persistence path.
- Require `pinConfigSafe` in `canAttemptCoinPost()`, so an older pending record cannot be dispatched while the GPIO map remains unsafe.
- Preserve default-deny; no positive poll/register/coin response authorization was introduced.

The host labs add an unsafe-pin ingress case, an unsafe-pin pending-dispatch case, and fail-open mutations that remove each guard.

## Test-first and exact-SHA CI

RED: test-only commit `d700f99e6c101887c2e350e346bd645de5ed9600`; Quarantine push [#44857660388](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44857660388), job `136703526381`, rejected the new `unsafe-pin-sample` case before the firmware fix.

GREEN at exact source/test SHA `69a21b9ed6ebe490750f625e053b77166fc131df`:

- Quarantine push [#44858886123](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44858886123), job `136707417683`: PASS.
- Quarantine PR [#44858892181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44858892181), job `136707436341`: PASS.
- Relay/output PR [#44858892041](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44858892041), ESP32 boot-polarity job `136707435111` and source/output-polarity job `136707435427`: PASS.

Exact-head host evidence:

- 72/72 source-extracted scenarios PASS; explicitly simulated only.
- ESP8266 and ESP32 coin-pulse capture: 17/17 each.
- Pending-attempt marker: 29/29 per board.
- Coin POST gate: 11/11 per board.
- Board shared-safety parity: 22/22 functions byte-identical.
- Mutations `missing-unsafe-pin-sample-deny` and `missing-unsafe-pin-post-gate` rejected on both boards.
- The workflow explicitly records `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

Full build push [#44858886105](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44858886105): 14/14 firmware-target plus Android jobs PASS. Full validation job `136707417849` FAILS at `experiment/openwrt/BlazePwifi/tests/controllers.sh`: `Missing poll signature check`. Downstream simulations, signed-APK import, update bundle, signing handoff, candidate gate and publication were skipped. This is not a Full validation pass.

## Status and blockers

- Host simulation: SIMULATED.
- Focused source/target checks: CI VERIFIED.
- Physical electrical / relay / coin acceptance: NOT TESTED.
- HARDWARE ACCEPTED: NO.
- PRODUCTION READY: NO.

The controller register/poll response-signature contract remains unapproved and must be resolved by PHX-CORE with PHX-QA. Firmware does not invent `response_sig` or weaken the deny gate. Master must refresh the stale #327 pins in `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md`, and the #172 control-plane summary without retargeting the #322 → #323 → #326 → #327 stack.

Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the connected Library listing/search during this activation; older registry snapshots were not substituted.

## Next exact action

PHX-MASTER refreshes the canonical role/stack pins; PHX-CORE publishes the authenticated register/poll/coin receipt contract; PHX-QA validates it independently. PHX-HARDWARE then re-reads all live heads and continues with the next unblocked firmware-owned task. No flashing, device reset, live money, production migration, signing, release, or deployment is authorized by this handover.
