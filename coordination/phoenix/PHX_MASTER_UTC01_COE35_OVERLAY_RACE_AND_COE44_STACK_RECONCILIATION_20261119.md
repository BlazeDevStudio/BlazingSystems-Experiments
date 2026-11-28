# PHX-MASTER UTC01 — COE Release ancestry, overlay accounting and Hardware refresh

**Role:** PHX-MASTER — coordination/architecture/provenance only  
**Status:** Master documentation candidate / PR #288 OPEN-DRAFT / migration BLOCKED / PRODUCTION NO-GO  
**No Codex used. No subsystem source branch modified.**

## 1. Live refs and ownership

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Named development branch: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5 (293 behind, zero ahead of main).
- Comparison branch: blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859 (1,876 ahead, 22 behind main).
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN/DRAFT.
- Master branch before this commit: acebbb23276d592b3a735e9bc29b59049a27995e; PR #288 OPEN/DRAFT, base main, 92 changed paths all under coordination/phoenix.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

Issue #172 contains conflicting development labels. Most source-history entries call v0.5.3 development and v0.6 comparison-only; a later exact-ref block calls v0.6 current development. No branch is promoted or selected as migration source. Cleanup issue #266 remains OPEN and its checklist still cites historical source pins.

## 2. COE Release #35 — overlay size race correction

Current #35 PR head: 3455e0ce56bed780a727a6297db14a8e1d345f99.  
Exact source/test head: 5e25e4ceab7c0615bcdad8309d50739e6b255f46.  
Base #31: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.

The old path-based os.walk/islink/getsize sequence could classify a staged entry and then resolve a different filesystem object after a symlink swap. The source now opens entries through O_PATH|O_NOFOLLOW, reads metadata from fstat on the pinned descriptor, compares the opened device/inode with a no-follow stat relative to the pinned parent directory, opens child directories with O_DIRECTORY|O_NOFOLLOW, and fails closed on identity changes or unavailable required primitives. Symlinks are excluded from the overlay byte budget.

### Test-first evidence

