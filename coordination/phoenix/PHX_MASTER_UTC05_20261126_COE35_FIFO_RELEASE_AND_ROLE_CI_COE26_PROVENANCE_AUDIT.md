# PHX-MASTER UTC05 — exact-head COE #35 FIFO verifier, role CI and COE #26 provenance audit

**Observed:** 2026-11-26T05:39:01Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. GitHub connected-source inspection, exact recursive tree comparison, and Master-owned documentation only.

## 1. Live control plane, branch and ownership state

- CONTROL PLANE [issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) is OPEN. The latest current-date UTC05 worker checkpoint at start was PHX-RELEASE comment [#7183337214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7183337214). No current-date PHX-MASTER UTC05 message ID existed; this report is the single Master UTC05 checkpoint.
- Cleanup-first [issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) is OPEN, **0/7 tracks completed**. No role checkbox is claimed complete.
- Experiments exact refs: default main 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5; development aad3aade72c1156eecba1fed30907c6d0283b2c5; Master phoenix/master-coordination@0d4dc02e3262d35bea6125dbfde97d3d0f03d6ec.
- Master [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) is OPEN / DRAFT / UNMERGED. At start its head matched the remote Master branch. The PR has 230 changed paths, all under coordination/phoenix/. Live main is one commit ahead of the PR's recorded base; compare live main 6be5d19b to Master 0d4dc02e: **600 ahead / 1 behind**, merge base f4e8a891. No rebase, retarget, force-push or merge was attempted.
- COE default main: a6513ab4412b4c014eee2863e45cbe32d06cb243. COE [integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) is OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12, with five queued workflows and no completed jobs.
- Current OWNERSHIP_ROUTES.json is 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. Its source_ref=f4e8a891 is a historical routing baseline, not the current HARDWARE #353 source pin. The destination candidate remains #26 at b382d233; this manifest does not authorize a copy or move.
- Root AGENTS.md, README_FIRST, BLAZE-COMMS/1 COMMUNICATION_PROTOCOL, current Master coordination documents, and the linked public cloud artifact policy / recovery handover were re-read. CORE source remains reserved to its separate owner; no CORE source work or parallel CORE task was started.

## 2. Current role PR and exact-head CI matrix

| Owner / PR | Exact current head(s) | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped BlazePwifi build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS. Not financial acceptance. CORE remains owner-reserved. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API21/23 smoke [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/installer [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL at mandatory handover freshness and ESP32 compile. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED. |
| HARDWARE #340 | PR/docs f70f6af78c64ef86ba0f631faeb02b6cb6eb2725; source/test d1380acf80c0b631c5814d746dca36b2fad7a986 | ESP32 core 4.0.0 actual sketch compile [#45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648) PASS; Full [#45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) PASS, 26 successful jobs / 4 intentional production import/sign/publication skips. Cross-run binary reproducibility remains unproven. |
| HARDWARE #348 | 93afd4830b2728d5976e21951610943e1ec96c85 | Full [#45731176586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45731176586) FAIL: ESP32 core 4.0.0 compile cannot find mbedtls/sha256.h. #340 provider evidence is not a port to this branch. |
| HARDWARE #349 | 1a2ecf5fa8c8c20a0095ac898c1bff254280ad27 | Full [#45724609215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609215) FAIL at Controller protocol parity / missing poll signature assertion. |
| HARDWARE #352 | 2fa3b7db1161ddb531ed94bcf60617947fa1a7bd | Exact core compiles and focused Quarantine/Relay pass; Full [#45745420916](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45745420916) FAIL at Controller protocol parity. |
| HARDWARE #353 | docs/PR cb1787ac8f89562f20b6ecdee0c7969fbd12bd01; source/test ed2f77d5924172881f27222cc26649f8f85abe6c; parent #352 2fa3b7db | 29 ahead / 0 behind. Quarantine [#45756942179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942179) and Relay [#45756942276](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942276) PASS. Full [#45756942184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942184) FAIL at Controller protocol parity / missing poll signature assertion; 14 firmware/platform jobs and Android pass, downstream production/simulation/update/sign/publication/candidate jobs skip. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM NOT TESTED. #292 has no PR-triggered runs. |
| RELEASE #242 | a7e27fe50e13326a7258bbaed1388594141ddda3 | No exact-head PR-triggered Actions run or PowerShell execution evidence. |
| RELEASE #291 | final docs head 0441a8e5ead737a1a160b6e7eea0b4ec836f457f; source/test/workflow f556769bec30dea156f223f760547f76d99693ca | 873 ahead / 9 behind #242, merge base 734b89d9. Exact-head PR runs/statuses remain zero. Hosted toolchain-lock verification, artifact retention and reproducibility are UNVERIFIED. |
| COE RELEASE #35 | final head d628bb62f7b6d31bdc0b88b8816d57817bb9ca77; source/test 829662af6e454b1d53de6f732f5d475ecd6ed502; test-only RED cb663e205f276a1f5a6eb379969ae6acf8a3e3b0 | FIFO verifier correction is exact-source CI verified; final handover-head shared and sandbox gates still fail closed for ULA authority / Bubblewrap. Details in §3. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared ESP32 compile [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL at missing Mbed TLS header. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT / FROZEN; five workflows remain QUEUED, no completed jobs. No destination writes. |

## 3. New RELEASE evidence — COE #35 published-manifest FIFO correction

Static exact-source inspection at final PR #35 head d628bb62 confirms:

- tools/write_firmware_artifact_manifest.py::_verify_published_output() opens the manifest/checksum output relative to the pinned directory descriptor using O_RDONLY | O_NOFOLLOW | O_NONBLOCK.
- It then checks regular-file type, effective owner, single link, expected device/inode identity, reads the complete bytes, and rechecks the descriptor metadata/content.
- tools/test_firmware_artifact_manifest.py::test_verify_published_output_opens_nonblocking_before_rejecting_fifo creates a FIFO and asserts that the open flags include O_NONBLOCK.

Test-first evidence:
- Expected RED [#45760650056](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45760650056): 243 tests; the FIFO assertion failed as expected; two intentional skips.
- Exact-source GREEN push [#45760797475](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45760797475) and PR [#45760803647](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45760803647): 243 tests, 241 pass / 2 intentional skips; manifest durability marker emitted.
- Final handover-head shared [#45761155808](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45761155808): 243 tests, 241 pass / 2 skips; one synthetic staged profile passes, then 10/10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is absent; ESP32/ESP8266 compile jobs are skipped.
- Final handover-head sandbox [#45761155710](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45761155710): 42/42 host preflight tests pass; Bubblewrap is unavailable (exit 125), so namespace and mandatory sandbox packaging are skipped.
- Final handover-head case-collision [#45761155732](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45761155732): PASS.

This closes one narrow local manifest-verification availability defect only. It does not establish appliance admission, Bubblewrap isolation, firmware build/release, protected signing, financial durability, or hardware acceptance. PR #35 remains OPEN / DRAFT / UNMERGED.

## 4. Active v0.6 register/poll trust-boundary P0 remains open

Active branch remains blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859. Both board sketches consume poll insert / target_nonce and call applyRemoteConfig; the CGI poll response still lacks response_sig. COE #26's two destination sketches retain the keyless sigOk=true bypass. This is source-level evidence, not a demonstrated live exploit or unauthorized credit.

**Required order:** CORE publishes the versioned authenticated register/poll envelope, canonical serialization, standard MAC/HMAC construction, mandatory nonempty key provisioning, controller/target binding, freshness and replay rules; HARDWARE implements only after that contract; QA independently verifies both boards and negative/replay vectors. Do not invent a signature or weaken the inherited Full validation.

## 5. Exact #353 → COE #26 migration provenance

Both recursive Git trees were complete and non-truncated at the exact PR heads: source #353 cb1787ac... **2,572 entries**; destination #26 b382d233... **286 entries**.

| Route | Source blobs | Destination blobs | Same relative paths | Exact blob+mode matches | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| ESP32 → Hardware/esp32 | 16 | 1 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 → Hardware/esp8266 | 67 | 1 | 1 | 0 | 1 | 66 | 0 |
| Tests → Pisowifi/tests | 47 | 19 | 4 | 1 | 3 | 43 | 15 |

- ESP32 source sketch blob 1412cf57... differs from destination 3cc7ec54....
- ESP8266 source sketch blob b99f1f21... differs from destination c8be98f7....
- The only exact mapped test is one of four common relative paths; three common tests diverge. Forty-three source tests are absent from the destination and fifteen destination tests are destination-only.
- Source product LICENSE and destination Pisowifi LICENSE are the same Git blob 1ee55b94183417be977ca287cd7391f9a6f7e721 (1,071 bytes). Source root NOTICE blob f6d92cd2... has no destination root NOTICE counterpart. One matching product LICENSE does not establish complete per-file licensing/NOTICE compliance.

**Decision:** #26 stays FROZEN / DRAFT_REVIEW_ONLY. No staging, copy, move, overwrite, cherry-pick or destination modification. The stale manifest source_ref is not a substitute for current source blob pins or owner approval.

## 6. Registry, branch governance and execution limitations

- Exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Authorized Library title search surfaced historical v3–v7 snapshots only; they were not substituted. No Google Drive connector was exposed in this runtime. No private IDs or registry contents were published.
- Experiments rulesets API returned an empty list; branch-protection read returned 403. Effective required-check enforcement is UNKNOWN. The first branch-list page is capped at 100 entries and is not a full inventory.
- Master Actions at starting HEAD: zero workflow runs / zero combined statuses.
- Master Python suite and verify_coordination.py: NOT RUN; no authenticated local checkout is available. Owner CI above was inspected at exact SHAs, not executed by Master.
- Native COM, physical firmware/hardware, real power cuts, 30-device soak, payment and migration tests: NOT TESTED.

## 7. Master-owned change and verification

This UTC05 update is documentation-only on the existing PR #288 branch: ROLE_ASSIGNMENTS.md, INTEGRATION_MATRIX.md, AUDIT_SUMMARY.md, INDEX.md, and this new report. All changed paths remain under coordination/phoenix/. No subsystem source, COE destination, ownership manifest, secret, signing identity, payment state or hardware was modified.

Static assertions before commit: manifest parses with 11 routes and Master target null; current #353/#26 tree counts and per-route blob/mode comparisons match the table; product LICENSE blobs match and root NOTICE is absent at destination; #35 exact source contains O_NONBLOCK and the test asserts it; current UTC05 Master message ID is absent from issue #172 and PR #288.

## 8. Next exact actions

1. CORE: publish the authenticated register/poll response contract and mandatory key-provisioning/freshness/replay vectors.
2. HARDWARE: resolve the inherited #353/#352/#349 poll-signature parity failure only against the approved contract.
3. QA: independently review COE #35 source/test commits cb663e20 / 829662af and verify both firmware boards and negative authentication vectors.
4. COE RELEASE / INFRA: obtain owner-approved site-scoped ULA /48 authority and a disposable unprivileged Bubblewrap runner; no privileged install or unsandboxed fallback.
5. RELEASE / INFRA: dispatch exact-head #291 lock/artifact workflows and retain byte-identical two-clean-build evidence; CORE must first publish the canonical freshness SHA.
6. Registry custodian: restore authorized provenance-only access to private v11 and newer corrections.
7. Repository administrator: independently verify branch protection and required-check enforcement.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and explicit owner-authorized release gates are independently evidenced.

No merge, rebase, release, signing, secret provisioning, firmware flash, physical test, real-payment operation, customer cutover or financial migration occurred.
