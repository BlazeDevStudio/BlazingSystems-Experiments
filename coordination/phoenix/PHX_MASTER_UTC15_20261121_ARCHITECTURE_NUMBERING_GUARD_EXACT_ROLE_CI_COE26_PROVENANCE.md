
# PHX-MASTER UTC15 — exact-head role/CI, architecture numbering guard and COE #26 provenance

Audit timestamp: 2026-11-21T16:00:42.378Z. Strict NO CODEX. Master scope only: coordination/phoenix/, architecture/interface contracts, migration provenance and integration matrices.

## Exact refs
- Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b; active v0.6 development 2fbd2475e9f54878c316fa7cea2f228386b0e859; legacy v0.5.3 development aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch and PR #288 head d02335240eb8cdc7f7e671beb53f721ffd13247c; base main f4e8a891aed8af86d5fd315d28750a0ac3a7372b; OPEN/DRAFT/UNMERGED.
- COE main a6513ab4412b4c014eee2863e45cbe32d06cb243; COE #26 b382d233ff06c8791b1028bed3c617cc7b670d12 OPEN/DRAFT/FROZEN.
- Manifest e4db324315a1b3543fec17a148fbf960170fcb29: DRAFT_REVIEW_ONLY, 11 routes, PHX-MASTER target null.
- PR #288 started with 153 changed paths, all under coordination/phoenix/. This adds one report path; no subsystem source paths changed.
- Branch API reports protected=false for main, v0.6 development and Master; rulesets empty; classic protection detail 403. Effective protection NOT ESTABLISHED.

## Role PRs and CI
| Role | Exact heads | Current evidence |
|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4; COE #45 9d76a134c1f6512aa40c20ec4d247306a71a8cce | #252 build and #45 overlay/case-collision PASS. CORE remains separate. |
| RENTAL | #240 a7d113fb8ae3f0c5e838e64d31cae7a154e37b56; #287 a4fffd01c8fb1818c32a53522e0590c1dc8a77cd; #289 68928774d0d7cf65adb26bc6b54199a3159d066c; #328 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | #328 identity/API PASS; ESP32 build FAIL: mbedtls/sha256.h missing; handover freshness FAIL at 468adc8129ea311e13f4c5c63eb6bb01ca67ecb0. |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09; COE #28 b21b04617d38a177260258de2d56b24382822117, #30 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc, #32 29b6fe08b10688182d981a66745f482758bd6630 | Scoped CI PASS; native COM acceptance NOT TESTED. |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows PASS; #292 no PR CI and base behind Master. QA owns the inherited poll-signature fixture. |
| HARDWARE | #327 827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8; #329 41efc1ddf4a101d7d1cb4428dcea2662ade6936e; #330 1a1e5e25834748fbba95d6253eb668f29b6c82f8; #331 33a32ef092f22718cbda141baee75b54323986ff; #332 9f1d9ebf9c7256da2e8eace4bc0be510f6566daa; #333 e93d178bbe3fcf6a7ba7f3a049f996de10727750 | #329 focused Quarantine/Relay PASS, Full FAIL. #333 Quarantine PASS; Full fails QA-owned Missing poll signature check after 14/14 target/platform jobs pass; downstream jobs skipped. Stack unchanged. |
| RELEASE | #291 42797e2f3d65c30a1070caf49c93aebec149d897; COE #35 b4f23d6cd297f51425bd927833f62bd0471918b6 | #291 compatibility PASS; Full/Windows fail handover freshness at adcae8141e673dc2147fcad50521ef3a23084d71. #35 140 tests PASS / 2 SKIP, ten profiles fail closed without approved ULA /48; sandbox fails because Bubblewrap absent; case-collision PASS. |
| COE integration | #26 b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED, zero jobs. |

## Exact #333 to COE #26 provenance
Hardware #333 tree c255374b6e9ff9885605fefe07f37ef7915dffa6: 2,478 entries / 1,899 blobs. COE #26 tree 8a7d4cf81d7227118b876c1138dd2da12345fefa: 286 entries / 207 blobs. Both complete.

| Route | Source | Destination | Same | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | 34 | 1 | 0 | 1 | 33 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |
| OpenWrt library | 15 | 20 | 6 | 9 | 0 | 5 |
| Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |

38 Hardware-local Python labs exist in source and zero under COE Hardware. Three source PHX hardware workflows map to generic hardware-ci.yml and pisowifi-ci.yml. BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at 1ee55b94183417be977ca287cd7391f9a6f7e721; vendor TailAdmin NOTICE matches at f0425bbbe34c1227311098173b1eae0c3e2a807b. COE has no root LICENSE or Hardware/LICENSE/NOTICE; license applicability to Hardware requires owner/legal review. No staging or migration occurred.

## Architecture numbering audit
Top-level level-two 6.x headings only; nested 6.x.y headings excluded. Five legacy duplicate numbers: 6.9 (278,404), 6.10 (305,413), 6.11 (317,426), 6.25 (542,572), 6.38 (782,794). Explicit non-heading §6.9 references in this file point to the first ULA identity contract at line 278; no body references to the other four were found here. Cross-document references are not fully audited, so no renumbering was attempted.

A regression test now rejects any new top-level collision outside {6.9,6.10,6.11,6.25,6.38}. Existing collisions are not claimed fixed.

## Cleanup, registry and execution limits
Cleanup #266 remains OPEN, 0/7 checked. AGENTS.md, cloud artifact policy and recovery handover were re-read. They require the private registry/sync ledger before Drive writes. Recursive Library listing found 1,422 items; no v11/newer correction surfaced; v7 is the newest accessible snapshot and was not substituted. No Google Drive connector is exposed; no Drive write occurred.

CORE source ownership was left untouched. Custom static assertions against fetched exact GitHub objects passed. New Python regression test added; repository unittest suite NOT RUN. No Master Actions run is claimed. Native COM, electrical, 150 power-cut and 30-device/24-hour soak tests remain NOT TESTED.

## Next exact actions
1. CORE publishes authenticated poll/receipt contract; QA fixes the positive poll-signature fixture and reruns #292 against current Master.
2. HARDWARE reruns Full after CORE/QA dependency resolution; retain deny-only behavior.
3. RENTAL resolves Mbed TLS/toolchain mismatch and refreshes handover; RELEASE refreshes handover and reruns Full/Windows.
4. Site authority supplies approved ULA /48; infrastructure supplies Bubblewrap runner.
5. Registry custodian restores v11 access; repository admin supplies branch-protection evidence.
6. Keep COE #26 frozen pending exact-source, licensing, import completeness, test identity and destination CI acceptance.

**Disposition:** Master audit scoped and verified; PR #288 OPEN/DRAFT/UNMERGED; COE #26 FROZEN; PRODUCTION NO-GO. No merge, release, signer provisioning, flash, secrets, real payment operation, production migration or physical test.
