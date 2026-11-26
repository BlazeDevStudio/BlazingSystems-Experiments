# PHX-MASTER UTC09 — cross-role route provenance and HARDWARE #354 exact-head CI

**Observed:** 2026-11-26T10:00:41.993Z  
**Role:** PHX-MASTER — master coordination, interface contracts and migration provenance only.  
**Mode:** Strict NO CODEX.  
**Starting Master branch / PR #288 HEAD:** `59cc5ca71e615fa9a732ad3b8a26fbf0762388b2`  
**Production disposition:** **NO-GO**.

## 1. Live repository and control-plane refs

- Experiments main: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`
- Development `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5`
- Comparison-only v0.6 base: `2fbd2475e9f54878c316fa7cea2f228386b0e859`
- Master branch / PR #288: `59cc5ca71e615fa9a732ad3b8a26fbf0762388b2`
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`
- COE integration #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`
- PR #288 was OPEN / DRAFT / UNMERGED with 231 changed paths, all under `coordination/phoenix/`; compare main...Master was 606 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Cleanup #266 remains OPEN / 0 of 7. Ownership manifest blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains 11 routes / `DRAFT_REVIEW_ONLY` / PHX-MASTER destination null.

## 2. HARDWARE #354 — current exact-head result

Current PR/docs head `e7f63da29b8b27ff2143aebc128e63f9789b0ad2`; source/test commit `87ef824d7d4dd88c712da1a690a3ebb30989ac86`. The docs-only follow-up records the shared source-extractor lab result; production sketches/runtime behavior were not changed in that follow-up.