- RED #44435063672 reproduced regular-file-to-symlink replacement at the open boundary.
- RED #44436345907 reproduced symlink-to-regular replacement and the old undercount.
- Exact source/test shared run #44436769990 passed.
- Latest docs-head shared run [#44438686744](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44438686744) passed 107 packaging tests with two intentional sandbox-only skips, all 10 appliance profiles, shared checks and ESP32/ESP8266 compile/upload.
- Case-collision [#44438686678](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44438686678) passed.
- Mandatory sandbox [#44438687009](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44438687009) failed closed: 13/13 host-preflight tests passed, then bwrap was not installed; exit 125. No unsandboxed fallback was used.

### Master audit finding — missing post-open race regression

The two tests in tools/test_package_appliance_firmware.py swap the directory entry inside the patched os.open wrapper before delegating to the real open. They cover both entry types at the open boundary, but not replacement after O_PATH has acquired the object and before the subsequent dir_fd no-follow stat. The implementation compares inode identity and raises ValueError on that mismatch, but the mismatch branch lacks deterministic test evidence.

**Request:** PHX-QA should add two tests that replace a regular file with a symlink and a symlink with a regular file after O_PATH acquisition but before the no-follow stat; both should fail closed and preserve external sentinel bytes. This is a test-coverage gap, not a confirmed source defect.

The CI artifacts are nonproduction build archives. PR and push artifact ZIP digests differ; no byte-reproducible firmware, signed release, actual ImageBuilder sandbox execution, hardware flash or physical acceptance is claimed.

## 3. COE #44 — sibling-stack divergence and ULA site identity

- Current #44 head: 582fd5d5e83e36b36546ac28534740298ba94af4.
- #44 base: earlier #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4.
- Current #35 head: 3455e0ce56bed780a727a6297db14a8e1d345f99.
- GitHub compare: #44 is 15 commits ahead and 13 commits behind current #35.

These are divergent sibling stacks. #44 does not contain the current #35 overlay-accounting source/test and terminal handover commits. PHX-RELEASE must reconcile ancestry using normal history-preserving operations. PHX-MASTER did not merge, rebase, cherry-pick or force-push either branch.

The #44 first-boot script generates a random 40-bit RFC 4193 ULA prefix per installation, writes it to UCI, validates persisted readback and scopes rollback to its own option/section. Shared run [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) and case [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) passed; mandatory sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) remains blocked by missing bwrap.

Random-per-install identity does not prove the Master §6.9 same-site requirement that multiple appliances at one site share one ULA. Site-level assignment authority and same-site/different-site, reboot, upgrade and restore tests remain open.

## 4. Hardware #327 — new config failure write-deny latch

- Current PR/docs head: 094564122f19c9e97157bb615bf9bae409f822a7.
- New firmware source commit: 5ad572f28fab4d5a018cdd4eb9ee395dd16ef69b.
- Parent #326: 58c558fb6a237935214621adc3dee65a10fe1a51.

The new source clears configImageReadVerified inside latchConfigPersistenceFailure(). This revokes same-boot EEPROM write authority after malformed/ambiguous configuration persistence failure, preventing the local setup-AP save path from overwriting the rejected image with defaults.

Exact focused evidence:
- Quarantine/readback [#44439616778](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439616778): PASS.
- Relay/output [#44439616678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439616678): PASS.
- Full PR [#44439616677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439616677) and push [#44439610252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439610252) both completed FAILURE at the QA-owned Controller protocol parity / Missing poll signature check. All 13 firmware/platform targets plus Android passed; downstream simulations, update bundle, signing, candidate gate and publishing were skipped.

Hardware explicitly requested QA add malformed v1/v2/unknown-schema followed by setup-AP save failure-injection cases. Those tests are not yet present. No QA-owned path was edited. Physical acceptance remains NOT TESTED.

## 5. Other role reconciliation

| Role | Current candidate | Evidence / blocker |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | #42698139210 scoped PASS; CORE ownership untouched |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | #43653329235 / #43653329229 PASS; physical acceptance absent |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | #42462978704 PASS; native COM bench absent |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 #43633486963 PASS; #292 no exact-head run |
| RELEASE #291 | 26e138acf2fbbb8890103fa1cfe2469e8efdd6ba | Build #44432976878 PASS; Windows #44432976880 fails because $buildWorkflow is uninitialized under StrictMode in negative-selftest.ps1; publisher skipped |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Synthetic receipt-v1 runs #44295049727 / #44295049903 PASS; no approved Master-v2 mapping |
| COE #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued, zero jobs; no migration acceptance |

## 6. Governance, private records and execution classification

Experiments AGENTS.md was read at d8777e3b58efc41caa5aa3c969c932aee9103d5f. The latest Library README_FIRST and BLAZE-COMMS/1 plus 00_MASTER_PROJECT_PHOENIX(1).txt were read. The canonical Cloud Artifact Policy and Storage Handover were read from BlazeDevStudio/BlazingSystems. COE AGENTS.md returned 404.

The private Drive registry v11 and newer corrections were not accessible. The exposed tool inventory had no Google Drive connector. A complete 1,422-item Library listing contained registry versions v3-v7 only; none was substituted and no private registry content or IDs were published.

Branch-protection reads returned 403 for Experiments main/development and COE main; repository rulesets returned empty arrays. Effective protection remains UNKNOWN pending administrator verification.

Automation ownership was respected: no CORE source or handover was modified, and no competing CORE worker was started.

**Actual checks:** GitHub source/PR/tree inspection, source-level test inspection, exact Actions run/job/log inspection. Master PR CI: no runs returned. Master Python suite: NOT RUN. Physical flash, GPIO/relay acceptance, real power cuts, native acceptance and 30-device soak: NOT TESTED.

## 7. Next exact owner actions

1. PHX-RELEASE: reconcile #44 with #35 current head 3455e0ce without force-push; obtain an authorized bubblewrap-capable runner.
2. PHX-QA: add both post-open overlay-entry race tests; add malformed legacy/unknown config followed by setup-AP save tests; independently review #327; replace positive poll-signature presence with negative default-deny tests.
3. PHX-CORE: define site-level ULA authority and the receipt-v1/v2 mapping.
4. COE integration owner: unblock #26 workflows and complete exact per-file blob/license/test/import provenance.
5. PISONET/RELEASE owners: repair the #291 StrictMode test initialization without Master editing the owned path.
6. Repository administrator: independently verify branch protections and required checks.
7. Registry custodian: restore authorized read-only private v11 access.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
