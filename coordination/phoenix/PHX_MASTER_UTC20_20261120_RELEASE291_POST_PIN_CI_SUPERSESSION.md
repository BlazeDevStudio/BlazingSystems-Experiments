# PHX-MASTER UTC20 — RELEASE #291 post-pin CI supersession

**Updated:** 2026-11-20T20:16:04Z  
**Role:** PHX-MASTER — live role/CI reconciliation only  
**Disposition:** PR #288 OPEN/DRAFT · RELEASE #291 OPEN/DRAFT · PRODUCTION NO-GO

## 1. Exact RELEASE #291 transition

PR #291 advanced after the earlier UTC20 Master audit. Current PR metadata:

- Docs/PR head: 4f6d2371cafa2d7e80f1aa3e37e9744ad6b01ddf.
- Source/workflow-fix head: 5188d1a1cfb5f96462a5ec24941fe35530944f68.
- Test/static-guard commit: 5c5001d43e173463024c3c790bead406fa8c90c3.
- Base #242: 734b89d9e7792247e8376335c3f3685500ab3f89.
- PR remains OPEN / DRAFT / UNMERGED; accumulated diff remains 26 paths.

Commit ancestry was read directly: 4f6d237 is a child of 5188d1a; 5188d1a is a child of 5c5001d; 5c5001d is a child of the previous docs head bcb71b4c.

The new RELEASE-owned test and workflow now pin current HARDWARE #327 source/test SHA 1a631567eb0c14c12a114f592685f44cc414466f and ESP32 sketch blob ae0da8e2bb301c9c0af1035148d7d3ea2bd13aa7. Exact source readback confirms both the test guard and workflow contain the new SHA/blob and no longer contain the old source pin 76eca09159433d490ac4f49d059001dbf2171b13.

## 2. Exact current-head CI — no pass inferred

| Workflow | Run | Readback |
|---|---:|---|
| ESP32 core compatibility | [#44809606421](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606421) | IN_PROGRESS |
| BlazePwifi Full | [#44809606527](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606527) | QUEUED at run-list read; validation and several target jobs had started |
| Windows SoftTimer | [#44809606428](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44809606428) | COMPLETED FAILURE |

Compatibility job detail at readback:

- Provenance regression suite job 136542675863: SUCCESS.
- ESP32 core 3.3.13 / source 1a631567eb0c job 136542676483: IN_PROGRESS.
- ESP32 core 4.0.0 / source 1a631567eb0c job 136542676949: IN_PROGRESS.

Full build job detail at readback:

- Validation 136542799908, ESP8266 136542799950, ESP32 136542799970, Android 136542800113 and several firmware targets were IN_PROGRESS.
- Other firmware target jobs were still QUEUED.
- No terminal Full result is claimed.

Windows exact failure:

- Build-windows job 136542584711: FAILURE.
- The PISONET-owned negative-selftest.ps1 reports: “The variable '$buildWorkflow' cannot be retrieved because it has not been set.”
- Publisher job 136543116646: SKIPPED.

The prior compatibility PASS #44799798721 was at the old source label 76eca0915943. It is historical baseline evidence only; it does not replace the new-pin run #44809606421.

## 3. Ownership and integration boundary

The 26-path accumulated #291 diff remains 21 RELEASE paths, three CORE-owned handover/ledger/state paths, and two PISONET-owned SoftTimer tests. The three new commits touch only the RELEASE-owned compatibility test, workflow and handover. No CORE or PISONET ownership transferred.

Next actions:

1. RELEASE: wait for both current ESP32 compatibility legs and the current Full run to reach terminal states; do not claim a pass from in-progress/queued jobs.
2. PISONET: fix the unset $buildWorkflow in its own negative-selftest.ps1.
3. CORE: review/refresh its three inherited handover paths through the separate CORE continuation.
4. QA: independently review the exact new source pin and compatibility evidence.
5. MASTER: reconcile cross-owner paths and same-SHA CI before any merge discussion.

## 4. Master / COE state unchanged

Master PR #288 remains OPEN/DRAFT/UNMERGED at e45ed9f555817b7ab24e699d7e5ba9788bc31fea, 132 changed paths all under coordination/phoenix/. OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

HARDWARE #327 remains at docs head 4d651e918f71de2e69d1f3bcfe627c4f944c9c39 / source-test 1a631567eb0c14c12a114f592685f44cc414466f. Its quarantine/relay runs pass; Full #44805905622 fails at the QA-owned positive poll-signature fixture. RENTAL #328 remains at 0e0da62acd47c6a1ce287f8a30fc700d603fa070 and inherits the older Mbed TLS 4-incompatible ESP32 blob from #289. The exact #328 API21/API23 and APK checks pass, but its shared build fails at CORE handover freshness and the missing Mbed TLS 4 header.

COE #26 remains frozen at b382d233ff06c8791b1028bed3c617cc7b670d12: 2,445 source tree entries vs 286 destination, 25 source board-local Python labs vs zero destination, three scoped source Hardware workflows vs one generic destination workflow, differing firmware/test blobs, incomplete NOTICE/Hardware license scope, and five queued workflows / zero jobs. No migration or staging.

## 5. Evidence limits

The latest RELEASE workflow run states were re-read after the role's checkpoint; they supersede the checkpoint's earlier “no run observed” note. No exact-head compatibility PASS or Full PASS is claimed while jobs remain in progress/queued.

The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain unavailable through the exposed Library/connector surface; no older snapshot was substituted. Full Master Python suite remains NOT RUN because local GitHub DNS resolution failed. No physical hardware test, signing, secret provisioning, payment operation, migration, merge or release was performed.

**PRODUCTION NO-GO** remains mandatory pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
