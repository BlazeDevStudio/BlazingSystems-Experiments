# PHX-MASTER UTC22 — Hardware stack reconciliation, response trust boundary, and COE #26 hold

**Observed:** 2026-11-25T22:51:17Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX.  
**Scope:** Master-owned coordination and architecture records only.

## 1. Live refs and control state

| Ref | Exact observed SHA / state |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch / PR #288 start | 22c20eeb444bda86a177035b9b1c438b8c715bdb |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| OWNERSHIP_ROUTES.json | e4db324315a1b3543fec17a148fbf960170fcb29 |

PR #288 was OPEN / DRAFT / UNMERGED at the start. Its 223 changed paths were all under coordination/phoenix/. Compare against main: 583 ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. The route manifest has 11 routes, status DRAFT_REVIEW_ONLY, and PHX-MASTER has no destination target. Cleanup #266 remains OPEN with 0 of 7 checklist items checked. Issue #172 remains OPEN.

## 2. Three independent HARDWARE stacks — do not combine or rewrite

### 2.1 HARDWARE #340 — poll-response discard guard

- PR #340 OPEN / DRAFT / UNMERGED; branch phoenix/hardware-prepoll-intake-deny-20261122-utc01.
- PR/docs HEAD 547148eeb4384df7971d17d762e3f12bc5dcab3c; source/test SHA 0dcd64f5335f49aec0550bfd8fc7b65b35c12e24.
- Captured base 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d; current #283 HEAD 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30. #283 is 4 commits ahead of the captured base; #340 is 43 ahead / 4 behind current #283, merge base 88581eef. HARDWARE must refresh this stack; MASTER did not rebase/retarget.
- Exact #340 sketch blobs: ESP32 fc883d20ef76ec5521a5872a175ec73a16cf8cbe; ESP8266 c7b31b573123a73b22f41309025926c9b181fc7f. Both loops deny before and after the synchronous poll and explicitly discard its response with (void)post("poll"). applyRemoteConfig() is a no-op deny stub; no poll body is applied.
- Focused runs: Poll Preflight #45708073648, Quarantine #45708073619, Mbed TLS guard #45708073590, ESP8266 core #45708073585, ESP32 core #45708074035 — all PASS.
- Full BlazePwifi build #45708073607 PASS: 26 jobs successful, 4 production import/sign/publication jobs skipped, zero failures.

This is a consumer-side deny/discard mitigation and CI build evidence, not authenticated poll-response support, a signed candidate, or hardware acceptance.

### 2.2 HARDWARE #348 — non-actuating ControllerAuthV1Lab helper

- PR #348 OPEN / DRAFT / UNMERGED; branch phoenix/hw-controller-auth-nonempty-spans-20261123-utc15.
- Current docs/PR HEAD 8bdddfb88630c0c9675f7e4a47ab640f5d17f699; source/test commit 659b1e646ba6d3efdbe6e03df4ab4f170a89f0e1.
- Parent #254 exact HEAD 84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9; #254 remains stacked on Phase-A deny #239 at d83b715b116185107737fef721c2eece8feebf39.
- Six changed files are handovers, the lab header, and its native test. No production sketch or CORE API changed.
- ControllerAuthV1Lab.h now rejects null pointers and zero-length fixed comparisons, empty raw-policy spans, and empty canonical-message spans. It supports Mbed TLS 2.x/3.x only; Mbed TLS 4 needs a separately reviewed PSA adapter. The helper never admits coins or touches GPIO; the native test uses a synthetic key.
- Focused native CI #45715616078 / job 139560779561 PASS: exact checkout, Mbed TLS 2.28.8, C++17, warnings-as-errors, ASan/UBSan, boundary cases and Phase-A deny all passed. Full #45715616079 is CANCELLED / no jobs returned; no Full pass is claimed.

This helper is not a complete producer/consumer protocol, key-provisioning path, protected witness, or monetary authority. QA review remains required.

