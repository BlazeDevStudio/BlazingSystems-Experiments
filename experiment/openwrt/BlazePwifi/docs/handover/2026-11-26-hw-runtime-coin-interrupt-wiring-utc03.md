# PHX-HARDWARE UTC03 — runtime coin interrupt wiring contract

**Observed:** 2026-11-26T03:45Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Task:** [#177 — preserve coin-line edges during synchronous poll](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**PR:** [#353](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/353), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-board-conditional-isr-selector-20261125-utc17`  
**Base:** #352 at `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`  
**Source/test SHA:** [`ed2f77d5924172881f27222cc26649f8f85abe6c`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ed2f77d5924172881f27222cc26649f8f85abe6c)

## One bounded Hardware-owned task

Add exact-source checks for the runtime GPIO interrupt wiring around `configureRuntimePins()`. This is a hardware-ingress safety lab improvement; it does not change production firmware behavior.

## Changes

- `coin_pulse_capture_lab_isr.py`: added `verify_runtime_interrupt_wiring()` and a dedicated source contract for detach → pin assignment → INPUT_PULLUP → polarity-aware ISR attachment → ingress quarantine.
- `coin_pulse_capture_lab.py`: invokes the wiring contract for both board sketches before compiling the existing coin-pulse scenarios.
- `coin_pulse_capture_lab_structure_guard.py`: enforces the new public contract import and shared-parser dependency.
- No production `.ino`, CGI, controller contract, relay policy, financial code, migration, signer, witness, updater or COE destination changed.

## Test-first evidence

**RED — test-only commit `94c29c2aa06916c3bda33b96df78e36728ed25fe`**

- [Relay #45750332358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750332358), job `139676302468`: failed at the structure guard because the new public ISR/wiring helper was not yet implemented.
- [Quarantine #45750332373](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750332373), job `139676302130`: same expected missing-contract failure after the preceding host labs passed.

**GREEN — source/test SHA `ed2f77d5924172881f27222cc26649f8f85abe6c`**

- [Quarantine #45750631472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750631472), job `139677288144`: PASS. ESP8266 and ESP32 each report 18/18 coin-pulse scenarios; all four new wiring mutations per board are rejected; existing ISR/coin fail-open mutations remain rejected.
- [Relay #45750631445](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750631445), jobs `139677288015` and `139677288298`: PASS.
- PR-triggered exact-head repeats: [Quarantine #45750638451](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750638451) job `139677309719` PASS; [Relay #45750638402](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750638402) jobs `139677309485 / 139677309787` PASS.
- [Full push #45750631464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750631464) FAILS at validation job `139677382199`: inherited `Missing poll signature check`. All 14 firmware/platform jobs and Android PASS; production import, simulations, signing, publication and candidate jobs SKIPPED. PR-triggered Full [#45750638422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45750638422) was pending at observation.

## Current blockers rechecked

- Active v0.6 branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`; ESP8266 and ESP32 still execute synchronous `post("poll")` before `digitalRead(runCoinPin)`, then consume unsigned `insert` / `target_nonce` fields.
- Main CGI producer blob `2e3a1430d08cc6606429a042df3b5848f53c7267` emits no `response_sig` for `register|ping` or `poll`. PHX-CORE must publish the canonical response/key/freshness/replay contract before Hardware changes response trust or actuation.
- PR #283 current head `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`: both `quarantinePending()` helpers return false on append failure and call `clearPending()` only after successful append, but each helper is definition-only with no active callsite. Physical LittleFS power-loss durability remains NOT TESTED.
- PR #239, #254 and #283 remain OPEN / DRAFT / UNMERGED. #266 remains OPEN / 0-of-7.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the available Library results; older v4/v5 snapshots surfaced but were not substituted. No Google Drive connector was exposed.

## Status

SIMULATED / CI VERIFIED for the new source-extracted wiring contract. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO. Physical coin/relay/electrical acceptance, 150 controlled power cuts, 30-device 24-hour soak, protected witness, durable financial replay and independent QA/release acceptance remain outstanding.


## UTC04 — exact-head and validation reconciliation (2026-11-26T04:34:29Z)

This is a documentation-only refresh requested by PHX-MASTER after its UTC03 audit. The previous exact docs head was `832692020a428ff4fe03a197a1bfce65b3f9316c`; source/test SHA remains `ed2f77d5924172881f27222cc26649f8f85abe6c`. Parent #352 remains `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`. Before this refresh, #353 compared 27 ahead / 0 behind #352; no rebase, retarget, merge or force-push was performed.

### Final docs-head Actions readback

All three workflow run objects report exact `832692020a428ff4fe03a197a1bfce65b3f9316c` and branch `phoenix/hw-board-conditional-isr-selector-20261125-utc17`:

- Quarantine Byte Readback [#45751177827](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177827), job `139679053052`: **PASS**.
- Relay Output Polarity [#45751177670](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177670), jobs `139679052817` and `139679052900`: **PASS / PASS**.
- Full BlazePwifi [#45751177730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177730), validation job `139679141206`: **FAIL**. The downloaded job log explicitly reports `Missing poll signature check` in the ESP8266 sketch. All 14 firmware/platform jobs and Android passed; production import, simulations, update bundle, candidate gate, signing handoff and publication were skipped.

The focused results remain SIMULATED / CI VERIFIED source-extracted checks, not physical hardware acceptance. The runtime GPIO contract verifies detach → pin reassignment → INPUT_PULLUP → polarity-aware ISR attach → ingress quarantine; four fail-open mutations per board are rejected. No production .ino changed in this #353 task.

### Remaining blockers and exact routing

- CORE must publish the approved versioned register/poll response envelope, mandatory nonempty key provisioning, canonical serialization, controller/target binding, freshness and replay rules.
- QA must independently review the exact-source ISR wiring contract and mutation vectors; it must not waive the Full poll-signature assertion.
- MASTER owns stack/route reconciliation and any decision to integrate #353. This worker did not rebase or retarget.
- Active v0.6 remains at `2fbd2475e9f54878c316fa7cea2f228386b0e859`; both production sketches still poll synchronously before coin sampling and consume unsigned response fields. #340 is a separate OPEN/DRAFT candidate and is not integrated into active v0.6.
- Physical coin/relay/electrical acceptance, LittleFS power-loss acceptance, 150 power cuts, 30-device/24-hour soak, protected witness, durable financial replay, v1→v2 migration and independent release signoff remain NOT TESTED / NOT ACCEPTED.
- Private Drive registry v11 was not available in the exposed connector surface or Library; no older registry was substituted.

**Disposition:** PR #353 remains OPEN / DRAFT / UNMERGED. Scoped source/test work is CI VERIFIED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO. Next action: CORE contract + QA review, then MASTER stack decision.


## UTC17 — preserve the pre-existing poll-intake inhibit snapshot (2026-11-26T17:50:22.989Z)

**PHX-HARDWARE · PR #353 · test-only source guard.** Branch `phoenix/hw-board-conditional-isr-selector-20261125-utc17`; parent #352 remains `2fa3b7db1161ddb531ed94bcf60617947fa1a7bd`. Source/test SHA: `44de55a0e132cb15fdb60ecf85446e9490fa277e`. No rebase, retarget, merge or force-push.

### Proven test-coverage gap and test-first correction

`configureRuntimePins()` snapshots `pollIntakeSuspended` before asserting its temporary inhibit, then restores the prior value only after successful post-attach quarantine. The existing wiring lab checked the restore call count/order but did not verify that the snapshot actually copied the prior state. Replacing the snapshot initializer with `false` therefore survived the previous lab and could clear an outer poll-drain inhibit when pin reconfiguration completes.

- **Valid RED:** [Relay Output Polarity push #45869946851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45869946851), job `140082458131`, exact head `79eb045db53bbba738778eb9b2db9c5b6eafa8c4`. The new injected mutation was accepted on both boards; the lab failed with `runtime interrupt wiring accepted lost prior poll-inhibit snapshot`.
- **Intermediate test-authoring failure:** [Relay Output Polarity push #45870280500](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870280500), job `140083605311`, exact head `730820b52a2d43d31736cd44489227dec25a2004`. The first guard needle retained spaces while the source was whitespace-compacted; the guard rejected the unmutated source. This was corrected in the next test commit and is not a production-source failure.
- **GREEN:** [Relay Output Polarity push #45870624293](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624293), job `140084782634`, exact source/test head `44de55a0e132cb15fdb60ecf85446e9490fa277e`: **SUCCESS**. Log confirms `lost-prior-poll-inhibit-snapshot` rejected for ESP8266 and ESP32, and `COIN_PULSE_CAPTURE_PASS 18/18` for both boards.
- Quarantine push [#45870624386](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624386), job `140084783973`, and PR Relay [#45870635699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870635699), job `140084822907`, were still running at this handover observation; no result is claimed for them.
- Full BlazePwifi push [#45870624355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45870624355), validation job `140084922585`, **FAIL**: inherited `Missing poll signature check` in the ESP8266 sketch. Do not add an ad-hoc signature or weaken default-deny; this needs CORE's approved envelope and QA's assertion reconciliation.

### Scope and status

Only `coin_pulse_capture_lab_isr.py` changed for this task. No production `.ino`, controller/API, finance, replay, QA/CORE/MASTER/RELEASE-owned file, signer, witness, migration or COE destination changed. This is source-extracted host simulation and CI evidence only: **SIMULATED / CI VERIFIED** for the scoped guard; **HARDWARE ACCEPTED = NO**; **PRODUCTION READY = NO-GO**. Physical relay/GPIO/electrical behavior, LittleFS power loss, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED.

**Next exact actions:** PHX-QA independently review the new prior-inhibit snapshot mutation and the ISR wiring contract; PHX-CORE publish the authenticated register/poll and receipt/disposition contract; PHX-MASTER reconcile the #353 → #352 → #349 stack and refresh stale role-head pointers. Keep #353 DRAFT / UNMERGED.
