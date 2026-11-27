# PHX-MASTER UTC19 — exact-head Hardware stack, COE #26 provenance and owner CI audit

**Observed UTC:** 2026-11-25T19:51:24.680Z  
**Role:** PHX-MASTER — master coordination, architecture/interface contracts, migration provenance and integration sequencing.  
**Disposition:** coordination audit committed; COE #26 remains FROZEN; PR #288 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**. Strict NO CODEX.

## 1. Scope and exact repository refs

This is a read-only audit of subsystem source and destination trees plus Master-owned coordination documentation. No CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branch was modified.

- Experiments `main`: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Active v0.6 development `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master branch starting HEAD: `7aa4c3bd5248a31f12d089a1ec40a46a9d941f06`.
- COE `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER source is `coordination/phoenix/`, destination null.

At audit start, PR #288 was OPEN / DRAFT / UNMERGED at `7aa4c3bd`; current main comparison was 575 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 220 changed paths, all under `coordination/phoenix/`. Main was not synchronized; no rebase or retarget occurred.

## 2. HARDWARE #352 / #353 exact stack reconciliation

### Parent #352

- Branch: `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`.
- Current PR/docs HEAD: `0e984e267b3a8fb10c314800d1a7f120806354b7`.
- Source/test pin in the current PR body: `8eab82606ab8bf7ae5c598edde739d7b47e7c7a2`.
- The latest commit `0e984e2` changes one newline matcher in `coin_pulse_capture_lab_structure_guard.py`; it does not change a production `.ino` sketch.
- Exact docs-head Quarantine [#45683122459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122459) PASS; Relay [#45683122371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122371) PASS; ESP8266 core [#45683122364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122364) PASS; ESP32 core [#45683122379](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122379) PASS.
- Full [#45683122413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122413) FAILS in validation at `Missing poll signature check` in the ESP8266 sketch. Target/platform jobs pass; downstream candidate, simulation, signing and publication stages do not establish acceptance.

### Stacked child #353

- Branch: `phoenix/hw-board-conditional-isr-selector-20261125-utc17`.
- Current docs HEAD: `e2ac06974874ed1fe72391e9246d6f4abfb73f2e`.
- Source/test HEAD: `2c9581e96363c0d5cba5293347d386edf2ac96f7`.
- Child PR base SHA captured at open: `6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec`; live parent #352 branch HEAD is now `0e984e267b3a8fb10c314800d1a7f120806354b7`. The stacked child is therefore based on an older parent snapshot. Keep it draft; no rebase, retarget or merge was performed.
- Exact-source Quarantine [#45685861838](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861838) PASS; Relay [#45685861933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861933) PASS; Full [#45685861934](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861934) FAILS at the same inherited poll-signature assertion.
- Latest docs-head Quarantine [#45687084991](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45687084991) PASS; Relay [#45687084897](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45687084897) PASS; Full [#45687084859](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45687084859) FAILS at the same assertion.
- #353 changes only the host-lab selector `coin_pulse_capture_lab.py`: it selects the active board definition before checking IRAM attributes and tolerates an inactive preprocessor decoy. It does not change production firmware, GPIO/relay behavior, controller APIs, finance, signer, witness or migration code.

**Ownership:** HARDWARE owns #352/#353 source and PR descriptions; CORE owns the authenticated poll/register producer contract; QA owns independent assertion review. Do not weaken default-deny or invent `response_sig` bytes.

## 3. Exact HARDWARE source → COE #26 candidate comparison

Complete, non-truncated recursive Git trees were compared at source #352 docs HEAD `0e984e2` and destination #26 `b382d233`.

| Measure | Experiments #352 | COE #26 |
|---|---:|---:|
| Tree entries | 2,564 | 286 |
| Blobs | 1,985 | 207 |
| ESP32 + ESP8266 subtree entries | 86 | 6 |
| ESP32 + ESP8266 subtree blobs | 82 | 2 |
| Board-local Python helpers | 70 | 0 |
| Mapped test files | 47 | 19 |

Test identity under the Hardware QA route: 4 same-relative-path files, 1 exact blob+mode, 3 divergent, 43 source-only and 15 destination-only. Similar names are not treated as equivalent tests.

Firmware blobs remain different:
- ESP32 source `1412cf57b70c6ee3061da9831b8d9abf6d58d94e` vs destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 source `b99f1f21d8ad1e6df0e403b2b34507f97bd90c16` vs destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.

License/NOTICE identity:
- Experiments root `NOTICE.md` (`f6d92cd2`) is absent from the candidate.
- Tabler `LICENSE` (`22ee8122`) is absent from the candidate.
- Product LICENSE (`1ee55b94`), QRCode LICENSE (`150770c0`), TailAdmin LICENSE (`cb92d417`) and TailAdmin NOTICE (`f0425bbb`) have exact destination counterparts.
- BlazeRentalLauncher LICENSE (`c5b1efa7`) is on the separate RENTAL surface; it is not a Hardware subtree file.

COE #26 has no Hardware-specific `SOURCE_INTAKE.json` or `MIGRATION_MAP.md`. The existing PisoWiFi intake is not Hardware provenance and its summary 47/14 disagrees with the 61 runtime rows (46/15). Five COE #26 workflows remain QUEUED with zero jobs.

**Admission:** keep #26 FROZEN. No staging, copy, move, overwrite, cherry-pick, rebase or destination write. Require per-file source commit/path/blob/mode → destination path/blob/mode, licence/NOTICE, test identity and owner disposition, then exact-destination CI.

## 4. Other current owner PR / CI evidence

| Owner / PR | Exact current head | Evidence / disposition |
|---|---|---|
| CORE #252 | `c82705f2` | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; not financial acceptance. CORE scope left untouched. |
| RENTAL #328 | `10fc200b` | APK [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAILS at CORE CURRENT_STATE freshness and ESP32 core 4.0.0 missing `mbedtls/sha256.h`. |
| PISONET #255 | `d01fd164` | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not invoked. |
| HARDWARE #349 | `2a5c997a` | Quarantine [#45603969253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969253) and Relay [#45603968961](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603968961) PASS; Full [#45603969181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969181) FAILS at Missing poll signature check. |
| QA #290 | `5c29d159` | Synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked. |
| QA #292 | `75a3f66d` | No PR-triggered runs. |
| RELEASE #291 | `9b928c9e` | Windows [#45669599214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599214) and Full [#45669599438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599438) FAIL at `source/workflow changes newer than CURRENT_STATE.md`; ESP32 compatibility [#45669599322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599322) PASS. CORE owns canonical handover; RELEASE owns rerun. |
| COE RELEASE #35 | docs `1c08a339`; source/test `b3a7873e` | Shared [#45684703416](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45684703416): 230 PASS / 2 skips, then 10/10 ULA profile admission failures; sandbox [#45684703501](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45684703501): 40 host preflight PASS, Bubblewrap absent / exit 125; case guard [#45684704383](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45684704383) PASS. PR body still pins older docs/source heads `28da39c6` / `10f19a28`; RELEASE owns refresh. |
| COE CORE #45 | `9d76a134` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | `aeb8ff11` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) fails ESP32 compile at missing `mbedtls/sha256.h`; ESP8266 compile passes. |
| COE integration #26 | `b382d233` | Five workflows QUEUED / zero jobs; FROZEN. |

## 5. Registry, policy and execution limits

Experiments `AGENTS.md`, `BLAZE_CLOUD_ARTIFACT_POLICY.md`, `BLAZE_CLOUD_STORAGE_HANDOVER.md`, `README_FIRST` and the latest surfaced `COMMUNICATION_PROTOCOL` were read. The cloud policy requires exact source SHA, size and SHA-256 readback for Drive transfers and says to report BLOCKED if Drive access is unavailable.

No Google Drive connector is exposed in this runtime. Authorized Library search surfaced the 2026-11-09 checkpoint reference and 2026-10-26 sync-ledger snapshots, but not canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. No older snapshot was substituted; no private IDs/content were published. Registry status: **NOT RECOVERED / BLOCKED**.

Master ran exact recursive-tree, blob/mode, test identity and license comparisons as read-only GitHub API audits. Master product Python tests, `verify_coordination.py`, local native COM, hardware tests and Master GitHub Actions were NOT RUN; current Master head has zero workflow runs/statuses. Remote role CI above is not Master test execution.

## 6. Next owner actions

1. HARDWARE / MASTER / QA reconcile #353's captured base `6d743ae` against live #352 parent `0e984e2` before any stack integration; no rebase/retarget without owner authorization.
2. CORE publishes canonical CURRENT_STATE / PROJECT_HANDOVER and the authenticated poll/register producer contract. RELEASE then reruns #291 Full/Windows at that exact SHA.
3. CORE + HARDWARE + QA resolve the poll-signature assertion against the actual producer contract without weakening default-deny.
4. RELEASE refreshes COE #35's PR description to current docs/source pins; QA independently reviews the source/test change.
5. CORE / COE integration define approved site-scoped RFC4193 ULA /48 authority; RELEASE must not invent a prefix.
6. INFRA / COE provide an authorized disposable Bubblewrap-capable runner with unprivileged single-ID namespace support.
7. COE integration owner supplies Hardware-specific source intake, exact per-file provenance, matching license/NOTICE, test identities and destination CI before reconsidering #26.
8. Registry custodian restores authorized private v11 access.

Cleanup #266 remains OPEN / 0-of-7. CORE remains reserved to its separate continuation; no competing CORE work or source edits were performed.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory.
