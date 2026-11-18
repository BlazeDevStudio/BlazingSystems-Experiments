# HARDWARE #323 poll-deny contract, legacy fixture mismatch and exact-head reconciliation

**Date:** 2026-11-18 UTC07  
**Role:** PHX-MASTER  
**Disposition:** DRAFT-ONLY / QA-BLOCKED / MIGRATION-HOLD / PRODUCTION NO-GO  
**Scope:** coordination, architecture, exact-head evidence and cross-repository routing only. No Hardware, QA, Release, CORE or COE source branch was modified.

## 1. Live refs and control-plane freshness

| Reference | Exact current value |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch before this commit | `phoenix/master-coordination@d60e751f717e5b29a1cba3c8002f8adb0366f363` |
| Master PR #288 | OPEN / DRAFT; base `main@f4e8a891...`; 72 existing changed paths, all under `coordination/phoenix/` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| OWNERSHIP_ROUTES.json | blob `e4db324315a1b3543fec17a148fbf960170fcb29`; `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null |

Issue #172 remains the single control-plane inbox. Its body still contains an older Master branch head and older role PR pins; this UTC07 checkpoint and the updated coordination matrix supersede those pins for current work. Cleanup issue #266 remains OPEN and cleanup-first; its historical source refs are not current branch authority. No previous PHX-MASTER UTC07 checkpoint was found before this run.

## 2. Current Hardware lineage

| PR | Current exact head | Base | Disposition |
|---|---|---|---|
| #317 | `fce915c1167fc43c6936f3594ae9efce376b711f` | #315 | Parent candidate |
| #320 | `b2b41a3d6ce7887b9624137c966f58462895d3fa` | #317 | ISR/poll-edge child |
| #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | #320 | Output-preload child |
| #323 | `0d6f0c7f4f9d2d07bc43d24e5db63d8bddb11f43` | #322 | Current Hardware candidate; source/test parent `a3aa967087680887e925791f83a8fbc48a1e62b9` |
| #318 | `696e28ed4cd53b9189b78095b38aee973d774683` | #317 | Separate branch; compare is DIVERGED 51 ahead / 71 behind; no current-head workflow run |

#323's current PR head is a documentation-only successor whose parent is the exact source/test head `a3aa967...`. The live PR description is stale: it still reports docs head `f98bc39c...` and source/test `67381712...`. Master did not edit the Hardware-owned PR body or source.

## 3. Source-grounded poll authorization contract

Current ESP8266 sketch blob: `8e79b9eb8856e67d966f4c6385f89fccdc8be7fc`.  
Current ESP32 sketch blob: `bd74b11c1496b0943404ff387ee72bb45d4743e5`.

Both sketches implement `acceptPollResponse()` as a deliberate hard-deny: it ignores the response, sets `insertMode=false`, clears `activeTarget`, and returns false. Both also implement `coinPostDispositionVerified()` as hard-deny. No unsigned poll response can authorize coin insertion or pending-coin disposition through these functions.

The current Experiments `cgi-bin/vendo` poll branch (blob `2e3a1430d08cc6606429a042df3b5848f53c7267`) emits `ok`, `insert`, `target_nonce`, `expires` and controller JSON, but no `response_sig`. The COE #26-derived poll signature candidate is not an adopted contract and has no approved shared golden vectors.

### Exact QA fixture mismatch

- `tests/v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` still requires literal `response_sig` and `|poll|` strings in both firmware sketches.
- `tests/controllers.sh` blob `f7896647713d6bf8034ff48ed19b6383e4dedea0` invokes that legacy fixture.
- Neither QA test file is changed in PR #323. The Full workflow fails at the fixture's `Missing poll signature check` assertion.

This is a contract/fixture mismatch: the inherited positive-presence assertion conflicts with the current intentionally deny-only firmware and the current unsigned source poll producer. Do **not** add a synthetic `|poll|` string, accept an unsigned poll, or weaken the deny path merely to satisfy grep. PHX-QA should replace the legacy positive-presence assertion with source-extracted negative tests proving that an unsigned/unknown poll response cannot enable insertion, retain a target, clear a pending coin or authorize a disposition. A future positive poll path requires a PHX-CORE-owned producer/consumer schema, canonical serialization, golden vectors, pinned two-sided tests and independent QA approval first.

## 4. Exact-head Hardware CI

All three current PR workflows report head SHA `0d6f0c7f4f9d2d07bc43d24e5db63d8bddb11f43`.

| Run | Result | What it proves |
|---|---|---|
| [44256737982 — Quarantine Byte Readback LAB](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256737982) | SUCCESS | Source-extracted quarantine / persistence lab only |
| [44256738001 — Relay Output Polarity LAB](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256738001) | SUCCESS | Host-simulated output/poll regression only |
| [44256738002 — BlazePwifi build](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256738002) | FAILURE | Validation job `134640181011` fails at inherited `Missing poll signature check`; all 14 target/platform build jobs completed SUCCESS; downstream simulations, update/import, signing and publishing jobs were skipped |

