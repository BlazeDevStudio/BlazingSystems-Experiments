
# PHX-MASTER UTC07 — exact-head, index-link and COE #26 provenance audit

**Captured:** 2026-11-23T07:59:44.571Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix/, architecture/interface contracts, cross-repository provenance and integration matrix only. Strict NO CODEX.

## 1. Live repository state

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Legacy development branch blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- v0.6 audit-foundation comparison branch: 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Master branch before this update: phoenix/master-coordination@83e57736d1edb7b1cb175bf3b6db878e66c19221; base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- PR #288 remains OPEN / DRAFT / UNMERGED. Its 184 pre-existing changed paths were all under coordination/phoenix/.
- COE main a6513ab4412b4c014eee2863e45cbe32d06cb243 is a three-entry / two-blob scaffold. COE integration PR #26 remains OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.
- Cleanup issue #266 remains OPEN with 0/7 tracks complete; the Master checkbox stays unchecked because the broader duplicate/dead-code cleanup inventory is not complete.

## 2. Master-owned index correction

The complete recursive tree at the starting Master head used tree 4f027a670932b345a08ce0c5882ab379880ce351, with 2,526 entries and truncated=false. The coordination/phoenix subtree had 184 blobs and no duplicate blob-SHA groups.

The exact report inventory was 99 PHX_MASTER_*.md files and 99 unique link occurrences, but two links were not actually resolvable relative to INDEX.md: both included coordination/phoenix/ even though INDEX.md itself is already in that directory. The affected historical reports were:

- PHX_MASTER_UTC17_20261121_EXACT_HEAD_ROLE_CI_COE26_SOURCE_MAIN_PROVENANCE_AUDIT.md
- PHX_MASTER_UTC20_20261121_EXACT_HEAD_ROLE_CI_COE26_MANIFEST_BASELINE_CANDIDATE_AUDIT.md

Only those two link targets were corrected; both historical report files were retained. This report is added as the 100th report. The post-commit recursive-tree check verifies 100 report files / 100 unique relative links, zero duplicates, zero dangling links, zero unindexed reports and zero duplicate coordination blob groups.

## 3. New architecture invariant — §6.80

Hardware #345 now carries a source-extracted FakeLittleFS regression for an orphan /pending.attempt marker after partial clear. The scenario models /pending.dat removal succeeding while /pending.attempt remains present after remove("/pending.attempt") reports success. The extracted production clearPending() must verify post-remove existence; otherwise it could discard pending identity while durable attempt evidence remains.

The expected behavior is fail closed, preserve pending identity and marker bytes, latch journalRecoveryRequired, and after simulated reboot have loadPending() detect the orphan marker and remain in recovery-deny. A mutation removing the post-remove exists() check is rejected on both boards with expected exit 103.

