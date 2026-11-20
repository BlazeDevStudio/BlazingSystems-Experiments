# PHX-HARDWARE — persistent journal deny during poll-drain cleanup

**Date:** 2026-11-20 UTC06  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Task:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `354dddcdbfb93235f10fc99171d15ce63bc01451`

## Bounded change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py` changed.

The existing extracted `handlePollDrainAbortAfterSample()` has a branch for a temporary active-line drain abort that coexists with an already-latched `journalRecoveryRequired`. The regression constructs an adversarial stale-positive controller state (`insertMode=true`, non-empty target, outputs initially energized), then verifies that clearing the temporary drain flags still leaves both outputs OFF because the persistent journal-fault gate dominates.

This tests a critical invariant: temporary poll-drain cleanup must never override an older persistent deny latch, even if stale positive controller state remains in RAM.

No firmware runtime .ino, API, receipt contract, persistence schema, CORE finance code, QA-owned test file, Release workflow or COE source changed.

## Failure injection

The lab runs against both actual board-sketch helper bodies.

- Exact source case emits `POLL_ABORT_PRIOR_JOURNAL_FAULT_REMAINS_DENY_PASS` on ESP8266 and ESP32.
- Mutation removes `!journalRecoveryRequired &&` from the extracted production `applyOutputs()` gate.
- The mutated build is required to exit 47; both boards reject the mutation with `MUTATION_REJECTED ignore-journal-recovery-output-deny expected_exit=47`.

This is host-compiled source-extraction evidence only.

## Exact GitHub Actions evidence

At exact source/test SHA `354dddcdbfb93235f10fc99171d15ce63bc01451`:

- Quarantine/readback PR [run 44690508367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508367), job `136134898059`: **SUCCESS**. Both board logs contain the new regression marker and mutation rejection.
- Quarantine/readback push [run 44690503396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690503396), job `136134881782`: **SUCCESS**.
- Relay/output PR [run 44690508288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508288), jobs `136134897814` and `136134898111`: **SUCCESS**.
- Full BlazePwifi [run 44690508314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508314), validation job `136134898490`: **FAILED** at the inherited QA-owned controller protocol parity assertion, `Missing poll signature check` in ESP8266 `BlazePwifiVendo.ino`. ESP8266 target job `136134898467` passed; remaining target jobs were still in progress at the handover's first inspection. No Full PASS is claimed.

The firmware poll consumer remains default-deny. Do not add a synthetic signature or weaken admission to satisfy the stale positive fixture.

## Status and blockers

- **CI VERIFIED:** focused exact-source quarantine/readback and relay/output jobs.
- **SIMULATED:** source-extracted ESP32/ESP8266 loop, persistence and failure-injection cases.
- **NOT TESTED:** physical coin acceptor, electrical relay behavior, real LittleFS/NVS/EEPROM power-loss behavior, 150 power cuts, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO — PRODUCTION NO-GO.

PHX-QA owns the stale positive poll-signature fixture. PHX-CORE must publish the authenticated register/poll and event-bound receipt contract before any positive disposition can be enabled. PHX-MASTER owns canonical stack reconciliation; Hardware does not rebase, retarget or merge the stack unilaterally.

## Next exact action

PHX-QA replaces the obsolete positive poll-signature presence assertion with source-exact default-deny vectors and reruns Full validation at a pinned SHA. PHX-HARDWARE then reloads the live #327 head and continues only after that exact run and current branch ancestry are reconciled.

No physical flash, device reset, live money, production migration, secret provisioning, signing, merge, release tagging or deployment was performed.
