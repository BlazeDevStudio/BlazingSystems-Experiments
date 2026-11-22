# PHX-MASTER UTC04 — live role CI and exact COE #26 provenance

**Checkpoint:** 2026-11-22T04:39Z · **Role:** PHX-MASTER · **Status:** PR_READY · **Production:** NO-GO

Strict NO CODEX. This activation changed Master coordination documents only. No subsystem source, COE destination, payment system, signing, secret, hardware or release operation was changed.

## Live refs and control plane

- Issue #172 OPEN; cleanup #266 OPEN, 0/7 tracks complete.
- Experiments default main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Exact branch named development: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5. Separate v0.6.0-audit-foundation ref: 2fbd2475e9f54878c316fa7cea2f228386b0e859. The latter is not literally named development; this corrects UTC03 wording.
- PHX-MASTER branch phoenix/master-coordination / PR #288: pre-update head 33deb02a55f4f1a3d9ea22cb96b4329dd9489626, base main f4e8a891..., OPEN / DRAFT / UNMERGED, 162 changed paths, all under coordination/phoenix/.
- COE main a6513ab4412b4c014eee2863e45cbe32d06cb243; COE #26 b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN, 205 changed paths, five workflows QUEUED / zero jobs.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.
- Experiments AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f; cloud artifact policy and public recovery handover were read.

## Exact owner PR/CI reconciliation

| Role / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2... | Build #42698139210 PASS (scoped). CORE remains with separate owner/automation; no CORE work taken. COE #45 9d76a134... overlay #44295049727 and case #44295049903 PASS. |
| RENTAL #328 | 0e0da62a... | APK identity #44782114384 and API21/API23 #44782114393 PASS; build #44782114390 FAIL: stale handover and missing mbedtls/sha256.h. |
| PISONET #255 | d01fd164... | Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED. COE #30 #43653415598 PASS. |
| HARDWARE #339 | 155af6d58f8a666c178946ae3e2e00855e0635af, child of #338 1a6a7acf... | Quarantine #44985602488 PASS. Full #44985602493 FAIL at QA-owned Missing poll signature check; 14/14 target/platform builds PASS; simulations, update bundle, candidate and signing/publication jobs skipped. Current head adds LF/CRLF/CR raw-prefix-splice tests; failure is the inherited poll-contract gate. |
| HARDWARE #340 | 20c5889fc4ceeb95ab0b05c7c11952704caff36b, separate child of #283 88581eef... | Five focused workflows PASS (#44983396273, #44983396365, #44983396281, #44983396263, #44983396267). Full #44983396262 PASS: 14/14 targets, simulations, update bundle and candidate gate. Signed import, signing handoff and publication were skipped. Candidate CI is not hardware acceptance; base test's comment-sensitive grep does not prove authenticated register/poll responses. |
| QA #290 / #292 | 5c29d159... / 75a3f66d... | #290 Windows CI #43633486963 PASS. #292 has zero PR-triggered runs and stale Master base b1ca02e2... |
| RELEASE #291 / COE #35 | 42797e2f... / a09b014c... | #291 ESP32 compatibility #44894604453 PASS; Windows #44894604466 and BlazePwifi #44894604464 FAIL handover freshness. COE #35 shared #44984431434: 172 tests PASS / 2 skips, then 10/10 profiles fail closed without approved ULA /48. Sandbox #44984431366: 31/31 host tests PASS, Bubblewrap absent / exit 125. Case guard #44984431339 PASS. |
| COE QA #32 | 29b6fe08... | Synthetic Windows CI #43653540607 PASS; native COM acceptance not established. |

CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE source branches remain owner-controlled. No cross-role implementation or parallel competing worker was started.

## Exact recursive-tree and migration provenance

All four recursive trees were complete (truncated=false): Experiments main 2,340 entries; Hardware #339 2,479; separate #340 2,363; COE #26 286.

| Candidate | ESP32 files | ESP8266 files | Python board-lab helpers | COE #26 equivalents |
|---|---:|---:|---:|---|
| #339 | 18 | 30 | 36 (11 ESP32, 25 ESP8266) | one sketch per route; zero Python helpers |
| #340 | 9 | 4 | 7 (6 ESP32, 1 ESP8266) | one sketch per route; zero Python helpers |

Sketch blob identities:
- ESP32 main 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0; #339 53b27aa80fa4a91aabac71de57f550a8eef2cb61; #340 6a6b1c826872af9f21721fb82cbc5754785c7888; COE #26 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 main bfb94920eb0a189ca01d52e5443954fa133f5423; #339 71160ac8ebd5163b19a56d6c9e229a5429975fc8; #340 fdd4e45b2346957ce5f55ae529734854e4c78c7f; COE #26 c8be98f72596681e36a3ad1f8939bf8046c96887.

Test blobs differ: #339 source v05_firmware_hardening_test.sh 41211b2c110ab409f6d9d1812ef12fda73b13211; #340 source same path dc20a6ce1a1828c9cba9631fc67193840de5c224; COE Hardware/tests/test_firmware_hardening.sh f921c56cecc19cab1989507b9b4ade1f45dac54e. COE Hardware has four files only (README, two sketches, one shell test) and zero Python host-lab equivalents.

Only BlazePwifi/LICENSE ↔ Pisowifi/LICENSE is byte-identical (1ee55b94183417be977ca287cd7391f9a6f7e721). Source root NOTICE.md exists (f6d92cd21465312be5993631fe26977219be0fb9); COE root NOTICE.md and COE Hardware/LICENSE / Hardware/NOTICE.md are absent.

**No destination staging, copy, move, overwrite, cherry-pick, rebase, route promotion or COE write occurred.**

## Execution and blockers

- Master #288 returned zero PR-triggered workflow runs. Full Master coordination unittest suite NOT RUN.
- Local git ls-remote failed before checkout: Could not resolve host: github.com. No local authenticated checkout; source/tree inspection is not a test execution.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections BLOCKED: no canonical v11 Library copy and no Google Drive connector exposed. No older snapshot substituted; no private data or Drive write/readback claimed.
- Rulesets endpoint returned an empty list; classic branch-protection read returned HTTP 403. Effective branch protection UNKNOWN.
- Cleanup #266 remains 0/7; broader duplicate/dead-code cleanup inventory incomplete; MASTER checkbox remains unchecked.
- PHX-MASTER recurring wake-up is enabled for this role; this report covers this activation only, not a continuously running process between activations.

## Next exact actions

1. PHX-CORE + PHX-QA: publish authenticated register/poll response and event-bound receipt contract; replace comment-sensitive lexical checks with behavioral fixtures/golden vectors; rerun #339 Full at the exact updated head. Hardware remains default-deny.
2. PHX-RENTAL: refresh exact handover and resolve ESP32 Mbed TLS compatibility within its owner branch.
3. PHX-RELEASE / infrastructure: provide approved site-scoped ULA /48 authority and trusted Bubblewrap runner; refresh #291 handover.
4. Registry custodian: restore authorized Drive access to v11 and newer corrections before artifact or migration planning.
5. PHX-MASTER human runner: provide authenticated checkout/network and execute full coordination unittests and verifier scripts at final Master commit.
6. Independent QA / Hardware / owner: retain NO-GO until protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized gates have independently verified evidence.

**PRODUCTION NO-GO.** Candidate CI PASS is not hardware acceptance, signing, production readiness or migration authority.