# PHX-MASTER UTC01 — exact-head Hardware ancestry, role CI and COE migration provenance audit

**Observed:** 2026-11-26 UTC01  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution boundary:** Strict NO CODEX. Coordination/phoenix only. No subsystem source or COE destination edits.

## 1. Control plane and exact refs

- Experiments issue #172 remains the control plane; the UTC00 Master checkpoint is present and no PHX-MASTER UTC01 checkpoint existed before this run.
- Cleanup issue #266 remains OPEN / 0-of-7. The global cleanup task is not complete; no broad moves or deletions were made.
- Experiments main: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 (branch metadata protected=false).
- Experiments development: blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 (protected=false).
- Active v0.6 development: blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Master branch before this update: phoenix/master-coordination @ 9eea910fe2a2851ffc4c091ae369144020d67716.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243 (protected=false).
- Master PR #288 was OPEN / DRAFT / UNMERGED, base main, 588 ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b, 226 paths all under coordination/phoenix.
- COE integration PR #26 remains OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12, base main@a6513ab, 205 changed files.
- Ownership manifest blob e4db324315a1b3543fec17a148fbf960170fcb29 remains 11 routes / DRAFT_REVIEW_ONLY; PHX-MASTER target is null and only owns coordination/phoenix.

The repository root AGENTS.md and README_FIRST / BLAZE-COMMS/1 protocol were reread. AGENTS-linked cloud policy and recovery handover were read from BlazeDevStudio/BlazingSystems main (policy blob 5e503925750c4e511314e4b7624579d82f60aae2; handover blob a15f14cb3baf46424b820e1a921462794422f06b). The policy makes GitHub the source-code authority and requires the private registry/sync ledger before Drive artifact work.

## 2. New owner-side progress: HARDWARE #340 ancestry reconciled

- PR #340 branch: phoenix/hardware-prepoll-intake-deny-20261122-utc01.
- Final docs/PR HEAD: a85eec4aa2ca1ad834f50031658f52aec51856e3.
- Source/test merge commit: a32c02311e4837669124c5b4b54fb1dfceed94fc; first parent 547148eeb4384df7971d17d762e3f12bc5dcab3c, second parent current parent #283 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30.
- The final docs commit is exactly one commit after the source/test merge and adds only the UTC01 ancestry handover.
- Current compare #283 → #340 final head: 45 ahead / 0 behind, merge base equals #283 4dd0b01. This is now reconciled; the earlier 4-behind condition is superseded.
- Owner used a two-parent merge and non-force fast-forward branch update. No force push, rebase, retarget, PR merge or Master source edit occurred.

The candidate sketches now de-energize/deny remote control before synchronous poll, discard poll/register response fields, and make applyRemoteConfig a deny-only compatibility sentinel. It does not implement positive response authentication or the approved CORE envelope.

### Exact final-head CI at a85eec4

