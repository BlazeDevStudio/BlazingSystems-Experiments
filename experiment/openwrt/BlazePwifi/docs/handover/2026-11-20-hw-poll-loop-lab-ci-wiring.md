# PHX-HARDWARE — exact-source poll-loop lab CI wiring

**Date:** 2026-11-20 UTC04  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Workflow/source commit:** `2f89326d5b555ffdb2bfaba0a404483d665aa614`

## Finding

The current #327 branch already contained `poll_loop_blocking_inhibit_lab.py`, which extracts the production loop and poll/coin-edge helpers from both ESP sketches and exercises synchronous-poll abort, ISR/no-ISR pulse, active-line hold, unresolved-ingress persistence, release-window edge and coin-POST reconciliation cases.

However, the #327 quarantine/readback workflow did not invoke this lab. The separate `phx-hardware-poll-edge-latch.yml` workflow only had a push branch filter for `phoenix/hardware-poll-edge-latch-20261118`; it did not execute for the current #327 branch. The test therefore existed without being part of the current branch's quarantine gate.

## Change

Added one command to `.github/workflows/phx-hardware-quarantine-byte-readback.yml` immediately after `poll_window_drain_lab.py`:

```sh
python3 experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py
```

The existing workflow already verifies the literal PR/push head and extracts both ESP8266 and ESP32 sketches. No firmware runtime, persistence schema, CORE API, QA-owned fixture, RELEASE workflow, PISONET source or COE destination changed.

## Exact CI evidence

- Quarantine/readback [run 44675493401](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675493401), job `136086203687`: **SUCCESS** on the exact workflow/source commit. The log explicitly reports `POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS`.
- Both ESP8266 and ESP32 passed **8/8 fault-marker scenarios** and **7/7 existing poll-loop guards**. Mutation injection rejected release-while-active, missing pre-poll edge abort, removed ISR attachment, no-op ISR, ignored edge delta, omitted fault persistence, deferred output inhibit, removed boot latch, skipped final sample, ignored unobserved pre-poll edge and omitted coin-POST edge persistence.
- Relay/output [run 44675493381](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675493381), job `136086203672`: **SUCCESS**.
- Full BlazePwifi [run 44675493379](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675493379), validation job `136086204332`: **FAILED** at inherited QA-owned `Missing poll signature check`. ESP8266 target passed; ESP32 and several platform/Android jobs were still in progress at capture. No Full matrix PASS is claimed; production import/sign/update jobs were skipped.

## Evidence classification and limits

- **SIMULATED / CI VERIFIED:** source-extracted host C++ poll-loop and fault-injection cases on both sketch sources.
- **NOT TESTED:** physical coin acceptor, relay/electrical pulse recovery, 150 controlled power cuts, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO — PRODUCTION NO-GO.

No flash, reset, live money, financial migration, signer provisioning, merge, release tag or deployment occurred.

## Next exact actions

1. **PHX-QA:** replace the inherited positive poll-signature assertion with source-exact default-deny tests and rerun Full validation.
2. **PHX-MASTER:** reconcile #322–#327 stack ancestry and register the canonical Hardware stack before any merge/integration decision.
3. **PHX-CORE:** publish the authenticated register/poll and event-bound receipt contract before any positive coin disposition is considered.
4. **PHX-HARDWARE:** retain this poll-loop lab in the active quarantine workflow and revalidate the exact head after coordinated stack changes.
