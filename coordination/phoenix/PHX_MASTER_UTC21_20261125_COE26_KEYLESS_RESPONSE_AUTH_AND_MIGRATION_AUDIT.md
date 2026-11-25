# PHX-MASTER UTC21 — COE #26 keyless response-auth bypass, digest-label mismatch, and migration provenance audit

**Observed UTC:** 2026-11-25T21:33:04Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** P0 response-contract and candidate migration audit  
**Disposition:** BLOCKED / COE #26 FROZEN / PRODUCTION NO-GO

## 1. Exact live refs

| Ref | Exact identity |
|---|---|
| Experiments main | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Product development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch / PR #288 starting HEAD | `phoenix/master-coordination@fe33a297108d8a3b0dc812f7b2a133fb78a14230` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership route manifest | `coordination/phoenix/OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29` |

PR #288 was OPEN / DRAFT / UNMERGED at starting HEAD `fe33a297`; base `main`; current main `6be5d19b`; merge base `f4e8a891`. The route manifest has 11 routes, status `DRAFT_REVIEW_ONLY`, and PHX-MASTER target `null`.

## 2. Exact candidate source pins

| File | Blob SHA |
|---|---|
| COE ESP32 sketch | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| COE ESP8266 sketch | `c8be98f72596681e36a3ad1f8939bf8046c96887` |
| COE CGI `vendo` | `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e` |
| COE `common.sh` | `ae00667da26c68c9e44a54a941887191029afc11` |
| COE UCI defaults | `532727f06d78c05b87fef28d1c0e89a7c5de8308` |
| COE Hardware test | `f921c56cecc19cab1989507b9b4ade1f45dac54e` |
| COE Hardware README | `99af3e5b46cd8b6f35c6479b204683f60c55ebcb` |

Active v0.6 source pins: ESP32 `29f1125d52ff474a0d028ad41f7af201be1f0f9d`, ESP8266 `12c4bb82b6fddafe813674a0b5f692c1d3634073`, CGI `db58041c0575ad0a1101d99cb85403e03c8dcb22`.

## 3. P0 finding — candidate keyless response-auth bypass

Static source inspection of both COE candidate sketches establishes:

1. ESP32 `loadConfig()` reads `cfg.key` with an empty default. ESP8266 `defaults()` zeroes the full config, including the key.
2. Both setup portals expose the controller-key field without HTML `required`; both save handlers only replace the stored key when the submitted value is nonempty.
3. Both register and poll response paths initialize `sigOk=true` and verify `response_sig` only inside a nonempty-key conditional. With an empty key the verification block is skipped and `sigOk` remains true.
4. A response body containing `"ok":true` can therefore reach the success branch without response authentication. The poll loop reads `insert` and `target_nonce` and invokes `applyRemoteConfig()`.
5. The setup portal communicates over HTTP. A network-forged `ok:true` response is not dynamically demonstrated here, but the source contains no response-auth check on the empty-key path. No unauthorized credit or physical actuation is claimed.

The router's `99-blazepwifi` first-boot UCI-defaults hook normally generates a random 18-byte `vendo_key`. That does not provision the same key into the controller's optional setup field. `common.sh` reads the UCI key, while `bp_check_vendo_sig()` does not independently reject an empty secret if the defaults hook is bypassed or fails. The candidate therefore needs explicit client and server key-presence gates, not only a random server bootstrap.

## 4. Digest and response-envelope mismatches

- `Hardware/README.md` calls the response construction `HMAC/SHA256(key | action | id | nonce | ... | key)`. Board code uses raw SHA-256 over a concatenated secret/message/secret string (`mbedtls_sha256`); CGI `bp_sha256` uses `sha256sum`. This is not a standard HMAC primitive. Do not describe it as HMAC until CORE approves the exact algorithm.
- `vendo_ping_sig()` binds action, ID, nonce and server time. `vendo_poll_sig()` binds insert, target nonce and expiry. The JSON response also includes a nested `controller` object, but that object is not covered by the response digest.
- Firmware `applyRemoteConfig()` reads top-level enable/config fields, while the CGI response places controller state inside `controller`. The response schema, signed-field set and consumer parser do not form a single canonical versioned contract.

## 5. Test adequacy

`Hardware/tests/test_firmware_hardening.sh` checks token presence with grep, performs a brace-balance scan, checks ESP8266 RNG tokens, and computes a separate Python SHA-256 example using a fixed nonempty test key. It does not execute the actual firmware verifier or CGI helper and has no test for empty/missing key, invalid signature, stale/replayed nonce, wrong controller/target, or altered nested controller data. The current test does not prove the claimed response-authentication invariant.

## 6. Active v0.6 source remains a separate blocker

At active v0.6 source HEAD `2fbd2475e9f54878c316fa7cea2f228386b0e859`, neither board sketch contains a `response_sig` verifier. The CGI `register|ping` and `poll` response blocks do not emit `response_sig` (the CGI has signatures on member endpoints, which are not a poll-response contract). The existing §7.20 finding remains valid: active v0.6 is not verified deny-only. COE #26's divergent candidate does not fix the active source branch and is not byte-identical migration evidence.

## 7. Exact migration provenance recheck

Complete recursive trees were fetched at current #353 docs head and COE #26; neither tree was truncated.

| Measure | Experiments #353 | COE #26 |
|---|---:|---:|
| Tree entries | 2,560 | 286 |
| Blobs | 1,981 | 207 |
| ESP32 subtree blobs | 16 | 1 |
| ESP8266 subtree blobs | 61 | 1 |
| Board-local Python helpers | 65 | 0 |
| Mapped tests | 47 | 19 |
| Additional `Hardware/tests` files | 0 | 1 |