| Workflow | Run | Result |
|---|---|---|
| Quarantine append/readback | [#45737856305](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856305) | PASS |
| Poll preflight inhibit | [#45737856314](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856314) | PASS |
| Mbed TLS SHA256 compatibility guard | [#45737856364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856364) | PASS — source-extracted simulation only |
| ESP8266 Arduino core 3.1.2 compile | [#45737856422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856422) | PASS |
| ESP32 Arduino core 3.3.13 compile | [#45737856339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856339) | PASS |
| Full BlazePwifi build | [#45737856635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45737856635) | PASS — 26 success / 4 skips |

The four Full skips are production signed APK import, prerelease publication, release publication and production-sign handoff. The Mbed TLS guard log explicitly reports SIMULATED_ONLY=1, TARGET_BUILD_REQUIRED=1 and COIN_ADMISSION_ENABLED=0. It is not an Arduino core 4.0.0 application compile. The Full ESP32 target build is core 3.3.13. The earlier source/test Full run #45737591616 was CANCELLED; the final docs-head Full run #45737856635 is the current exact PR-head result.

## 3. Active v0.6 response-auth P0 remains separate

Exact active branch blobs reread:
- ESP32 sketch 29f1125d52ff474a0d028ad41f7af201be1f0f9d.
- ESP8266 sketch 12c4bb82b6fddafe813674a0b5f692c1d3634073.
- CGI vendo db58041c0575ad0a1101d99cb85403e03c8dcb22.

Both active sketches have no response_sig token; poll consumes insert and target_nonce and invokes applyRemoteConfig. The CGI register/ping and poll response bodies lack response_sig, although member endpoints have signatures. Those endpoint signatures are not a poll contract. Active v0.6 remains not verified deny-only. #340 is not integrated into active v0.6.

COE #26 candidate exact blobs were also reread:
- ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887.
- CGI vendo 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e.

The candidate includes response_sig in poll/register, but both sketches retain sigOk=true and only enter verification when the controller key is nonempty. Empty-key bypass remains. The digest description/implementation also remains a CORE-owned standard-MAC contract issue. No exploit or live actuation test was performed.

## 4. Current role PRs and exact CI

| Owner / PR | Exact head | Current result |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; not financial acceptance. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API21/23 [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not invoked. |
| HARDWARE #340 | a85eec4aa2ca1ad834f50031658f52aec51856e3 | Final-head Full PASS; 26 success / 4 production import-sign-publication skips; no physical acceptance. |
| HARDWARE #348 | 93afd4830b2728d5976e21951610943e1ec96c85 | Focused #45731176550 PASS; Full [#45731176586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45731176586) FAIL at missing mbedtls/sha256.h under ESP32 core 4.0.0. |
| HARDWARE #349 | 1a2ecf5fa8c8c20a0095ac898c1bff254280ad27; source/test 9dc0ae39832e5fe7db79694b670a841f0c90ffe0 | Quarantine [#45724609180](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609180) and Relay [#45724609178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609178) PASS; Full [#45724609215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609215) FAIL at Missing poll signature check. |
| HARDWARE #352 | 0e984e267b3a8fb10c314800d1a7f120806354b7 | 43 ahead / 3 behind #349; Full [#45683122413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45683122413) FAIL at Controller protocol parity. |
| HARDWARE #353 | dc9cf634248ecc23f51f1477bd1769d63d3fe5ea | 17 ahead / 11 behind #352; no exact-head PR-triggered runs. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked; #292 no PR-triggered runs. |
| RELEASE #291 | 9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30 | Windows [#45669599214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599214) and Full [#45669599438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599438) fail CORE CURRENT_STATE freshness; ESP32 compatibility [#45669599322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599322) PASS; sign/publication skipped. |
| COE RELEASE #35 | 3cbc6580218c1575ae7fd49159d7e9bfd17960d8; source/test fdbbbbda | Shared [#45734911002](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45734911002): 240 PASS / 2 skips, then 10/10 ULA denials; sandbox [#45734910925](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45734910925): 42/42 host tests then missing Bubblewrap / exit 125; case [#45734910935](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45734910935) PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; scoped only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL at missing mbedtls/sha256.h. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued / zero jobs; FROZEN. |

No role branch was edited or taken over.

## 5. COE #26 exact source/destination migration recheck

Exact source: HARDWARE #349 at 1a2ecf5fa8c8c20a0095ac898c1bff254280ad27. Exact destination: COE #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. Both recursive trees are complete / non-truncated.

| Measure | Source | Destination |
|---|---:|---:|
| Tree entries | 2,553 | 286 |
| Blob files | 1,974 | 207 |
| ESP32/ESP8266 board blobs | 76 | 2 |
| Board-local Python helpers | 64 | 0 |
| Tests in mapped test directories | 47 | 19 |

- Only two board sketch paths map to the destination; both blobs differ, so 0/2 are exact and 74 source board blobs have no destination counterpart.
- Test identity: four same-relative-path tests, one exact blob/mode match, three divergent, 43 source-only and 15 destination-only.
- Source root NOTICE.md and product LICENSE are absent from destination root.
- No Hardware-specific SOURCE_INTAKE or MIGRATION_MAP was found; the historical PisoWiFi intake does not establish Hardware provenance.
- Five destination workflows remain queued with zero jobs.

**Decision:** COE #26 remains FROZEN / DRAFT_REVIEW_ONLY. No copy, move, overwrite, cherry-pick, staging, or destination write is authorized or performed.

## 6. Governance, branch protection and private registry

- Repository rulesets lists are empty for Experiments and COE.
- Branch metadata reports protected=false for Experiments main, Experiments development and COE main. The branch-protection detail endpoint returned 403, so no claim is made about the Master branch's classic protection. Administrators should configure/verify protected required checks.
- The private Drive registry v11 and newer corrections were not available. ChatGPT Library search surfaced v5, v6, v7, BLAZE_SYNC_LEDGER and its 2026-10-26 addendum, plus a 2026-11-09 production checkpoint; none is a substitute for v11.
- No Google Drive connector is exposed in this run. Per the Cloud Artifact Policy, status is BLOCKED / NOT_ACCESSIBLE; no Drive upload, folder creation, share change or private-data publication was attempted.

## 7. Execution and evidence classification

- GitHub source/tree/blob, PR, issue, branch and CI metadata inspections completed.
- Owner GitHub Actions results above are inspected exact-head evidence; they were not executed by PHX-MASTER.
- The Mbed TLS compatibility guard is source-extracted simulation only.
- Master repository Python unittest suite and verify_coordination.py were NOT RUN; no authenticated local checkout or Master Actions run/status is available.
- No native COM invocation, physical board test, coin pulse, relay/electrical recovery, LittleFS power-loss test, 150 power cuts or 30-device/24-hour soak was performed.

## 8. Next owner actions

1. HARDWARE retains #340 as a separate deny-only candidate; refresh #348's core-4 provider failure evidence and reconcile #349 → #352 → #353 ancestry in owner branches.
2. CORE publishes the approved authenticated register/poll response and mandatory nonempty key-provisioning contract.
3. HARDWARE implements only against that approved contract; QA independently validates positive and negative vectors on both boards.
4. RELEASE/INFRA obtain approved site-scoped ULA authority, a trusted Bubblewrap runner and fresh CORE handover evidence.
5. COE integration owner prepares per-file Hardware provenance, license and test identity before any migration staging review.
6. Registry custodian restores authorized access to v11 and newer corrections; repository administrators verify protected required checks.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.

No Codex, merge, release, signing, secret provisioning, hardware flash, real payment operation, physical test, or financial migration occurred.
