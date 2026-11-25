# PHX-HARDWARE handover — poll/register trust boundary deny

**Date:** 2026-11-18 UTC18  
**Role:** PHX-HARDWARE  
**Task:** Master Architecture Contracts §6.1 / §6.3 / §6.4 alignment  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Firmware source commits:** [a3de2abbd8ffcdac98773b878604042afbe23411](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a3de2abbd8ffcdac98773b878604042afbe23411) (poll/register/config deny) and [236e6a6976f9f83a611f97eb82a7a336240fbf4c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/236e6a6976f9f83a611f97eb82a7a336240fbf4c) (coin POST/replay deny)

## Source finding

The current Experiments `main` Vendo producer at blob `2e3a1430d08cc6606429a042df3b5848f53c7267` returns register/ping with `ok`, `server_time`, and `controller`, and poll with `ok`, `insert`, `target_nonce`, `expires`, and `controller`. Neither action returns `response_sig`.

Before this change, both #283 sketches initialized `sigOk=true`; signature validation ran only when a controller key was non-empty. An empty key therefore allowed an `ok:true` poll to set `insertMode` and `activeTarget`. Both register and poll paths also called `applyRemoteConfig()`, although Master §6.4 says register/poll signatures do not authenticate the configuration object and no separate config-auth envelope is approved.

## Firmware change

At source commit `a3de2abbd8ffcdac98773b878604042afbe23411`:

- ESP32 and ESP8266 controller/coin/relay/LED enable flags now initialize OFF.
- Added `denyRemoteControl()`, which clears `insertMode` and `activeTarget`, keeps all actuation flags false, and reapplies safe outputs.
- Setup invokes the deny helper after runtime pin configuration.
- Register/ping is still sent for discovery/heartbeat, but its response is ignored; it cannot invoke `applyRemoteConfig()`.
- Poll is still sent, but all response fields are ignored and the deny helper runs every poll. This prevents keyless authorization, unapproved derived-signature authorization, and reuse of stale positive poll state.
- The HTTP `post()` allowlist now permits only `register` and `poll`; `coin` and unknown actions are rejected before network dispatch.
- The automatic pending-coin POST/retry/clear loop was removed. Any recovered or pending journal remains intact for operator/CORE reconciliation until Master §6.6's event-bound authenticated receipt/disposition contract is approved.
- `applyRemoteConfig()` remains present only as a future candidate helper and has no register/poll call sites.
- The audit table no longer claims that the candidate response-signature calculation is an accepted authentication protocol.

This is deliberately fail-closed downtime, not a working authenticated coin-intake implementation. It does not define or change the shared protocol.

## Verification

- Source-shape checks in the write step passed: both sketches have default-off flags, a deny helper, no `sigOk=true`, and only the disabled `applyRemoteConfig` definition (no call sites).
- Exact source commit Actions run: [#44152159613](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44152159613) — QUEUED at checkpoint time; no pass/fail result yet.
- Firmware compilation and independent keyless/config/poll failure-injection tests: NOT YET VERIFIED.
- Physical coin, relay, power-cut, electrical recovery and soak tests: NOT TESTED.

PHX-QA owns independent regression fixtures and must add negative tests for empty-key `ok:true`, an unapproved configured-key poll candidate, register-driven configuration injection, and stale positive poll state at this exact source SHA. PHX-CORE owns the canonical poll producer/consumer and separate configuration-auth contracts.

## Remaining blockers (not fixed by this task)

- Master §6.2: quarantine append failure still lacks byte-for-byte readback and a durable cross-reboot no-replay/reconciliation marker.
- Master §6.5: the current #283 `/quarantine/clear` handler still deletes reconciliation evidence; authenticated operator reconciliation is not approved.
- Current main poll/register producer/consumer compatibility and golden vectors remain unapproved.
- Protected signer/witness, durable accounting/replay, v1-to-v2 migration, 150 real power cuts, 30-device 24-hour soak, electrical pulse/recovery and independent release signoff remain open.

**Disposition:** PR #283 remains DRAFT / UNMERGED. Coin admission and remote configuration remain denied. PRODUCTION NO-GO.


## Additional fail-closed coin-dispatch correction — 2026-11-17 UTC18

At source commit `236e6a6976f9f83a611f97eb82a7a336240fbf4c`:

- `post()` now allows only `register` and `poll`; `coin` and unknown actions are denied before HTTP dispatch.
- The automatic pending-coin POST/retry/clear loop was removed from both sketches. Pending journals are retained; there is no automatic financial replay or clear based on raw `ok:true`.
- This is required by Master §6.6 because no event-bound authenticated receipt/disposition contract is approved. It deliberately prevents coin credit until PHX-CORE and PHX-QA complete their contracts and vectors.

No new tests were added or modified by PHX-HARDWARE because independent verification fixtures belong to PHX-QA. The existing #283 generic response-signature simulation is not evidence for this deny path. Full exact-head CI must be rerun on the new source commit.


## UTC21 supersession — 2026-11-17T21:42Z

This addendum supersedes only the stale status statements above; it does not rewrite their historical source findings.

- The earlier statement that `POST /quarantine/clear` still deletes `/quarantine.log` is historical for the prior source SHA. At the current #283 branch head at this checkpoint, both sketches return HTTP 403 for the clear route and contain no `LittleFS.remove("/quarantine.log")` call. The route-denial lab exists but is not yet wired into the QA-owned controller test entrypoint; PHX-QA should integrate and independently execute it.
- The separate LittleFS mount-failure auto-format defect is fixed at source/test commit [90a9cf8623b54139dabe6ef5360f0a7da91a9519](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/90a9cf8623b54139dabe6ef5360f0a7da91a9519). See [the dedicated mount-preservation handover](2026-11-18-hw-littlefs-mount-failclosed.md).
- Exact-head [Actions #44182117122](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44182117122) checked out PR #283 documentation head `a43ca007b1a7ef38cc278395ca12c5bb2ec656da`, whose firmware blobs are the unchanged source/test commit above:
  - ESP8266 job `134389072926`: SUCCESS.
  - ESP32 job `134389073268`: SUCCESS.
  - Full validation job `134389072950`: SUCCESS.
  - Target/platform matrix: 14/14 SUCCESS (including both ESP boards, x86_64, Ruijie, Android and supported Orange Pi variants).
  - Update bundle and completed v0.4 browser/ESP/Ruijie/Orange Pi simulations reported SUCCESS; at this checkpoint x86 and Android emulator simulations were still in progress.
  - Production APK import/signing, production sign handoff, prerelease and release publication were SKIPPED. No production readiness is implied.
- The committed `littlefs_mount_failclosed_lab.py` is not invoked by this existing workflow. The local exact-function host C++ RED/GREEN and mutation checks are SIMULATED only; QA integration and independent exact-head execution remain required.

No physical flash, coin acceptor, relay contact, power-cut, electrical recovery or customer device was operated. PRODUCTION NO-GO remains.