### 2.3 HARDWARE #349 → #352 → #353 stack

- #349 HEAD 2a5c997add4f49fcd74f753101d3a9daac0040bf; focused Quarantine/Relay PASS; Full #45603969181 FAIL at poll-signature assertion.
- #352 HEAD 0e984e267b3a8fb10c314800d1a7f120806354b7; source/test 8eab8260. Quarantine, Relay, ESP8266 and ESP32 focused workflows PASS; Full #45683122413 FAIL at Controller protocol parity.
- #353 HEAD dc9cf634248ecc23f51f1477bd1769d63d3fe5ea; source/test 4f361e032c30faa368105775e3646c570f9760a8. No PR-triggered runs at the current exact head. Captured base 6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec is 11 commits behind current parent #352 at 0e984e267b3a8fb10c314800d1a7f120806354b7. HARDWARE owns the stack correction.

#340, #348, and #349/#352/#353 are three distinct stacks. MASTER does not cherry-pick or rebase across them.

## 3. Response-authentication boundary — exact source distinction

### Active v0.6 producer/consumer

At active development HEAD 2fbd2475e9f54878c316fa7cea2f228386b0e859:
- ESP32 sketch blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d and ESP8266 sketch blob 12c4bb82b6fddafe813674a0b5f692c1d3634073 contain no response_sig token; both consume poll data and call applyRemoteConfig().
- CGI blob db58041c0575ad0a1101d99cb85403e03c8dcb22: register|ping and poll response bodies have no response_sig. Other member API actions do emit response_sig; do not generalize this to the whole CGI.
- The active v0.6 register/poll path remains an unauthenticated response boundary. Keep the P0 contract blocker open.

### #340 deny-only consumer branch

#340's current ESP32/ESP8266 sketches discard poll responses and keep remote configuration disabled. This reduces response consumption in that branch but does not create an authenticated response contract or resolve the active v0.6 producer mismatch.

### COE #26 candidate

At COE #26 exact head b382d233ff06c8791b1028bed3c617cc7b670d12:
- ESP32 blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 and ESP8266 blob c8be98f72596681e36a3ad1f8939bf8046c96887 retain the keyless bypass: sigOk starts true and verification is conditional on a nonempty controller key.
- ESP32 calls LittleFS.begin(true); ESP8266's mount-failure path formats LittleFS. Both expose a quarantine-clear HTTP handler; no independent operator authorization check was observed in the handler.
- CGI blob 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e emits response_sig for register/poll, but the response binding and firmware parser do not form a complete canonical envelope. The UTC21 audit records the raw concatenated SHA-256 versus HMAC documentation mismatch and omission of nested controller data from the signed message.

This is source-level evidence, not a demonstrated live exploit or proof of unauthorized financial credit. COE #26 remains FROZEN.

## 4. Current owner PR and CI matrix

