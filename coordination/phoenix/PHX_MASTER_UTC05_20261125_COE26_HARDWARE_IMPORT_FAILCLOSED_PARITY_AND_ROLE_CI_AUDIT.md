# PHX-MASTER UTC05 — exact role heads, COE #26 Hardware import parity and fail-closed audit

**Observed:** 2026-11-25T05:34:49Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, provenance and integration matrix only.  
**Execution:** Strict NO CODEX. No subsystem source branch, COE destination or production system was modified.

## 1. Exact repository identity

| Reference | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Development branch blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch parent | 544a76ead141de4c2c257ac3dcea3e54984889e8 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN |
| Master PR #288 | OPEN / DRAFT / UNMERGED, base main |
| Routing manifest | OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes, DRAFT_REVIEW_ONLY, Master target null |

Issue #172 remains OPEN. Cleanup #266 remains OPEN with zero of seven role checkboxes complete. PR #288 had 209 changed paths at audit start; all 209 are under coordination/phoenix/.

## 2. Current role-owned PRs and exact-head CI

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build #42698139210 PASS; older evidence. CORE owns poll/register producer, durable finance and canonical handover. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK #44782114384 PASS; API #44782114393 PASS; build #44782114390 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS; not native acceptance. |
| HARDWARE #340 | 38f3e9419f37109443c806a2362577d9efc50e4d | Six focused/build workflows #45530901795/#45530901830/#45530901893/#45530901919/#45530901824/#45530901908 PASS. |
| HARDWARE #347 | 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine #45299741995, Relay #45299742437 and build #45299741993 FAIL. |
| HARDWARE #348 | eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Header #45352513178 PASS; build #45352513177 FAIL at missing mbedtls/sha256.h. |
| HARDWARE #349 | PR 56de0761ca67b54feb4889401a810b0069f50614; source/test f591cb85ba032e4f2c30e5008c71de9ce8d17f2e; docs dc6ef11c104fdd9b73dfdd1120ca3a2bc3f86dcf | Quarantine #45549636102 PASS; Relay #45549636112 PASS; Full #45549636091 FAIL at Controller protocol parity / Missing poll signature check. Fourteen target/platform + Android jobs PASS; twelve dependent stages SKIPPED. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs; no pass claimed. |
| RELEASE #291 | PR/docs c624251ef9072d5caf8032142edad2882ea84aee; source/workflow 1c99aa9b2eac493cfec2a965a7c2572dc8e73b55 | Full #45553954529 FAIL and Windows #45553954963 FAIL at CORE-owned CURRENT_STATE freshness; compatibility #45553954953 PASS 3/3 on exact HARDWARE source f591cb85ba032e4f2c30e5008c71de9ce8d17f2e and ESP32 sketch blob adfd2f110d88243d03f2195658fb456b154dcb84. PR body omits current head and UTC05; zero independent reviews. |
| COE RELEASE #35 | f611c96091a1014ad36bf64251c180bcbc2d1f65 | Shared #45541598251 FAIL after 223 tests (2 skipped), then ten site profiles fail for missing approved ULA /48. Sandbox #45541598267: 40/40 host preflight PASS, then Bubblewrap unavailable / exit 125. Case guard #45541598250 PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay #44295049727 and case guard #44295049903 PASS. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared Hardware #44646341922 FAIL. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED, zero jobs. No CI pass. |

The RELEASE Full/Windows logs explicitly say source/workflow changes are newer than docs/handover/CURRENT_STATE.md; last accepted checkpoint is d85eb6a2766781b6cac1807cef461993d8216b84. The gate instructs updating the live record after the code change; no bypass was attempted. CORE owns canonical freshness. RELEASE owns its own PR body and reruns.

## 3. Exact COE #26 destination review

The COE candidate recursive tree is complete at 286 entries. The current #349 source recursive tree is complete at 2,540 entries. Under the current source project root, the ESP32 subtree has 16 files, ESP8266 has 54, the tests directory has 47 files, and the two board trees contain 58 Python labs/helpers. The destination Hardware subtree has two sketches and one hardening test, no board-local Python labs, and no Hardware-specific SOURCE_INTAKE or MIGRATION_MAP.

