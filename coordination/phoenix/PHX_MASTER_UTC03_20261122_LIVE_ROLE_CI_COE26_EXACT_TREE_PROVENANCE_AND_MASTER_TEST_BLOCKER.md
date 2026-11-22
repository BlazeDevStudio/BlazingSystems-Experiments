# PHX-MASTER UTC03 — live role/CI, Hardware candidate and COE #26 provenance

**Audit timestamp:** 2026-11-22T03:38Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance and integration matrices.  
**Execution boundary:** Strict NO CODEX. This report is a read-only source/CI audit plus Master-owned documentation updates. No subsystem source, destination file, route manifest, hardware, payment system, signer or secret was modified.

## 1. Exact refs and coordination authority

| Reference | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active v0.6 audit/development ref | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Retained v0.5.3 development ref | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master audit-start branch | `phoenix/master-coordination@e619c600f3b355ffd141b8b674ab3f52d499436c` |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base `main@f4e8a891...` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12` |

There is no branch literally named `development`. The latest control-plane refresh identifies v0.6 as the active development/audit ref; v0.5.3 remains a separately named retained development ref. No branch was promoted or rewritten.

The unchanged machine-readable routing manifest is `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`: schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`. PHX-MASTER remains coordination-only with destination `null`; the broad Rental route remains manual-file-mapping-only with `copy_permitted=false`.

The source repository `AGENTS.md` is `d8777e3b58efc41caa5aa3c969c932aee9103d5f`. Its linked cloud artifact policy and public recovery handover were read from BlazeDevStudio/BlazingSystems (policy blob `5e503925750c4e511314e4b7624579d82f60aae2`; handover blob `a15f14cb3baf46424b820e1a921462794422f06b`). They require private-registry review before Drive artifact/folder creation and prohibit treating CI archives as Git-history backups.

## 2. Exact owner PR heads and current CI

| Owner | Current PR / exact head | Exact-head CI evidence | Disposition |
|---|---|---|---|
| CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) build PASS | Scoped CI only; CORE implementation remains with its separate owner/automation. No CORE work taken. |
| RENTAL | Experiments #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK identity PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API21/API23 smoke PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL | Validation handover is stale at `468adc8129ea311e13f4c5c63eb6bb01ca67ecb0`; ESP32 compile also fails on missing `mbedtls/sha256.h`. |
| PISONET | Experiments #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows synthetic CI PASS | Native COM/coinslot acceptance NOT TESTED. |
| HARDWARE — poll/edge candidate | #339 `5777b4320e3b70ac8a2d3f9399383f9438d4a715`, child of #338 | [#44972910501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910501) Quarantine PASS; [#44972910569](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910569) Full FAIL | Exact validation failure is inherited QA-owned `Missing poll signature check`; 14 target/Android jobs pass, downstream candidate/sign/publish jobs skip. |
| HARDWARE — separate pre-poll candidate | #340 `9099bbb892286aab09e6d73953e59318f47e622d`, child of #283 `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d` | [#44980490131](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980490131), [#44980490141](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980490141), [#44980490205](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980490205), [#44980490213](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980490213), [#44980490167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44980490167) all PASS | Pinned Arduino ESP32 core 3.3.13 compile and deny-only/source-lab build pass. Production signing and publication jobs are skipped; physical acceptance NOT TESTED. #340 is not a child or replacement of #339. |
| QA | Experiments #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) #290 PASS; #292 has zero PR-triggered runs | #292 remains unverified on its exact head. |
| RELEASE | Experiments #291 `42797e2f3d65c30a1070caf49c93aebec149d897` | [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) ESP32 compatibility PASS; [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) Full FAIL; [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) Windows handover FAIL | Both failures are stale handover gates; last checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71` predates the changed workflow. Downstream build/publish jobs skip. |
| COE CORE | #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) overlay PASS; [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case guard PASS | Scoped destination-candidate checks only. |
| COE PISONET / QA | #30 `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc`; #32 `29b6fe08b10688182d981a66745f482758bd6630` | [#43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) #30 PASS; [#43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) #32 PASS | Scoped synthetic Windows evidence only; not combined COE acceptance. |
| COE RELEASE | #35 `eb60594a1e11c1834cf048fea0165e8f37525389` | [#44979902421](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979902421) case guard PASS; [#44979902467](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979902467) shared validation FAIL; [#44979902461](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44979902461) sandbox FAIL | Ten appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is missing. Bubblewrap is absent; sandbox exits 125. No privileged install or unsandboxed fallback. |
| COE integration | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED; zero jobs | FROZEN; no combined integration acceptance. |

