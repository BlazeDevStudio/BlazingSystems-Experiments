# PHX-MASTER — QA evidence freshness and live CI audit

**Checkpoint:** 2026-11-16 UTC22  
**Role:** PHX-MASTER  
**Scope:** `coordination/phoenix/` only; coordination and evidence freshness, no subsystem source edits  
**Disposition:** DRAFT / PRODUCTION NO-GO

## 1. Exact live repository refs

| Ref | Exact observed commit |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Phoenix v0.5.3 development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Phoenix v0.6.0 audit foundation | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master draft PR #288 | `phoenix/master-coordination@9f05cf7eedb9a91f599504450520f59702ded91d` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft PR #26 | `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains open/draft, based on Experiments `main`. COE #26 remains open/draft, based on COE `main`. The two Phoenix development refs are distinct from `main`; neither is promoted by this audit.

## 2. QA recipient regression: source is fixed, QA evidence is stale

Current Master source readback:

- `coordination/phoenix/verify_coordination.py` Git blob: `3a6d0ca34cad54cd113abbda17d90898603547b3`.
- `coordination/phoenix/test_verify_coordination.py` Git blob: `28c9162c2bbd72f7d9587a6741f03f923999e575`.
- The current validator accepts exactly one registered PHX role or literal `ALL`; semicolon lists, unknown roles and whitespace variants are rejected.
- The current Master test file contains 21 test methods, including positive and negative recipient-contract cases.

QA draft PR #292 is still open/draft at head `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`, but its base is `b1ca02e2087f3b1a7169ceab9c34e52646e700df`. GitHub commit comparison confirms current Master HEAD is **55 commits ahead** of that base (0 behind). The QA report's 4/4 GREEN retest used older verifier blob `903df4034f8aa46f66e32de6e0be9b9ab2ca4b48`, not the current verifier blob `3a6d0ca...`. PR #292 has no PR-triggered workflow run at its current head.

**Disposition:** the historical QA RED and its later old-blob GREEN retest remain preserved, but neither is current-HEAD acceptance. The current Master source contains the recipient fix and corresponding tests; PHX-QA must rebase or reproduce against PR #288 HEAD `9f05cf7...`, hash the exact verifier/test blobs, and attach current-SHA evidence. Do not merge or label #292 VERIFIED on the strength of the older blob retest.

## 3. Current Master test inventory and execution boundary

The exact recursive Git tree at Master HEAD `9f05cf7...` contains these three Python test files:

| Test file | Git blob | Test methods |
|---|---|---:|
| `test_verify_coordination.py` | `28c9162c2bbd72f7d9587a6741f03f923999e575` | 21 |
| `test_verify_source_intake_manifest.py` | `c4b097930bf5deaebe0bf186b515f140161c1c93` | 11 |
| `test_snapshot_identity.py` | `f7fb30abe29169d8cdb2647a22ff80301b6fa143` | 6 |
| **Total authored methods** | | **38** |

This supersedes the older `18`-test count in the matrix. The method count is a source/tree inventory, **not** a test pass.

A targeted Python harness executed the current `validate_envelope()` function copied verbatim from verifier blob `3a6d0ca...`: **8/8 recipient cases passed** (known role, ALL, unknown role, mixed/ambiguous recipients, and leading/trailing whitespace). This was an extracted-function harness, not a full checkout or complete suite.

A full local checkout/test attempt was blocked because the runtime could not resolve `github.com` during `git clone`. No full 38-method suite or full `run_checks()` execution is claimed. Master PR #288 has no PR-triggered workflow runs at the observed HEAD.

## 4. Live role PR and CI snapshot

Workflow observations are exact-head, scoped software evidence only:

| Role | Draft PR / exact head | Observed workflow result |
|---|---|---|
| CORE | #252 / `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Run [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) completed success |
| RENTAL | #289 / `68928774d0d7cf65adb26bc6b54199a3159d066c` | Runs [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) completed success |
| PISONET | #255 / `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Run [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) completed success |
| HARDWARE | #314 / `556adc20ef0cfd355089aff3b979c0169af79bdd` | Runs [43782088731](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088731) and [43782088748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43782088748) completed success |
| HARDWARE | #315 / `953b743f3edc26671ddf7a457c2a4a4ac0de093f` | Runs [43963997471](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43963997471) and [43963997475](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43963997475) completed success |
| QA | #292 / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered workflow runs returned |
| QA | #290 / `5c29d15994cee1279058f1eca12f2a3180704292` | Run [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) completed success |
| QA | #267 / `ff5367990c2d27b8ebbb822ee208251af0c890e2` | Run [41452247439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41452247439) completed success |
| RELEASE | #291 / `2c4edff231d9b2819415086825530d80b8801307` | Run [43744993487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43744993487) completed success |
| MASTER | #288 / `9f05cf7eedb9a91f599504450520f59702ded91d` | No PR-triggered workflow runs returned |

COE integration #26 exact head `b382d233...` still has five queued workflows (case-collision, Pisonet Windows, Hardware/Shared, Rental, Pisowifi). COE stacked PR #30 at `8144242c0469ffc9fc7757ebe91964caa4a2a527` has one completed-success Pisonet workflow [43643411388](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43643411388); #30 is not #26 and does not clear #26's queue. None of these software runs is hardware acceptance or integrated production evidence.

PHX-MASTER did not edit CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branches. The separate CORE continuation remains outside this role's scope.

## 5. Private registry and blockers

The required private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were **not retrieved** in this activation: no Google Drive connector/read action was exposed to this run. No older Library registry was substituted, and no private Drive identifiers or contents were copied to GitHub.

Open actions:

1. PHX-QA: rebase/reproduce recipient tests against current Master HEAD `9f05cf7...`; run the complete current 38-method Master suite from an exact checkout and attach source/blob identities plus logs.
2. COE integration owner: reconcile the #26 source-intake summary (47/14 versus the previously audited 46/15 runtime entries), verify exact blobs/modes/licenses/imports/test identities, and resolve the five queued workflows.
3. Registry custodian: restore authorized private Drive read access or supply the v11 file through an approved secure route.
4. PHX-MASTER: refresh this snapshot on the next activation; do not infer acceptance from scoped green CI.

**Production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory and unverified.

No Codex, merge, release, firmware flash, physical test, secret provisioning, live payment operation or migration occurred.
