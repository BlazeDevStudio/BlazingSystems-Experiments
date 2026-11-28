# PHX-MASTER UTC20 — live exact-head, owner CI and COE #26 provenance audit

Observed: 2026-11-26T20:34:07Z  
Role: PHX-MASTER — Master Auditor / Integration Coordinator  
Execution: **STRICT NO CODEX**. One coordination-only change set; no subsystem source, destination, payment, firmware or release writes.

## 1. Scope and evidence method

Re-read CONTROL PLANE #172, cleanup-first #266, the uploaded Master execution prompt, README_FIRST, BLAZE-COMMS/1, Experiments AGENTS.md, the current Master coordination records, the live ownership manifest, the relevant role PRs and exact-head Actions, COE main and integration PR #26. Re-read the Library storage policy and recovery handover. All GitHub refs below were resolved live, not copied from an earlier checkpoint.

The private Google Drive registry `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were **NOT RECOVERED**. No Google Drive connector is available in this run, and Library search did not return that named v11 artifact. The available 2026-10-26 recovery handover is explicitly partial and does not satisfy the required v11 preflight. No older registry was substituted; no private Drive IDs or contents were copied to GitHub.

## 2. Exact live repository refs

| Repository / purpose | Exact ref |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Legacy v0.5.3 development | `blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 audit base | `blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master coordination (starting HEAD) | `phoenix/master-coordination @ ed6bb786c08d360a611e0e6c5c0505fa90d9b477` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration candidate / PR #26 | `integration/ecosystem-nonproprietary-candidate-20261111 @ b382d233ff06c8791b1028bed3c617cc7b670d12` |

The legacy v0.5.3 development line and active v0.6 audit base remain distinct; neither is silently substituted for the other.

## 3. Master PR #288 and ownership

PR [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) is **OPEN / DRAFT / UNMERGED**. At the start of this update its head was `ed6bb786c08d360a611e0e6c5c0505fa90d9b477`, base `main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, and live comparison was **642 ahead / 1 behind**, with **240 changed paths and zero outside `coordination/phoenix/`**. GitHub reported mergeable=true, but the base is one commit behind current main and the exact Master head has no PR-triggered workflow runs or combined statuses. No rebase, merge or force-push was performed.

The live `OWNERSHIP_ROUTES.json` blob is `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER owns `coordination/phoenix/` with destination `null`. The manifest still pins source_ref `f4e8a891` (the historical PR merge base, not current main) and destination PR #26 at `b382d233`. Its broad `Rental/` route is manual-file-mapping-only and explicitly not copy-permitted. No route authorizes recursive copy or migration.

**Master manifest structural audit: 8/8 assertions PASS** — schema, draft-only state, route count, Master target null, no copy authority, unique role/source pairs, Rental overlap quarantine, and destination PR/SHA pin. This is an in-tool structural audit, not the repository test suite.

## 4. Current role PR heads and exact-head CI

| Owner / PR | Exact current head | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS. No financial acceptance; CORE source untouched. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; scoped only. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | API21/23 smoke [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS. Shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL: mandatory handover freshness; ESP32 compile also fails because `mbedtls/sha256.h` is missing. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS. Native COM/device acceptance NOT TESTED. |
| HARDWARE #355 | docs HEAD `4e98613077b89e58ee66daa4ef40cfb257b2d962`; source/test `6b4f7a873dd72663c00c4e08f23131d58e662584` | Poll-deny [#45888075336](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45888075336) and Mbed TLS matrix [#45888075294](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45888075294) PASS. Native [#45888075305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45888075305) FAILS PAY-0745 because the QA assertion requires active `clearPending(true/false)` callsites. Full [#45888075373](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45888075373) FAILS `Controller protocol parity`; target compile jobs completed successfully. No physical acceptance. |
| HARDWARE #354 | `fc842342596786e072630179acfbbc4feeb2ba02` (source/test `145aac9607682071e2db05944a6f9db5aa06e524`) | Poll-deny [#45864684458](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684458) and Mbed TLS [#45864684325](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684325) PASS; Full [#45864684497](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684497) fails Controller protocol parity; Native [#45864684295](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684295) fails the same QA-owned active-clear assertion. Preserve deny-only and pending evidence. |
| HARDWARE #353 | `f527b33c9e391a9a66490388d96f06d6c8761dfa` (source/test `44de55a0e132cb15fdb60ecf85446e9490fa277e`) | Relay [#45871096516](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096516) and Quarantine [#45871096480](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096480) PASS; Full [#45871096425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096425) FAILS the inherited missing ESP8266 poll-signature check. No physical acceptance. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 has no exact-head PR run. |
| RELEASE #242 / #291 | `44708e127d6f03bc8458a190bfef98067a355255` / `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head PR runs/statuses. #242 base trails active v0.6 by 22 commits; #291 base trails current #242 head by 20 commits. Both mergeable=false; RELEASE owns stack/CI reconciliation. |
| COE RELEASE #35 | `6413e557eb2e552513eedae2bc6559646278b2f2` | Shared [#45882585001](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45882585001): 255 host tests pass / 2 skipped, then 10/10 appliance profiles fail closed because no approved site-scoped RFC 4193 ULA /48 is configured. Sandbox [#45882585016](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45882585016) FAILS because Bubblewrap is absent (exit 125). Case guard [#45882585024](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45882585024) PASS. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware/Contracts [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |

No owner branch was edited or retargeted by MASTER.

## 5. COE #26 destination/provenance gate

COE #26 is OPEN / DRAFT / FROZEN at `b382d233`, based on COE main `a6513ab4`; its recursive tree has 286 entries, PR reports 205 changed files / 85 commits. All five current PR workflows are still **QUEUED with zero jobs**: case-collision, Pisonet synthetic, Hardware/shared contracts, Rental standalone and PisoWiFi Overlay/Shell.

Exact current file readback found:
- `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`: 61 runtime rows recount as 46 byte-identical + 15 derived/review-required; its summary still declares 47 + 14. It pins source `6d4c9b48` and destination branch `feature/pisowifi-cleanup-stabilization`, not the current #26 branch. `hardware_tested`, `full_ci_tested`, `source_admission_complete`, and `release_authorized` are all false.
- `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` repeats the historical source and destination branch pins.
- `docs/audits/HARDWARE_FIRMWARE_AUDIT.md` blob `86c06e7574761465b80482430296eb712d985367` contradicts itself: an earlier section says the ESP sketches were not copied, while a later addendum says they were migrated under PR #27.
- Current #354 source ESP32 blob `3edbe38da543ef118b287f3e04c1601692cfa99f` differs from COE #26 `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`; ESP8266 source `b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9` differs from destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- The candidate tree contains only four LICENSE/NOTICE files (PisoWiFi and its QRCode/TailAdmin vendors); root and Hardware LICENSE/NOTICE counterparts are absent, as are the noted Tabler and BlazeRentalLauncher license counterparts.

The older test-identity counts are not promoted to current #355 provenance. Recompute exact file/test identities at current owner source/test heads before any future staging review. **No copy, move, overwrite, cherry-pick, recursive import or destination write occurred. COE #26 stays FROZEN.**

## 6. Test execution and blockers

- Exact-head owner GitHub Actions above were inspected; they are not claimed as Master tests.
- Master PR #288 has no exact-head Actions runs or combined statuses.
- Local `git ls-remote` failed because this runner could not resolve `github.com`; the Master Python suite and `verify_coordination.py` were therefore **NOT RUN**. Source/tree inspection and the 8/8 manifest assertions are not substitutes for repository tests.
- Cleanup-first #266 remains **OPEN / 0-of-7**; no role completion checkbox is claimed.
- Private Drive registry v11/newer corrections remain NOT_RECOVERED.

## 7. Next exact actions / release decision

1. PHX-QA must reconcile deny-only poll assertions with the current Hardware candidate: do not require unsigned `config_revision` or active pending-clear calls; assert that pending evidence remains preserved while admission is denied.
2. PHX-CORE must publish the approved versioned authenticated register/poll and receipt/disposition contract before HARDWARE changes poll consumption.
3. HARDWARE owns #355/#354 source, tests and handovers; preserve the deny-only boundary and refresh its own exact-head CI after QA/CORE contract review.
4. PHX-RELEASE owns #242/#291 ancestry and exact-head CI refresh; MASTER does not rebase or retarget those stacks.
5. COE integration owner must reconcile the current destination branch, source pins, firmware blobs, license/NOTICE counterparts, import completeness and test identities before any future migration proposal.
6. Registry custodian must provide the canonical private v11 registry and newer corrections through an authorized Drive connection before any artifact/migration write.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, flash, secret provisioning, live payment or physical test was performed.
