# PHX-HARDWARE handover — poll/register trust boundary deny

**Date:** 2026-11-18 UTC18  
**Role:** PHX-HARDWARE  
**Task:** Master Architecture Contracts §6.1 / §6.3 / §6.4 alignment  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Firmware source commit:** [a3de2abbd8ffcdac98773b878604042afbe23411](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a3de2abbd8ffcdac98773b878604042afbe23411)

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
