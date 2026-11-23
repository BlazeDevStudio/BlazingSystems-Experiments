# PHX-HARDWARE handover — coin POST output-polarity gate

**Date:** 2026-11-21 (UTC03)  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `268ca9bde6d3710b418134ffd328060250fad42f`  
**Test file blob:** `b1076a0f30204eb23a994a7d5aa41b7a414b3d75`

## Selected task

Close a specific coverage gap in the Hardware-owned, source-extracted coin POST admission lab: the actual `canAttemptCoinPost()` helper requires known output polarity, but the previous scenario matrix never set `outputPolarityKnown=false`. A regression removing that guard could therefore survive the prior 11/11 scenario set.

## Change

Only `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/coin_post_gate_lab.py` changed in the source/test commit.

- Added an explicit unknown-output-polarity case while keeping the journal, pin map, pending record and pulse count otherwise valid.
- The static contract now requires `outputPolarityKnown`, `pinConfigSafe`, `fsReady`, `!journalRecoveryRequired`, `!pendingPostAttempted`, `pendingReady` and `pendingPulses>0`.
- Added failure injection that removes `outputPolarityKnown &&`; the exact helper must fail with exit 1 on both ESP32 and ESP8266.
- Updated the per-board helper count to 12/12 and corrected the aggregate from 20/20 to 24/24.

No production `.ino`, backend, response contract, GPIO mapping, relay behavior, finance, witness, migration, QA-owned assertion or Release workflow changed.

## Exact-SHA CI

All runs below checked out exact commit `268ca9bde6d3710b418134ffd328060250fad42f`.

| Workflow | Run / job | Result |
|---|---|---|
| Quarantine push | [44860819154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44860819154) / `136713535766` | PASS |
| Quarantine PR | [44860824116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44860824116) / `136713550495` | PASS |
| Full push | [44860819130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44860819130) / validate `136713536248` | FAILED validation; 14/14 target + Android jobs PASS |
| Full PR | [44860824160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44860824160) / validate `136713551139` | FAILED validation; 14/14 target + Android jobs PASS |

Both Quarantine job logs contain:

- `COIN_POST_GATE_PASS 12/12 exact helper scenarios` for each board.
- `MUTATION_REJECTED remove-output-polarity-guard (exit=1)` for ESP32 and ESP8266.
- `COIN_POST_DISPOSITION_DISPATCH_PASS 7/7` for each board.
- `PHX-HARDWARE: 24/24 coin POST gate + 14/14 disposition dispatch cases PASS; actual money NOT TESTED`.

Both Full validation jobs fail at the existing QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. This task did not change or weaken that assertion. The authenticated register/poll/coin response contract remains unapproved; firmware must remain default-deny.

## Evidence boundary

**SIMULATED / CI VERIFIED only.** This is host C++ compilation of source-extracted helpers with synthetic state and mutation injection. It does not test a physical coin acceptor, output polarity, relay, electrical pulse, flash persistence, abrupt power loss or customer money.

Physical 150-power-cut acceptance, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff remain NOT TESTED or NOT ESTABLISHED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

## Next exact action

PHX-CORE must publish the versioned authenticated register/poll and event-bound coin receipt contract; PHX-QA must replace the stale positive poll-signature assertion only against that approved contract. PHX-MASTER must refresh stale #327/#323 pins in `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md` and #172 without retargeting the #322 → #323 → #326 → #327 stack. PHX-HARDWARE will continue only within its firmware/lab ownership.

PR #327 remains OPEN / DRAFT / UNMERGED. No merge, force-push, physical flash, production migration, signing, release tag, deployment or cutover is authorized.
