# PHX-MASTER UTC12 — exact-head QA poll contract, RELEASE handover freshness and COE #26 provenance

**Audit timestamp:** 2026-11-20T12:39:46Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance and integration matrix only  
**Execution boundary:** NO CODEX. No Codex app, CLI, API, agent, workflow or delegation. No subsystem source branch was edited.

## 1. Exact live repository references

| Ref | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| v0.6 audit-foundation development | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master branch / PR #288 head | 7f804b678ed81fa633edc87c60ae08433fbbcc89 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

Experiments PR #288 remains OPEN / DRAFT against main at f4e8a891. Before this audit it had 126 changed paths; the live changed-file listing was checked and every path was under coordination/phoenix/. The branch head was confirmed through the live branch ref and PR metadata.

Cleanup issue #266 remains OPEN. The PHX-MASTER cleanup checkbox remains intentionally unchecked: this bounded audit does not complete the wider duplicate/dead-code inventory.

The exact ownership manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, with the PHX-MASTER route target null.

## 2. Current role PR heads and exact-head CI

| Role | PR | Current head | Exact-head CI and result |
|---|---:|---|---|
| CORE | #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | #42698139210 scoped build PASS; CORE remains with the separate CORE continuation |
| RENTAL | #240 | a7d113fb8ae3f0c5e838e64d31cae7a154e37b56 | #40910311159 and #40910311141 PASS |
| RENTAL | #287 | a4fffd01c8fb1818c32a53522e0590c1dc8a77cd | #43754089203 scoped entropy-contract PASS |
| RENTAL | #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | #43653329229 and #43653329235 PASS |
| PISONET | #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | #42462978704 scoped Windows PASS |
| HARDWARE | #254 | 84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9 | #44683629378 focused header PASS; #44683629491 Full build FAIL |
| HARDWARE | #327 | e759f70325523fe6429170e8b4396e335f574c8b | quarantine #44732030243 PASS; relay #44732030253 PASS; Full #44732030246 FAIL |
| QA | #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | #43633486963 scoped PASS; NativeComInterfaceHandleLab not invoked |
| QA | #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | no exact-head workflow run returned |
| RELEASE | #291 | d497ee71f1d84d9fd0ca22dd1127a53d62515642 | compatibility #44736348774 PASS on both ESP32 core legs; Windows #44736348781 FAIL at handover freshness; Full #44736348760 FAIL at the same mandatory handover gate |

These are scoped CI observations, not native device acceptance or production approval.

## 3. HARDWARE #327 — inherited positive poll fixture contradicts the approved deny-only contract

Current source/test head is e759f70325523fe6429170e8b4396e335f574c8b. The focused quarantine and relay/output workflows pass. The Full workflow fails at the Controller protocol parity step; its invoked controller test path reports:

Missing poll signature check in the ESP8266 sketch.

Exact test identities at the current merge tree:

- tests/v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211
- tests/controllers.sh blob f7896647713d6bf8034ff48ed19b6383e4dedea0

The legacy v0.5 test explicitly requires response_sig and the literal |poll| expression in both sketches. The current firmware documents that register/poll admission signatures do not authenticate the returned configuration object and keeps that positive path dormant. The Master architecture contract already requires poll admission and coin POST disposition to remain hard-deny until CORE defines the canonical authenticated envelope and QA independently verifies positive/negative golden vectors.

This is a QA-owned test-contract mismatch, not permission to add a synthetic signature string or weaken firmware. PHX-QA must replace the legacy positive string-presence requirement with exact-source negative tests for both boards: missing, unsigned, malformed, forged and positive-looking unverified responses must not enable insertion, retain an active target, authorize coin disposition, clear pending evidence or turn outputs on. HARDWARE retains firmware ownership. Master made no firmware or QA source changes.

## 4. RELEASE #291 — compatibility recovered; mandatory handover freshness now blocks Windows and Full

Current head: d497ee71f1d84d9fd0ca22dd1127a53d62515642.

- ESP32 compatibility #44736348774: both pinned core legs pass.
- Windows handover run #44736348781: FAIL in “Verify shared BlazePwifi and SoftTimer handover freshness”.
- Full BlazePwifi run #44736348760: firmware target jobs pass, but “Mandatory handover freshness gate” fails before the downstream validation/simulation path. Update, simulation, production-signing and publishing jobs are skipped.

The failing gate is not an ESP32 compile failure and must not be bypassed. Exact source identities inspected:

- handover_gate.sh blob d175106a9c534ca17a35f9f49082b70ea27e77da
- PROJECT_HANDOVER.md blob 38da8466baf977c6e158451f9ffd7ee1de59912d
- blazepwifi-build.yml blob 317309fca0045986ccd68a034ee92f230343da48

