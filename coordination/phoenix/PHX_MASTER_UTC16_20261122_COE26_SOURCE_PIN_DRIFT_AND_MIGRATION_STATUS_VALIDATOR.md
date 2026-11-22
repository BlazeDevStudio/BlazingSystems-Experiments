# PHX-MASTER UTC16 — COE #26 source-pin drift and migration-status validator hardening

**Updated:** 2026-11-22T16:33:45Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance only  
**Task:** PHX-MASTER-UTC16-COE26-SOURCE-PIN-RECONCILIATION  
**Disposition:** COE #26 FROZEN · SOURCE BASELINE STALE · SUMMARY COUNTER MISMATCH · VALIDATOR HARDENED · PRODUCTION NO-GO

## 1. Exact live refs and ownership

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Active v0.6 development/audit branch: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- PHX-MASTER pre-update HEAD: `phoenix/master-coordination@2dd7de41bfc6068057ece48f2d03e347a2b2b76e`; parent `63342787fc1e55a7a55289ef7bff5e8e36493c5e`; base `main@f4e8a891...`.
- Experiments PR #288: OPEN / DRAFT / UNMERGED.
- COE default branch: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`; source ref is Experiments `f4e8a891...`; destination candidate is COE #26 `b382d233...`; PHX-MASTER target is null.

No subsystem source branch or COE destination was changed. CORE was inspected only; its implementation ownership remains separate.

## 2. Exact COE #26 migration source-pin reconciliation

At COE #26 exact head, the destination candidate contains:

- `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9`.
- `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`.
- Both documents pin source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` (2026-10-28), project root `experiment/openwrt/BlazePwifi`.

The route manifest's current source ref is `f4e8a891...`, not the older `6d4c9b...` pin. Exact recursive-tree/blob comparison of the 61 recorded rootfs paths found:

| Comparison | Exact result |
|---|---:|
| Recorded source blobs match the pinned 6d4c9b tree | 61/61 |
| Recorded destination blobs match COE #26 tree | 61/61 |
| MIGRATION_MAP rows match SOURCE_INTAKE runtime paths and both blob fields | 61/61 |
| Recorded source blobs still match current Experiments main f4e8 | 33/61 |
| Current-main paths with changed blobs | 20 |
| Recorded paths absent from current main | 8 |

The 20 changed and 8 absent paths are source-baseline drift, not an instruction to copy, delete, or restore files. The old candidate is internally pinned to its 2026-10-28 source snapshot, but it is not a complete provenance statement for the current route-manifest source ref. Any refresh requires owner review of each changed/absent path, licenses/notices, test identities, import completeness, and exact-head CI. No staging or destination edit is authorized by this audit.

### Migration table / intake summary discrepancy

The exact 61-row rootfs table classifies:

- 46 `copied unchanged` rows with identical source/destination blobs;
- 13 `intentionally edited` rows with divergent blobs;
- 2 `locally derived` rows with divergent blobs.

Therefore the table's recorded Git blob identities compute **46 byte-identical / 15 derived**. `SOURCE_INTAKE.json.summary` instead claims **47 byte-identical / 14 derived**. The path and blob records are 61/61 aligned, but the summary counters are off by one in opposite directions. The candidate verifier's existing `test_observed_61_row_off_by_one_is_reported` covers this exact 61-row 47/14-vs-46/15 discrepancy; the actual candidate remains unverified by a local full-checkout run.

The intake also records `source_admission_complete=false`, `release_authorized=false`, `hardware_tested=false`, and `full_ci_tested=false`. These explicit false gates remain in force.

## 3. Master-owned migration-status validator improvement

The current `coordination/phoenix/verify_migration_map.py` matched recognized status labels as arbitrary substrings. A status such as `note: copied unchanged; source retained` was accepted when the blobs were identical, even though the classification was not the row's leading status. A contradictory row containing more than one classification was not reported as an ambiguous status.

A narrow Master-owned fix now requires exactly one recognized classification, requires it to occur once and lead the status field, and then applies the existing blob-equality rules. No COE data or subsystem code was modified.