The focused logs report poll-response fail-closed 11/11, strict root JSON 13/13, coin POST ACK root status 4/4 and coin-disposition default-deny 4/4. They explicitly report `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `SIMULATED_ONLY=1` and `PRODUCTION_FINANCIAL_AUTHORIZED=0`. This is CI/SIMULATION evidence, not board flash, electrical acceptance or power-cut proof.

The Full-run checkout merge ref was `59a264e382cc111282838c10d393c66468425120`, merging live PR head `0d6f0c7...` into parent #322 `50d93e0...`.

## 5. COE Release and destination state

COE Release PR #35 is a child of #31. Live docs head is `68657a5fcc21df3883c8f3296c3925d5876ac05b`; source/test parent is `5fe815f9e985bf2280b05fb189598826c68a7be6`. Its PR description is stale at `d73986d2...` / `aaecb633...`; PHX-RELEASE should refresh the description rather than Master editing its source/PR.

- [44259106391 — shared/firmware](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44259106391): SUCCESS.
- [44259106288 — case-collision](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44259106288): SUCCESS.
- [44259106331 — mandatory sandbox](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44259106331): FAILED CLOSED. The 9/9 host preflight tests pass, but the real unprivileged bubblewrap probe fails with `setting up uid map: Permission denied`, exit 125. Sandbox-dependent packaging regressions are skipped. No privileged mapping or unsandboxed fallback is approved.

COE #26 remains at `b382d233...` with five workflows QUEUED and zero jobs. It has no combined integration acceptance. INTERCON Stage-3 #39/#40/#42 remain incompatible 64/76/92-byte journal alternatives; Stage-4 #41 is shadow-only on #39 and #43 is live timer/relay on #42. Neither Stage-4 branch is selected or integrated.

No destination copy, move, overwrite, rename, rebase, merge or route change occurred. Exact source/destination blobs, licensing applicability, import completeness, test identities and exact-head combined CI still require owner review.

## 6. Current role/CI snapshot

| Role | Current owner PR/head | Exact evidence |
|---|---|---|
| PHX-CORE | Experiments #252 `c82705f2...` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped SUCCESS; separate CORE continuation retains ownership |
| PHX-RENTAL | Experiments #289 `68928774...` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235), [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) scoped SUCCESS |
| PHX-PISONET | Experiments #255 `d01fd164...` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) scoped SUCCESS; native COM acceptance remains separate |
| PHX-HARDWARE | Experiments #323 `0d6f0c7...`; source/test `a3aa967...` | Two focused SUCCESS; Full validation FAILURE at QA fixture; physical acceptance NOT TESTED |
| PHX-QA | Experiments #290 `5c29d159...`; #292 `75a3f66d...` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) scoped SUCCESS; #292 no current-head run |
| PHX-RELEASE | Experiments #291 `a74b8b94...`; COE #35 `68657a5...` (source/test `5fe815f9...`) | #291 [44199987756](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44199987756) scoped SUCCESS; COE #35 evidence above |
| COE integration owner | #26 `b382d233...` | Five workflows QUEUED / zero jobs; no combined acceptance |

## 7. Registry, policy and access limitations

Experiments `AGENTS.md`, root README and NOTICE were read, along with the uploaded Master prompt, README_FIRST and COMMUNICATION_PROTOCOL. AGENTS-linked cloud artifact policy/storage handover endpoints redirect to a different repository identity and were not retrievable through the current GitHub connector. No policy content was guessed.

The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections are unavailable: no Google Drive connector is exposed, and Library search found only older v3–v7 registry snapshots plus a 2026-11-09 production checkpoint. Those older files were not substituted. No private registry contents or identifiers were published.

## 8. Required next actions

1. **PHX-QA:** replace the inherited positive poll-signature string assertion with negative source-extracted deny tests at the current pinned #323 source/test SHA; rerun the Full workflow without enabling poll admission.
2. **PHX-HARDWARE:** refresh PR #323 description with live docs head `0d6f0c7...`, source/test head `a3aa967...` and current CI.
3. **PHX-RELEASE:** refresh COE #35 description with live docs head `68657a5...`, source/test head `5fe815f9...` and the terminal sandbox result.
4. **PHX-CORE:** publish the canonical poll producer/consumer schema and golden vectors; no Master or Hardware source takeover.
5. **Release infrastructure owner:** provide an authorized ephemeral no-secret runner supporting unprivileged user namespaces.
6. **Registry custodian:** restore authorized Drive v11/newer-correction access.
7. **QA/HARDWARE:** retain real noncustomer board acceptance, 150 power cuts and 30-device/24-hour soak as uncompleted gates.

**Production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
