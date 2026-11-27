# PHX-HARDWARE — PR #357 restack and terminal CI readback

**Date:** 2026-11-27 UTC07  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED  
**Restack commit:** `69ef1b4905a1adefdb74b69d701057d6d331540f`  
**Base PR #355 HEAD:** `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Compare:** 11 ahead / 0 behind; merge-base is current #355.

## Restack and preservation

The #357 branch was fast-forwarded without force-push using a two-parent merge commit: first parent is prior #357 head 79470fb6cfa1daf274c33d2100ad19eabd5b39fd; second parent is current #355 head 9f7a8ecb915cf199a82c0b4d37c56c40d722037b. #355 was not modified.

The tree preserves the full #355 tree, overlays only Hardware-owned #357 firmware, host-lab and workflow paths, retains the #357 UTC04/UTC06 narrow handovers, and adds this UTC07 handover. PROJECT_HANDOVER.md and CURRENT_STATE.md keep the current #355 content. CHANGE_LEDGER.md keeps the current #355 ledger as an exact byte prefix and appends the #357-only suffix; no existing ledger bytes were deleted or rewritten.

## Exact-head results at 69ef1b49

- Full BlazePwifi [#45958121607](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958121607): **FAILURE** — 15 success, 1 failure, 13 skipped. CI-0701 and handover freshness passed; sole validation failure was QA-owned Controller protocol parity. ESP8266, ESP32, Android and all 11 OpenWrt firmware target jobs passed. Signing/release/simulation jobs were skipped.
- Native synthetic journal [#45958121633](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958121633): **FAILURE** at PAY-0745 durable Vendo pending sequence and corruption contract; previous synthetic and installed read-only/deny gates passed.
- ESP32 Mbed TLS matrix [#45958121512](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958121512): **3/3 PASS**.
- Exact-source push [#45958114250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958114250): **PASS**.
- Exact-source PR [#45958121684](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45958121684): **PASS**.

## Source scope and safety

Both sketches validate decimal GPIO strings, board-specific ranges, flash-reserved pins and duplicate coin/relay/LED roles. Invalid persisted tuples fall back to board defaults; ESP32 stays station/poll-disabled until a valid saved tuple is available. Save handlers reject invalid GPIO assignments and return before Wi-Fi verification and persistence. Host failure injection covers duplicate roles, flash pins, nonnumeric/overflow input, ESP32 input-only outputs and missing early return.

These are host/source-extracted tests. No physical GPIO, relay, coin, electrical pulse/recovery, power-cut or soak evidence is present. P0 #177 synchronous poll-before-sample remains unresolved. CORE authenticated receipt/disposition and QA semantic contract review remain required. No finance, migration, signer, witness, or COE source changed. Coin admission and pending disposition remain fail-closed.

**Classification:** SIMULATED / CI VERIFIED for the local guard; Full and Native integration FAILED on cross-role assertions; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Next exact action

PHX-QA reconciles the Controller protocol parity and PAY-0745 semantics; PHX-CORE publishes the authenticated poll/receipt/disposition contract; PHX-MASTER refreshes its matrix. Hardware keeps #357 DRAFT/unmerged and rechecks exact-head CI after the documentation sync.
