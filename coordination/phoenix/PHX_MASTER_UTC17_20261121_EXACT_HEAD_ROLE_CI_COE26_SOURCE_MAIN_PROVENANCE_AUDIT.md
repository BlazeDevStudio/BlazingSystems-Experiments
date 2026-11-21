# PHX-MASTER UTC17 — exact-head, role/CI and COE #26 source-main provenance audit

**Audit time:** 2026-11-21T17:41:08Z  
**Role:** PHX-MASTER  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Audit start HEAD:** `8cc44fdf748fb7ba2ab44e665b0556c836be6351`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Disposition:** Master coordination audit verified; integration and production remain blocked.

## 1. Exact repository identities

| Ref | Exact SHA | State |
|---|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | default/source branch |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | development branch |
| `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` | comparison-only |
| PHX-MASTER #288 | `8cc44fdf748fb7ba2ab44e665b0556c836be6351` | OPEN / DRAFT / UNMERGED |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | destination default branch |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN |

At audit start, PR #288 had **154 changed paths**, all under `coordination/phoenix/`; zero paths were outside Master ownership. No PR-triggered Actions run exists for the audit-start Master HEAD.

## 2. Ownership and role CI reconciliation

| Role | Current exact PR refs | Exact-head CI / disposition |
|---|---|---|
| CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4`; COE #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | #252 build #42698139210 PASS; COE #45 scoped overlay/case checks #44295049727 and #44295049903 PASS. CORE source remains with its separate owner; no competing worker or CORE edit. |
| RENTAL | #240 `a7d113fb8ae3f0c5e838e64d31cae7a154e37b56`; #287 `a4fffd01c8fb1818c32a53522e0590c1dc8a77cd`; #289 `68928774d0d7cf65adb26bc6b54199a3159d066c`; #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | #240/#287/#289 scoped runs PASS. #328 APK identity #44782114384 and API smoke #44782114393 PASS; build #44782114390 FAILS on missing `mbedtls/sha256.h`; mandatory handover freshness also fails. |
| PISONET | Experiments #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09`; COE #28 `b21b04617d38a177260258de2d56b24382822117`, #30 `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc`, #32 `29b6fe08b10688182d981a66745f482758bd6630` | Scoped Windows/synthetic CI passes (#42462978704, #43632393888, #43653415598, #43653540607). Native COM/PnP acceptance NOT TESTED. |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows #43633486963 PASS; #292 has no PR-triggered runs. QA owns the inherited positive poll-signature fixture and exact-base replay. |
| HARDWARE | #327 `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`; #329 `41efc1ddf4a101d7d1cb4428dcea2662ade6936e`; #334 `46dadb2414dfff76b34e78fd88b50b88ffe553ae`; #335 `7a4da71b800aef50557342176c8b584b98a23aae`; separate #333 `e93d178bbe3fcf6a7ba7f3a049f996de10727750` | #335 Quarantine #44928924423 and Relay #44928924437 PASS; Full #44928924442 FAILS at `Missing poll signature check`. #333 Quarantine #44901170202 PASS; Full #44901170215 FAILS at the same inherited fixture. #329/#334 focused Quarantine/Relay runs pass; their Full builds fail at the inherited validation. These are host/CI checks, not hardware acceptance. |
| RELEASE | Experiments #291 `42797e2f3d65c30a1070caf49c93aebec149d897`; COE #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; COE #35 `7fd3d96833ed535b9f3d2c1922663cb9a864fd5e` | #291 compatibility #44894604453 PASS; Full #44894604464 and Windows #44894604466 FAIL at handover freshness. #35 case-collision #44929601674 PASS; sandbox #44929601611 FAILS because Bubblewrap is absent; shared #44929601659 FAILS all ten profiles closed because no approved site-scoped ULA /48 exists. |
| COE integration | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED with zero jobs. Candidate stays FROZEN. |

### HARDWARE stack ancestry

Exact live ancestry remains non-overlapping:

- #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08` → #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470` → #326 `58c558fb6a237935214621adc3dee65a10fe1a51` → #327 `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`.
- #329 `41efc1ddf4a101d7d1cb4428dcea2662ade6936e` is a separate child of #327; #334 `46dadb2414dfff76b34e78fd88b50b88ffe553ae` and #335 `7a4da71b800aef50557342176c8b584b98a23aae` are sibling children of #329.
- Another line is #327 → #330 `1a1e5e25834748fbba95d6253eb668f29b6c82f8` → (#331 `33a32ef092f22718cbda141baee75b54323986ff`, #332 `9f1d9ebf9c7256da2e8eace4bc0be510f6566daa`) → #333 `e93d178bbe3fcf6a7ba7f3a049f996de10727750`.

No rebase, retarget, consolidation or owner-branch write was made.

## 3. Exact source-main to COE #26 tree comparison

Both recursive trees were complete (not truncated): Experiments main has 2,340 entries / 1,764 blobs; COE #26 has 286 entries / 207 blobs. The manifest blob remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, 11 routes; PHX-MASTER target is `null`.