The actual log says source/workflow changes are newer than PROJECT_HANDOVER.md, names .github/workflows/blazepwifi-build.yml, and identifies last checkpoint commit 0f2e67b3794b2469523b51ced2ba4ec4a334e84b. The gate checks committed freshness of PROJECT_HANDOVER.md, CURRENT_STATE.md and CHANGE_LEDGER.md after meaningful source/workflow changes; it explicitly says to update the live record and exact evidence after the code change, not bypass the check.

PHX-RELEASE must coordinate with the canonical BlazePwifi handover owner and refresh the affected live record(s) after the latest workflow change, then rerun both handover and Full workflows. Do not edit the handover or workflow from Master.

PR #291 still changes two PISONET-owned SoftTimer files: PublisherMockCli.ps1 and negative-selftest.ps1. PISONET owns and must approve any change to those paths. RELEASE owns its release workflow/ELF tooling; this audit transfers no ownership.

## 5. COE #26 — fresh complete-tree provenance comparison

COE #26 remains OPEN / DRAFT / FROZEN, base main a6513ab4412b4c014eee2863e45cbe32d06cb243, head b382d233ff06c8791b1028bed3c617cc7b670d12, 205 changed paths. Its five workflows remain QUEUED with zero jobs.

Recursive Git trees were complete and not truncated:

| Tree | Entries |
|---|---:|
| Experiments source at HARDWARE #327 head e759f703... | 2,436 |
| COE #26 destination candidate b382d233... | 286 |

Exact board firmware blobs differ:

| Source blob | Destination blob | Identical |
|---|---|---|
| ESP8266 3ff575f5cd879c021407849578854b74a2d460bd | c8be98f72596681e36a3ad1f8939bf8046c96887 | No |
| ESP32 849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | No |

Test and workflow completeness:

- Source has 25 board-local Python labs/helpers; destination Hardware has zero Python lab files and one generic shell test. No exact test identity/import parity is established.
- Source has three PHX-HARDWARE workflows; destination has one generic hardware-ci.yml. This is not workflow parity.
- Source BlazePwifi LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721 matches destination Pisowifi/LICENSE, but this sibling license match does not establish Hardware subtree license/notice scope.
- Source root NOTICE.md blob f6d92cd21465312be5993631fe26977219be0fb9 is absent at destination. Destination Hardware/LICENSE and Hardware/NOTICE.md are also absent.

No copy, move, overwrite, rebase, cherry-pick, staging or route promotion is proposed. The separate COE candidates remain separate; #31 ImageBuilder fails, #35 ImageBuilder and Shared Hardware fail, #48 and #49 Shared Hardware fail, while their respective scoped Stage/case jobs have the results recorded in the integration matrix. COE #49 remains audit-only after HARDWARE declined implementation ownership.

## 6. Governance, storage and test execution

- Experiments branch metadata reports protected=false for listed refs; repository rulesets endpoint returned an empty list. Classic main branch-protection read returned HTTP 403, so effective organization-level enforcement remains unverified.
- COE root AGENTS.md was not found (404); Experiments AGENTS.md and README_FIRST/communication protocol were read.
- The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the available Library search. Older v3–v7 snapshots appeared, but none was substituted. No Google Drive connector was exposed in this runtime. No private registry data was copied or published.
- The full Master Python suite was NOT RUN. A local Git operation failed because the container could not resolve github.com.
- Master-side static consistency assertions were executed against the fetched exact refs and document/source identities; these are not the repository Python suite and do not replace GitHub Actions.

## 7. Required next actions

1. PHX-QA: replace the legacy positive poll-signature fixture with source-linked negative/default-deny behavior tests; rerun QA and #327 Full at exact current source SHA.
2. PHX-RELEASE: refresh the canonical handover after its latest workflow change and rerun #291 Windows and Full; keep PISONET-owned SoftTimer paths with PISONET.
3. PHX-HARDWARE: retain deny-only firmware and address any new exact-head failures without weakening persistence/output inhibition.
4. COE integration owner and subsystem owners: keep #26 frozen until every file has exact source/destination blob and mode provenance, license/NOTICE disposition, import/test identity, and destination CI at the exact candidate SHA.
5. Repository administrator: establish and independently verify effective protected branch admission.
6. Registry custodian: restore authorized access to private v11 and newer corrections.
7. PHX-MASTER: run the full coordination suite when an authenticated checkout/runtime is available; retain the Master cleanup checkbox as incomplete.

## 8. Production gate

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, flash, real payment operation, secret provisioning, physical test or financial migration was performed.
