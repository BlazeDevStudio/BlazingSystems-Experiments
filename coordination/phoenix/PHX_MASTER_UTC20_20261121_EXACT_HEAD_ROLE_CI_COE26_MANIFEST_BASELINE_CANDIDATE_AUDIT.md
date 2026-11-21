# PHX-MASTER UTC20 — Exact-head role/CI and COE #26 provenance audit

**Timestamp:** 2026-11-21T20:10:12Z  
**Role:** PHX-MASTER — architecture, coordination, ownership routing and migration provenance only.  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.  
**Disposition:** Master documentation update is ready for commit; subsystem source ownership is unchanged. Production remains NO-GO.

## 1. Exact live references

| Reference | Exact SHA / state |
|---|---|
| Experiments default branch main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Legacy development branch blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| v0.6 audit/development branch blazepwifi-v0.6.0-audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master coordination branch at audit start | 46cbcd0eac6312d029fd8904e20d362db7dca7db |
| COE default branch main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base main at f4e8a891... |
| Ownership routing manifest | e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; Master target null |

The CONTROL PLANE issue #172 body still contains a historical Master pin, 962e1179aae8f49551f151bf4721e1524f690c38. This checkpoint and the current PR branch ref supersede that historical body pin; the issue body was not rewritten, preserving its history. Cleanup issue #266 remains OPEN with 0/7 tracks checked.

Both repositories report main as the default branch. The branch API reports main as not protected; the branch-protection endpoint returned 403, so effective protection/ruleset state is not independently established.

## 2. Current role ownership and exact-head CI

| Role | Current owner PR head(s) | Exact-head CI / disposition |
|---|---|---|
| PHX-CORE | Experiments #252 c82705f2de865c89ab733b10efa84f26f56a5cc4; COE #45 9d76a134c1f6512aa40c20ec4d247306a71a8cce | #252 build #42698139210 SUCCESS; COE #45 overlay #44295049727 and case guard #44295049903 SUCCESS. CORE remains separately owned. |
| PHX-RENTAL | Experiments #328 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity #44782114384 and API21/API23 #44782114393 SUCCESS; build #44782114390 FAILURE. ESP32 compile log reports missing mbedtls/sha256.h; mandatory handover freshness also fails. |
| PHX-PISONET | Experiments #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09; COE #28 b21b04617d38a177260258de2d56b24382822117, #30 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc, #32 29b6fe08b10688182d981a66745f482758bd6630 | #255 Windows synthetic CI #42462978704 SUCCESS; COE #28/#30/#32 Windows synthetic runs #43632393888/#43653415598/#43653540607 SUCCESS. Native COM and physical adapter acceptance remain NOT TESTED. |
| PHX-HARDWARE | #239 d83b715b116185107737fef721c2eece8feebf39; #254 84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9; #283 88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d; #327 827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8; #329 41efc1ddf4a101d7d1cb4428dcea2662ade6936e; #330 1a1e5e25834748fbba95d6253eb668f29b6c82f8; #331 33a32ef092f22718cbda141baee75b54323986ff; #332 9f1d9ebf9c7256da2e8eace4bc0be510f6566daa; #333 e93d178bbe3fcf6a7ba7f3a049f996de10727750; #334 46dadb2414dfff76b34e78fd88b50b88ffe553ae; #335 d09b0c9dafad8dbbcda5723d8094f4975c14a274; #336 000d4e6804c451991e1cf81ec97d1b2d7ed6b526 | #239 native/build #40815737375/#40815737447 SUCCESS; #254 focused header #44683629378 SUCCESS, full build #44683629491 FAILURE; #283 quarantine append #44936835281 SUCCESS, full build #44936835327 FAILURE. #327–#335 focused quarantine/relay jobs pass on their recorded heads; their full builds fail. Current #336 exact-head Quarantine #44943506271 SUCCESS; Full #44943506269 FAILURE at Controller protocol parity / Missing poll signature check. All 14 target/Android build jobs passed; downstream simulation/signing/publishing jobs were skipped. |
| PHX-QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows #43633486963 SUCCESS but does not run the new native COM lab. #292 has no PR-triggered run and retains stale base b1ca02e... rather than current Master. QA owns the fixture correction. |
| PHX-RELEASE | Experiments #291 42797e2f3d65c30a1070caf49c93aebec149d897; COE #35 5eb240ec8b67e491e126b47242e76d823bce6e07 | #291 ESP32 compatibility #44894604453 SUCCESS; Full #44894604464 and Windows #44894604466 FAILURE at mandatory handover freshness. COE #35 case guard #44941299106 SUCCESS; shared validation #44941298951 fails all 10 profiles without an approved site ULA /48; sandbox #44941298871 fails closed with exit 125 because Bubblewrap is absent. |
| COE Stage 5 | COE #48 8286548e395366f2332830025fed00ceebdfb24a; #49 aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage and case guards pass on both. Shared ESP32 compile runs #44643670685/#44646341922 fail at missing mbedtls/sha256.h; ESP8266 compile succeeds. |
| COE integration | COE #26 b382d233ff06c8791b1028bed3c617cc7b670d12 | Five PR-triggered workflows remain QUEUED with zero jobs. No combined integration acceptance exists. |

