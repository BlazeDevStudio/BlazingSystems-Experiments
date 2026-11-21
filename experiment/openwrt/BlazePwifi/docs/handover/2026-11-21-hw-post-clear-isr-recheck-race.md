# PHX-HARDWARE — post-clear ISR recheck race regression

**Date:** 2026-11-21 UTC11  
**Task:** #177 coin-ingress safety / #266 cleanup-first test quality  
**PR:** [#332 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/332)  
**Branch:** `phoenix/hardware-post-clear-isr-recheck-20261121-utc11`  
**Parent:** #330 at `1a1e5e25834748fbba95d6253eb668f29b6c82f8`  
**Source/test SHA:** `8b5b99e08297ba85bda1e665818161ee8d8859f6`

## Why

Both ESP sketches intentionally reconcile the ISR edge sequence before clearing an authenticated, acknowledged pending event and again after `clearPending()`. The second snapshot is required because `clearPending()` performs LittleFS operations; an ISR edge can arrive while those operations are in progress. The existing dispatch lab checked that the handler calls reconciliation twice, but its fake helper did not exercise the actual source-extracted reconciliation logic or inject an edge during the clear boundary.

## Change

Only the Hardware-owned `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/coin_post_gate_lab.py` changed.

The added C++17 host harness extracts both actual functions from each board sketch:

- `reconcileUnobservedCoinEdges()`
- `handleCoinPostResponse()`

It runs three scenarios per board:

1. **Edge during clear:** the fake `clearPending()` injects an ISR sequence increment; the second source-extracted snapshot must call the fault latch and leave the simulated output gate denied.
2. **No-edge control:** the acknowledged pending record clears with no recovery latch.
3. **Pre-existing edge:** the first snapshot latches the edge and prevents pending clear.

A fail-open mutation removes the post-clear reconciliation call. The harness must reject that mutation at the edge-during-clear scenario (exit 32).

No production .ino, controller API, receipt contract, finance, migration, signer, witness, QA-owned test, or Release source changed.

## Test-first history

- Initial exact-source run [#44898252978](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44898252978), job `136828429774`, failed in the mutation-check ordering: the mutant was rejected by the no-edge snapshot-count assertion (exit 31) before reaching the injected race assertion (exit 32). The actual ESP32 race scenario itself printed `POST_CLEAR_ISR_RECHECK_PASS 3/3`; the workflow did not reach the ESP8266 race harness.
- Test-only correction at source/test SHA `8b5b99e08297ba85bda1e665818161ee8d8859f6` places the injected race first so the mutation is rejected by the intended scenario.
- Corrected exact-head focused run [#44898340322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44898340322), job `136828701829`: **SUCCESS** on source/test SHA `8b5b99e08297ba85bda1e665818161ee8d8859f6`.
- Exact log markers on **both ESP32 and ESP8266**:
  - `POST_CLEAR_ISR_RECHECK_PASS 3/3; simulated source boundary only`
  - `MUTATION_REJECTED remove-post-clear-isr-recheck (exit=32)`
  - Existing `COIN_POST_DISPOSITION_DISPATCH_PASS 7/7`
  - Existing event-bound authentication bypass mutation rejected (exit 11)
- The corrected Full build push run [#44898336541](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44898336541) ended **CANCELLED** after validation job `136828756010` **FAILED** at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. Some target jobs passed, but ESP32, x86-64, Android and several optional targets were cancelled; downstream simulations, bundle, signing and publication were not completed. The PR Full run [#44898340282](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44898340282) was also cancelled. Do not claim full integration or all-target build acceptance.

The hardware test does not change or satisfy the CORE/QA poll-response contract.

## Evidence classification and limits

- Current work: SIMULATED C++17 host boundary with exact source extraction.
- Focused exact-head CI: VERIFIED on source/test SHA 8b5b99e08297ba85bda1e665818161ee8d8859f6 (run #44898340322, job 136828701829).
- Physical GPIO/relay/coin behavior: NOT TESTED.
- LittleFS physical durability and power-cut behavior: NOT TESTED.
- 150 controlled power cuts: NOT TESTED.
- 30-device / 24-hour soak: NOT TESTED.
- Electrical pulse/recovery: NOT TESTED.
- Protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff: NOT ESTABLISHED.

**HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

## Registry and provenance

The current connected Library search did not locate the requested private `BLAZE_PROJECT_REGISTRY_v11_20261027.json`, and no Google Drive connector is exposed in the current tool surface. Older registry snapshots were not substituted.

## Next exact action

PHX-HARDWARE: retain the exact-source focused evidence and request QA review of the new race assertion. PHX-CORE/PHX-QA must resolve the inherited authenticated poll-signature contract without weakening default-deny. PHX-MASTER must preserve the #327 → #330 → #332 stack. Keep PR #332 DRAFT / UNMERGED; do not merge, rebase, retarget, flash, migrate, sign, tag, deploy or cut over.