| Owner / PR | Exact current HEAD | Latest exact-head evidence / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS; scoped only, not financial acceptance. CORE ownership remains with its separate continuation. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | APK identity #45622918340, API21/23 #45622918364, auth/recovery #45622918551 PASS; shared #45622918468 FAIL at CORE freshness / missing ESP32 mbedtls/sha256.h. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS; native COM not invoked. |
| HARDWARE #340 | 547148eeb4384df7971d17d762e3f12bc5dcab3c | Five focused checks and Full #45708073607 PASS; four production import/sign/publication jobs skipped; base 4 commits behind #283. |
| HARDWARE #348 | 8bdddfb88630c0c9675f7e4a47ab640f5d17f699 | Focused native sanitizer #45715616078 PASS; Full #45715616079 CANCELLED / no jobs. Helper-only. |
| HARDWARE #349 | 2a5c997add4f49fcd74f753101d3a9daac0040bf | Focused Quarantine/Relay PASS; Full #45603969181 FAIL at poll-signature assertion. |
| HARDWARE #352 | 0e984e267b3a8fb10c314800d1a7f120806354b7 | Four focused workflows PASS; Full #45683122413 FAIL at Controller protocol parity. |
| HARDWARE #353 | dc9cf634248ecc23f51f1477bd1769d63d3fe5ea | No current PR-triggered runs; captured parent base 11 commits behind #352. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Synthetic Windows #43633486963 PASS; native COM not invoked. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs. |
| RELEASE #291 | 9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30 | Windows #45669599214 and Full #45669599438 FAIL at CORE CURRENT_STATE freshness; ESP32 compatibility #45669599322 PASS. |
| COE RELEASE #35 | 6a783576297dd612176289cfb0f654e4ff8eb6a1 | Shared #45711676706 FAIL at site-ULA profile gate; sandbox #45711676601 FAIL (Bubblewrap unavailable / timeout); case guard #45711676365 PASS. Latest role checkpoint: host preflight 42/42; shared suite 236 run, 234 pass + 2 skips; 10/10 site-ULA profiles fail closed. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell #44295049727 and case guard #44295049903 PASS; focused only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared #44646341922 FAIL at missing mbedtls/sha256.h. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued, zero jobs; FROZEN. |

Owner CI is not Master-executed product testing. PASS labels above are limited to the named exact runs.

## 5. COE migration and destination gate

The current routing manifest remains 11 routes / DRAFT_REVIEW_ONLY / Master target null. COE #26 remains OPEN / DRAFT / UNMERGED with 205 changed files and five queued workflows / zero jobs.

The last complete exact recursive-tree audit at unchanged #353/#26 heads recorded:
- Source / destination: 2,560 / 286 tree entries.
- Board firmware blobs: 77 / 2.
- Board-local helpers: 65 / 0.
- Test files: 47 / 19; identity: 1 exact, 3 divergent, 43 source-only, 15 destination-only.
- Root NOTICE and Tabler LICENSE are missing from the candidate.
- Existing PisoWiFi intake is from a different historical source/target branch and its declared counts do not match its runtime rows.

No staging, copy, move, overwrite, cherry-pick, or COE destination write was performed. A new move is not proposed.

## 6. Verification and limitations

**Executed:** live branch/PR/issue reads; exact source-file reads; current role workflow/job reads; branch ancestry comparisons; coordinator-side static assertions for PR path scope, route count, cleanup checklist, source token/poll behavior and stack drift.

**Not executed:** Master Python unittest suite, Master GitHub Actions, native COM, physical hardware, power-cut tests, 30-device soak, financial migration, signing or production acceptance.

The private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain NOT_RECOVERED. Library search surfaced older v5-v7 snapshots only; no connected Google Drive tool is available. No older snapshot was substituted and no private IDs/content were published. AGENTS.md was read at main blob d8777e3b58efc41caa5aa3c969c932aee9103d5f; its linked Cloud Artifact Policy / Storage Handover could not be fetched through the available GitHub connector.

## 7. Required next owner actions

1. HARDWARE refreshes #340 against current #283 and #353 against current #352, preserving separate stacks.
2. CORE publishes the approved versioned register/poll response envelope, canonical serialization, HMAC algorithm, controller-key provisioning and golden vectors.
3. HARDWARE implements verification-before-consumption only against that approved contract; keep deny/discard until then.
4. QA independently tests both boards, CGI and negative cases: empty key, missing/invalid signature, replay, stale nonce, wrong controller/target, malformed/duplicate JSON and nested configuration tampering.
5. COE integration owner completes per-file source intake, license/NOTICE parity, import completeness, test identity mapping and exact-head destination CI before any staging review.
6. RELEASE/INFRA resolve site-ULA authority and provide an authorized Bubblewrap-capable runner.
7. Registry custodian restores authorized access to private v11 and newer corrections.

**PRODUCTION NO-GO remains mandatory:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak, and owner-authorized release gates are still required.