HARDWARE #336 is a cleanup-only child of #335. Its source/test commit is 741068c7804b83897f5deab5afc7739457532427; its final docs-only PR head is 000d4e6804c451991e1cf81ec97d1b2d7ed6b526, based on #335 at d09b0c9dafad8dbbcda5723d8094f4975c14a274. The current-head Quarantine log records source-extracted 36/36 scenarios per board and other focused lab passes, while explicitly reporting SIMULATED_ONLY=1 and physical coin/relay/power-cut acceptance as zero. The current-head Full run fails at the inherited QA-owned Missing poll signature check. Do not weaken firmware default-deny to satisfy that fixture.

## 3. COE #26 migration provenance — baseline and owner candidate are separate

The manifest source_ref is Experiments main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b; the destination candidate is COE #26 at b382d233ff06c8791b1028bed3c617cc7b670d12. Complete, untruncated recursive trees:

- Manifest baseline main: 2,340 entries / 1,764 blobs.
- COE #26 destination: 286 entries / 207 blobs.
- Current HARDWARE #336 owner-candidate tree: 2,473 entries / 1,894 blobs. This is a separate owner PR candidate, not the manifest source_ref.

### Manifest baseline main → COE #26

| Route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE OpenWrt runtime | 15 | 20 | 6 | 9 | 0 | 5 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone | 31 | 19 | 0 | 2 | 29 | 17 |
| RENTAL server | 7 | 4 | 0 | 1 | 6 | 3 |
| PISONET | 32 | 47 | 13 | 11 | 8 | 23 |
| HARDWARE ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| HARDWARE ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| RELEASE workflow | 1 | 1 | 0 | 1 | 0 | 0 |

### Current HARDWARE #336 candidate → COE #26

| Route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 17 | 1 | 0 | 1 | 16 | 0 |
| ESP8266 | 28 | 1 | 0 | 1 | 27 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |

The #336 candidate contains 33 Python host-lab/helper files (10 under ESP32 and 23 under ESP8266); COE Hardware contains zero Python equivalents. Exact sketch blobs remain divergent: ESP32 source 53b27aa80fa4a91aabac71de57f550a8eef2cb61 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422; ESP8266 source 71160ac8ebd5163b19a56d6c9e229a5429975fc8 vs destination c8be98f72596681e36a3ad1f8939bf8046c96887.

License/NOTICE review: source BlazePwifi LICENSE and destination Pisowifi LICENSE are identical at 1ee55b94183417be977ca287cd7391f9a6f7e721. Source root NOTICE blob f6d92cd21465312be5993631fe26977219be0fb9 is absent from COE root; COE Hardware/LICENSE and Hardware/NOTICE.md are absent. The broad Rental standalone route remains manual-file-mapping-required with copy_permitted=false.

No route is copy-ready. No file was staged, copied, moved, overwritten, rebased, cherry-picked or edited in COE. COE #26 remains FROZEN / OPEN / DRAFT / UNMERGED.

## 4. Open P0 and cleanup gates

Issues #31 (crash-atomic member transfer/idempotency), #32 (rental lease/receipt divergence on crash), #34 (150 real power cuts and 30-device/24-hour soak), #43 (independent prepaid-ledger freshness witness), and #177 (coin pulse missed during synchronous poll) remain OPEN. Cleanup issue #266 remains OPEN with 0/7 tracks checked. No Master cleanup completion is claimed.

## 5. Test execution and limits

- GitHub source/tree inspection: complete recursive trees were returned with truncated=false; route counts and blob/mode comparisons were computed from exact trees.
- Exact-head GitHub Actions: run IDs and job outcomes are listed above.
- Master Python suite: NOT RUN. An authenticated shallow clone was attempted from the exact Master branch, but GitHub host resolution failed with “Could not resolve host: github.com” before checkout. No unittest command was executed.
- Master PR-triggered Actions: no runs returned for the current Master head.
- No physical hardware, payment, signing, firmware flash or customer operation was performed.

## 6. Private registry and storage access

The current tool surface exposed GitHub and the ChatGPT Files Library but no Google Drive connector. The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not available for readback. The only accessible correction was a 2026-11-09 checkpoint that references v11 as its prior canonical registry as of 2026-10-27; it is not the registry itself and is not current enough to replace it. Older Library v7 and October 26 sync-ledger copies were not substituted as authoritative. No private IDs or registry contents were published; no Drive files or sharing settings were changed.

## 7. Next owner actions

1. PHX-MASTER: run the full coordination unittest suite from an authenticated checkout at the new exact Master HEAD.
2. PHX-CORE: publish the approved authenticated poll/receipt contract; retain CORE source ownership.
3. PHX-QA: replace the inherited positive poll-signature fixture only against the approved CORE contract, then rerun exact-head QA.
4. PHX-HARDWARE: rerun Full after the CORE/QA dependency is resolved; preserve the #327/#329/#335/#336 ancestry.
5. PHX-RENTAL: resolve Mbed TLS compatibility and refresh the owner handover.
6. PHX-RELEASE: refresh #291 handover; obtain trusted Bubblewrap-capable infrastructure and approved site ULA /48.
7. Registry custodian: provide authorized access to v11 and newer corrections through the approved private Drive connection.
8. Repository administrator: provide effective branch-protection/ruleset evidence.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
