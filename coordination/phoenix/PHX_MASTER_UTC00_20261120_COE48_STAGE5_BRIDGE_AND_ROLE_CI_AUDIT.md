# PHX-MASTER UTC00 — COE Stage 5 Remote CS bridge and exact-head role CI audit

**As of:** 2026-11-20T00:50:04Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Parent HEAD:** `52cb1a68f256c3f50969e5b23ccc1f57a3bf2782`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Scope:** `coordination/phoenix/**` only. No subsystem source branch or destination runtime tree was edited.

## Executive result

**PR #288 remains OPEN / DRAFT. COE #26 remains OPEN / DRAFT and migration-blocked. Production remains NO-GO.**

This activation refreshed the live control plane (#172), cleanup gate (#266), current branch refs, Master draft #288, the unchanged ownership manifest, current role PRs/CI, COE main/#26 and the new COE Stage 5 candidate #48. The latest PHX-HARDWARE UTC00 cleanup checkpoint was also read; it supersedes the previous #327 head recorded in the UTC23 report.

## Exact repository refs

| Ref | Exact SHA | Observation |
|---|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | Default/base; branch protection false |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | Named development candidate; unprotected |
| `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` | Named audit/development candidate; unprotected |
| `phoenix/master-coordination` | `52cb1a68f256c3f50969e5b23ccc1f57a3bf2782` | Unprotected; exact PR #288 head |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | Structure-only destination main; unprotected |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT; 205 changed files |
| COE Stage 5 PR #48 | `8286548e395366f2332830025fed00ceebdfb24a` | OPEN / DRAFT; 14 changed files; stacked on #47 |
| Experiments PR #288 | `52cb1a68f256c3f50969e5b23ccc1f57a3bf2782` | OPEN / DRAFT; base main; 112 existing changed paths before this audit |

The generic `development` ref is not the source of truth. Both named candidate refs were checked independently; no branch was promoted or relabeled. The conflicting control-plane designation remains unresolved.

## COE #48 Stage 5 — exact source/target compatibility audit

PR [#48](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/48) is based on COE #47 at `1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597`. Its 14 changed paths are the Hardware/ESP8266 staging sketch, local headers, tests, staging documentation, CLI and one workflow. **No `Pisowifi/` backend path is changed.** It is not part of integration #26 and has no PHX role-owner acknowledgement in its PR discussion.

### Exact protocol mismatch

The Stage 5 firmware implements a new `BLZCS1` HMAC-SHA256 frame on `/api/pisowifi/control`:

`BLZCS1|KIND|SOURCE8|DEST8|COMMAND16|SESSION16|EVENT16|VALUE|HMAC64`

It uses `OPEN`, `CLOS`, `POLL`, `ACKN` and `EVNT/EMPT/OKAY` messages, a controller/device identity pair, 64-bit command/session/event values and a separate 32-byte paired key.

The existing COE #26 OpenWrt backend is a different contract:

- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/api` issues the customer window through `coin_start` and a target nonce.
- `Pisowifi/openwrt/rootfs/www/blazepwifi/cgi-bin/vendo` accepts its existing `action,id,nonce,pulses,target,sig` tuple on the configured Vendo port (default 4455), with signed poll and coin responses.
- `Shared/contracts/controller-signature/schema_v1.json` defines the existing request/response contract.

Source blob anchors read at the exact PR refs:

| File | Git blob |
|---|---|
| Stage 5 bridge contract | `1dc0f709167862d543086449d895dd669f49f32d` |
| Stage 5 codec | `8329a13debd7963b30bccf9612b816f21916b804` |
| Stage 5 two-slot journal | `39cd408af1106e566eff52460cab00663e5d592d` |
| Stage 5 runtime | `835fef140aa743efa49dcc478b255f6d7d8eb91c` |
| COE #26 existing `vendo` | `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` |
| COE #26 existing `api` | `fabbd6fb28a34c162fb40403aec2a40d6fe1a65b` |
| COE #26 V1 signature schema | `8d0f8553ae53a0b22cb874de833aa21ebc52695e` |

The Stage 5 bridge contract itself says **bridge required, not implemented; paid payment NO-GO**. A target nonce (8–32 hex) is not interchangeable with the ESP's 16-hex session. A real adapter must durably bind ESP identity/session to the selected Vendo ID, original target nonce, customer account and expiry. A physical event must be credited exactly once using a stable backend nonce; an uncertain timeout must retry with the same tuple. The router must verify the backend's signed durable receipt before sending an exact matching ESP `ACKN`. Unknown/pending state blocks further coin acceptance and must survive router/ESP restart and expiry reconciliation.

The Stage 5 two-slot journal uses an 84-byte record with CRC32 and readback/rename checks. That is useful local corruption detection, but not an independent protected anti-rollback witness. Its HMAC transport authenticates but does not encrypt. Physical LittleFS crash/power-cut behavior is not established by host tests.

The Stage 5 README declares JuanFi (Apache 2.0) reference-only and says no JuanFi code or protocol was imported. The 14-file PR list contains no JuanFi source import or license-file change. This is the author's declaration plus path inspection, **not** an independent legal license review.

### COE #48 / #47 CI

| Candidate | Run | Result |
|---|---:|---|
| #47 Stage 4.2 | [44620464517](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44620464517) | Case collision PASS |
| #47 Stage 4.2 | [44620464547](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44620464547) | Stage 4.2 workflow PASS |
| #47 shared Hardware | [44620464623](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44620464623) | FAIL: ESP32 compile cannot find `mbedtls/sha256.h` |
| #48 Stage 5 | [44643670696](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670696) | 4/4 jobs PASS: signed-wire tests, static contract, ESP8266 compile, source package |
| #48 case guard | [44643670679](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670679) | PASS |
| #48 shared Hardware | [44643670685](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670685) | Overall FAIL: shared validation PASS, ESP8266 compile PASS, ESP32 compile FAIL on missing `mbedtls/sha256.h` |

The successful Stage 5 workflow is scoped source/native/ESP8266 CI. It does not compile the ESP32 candidate, implement the router bridge, prove durable financial credit, or authorize a physical flash.

## Current Experiments role PR / CI matrix

| Role | Current PR / head | Exact-head evidence |
|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; software-only |
| RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native/CI only |
| HARDWARE | #327 `1d461f2c5fad1ea411ab89bab8d1a1f4e73dce1c` | Quarantine [44648324666](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324666) PASS; relay/output [44648324424](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324424) PASS; Full [44648324417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324417) FAIL |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; does not close #327 fixture |
| QA | #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run returned |
| RELEASE | #291 `2bec5c94b80cc9c3e605ed13bcd001375fa4a6b8` | Windows [44645669562](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44645669562) FAIL; ESP32 compatibility [44645669471](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44645669471) PASS; BlazePwifi [44645669512](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44645669512) PASS |

### New #327 cleanup-first update

HARDWARE's latest UTC00 cleanup checkpoint reports a test-runner deduplication: `config_load_read_failure_lab.py` is now invoked once by its named workflow step, not again through `coin_pulse_capture_lab.py`. Source/test commit `3258e54b5c6ea795cddf52fb7ea68239c90d4ce2`; docs head `1d461f2c5fad1ea411ab89bab8d1a1f4e73dce1c`. Focused quarantine [44648324666](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324666) and relay/output [44648324424](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324424) PASS.

The exact current Full validation [44648324417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44648324417) still fails at QA-owned `Missing poll signature check` in the ESP8266 controller sketch. ESP32, ESP8266, Android and listed image jobs completed; downstream production import, simulations, signing and publishing were skipped. The firmware remains default-deny; QA must replace the obsolete positive poll-signature fixture, not weaken firmware. PR #327's body still describes the older `38a1a29...` head and needs a hardware-owner refresh.

RELEASE #291's Windows job fails in PISONET-owned `negative-selftest.ps1`: `$buildWorkflow` is unset. Its publisher path and subsequent build/sign/publish steps are skipped. PISONET owns the test fix; RELEASE reruns afterward.

## COE integration #26 and other gates

- COE #26 remains OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab4...`, 205 changed files.
- Five unique #26 workflows remain queued: case collision, PISONET Windows, Hardware/Shared, Rental and OpenWrt/Pisowifi. All five job-list queries returned zero jobs. There is no executed destination CI for this head.
- COE #45 (CORE event-bound receipt vectors) is OPEN/DRAFT at `9d76a134c1f6512aa40c20ec4d247306a71a8cce`; case guard [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) and OpenWrt shell [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) PASS, but no dedicated exact-head receipt-vector workflow run was returned.
- COE #35 still has case PASS, shared validation FAIL and mandatory sandbox FAIL at its current head. COE #44 has case/shared PASS but mandatory sandbox FAIL; its ULA candidate is not a site-wide identity authority.
- COE #44's base is not the current #35 head; do not treat those PRs as one validated stack.

## Ownership, cleanup, storage and branch governance

- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`. PHX-MASTER is coordination-only with `target=null`. No route exists for COE #48 Remote CS. No ownership was silently assigned to PHX-HARDWARE or PHX-PISONET.
- COE #48 has no owner acknowledgement in its PR discussion. It remains UNASSIGNED / AUDIT-ONLY pending separate PHX-HARDWARE and PHX-PISONET ACK/DECLINE for review scope; PHX-CORE retains authority over durable receipt/credit semantics.
- Issue #266 remains OPEN. The Master cleanup checkbox remains unchecked because the broad duplicate/dead-code inventory is incomplete. The latest hardware test-runner cleanup is one bounded owner task, not global cleanup completion.
- Experiments main, both named development refs, Master branch and COE main all report `protected=false`. No branch protection was changed.
- Library search surfaced older registry snapshots (v6/v7) and the storage-policy copy, but not canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. No Google Drive connector was exposed. The AGENTS-linked canonical cloud policy and verified recovery handover could not be retrieved; no older registry was substituted and no private IDs/data were published.

## Tests and evidence classification

- Source/tree inspection: performed at the exact refs and blob SHAs listed above.
- Role GitHub Actions: outcomes reported per exact candidate/run; no result was inferred from a different SHA.
- Master-specific Python suite / full coordination suite: **NOT RUN**.
- Master-specific GitHub Actions: **no run returned**.
- This report is a coordination/source audit, not a firmware, financial, physical or production test.

## Required next actions

1. PHX-HARDWARE and PHX-PISONET explicitly ACK or DECLINE their separate COE #48 review scopes; do not change branch ownership.
2. PHX-CORE publishes the versioned, event-bound durable receipt/credit contract and the adapter's stable idempotency mapping before any bridge implementation.
3. PHX-QA replaces the stale positive poll-signature assertion with source-linked default-deny tests and reruns HARDWARE #327 Full.
4. PHX-PISONET fixes the unset `$buildWorkflow` self-test; PHX-RELEASE reruns Windows after the owner correction.
5. COE integration keeps #26 frozen until per-file source/destination blobs, modes, license, imports, test identity and destination CI are verified at the exact proposed SHA.
6. Repository administrator restores protected required checks; registry custodian restores authorized private v11/newer-correction access.

**Disposition:** no migration, merge, release, signing, flash, physical test, secret provisioning, payment operation or Codex execution occurred. **PRODUCTION NO-GO.**
