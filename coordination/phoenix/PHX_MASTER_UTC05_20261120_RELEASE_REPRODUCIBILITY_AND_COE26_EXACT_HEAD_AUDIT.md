# PHX-MASTER UTC05 — Release Reproducibility and COE #26 Exact-Head Audit

**Audit time:** 2026-11-20T05:36:00Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.  
**Scope:** Experiments #172 / #266 / #288; current default/development/Master refs; role PRs and exact-head CI; COE main / #26 / #35 / #49; private registry availability.

## 1. Exact refs and ownership boundary

| Ref | Exact SHA / state |
|---|---|
| Experiments main | \`f4e8a891aed8af86d5fd315d28750a0ac3a7372b\` |
| Active v0.6 audit-foundation development ref | \`2fbd2475e9f54878c316fa7cea2f228386b0e859\` |
| Legacy v0.5.3 development ref | \`aad3aade72c1156eecba1fed30907c6d0283b2c5\` |
| Master branch at audit start | \`2a2f6bf0926676250aed007c1a001605173bb6c0\` |
| COE main | \`a6513ab4412b4c014eee2863e45cbe32d06cb243\` |
| COE integration PR #26 | \`b382d233ff06c8791b1028bed3c617cc7b670d12\` |

Experiments PR #288 is OPEN / DRAFT against main. At audit start it contained 119 changed paths, all under \`coordination/phoenix/\`; no subsystem source path was included. The machine-readable \`OWNERSHIP_ROUTES.json\` remains blob \`e4db324315a1b3543fec17a148fbf960170fcb29\`, \`DRAFT_REVIEW_ONLY\`, with PHX-MASTER destination \`null\`.

PHX-MASTER did not modify CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branches. The separate CORE continuation retains CORE implementation ownership. No competing CORE task was started.

## 2. RELEASE #291 — exact docs-head reproducibility result

Current PR #291 docs/head: \`8d0c975816569849118c95637078cc29509ef3a0\`.  
Release source/test commit: \`a7ad93d4a55292a3e281a6fe2d9ba46543a23070\`.  
Pinned Hardware source: \`369007bcbc684a0923a586e991f3aa0667cda105\`.  
Pinned ESP32 sketch blob: \`1458f32881d3b340f1101dd0215618b54c1b688b\`.

The release-owned comparator now maps differing byte ranges to ESP image segments and load addresses. It remains strict byte-for-byte and fail-closed.

- Exact docs-head compatibility [run #44681557945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557945): FAIL on both ESP32 cores after both builds compiled and exact Hardware source/sketch admission passed.
  - ESP32 core 3.3.13, job \`136105924081\`: equal image sizes 1,044,096 bytes; 68 differing bytes in four ranges: \`176–207\`, \`9668\`, \`9670–9671\`, and \`1044063–1044095\`. The first range is \`app_desc.app_elf_sha256\` in segment 0; offsets 9668 and 9670–9671 are segment-0 data at load address \`0x3f400020\`, segment-relative offsets 9636 and 9638–9639; the final range is image checksum plus appended SHA.
  - ESP32 core 4.0.0, job \`136105924432\`: equal image sizes 1,098,176 bytes; 65 differing bytes in four ranges: \`176–207\`, \`9716\`, \`1098143–1098156\`, and \`1098158–1098175\`. The first range is the ELF descriptor SHA; offset 9716 is segment-0 data at load address \`0x3f400020\`, segment-relative offset 9684; the final ranges are checksum/appended-SHA data.
  - The descriptor SHA and checksum/footer differences are dependent consequences of image differences, not proven root causes. The exact non-descriptor offsets remain unexplained.
- Exact docs-head Windows [run #44681557650](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557650), job \`136105990554\`: FAIL in PISONET-owned \`negative-selftest.ps1\`; PowerShell reports \`$buildWorkflow\` cannot be retrieved because it has not been set. Publisher skipped.
- Exact docs-head BlazePwifi [run #44681557828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557828): terminal SUCCESS: 26 jobs passed, 0 failed, and 4 production import/sign/publish jobs were skipped. CI-0701, validation, Android, firmware/platform target jobs and update bundle had passed; x86 and Android v0.4 simulations were still running. Signing and publishing were skipped. This is not a terminal Full PASS.
- Earlier exact source/test build [run #44680793729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44680793729) passed its guard and hosted build, with signing/import/publishing skipped. It does not override the strict reproducibility failures above.

**Release owner next action:** preserve the first and second ELF outputs before the second clean build overwrites its build directory, compare those ELF files, then use the pinned Xtensa \`objdump -h\` section table to map the non-descriptor byte offsets to exact ELF sections. Do not normalize bytes, patch the linker output, weaken the comparator, or publish raw binaries. PISONET owns the Windows self-test correction.

## 3. HARDWARE #327 — current focused and Full CI

PR #327 docs/head: \`b6304208d65548a9cfe371504badf03ae3e15dcf\`; source/test workflow commit \`2f89326d5b555ffdb2bfaba0a404483d665aa614\`; base #326 at \`58c558fb6a237935214621adc3dee65a10fe1a51\`.

- Quarantine/readback [#44675789220](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675789220): PASS.
- Relay/output [#44675789222](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675789222): PASS.
- Full [#44675789227](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44675789227): FAIL at QA-owned \`Missing poll signature check\`. All 13 firmware/platform target jobs and Android passed; downstream simulations, update bundle, signing and publishing were skipped.

The firmware's poll admission remains deliberately default-deny. QA must replace the stale positive-signature fixture with source-exact deny assertions; do not weaken firmware to satisfy the obsolete assertion. Focused host labs are CI evidence only, not physical acceptance.

Parallel HARDWARE #254 remains a separate candidate: focused header run [#44674147661](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44674147661) PASS; Full [#44674147778](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44674147778) FAIL because ESP32 compilation cannot find \`mbedtls/sha256.h\`. Do not silently stack #254 into #327.

## 4. Other role PRs — exact current heads and scope

| Role | PR / exact head | Evidence and limitation |
|---|---|---|
| PHX-CORE | #252 \`c82705f2de865c89ab733b10efa84f26f56a5cc4\` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; scoped DENY-only evidence, not independent witness or production financial acceptance. Separate CORE owner retains source authority. |
| PHX-RENTAL | #289 \`68928774d0d7cf65adb26bc6b54199a3159d066c\` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS; scoped CI, not real failed PackageInstaller acceptance. |
| PHX-PISONET | #255 \`d01fd1642c105b3b0f6cd3343d1c9b67291f6e09\` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; scoped Windows CI, not physical adapter acceptance. |
| PHX-QA | #290 \`5c29d15994cee1279058f1eca12f2a3180704292\`; #292 \`75a3f66d9563e38a0a48b9cf487b0b057a91ea96\` | #290 [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke \`NativeComInterfaceHandleLab\`; #292 has no exact-head PR-triggered run. |
| PHX-RELEASE | #291 docs/head \`8d0c975816569849118c95637078cc29509ef3a0\`; source/test \`a7ad93d4a55292a3e281a6fe2d9ba46543a23070\` | Compatibility [#44681557945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557945) FAIL; Windows [#44681557650](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557650) FAIL; BlazePwifi [#44681557828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557828) still terminal SUCCESS: 26 jobs passed, 0 failed, and 4 production import/sign/publish jobs were skipped. |

## 5. CoinOperatedEcosystem — destination freeze and separate candidates

### Integration #26

COE main is \`a6513ab4412b4c014eee2863e45cbe32d06cb243\`. Draft PR #26 remains OPEN / DRAFT at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`, based on current main, with 205 changed paths. Five unique workflows remain QUEUED with zero jobs: case-collision \`43096752609\`, Windows \`43096752632\`, Hardware/Shared \`43096752800\`, Rental \`43096752563\`, and Pisowifi \`43096752557\`. No combined destination CI has executed. Keep #26 frozen.

### COE #49 / #48

COE #49 \`aeb8ff11b2f5db9a5f86280ab62ab988245f3919\` is stacked on #48 \`8286548e395366f2332830025fed00ceebdfb24a\`, not #26 or COE main.

- Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873): 5/5 jobs PASS.
- Case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992): PASS.
- Shared Hardware [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922): ESP8266 compile and shared contract checks pass, ESP32 compile FAIL because \`mbedtls/sha256.h\` is missing under core 4.0.0.

PHX-HARDWARE explicitly acknowledged audit-only review and declined COE implementation ownership in [comment #7028198239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/49#issuecomment-7028198239). No CORE or PISONET implementation ACK is recorded. No #48/#49 route exists in the ownership manifest.

### COE #35

COE #35 head is \`7b9706d898fb5f36c6ed96504aefd04dc59bdc1b\`. Case guard [#44617783021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617783021) PASS. Mandatory sandbox [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) FAILS closed because Bubblewrap is not installed on the runner. Shared Hardware/profile validation [#44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050) fails all 10 appliance profiles because an approved site-scoped RFC 4193 ULA /48 has not been defined. This is a separate release candidate, not evidence for #26.

## 6. Governance, cleanup and private registry

- Issue #266 remains OPEN. The Master cleanup checkbox remains intentionally unchecked: the complete duplicate/dead-code/source inventory is not finished. No mass moves, deletions or renames were performed.
- Experiments root \`AGENTS.md\` blob \`d8777e3b58efc41caa5aa3c969c932aee9103d5f\` was read at main and Master. The linked Cloud Artifact Policy and Cloud Storage Recovery Handover were read from the actual repository \`BlazeDevStudio/BlazingSystems\` (the older AGENTS links use its former owner spelling). Policy requires the canonical private registry and append-only ledger before mirror/archive work.
- Exact-title Library search did not find \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` or newer authoritative corrections. Results exposed older v3–v7 snapshots and historical addenda/checkpoints only. No Google Drive connector is exposed. No older snapshot was substituted; no private contents or identifiers were published.
- Branch API objects report \`protected=false\` for Experiments main, the v0.6 audit-foundation ref, and COE main. Classic protection reads have returned 403 and repository rulesets are empty; effective organization-level enforcement remains unestablished. No settings changed.
- COE root \`AGENTS.md\` is not present at the current COE main path (earlier fetch returned 404).

## 7. Verification and safety

- 14 live readback assertions verified Master ref/PR equality, PR base freshness, all #288 paths remaining under Master ownership, route-manifest source/destination pins, COE #26 base identity, current role PR heads, cleanup state and UTC05 checkpoint deduplication. These are in-memory API/source assertions, not the repository's Python test suite.
- Exact workflow job steps and logs were read for RELEASE #291, HARDWARE #327/#254, and COE #35/#49.
- Full Master Python suite: NOT RUN. Master GitHub Actions: NOT RUN. Container Git clone was attempted but DNS resolution for github.com failed; no authenticated local checkout was available. This does not imply tests failed.
- No subsystem source, shared API, ownership route, payment state, signing material, secret, release artifact or hardware was changed. No migration, merge, release, flash, payment operation, secret provisioning or physical test was performed.

## 8. Next owner actions

1. PHX-RELEASE: preserve both ELF outputs and use the pinned Xtensa section table to identify the two unexplained non-descriptor byte locations; keep the comparator fail-closed.
2. PHX-PISONET: initialize/fix the owned \`$buildWorkflow\` negative self-test and rerun exact #291 Windows CI.
3. PHX-QA: replace the stale positive poll-signature assertion with source-exact default-deny tests; independently review #327 at the exact source/test SHA.
4. PHX-CORE: review signed target-kind, authenticated server-time and durable receipt/no-mutation contract for COE #49 before any implementation is routed.
5. COE integration owner: keep #26 frozen until per-file source blob, license, import completeness, test identity and exact-head destination CI are independently accepted.
6. Repository administrator: establish and independently verify protected branch admission and required checks.
7. Registry custodian: restore authorized access to canonical private v11 and newer corrections.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.


### Terminal BlazePwifi full-build supersession — 2026-11-20T05:37Z

The exact docs-head [#44681557828](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557828) completed after the initial readback: **26 successful jobs, 0 failed, 4 skipped**. Validation, Android, all firmware/platform targets, update bundle and all six v0.4 simulation jobs passed. The four skipped jobs are production signed-APK import, production sign handoff, release publication and prerelease publication. This is a terminal successful hosted build/simulation result only; it does not clear the still-failing two-core reproducibility run [#44681557945](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557945) or Windows self-test [#44681557650](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44681557650). No signing or publishing occurred. **PRODUCTION NO-GO.**
