# PHX-MASTER UTC06 — COE #35 manifest durability, exact role CI, and integration boundaries

**Audit time:** 2026-11-21T06:35:21Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository migration provenance.  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow, or delegation.  
**Disposition:** Master coordination update PR-ready; overall integration BLOCKED; COE #26 FROZEN; PRODUCTION NO-GO.

## 1. Live control-plane and repository identity

- Experiments default branch: main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Active v0.6 development branch: blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Legacy v0.5.3 development branch: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5.
- PHX-MASTER branch before this update: phoenix/master-coordination at d203c82ca2a594e5b17c859d1c15cf6608303d45; PR #288 OPEN / DRAFT / UNMERGED, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b, 148 changed paths before this update, all under coordination/phoenix/.
- CoinOperatedEcosystem main: a6513ab4412b4c014eee2863e45cbe32d06cb243. Frozen integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT.
- Routing manifest: OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null. The live JSON parsed successfully and seven structural assertions passed: schema, status, 11 routes, single Master route, Master target null, non-copyable Rental root guard, and unchanged candidate #26 identity.
- Issue #172 and cleanup #266 were re-read. Cleanup remains OPEN / 0 of 7 checked.
- Experiments root AGENTS.md, README.md, the BLAZE-COMMS/1 protocol, uploaded Master directive and README_FIRST were read. The cloud artifact policy and public storage-recovery handover were also read. No root AGENTS.md was found in COE.
- The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not accessible. Library search returned older v3-v7 registry snapshots only; none was substituted. No Google Drive connector is exposed in this runtime. No private registry data was copied or published.

## 2. COE RELEASE #35 — source-level durability review

**PR:** https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35  
**Branch:** phoenix/release-build-script-publication-safety-20261117  
**Base/parent #31:** 59ed44d0b911e176f1a95b9cf5585ef811ffd31b  
**Current PR/docs head:** 93bab4c97e2a487a3223dc209c5be8fbbc609b5c  
**Source/test head:** 3f4028aec38f922e197fa25bd54bf31cdd4c31cd  
**Test-first commit:** ea08e48b66be4d8d912fa42797fd707dd98d2e17  
**Current file blobs:** packager 2dbe5636c93e165e2fa8f1381dbd3f435d0363f3; tests ac1de367a15dcb8a286184dec8b52dfb37197f9c; handover d85df18e9d970ae1f163cf2dab48887b5ad62980.

The generated wrapper publishes RELEASE_MANIFEST.sha256 with a same-directory no-overwrite hard link. The new finalizer pins the directory with O_DIRECTORY | O_NOFOLLOW, opens the final manifest relative to that descriptor with O_NOFOLLOW, checks regular-file and inode/link identity, fsyncs the final manifest, fsyncs the directory before cleanup, unlinks the two temporary names relative to the pinned directory, then fsyncs the directory again. Open/stat/fsync/unlink errors stop packaging with a nonzero RELEASE-BLOCKED result. The release-owned source and test files were inspected at the exact current PR head; Master did not modify them.

### Exact CI evidence

