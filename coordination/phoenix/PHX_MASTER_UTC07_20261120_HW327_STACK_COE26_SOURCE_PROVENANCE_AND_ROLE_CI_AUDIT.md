# PHX-MASTER UTC07 — Hardware #322→#327 stack, Release CI and COE #26 source provenance

**Date:** 2026-11-20  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**Branch at start:** \`phoenix/master-coordination@230bdecf1b404eece414802f544eabbc352e6991\`  
**Draft:** [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), OPEN / DRAFT / UNMERGED  
**Execution boundary:** NO CODEX. No Codex app, CLI, API, agent, workflow or delegation. No subsystem source edits, merge, release, flash, secret provisioning, payment operation or physical test.

## 1. Live refs and instructions

- Experiments default branch: \`main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b\`.
- Legacy development branch: \`blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5\`.
- \`blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859\` remains comparison-only; it is not promoted.
- Master PR #288 at start: \`230bdecf1b404eece414802f544eabbc352e6991\`, base \`main@f4e8a891...\`, 120 changed paths, all under \`coordination/phoenix/\`.
- COE default branch: \`main@a6513ab4412b4c014eee2863e45cbe32d06cb243\`.
- COE integration PR #26: \`integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12\`, base \`main@a6513ab...\`, OPEN / DRAFT / UNMERGED, 205 changed paths, 85 commits.

Re-read the uploaded Master directive, Library copies of \`README_FIRST\` and \`COMMUNICATION_PROTOCOL\` (BLAZE-COMMS/1), Experiments root \`AGENTS.md\` (blob \`d8777e3b58efc41caa5aa3c969c932aee9103d5f\`), repository README, issue #172, cleanup issue #266, PR #288, PR #26, current Master coordination documents and role-owner PR/CI evidence. The AGENTS.md-linked Cloud Artifact Policy and Storage Recovery Handover could not be fetched through the available GitHub/web surfaces in this run; no claim is made that those two linked files were read.

The private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` and newer corrections remain unavailable through the exposed Library/connector surface. Older Library snapshots were not substituted. No private Drive IDs or contents were published.

## 2. Corrected live Hardware ancestry

The prior Master record said current #323 was \`1761bf38...\` and described a parent-snapshot discrepancy against #326. Live PR metadata now resolves that stale statement:

| PR | Current head | Base | State |
|---|---|---|---|
| #322 | \`50d93e0de3d682550b6f02fb43484e76ad9c7e08\` | #320 at \`b2b41a3d6ce7887b9624137c966f58462895d3fa\` | OPEN / DRAFT |
| #323 | \`988904e8bcd058b62a9fac4aa6319a9b7c5b2470\` | #322 at \`50d93e0d...\` | OPEN / DRAFT |
| #326 | \`58c558fb6a237935214621adc3dee65a10fe1a51\` | #323 at \`988904e8...\` | OPEN / DRAFT |
| #327 | \`63c1d2b38855646acc1e04b3f7952c778692460a\` | #326 at \`58c558fb...\` | OPEN / DRAFT |

**Correction:** current PR #323 head \`988904e8...\` exactly equals #326's base. The earlier statement that current #323 was \`1761bf38...\` and that the parent chain was 31 commits ahead / 11 commits behind is superseded. The live stack is now a continuous draft chain \`#322 → #323 → #326 → #327\`. This corrects the ancestry ledger only; it is not merge approval and does not authorize a rebase or source edit.

#327's latest exact source/test commit reported by PHX-HARDWARE is \`354dddcdbfb93235f10fc99171d15ce63bc01451\`; current docs/PR head is \`63c1d2b38855646acc1e04b3f7952c778692460a\`.

### #327 exact-head CI

