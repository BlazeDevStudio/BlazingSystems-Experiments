# PHX-MASTER UTC01 — COE #49 Stage 5.1 target-kind, expiry and ownership audit

**Scheduled slot:** 2026-11-20T01:37:37Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** #172, #266, #288, exact role PR/CI refresh, COE #26/#48/#49  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.

## 1. Exact refs

| Ref | SHA / state |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments v0.6.0 audit-foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Generic Experiments development | Not found (404) |
| Master branch before this commit | `59895f794e6e14d1cee2665f314a26bb66f42577` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| COE #48 | `8286548e395366f2332830025fed00ceebdfb24a` |
| COE #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`, base exactly #48 |

COE #49 changes 7 files, all under Hardware staging/tests/tools and its scoped workflow. No changed path is under `Pisowifi/`. It is a separate Stage 5.1 candidate stacked on #48, not part of #26.

## 2. Source-grounded findings

### 2.1 Target-kind is checked after the backend mutation

The current v1 `poll` response signs `insert`, `target_nonce` and `expires`; it does not return a signed target `kind` or signed server time. The separate `register|ping` action returns signed `server_time`, but Stage 5.1 does not call it and its poll proof does not bind time or kind. See [poll signature/response](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/b382d233ff06c8791b1028bed3c617cc7b670d12/Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo#L96-L160).

[Stage 5.1 `RouterV1.coin()`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/aeb8ff11b2f5db9a5f86280ab62ab988245f3919/Hardware/tools/remote_cs_router_bridge.py#L200-L216) sends the `coin` request first, then rejects `rental:true`. The actual backend `coin` branch reads the target kind, calls `bp_rental_apply_coin`, updates rental progress, and only then returns `rental:true` ([backend mutation/response](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/b382d233ff06c8791b1028bed3c617cc7b670d12/Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo#L341-L412)).

**Impact:** the sidecar can withhold ESP `ACKN` after rejecting the response while the backend rental progress/time has already changed. The hotspot-only policy is not enforced before the paid mutation. This is a source-order finding, not a claim that a customer incident occurred.

### 2.2 Expiry authority is incomplete

`Bridge.tick()` uses local `time.time()`. The signed poll has no server-time anchor. An already-matching ESP session returns `ACTIVE` before the remaining router TTL is recalculated; the expiry-floor calculation is only reached on a new OPEN. See [adapter session/lease ordering](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/aeb8ff11b2f5db9a5f86280ab62ab988245f3919/Hardware/tools/remote_cs_router_bridge.py#L381-L458).

A slow/rolled-back sidecar clock or a shortened router target can leave the physical CS enabled beyond the authoritative target expiry. The later event path denies credit once local time says expired, but can strand a physical pulse. Require an authenticated server-time/relative-TTL anchor, monotonic deadline, and close-before-expiry enforcement on every poll before the existing-session fast path.

### 2.3 Existing test is mock-only for rental refusal

The exact-head CI ran **16 SQLite/mock tests and passed**. But `test_v1_rental_backend_refused_without_esp_ack` stubs `RouterV1._request()` to return `rental:true`; it does not execute the backend's `bp_rental_apply_coin` path or assert that rental progress/ledger state remains unchanged ([test](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/aeb8ff11b2f5db9a5f86280ab62ab988245f3919/Hardware/tests/test_remote_cs_router_bridge.py#L292-L297)). The expired-event test covers an event already past expiry, not closing an active ESP session before expiry ([test](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/blob/aeb8ff11b2f5db9a5f86280ab62ab988245f3919/Hardware/tests/test_remote_cs_router_bridge.py#L183-L190)).

## 3. Exact CI

### COE #49

| Workflow | Run | Result |
|---|---|---|
| Stage 5.1 bridge | [44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) | PASS; 16/16 SQLite/mock tests, ESP8266 compile and source-only package pass |
| Case-collision guard | [44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) | PASS |
| Shared Hardware/Contracts | [44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) | Validation and ESP8266 pass; ESP32 compile FAIL: `mbedtls/sha256.h` missing under Arduino ESP32 core 4.0.0 |

This is scoped LAB/CI evidence, not a combined destination build, real router test, physical coin test or production acceptance.

### COE #26

| Workflow | Run | Result |
|---|---|---|
| Case-collision | [43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609) | QUEUED; zero jobs |
| Windows synthetic | [43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632) | QUEUED; zero jobs |
| Hardware/Shared | [43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800) | QUEUED; zero jobs |
| Rental standalone | [43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563) | QUEUED; zero jobs |
| PisoWiFi overlay | [43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557) | QUEUED; zero jobs |

#26 remains frozen; no migration staging occurred.

### Experiments role heads / exact-head CI

| Role / PR | Exact head | Evidence at capture |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| HARDWARE #327 | `a2b7903b4009fd7182247e11a7d2954a79cb9bbd` | [44657641548](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641548) and [44657641425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641425) IN PROGRESS; [44657641509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641509) QUEUED |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head run |
| RELEASE #291 | `7d51c438469fdfd0412377cc1da17c2a83efb26c` | Windows [44656994686](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994686) FAIL at PISONET-owned `$buildWorkflow` unset; ESP32 [44656994754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994754) PASS; BlazePwifi [44656994849](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994849) QUEUED |

The previous #327 head `9c372832...` had a quarantine-lab failure (“ESP32: ambiguous POST outcome is not fail-closed”); that head is superseded by the current-head runs above and is not represented as the current terminal result.

## 4. Ownership and routing

`OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`. No route exists for COE #48 or #49. Do not infer PHX-HARDWARE or PHX-PISONET ownership from the Hardware directory or stacked PR base.

- PHX-CORE retains the existing v1 backend/financial authority; Master requests review of the pre-mutation target-kind and signed-time contract only.
- PHX-PISONET sidecar review and PHX-HARDWARE ESP lease/journal review are requested, not assigned, pending each owner's explicit ACK/DECLINE.
- PHX-QA owns independent negative tests.
- PHX-MASTER owns only coordination/phoenix, architecture/interface contracts and migration provenance.

No source blob, licence, test, workflow or file was copied, moved, rebased, cherry-picked or staged into #26.

## 5. Required next actions

1. **PHX-CORE:** enforce target-kind allow-list before `bp_rental_apply_coin`; return a signed kind and server-time anchor, or an equally strong authenticated alternative.
2. **PHX-PISONET (review requested):** reject unsupported product kinds before any coin mutation; do not rely on the post-response `rental:true` check.
3. **PHX-HARDWARE (review requested):** close existing ESP sessions before the authoritative expiry floor on every poll.
4. **PHX-QA:** test the real backend path and prove rejected rental targets cause no progress/ledger mutation; add signed-kind, clock-skew, active-session-expiry, replay, lost-response/ACK and reboot cases.
5. Keep #49 draft/LAB and #26 frozen until source, licence, test identity, owner ACKs and exact destination CI are independently complete.

## 6. Limitations

- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced by Library search; no Google Drive connector is exposed. No older snapshot was substituted and no private contents were published.
- Branch protection was not changed. No Master Python suite or Master Actions run was executed; the five source assertions were static source/tree checks, not a substitute for CI.
- No hardware, physical coin, payment, migration, signer, flash, power-cut or soak operation was performed.

**Disposition:** COE #49 is a useful LAB adapter candidate but has unsafe target-kind ordering and incomplete expiry authority. COE #26 remains migration-blocked. **PRODUCTION NO-GO.**


### Terminal CI status supersession — 2026-11-20T02:01Z

The exact-head runs have now completed. This supersedes the earlier “in progress / queued at capture” status above:
- HARDWARE #327 `a2b7903b4009fd7182247e11a7d2954a79cb9bbd`: quarantine [44657641425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641425) PASS; relay [44657641548](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641548) PASS; BlazePwifi build [44657641509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641509) FAIL in validate job `136027838672` at QA-owned `Missing poll signature check` in the ESP8266 sketch. All ESP8266/ESP32/other firmware compile targets in that workflow completed successfully; validation failed before later release/production jobs, which were skipped. Keep firmware default-deny; QA owns the stale positive marker correction.
- RELEASE #291 `7d51c438469fdfd0412377cc1da17c2a83efb26c`: Windows [44656994686](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994686) FAIL at PISONET-owned `$buildWorkflow` unset; ESP32 [44656994754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994754) PASS; BlazePwifi [44656994849](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656994849) PASS. Publisher remains skipped.

No role-owned source was edited by Master.
