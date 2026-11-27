# PHX-MASTER UTC19 — Hardware fixture-runner correction, Release source-pin qualification, COE #26 provenance and branch-protection audit

**Date:** 2026-11-23 UTC19  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/master-coordination  
**Starting HEAD:** 88cf6a42fef138b0a3ddc9b723e3fe4dba63eca7  
**Base:** Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Execution:** Strict NO CODEX.

## 1. Live refs and ownership

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development: blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch: phoenix/master-coordination@88cf6a42fef138b0a3ddc9b723e3fe4dba63eca7.
- PR #288: OPEN / DRAFT / UNMERGED, 190 changed paths, all under coordination/phoenix/. Its 83,836-character description exceeds GitHub's body limit. The live update is therefore a PR conversation comment, not a destructive body replacement.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243, a 3-entry scaffold.
- COE integration #26: OPEN / DRAFT / UNMERGED at b382d233ff06c8791b1028bed3c617cc7b670d12, 205 changed paths.
- Cleanup #266 remains OPEN / 0-of-7.
- Ownership manifest OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

CORE remains with its separate owner/continuation. No CORE source branch, automation, or handover was edited.

## 2. HARDWARE #347 — corrected test/lab source and final docs head

Current PR #347 is OPEN / DRAFT / UNMERGED, child of #345 at ca72497ed386c9ac4e50d3f811827bef51e296ad.

| Evidence identity | Exact SHA |
|---|---|
| Firmware source anchor | 275057aa28375223a32da099420f52696d9b667c |
| ESP8266 sketch blob | fa8ed828026396db89aab2889bf6a61d6cf6bbac |
| ESP32 sketch blob | 717336b84d434d51eb24beac1ed8efce8e719f69 |
| Test/lab source HEAD | fc1bfe86e51e1446712915c69087dca5be8e0763 |
| Current PR/docs HEAD | 5260d433ca440ddb7526ec08519b00a7e6620eb5 |

Both current board sketch blobs were fetched at the current #347 docs head and independently compared with the firmware source anchor. ESP8266 and ESP32 blobs match exactly.

### Failed intermediate and correction

The first shared C++ fixture-runner refactor at 0bf7d9b53f6457e5e2a42514b0e4fb29f1ea7b1f removed the adjacent POLL_SAFETY_PARITY constants. Quarantine and Relay failed with a Python NameError in poll_loop_blocking_inhibit_lab.py. Hardware restored the constants in fc1bfe8; the failed intermediate is retained as a real failure, not relabeled PASS.

### Exact-head CI

