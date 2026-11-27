# PHX-MASTER UTC19 — live poll transport, COE provenance and registry access audit

**Observed:** 2026-11-27T19:38Z  
**Role/task:** PHX-MASTER / `PHX-MASTER-20261127T19Z`  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, cross-repository migration provenance only. Strict NO CODEX.

## 1. Exact refs and control-plane state

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Active v0.6 audit foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch / PR #288 at audit start | `13d397095f8712f17c9b700cf5f0812d81e07fea` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Issue #172 is OPEN. The latest current-date Master checkpoint at audit start was UTC18; no UTC19 Master message for 2026-11-27 existed. Cleanup issue #266 is OPEN with 0/7 role tracks checked.

PR #288 is OPEN / DRAFT / UNMERGED, head `13d397095f8712f17c9b700cf5f0812d81e07fea`, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Its 258 existing changed paths are all under `coordination/phoenix/`. Current-main compare: 670 ahead / 1 behind, merge base `f4e8a891`. No rebase, retarget or merge. No exact-head Master workflow run or combined status exists.

The machine ownership manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. No route or owner changed.

## 2. New Hardware evidence — PR #365

[PR #365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/365) is an OPEN / DRAFT / UNMERGED child of #364. Current PR head `e65b0b895af9c3fc5e5632f704cb67b347e69725`; source/test SHA `fcd5d7df210c8521f9c8fcc1019c8db8bdaf7eb0`; evidence docs head `6e5e126199368cbe78f9d46dd6c702c883cfa5cb`.

The owner added a host poll-deny transport matrix with five outcomes × four relay/LED polarity combinations: 20 cases per board / 40 total. Outcomes: immediate begin failure, empty timeout, malformed body, server-error body and untrusted positive `insert=true`. The same harness also models six blocking-poll pulse windows × four relay/LED polarity combinations: 24 cases per board / 48 total; its host output asserts `accepted=0`. A transient response-consumption/re-enable mutation is rejected on both boards. This is test-harness work; no production sketch, CORE API, finance or COE file changed.

Exact current-head CI:
- Focused [#46056656161](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656161): PASS, exact-source/ledger guard and poll/relay/pending-evidence host lab.
- Mbed [#46056656203](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656203): PASS, 3/3 (source contract, Arduino core 3.3.13, core 4.0.0).
- Full [#46056656151](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46056656151): FAIL at `Controller protocol parity`; 15 jobs succeeded, 13 skipped, one validation job failed. No signing/publication acceptance.
- Native PAY-0745: NOT RUN on #365.

This improves a source-extracted deny-only test matrix but does not establish physical acceptor pulse retention and does not resolve P0 #177.

## 3. P0 #177 and controller contract re-read

Issue #177 remains OPEN. Its embedded source pin `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed` is stale relative to the live active v0.6 branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`.

- ESP8266 sketch blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: synchronous `post("poll")` at line 354; first `digitalRead(runCoinPin)` at line 357.
- ESP32 sketch blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: synchronous `post("poll")` at line 314; first `digitalRead(runCoinPin)` at line 318.
- The blocking request timeout is 3,500 ms. The active branch was not changed by #365.

Current main controller CGI `vendo` blob `2e3a1430d08cc6606429a042df3b5848f53c7267`: `register|ping` and `poll` response blocks (lines 63–86) do not emit controller `response_sig`. Later `response_sig` fields belong to member endpoints and do not authenticate controller poll/disposition. The current firmware consumer also does not verify a controller response signature.

CORE owns authenticated register/poll, receipt identity and disposition semantics; HARDWARE owns firmware intake/relay behavior; QA owns independent golden-vector and source-linked regression verification; MASTER owns cross-role interface coordination only. Keep coin/relay admission deny-only. Do not invent positive tokens or weaken fail-closed checks.

## 4. COE #26 exact tree, route, test and license audit

Source #365 recursive tree: 2,432 entries / 1,886 blobs, non-truncated. COE #26 destination tree: 286 entries / 207 blobs, non-truncated.

| Route | Source | Destination | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone | 12 | 4 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 47 | 16 | 9 | 19 | 22 |
| HARDWARE ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| HARDWARE ESP8266 | 16 | 1 | 0 | 1 | 15 | 0 |
| QA PisoWiFi tests | 151 | 19 | 2 | 2 | 147 | 15 |
| RELEASE workflow | 1 | 1 | 0 | 1 | 0 | 0 |

The two board sketches are divergent:
- ESP32 source `a673e323e1c160cbfe03949d13a9e01b47386596` vs destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 source `7527dbff41b7f21bdc3d3ed9ee3db1c0d21eb07b` vs destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.

The QA route counts include documentation, fixtures and vendor entries, not only executable tests.

SOURCE_INTAKE schema 8 has 61 runtime rows; actual status counts are 46 byte-identical / 15 derived, while its summary declares 47 / 14. It lists 15 derived tests. MIGRATION_MAP has 18 test rows (4 original + 14 derived), omits `tests/voucher_txn_journal.sh`, and carries stale hashes for `run_focus.sh` and `member_txn_journal.sh`. The intake pins historical source `6d4c9b48` and destination branch `feature/pisowifi-cleanup-stabilization`, while live PR #26 uses `integration/ecosystem-nonproprietary-candidate-20261111@b382d233`.

Ten source LICENSE/NOTICE/license artifacts were enumerated; four mapped counterparts are exact and six are absent (root NOTICE, Android launcher LICENSE, Android `assets/license.html`, jsQR LICENSE, UI QR LICENSE and Tabler LICENSE). The destination firmware audit says the sketches were not copied, but the destination tree contains one divergent sketch per board.

All five PR #26 workflows are terminal CANCELLED: [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557), [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632). COE main remains a three-entry scaffold. **No staging, copying, moving, overwriting, cherry-picking, rebase, retarget or destination write occurred.**

## 5. Other role CI snapshot

| Role | Exact-head result |
|---|---|
| CORE #252 `c82705f2` | [Build #42698139210 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210), scoped only. |
| RENTAL #328 `10fc200b` | API #45622918364 PASS; auth/installer #45622918551 PASS; APK #45622918340 PASS; shared build #45622918468 FAIL. |
| PISONET #255 `d01fd164` | Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED. |
| QA #290 `5c29d159` | Windows synthetic #43633486963 PASS; native COM lab not invoked. |
| QA #292 `75a3f66d` | No exact-head run/status. |
| RELEASE #291 `bf339a76` / #242 `36c0d0bb` | No exact-head PR-triggered runs/statuses. |

All listed owner PRs remain OPEN / DRAFT / UNMERGED. CORE was not modified. The automation inventory surfaced active `Blaze Hourly Production Development` assigned PHX-HARDWARE; no exact-title `Blaze Production Continuation` entry surfaced.

## 6. Private registry, policy and execution limits

Root README and AGENTS.md were read. AGENTS-linked public cloud policy and storage handover were read from the renamed `BlazeDevStudio/BlazingSystems` repository (policy blob `5e503925...`, handover blob `a15f14cb...`).

Full Library pagination covered 1,422 items across eight pages. It surfaced registry snapshots v3–v7 and a base registry, plus a 2026-11-09 private production checkpoint that references v11; the canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections themselves were not surfaced. The available artifact-manifest and sync-ledger snapshots are dated 2026-10-26, not current authority. No dedicated Google Drive connector is exposed. Older snapshots were not substituted; private IDs/content were not emitted and no Drive artifacts were created or changed.

A read-only in-memory audit ran 17 assertions over live refs, ownership, source/destination trees, intake/map counts, sketch/license identities and exact-head CI: **17/17 PASS**. This is not the repository test suite.

Master Python suite: NOT RUN. `verify_coordination.py`: NOT RUN. No exact-head Master Actions run or combined status. Physical acceptance: NOT TESTED.

## 7. Required next actions

1. Registry custodian: restore authorized canonical v11 and newer corrections plus current manifest/ledger via a connected Drive surface.
2. CORE + HARDWARE: publish the authenticated controller poll/receipt/disposition contract and reconcile active-v0.6 source authority.
3. QA: review #365 transport vectors and resolve Controller protocol parity without weakening fail-closed semantics.
4. COE integration owner: reconcile exact source/destination pins, test identities, missing files and license counterparts; keep #26 frozen until independent review.
5. Repository administrator: provide a non-Codex local checkout or dedicated Master CI path for the Master Python suite and `verify_coordination.py`.

**Final disposition: PHX-MASTER coordination-only progress; production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA/native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, secret provisioning, hardware flash, physical test, real payment operation or financial migration occurred.
