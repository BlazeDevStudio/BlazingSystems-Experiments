# PHX-HARDWARE — Pending-recovery host String ownership regression

**Date:** 2026-11-27 UTC14  
**PR:** [#361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/361), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-pending-recovery-harness-module-split-20261127-utc13`  
**Parent:** #359 at `47357aab2ff7910b38ca538a46dfa01bdbca01e8`  
**Source/test commit:** `4a85070a1f6a1caa417570a91dcdf355ff072fcc`  
**Role:** PHX-HARDWARE

## Finding

The source-extracted `loadPending()` declares `BpPendingSequence r{}` locally, then copies `r.nonce` and `r.target` into Arduino `String` values. The host harness's fake `String` stored only the incoming pointer. After `loadPending()` returned, that pointer referenced expired stack storage. Existing tests checked sequence/filesystem state but did not read the nonce/target after return, so this harness-fidelity defect was invisible.

## Change

In `pending_recovery_promotion_lab_harness.hpp`:

- Replaced the borrowed `const char *` fake with an owning `std::string` value.
- Added `c_str()` and `length()` accessors matching the operations needed by the extracted function and assertions.
- Added identity assertions to all existing scenarios: successful canonical/new/backup recovery must preserve the expected nonce and target; ambiguous candidates, failed rename, invalid-only and empty-journal paths must not publish identity; legacy migration write failure retains the loaded identity while keeping `fsReady=false` and `pendingReady=true`.

No scenario count, extracted firmware body, production sketch, or firmware behavior changed.

## Exact-source CI

- Focused run [#46016953274](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953274), job `140566402392`: PASS.
- Mbed run [#46016953049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953049): source-contract job `140566402516` PASS; core 3.3.13 job `140566402198` PASS; core 4.0.0 job `140566402334` in progress at checkpoint.
- Pre-sync Full run [#46016953164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953164): mandatory handover freshness job `140566586511` failed because this source commit was not yet documented; CI-0701 passed and target jobs were still running. Post-sync Full rerun required.

## Ownership and safety

No production sketch/runtime, shared API, QA-owned assertion, finance, signer/witness, migration, COE source, or release workflow changed. Parent #359 remains deny-only. CORE owns authenticated register/poll and receipt/disposition; QA owns independent semantic assertions; MASTER owns stack integration and release gates.

**Evidence classification:** host-only SIMULATED / CI VERIFIED. Physical LittleFS, GPIO/relay/electrical acceptance, 150 controlled power cuts, and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

No flash, reset, live money, production migration, merge, signing, release tag, or deployment.
