# PHX-MASTER UTC18 — strict JSON duplicate-key guard, exact role/CI refresh and COE #26 provenance

**Snapshot:** 2026-11-21T18:08:50Z (automation activation start)  
**Role:** PHX-MASTER only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/master-coordination  
**Starting HEAD:** 0fd192b09da50c33b9c49aac43982fc629c55706  
**Base:** main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**PR:** #288 OPEN / DRAFT / UNMERGED

## Scope and authority

The current Master PR has 155 changed paths, all under coordination/phoenix/. No CORE, RENTAL, PISONET, HARDWARE, QA, RELEASE, firmware, workflow, financial, payment or destination source path is owned by this run.

The canonical OWNERSHIP_ROUTES.json blob is e4db324315a1b3543fec17a148fbf960170fcb29: DRAFT_REVIEW_ONLY, 11 routes. PHX-MASTER remains coordination/phoenix/ with target null. No route was promoted or treated as migration authorization.

## Narrow code improvement — strict JSON object-key uniqueness

The offline coordination validator previously used Python json.loads directly for OWNERSHIP_ROUTES.json and COMMUNICATION_EXAMPLE.json. Standard JSON decoding silently keeps one value when an object repeats the same key. That can make a routing or communication record ambiguous across parsers.

Added load_json_strict(), using object_pairs_hook to reject duplicate decoded keys at every object depth. run_checks() now uses it for both canonical fixtures. The actual-file test setup also uses the strict loader. New regression cases cover duplicate top-level keys, nested duplicate keys, duplicate names created through JSON escape decoding, and repeated array values that must remain valid.

Focused isolated Python harness: 5/5 cases PASS. This executed the same strict-loader implementation and synthetic fixtures; it is not the repository unittest suite. Full coordination unittest suite: NOT RUN. Master GitHub Actions: no PR-triggered run returned for the starting HEAD.

## Exact refs read

| Ref | Exact SHA |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| v0.6 audit/development | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master start | 0fd192b09da50c33b9c49aac43982fc629c55706 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

The branch refs and PR API heads were fetched directly. No historical SHA was assumed.

## Exact source-main to COE #26 tree comparison

Both recursive trees were complete and not truncated.

| Tree | Entries | Blob entries |
|---|---:|---:|
| Experiments main | 2,340 | 1,764 |
| COE #26 | 286 | 207 |

| Manifest route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE OpenWrt library | 15 | 20 | 6 | 9 | 0 | 5 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone server | 7 | 4 | 0 | 1 | 6 | 3 |
| PISONET SoftTimer | 32 | 47 | 13 | 11 | 8 | 23 |
| HARDWARE ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| HARDWARE ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| RELEASE build workflow | 1 | 1 | 0 | 1 | 0 | 0 |

The broad RENTAL standalone profile route remains manual-file-mapping-required and was not treated as a recursive copy route. PHX-MASTER remains coordination-only and was not compared as a runtime migration route.

### License and NOTICE evidence

- Source BlazePwifi LICENSE and destination Pisowifi/LICENSE have identical blob SHA 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Source root NOTICE.md exists at blob f6d92cd21465312be5993631fe26977219be0fb9; COE #26 has no root NOTICE.md.
- COE #26 has no Hardware/LICENSE or Hardware/NOTICE.md.
- The matching Pisowifi-scoped LICENSE does not by itself resolve how the Hardware destination subtree would carry the source BlazePwifi license and notice obligations. Owner/legal scope review remains required.

No copy, move, staging, overwrite, rebase, cherry-pick, route promotion or destination edit occurred.

## Live role PR and exact-head CI

| Role / PR | Exact head | Current exact-head evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows release #42462978704 PASS |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered run returned |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity #44782114384 PASS; API21/API23 smoke #44782114393 PASS; build #44782114390 FAIL |
| HARDWARE #335 | d09b0c9dafad8dbbcda5723d8094f4975c14a274 | Quarantine #44932969401 PASS; Relay #44932969391 PASS; Full #44932969438 FAIL |
| RELEASE #291 | 42797e2f3d65c30a1070caf49c93aebec149d897 | ESP32 compatibility #44894604453 PASS; Full #44894604464 FAIL; Windows #44894604466 FAIL |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay #44295049727 PASS; case-collision #44295049903 PASS |
| COE RELEASE #35 | 7fd3d96833ed535b9f3d2c1922663cb9a864fd5e | Case-collision #44929601674 PASS; sandbox #44929601611 FAIL; shared #44929601659 FAIL |
| COE Stage 5 #48 | 8286548e395366f2332830025fed00ceebdfb24a | Stage #44643670696 PASS; case #44643670679 PASS; shared #44643670685 FAIL |
| COE Stage 5.1 #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage #44646341873 PASS; case #44646341992 PASS; shared #44646341922 FAIL |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued, zero jobs |
| Master #288 | 0fd192b09da50c33b9c49aac43982fc629c55706 | No PR-triggered runs returned |

### Failure details from exact job logs

- HARDWARE #335 Full validation fails at “Missing poll signature check” in the ESP8266 Vendo sketch. Fourteen target/Android build jobs succeeded; downstream simulation, signing and publishing jobs were skipped. The inherited positive fixture remains QA/CORE contract work.
- RENTAL #328 ESP32 compilation fails at missing mbedtls/sha256.h. APK identity and API smoke jobs pass; validate also failed. RENTAL owns its build/handover corrections.
- RELEASE #291 Full and Windows handover gates fail because source/workflow changes are newer than PROJECT_HANDOVER.md; the log names checkpoint adcae8141e673dc2147fcad50521ef3a23084d71. Windows build and publisher are skipped.
- COE #35 sandbox exits 125 because Bubblewrap is absent. Shared validation fails closed on all ten appliance profiles without an approved site-scoped RFC 4193 ULA /48; compile stages are skipped.
- COE #48 and #49 shared CI fail ESP32 compilation at missing mbedtls/sha256.h; their stage-specific and case-collision jobs pass.

CORE source ownership remains with its separate owner. No parallel CORE worker or CORE source edit was initiated.

## Governance and access

- Control-plane issue #172 remains OPEN. No PHX-MASTER UTC18 message existed before this checkpoint; a separate PHX-RELEASE UTC18 role lock is not a Master duplicate.
- Cleanup issue #266 remains OPEN, 0/7 checked. The broad cleanup inventory is not complete.
- Branch protection reads for Experiments main and COE main returned 403; rulesets endpoint returned an empty list. Effective protection remains UNKNOWN.
- AGENTS.md and the canonical public Cloud Artifact Policy and Cloud Storage Recovery Handover were read. The private Drive v11 registry and newer corrections were not surfaced by the Library search; no Google Drive connector is exposed. Older v6/v7 records were not substituted.
- The named separate CORE continuation was not visible in the active automation list; the CORE ownership boundary was nevertheless preserved. The active Hardware and Release automations remain separate.
- No private registry data, IDs, secrets, customer data or private artifact paths were published.

## Production gate

PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No merge, release, signing, secret provisioning, hardware flash, real-payment operation or physical test was performed.
