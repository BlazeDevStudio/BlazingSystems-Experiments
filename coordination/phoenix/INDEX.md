# Project Phoenix — Coordination Index

**Updated:** 2026-11-20T12:39:46Z  
**Role:** PHX-MASTER — coordination / architecture / integration provenance only  
**Safety:** DRAFT REVIEW ONLY · PRODUCTION NO-GO

## Start here — authoritative live sources

1. [Control plane issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) — canonical role inbox, assignments and BLAZE-COMMS/1 checkpoints.
2. [Cleanup-first issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) — seven-role cleanup checklist. The Master inventory remains incomplete; do not treat the checklist as proof of cleanup.
3. [Phoenix Master draft PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) — Master-owned coordination branch only.
4. `OWNERSHIP_ROUTES.json` — machine-readable draft routing; current blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, Master destination `null`.

## Canonical live documents

| File | Purpose |
|---|---|
| `ARCHITECTURE_CONTRACTS.md` | Cross-subsystem invariants and candidate interface gates; current Remote CS review gate is §6.55. |
| `ROLE_ASSIGNMENTS.md` | Current owner/PR heads, scope boundaries and next owner actions. |
| `INTEGRATION_MATRIX.md` | Exact source/destination heads and CI dispositions. |
| `AUDIT_SUMMARY.md` | Current blockers and release-readiness disposition. |
| `REPOSITORY_ROUTING.md` | Human-readable routing and manual-review restrictions. |
| `OWNERSHIP_ROUTES.json` | Machine-readable routes; do not modify without exact per-file provenance and owner review. |

## Verification tools

- `verify_coordination.py` / `test_verify_coordination.py`
- `verify_migration_map.py` / `test_verify_migration_map.py`
- `verify_source_intake_manifest.py` / `test_verify_source_intake_manifest.py`
- `test_architecture_contracts.py` and `test_snapshot_identity.py`

Run the repository's actual test suite from an authenticated checkout at the exact branch SHA. A static document/manifest check or a scoped subsystem CI run is not a full Master-suite result.

## Append-only audit reports

Timestamped `PHX_MASTER_*.md`, subsystem audits, and migration-gate reports are immutable historical evidence. They are **not** the current source of truth when their exact SHA differs from the live branch/PR API. Start with the four canonical live documents above, then open the newest report only for the issue under investigation. Do not mass-delete or rename older reports; first inventory inbound links and consumers.

## UTC04 cleanup-first inventory

- Coordination tree at the audited Master head: 116 files (105 `.md`, 3 `.json`, 8 `.py`).
- Exact duplicate blob SHA count: **0**.
- Architecture-contract numbered heading collisions: §6.9, §6.10, §6.11, §6.12, §6.25, §6.32. No renumbering performed because references have not been fully inventoried.
- No source files, test files, route manifest, or historical report were deleted or moved.

## Live refs at the UTC04 audit

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`
- v0.5.3 development: `aad3aade72c1156eecba1fed30907c6d0283b2c5`
- v0.6 audit-foundation: `2fbd2475e9f54878c316fa7cea2f228386b0e859`
- Master branch at UTC04:39 audit start: `5d96b2df6351788613dfc49d4a246637f7b23f64`
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`
- COE integration PR #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, 205 paths, five queued workflows / zero jobs.

## Standing gates

No route promotion, source migration, merge, release, signing, secret provisioning, hardware flash, customer payment, or physical test is authorized by this index. Production remains NO-GO pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.

## Latest exact-head reconciliation — 2026-11-20 UTC04:39

- [Hardware stack and terminal CI audit](PHX_MASTER_UTC04_20261120_HARDWARE_STACK_AND_RELEASE_TERMINAL_CI_RECONCILIATION.md).
- Active Hardware child #327: docs head b6304208d65548a9cfe371504badf03ae3e15dcf, source/test 2f89326d5b555ffdb2bfaba0a404483d665aa614, base #326 58c558fb6a237935214621adc3dee65a10fe1a51.
- Release #291: BlazePwifi full CI #44673292595 PASS with production signing/publishing skipped; ESP32 reproducibility #44673292516 FAIL on both cores; Windows #44673293276 FAIL.
- COE #26 remains frozen at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows / zero jobs.
- No source migration, ownership transfer, route promotion, merge, release or hardware acceptance.