**Corrected source/test head fc1bfe8:**
- [Quarantine #45252412144](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412144) — SUCCESS.
- [Relay #45252412350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412350) — SUCCESS.
- [Full #45252412053](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412053) — FAILURE.

**Final PR/docs head 5260d433:**
- [Quarantine #45253005056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253005056) — SUCCESS.
- [Relay #45253003611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253003611) — SUCCESS.
- [Full #45253005102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45253005102) — FAILURE. All 14/14 target/platform jobs succeed; validation fails at the inherited QA-owned Missing poll signature check; 12 dependent simulation/update/signing/candidate/publication stages are skipped.

**Owner action:** CORE must publish the approved authenticated register/poll producer contract and golden vectors. QA must independently reconcile its assertion only against that pinned contract. Do not synthesize a legacy signature field or weaken default-deny. Hardware retains ownership of its test/source branch.

## 3. RELEASE #291 — compatibility pass is narrower than full integration

RELEASE #291 is OPEN / DRAFT at docs head c5a566fd04a59a3c4a4bbbaa9524f8a9b97e6b7d; workflow source head 98ba3af1fe76128b331f93a4cf3543087cc0919b.

- [ESP32 compatibility #45209288305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288305) — 3/3 PASS against firmware source 275057aa.
- Current #347 ESP32 sketch blob is exactly the same 717336b84d434d51eb24beac1ed8efce8e719f69; the compatibility result remains source-exact for this ESP32 sketch.
- [Full #45209288533](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288533) and [Windows #45209288746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45209288746) FAIL at CORE-owned handover freshness.

This compatibility pass does not qualify ESP8266, test/lab code, or full integration. Do not demand a firmware repin solely because a test-only commit advanced; compare the exact sketch blob. Do not promote a narrow ESP32 compile pass into full-stack acceptance.

## 4. COE #26 — exact migration staging audit

Exact complete trees:
- Historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00: 2,391 entries.
- Current Experiments main: 2,340 entries.
- COE #26 destination: 286 entries.
- COE main: 3 entries.

All 61 runtime rows resolve against their recorded historical source and destination blobs and modes: 61/61 source blobs, 61/61 destination blobs, 61/61 modes. The computed row classification is **46 byte-identical / 15 derived**, while SOURCE_INTAKE summary says **47 / 14**.

Against current Experiments main, 33/61 historical source blobs remain identical, 20 differ, and 8 are absent. The historical intake commit and current main must not be silently conflated.

Test provenance:
- SOURCE_INTAKE lists 15 derived tests; MIGRATION_MAP contains 14 derived-test rows.
- tests/voucher_txn_journal.sh exists in the destination and intake but is absent from MIGRATION_MAP.
- MIGRATION_MAP records run_focus.sh blob fa1f4f2c6393504499d50659d8bf980caf7ff85b; actual destination blob is 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9.
- MIGRATION_MAP records member_txn_journal.sh blob 01dc9c65ae9d74eaafb403d47aebcd20edd14390; actual destination blob is d04df3c6f3ada60b9fda8c8c04230dd31e37019a.
- Destination voucher_txn_journal.sh blob is 4277a56af800b930135745bb942d62b6d580cb99.

License/NOTICE:
- First-party Pisowifi/LICENSE matches source blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- QRCode LICENSE and TailAdmin LICENSE/NOTICE match their source blobs.
- Source repository root NOTICE blob f6d92cd21465312be5993631fe26977219be0fb9 has no COE root counterpart.
- Source Tabler LICENSE blob 22ee8122400915cbff18e5f69368fa9eea6145eb and Android Launcher LICENSE blob c5b1efa7aac764ae6d8da63476a2d5cec02a6a5d have no reviewed destination counterparts at their expected mapped paths.

Five #26 workflows remain QUEUED with zero jobs. **Decision: FROZEN.** No staging, copying, moving, overwriting, cherry-picking, rebasing or retargeting. COE owner must reconcile the summary, test inventory, stale blobs, and license/NOTICE gaps before exact-head CI and independent review.

## 5. COE RELEASE #35 and other owner PRs

COE RELEASE #35 is OPEN / DRAFT at docs head be3d3e5aa2c91551b26b9018191743213e60a402, source/test head 1a9210d2b21eed4dfcc71f128bbbea8d1da79e70.

- [Shared #45246282016](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45246282016): 203 packaging/tool tests PASS / 2 intentional skips, then 10/10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is undefined; ESP32/ESP8266 compiles are skipped.
- [Sandbox #45246281947](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45246281947): host preflight 40/40 PASS, then Bubblewrap is absent (exit 125); unprivileged identity, namespace and mandatory sandbox packaging tests are skipped.
- [Case collision #45246281935](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45246281935): PASS.

Other exact owner candidates:
- CORE #252 c82705f2: Build PASS.
- RENTAL #328 0e0da62a: APK identity/API smoke PASS; build FAIL.
- PISONET #255 d01fd164: Windows Release PASS.
- QA #290 5c29d159: Windows PASS; QA #292 75a3f66: no exact-head runs.
- COE #45 9d76a134: Overlay/Shell + case PASS.
- COE #49 aeb8ff11: Stage 5.1 + case PASS; Shared Contracts compile FAIL.
- HARDWARE #346 remains a stale sibling at bd3fd6e, with no exact-head runs.

## 6. Branch protection and source-of-truth documentation

Live branch metadata reports protected:false for Experiments main, development, Master coordination, and COE main. Rulesets reads return empty lists for both repositories. The classic branch-protection detail endpoint returns 403 to this integration. No protected required-check enforcement is evidenced. Repository owner/admin must establish branch protection and required checks before integration.

Documentation conflict:
- Experiments main product README blob 7990e2ecbab06cafa5f8227050929e16fff1f4a1 says current production release **0.3.0**.
- Main PROJECT_HANDOVER blob f86c0ae9b14853963b8a9b835e1100eb5178d1a6, last updated 2026-10-07, says production is frozen at **v0.5.2**.
- Development PROJECT_HANDOVER blob 0430f421f705451b2c94cf9a97d2cf02398e9657, last updated 2026-10-06, also says v0.5.2.
- GitHub Release [v0.5.2](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/releases/tag/v0.5.2) exists and targets candidate bf2992977fe8504d21b107df02826032c31d3a62; release metadata reports immutable=false.

Master did not edit product README or historical handover files. The repository owner must reconcile the canonical release identity and update the correct product-owned entry point with verified release evidence.

## 7. Registry and storage boundary

Root AGENTS.md, the public Cloud Artifact Policy and public Storage Recovery Handover were read. The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the current Google Drive/Library connection. Only older v3/v5/v6 Library snapshots surfaced; none was substituted. No private registry contents or IDs were published and no Drive artifact was created.

## 8. Validation and disposition

Executed static JavaScript checks:
- Recomputed all 61 runtime status rows and source/destination blob/mode identities.
- Recomputed 33 same / 20 different / 8 missing current-main source comparisons.
- Compared 15 derived-test entries against MIGRATION_MAP and destination blobs.
- Compared both current Hardware board sketch blobs against the pinned firmware source anchor.
- Read exact workflow logs for the Hardware fixture-runner failure/correction and COE #35 ULA/Bubblewrap blockers.

Not executed:
- Full Master Python suite.
- verify_coordination.py.
- Master PR Actions (zero runs/statuses on starting head).

No subsystem source, firmware, tests, payment code, or COE destination file changed. Only PHX-MASTER coordination documents are updated. No merge, release, signing, secret provisioning, flashing, physical test, payment operation, customer cutover or financial migration occurred.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates are independently evidenced.