| Route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE OpenWrt library | 15 | 20 | 6 | 9 | 0 | 5 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android path | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone server | 7 | 4 | 0 | 1 | 6 | 3 |
| PISONET | 32 | 47 | 13 | 11 | 8 | 23 |
| HARDWARE ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| HARDWARE ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| RELEASE build workflow | 1 | 1 | 0 | 1 | 0 | 0 |

The RENTAL Android counts are a path-mapping inventory, not a claim that every source file is intended to be copied; the manifest route requires owner review and exact file mapping. The standalone-rental profile route remains `manual-file-mapping-required`.

### Exact Hardware/test identities

The active Hardware #335 tree has 2,471 entries; separate #333 has 2,478. #335 is an unmerged owner branch and is not a replacement for the manifest's Experiments-main source ref.

At #335 HEAD `7a4da71b800aef50557342176c8b584b98a23aae`, ESP32 sketch blob `a2c767be512ebb47ae93190ab045c2659c3426b3` and ESP8266 blob `098a46f698fd672595a9c0cc62b640ac41d84959` differ from COE #26 blobs `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` and `c8be98f72596681e36a3ad1f8939bf8046c96887`.

Source QA fixture `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` at #335 tree is blob `41211b2c110ab409f6d9d1812ef12fda73b13211` (6,782 bytes). COE #26 `Hardware/tests/test_firmware_hardening.sh` is blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` (4,118 bytes). They are not identical; both still require `response_sig` and literal `|poll|`. The inherited positive fixture conflicts with the current deny-only contract and causes Full validation failure. QA owns fixture correction after CORE publishes the approved authenticated register/poll and event-bound receipt contract. Do not add a positive firmware admission path to make CI green.

### License / NOTICE comparison

- BlazePwifi `LICENSE` and COE `Pisowifi/LICENSE` are byte-identical at `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Vendor QR-code LICENSE matches at `150770c0fc2994865ccdbef6662735cc083e780d`.
- Vendor TailAdmin LICENSE matches at `cb92d4176b21b0594e5a6caf94d79340505e3d33`; TailAdmin NOTICE matches at `f0425bbbe34c1227311098173b1eae0c3e2a807b`.
- Source root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE root. COE has no `Hardware/LICENSE` or `Hardware/NOTICE.md`; hardware-specific license/NOTICE applicability still needs owner/legal review.

No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or destination edit occurred. The manifest was not changed.

## 4. Master verification and execution limits

- Exact-source architecture assertions: **10/10 PASS** in a local JavaScript harness against remote `ARCHITECTURE_CONTRACTS.md` blob `1767bcd626a7697329f25effdc3ae3c1b0581de4` and test source blob `22507414529e9e95abde0114a1215e652cb747cf`. This executed the same ten documented assertions over exact fetched source content; it is **not** a Python unittest invocation.
- Full `python3 -m unittest discover -s coordination/phoenix -p 'test_architecture_contracts.py' -v`: NOT RUN; no local repository checkout/working tree is exposed in this runtime.
- Master PR-triggered Actions: none for audit-start HEAD `8cc44fdf748fb7ba2ab44e665b0556c836be6351`.
- Experiments root `AGENTS.md`, README_FIRST, COMMUNICATION_PROTOCOL, Cloud Artifact Policy and Cloud Storage Recovery Handover were read. COE root `AGENTS.md` returned 404; COE root README is only a title.
- Branch rulesets endpoint returned `[]`; classic branch-protection endpoint returned 403. Effective branch protection is UNKNOWN, not PASS.
- Library exact-name search surfaced registry snapshots v3–v7 and a 2026-11-09 production checkpoint, but not canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. No Google Drive connector is exposed. Older snapshots were not substituted; no private registry content or Drive identifiers were published and no Drive artifact was created.
- Cleanup issue #266 remains OPEN with 0/7 tracks complete; the Master checkbox remains intentionally unchecked because broader dead/duplicate-source cleanup is not complete.

## 5. Open blockers and next owner actions

1. PHX-CORE: publish the approved authenticated register/poll and event-bound receipt contract; CORE remains exclusively with its separate owner.
2. PHX-QA: replace the inherited positive poll-signature fixture with source-linked default-deny negative assertions after the CORE contract is published; run #292 and rerun current Hardware Full at exact SHA.
3. PHX-HARDWARE: retain default-deny and rerun Full only after QA/CORE fixture/contract reconciliation; physical GPIO/relay acceptance remains NOT TESTED.
4. PHX-RENTAL: resolve Mbed TLS 4.0.0 header compatibility and refresh its own handover freshness.
5. PHX-RELEASE: refresh owner handover evidence and rerun #291 Full/Windows.
6. Site authority / Infrastructure: provide approved site-scoped ULA /48 and a trusted Bubblewrap-capable runner.
7. COE integration owner: keep #26 frozen until exact source blobs, test imports/identities, licensing, and destination CI are owner/QA accepted.
8. Registry custodian: restore authorized access to private v11 and newer corrections. Repository administrator: provide effective branch-protection evidence.
9. QA/local runner: execute the actual Python unittest suite against final Master HEAD.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.

## 6. Safety / side-effect record

No subsystem source branch was edited. No CORE worker was started. No destination file was changed. No migration, merge, release, signing, secret provisioning, firmware flash, real-payment action, physical test or release approval occurred.
