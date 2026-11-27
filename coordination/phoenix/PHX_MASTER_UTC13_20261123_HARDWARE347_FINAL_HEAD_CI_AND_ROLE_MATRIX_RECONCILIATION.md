# PHX-MASTER UTC13 — Hardware #347 final-head CI and live role matrix reconciliation

**Observed:** 2026-11-23T13:42:41Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, cross-repository migration provenance and integration matrices only.  
**Execution:** Strict NO CODEX. Connected GitHub and ordinary JavaScript validation only.

## 1. Exact repository refs

| Ref | Exact SHA / state |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| PHX-MASTER start | `phoenix/master-coordination@9f04ece155d2a7f58753521645d16042ae52dbaa` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership manifest | `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29` |

Experiments default branch is `main`; development branch is the v0.5.3 development ref above. COE default branch is `main`. The current Master branch API metadata reports `protected=false`; this connector read does not establish administrator-enforced required checks.

PR #288 was OPEN / DRAFT / UNMERGED at audit start, based on Experiments main, with 188 changed paths, all under `coordination/phoenix/`. No Master PR-triggered workflow run or combined status was returned at the starting head.

## 2. Primary finding — Hardware #347 current test-source anchor is stale

The Hardware owner has reconciled the configured coin-ingress candidate onto the current #345 parent without rebasing or force-pushing stale sibling #346.

| Item | Exact ref |
|---|---|
| Parent #345 HEAD | `ca72497ed386c9ac4e50d3f811827bef51e296ad` |
| Reconciled child #347 base | `ca72497ed386c9ac4e50d3f811827bef51e296ad` (exact parent match) |
| #347 current HEAD | `275057aa28375223a32da099420f52696d9b667c` |
| Earlier handover/docs HEAD | `c7ab3601e7af8c33f78ad49a2d073567ab5c6ebb` |
| Earlier declared test-harness SHA | `724d892e980f878903425837226c45b321638793` |
| Stale sibling #346 | `bd3fd6e85717395f768aae26a310b647cdd72a7e`, based on `797dece76c18d464a7c0580658b5db9351cb8e15` |

The current #347 PR body still says no firmware/test source changed after `724d892...` and identifies `c7ab360...` as the current PR/docs head. The actual current PR API head is `275057aa...`; its final commit changes exactly one file: `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_clear_failure_lab.py`. Therefore the PR body’s test-source anchor is stale. This final commit does not modify firmware runtime code, but it does modify a test/lab source and must be represented in the test lineage. PHX-HARDWARE owns the PR description and handover correction; Master did not edit #347.

### Exact-head CI at #347 HEAD `275057aa...`

