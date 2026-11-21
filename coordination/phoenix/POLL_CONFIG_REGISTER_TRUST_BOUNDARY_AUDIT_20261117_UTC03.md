# PHX-MASTER — Register-response remote-configuration trust-boundary audit

**Checkpoint:** 2026-11-17 UTC03  
**Disposition:** BLOCKED / PRODUCTION NO-GO  
**Role:** PHX-MASTER  
**Tasks:** #172 / #266 / #288 / #177  
**Scope:** Master-owned coordination and interface contracts only. No CORE, HARDWARE, QA, RELEASE, RENTAL or PISONET source branch was modified.

## 1. Exact repository snapshot

| Ref | Exact SHA |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch / PR #288 before this audit | `2c2b517995365e23d89e423e2b9faeac4135381f` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration candidate / PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| HARDWARE PR #315 | `58ade5df83df0c6894dd8d1e2a70617b90dae374` |
| HARDWARE PR #316 | `888e6941e3a7a81641682c23d937f97d8117d2ea` |

The routing manifest remains `DRAFT_REVIEW_ONLY`. PHX-MASTER owns `coordination/phoenix/` only. No source relocation or destination move is proposed.

## 2. Source-confirmed residual trust-boundary defect

The UTC03 HARDWARE change removed `applyRemoteConfig(response)` from the **poll admission** consumers. That does not close the register/bootstrap path.

At PR #315 exact head `58ade5df...`:

- ESP32 `connectSta()` initializes `sigOk=true`; only when `cfg.key.length()` is nonzero does it inspect `response_sig`. After that conditional, it calls `applyRemoteConfig(r)` whenever the response contains `"ok":true`. The call is at source line 861.
- ESP8266 `connectSta()` has the same control flow using `strlen(cfg.key)`; its `applyRemoteConfig(r)` call is at source line 733.
- Therefore an empty/unprovisioned key leaves `sigOk=true` and permits a positive register response to reach the configuration mutator without signature verification.
- With a provisioned key, the COE #26 candidate's `vendo_ping_sig()` binds the register action, controller ID, request nonce and server time, but **does not bind the returned `controller` configuration object**. The candidate response includes both `controller` and `response_sig`; changing configuration fields does not change the signed input.
- Experiments main's register/ping response has no `response_sig`; a configured-key client rejects it, but the keyless path above still permits configuration application.

The firmware's `applyRemoteConfig()` consumes behavior-changing fields including controller/coin/relay/LED enable flags, GPIO assignments, active polarity, debounce, pulse grouping, Wi-Fi retry count and configuration revision. The current hardware-owned poll lab injects hostile config fields into a poll response; it does not exercise the separate `connectSta()` register-response path.

This also narrows the current HARDWARE handover statement that the remote-config helper is “dormant”: it is no longer called by poll admission, but the exact source still calls it from `connectSta()`.

### Pinned source links

