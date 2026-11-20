# PHX-HARDWARE — poll-drain active-line / missing-ISR reconciliation

**Date:** 2026-11-20 UTC03  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326, `phoenix/hardware-pending-write-fault-latch-20261119`, `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source implementation commit:** `369007bcbc684a0923a586e991f3aa0667cda105`  
**Exact focused source/test head:** `242e5a2b72b12030324058a58430e04900e0bbb1`

## Finding

When `beginPollWindow()` had already inhibited intake and `coinLineQuietAfterInhibit()` observed an active coin input, it returned false. If the ISR sequence had not advanced, the loop's abort branch could release `pollIntakeSuspended` before the ordinary GPIO sample ran. That created a source-level window where the relay/LED could be re-enabled while the input line was still active, or where an observed pulse that disappeared before sampling could be silently lost.

The correction preserves the existing normal pulse-capture path. A GPIO-observed pulse without an ISR delta is not automatically rejected if the ordinary sample can durably queue it; however, the inhibit remains asserted until the input is idle. If the pulse disappears before the ordinary sample can create a pending journal entry, the firmware records an unresolved-ingress fault and remains deny-only.

## Firmware change

Applied identically to the ESP8266 and ESP32 sketches:

- Added `pollDrainAbortedOnActiveLine` state, set by the quiet-drain helper when it observes an active line.
- Added the small `handlePollDrainAbortAfterSample()` reconciliation helper and call it only after ordinary pulse sampling and pulse-group readiness processing.
- Keep `pollIntakeSuspended` asserted while a sampled pulse remains active.
- Release the temporary inhibit only after the line is idle and a pending event exists.
- If the drain observed a pulse but the ordinary sample produced no pending event, latch the existing persistent `COIN_INGRESS_UNRESOLVED` deny marker before any output release.
- If another fault is already latched, clear only the temporary drain flag; the existing journal-recovery deny continues to hold outputs OFF.

No register/poll response contract, positive `response_sig` acceptance, financial state, receipt schema, CORE API, COE destination, pin mapping, debounce constant, relay polarity, or persistence layout was changed.

## Test-first and exact-head evidence

A no-ISR active-line regression was added before the final reconciliation helper. The intermediate source failed the new active-line capture/hold assertion (expected RED), proving the abort path did not preserve the required inhibit state.

At exact source/test head `242e5a2b72b12030324058a58430e04900e0bbb1`:

- Quarantine/readback push [run 44671025193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44671025193), job `136071746877`: **PASS**.
- Relay/output polarity [run 44671032112](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44671032112):
  - ESP32 boot-polarity job `136071767208`: **PASS**.
  - Source/output-polarity job `136071767486`: **PASS**.
- Exact log assertions include:
  - ESP8266 and ESP32 coin pulse capture: `15/15` each.
  - Poll blocked-edge fault scenarios: `8/8` each, plus existing poll-loop guards `7/7`.
  - Active-low and active-high no-ISR pulse capture remains inhibited until idle.
  - Pulse ending before sample fails closed with a persistent unresolved-ingress marker.
  - Mutation `release-while-active-drain-line` rejected on both boards.
  - Poll-window timeline guard passes.
  - Poll-response fail-closed: `11/11`; strict root JSON: `13/13`; coin POST ACK root-status: `4/4`; coin disposition remains default-deny.

All these are **source-extracted host simulations / CI evidence**, not physical coin-acceptor or relay tests. Workflow logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

## Full build / validation disposition

Full BlazePwifi build [run 44671025156](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44671025156), same exact head `242e5a2b72b12030324058a58430e04900e0bbb1`:

- ESP8266 job `136071847632`: PASS.
- ESP32 job `136071847938`: PASS.
- All 13 firmware/platform target build jobs: PASS.
- Android job `136071847990`: PASS.
- Validation job `136071847984`: **FAIL** at the inherited QA-owned `Missing poll signature check` assertion in the ESP8266 controller validation.
- Production import/sign, update bundle, emulator simulations, candidate gate, and publish/sign handoff remained skipped after validation failure.

Do not add a fabricated positive poll marker or `response_sig` to satisfy this fixture. PHX-QA owns the stale positive assertion/extractor correction; PHX-CORE must publish the authenticated register/poll and event-bound receipt contract before any positive disposition is enabled.

## Stack and coordination

- PR #327 is a child of #326; #326 is a child of #323; #323 is a child of #322. All remain open drafts. This is a separate candidate stack; no base/head was retargeted.
- The current Master `ROLE_ASSIGNMENTS.md` still lists #239, #254 and #283 as active Hardware PRs and does not yet register #323–#327. PHX-MASTER must reconcile the canonical stack/assignment list before any merge or integration decision.
- The owner-requested #239, #254 and parallel #283 candidates were revalidated and left untouched.
- Ownership routes confirm PHX-HARDWARE owns the ESP32 and ESP8266 firmware trees; no CORE, PISONET, QA, RELEASE, Master-coordination or COE source files were edited.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the exposed Drive connector surface. No older Library snapshot was substituted and no Drive storage mutation was attempted.

## Safety disposition

**CI VERIFIED:** source-extracted regression and focused hardware labs at the exact SHA above.  
**SIMULATED:** all pulse, ISR, line-state, persistence and mutation-injection cases.  
**NOT TESTED:** physical coin acceptor, relay/electrical pulse recovery, 150 power cuts, 30-device 24-hour soak.  
**HARDWARE ACCEPTED:** NO.  
**PRODUCTION READY:** NO — PRODUCTION NO-GO.

No physical flashing, device reset, live money, production migration, signing, release tagging, deployment, merge, or force-push was performed.

## Next exact actions

1. **PHX-QA:** repair the inherited positive poll-signature fixture using source-exact default-deny assertions; rerun Full validation at a newly revalidated exact head.
2. **PHX-MASTER:** reconcile #322–#327 stack ancestry and update the canonical Hardware active-PR assignment without merging or silently composing branches.
3. **PHX-CORE:** publish the authenticated register/poll and event-bound receipt contract.
4. **PHX-HARDWARE:** preserve this fail-closed pulse reconciliation and revalidate the exact source/test head after Master/QA coordination; do not enable positive coin admission.

