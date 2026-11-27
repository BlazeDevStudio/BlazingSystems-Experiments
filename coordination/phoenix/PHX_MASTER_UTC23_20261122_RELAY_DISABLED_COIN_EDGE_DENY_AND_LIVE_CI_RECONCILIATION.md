# PHX-MASTER UTC23 — relay-disabled coin-edge deny contract and live exact-head reconciliation

**Updated:** 2026-11-22T23:34:12Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Mode:** Strict NO CODEX · coordination/architecture/provenance only · PRODUCTION NO-GO

## 1. Exact live refs

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch start: 72f1c39a951229ba3c9d5337c0e28ff5eb01d852; base main.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN.
- Master #288: OPEN / DRAFT / UNMERGED; 177 changed paths, all under coordination/phoenix/.
- OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, Master target null.

Root AGENTS.md was re-read at blob d8777e3b58efc41caa5aa3c969c932aee9103d5f. README_FIRST (2026-11-14) and COMMUNICATION_PROTOCOL (2026-11-14) were re-read from the current Library attachment set. The private Drive registry requirement remains blocked: exact v11 and newer corrections were not surfaced; only older v3-v7 snapshots/addenda appeared, and no Google Drive connector is exposed. No older snapshot was substituted.

## 2. New Hardware #345 finding — test-first RED

Hardware #345 is OPEN / DRAFT / UNMERGED, one changed path, child of #343 at pinned parent dfeff7d5f63e699de7bc296c7641f2493f1e0e13. Test head: 834738d2e82b6857779935b988c4046cbcb6c89f. It changes only experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_scenario_fixtures.py; neither production sketch changed.

Source review at that exact head confirms both board sketches use relayEnabled in applyOutputs() to force the relay output OFF, but sampleCoinPulseEdge() does not include relayEnabled in sampled-edge eligibility. With insertMode and activeTarget still set, an active GPIO transition can enter the normal pending-pulse path while the acceptor relay is disabled.

The new scenario requires a boot-visible sticky fault marker, zero pending pulses, zero persistence calls, relay/LED OFF, insertion mode OFF, and empty active target. This is a source-level safety gap, not a reported customer incident.