At docs/PR head \`63c1d2b...\`:

- [Quarantine/readback #44690922470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690922470) — SUCCESS.
- [Relay/output polarity #44690922558](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690922558) — SUCCESS.
- [Full BlazePwifi #44690922491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690922491) — FAILURE in validation job \`136136240246\`: QA-owned \`Missing poll signature check\` in the ESP8266 controller sketch. All 13 firmware/platform targets and Android completed successfully; downstream simulations, signing and publishing were skipped.

The source/test commit \`354dddc...\` also has focused quarantine [#44690508367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508367), push [#44690503396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690503396), and relay [#44690508288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508288) PASS. Full [#44690508314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44690508314) fails at the same inherited QA assertion. Firmware remains default-deny; no \`response_sig\` producer was invented and no admission guard was relaxed.

### Parallel Hardware candidates

- #239: \`d83b715b116185107737fef721c2eece8feebf39\`, OPEN / DRAFT.
- #254: \`84c442a46ee2ee48ab733b10efa84f26f56a5cc4\`, OPEN / DRAFT. Focused ASan/UBSan [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) PASS; Full [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) FAILS at handover freshness (\`CHANGE_LEDGER has no dated entries\`) and inherited ESP32 core 4.0.0 \`mbedtls/sha256.h\` compile failure.
- #283: \`830c355376380f9b5533d5cda2558beed41a593a\`, OPEN / DRAFT. Quarantine [#44219099309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099309) and build [#44219099256](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099256) PASS. The earlier unconditional-clear finding is no longer present, but \`quarantinePending()\` remains definition-only and register/poll/coin still lack an approved \`response_sig\` producer/consumer contract. #239/#254/#283 are parallel drafts, not prerequisites in #322–#327.

## 3. Other role exact-head evidence

| Role | PR / exact head | Current evidence and limit |
|---|---|---|
| CORE | #252 \`c82705f2de865c89ab733b10efa84f26f56a5cc4\` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped software validation only. Separate \`Blaze Production Continuation\` retains CORE source ownership; Master did no CORE work. |
| RENTAL | #289 \`68928774d0d7cf65adb26bc6b54199a3159d066c\` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) SUCCESS, scoped. |
| PISONET | #255 \`d01fd1642c105b3b0f6cd3343d1c9b67291f6e09\` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance not established. |
| QA | #290 \`5c29d15994cee1279058f1eca12f2a3180704292\`; #292 \`75a3f66d9563e38a0a48b9cf487b0b057a91ea96\` | #290 [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, but its workflow does not invoke \`NativeComInterfaceHandleLab\`. #292 has no exact-head workflow run and remains based on an older Master base. |
| RELEASE | #291 \`7fbd4ea256b250aa7305a9a72948655f71e649d6\` | Full [#44692255873](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44692255873) SUCCESS (26 jobs passed, 0 failed, 4 production import/sign/publish jobs skipped). Compatibility [#44692255708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44692255708) FAILS on both ESP32 cores with \`OTHER_IMAGE_CONTENT_DIFF\`; Windows [#44692256309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44692256309) FAILS in PISONET-owned \`negative-selftest.ps1\` because \`$buildWorkflow\` is unset; publisher skipped. |

The latest RELEASE byte diagnostics remain fail-closed: core 4.0.0 differs at 68 bytes (\`176–207\`, \`9714\`, \`9716–9717\`, \`1098143–1098175\`); core 3.3.13 differs at 67 bytes (\`176–207\`, \`9670–9671\`, \`1044063–1044095\`). The middle ranges map into \`.flash.rodata\`; no root cause is claimed. No byte normalization, linker patch, timestamp override or raw binary publication was performed.

## 4. COE #26 exact source/destination provenance

The unchanged \`OWNERSHIP_ROUTES.json\` blob is \`e4db324315a1b3543fec17a148fbf960170fcb29\`: \`DRAFT_REVIEW_ONLY\`, source ref \`f4e8a891...\`, destination PR #26 \`b382d233...\`, PHX-MASTER target \`null\`; Hardware routes are \`selective-review\`. The manifest is pinned to Experiments main, not to current Hardware #327, and is a review map rather than a copy/move instruction.

Current #327 branch source and COE #26 destination blobs:

| File | Experiments #327 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP8266 \`BlazePwifiVendo.ino\` | \`b956bc031df32ef69350dec368eaa91073b5a638\` | \`c8be98f72596681e36a3ad1f8939bf8046c96887\` | DIFFERENT |
| ESP32 \`BlazePwifiVendo32.ino\` | \`1458f32881d3b340f1101dd0215618b54c1b688b\` | \`3cc7ec54b476943dc04a8d1af5e2df5fe054e422\` | DIFFERENT |

The current candidate therefore does not contain the current #327 firmware blobs byte-for-byte.

### License and notice scope

- Source \`experiment/openwrt/BlazePwifi/LICENSE\` exists at blob \`1ee55b94183417be977ca287cd7391f9a6f7e721\` and is MIT.
- Source Experiments root \`NOTICE.md\` is blob \`f6d92cd21465312be5993631fe26977219be0fb9\`; it is a repository-level experimental-software notice, not a replacement for third-party component notices.
- COE #26 \`Hardware/\` contains README, ESP32, ESP8266 and tests, but no Hardware-scoped LICENSE or NOTICE; COE candidate root also has no root LICENSE/NOTICE entry.
- This is a provenance/license carry-through gap requiring human license-scope review, not a legal conclusion that the files are unlicensed.

### Test and workflow import completeness

- Current source #327 board directories contain 16 ESP8266 Python lab files and 9 ESP32 Python lab files (25 board-specific source-extracted labs).
- COE #26 \`Hardware/tests/\` contains only \`test_firmware_hardening.sh\` (blob \`f921c56cecc19cab1989507b9b4ade1f45dac54e\`); none of those 25 Python lab files is present there as an exact imported test identity.
- Source workflow blobs include \`phx-hardware-poll-edge-latch.yml\` (\`f1dfa7fd...\`), \`phx-hardware-quarantine-byte-readback.yml\` (\`3ad7d6e4...\`) and \`phx-hardware-relay-output-polarity.yml\` (\`9fee8f85...\`). COE #26 instead has one generic \`.github/workflows/hardware-ci.yml\` blob \`fe79adbdb3745a22c5ef6d1f0c87c868b7785793\`; it is not an exact import of those source workflow identities.
- COE #26's five workflows [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563) and [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557) are all QUEUED with zero jobs. No destination acceptance is established.

**Disposition:** do not copy, move, rebase, cherry-pick or stage #327 into #26. Before any future proposal, require exact per-file source/destination blob and mode comparison, license/NOTICE carry-through, import-complete test identities and workflow equivalence, dependency closure, rollback plan, role-owner acknowledgement, independent QA and completed exact-destination CI.

## 5. Separate COE Stage 5 candidates — no role ownership

- COE #48: \`8286548e395366f2332830025fed00ceebdfb24a\`, based on #47 \`1c10f7421dfaa87fcb2ce89d4a8b2d22422d1597\`. Stage 5 [#44643670696](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670696) and case guard [#44643670679](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670679) PASS; shared Hardware [#44643670685](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670685) FAILS compiling ESP32 because \`mbedtls/sha256.h\` is missing.
- COE #49: \`aeb8ff11b2f5db9a5f86280ab62ab988245f3919\`, child of #48. Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAILS at the same missing ESP32 mbedTLS header. Its 16/16 host mock tests and ESP8266 compile pass; this does not establish backend integration or production safety.

Neither #48 nor #49 has a route in \`OWNERSHIP_ROUTES.json\`. PHX-HARDWARE explicitly declined implementation ownership and described its scope as audit-only. PHX-MASTER does not assign the branch to HARDWARE, PISONET or CORE. Keep both separate from #26 pending explicit accountable-owner decisions and the CORE signed target-kind/server-time/receipt contract.

COE RELEASE #35 is also blocked: case guard [#44617783021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617783021) PASS; mandatory sandbox [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) FAILS because Bubblewrap is unavailable; shared CI [#44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050) runs 118 tests (2 intentional skips) but all 10 appliance profiles fail because no approved site-scoped RFC 4193 ULA /48 authority exists.

## 6. Verification and limits

- Live GitHub metadata, exact branch/PR heads, file tree entries, blob identities, issue/PR comments and workflow job logs were read back.
- Source/destination Hardware firmware blobs, LICENSE presence, board-lab inventory, workflow inventory and destination CI queue were compared at the exact refs above.
- No local checkout or source-exact Master test suite was executed: \`git ls-remote\` failed because this runtime could not resolve \`github.com\`. No Master-specific Actions workflow was surfaced by the available connector. Do not report a full Master Python suite PASS.
- No physical hardware, 150 power-cut trial, 30-device/24-hour soak, live financial migration, production signer, protected anti-rollback witness or native COM bench was available or invoked.
- Experiments main and COE main branch APIs both report \`protected=false\`; effective organization-level rules remain unverified. No repository settings were changed.

## 7. Next owner actions

1. **PHX-QA:** replace the stale positive poll-signature assertion with source-exact default-deny checks and rerun Full on the exact Hardware source/test SHA; do not manufacture \`response_sig\`.
2. **PHX-CORE:** publish the authenticated register/poll, target-kind, signed server-time and event-bound durable receipt contract before any positive poll/coin disposition.
3. **PHX-RELEASE:** diagnose the exact ESP32 \`.flash.rodata\` differences and keep byte-for-byte comparison fail-closed; leave the PISONET-owned \`$buildWorkflow\` test correction with PISONET.
4. **PHX-HARDWARE:** preserve the #322→#323→#326→#327 draft chain; refresh its own PR body/handover after any further source change; no physical acceptance claim.
5. **COE integration owner + QA:** keep #26 frozen; perform file-by-file license, test-identity, dependency and exact destination-CI review before proposing any import. Obtain explicit accountable-owner decisions for #48/#49.
6. **Repository administrator:** independently establish and verify protected branch admission/required checks.
7. **Registry custodian:** restore authorized access to private v11 and newer corrections; do not publish private records.

## 8. Production gate

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. Green scoped CI, host simulations, current source ancestry or a coordination-only PR do not waive any gate.
