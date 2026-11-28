# PHX-MASTER UTC20 — deny-only parity, Hardware stack, and COE #26 exact provenance audit

**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** PHX-MASTER-UTC20-20261127-DENY-STACK-COE26  
**Observed UTC:** 2026-11-27T20:39Z  
**Execution:** Strictly NO CODEX.  
**Scope:** coordination/phoenix/ only; no subsystem source edits.

## 1. Live refs at audit start

| Ref | Exact SHA |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Master branch / PR #288 | 90292a7a280c21dee29eebca7e76186bd4c02034 |
| Active v0.6 development | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 was OPEN / DRAFT / UNMERGED. At audit start it had 259 changed paths, all under coordination/phoenix. Current main compare was 673 commits ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. Master had no exact-head Actions run or combined status.

The live ownership manifest remains schema v1, 11 routes, DRAFT_REVIEW_ONLY, with PHX-MASTER target null. No ownership route was changed.

## 2. Hardware #366 exact source and CI audit

PR #366 is OPEN / DRAFT / UNMERGED at 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9, branch phoenix/hw-output-enable-lab-modules-20261128-utc19, child of #365 at e65b0b895af9c3fc5e5632f704cb67b347e69725. The source/test SHA is ff73702adf6fb958c9f21ebe9a68c908ee829ea4.

The Hardware-owned change splits the startup GPIO sequence lab into a source-contract/mutation module, a C++ event/compile harness, and a thin runner. It preserves the original command and existing cases. No production ESP sketch, shared API, controller schema, finance, QA-owned assertion, or COE file changed.

| Exact-head workflow | Result |
|---|---|
| Focused PR #46059524018 | PASS — 8/8 board/polarity cases; 14/14 unsafe mutations rejected; append-only ledger guard PASS |
| Mbed #46059523991 | PASS — 3/3 source-contract / ESP32 core 3.3.13 / core 4.0.0 |
| Full #46059524022 | FAIL — Controller protocol parity at tests/controllers.sh:21; ESP8266, ESP32, Android and 11 OpenWrt targets PASS; downstream update/simulation/signing/publication skipped |

The PR body records a transient incomplete ledger candidate in an intermediate commit, corrected by restoring the exact parent blob and appending one record. The final tree's append-only guard passes, but the temporary commit remains in the draft branch history. No force-push or history rewrite was performed. QA/reviewers should inspect the final tree and commit chain before any merge; Master did not rewrite or alter Hardware history.

These are host/CI results only. Physical GPIO voltage, relay contacts, coin acceptor, pulse retention, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## 3. Corrected controller-parity finding

The exact source blobs show why the Full assertion fails:

| Source ref | ESP8266 | ESP32 | config_revision |
|---|---|---|---|
| Experiments main | bfb94920eb0a189ca01d52e5443954fa133f5423 | 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 | Present |
| Active v0.6 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | Present |
| HARDWARE #354 candidate | b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9 | 3edbe38da543ef118b287f3e04c1601692cfa99f | Absent |
| HARDWARE #366 candidate | 7527dbff41b7f21bdc3d3ed9ee3db1c0d21eb07b | a673e323e1c160cbfe03949d13a9e01b47386596 | Absent |

The current QA test script blob is 53a7af25fdee9a650e10e870c4204e0fb43239c6. Line 21 still requires config_revision in both sketches. #354 and #366 intentionally omit it while keeping untrusted controller register/poll responses out of the trusted config path. The exact Full failures are #45864684497 (#354) and #46059524022 (#366).

Therefore the failure is not simply a current-main vs active-v0.6 mismatch. It is an unchanged QA presence assertion that does not match the deny-only candidate. The #366 PR body describes the mismatch too broadly. Master did not edit that Hardware-owned PR.

**Owner actions:** PHX-QA must replace the presence assertion with source-linked checks that prove unsigned poll/config fields are discarded and admission stays denied. PHX-CORE must publish authenticated register/poll/receipt/disposition semantics and golden vectors. PHX-HARDWARE owns the candidate firmware and host labs. Do not add a decoy config_revision token, re-enable untrusted remote configuration, or weaken default-deny.

## 4. Active v0.6 P0 and controller producer

The active development branch remains 2fbd2475e9f54878c316fa7cea2f228386b0e859. It still performs synchronous post("poll") before the first coin sample:

| Board | Poll | First coin sample |
|---|---:|---:|
| ESP8266 | line 354 | line 357 |
| ESP32 | line 314 | line 318 |

The HTTP timeout remains 3,500 ms. Issue #177 remains OPEN and its embedded source pin 9df0a7e7 is stale. Separate draft #354 is a deny-only candidate at fc842342596786e072630179acfbbc4feeb2ba02; its focused and Mbed runs pass, but Full fails Controller parity and Native fails PAY-0745. No physical relay/pulse evidence exists.

Current main CGI producer blob 2e3a1430d08cc6606429a042df3b5848f53c7267 has no controller response_sig in register|ping or poll response blocks. Later response_sig fields belong to member endpoints and do not authenticate controller poll/disposition.