| Run | Result | Exact interpretation |
|---|---|---|
| [RED #44875832118](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44875832118) | Expected FAIL | Test-only head: 124 packaging/tool tests, two intentional skips; both new manifest-durability assertions failed before the source fix. |
| [Source/test #44876039985](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876039985) | Partial PASS / gate FAIL | 124 PASS / 2 intentional skips, including the new finalization tests; all 10 appliance profiles then failed closed because no approved site-scoped RFC 4193 ULA /48 is defined; board compiles skipped. |
| [Current-head shared #44876192956](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876192956) | Partial PASS / gate FAIL | Current docs head repeated 124 PASS / 2 intentional skips, then the same 10-profile ULA authority failure. ESP32/ESP8266 compile jobs skipped. |
| [Current-head case collision #44876192979](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876192979) | PASS | Case-collision guard and unit tests passed. |
| [Current-head sandbox #44876192967](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44876192967) | FAIL CLOSED | Host preflight 14/14 PASS; Bubblewrap is absent, exit 125. Unprivileged identity, namespace probe and sandbox-dependent packaging tests were skipped, not passed. |

### Master review finding — test coverage request, not a source defect

The success-path regression verifies file → directory → directory fsync order and checks that the final manifest remains while temporary names are removed. The failure-path regression patches fsync to raise on its first call, proving the manifest-file sync failure preserves the final and temporary names.

It does not separately inject failure on the second fsync — the pre-cleanup directory fsync that persists the final published name. Request PHX-RELEASE add a second-call failure test that allows the file fsync, raises on the directory fsync, and asserts a nonzero blocked result plus preservation of the final and both temporary names. PHX-QA should independently review the exact source/test SHA. This is a coverage gap, not evidence that the implementation is wrong.

Hosted filesystem-call-order CI is not a physical power-cut test, not a storage-controller durability guarantee, and not actual ImageBuilder sandbox execution.

## 3. Current role PR and CI reconciliation

| Owner | Current PR / exact head | Evidence and remaining boundary |
|---|---|---|
| CORE | Experiments #252, c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS, scoped. CORE source and canonical handover remain with the separate owner. |
| RENTAL | Experiments #328, 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity #44782114384 PASS; API21/API23 #44782114393 PASS; shared build #44782114390 FAIL. Rental owns Android/APK; CORE owns canonical handover; ESP32 core 4.0.0 mbedtls/sha256.h remains a toolchain/source blocker. |
| PISONET | Experiments #255, d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows #42462978704 PASS, scoped. Native COM/PnP/race and physical serial acceptance NOT TESTED. |
| HARDWARE | Experiments #327 docs head a873042c2a59a2197e4b4457c18dc75da12a0d02; source/test 3292d2a1e207da4241189952eec0e97255a48475 | Quarantine #44873105133 PASS; Relay/output #44873105198 PASS; Full #44873105141 FAIL at QA-owned Missing poll signature check after 15/15 target/platform jobs PASS. Firmware remains default-deny. |
| QA | Experiments #290 head 5c29d15994cee1279058f1eca12f2a3180704292; #292 head 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows #43633486963 PASS, scoped; #292 has no PR-triggered CI and retains historical Master base b1ca02e2087f3b1a7169ceab9c34e52646e700df. Native COM acceptance and current-head verifier retest remain unproven. |
| RELEASE | Experiments #291 head f06ac4df2f61b9c39a03a6ff6009b32948b94778 | Compatibility #44862405800 PASS 3/3 only for older Hardware pin 268ca9bde6d3710b418134ffd328060250fad42f / ESP32 blob 09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79. Full #44862406950 and Windows #44862405809 FAIL. Current #327 modifies both board sketches; old compatibility PASS is valid only for its immutable old pin. RELEASE must re-pin and rerun. |
| COE RELEASE | COE #35 docs head 93bab4c97e2a487a3223dc209c5be8fbbc609b5c; source/test 3f4028aec38f922e197fa25bd54bf31cdd4c31cd | 124 tests PASS / 2 intentional skips; all 10 profile admissions fail closed for missing approved ULA /48; case collision PASS; mandatory sandbox fails because Bubblewrap is missing. |
| COE integration | COE #26 head b382d233ff06c8791b1028bed3c617cc7b670d12 | Five candidate workflows QUEUED / zero jobs. Remains FROZEN. |

### Separate COE INTERCON Stage 4/5 chain

COE PRs #46 → #47 → #48 → #49 are separate OPEN/DRAFT branches, not routes in OWNERSHIP_ROUTES.json and not part of Phoenix destination #26. Their focused stage tests and case-collision checks pass, but the overall hardware workflow fails at ESP32 compile. The #48 and #49 logs identify missing mbedtls/sha256.h under ESP32 core 4.0.0; #49 ESP8266 compile and shared/profile validation pass. Keep this chain with its own owner; no Master migration or merge action.

## 4. Frozen destination and exact migration provenance

The prior complete, untruncated tree comparison remains applicable because current HARDWARE #327 docs head a873042c2a59a2197e4b4457c18dc75da12a0d02 and COE #26 head b382d233ff06c8791b1028bed3c617cc7b670d12 have not changed:

- Experiments source: 2,463 tree entries / 1,884 blobs.
- COE #26 destination: 286 tree entries / 207 blobs.
- ESP32 route: 16 source / 1 destination / 0 identical.
- ESP8266 route: 26 source / 1 destination / 0 identical.
- QA route: 47 source / 19 destination / 1 identical / 3 divergent / 43 source-only / 15 destination-only.
- 30 source board-local Python labs/helpers have no destination Hardware equivalent.
- Source root NOTICE has no COE root counterpart; Hardware-specific license/NOTICE applicability remains unresolved. Pisowifi LICENSE identity alone does not settle Hardware licensing.

This activation did not rerun the recursive tree walk; the exact source and destination refs remain unchanged from the prior complete comparison. No staging, copying, moving, overwriting, rebase, cherry-pick, route promotion or destination edit occurred. The route manifest remains DRAFT_REVIEW_ONLY with Master target null.

## 5. Cleanup, tests, access and governance

- Cleanup #266 remains OPEN / 0 of 7. The broader duplicate/dead-code inventory and inbound-reference audit are incomplete; no mass deletion or renumbering was performed.
- Seven structural assertions on the live routing JSON passed. This is a small runtime manifest sanity check, not the source-exact Python verifier.
- A normal Git clone of the exact Master branch was attempted but failed because this runtime could not resolve github.com. The full Master Python coordination suite was NOT RUN. Master exact-head Actions inventory has no run.
- Branch metadata reports protected=false for the inspected refs, but the branch-protection detail endpoint returns 403 and organization-level rulesets are not independently verified. Effective protection is UNKNOWN; repository administration must verify it.
- The private registry v11 and newer corrections remain BLOCKED. No Google Drive connector is exposed. Library search surfaced older v3-v7 snapshots only; none was substituted. No Drive artifact was created.
- No CORE, RENTAL, PISONET, HARDWARE, QA, or RELEASE source branch was changed. No private registry data, secret, financial state, customer/payment system, or destination tree was touched.

## 6. Required next owner actions

1. PHX-RELEASE: add the second-fsync failure-injection regression, rerun exact-source packaging tests, and independently document the failure-preservation behavior.
2. PHX-QA: review the exact COE #35 source/test SHA and the failure behavior; correct the inherited positive poll-signature fixture only after CORE publishes the authenticated poll/receipt contract.
3. PHX-RELEASE: refresh Experiments #291 to the current HARDWARE #327 source/test identity and rerun the two-core compatibility and reproducibility matrix.
4. Site/network authority: provide the real approved site-scoped RFC 4193 ULA /48. Do not invent or substitute a prefix.
5. Runner/infrastructure owner: provide trusted pre-provisioned Bubblewrap and a working unprivileged namespace. Do not install privileged dependencies or add an unsandboxed fallback.
6. CORE's separate owner: refresh canonical handover and publish the authenticated poll/receipt contract; Master does not take over CORE.
7. COE integration owners: keep #26 frozen until per-file source/test identity, license/NOTICE applicability, complete imports, and exact-destination CI are independently accepted.
8. Repository administrator: verify classic protection and organization rulesets for main, development, and Master branches.

## 7. Safety disposition

No subsystem source, ownership manifest, COE destination tree, private Drive record, secret, signing key, financial state, or customer/payment system was changed. No merge, release, signing, hardware flash, physical test, or migration was performed.

Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory.

**PRODUCTION NO-GO.**
