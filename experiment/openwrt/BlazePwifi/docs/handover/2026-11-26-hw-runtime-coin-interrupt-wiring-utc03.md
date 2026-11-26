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