- Focused extractor/output sequence [#45795418063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45795418063): PASS; source extractor, both board output-order scenarios and 4/4 output-enable checks pass.
- Mbed TLS 3/4 matrix [#45795418284](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45795418284): PASS; source-contract, Arduino core 3.3.13 and 4.0.0 legs pass.
- Native [#45795418477](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45795418477): FAIL at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which requires active `clearPending(true/false)` callsites. The deny-only candidate intentionally has no active pending-disposition callsite and preserves pending evidence.
- Full [#45795418386](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45795418386): terminal FAILURE at QA-owned Controller protocol parity / `config_revision` expectation. ESP32, ESP8266, all listed firmware targets and Android pass; simulations, update bundle, candidate gate, signing and publication are skipped after validation fails.
- The current Hardware PR description now pins `e7f63da`. No physical GPIO/relay/electrical, coin acceptance, LittleFS power-loss, 150 power-cut or 30-device/24-hour soak evidence exists.

**Ownership:** QA updates its assertions; CORE supplies the authenticated poll/register and receipt/disposition contract; Hardware owns its source and handover. Master does not modify those files.

## 3. Exact current-owner source route comparison to COE #26

Complete recursive Git trees were read at each owner PR head and at COE #26; every tree returned `truncated=false`. Comparisons below use exact relative path, blob SHA and mode. They are not copy authorization.

| Owner source / route | Source | Destination | Common | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| CORE #252 `c82705f2` — rootfs library | 20 | 20 | 20 | 13 | 7 | 0 | 0 |
| CORE #252 — vendo CGI | 1 | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL #328 `10fc200b` — Android | 994 | 8 | 0 | 0 | 0 | 994 | 8 |
| RENTAL #328 — standalone profile / broad Rental target | 30 | 19 | Manual mapping required | — | — | — | — |
| RENTAL #328 — Rental Server | 12 | 4 | 1 | 0 | 1 | 11 | 3 |
| PISONET #255 `d01fd164` — SoftTimer | 68 | 47 | 38 | 27 | 11 | 30 | 9 |
| HARDWARE #340 `f70f6af7` — ESP32 | 9 | 1 | 1 | 0 | 1 | 8 | 0 |
| HARDWARE #340 — ESP8266 | 6 | 1 | 1 | 0 | 1 | 5 | 0 |
| HARDWARE #353 `cb1787ac` — ESP32 | 16 | 1 | 1 | 0 | 1 | 15 | 0 |
| HARDWARE #353 — ESP8266 | 67 | 1 | 1 | 0 | 1 | 66 | 0 |
| HARDWARE #354 `e7f63da2` — ESP32 | 4 | 1 | 1 | 0 | 1 | 3 | 0 |
| HARDWARE #354 — ESP8266 | 8 | 1 | 1 | 0 | 1 | 7 | 0 |
| QA #290 `5c29d159` — tests | 145 | 19 | 4 | 2 | 2 | 141 | 15 |
| RELEASE #291 `bf339a76` — build workflow | 1 | 1 | 1 | 0 | 1 | 0 | 0 |

The standalone Rental profile route is explicitly manual-file-mapping-required because its broad target overlaps other routes. The RELEASE workflow is a reimplementation review, not a direct-copy route. The routing manifest still has 11 routes, global source_ref `f4e8a891`, destination candidate `b382d233`, and Master target null; it does not pin the current per-role PR heads above.

## 4. Historical COE #26 rootfs intake — source-grounded correction

- `SOURCE_INTAKE.json` is pinned to historical source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`. Its recorded rootfs subtree `f4a923aaacf1374e90c7bab5f335efe6c6ec55cf` and tests subtree `7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17` were verified against the actual historical Git tree.
- The 61 runtime rows' source and destination blob identities all match the pinned source and current COE #26 destination tree. Current destination has 62 rootfs files: the 61 mapped rows plus destination-only derived `usr/sbin/blaze-appliance-diag` (blob `6690c739`).
- **Summary mismatch:** the intake summary says 47 byte-identical / 14 locally derived. Its 61 runtime row statuses are 46 `byte_identical` / 15 derived-cleanup-review. `MIGRATION_MAP.md` records 46 copied unchanged, 13 intentionally edited and 2 locally derived (46 exact + 15 non-identical). Correct the summary; do not change the row-level evidence.
- The intake records destination head `cf59b41e` before its manifest, while current #26 is `b382d233`; all 61 recorded destination blobs still match the current tree. The map header names historical branch `feature/pisowifi-cleanup-stabilization`, not the current PR branch `integration/ecosystem-nonproprietary-candidate-20261111`.
- The historical intake is not the current owner-branch matrix: current QA #290 has 145 test blobs versus 19 in COE #26 (4 common paths, 2 exact, 2 divergent, 141 source-only, 15 destination-only). The intake's 4 original-test rows plus 15 derived tests do not establish current QA route completeness.
- Product MIT license is exact: source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` both blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root `NOTICE.md`, Tabler LICENSE and BlazeRentalLauncher LICENSE have no destination counterpart. QRCode and TailAdmin license/notice counterparts match.
- Intake flags remain `release_authorized=false`, `hardware_tested=false`, `full_ci_tested=false`, `source_admission_complete=false`.
- COE #26 is OPEN / DRAFT at `b382d233`, 205 changed files; its five PR-triggered workflows remain queued with zero jobs. Its migration-plan 95% readiness narrative is not current exact-head CI or physical-acceptance evidence.

**Decision:** #26 remains FROZEN. No destination staging, copying, moving, overwriting, cherry-picking or writes. The COE integration owner must correct the summary, separately classify the diagnostic addition, refresh per-role source pins, and reconcile current QA/Android/Rental/Pisonet/Hardware routes before requesting review.

## 5. Governance, access and test classification

- Experiments main, development, Master and COE main branch objects report `protected=false`; both repository ruleset lists are empty. Effective required-check enforcement is NOT ESTABLISHED.
- Cleanup #266 remains OPEN / 0-of-7.
- Canonical private Drive registry v11 and newer corrections were NOT_RECOVERED. No Google Drive connector is exposed; older Library snapshots were not substituted and no private contents or IDs were published.
- Master executed GitHub exact-head reads, non-truncated tree reads, blob/mode comparisons, historical intake hash checks and static consistency assertions. Master Python unittest suite and `verify_coordination.py` were NOT RUN because no authenticated local checkout is available. The starting Master head has zero GitHub Actions runs and zero combined statuses.
- No subsystem source, COE destination, manifest, signer, secret, financial state, hardware, release artifact or customer/payment state changed.

## 6. Required next actions

1. **PHX-QA:** replace the two #354 legacy assertions with deny-only / no-callsite / pending-evidence-preservation checks.
2. **PHX-CORE:** publish the authenticated register/poll and receipt/disposition contract.
3. **PHX-HARDWARE:** retain the exact #354 source/docs/CI handover and rerun Full after QA correction.
4. **COE integration owner:** correct 47/14 to the 46/15 row evidence, record the diagnostic addition separately, pin per-role source SHAs, and reconcile the 145-test QA and other route gaps.
5. **COE-RELEASE / infrastructure:** obtain approved site-scoped ULA /48 authority and a Bubblewrap-capable sandbox; no invented prefix or sandbox bypass.
6. **Registry custodian / repository administrator:** restore v11 access and establish effective protected branches/required checks.

**PRODUCTION NO-GO** remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.