## Latest exact-head reconciliation — 2026-11-20 UTC05

- [UTC05 Release reproducibility and COE #26 audit](PHX_MASTER_UTC05_20261120_RELEASE_REPRODUCIBILITY_AND_COE26_EXACT_HEAD_AUDIT.md).
- Master branch at audit start: \`phoenix/master-coordination@2a2f6bf0926676250aed007c1a001605173bb6c0\`; PR #288 was OPEN/DRAFT against main \`f4e8a891aed8af86d5fd315d28750a0ac3a7372b\`, with 119 changed paths, all under \`coordination/phoenix/\`.
- Active v0.6 audit-foundation ref: \`2fbd2475e9f54878c316fa7cea2f228386b0e859\`; legacy v0.5.3 ref: \`aad3aade72c1156eecba1fed30907c6d0283b2c5\`.
- RELEASE #291 docs head \`8d0c975816569849118c95637078cc29509ef3a0\`: strict reproducibility [#44681557945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557945) fails on both ESP32 cores; Windows [#44681557650](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557650) fails in PISONET-owned \`$buildWorkflow\`; BlazePwifi [#44681557828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557828) subsequently terminated SUCCESS: 26 jobs passed, 0 failed, and 4 production import/sign/publish jobs were skipped.
- HARDWARE #327 docs head \`b6304208d65548a9cfe371504badf03ae3e15dcf\`: focused quarantine/relay runs pass; Full [#44675789227](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675789227) fails at QA-owned \`Missing poll signature check\`.
- COE #26 remains frozen at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`, five queued workflows / zero jobs. COE #49 remains separate audit-only; COE #35 remains blocked by missing site ULA authority and unavailable Bubblewrap.
- Private v11 registry/newer corrections remain BLOCKED; no older snapshot was substituted. Issue #266 remains OPEN and the Master cleanup checkbox remains unchecked.


### Terminal BlazePwifi full-build supersession — 2026-11-20T05:37Z

The exact docs-head [#44681557828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557828) completed after the initial readback: **26 successful jobs, 0 failed, 4 skipped**. Validation, Android, all firmware/platform targets, update bundle and all six v0.4 simulation jobs passed. The four skipped jobs are production signed-APK import, production sign handoff, release publication and prerelease publication. This is a terminal successful hosted build/simulation result only; it does not clear the still-failing two-core reproducibility run [#44681557945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557945) or Windows self-test [#44681557650](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557650). No signing or publishing occurred. **PRODUCTION NO-GO.**


## Latest live audit — 2026-11-20 UTC07

- [PHX_MASTER_UTC07_20261120_HW327_STACK_COE26_SOURCE_PROVENANCE_AND_ROLE_CI_AUDIT.md](PHX_MASTER_UTC07_20261120_HW327_STACK_COE26_SOURCE_PROVENANCE_AND_ROLE_CI_AUDIT.md) — corrects #323/#326 ancestry, reconciles #327 exact-head CI and role PRs, and records exact Hardware source-vs-COE #26 blobs, license/NOTICE gap, test-import completeness and destination CI. No migration or source ownership change.

## PHX-MASTER UTC07 live role-CI and provenance supersession — 2026-11-20

The linked UTC07 audit report is an immutable snapshot at its recorded #327 docs head 63c1d2b.... Current exact owner heads and CI have advanced; the supersession sections in ROLE_ASSIGNMENTS.md, INTEGRATION_MATRIX.md, AUDIT_SUMMARY.md and REPOSITORY_ROUTING.md are the live source of truth. Current #327 docs/source-test heads are d9072ce... / 726981b...; current #291 docs/test heads are df189b0... / e6e9a7f.... #327 Full validation remains blocked by the QA poll-signature fixture; #291 Windows remains blocked by PISONET's unset $buildWorkflow, with compatibility and Full runs in progress. COE #26 remains five queued workflows / zero jobs. No migration or production authorization.

## Latest live audit — 2026-11-20 UTC08

- [PHX_MASTER_UTC08_20261120_TERMINAL_RELEASE_CI_AND_COE26_PROVENANCE_AUDIT.md](PHX_MASTER_UTC08_20261120_TERMINAL_RELEASE_CI_AND_COE26_PROVENANCE_AUDIT.md) — terminal exact-head correction for RELEASE #291 and HARDWARE #327; rechecks COE #26 source/destination blobs, license/notice placement, lab/test identities and destination CI. No migration.
- Current Master audit-start head: `ff3a4e961d45bbfaf40c23ff8f4e34d5299a19de`; #288 remains OPEN/DRAFT against `main@f4e8a891...`. The #172 body still contains older role pins; the new checkpoint and this report supersede those pins.
- RELEASE #291 compatibility is terminal FAIL on the POSIX `nm` parser test; Full non-production build/simulation is terminal SUCCESS with production import/sign/publish skipped; Windows is terminal FAIL on PISONET-owned unset `$buildWorkflow`.
- HARDWARE #327 focused quarantine/relay jobs PASS; Full validation FAIL remains at QA-owned `Missing poll signature check`. COE #26 remains five queued workflows / zero jobs and frozen.
- Full Master suite NOT RUN; local Git clone was blocked by DNS. Private Drive v11 registry unavailable; no older snapshot substituted. **PRODUCTION NO-GO.**


## Latest live exact-head supersession — 2026-11-20 UTC08:40Z

- [UTC08:40 exact-head release, PISONET scope and COE #26 provenance audit](PHX_MASTER_UTC08_20261120_0840Z_RELEASE_REPRODUCIBILITY_PISONET_SCOPE_AND_COE26_IMPORT_MATRIX.md).
- Master audit started from #288 head `737f42b40cc25c718aa1f1964165f53a50988bd0`; PR #288 remains OPEN/DRAFT against main `f4e8a891...`. The resulting commit is coordination-only; the route manifest remains `e4db324...`, DRAFT_REVIEW_ONLY, Master target null.
- RELEASE #291 current head `e6538892...`: Full non-production build 26 PASS / 4 production jobs SKIPPED; strict ESP32 compatibility fails on 67/68 differing bytes; Windows fails at PISONET-owned `$buildWorkflow` self-test.
- HARDWARE #327 current head `d9072ce...`: focused quarantine/relay PASS; Full validation fails at QA-owned `Missing poll signature check`.
- COE #26 remains frozen at `b382d233...`, five workflows queued / zero jobs. Current exact tree review confirms 25 source board-specific Python labs vs zero destination Hardware Python tests, one generic shell test, three source Hardware workflows absent from destination, firmware blobs different, and Hardware license/notice scope unresolved.
- Private v11 registry/newer corrections remain inaccessible; no older snapshot substituted. Full Master suite NOT RUN because local Git DNS failed. **PRODUCTION NO-GO.**


## Latest live exact-head supersession — 2026-11-20 UTC09

- [UTC09 live role-head, terminal CI and COE #26 exact-source reconciliation](PHX_MASTER_UTC09_20261120_ROLE_HEAD_CI_AND_COE26_EXACT_SOURCE_RECONCILIATION.md).
- Audit start: PR #288 head 129aa462322fb0bff2aedec524f42bb829fd7f4b; base main f4e8a891...; OPEN/DRAFT. Current Master changes remain coordination-only.
- HARDWARE #327 current head 8246afb3... now has quarantine and relay/output focused failures, in addition to Full validation's QA-owned poll-signature failure.
- RELEASE #291 current head f1126706... passes non-production Full build/simulation but fails strict two-core reproducibility and the PISONET-owned negative self-test.
- COE #26 remains frozen at b382d233..., five workflows queued / zero jobs. A fresh exact #327/#26 recursive-tree comparison found different firmware blobs, 24 source board-local Python lab files versus zero destination Hardware Python files, three source workflows versus one generic destination workflow, and incomplete destination notice scope.
- Private v11 registry/newer corrections remain inaccessible; no older registry substituted. Master suite NOT RUN because local Git DNS failed. **PRODUCTION NO-GO.**


## Latest live exact-head supersession — 2026-11-20 UTC11

- [PHX-MASTER UTC11 exact owner-head CI and COE #26 tree provenance audit](PHX_MASTER_UTC11_20261120_ROLE_CI_COE26_TREE_PROVENANCE_AND_RELEASE_FAILURES.md).
- Audit start: #288 / phoenix/master-coordination at 1c9eba9d8af0fdf8eef04e239c4f31516743c30f; base main f4e8a891...; PR OPEN/DRAFT. The UTC11 update remains coordination-only.
- HARDWARE #327 head 89442ce...: focused quarantine/relay PASS; Full FAIL at QA-owned Missing poll signature check.
- RELEASE #291 head b883662...: Windows FAIL at PISONET-owned $buildWorkflow; compatibility FAIL at missing verify_esp32_source_date_epoch import; Full CANCELLED.
- COE #26 remains frozen at b382d233..., five queued workflows / zero jobs. Exact #327/#26 tree comparison confirms differing firmware blobs, 25 source Python labs vs zero destination Hardware Python files, three source workflows vs one generic workflow, and incomplete notice scope.
- Private v11 registry/newer corrections remain inaccessible; no older snapshot substituted. Master Python suite NOT RUN because local Git clone failed DNS. **PRODUCTION NO-GO.**

## Latest live revalidation — 2026-11-20 UTC11 11:40Z

- [PHX-MASTER UTC11 live terminal CI and COE provenance revalidation](PHX_MASTER_UTC11_20261120_LIVE_TERMINAL_CI_AND_COE26_PROVENANCE_1140Z.md).
- Audit-start #288 head: 3d75d241263576c3913a6388a26d9d761324a957; PR #288 remains OPEN/DRAFT against main f4e8a891...
- Current #327 Full validation still fails at QA-owned Missing poll signature check; focused quarantine/relay pass.
- RELEASE #291 compatibility now passes both pinned ESP32 core legs; Windows fails at PISONET-owned $buildWorkflow; Full is CANCELLED with production sign/publish skipped.
- COE #26 remains frozen at b382d233..., five workflows queued / zero jobs. Exact source/destination blobs, lab imports, workflow parity and notice scope remain unaccepted.
- Private v11 registry/newer corrections remain unavailable; no older snapshot substituted. Master suite NOT RUN. **PRODUCTION NO-GO.**



## PHX-MASTER UTC12 live exact-head supersession — 2026-11-20T12:39:46Z

- [UTC12 exact-head QA poll-contract, RELEASE handover-freshness and COE #26 provenance audit](PHX_MASTER_UTC12_20261120_EXACT_HEAD_HANDOVER_GATE_AND_COE26_PROVENANCE.md).
- Master #288 starts at 7f804b678ed81fa633edc87c60ae08433fbbcc89, OPEN/DRAFT against main f4e8a891...; the existing 126 paths are all coordination/phoenix/.
- HARDWARE #327 @ e759f703...: focused quarantine and relay PASS; Full fails at Controller protocol parity because the inherited QA fixture still requires response_sig and literal |poll| despite the approved deny-only contract.
- RELEASE #291 @ d497ee71...: both ESP32 compatibility legs PASS; Windows and Full fail at the mandatory handover freshness gate because .github/workflows/blazepwifi-build.yml is newer than the committed PROJECT_HANDOVER.md checkpoint.
- COE #26 remains frozen at b382d233..., five queued workflows / zero jobs. Complete trees: 2,436 source entries and 286 destination entries; firmware blobs differ, 25 source Python labs have no destination Hardware Python identity, three source Hardware workflows have only one generic destination workflow, and root NOTICE / Hardware license-notice scope is incomplete.
- Ownership manifest remains e4db324..., DRAFT_REVIEW_ONLY, PHX-MASTER target null. No source migration or subsystem edit.
- Private v11 registry/newer corrections remain unavailable; no older snapshot substituted. Full Master Python suite NOT RUN because GitHub DNS failed. **PRODUCTION NO-GO.**
