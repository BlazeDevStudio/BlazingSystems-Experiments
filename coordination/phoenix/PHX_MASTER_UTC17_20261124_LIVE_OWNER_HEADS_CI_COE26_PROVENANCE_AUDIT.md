# PHX-MASTER UTC17 — live owner heads, CI and COE #26 provenance audit

**Read-time snapshot:** 2026-11-24 UTC17, including owner PR updates observed through 17:55Z.  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrices.  
**Execution:** Strict NO CODEX. GitHub-connected reads/writes and ordinary source/tree inspection only.

## 1. Control-plane snapshot

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Development branch blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master parent for this report: 359ef46213e8191c4e6831fd82cc2afca03a0142.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- PR #288 OPEN / DRAFT / UNMERGED at parent 359ef462, 199 changed paths, all under coordination/phoenix/. No Master reviews or Actions statuses.
- OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.
- Issue #172 OPEN; cleanup #266 OPEN / 0-of-7.
- Branch metadata: main, development, Master and COE main all protected=false; required status-check enforcement off. Detailed protection endpoints returned 403; repository ruleset lists were empty.
- Root AGENTS.md and its linked BLAZE_CLOUD_ARTIFACT_POLICY.md / BLAZE_CLOUD_STORAGE_HANDOVER.md were read. README_FIRST and COMMUNICATION_PROTOCOL (BLAZE-COMMS/1) were read from the available Library. The exact uploaded 00_MASTER_PROJECT_PHOENIX(1).txt was not present in current conversation attachments or the available Library; this run followed the complete instruction text supplied in the task.
- The full available Library listing contained 1,422 items and only BLAZE_PROJECT_REGISTRY base/v3-v7 files; v11 and newer corrections were not found. No Google Drive connector was exposed. The cloud policy says to report BLOCKED rather than pretend a Drive transfer occurred. No private registry contents or identifiers are reproduced here.

## 2. Current owner PR and CI state

| Role | PR / exact current head | CI evidence and blocker |
|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS, scoped only |
| RENTAL | #328 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK #44782114384 PASS; API #44782114393 PASS; build #44782114390 FAIL at PROJECT_HANDOVER freshness and missing mbedtls/sha256.h |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS |
| HARDWARE | #347 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine #45299741995 FAIL; Relay #45299742437 FAIL; build #45299741993 FAIL |
| HARDWARE | #348 eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Header-focused #45352513178 PASS; build #45352513177 FAIL at missing mbedtls/sha256.h |
| HARDWARE | #349 aa9ac766ee5316b35dfdb2942247127641647d2b | Relay #45453000020 PASS; Quarantine #45452999974 PASS; Full #45452999881 FAIL at Controller protocol parity / Missing poll signature check, job 138655025225; 14 jobs PASS and 12 dependent jobs skipped |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS |
| QA | #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs |
| RELEASE | #291 76da627a1a9c759ded5d74062c9f842c49a65dec; source/test a004c647e67f90269a9149f918887622bb8cc5e8 | Windows #45453527054 FAIL at handover freshness; compatibility #45453527038 PASS 3/3; build #45453527013 was in progress, but CI-0701 PASS and validate FAIL at freshness; 13/14 targets completed PASS, x86_64 still running |
| COE integration | #26 b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued, zero jobs |
| COE release infrastructure | #31 59ed44d0b911e176f1a95b9cf5585ef811ffd31b | Shared contracts and case guard PASS; mandatory Bubblewrap sandbox FAIL |
| COE release infrastructure | #35 e7801818b00854f34a5a88955d979c601ec96404 | Shared contracts FAIL: all ten appliance profiles lack approved site-scoped RFC 4193 ULA /48; case guard PASS; sandbox FAIL because Bubblewrap is not installed |
| COE finance/overlay | #45 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/shell #44295049727 PASS; case guard #44295049903 PASS |
| COE interconnect | #49 aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Case guard and Stage 5.1 PASS; shared hardware compile #44646341922 FAIL at missing mbedtls/sha256.h |

### 2.1 HARDWARE #349 — handover stale after test-module changes

Current PR head is aa9ac766; current source/test work now includes four commits after the earlier 6cfd2e09 test anchor. Commits fa1e1fa and aa9ac766 extracted two lab modules and fixed a missing poll_output_mutation argument. The fa1e1fa Relay/Quarantine runs failed with NameError because the extracted helper lacked that argument. The aa9ac766 correction is now covered by exact-head Relay #45453000020 PASS and Quarantine #45452999974 PASS.

Full #45452999881 still fails at Controller protocol parity: “Missing poll signature check” in the ESP8266 sketch. Fourteen jobs passed; twelve downstream jobs were skipped. The latest handover and PR description still identify 850f8b0, before the two new source/test commits. The owner must add a final handover covering aa9ac766 and refresh the PR description; Master does not edit Hardware-owned files.

### 2.2 RELEASE #291 — canonical CURRENT_STATE still stale

Current PR/docs head advanced to 76da627; source/test remains a004c647. The latest docs commit updates RELEASE-owned PHX_RELEASE_HANDOVER, PROJECT_HANDOVER and CHANGE_LEDGER only. It does not change the canonical CURRENT_STATE.md.

At the current head:
- Windows #45453527054 fails the mandatory shared handover freshness gate.
- ESP32 compatibility #45453527038 passes all 3 jobs.
- Build #45453527013 was still running at read-time. CI-0701 and Android passed; validate failed the mandatory freshness gate; 13/14 firmware targets were complete and successful, with x86_64 still running. Dependent simulation/update/signing stages were skipped.

