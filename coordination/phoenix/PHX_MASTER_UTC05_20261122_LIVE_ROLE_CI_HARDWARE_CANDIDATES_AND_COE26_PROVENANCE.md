# PHX-MASTER UTC05 — live role CI, Hardware candidate split and COE #26 provenance

**Checkpoint:** 2026-11-22T05:38:34Z · **Role:** PHX-MASTER · **Status:** BLOCKED · **Production:** NO-GO

Strict NO CODEX. No Codex application, CLI, API, agent, workflow or delegation was used. This report is a Master-only coordination/provenance audit.

## 1. Live refs and governance

- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Actual branch named `development`: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`. Separate `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` is not literally named development.
- Master branch before this append-only update: `phoenix/master-coordination@76d3af43d864d4528aabfb24128ae9981ef48f2f`; PR #288 OPEN / DRAFT / UNMERGED, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 163 existing changed paths all under `coordination/phoenix/`.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete. The broader Master duplicate/dead-code inventory remains incomplete.

## 2. Current owner PR and exact-head CI

| Owner | Exact refs | Terminal evidence |
|---|---|---|
| CORE | #252 `c82705f2...`; COE #45 `9d76a134...` | #42698139210, #44295049727 and #44295049903 PASS (scoped). CORE remains separately owned. |
| RENTAL | #328 `0e0da62a...`; predecessor #289 `68928774...` | #328 APK identity #44782114384 and API21/API23 #44782114393 PASS; Full #44782114390 FAILS because inherited ESP32 source cannot find `mbedtls/sha256.h`, and validation reports stale CORE handover. #289's own build/instrumentation PASS does not transfer to #328. |
| PISONET | #255 `d01fd164...`; COE #30 `4897348d...`; QA #32 `29b6fe08...` | #42462978704, #43653415598 and #43653540607 PASS (Windows synthetic). Native COM/device acceptance NOT TESTED. |
| HARDWARE #339 | source/test `f3dca92cd1f27bb3b1c717d1589fcb46baf5ccba`; docs head `b3e1558845ae2cd508e42d0d4722fdcd28293e32` | Quarantine #44986635350 PASS; Full #44986635417 FAILS at QA-owned `Missing poll signature check`; 14/14 target/platform jobs PASS, downstream jobs SKIPPED. |
| HARDWARE #340 | source/test `4eefce64719f40fd30621296db7c3fa764a44f1a`; docs head `20c5889fc4ceeb95ab0b05c7c11952704caff36b` | Five focused workflows and Full #44983396262 PASS; signed import/signing/publication SKIPPED; physical acceptance NOT TESTED. |
| QA | #290 `5c29d159...`; #292 `75a3f66d...` | #290 Windows #43633486963 PASS. #292 has no PR-triggered runs and stale Master base `b1ca02e2...`. |
| RELEASE | #291 `42797e2f...`; COE #35 source/test `99d97538...`, docs head `3ae883b...` | #291 ESP32 compatibility #44894604453 PASS; Full #44894604464 validation FAIL; Windows #44894604466 handover FAIL; publisher skipped. COE #35 case #44989195190 PASS; shared #44989195193 runs 173 tests PASS / 2 skips then all 10 profiles fail closed for missing approved site ULA /48; sandbox #44989195200 runs 31/31 host tests PASS then Bubblewrap absent / exit 125. |

COE #44 `582fd5d5...` is based on older #35 parent `1a5be48d...`; it is not the current #35 lineage or site-prefix authority. COE #26 still has five QUEUED workflows and zero jobs.

**Contract boundary:** Architecture contract §6.58 keeps poll admission deny-only until CORE publishes the approved producer/consumer response contract and QA approves source-linked negative/default-deny vectors. Do not weaken firmware to satisfy the inherited positive marker.

## 3. Exact migration provenance

All four recursive trees are complete (`truncated=false`): Experiments main 2,340 entries; #339 2,479; separate #340 2,363; COE #26 286.

| Candidate | Route | Source | Destination | Identical | Divergent | Source-only | Destination-only |
|---|---|---:|---:|---:|---:|---:|---:|
| Main | ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| Main | ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| Main | QA/Pisowifi tests | 38 | 19 | 1 | 3 | 34 | 15 |
| #339 | ESP32 | 18 | 1 | 0 | 1 | 17 | 0 |
| #339 | ESP8266 | 30 | 1 | 0 | 1 | 29 | 0 |
| #339 | QA/Pisowifi tests | 47 | 19 | 1 | 3 | 43 | 15 |
| #340 | ESP32 | 9 | 1 | 0 | 1 | 8 | 0 |
| #340 | ESP8266 | 4 | 1 | 0 | 1 | 3 | 0 |
| #340 | QA/Pisowifi tests | 39 | 19 | 1 | 3 | 35 | 15 |

Python board-lab helpers: #339 = 36, #340 = 7, COE Hardware = 0.

### Exact firmware/test identities

- ESP32: main `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0`; #339 `53b27aa80fa4a91aabac71de57f550a8eef2cb61`; #340 `6a6b1c826872af9f21721fb82cbc5754785c7888`; COE `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266: main `bfb94920eb0a189ca01d52e5443954fa133f5423`; #339 `71160ac8ebd5163b19a56d6c9e229a5429975fc8`; #340 `fdd4e45b2346957ce5f55ae529734854e4c78c7f`; COE `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- Firmware-hardening tests: #339 source `41211b2c110ab409f6d9d1812ef12fda73b13211`; #340 source `dc20a6ce1a1828c9cba9631fc67193840de5c224`; COE `Hardware/tests/test_firmware_hardening.sh` `f921c56cecc19cab1989507b9b4ade1f45dac54e`. No byte-identical test import is established.
- Experiments `BlazePwifi/LICENSE` and COE `Pisowifi/LICENSE` match exactly: `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root `NOTICE.md` `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE root; COE `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.

No destination staging, copy, move, overwrite, cherry-pick, rebase or edit occurred. COE #26 remains FROZEN.

## 4. Master execution and access

- Master head `76d3af43d864d4528aabfb24128ae9981ef48f2f` has zero PR-triggered Actions runs and no combined status entries.
- Ordinary `git ls-remote` failed with `Could not resolve host: github.com`. Full Master suite NOT RUN; neither `python3 -m unittest discover -s coordination/phoenix -p 'test_*.py' -v` nor `python3 coordination/phoenix/verify_coordination.py` was executed.
- 13/13 bounded static metadata assertions passed (branch/PR identity, base pin, Master-only path scope, route schema/status/count, Master target null, complete trees, license identity, NOTICE gaps, test-blob divergence, COE #26 queued workflows and checkpoint deduplication). These are not repository unit tests.
- The private Drive v11 registry and newer corrections remain inaccessible. Library search found older v3–v7 snapshots only; none was substituted. No Google Drive connector is exposed. Public cloud artifact policy and storage recovery handover were read; no Drive write, artifact upload, folder creation or sharing change occurred.
- No subsystem source, COE destination, secret, signer, device or payment system was changed. No merge, release, flash, financial migration or physical test occurred.

## 5. Next exact actions

1. PHX-QA + PHX-CORE: resolve the authenticated poll/receipt producer-consumer contract and replace the stale positive marker with source-linked negative/default-deny vectors; keep Hardware deny-only.
2. PHX-RENTAL: resolve Mbed TLS baseline compatibility and refresh its canonical handover in its owner branch.
3. PHX-RELEASE / site infrastructure: obtain approved site-scoped ULA /48 authority, provide a trusted Bubblewrap-capable runner, and refresh #291 handover.
4. Registry custodian: restore authorized access to private v11 and newer corrections before any artifact/migration planning.
5. PHX-MASTER human runner: restore authenticated GitHub network/checkout and run the complete coordination suite at the final Master head.
6. All owners: complete exact path/blob, license/NOTICE, import, test-identity and exact-SHA CI review before proposing any migration.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