**Test-first evidence using exact GitHub-fetched source/test contents in an isolated local Python harness:**

- Baseline: 10/10 existing tests PASS.
- Added two regression cases; RED: 2 expected failures (embedded/non-leading classification and contradictory classification).
- After the parser change: 12/12 tests PASS.
- The candidate table's 61 real status strings were separately parsed remotely; all begin with one recognized classification. This is static source inspection, not GitHub Actions or a full COE checkout test.

The full Master coordination suite, `verify_coordination.py`, and a full local execution against the COE candidate files remain NOT RUN. No Master PR-triggered Actions run was returned.

## 4. Exact owner PR / CI reconciliation

| Owner | Exact head | Exact-head evidence / disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | BlazePwifi build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS. No CORE source change by Master. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS mandatory handover freshness and ESP32 compile (`mbedtls/sha256.h` missing). RENTAL owns repair. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows release [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native adapter acceptance NOT TESTED. |
| HARDWARE #327 | `fadac4ed3bc837cf729753264b9427fa3fd312b9` | Relay [#45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) and Quarantine [#45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) PASS; aggregate [#45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) FAIL. |
| HARDWARE #342 | `e7815297b1a8780b7868bc9b28f45011ec419dce` | Quarantine [#45043657779](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657779) PASS; Full [#45043657792](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657792) FAILS at inherited `Controller protocol parity` (job `137273456792`, `Missing poll signature check`). Fourteen target/platform jobs PASS; validation fails and downstream signing/candidate/publish jobs are skipped. QA owns the assertion; firmware remains default-deny. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 has no PR-triggered runs. |
| RELEASE #291 | `42797e2f3d65c30a1070caf49c93aebec149d897` | ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL at mandatory handover freshness. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Receipt contract [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; contract-only, runtime DENY. |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage-specific [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; shared compile [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAILS ESP32 at missing `mbedtls/sha256.h`. It does not update #26's firmware/test. |
| COE RELEASE #35 | `e4701146a3c426699329a52227cba20fcfd53034` | Case guard [#45043451538](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45043451538) PASS. Shared validation [#45043451514](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45043451514) runs 188 tests (2 skipped), then all ten profiles fail closed for missing approved site ULA /48. Sandbox [#45043451623](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45043451623) runs 35 host tests PASS, then fails exit 125 because Bubblewrap is absent. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five queued workflow names; zero jobs. FROZEN. |

## 5. Cleanup and private registry

Cleanup issue [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN; its seven role checkboxes remain incomplete. Hardware posted one UTC16 cleanup increment on #342, but this does not complete the Master track or the seven-role gate. Master made no deletion, mass move, rename, or subsystem cleanup change.

The repository `AGENTS.md` requires the private Drive registry, artifact manifest, sync ledger, cloud artifact policy and recovery handover. The connected tool set exposes no Google Drive connector; the canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not retrievable from the Library. Older v3–v7 snapshots and a November 9 filename reference are not substitutes. The linked canonical policy/handover repository could not be fetched through the connected GitHub file interface. No private Drive IDs or registry data were published.

## 6. Next exact actions

1. Registry custodian: restore authorized read access to canonical Drive v11 and newer corrections.
2. COE owner + subsystem owners: keep #26 frozen; reconcile the 47/14 summary to the actual 46/15 blob counts and re-pin/review the 61 paths against current Experiments main f4e8. Review all 20 changed and 8 absent paths individually; do not infer copy/delete actions.
3. PHX-QA: correct the inherited poll assertion using source-linked negative/default-deny tests; do not weaken firmware behavior.
4. PHX-CORE: maintain the versioned producer contract under its separate owner; no Master takeover.
5. PHX-RELEASE: obtain approved site ULA /48 authority and a trusted Bubblewrap-capable runner.
6. Human runner: restore authenticated GitHub network access and execute the full Master coordination suite against the resulting exact HEAD.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No subsystem source, COE destination, private registry, secret, signer, payment system or hardware device was modified or used. No merge, release, signing, secret provisioning, firmware flash, financial migration, physical test or production approval occurred.
