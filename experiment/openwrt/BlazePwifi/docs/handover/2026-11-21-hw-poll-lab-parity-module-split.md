# PHX-HARDWARE — poll-loop parity module split (UTC21)

**Disposition:** PR_READY · CI VERIFIED (focused host labs) · SIMULATED ONLY · PRODUCTION NO-GO  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments (repository ID 1389289885)  
**PR:** [#337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/337) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-poll-lab-parity-module-20261121-utc21`  
**Parent:** PR #336 at `8ebe2e45622a82060a010691bbaa3f0abac72452`  
**Source/test SHA:** `66197b7ae39f95213ab1568e78611e23b8b4dd47`  
**Base:** #336 branch `phoenix/hardware-quarantine-lab-modules-20261121-utc19`

## One bounded task

The 707-line `poll_loop_blocking_inhibit_lab.py` mixed C++ token-aware normalization, 23-helper ESP32/ESP8266 parity and fail-open mutation guards with exact-loop extraction, compilation and scenario execution.

The source/test commit moved the parity responsibility into the adjacent `poll_loop_blocking_inhibit_lab_parity.py` module and left the runner responsible for scenario construction/execution. The runner now supplies its existing `BOARDS` map and `MAIN` fixture explicitly.

- Runner: 707 → 388 lines.
- New parity module: 332 lines.
- PR change: 2 files, 345 additions / 330 deletions.
- The C++ fixture payloads and all scenario bodies remain unchanged.
- No firmware sketch, controller API, response-signature contract, finance, signer, witness, GPIO/relay logic, QA-owned assertion, workflow policy or release path changed.

## Test-first failure and correction

The first source commit `5d10c66f243f253b13df394b996c45608e971103` left two old module-level no-argument calls in the extracted parity module. Exact-head Relay run [#44953145600](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44953145600) and Quarantine run [#44953145649](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44953145649) failed with a missing `boards` argument.

The correction is source/test SHA `66197b7ae39f95213ab1568e78611e23b8b4dd47`: module-level execution was removed; the runner now calls the three parity functions explicitly with its dependencies. The initial failure is retained in Actions history, not hidden.

## Exact-source CI evidence at `66197b7ae39f95213ab1568e78611e23b8b4dd47`

- Quarantine/readback [run #44953246591](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44953246591), job `136995617776`: SUCCESS.
- Relay/output [run #44953246604](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44953246604):
  - `esp32-boot-polarity` job `136995617999`: SUCCESS.
  - `source-output-polarity` job `136995618227`: SUCCESS.
- Observed poll-parity markers: C++ normalizer 10/10; shared helper parity 23/23; quarantine helper parity 6/6; drain-abort polarity fixture 2/2.
- The exact production-loop host lab passed for both ESP8266 and ESP32, including #177's 1501/1600/1680 ms blocked-poll timing fixture, pre/post-drain ISR snapshots, active-high/active-low edges, multi-edge rollover, and injected missing-inhibit/edge/persistence mutations.
- Quarantine suite also reported 36/36 scenarios per board (72/72 combined), pending-attempt marker 29/29 per board, pending clear/readback, fake-LittleFS and failure-injection checks.

These are source-extracted host simulations and CI checks. They are **not** physical coin acceptor, relay, flash, or power-cut evidence.

## Full integration disposition

Exact SHA [push run #44953242642](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44953242642):

- Validation job `136995677947`: FAILURE at `Controller protocol parity`, inherited QA-owned `Missing poll signature check` in ESP8266.
- All 14 firmware/Android target jobs: SUCCESS.
- Downstream browser/target simulations, candidate, signing and publication jobs: SKIPPED.

Do not add an ad-hoc signature or weaken the firmware's default-deny `acceptPollResponse()` / `coinPostDispositionVerified()` behavior. PHX-CORE owns the authenticated register/poll/coin response contract and golden bytes; PHX-QA owns the stale positive signature-presence assertion.

## Remaining gates

- Physical 150 power cuts, 30-device/24-hour soak, electrical pulse/recovery: NOT TESTED.
- Protected anti-rollback signer and independent witness: NOT ESTABLISHED.
- v1→v2 financial migration, durable accounting and replay: NOT TESTED / NOT ESTABLISHED.
- Independent QA and Release acceptance: PENDING.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json`: not available through the connected file/Drive surfaces; older Library snapshots were not substituted.

No physical flash, reset, live coin/money operation, production migration, signing, merge, release tag or deployment occurred.