Mapped test identity: 1 exact same-path blob+mode, 3 divergent same-path, 43 source-only, 15 destination-only. Firmware sketches differ: ESP32 source `1412cf57b70c6ee3061da9831b8d9abf6d58d94e` vs destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`; ESP8266 source `b99f1f21d8ad1e6df0e403b2b34507f97bd90c16` vs destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.

Licensing: root `NOTICE.md` and Tabler `LICENSE` exist in source but are absent in COE #26. Product, QRCode and TailAdmin license/notice counterparts were previously verified; no new license file was added.

Existing COE `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f` is schema 8, pinned to historical source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization`, not the current #26 branch. Its summary says 47 byte-identical / 14 derived, while its 61 runtime rows count 46 byte-identical / 15 derived. `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` carries the same historical pin and explicitly says NO-GO FOR SHOP INSTALL. Neither file is Hardware-specific provenance for current PR #26.

PR #26's body says the licensing/privacy P0-1 gate is resolved and removed. The exact current tree still lacks root NOTICE and Tabler LICENSE, and no Hardware-specific intake/map exists. That claim is not supported by the current candidate tree.

**Decision:** no staging, copy, move, overwrite, cherry-pick or destination write. COE #26 remains FROZEN / DRAFT_REVIEW_ONLY.

## 8. Current owner PR and CI reconciliation

| Owner / PR | Current head | Evidence / status |
|---|---|---|
| CORE #252 | `c82705f2` | Build #42698139210 PASS; scoped, not financial acceptance. CORE work remains reserved to its separate continuation. |
| RENTAL #328 | `10fc200b` | APK/API/auth #45622918340/#45622918364/#45622918551 PASS; shared #45622918468 FAIL (CORE freshness and missing `mbedtls/sha256.h`). |
| PISONET #255 | `d01fd164` | Synthetic Windows #42462978704 PASS; native COM not invoked. |
| HARDWARE #349 | `2a5c997a` | Focused checks PASS; Full #45603969181 FAIL at poll-signature assertion. |
| HARDWARE #352 | docs `0e984e26`, source/test `8eab8260` | Four focused workflows PASS; Full #45683122413 FAIL at missing poll signature. |
| HARDWARE #353 | docs `dc9cf634`, source/test `4f361e03` | Captured base `6d743ae` is 11 commits behind parent #352 `0e984e2` (13 changed paths). Latest known source Full #45698465506 and docs-head Full #45699196969 fail; no new PR-triggered runs returned for latest exact SHAs. |
| QA #290 | `5c29d159` | Synthetic Windows #43633486963 PASS; native COM not invoked. |
| QA #292 | `75a3f66d` | No PR-triggered runs. |
| RELEASE #291 | `9b928c9e` | Windows #45669599214 and Full #45669599438 FAIL at CORE CURRENT_STATE freshness; ESP32 compatibility #45669599322 PASS. |
| COE RELEASE #35 | docs `1789e314` | Shared #45704322384 FAIL; sandbox #45704322559 FAIL; case-collision #45704322556 PASS. Latest RELEASE checkpoint reports host preflight PASS but Bubblewrap unavailable. |
| COE CORE #45 | `9d76a134` | Overlay/Shell #44295049727 and case guard #44295049903 PASS; focused only. |
| COE INTERCON #49 | `aeb8ff11` | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared #44646341922 FAIL at missing `mbedtls/sha256.h`. |
| COE integration #26 | `b382d233` | Five workflows queued / zero jobs. Queued workflows are not CI acceptance. |

HARDWARE #353 stack remains owner-controlled; no rebase, retarget or branch rewrite was performed. CORE remains reserved to the separate `Blaze Production Continuation`; no competing CORE source work was started.

## 9. Master execution and limits

- Static source audit: **15/15 coordinator assertions PASS** across exact candidate and active-v0.6 blobs. These are source assertions, not firmware execution or product tests.
- Full recursive-tree and path/blob/mode/test/license comparisons were re-run at exact current SHAs.
- Master Python `unittest` suite: NOT RUN; no authenticated local checkout was available. Master GitHub Actions: no run.
- No native COM, board compilation, physical hardware, power-cut, soak, real-payment or migration test was run.
- `00_MASTER_PROJECT_PHOENIX(1).txt`, README_FIRST, COMMUNICATION_PROTOCOL, repository AGENTS.md, live control-plane issue, cleanup issue, route manifest, role PRs/CI, COE main and PR #26 were re-read.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain NOT_RECOVERED. No Google Drive connector is exposed. Library search surfaced older v3-v7 snapshots but they were not substituted. The AGENTS-linked Cloud Artifact Policy/Recovery Handover were not readable through the connected GitHub file action. No private IDs/content were copied to GitHub.
- Cleanup issue #266 remains OPEN / 0-of-7. No subsystem source or COE destination was changed.

## 10. Exact next owner actions

1. **CORE:** approve the versioned response schema, standard HMAC construction, canonical serialization, key provisioning and golden vectors; reject absent server secrets.
2. **HARDWARE:** require the controller key before network/polling; fail closed on empty key; authenticate the full envelope before any state/output change; refresh #353's stale parent ancestry with owner review.
3. **QA:** add source-exact negative tests for both boards and CGI, including keyless, malformed, invalid, stale, replayed, wrong-controller, wrong-target and nested-config tampering cases.
4. **COE integration owner:** reconcile per-file provenance, root NOTICE, Tabler LICENSE, Hardware-specific intake/map, README crypto wording and exact-head CI before any staging review.
5. **Registry custodian:** restore authorized private v11 and newer-correction access; do not mirror until canonical registry/ledger and policy are available.

**Production remains NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates all have independently verified evidence.