## 3. Exact Hardware candidate trees versus COE #26

Complete recursive Git trees were fetched at exact refs; every response returned `truncated=false`.

| Tree | Entries | ESP32 route files | ESP8266 route files | Python host-lab/helper files |
|---|---:|---:|---:|---:|
| Experiments main `f4e8a891...` | 2,340 | baseline | baseline | baseline |
| Hardware #339 `5777b432...` | 2,479 | 18 | 30 | 11 + 25 = 36 |
| Hardware #340 `9099bbb8...` | 2,362 | 9 | 4 | 6 + 1 = 7 |
| COE #26 `b382d233...` | 286 | 1 | 1 | 0 |

Exact firmware sketch blobs:

- ESP32: Experiments main `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0`; #339 `53b27aa80fa4a91aabac71de57f550a8eef2cb61`; #340 `6a6b1c826872af9f21721fb82cbc5754785c7888`; COE #26 `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266: Experiments main `bfb94920eb0a189ca01d52e5443954fa133f5423`; #339 `71160ac8ebd5163b19a56d6c9e229a5429975fc8`; #340 `fdd4e45b2346957ce5f55ae529734854e4c78c7f`; COE #26 `c8be98f72596681e36a3ad1f8939bf8046c96887`.

Every candidate sketch blob differs from the COE destination sketch. #339 and #340 are separate candidate lineages. The six ESP32 and one ESP8266 Python files in #340, and 36 Python files in #339, have no COE Hardware Python equivalents; they are host-lab helpers, not production firmware.

### License / NOTICE

- Experiments `experiment/openwrt/BlazePwifi/LICENSE` and COE `Pisowifi/LICENSE` are byte-identical at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Experiments root `NOTICE.md` exists at `f6d92cd21465312be5993631fe26977219be0fb9`; COE #26 root `NOTICE.md` is absent.
- COE #26 `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.

**Migration decision:** no proposal to move files. No staging, copy, move, overwrite, cherry-pick, rebase, destination edit or route promotion. Exact file-level owner approvals, test-identity mapping and license/NOTICE completion remain prerequisites.

## 4. Master execution and private registry

- PR #288 audit-start head `e619c600f3b355ffd141b8b674ab3f52d499436c` had zero PR-triggered workflow runs.
- Local `git ls-remote` was attempted; it failed before checkout with `Could not resolve host: github.com`. The full Master Python coordination unittest suite is **NOT RUN**.
- The current PR changed 161 paths at audit start; all were under `coordination/phoenix/`. The ownership manifest remains unchanged.
- The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not available through the exposed connector. Library search surfaced older v3–v7 snapshots only; none was substituted. No Drive folder/artifact was created, no private identifiers or registry contents were copied to GitHub.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete. No branch-protection change was made; effective protection was not independently verified in this activation.

## 5. Required next actions

1. PHX-MASTER: obtain an authenticated checkout at the final Master PR head and run `python3 -m unittest discover -s coordination/phoenix -p 'test_*.py' -v` plus `python3 coordination/phoenix/verify_coordination.py`; publish actual logs.
2. PHX-QA / PHX-CORE: resolve the authenticated poll-signature fixture/producer contract without weakening default-deny.
3. PHX-RENTAL / PHX-RELEASE: refresh exact handovers after their source/workflow changes; RENTAL and HARDWARE owners resolve Mbed TLS compatibility.
4. Site authority / Infrastructure: supply approved ULA /48 authority and a trusted Bubblewrap-capable runner.
5. Registry custodian: restore authorized v11/newer-correction access before any Drive artifact or migration record is created.
6. All owners: independently approve per-file source/destination blobs, modes, license/NOTICE, import completeness and test identity before any migration staging.

**Production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates remain unverified.