The canonical CURRENT_STATE.md blob remains 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3, last checkpoint d85eb6a2766781b6cac1807cef461993d8216b84. Four workflow paths are newer than that checkpoint: blazepisonet-softtimer-release.yml, blazepwifi-build.yml, blazepwifi-v053-release.yml and blazerental-v053-lineage2-sign.yml. The accumulated #291 diff is 30 paths: 25 RELEASE, 3 CORE shared handover and 2 PISONET tests. Zero independent reviews. CORE owns canonical CURRENT_STATE; RELEASE owns workflow changes; PISONET owns its tests; QA independently reviews. Do not bypass the gate.

## 3. COE #26 exact-tree and migration provenance

Exact recursive trees:
- Experiments #349 current head aa9ac766: 2,523 entries, 66 board-local files, 52 Python board helpers, 47 tests.
- COE #26 b382d233: 286 entries, 4 Hardware board files, 0 Python board helpers, 19 tests.
- Experiments main f4e8a891: 2,340 entries.
- COE main a6513ab4: 3 scaffold entries.

### 3.1 Test identity

Source versus destination tests are 47 versus 19:
- 1 exact blob+mode match.
- 3 divergent same-path tests: config.sh, integration.sh and security.sh.
- 43 source-only.
- 15 destination-only.

Both firmware sketch blobs differ. Same filename, file count or passing destination suite does not establish imported source identity.

### 3.2 SOURCE_INTAKE / MIGRATION_MAP

SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f contains 61 runtime rows. All 61 destination blobs and modes match their recorded destination identities.

Recomputed status:
- 46 byte-identical.
- 15 derived.

The JSON summary incorrectly states 47 identical / 14 derived.

The manifest pins historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00. Comparing current Experiments main and #349 source paths with that pin yields 33 unchanged, 20 changed and 8 missing. The historical pin is not current main.

The JSON lists 15 derived tests; MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 records only 14 derived/local rows. It omits voucher_txn_journal.sh. Two mapped hashes are stale:
- run_focus.sh: map fa1f4f2c6393504499d50659d8bf980caf7ff85b; JSON 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9.
- member_txn_journal.sh: map 01dc9c65ae9d74eaafb403d47aebcd20edd14390; JSON d04df3c6f3ada60b9fda8c8c04230dd31e37019a.

### 3.3 License / notice

Exact matches: PisoWiFi product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Missing destination counterparts: Experiments root NOTICE.md and Tabler LICENSE. BlazeRentalLauncher LICENSE belongs to the separate RENTAL route, not PisoWiFi. No jsqr path exists in either current tree.

COE #26 remains FROZEN with five queued workflows and zero completed jobs. No staging, copy, move, overwrite, rebase, cherry-pick or destination write occurred.

## 4. Architecture clarification — poll authentication

At Experiments main, CGI producer blob 2e3a1430d08cc6606429a042df3b5848f53c7267 has no response_sig in its register|ping or poll response branches; response_sig appears on member snapshot/auth/mutation responses. Current ESP8266 and ESP32 sketches do not contain a response_sig poll-consumer check. HARDWARE #349 Full fails the inherited “Missing poll signature check” assertion.

This is an unresolved producer/consumer contract mismatch, not authority to invent a signature or weaken default-deny. CORE must publish the authenticated register/poll envelope and golden vectors; QA must independently reconcile the assertion; HARDWARE retains fail-closed behavior until the approved contract is tested.

## 5. Governance, tests and limitations

- Branch metadata reports protected=false on Experiments main, development, Master and COE main; required status-check enforcement is off. Detailed protection endpoints returned 403; ruleset lists are empty.
- Private Drive registry v11 and newer corrections were not found in the available Library; no Google Drive connector was exposed. No older registry was substituted and no private registry content is disclosed.
- The exact uploaded 00_MASTER_PROJECT_PHOENIX(1).txt was not visible in current attachments or the available Library. README_FIRST, COMMUNICATION_PROTOCOL, root AGENTS.md, linked cloud policy/handover and current Master coordination documents were read.
- Master Python suite: NOT RUN. verify_coordination.py: NOT RUN. Master PR Actions: zero runs/statuses.
- Executed this activation: recursive GitHub tree reads; exact blob/mode comparison for all 61 intake rows; test identity and license comparisons; branch/PR/issue reads; owner Actions status and failed-job log inspection.
- Not executed: physical hardware, 150 real power cuts, 30-device/24-hour soak, financial migration, signing, release or customer/payment operation.

## 6. Next actions

1. PHX-CORE publishes the approved authenticated register/poll contract and updates canonical CURRENT_STATE.md with exact source/workflow evidence.
2. PHX-QA independently reconciles the positive poll-signature assertion against the approved contract; HARDWARE updates its final handover at aa9ac766 and reruns Full only after approval.
3. PHX-RELEASE reruns Windows/Full after CORE refreshes CURRENT_STATE; PISONET independently reviews its two inherited tests.
4. COE integration owner corrects SOURCE_INTAKE counters, the missing voucher_txn_journal map row and two stale test hashes, then rechecks licenses/import completeness at exact refs.
5. Registry custodian restores authorized v11 Drive access; repository administrators establish effective branch protection.
6. Authorized human runner executes Master Python tests and verify_coordination.py.

**Final disposition:** PR #288 remains OPEN / DRAFT / UNMERGED. COE #26 remains FROZEN. PRODUCTION NO-GO.