| Board | Current source #349 blob | COE #26 destination blob | Lines |
|---|---|---|---:|
| ESP32 | adfd2f110d88243d03f2195658fb456b154dcb84 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | 1,915 / 410 |
| ESP8266 | 8a0b458b6c7fb99c0913df16c5b4ca94dbcdc50e | c8be98f72596681e36a3ad1f8939bf8046c96887 | 2,036 / 489 |

### Candidate behavior defects verified at exact blobs

- Destination ESP32 uses LittleFS.begin(true) at line 337; destination ESP8266 calls LittleFS.format() on mount failure at line 143. Current source ESP32 uses LittleFS.begin(false) and latches journalRecoveryRequired instead of formatting.
- Both destination quarantinePending implementations clear pending state after the append attempt, without requiring verified durable append success. Current source validates the durable path and returns clearPending() only after successful quarantine handling.
- Both destination /quarantine/clear handlers delete the quarantine log and return success. Current source preserves unpaid-coin evidence and denies deletion without an approved durable receipt and authenticated recovery contract.
- Both destination register/poll paths start with sigOk=true, verify only inside a non-empty-key branch, and apply remote configuration from those responses. With an empty key, the signature gate remains true. Current source has no applyRemoteConfig call sites; poll response acceptance remains hard-deny pending CORE/QA contract evidence.
- Destination Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e (103 lines) differs from current source test blob 41211b2c110ab409f6d9d1812ef12fda73b13211 (181 lines). Exact test identity/parity is not established.

### Manifest, test and license provenance

- SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows and pins historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00. Its summary says 47 identical / 14 derived, but exact row recount gives 46 identical / 15 derived. Fifteen derived tests are declared.
- MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 uses the same historical source pin. It does not map current #349 Hardware files or tests.
- Pisowifi/LICENSE exactly matches source project LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Source root NOTICE.md blob f6d92cd21465312be5993631fe26977219be0fb9 and source Tabler LICENSE blob 22ee8122400915cbff18e5f69368fa9eea6145eb have no destination counterparts. QRCode/TailAdmin license counterparts remain present.

**Disposition:** COE #26 stays FROZEN. No destination staging, copying, moving, overwrite, path remap, cherry-pick, merge or promotion occurred.

## 4. Governance, tests and limits

- OWNERSHIP_ROUTES.json remains unchanged: 11 routes / DRAFT_REVIEW_ONLY / Master target null. Hardware routes are selective-review, not recursive-copy authorization.
- Cleanup #266 remains OPEN / 0-of-7.
- Private canonical Drive BLAZE_PROJECT_REGISTRY v11 and newer corrections were not retrievable through authorized connected sources. No older registry snapshot was substituted and no private registry contents were disclosed.
- Branch metadata reports protected=false for Experiments main, development and COE main; effective required-check enforcement is not established.
- 32/32 read-only source/tree/CI consistency assertions PASS; these are not product tests.
- Master commit 544a76ead141de4c2c257ac3dcea3e54984889e8 has no GitHub Actions runs or commit statuses. Master Python suite and verify_coordination.py were NOT RUN because no authenticated local checkout/runner is available. Owner CI results above are actual GitHub Actions executions; source/tree and blob comparisons are inspections, not product test executions.

## 5. Required owner actions

1. COE integration owner keeps #26 frozen and prepares a Hardware-specific per-file intake map with exact current source/test SHAs, destination blob/mode, test identity, license/NOTICE and owner disposition. No copy before independent review.
2. CORE publishes the authenticated poll/register response contract and canonical vectors; QA independently reviews exact consumer assertions. Until then, preserve deny-default.
3. CORE refreshes canonical CURRENT_STATE / PROJECT_HANDOVER after newer source/workflow changes. RELEASE then reruns Full and Windows and refreshes its own PR description.
4. Registry custodian restores authorized private v11/newer-correction access.
5. MASTER continues cleanup #266 ownership/dependency inventory and keeps the route manifest unchanged until owner evidence supports review.

## 6. Production disposition

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates remain mandatory.

No merge, release, signing, secret provisioning, firmware flash, physical test, real-payment operation, customer cutover or financial migration occurred.