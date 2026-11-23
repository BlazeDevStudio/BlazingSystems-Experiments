# PHX-HARDWARE — configured coin-ingress gate mutation coverage

**Date:** 2026-11-23 UTC09  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`)  
**PR:** [#345 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/345)  
**Branch:** `phoenix/hw-coin-intake-armed-gate-20261122-utc23`  
**Parent:** #343 at `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`  
**Starting PR head:** `deed0f49c04d8cd69dc4fda78d2a4d914aa4dd4d`  
**Source/test commit:** `ad0c6993e3cfdde4f1b11723c277488044b58abd`

## Scope

One Hardware-owned test-integrity improvement in:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

No production sketch, shared CORE API, QA-owned test, financial backend, signer, witness, migration, release workflow or COE destination was modified.

## Coverage gap

The existing #345 source fix correctly makes `sampleCoinPulseEdge()` require all three configured intake gates:

`controllerEnabled && coinEnabled && relayEnabled`

Existing disabled-ingress scenarios exercised controller-OFF, coin-OFF and relay-OFF cases, while a separate mutation checked the `applyOutputs()` relay-output interlock. The runner did not explicitly mutate each term in the *sample-path* `coinIngressConfigured` predicate.

Output-OFF alone is not enough: a sampled edge must also be unable to create a new pending credit.

## Change

Added three independent fail-open mutations against the source-extracted `sampleCoinPulseEdge()`:

- controller gate removed;
- coin-feature gate removed;
- acceptor-relay gate removed.

Each mutation runs the existing no-pending disabled-ingress scenario and must terminate at its distinct expected failure code. This supplements, rather than replaces, the existing output-interlock mutation and pending-identity preservation matrix.

## Exact source/test CI

- Quarantine [run #45150630588](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630588), job `137610815192`: **SUCCESS** at exact source/test SHA `ad0c6993e3cfdde4f1b11723c277488044b58abd`.
- ESP8266 rejected all three mutations: controller exit 64, coin exit 62, relay exit 60.
- ESP32 rejected all three mutations: controller exit 64, coin exit 62, relay exit 60.
- Existing disabled-ingress pending-identity cases emitted 6/6 and 9/9 preservation markers per board; attempted-evidence preservation emitted 6/6 per board.
- Existing coin pulse capture emitted 17/17 per board; output-interlock mutation remained rejected with exit 80.
- Relay/output [run #45150630809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630809): both source-output-polarity job `137610816792` and ESP32 boot-polarity job `137610816965` **SUCCESS**.

## Full integration result — NOT GREEN

Full [run #45150630590](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45150630590) completed with 14 target/platform jobs **SUCCESS**, but validation job `137610815994` **FAILED** at the inherited QA-owned:

`Missing poll signature check`

Twelve validation-dependent jobs were skipped. No synthetic `response_sig` was added and no default-deny behavior was weakened. This remains a cross-role CORE/QA contract blocker, not a Hardware test pass.

## Evidence classification and safety

- Configured-ingress source mutation tests: **CI VERIFIED**.
- Host GPIO/storage/ISR behavior: **SIMULATED**.
- Physical coin pulse, relay contact/voltage and LittleFS power-loss behavior: **NOT TESTED**.
- 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery: **NOT TESTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.**

No flashing, device reset, live coin/payment, production migration, signing, merge, release tag, deployment or cutover occurred.

## Coordination / next action

The live Master `ROLE_ASSIGNMENTS.md` at PR #288 head `876051f1b7c3c0a13a2c322c5a127306d0908b21` still lists #327 as the active Hardware child and omits #345; the live Hardware PR #345 is a separate #343 child. Master has already been asked to reconcile this assignment without collapsing the separate ancestry. No Master-owned file was changed.

Next:
1. PHX-QA independently reviews the three new source-path mutations and resolves the stale poll-signature assertion without inventing a signature.
2. PHX-CORE publishes the authenticated register/poll and event-bound receipt contract with golden vectors.
3. PHX-MASTER refreshes the #345 Hardware assignment and integration pins.
4. PHX-HARDWARE revalidates branch heads before any next source edit.