Exact CI:
- [Quarantine #45083252631](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45083252631) — FAIL as intended RED. Job 137395949187 reports ESP8266 exact-source expected exit 0, got 60.
- [Full #45083252628](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45083252628) — FAIL at inherited QA-owned Missing poll signature check. ESP8266, ESP32, target firmware jobs, and Android pass; downstream simulations/signing/publication are skipped.

Hardware owns the implementation on both sketches; QA owns independent source-linked negative/default-deny verification; Master records provisional contract §6.76 only. Do not call #345 a green regression or a completed firmware fix.

## 3. Current role CI

| Role / PR | Exact head | Exact-head evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped; separate CORE owner remains active. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | [APK identity #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and [API21/API23 #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; [build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL at stale handover and missing mbedtls/sha256.h. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [Windows #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS (synthetic only); physical COM acceptance NOT TESTED. |
| HARDWARE #283 | 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30 | [Quarantine #45057637178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637178) PASS; [Full #45057637196](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637196) FAIL at ESP32 Mbed TLS header. |
| HARDWARE #343 | dfeff7d5f63e699de7bc296c7641f2493f1e0e13 | [Quarantine #45062595339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595339) and [Relay #45062595335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595335) PASS; [Full #45062595995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595995) FAIL at QA poll-signature assertion. |
| HARDWARE #341 | 4368435ad762d507a907e72a9c739c7bddbc3a81 | [Quarantine #45060591705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591705) PASS; [Full #45060591630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591630) FAIL at inherited QA assertion. |
| HARDWARE #344 | 3bfa530c94a929191d7b3335c085dbd7f99e1e18 | [Quarantine #45080942944](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942944) PASS; [Full #45080942789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942789) FAIL at inherited QA assertion. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 [Windows #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke NativeComInterfaceHandleLab; #292 has no workflow runs. |
| RELEASE #291 | cb5e5450a4fc2afc7f38cf426e51b390859a1dd0 | [Windows #45071305811](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305811) and [Full #45071305854](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305854) FAIL at handover freshness; [ESP32 compatibility #45071305891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305891) PASS. |
| COE #35 | 16c0e140cbfd52d4cb572b7121189866763c77b2 | [Case #45082913966](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913966) PASS; [profiles #45082913844](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913844) fail closed on all ten profiles without approved site ULA /48; [sandbox #45082913881](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913881) exits 125 because Bubblewrap is absent. |
| COE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | [Overlay/shell #44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and [case #44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS (scoped). |
| COE #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | [Stage 5.1 #44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and [case #44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; [shared #44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) fails ESP32 compile on missing mbedtls/sha256.h under core 4.0.0. |
| COE #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows remain QUEUED, zero jobs/statuses. FROZEN. |

## 4. COE #26 exact-tree and provenance hold

All inspected recursive trees were non-truncated: Experiments main 2,340 entries; development 2,079; Hardware #343 2,481; Master start 2,519; COE main 3; COE #26 286.

The 61-row PisoWiFi source intake pins historical source 6d4c9b487af4d768c4d7627654d119417fcc6e00, not current main. Its runtime table computes 46 byte-identical and 15 derived while the summary claims 47 and 14. The Hardware #343 source tree has 34 board-local Python helpers; COE #26 has zero corresponding Hardware Python helpers.

| Component | Current source #343 | COE #26 |
|---|---|---|
| ESP32 sketch | 9011029ea05bb6160bc326598e6d25cbe953c4c2 | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 sketch | 01fe33404d51653515e64833038d23d080ff80b2 | c8be98f72596681e36a3ad1f8939bf8046c96887 |
| Hardening test | 41211b2c110ab409f6d9d1812ef12fda73b13211 | f921c56cecc19cab1989507b9b4ade1f45dac54e |

PisoWiFi LICENSE matches at 1ee55b94183417be977ca287cd7391f9a6f7e721. Experiments root NOTICE exists at f6d92cd21465312be5993631fe26977219be0fb9; COE root NOTICE is absent and Hardware-local LICENSE/NOTICE are absent. No staging, copy, move, overwrite, rebase, cherry-pick, route promotion, or destination edit.

## 5. Master scope, governance, and test execution

- Master recursive tree at start: 2,519 entries; 177 coordination/phoenix blobs; 92 PHX_MASTER reports; INDEX 92/92 unique links. After adding this report, the index is 93/93.
- Master PR #288 changed paths at start: 177, all under coordination/phoenix/; no out-of-scope path.
- OWNERSHIP_ROUTES.json remains 11 routes, DRAFT_REVIEW_ONLY, Master target null.
- Branch-protection details return 403 for Experiments main/development/Master and COE main; rulesets endpoints return empty arrays. Effective required-check enforcement is NOT independently readable; administrator verification required.
- Private canonical BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections are unavailable through the exposed Library/connector surface. No older v3-v7 snapshot substituted; no private IDs or contents published.
- Full Master unittest discovery and verify_coordination.py: NOT RUN. Static tree/blob/table assertions are inventory checks, not Master test-suite execution.
- Cleanup issue #266 remains OPEN; Master inventory remains partial. No subsystem source or COE destination changed.

## 6. Next exact actions

1. PHX-HARDWARE: implement the relay-disabled edge denial in both sketches on the existing #345 lineage; keep the sticky deny/fault-marker semantics and ensure no pending credit or POST eligibility.
2. PHX-QA: independently verify the same source SHA on both boards, including relay-disabled edge, output OFF ordering, persistence failure, reboot/recovery, and no-credit/no-POST negative paths. Do not restore positive legacy poll signatures.
3. PHX-RENTAL/CORE: resolve the Mbed TLS header/toolchain mismatch and stale handover on exact current heads.
4. PHX-RELEASE: refresh the handover after source/workflow changes; keep the 27-path mixed-owner diff under explicit review.
5. COE integration owner: reconcile the 61-row count discrepancy, 34 missing helper imports, divergent firmware/test identities, and LICENSE/NOTICE scope before any staging request; #26 remains frozen.
6. Repository administrators: verify effective branch protection and required checks in an authorized admin context.
7. Registry custodian: restore authorized v11/newer-correction access. Master test runner: execute full Master tests in an authenticated checkout.

**Production disposition: NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak, and owner-authorized release gates remain mandatory.