Keep coin admission deny-only until CORE's contract and QA's independent golden-vector review exist. Do not treat #366's host simulation as a P0 fix or physical acceptance.

## 5. COE #26 exact recursive tree and route comparison

Source #366 tree 4f0552d1926d134ff48be9b0c2dce512af69702e has 2,435 entries / 1,889 blobs. COE #26 tree 8a7d4cf81d7227118b876c1138dd2da12345fefa has 286 entries / 207 blobs. Both are non-truncated.

| Route | Source | Destination | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone | 12 | 4 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 47 | 16 | 9 | 19 | 22 |
| ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | 18 | 1 | 0 | 1 | 17 | 0 |
| QA tests | 151 | 19 | 2 | 2 | 147 | 15 |
| RELEASE workflow | 1 | 1 | 0 | 1 | 0 | 0 |

Both controller sketch blobs differ:
- ESP32 source a673e323e1c160cbfe03949d13a9e01b47386596 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 source 7527dbff41b7f21bdc3d3ed9ee3db1c0d21eb07b vs destination c8be98f72596681e36a3ad1f8939bf8046c96887.

The #366 output-enable runner and its two new helper modules are not present at the destination. The source ESP8266 route has 18 blobs against one destination blob; 17 source blobs are absent and one mapped blob diverges.

### Test identities

- Source tests: 151 blobs; destination: 19.
- Source executable/test code: 145 files. Two exact matches (portal.sh, security.sh); two divergent (config.sh, integration.sh); 141 source-only.
- Fifteen destination-only test files exist. voucher_txn_journal.sh has no matching source path and is absent from MIGRATION_MAP.md.
- SOURCE_INTAKE.json schema 8 blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f contains 61 runtime rows: 46 byte_identical / 15 derived, while summary says 47 / 14.
- Its derived_tests array has 15 rows; MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 lists 14 derived rows and omits voucher_txn_journal.sh.
- SOURCE_INTAKE pins source 6d4c9b487af4d768c4d7627654d119417fcc6e00 and destination feature/pisowifi-cleanup-stabilization. Live #26 uses integration/ecosystem-nonproprietary-candidate-20261111 @ b382d233.
- HARDWARE_FIRMWARE_AUDIT.md blob 86c06e7574761465b80482430296eb712d985367 says the sketches were not copied, but the exact destination tree contains one divergent sketch under each board route.

### License / NOTICE identities

Ten source license/notice artifacts were found; four have exact mapped-path counterparts and six mapped-path counterparts are absent: root NOTICE.md, BlazeRentalLauncher/LICENSE, BlazeRentalLauncher/assets/license.html, jsQR LICENSE, UI qrcode LICENSE and Tabler LICENSE. Same-blob content at another path does not repair missing path provenance.

All five candidate PR #26 workflows are terminal CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609 and #43096752632. No destination staging, copy, move, overwrite, cherry-pick, rebase, retarget or write occurred. COE #26 remains FROZEN.

## 6. Registry, automation and test execution blockers

The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not surfaced by exact Library title search. Older v3–v7/base snapshots and a checkpoint reference exist, but were not substituted. No Google Drive connector is exposed. The AGENTS-linked public Cloud Artifact Policy and Storage Recovery Handover were read from the renamed BlazeDevStudio/BlazingSystems repository. No private Drive data or IDs were published and no Drive artifact was changed.

The automation inventory shows active Blaze Hourly Production Development explicitly assigned to PHX-HARDWARE. No exact-title Blaze Production Continuation entry surfaced. CORE source/branch work was not touched; no competing CORE worker or automation was created.

Master Python suite and verify_coordination.py were NOT RUN; no exact-head Master Actions run or combined status exists. GitHub source/tree inspection and role-owned CI must not be represented as Master test execution.

## 7. Actual Master changes and next actions

Master updated only coordination/phoenix:
- ROLE_ASSIGNMENTS.md — exact role heads and current CI.
- INTEGRATION_MATRIX.md — exact #366/#26 tree, route, test and license comparison.
- ARCHITECTURE_CONTRACTS.md — corrected deny-only/controller-parity interpretation.

The coordination commit 12e0b840bcad4d108e183ac78141a65b2e021d12 is the first audit update on the existing Master branch. The UTC20 INDEX, AUDIT_SUMMARY and this report are committed in the following coordination update.

Next:
1. PHX-QA: replace the stale config_revision presence assertion with source-linked deny-only assertions; run focused and Full CI at the exact owner-approved head.
2. PHX-CORE + PHX-HARDWARE: publish and validate authenticated register/poll/receipt/disposition semantics; keep coin admission fail-closed.
3. COE integration owner: reconcile exact refs, missing test identities, license paths and the hardware audit before any staging.
4. Registry custodian: restore authorized canonical v11 and newer corrections plus current manifest/ledger.
5. Repository administrator: provide a non-Codex checkout or dedicated Master CI path.

**Disposition: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signing, secret provisioning, flashing, physical test, payment operation or financial migration occurred.