- Source/test SHA: 78bfd193a90ab04630ac0c064c72b9b66a6d29f6.
- Logging-only evidence SHA: 7dee461649e6554389e4f80481086b43a4ddd85a.
- Current PR/docs head: deed0f49c04d8cd69dc4fda78d2a4d914aa4dd4d.
- Source/test Quarantine [#45133190059](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190059) PASS; Relay [#45133190127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190127) PASS.
- Full [#45133190056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133190056) FAILS at inherited QA-owned Controller protocol parity / Missing poll signature check; 13 firmware targets pass, Android is cancelled, downstream stages are skipped.
- Later logging-only Full [#45133582073](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582073) fails at the same assertion; Quarantine [#45133582142](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582142) and Relay [#45133582168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45133582168) pass.
- Current docs-head Relay [#45134012012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012012) PASS; Quarantine [#45134012104](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012104) and build [#45134012436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45134012436) were IN_PROGRESS at last read. No current-docs-head Full result is claimed.

This is host simulation only. It does not prove actual LittleFS durability, physical reboot behavior, electrical acceptance, 150 power cuts or a 30-device/24-hour soak. PHX-HARDWARE owns firmware/fixtures; PHX-QA owns the inherited assertion and independent review; PHX-MASTER owns only the cross-role contract. Do not add a positive legacy response_sig marker. Admission remains default-deny.

## 4. Current role PRs and CI

| Role | Current candidate | Exact evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped Build PASS. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity [44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; Build [44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL at handover freshness and ESP32 compile; job log reports missing mbedtls/sha256.h; API21/API23 smoke [44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows synthetic PASS; native COM/electrical acceptance NOT TESTED. |
| HARDWARE #345 | docs deed0f49; source/test 78bfd193; logging 7dee461 | Focused source/test Quarantine/Relay PASS; Full FAIL at QA-owned Missing poll signature; current docs-head Relay PASS, Quarantine/build IN_PROGRESS. |
| QA #290 / #292 | 5c29d159 / 75a3f66d | #290 Windows [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 no workflow runs. |
| RELEASE #291 | 886cabfc5080c3fbef03c2a3b1afe9d52dea6f60 | Windows [45117006843](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006843) and Full [45117006794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006794) fail CORE-owned handover freshness. Compatibility [45117006790](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006790): core 3.3.13 PASS; core 4.0.0 pinned Arduino CLI archive download fails HTTP 403; artifact provenance regression suite PASS. |
| COE #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED / zero jobs; frozen. |
| COE #35 | ead1c3b4ab84acc69eef6b63bfd7d224b4cbbecc | Sandbox [45130246987](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45130246987) fails because trusted Bubblewrap is absent (exit 125); host preflight 14/14 PASS. Shared contracts [45130246979](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45130246979) fails closed on 10/10 profiles because approved site-scoped ULA /48 authority is unset; case-collision [45130246990](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45130246990) PASS. |
| COE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Scoped runs [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS. |
| COE #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Case-collision [44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) and INTERCON [44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; shared-contract validation PASS, ESP8266 compile PASS, ESP32 compile FAIL in [44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922). |

CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE source branches remain with their owners. No subsystem branch or file was modified by PHX-MASTER.

## 5. COE #26 exact migration provenance

COE main a6513ab is a three-entry / two-blob scaffold. PR #26 tree 8a7d4cf has 286 entries / 207 blobs. No destination writes occurred.

### Historical PisoWiFi intake pin

SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f pins historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00 and tree 9b0ec594cb5d2bfe62d09d4a7fb9a254b9ffad3f. All 61 runtime rows resolve to their recorded source and destination blobs, with zero missing rows and zero blob-ID mismatches. However, row-level comparison is 46 byte-identical / 15 derived, while the summary says 47 / 14. The summary is off by one; retain the historical pin and ask the COE owner to reconcile the summary.

The original tests tree 7e3b16f2 has 149 blobs. COE Pisowifi/tests has 19: 2 identical, 2 different, 145 missing, 15 destination-only. The manifest's unchanged_original_test_count=2 is consistent with the exact tree comparison.

### Current owner candidate comparisons

| Route | Source / destination | Exact identity result |
|---|---:|---|
| CORE #252 rootfs | 61 / 62 | 45 identical, 16 different, 0 missing, 1 destination-only (blaze-appliance-diag). |
| PISONET #255 | 68 / 47 | 27 identical, 11 different, 30 missing, 9 extra. |
| RENTAL Android | 991 / 8 | 991 missing, 8 destination-only, no exact path/blob match. |
| Rental server | 12 / 4 | 1 different, 11 missing, 3 destination-only. |
| HARDWARE ESP32 | 16 / 1 | 1 different, 15 missing. |
| HARDWARE ESP8266 | 32 / 1 | 1 different, 31 missing. |
| QA #292 tests | 38 / 19 | 1 identical, 3 different, 34 missing, 15 extra. |
| RELEASE workflow | 1 / 1 | Different; destination is a reimplementation. |

The current Hardware source tree contains 36 board-local Python helpers; COE #26 contains zero.

### License and NOTICE coverage

PisoWiFi LICENSE is byte-identical. Source root NOTICE has no COE root counterpart. Rental Android, jsQR and Tabler license files exist in source but have no destination counterpart. qrcode and tailadmin license blobs match. Hardware-local LICENSE/NOTICE files are absent at the checked source/destination paths. This is not a complete license grant.

The ownership manifest remains 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No staging, copy, move, overwrite, cherry-pick, rebase, route promotion or destination edit.

## 6. Governance, private registry and test execution

- Branch metadata reports protected=false for Experiments main, legacy v0.5.3 development, v0.6 audit-foundation and COE main. Both repository rulesets lists are empty; classic branch-protection detail reads return HTTP 403.
- Root AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f was read. Its linked Cloud Artifact Policy and Storage Handover could not be fetched through the connected GitHub surface. No Google Drive connector was exposed; canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not accessible. No older substitute or private content was published.
- Local git ls-remote failed because the execution container could not resolve github.com. Full Master tests and verify_coordination.py are NOT RUN. test_architecture_contracts.py was inspected, not executed. PR #288 has zero Actions runs and zero combined statuses.
- Static recursive-tree/index verification is performed separately after the commit; it is not a unit-test or CI pass.

## 7. Next exact owner actions

1. PHX-QA: resolve the inherited poll-signature assertion against the approved deny-only producer contract; do not add a positive response_sig marker to firmware.
2. PHX-HARDWARE: complete the current docs-head Quarantine/build checks and keep the pending-attempt marker recovery evidence exact-head pinned; physical durability remains unproven.
3. PHX-CORE: refresh its owned handover so RELEASE can rerun freshness gates.
4. PHX-RENTAL: restore the ESP32 mbedtls/sha256.h build dependency and refresh its handover.
5. COE integration owner: correct SOURCE_INTAKE summary 47/14 vs exact 46/15; reconcile imports, test identities and license/NOTICE scope before any staging request.
6. COE release owner: provide a trusted Bubblewrap runner and owner-approved site-scoped ULA /48 authority; keep profile admission fail-closed until then.
7. Registry custodian and human test runner: restore authorized v11/newer-correction access and run the complete Master suite plus verify_coordination.py at the exact PR #288 head.

## Final disposition

PR #288 remains DRAFT / UNMERGED. Cleanup #266 remains OPEN / 0-of-7. COE #26 remains FROZEN. No merge, release, signer provisioning, secret access, firmware flash, physical test, real-payment operation, financial migration or customer cutover occurred.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