- [ESP32 PR #315 source at exact head](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/58ade5df83df0c6894dd8d1e2a70617b90dae374/experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino)
- [ESP8266 PR #315 source at exact head](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/58ade5df83df0c6894dd8d1e2a70617b90dae374/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino)
- [COE #26 candidate producer at exact SHA](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/b382d233ff06c8791b1028bed3c617cc7b670d12/Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo)
- [Experiments main producer at exact SHA](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/f4e8a891aed8af86d5fd315d28750a0ac3a7372b/experiment/openwrt/BlazePwifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo)
- [HARDWARE UTC03 handover at exact head](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/58ade5df83df0c6894dd8d1e2a70617b90dae374/experiment/openwrt/BlazePwifi/docs/handover/2026-11-17-hw-poll-quarantine-consolidation.md)

This is static source inspection of the exact GitHub files, not a live attack, target execution or physical actuation test.

## 3. Exact-head CI evidence

- HARDWARE focused run [44008962809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008962809), job `133791040003`: **SUCCESS**. Poll/config-isolation 11/11 per board; strict root JSON 13/13; debounce 8/8; poll-window 8/8; quarantine 34/34; mount/output 14/14; boot recovery 32/32; pending-clear 22/22; pending write/readback 44/44; coin POST gate 18/18. These are source-extracted host/fake-filesystem simulations.
- HARDWARE full run [44008962837](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008962837): **FAILURE** at validation job [133791150681](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44008962837/job/133791150681), because QA-owned `tests/controllers.sh` omits `acceptPollResponse()` from both board harnesses. ESP32, ESP8266, target-image and Android build jobs passed, but the overall workflow is not green.
- HARDWARE #316 full run [43972511250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250) also failed validation; it remains a separate open draft.
- Master #288 at the pre-audit head returned no PR-triggered workflow runs.
- COE #26 still has five queued candidate-head workflows; no integration acceptance is established.

No PHX-MASTER unit suite or local source test was executed in this activation. CI results above belong to the owner-controlled HARDWARE workflow and are not Master test results.

## 4. Master interface hold — proposed config contract, owner approval pending

Until PHX-CORE defines the separate configuration envelope and PHX-QA independently verifies it:

1. **No remote configuration may be applied from either poll or register/ping responses.** Keep `applyRemoteConfig` unreachable from both paths. Local setup/provisioning remains separate and non-authorizing for coin admission.
2. Empty/unprovisioned key means no remote configuration authority. A default `sigOk=true` must not authorize configuration.
3. Poll `response_sig` and register/ping `response_sig` are not configuration signatures. Neither may authorize fields it does not cover.
4. Any future configuration envelope must be domain-separated from poll admission and bind, in one deterministic canonical representation: schema/version, controller identity, the matching request nonce, monotonic configuration revision, freshness/expiry data, key identity/version when applicable, and **every** field that can alter firmware behavior (enable flags, GPIOs, polarity, timing/debounce, pulse grouping, retry settings, and future additions).
5. The exact cryptographic construction and canonical bytes are **TBD by PHX-CORE and subject to independent PHX-QA approval**. Publish positive and negative golden vectors. Do not label an ad-hoc keyed SHA-256 concatenation as HMAC.
6. Validate identity, signature, revision and all field bounds before mutation. Persist the complete new configuration atomically before activating it. On signature, validation or persistence failure, keep the prior configuration intact, apply no partial fields, and keep coin admission denied. An exact replay may be a no-op; a conflicting or stale revision must be denied.

This is a Master coordination/interface hold, not permission for PHX-MASTER to edit firmware or CORE financial source.

## 5. Owner-specific next actions

- **PHX-HARDWARE:** add register-path regressions for both boards (empty key; configured key with a valid register signature but altered config); remove/guard the remaining `connectSta()` call until a separately authenticated config envelope is approved. Preserve the existing poll isolation and default-deny behavior.
- **PHX-CORE:** define the canonical configuration envelope, signing algorithm/domain separation, revision/freshness rules and exact golden vectors. Do not change the hardware consumer unilaterally.
- **PHX-QA:** independently reproduce the register-path injection cases and verify valid/invalid signature, wrong controller/nonce, stale/conflicting revision, range failure and persistence failure at the same exact source SHA. Repair the existing canonical extractor as a separate QA-owned change.
- **PHX-RELEASE:** keep signing, publication and release gates closed; focused simulated CI is not acceptance.

## 6. Registry and release limitations

The exact private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed connected tools in this activation. The Library search surfaced older historical registry snapshots only; none was substituted. No private registry contents or Drive identifiers are included here.

Protected signing/anti-rollback witness, crash-atomic financial state, reversible migration, independent QA, native acceptance, 150 real power cuts and 30-device/24-hour soak remain unverified. **PRODUCTION NO-GO.**

No Codex, merge, release, flash, reset, secret provisioning, live payment, physical test or migration occurred.