| Workflow | Run | Result |
|---|---|---|
| Quarantine Byte Readback | [#45186057750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057750) | **PASS** |
| Relay Output Polarity | [#45186057806](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057806) | **PASS** |
| Full BlazePwifi build | [#45186057891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057891) | **FAIL** |

The three run records independently report `head_sha=275057aa...`. Full validation job `137731998988` fails in `tests/controllers.sh` with `Missing poll signature check` in the ESP8266 sketch. All 14 firmware/platform/Android target jobs completed successfully, but validation-dependent simulation, update-bundle, signing and publication stages were skipped. This is not Full acceptance.

The #345 parent’s exact-head Quarantine [#45165015610](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45165015610) and Relay [#45165015665](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45165015665) pass; Full [#45165015859](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45165015859) fails at the same QA-owned poll-signature assertion. #346 has no workflow runs at its exact head. Do not inherit #345 or #347 evidence into #346.

**Ownership:** HARDWARE owns #345/#346/#347 firmware and labs; QA owns the inherited assertion and independent verification; CORE owns the authenticated register/poll producer contract. Do not fabricate a positive legacy signature or weaken default-deny behavior.

## 3. Current role PR / CI matrix

| Role / candidate | Exact current head | Exact-head evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS (scoped). CORE remains separately owned. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [APK identity #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; [API smoke #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; [build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS (scoped); native COM acceptance NOT TESTED. |
| HARDWARE #345 | `ca72497ed386c9ac4e50d3f811827bef51e296ad` | Quarantine/Relay PASS; Full FAIL at poll-signature assertion. |
| HARDWARE #346 | `bd3fd6e85717395f768aae26a310b647cdd72a7e` | No exact-head runs; stale sibling. |
| HARDWARE #347 | `275057aa28375223a32da099420f52696d9b667c` | Quarantine/Relay PASS; Full FAIL at poll-signature assertion. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [Windows #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS (scoped). |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No current-head workflow runs. |
| RELEASE #291 | `cc0192722cface63bcf5c2e5149b485ade83f41e` | [ESP32 compatibility #45183560775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45183560775) PASS; [Windows #45183560782](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45183560782) FAIL; [BlazePwifi build #45183560872](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45183560872) FAIL. |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs; FROZEN. |
| COE #35 | `4234ee00b1fbb02167b3c99853d4143a4a0550e` | [Shared/firmware #45174042588](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45174042588) FAIL; [Sandbox #45174042599](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45174042599) FAIL; [Case collision #45174042568](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45174042568) PASS. |
| COE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Scoped Overlay/Shell and case-collision checks PASS. |
| COE #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 and case-collision PASS; Shared/firmware compile FAIL. |

## 4. COE migration and routing

The machine manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. Experiments main remains the source baseline; COE #26 remains a frozen draft candidate, not an approved destination.

Previously verified #26 provenance discrepancies remain unresolved: SOURCE_INTAKE runtime rows classify 46 identical / 15 derived while the summary says 47 / 14; the derived-test list has 15 entries while the migration map has 14, including an omitted voucher journal and two stale test blob IDs; 28 of 61 historical source blobs have drifted from current Experiments main; root NOTICE and other license/NOTICE coverage remain incomplete. Five destination workflows are queued with zero jobs.

COE #35 remains blocked because ten appliance profiles fail closed without approved site-scoped ULA /48 authority and the runner lacks Bubblewrap. No network prefix or sandbox bypass was invented.

No source/destination file was staged, copied, moved, overwritten, cherry-picked, rebased, retargeted or promoted. No destination write occurred.

## 5. Governance and execution limits

- Cleanup #266 remains OPEN, 0/7; the broad Master duplicate/dead-code cleanup inventory is incomplete.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available. Library search returned a 2026-11-09 checkpoint that references v11 as a previous canonical registry, plus older v6/v7 snapshots; none is the canonical v11 file. No Google Drive connector is exposed. No older snapshot was substituted and no private IDs/contents were published.
- The uploaded Master directive, README_FIRST, BLAZE-COMMS/1, root AGENTS.md and current coordination documents were re-read. Experiments main/development/Master and COE main branch refs report `protected=false` in branch metadata; effective required-check enforcement is not established by this connector read.
- Master Python suite and `verify_coordination.py` were NOT RUN because no authenticated local checkout was available. The exact-head role CI above is not a Master-suite pass.
- CORE remained with its separate owner; no CORE branch/source edit or competing CORE task was started.

## 6. Next owner actions

1. PHX-HARDWARE refresh #347's own PR body/handover: identify `275057aa...` as the current test-source head and attach the three exact-head runs.
2. PHX-QA and PHX-CORE reconcile the inherited poll-signature assertion against the approved authenticated producer contract; do not add a positive legacy signature.
3. COE RELEASE/infra obtain approved site-scoped ULA /48 authority and a trusted Bubblewrap-capable disposable runner; rerun #35 at its exact head.
4. COE integration owner correct SOURCE_INTAKE/MIGRATION_MAP counts, omitted/stale test entries and license/NOTICE coverage; keep #26 frozen until exact-head CI and owner review.
5. Registry custodian restore authorized read-only access to canonical private v11 and newer corrections.
6. Human test runner execute the full Master suite and `verify_coordination.py` at the final #288 head.

**Final disposition:** coordination-only; PR #288 remains OPEN / DRAFT / UNMERGED; no subsystem source changes; no COE destination changes; no migration; **PRODUCTION NO-GO**.
