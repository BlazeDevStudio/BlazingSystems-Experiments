# PHX-MASTER UTC16 — HARDWARE stack, controller contract and COE provenance audit

**Observed UTC:** 2026-11-28T16:55:10Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repo provenance only.  
**Task ID:** not supplied by a GitHub task issue; none fabricated.  
**Audit input:** `phoenix/master-coordination@397e0d29f9103c6c0f00cd3d943d307e33df238d`.  
**Disposition:** BLOCKED / PRODUCTION NO-GO. Strict NO CODEX.

## 1. Live refs re-read

| Ref | Exact SHA |
|---|---|
| Experiments `main` (default) | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| active v0.6 audit foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| PHX-MASTER PR #288 head | `397e0d29f9103c6c0f00cd3d943d307e33df238d` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains OPEN / DRAFT / UNMERGED. Compare against current `main`: 718 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; 274 existing changed paths are all under `coordination/phoenix/`. No Master workflow run is associated with the input SHA.

## 2. HARDWARE #376–#379 exact-head state

| PR | Current head | Exact-head evidence |
|---|---|---|
| #376 | `0f5968b232f411943c4be3a4d4911a0da4f83fff` | Focused [#46164674619](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674619) PASS; Mbed [#46164674611](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674611) 3/3 PASS; Full [#46164674737](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164674737) PASS including target matrix, 9/9 simulations and update bundle. Signing/publication skipped. |
| #377 | `95ace1236c2b3e4816515c372edd4853ceeed064` | Poll [#46164676430](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676430) PASS; Mbed [#46164676331](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676331) 3/3 PASS; Native [#46164676365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676365) FAIL at QA-owned PAY-0745; Full [#46164676426](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46164676426) FAIL at QA-owned Controller protocol parity after 14/14 target jobs PASS. |
| #378 | `3f67ba41dc3e087f868d3c57f6604e69f7a0e17b` | Poll [#46162754701](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754701) PASS; Mbed [#46162754714](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754714) 3/3 PASS; Full [#46162754741](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162754741) CANCELLED; Native NOT RUN. PR reports mergeable=false. |
| #379 | `5ac75dbb53bc36abc161fb276b6e7e80534e9b28` | Exact final-head Poll [#46167474941](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474941) PASS; Mbed [#46167474965](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474965) 3/3 PASS; Full [#46167474925](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46167474925) FAIL at QA-owned Controller protocol parity after 14/14 target jobs PASS; Native NOT RUN. |

### Branch/stack reconciliation

- #376 and #377 remain separate OPEN / DRAFT / UNMERGED branches. Their new narrow reconciliation note is byte-identical at blob `79df6029dc5a4e83274b1dafa6015340a64ab74f`; HARDWARE reports the three historical shared handovers as append-only.
- #378 is based on #377 at `95e54790ab986dab3c1b3723ea9603a3d125c0d6`, but current #377 is `95ace123...`. The exact compare from current parent to #378 is DIVERGED: 4 ahead / 2 behind, merge base `95e54790...`, with five changed paths including the three shared handovers. The PR is mergeable=false.
- #379 is a child of #378 at `3f67ba41...`; it changes only Hardware-owned test/contract files and handover records, not production sketches. It inherits the stale #378 ancestry. Do not merge #378/#379 until HARDWARE reconciles the child against current #377 and preserves append-only history.
- #379's PR body says no new Actions run appeared for final docs head `5ac75dbb...`; direct run lookup found three exact-head runs (#46167474941, #46167474965, #46167474925). HARDWARE should update its own PR/handover to record that terminal evidence.

## 3. Cross-role controller configuration contract mismatch

This is an integration blocker, not authorization to change another role's source.

- HARDWARE #376 ESP8266 sketch blob `12c4bb82b6fddafe813674a0b5f692c1d3634073` reads `jsonInt(r, "config_revision", remoteRevision)` at line 238; ESP32 blob `6edefc9283a3a4554c15ec9c9e4a9e038e98504d` does the same at line 233. Its legacy `applyRemoteConfig(r)` reads flat root-level fields.
- CORE PR #252 current head `c82705f2de865c89ab733b10efa84f26f56a5cc4`: `controller.sh` blob `1a820416051a7af5462841b191b02630aa87781f` builds a controller object containing `config_revision`; Vendo CGI blob `16eb4105c15569dfd77b19a276ee05a25768083e` nests it under top-level `controller` and adds top-level `config_auth`. The signed v1 object carries `revision`, `policy_sha256`, and `admission_allowed:false`.
- CORE's `CONTROLLER_RESPONSE_AUTH_V1_LAB.md` blob `3528bf3a4cd63f83fdb2fb0eba9aa8a2265ae0a5` explicitly labels v1 a source-level lab proposal, not provisioning or paid-admission authorization; the consumer must verify the complete HMAC before applying even non-actuating configuration.
- Therefore #376's flat-root parser does not consume the current nested `controller.config_revision` or verify `config_auth`. #377's current sketches (ESP8266 blob `426ada921d6d20a56e3fdad9f3efd4bdf5047464`; ESP32 blob `449c76a6f2fbab548bd355c07a39bbfc850e0cb0`) reject register/poll replies as an unapproved authenticated control envelope and remain deny-only. #379 is test-only and does not resolve the wire contract.

**Decision:** do not copy `config_revision` into #377, treat `config_auth.revision` as positive authority, add a decoy field, or invent `response_sig`. CORE must publish the canonical versioned authenticated configuration contract; HARDWARE owns the consumer; QA owns semantic verification of the same exact SHA. Coin/relay admission remains denied.

## 4. Active v0.6 P0 poll ordering

At active branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`:
- ESP8266 sketch blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: synchronous poll line 354; first `digitalRead(runCoinPin)` line 357.
- ESP32 sketch blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: synchronous poll line 314; first coin sample line 318.

P0 [issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN. Candidate deny-only and host mutation tests do not establish pulse retention, relay polarity or physical acceptance.

## 5. COE #26 exact migration provenance

Trees were complete and not truncated: pinned source snapshot `6d4c9b487af4d768c4d7627654d119417fcc6e00` = 2,391 entries; current Experiments main = 2,341; COE candidate #26 = 286; COE main = 3.

- Runtime intake: 61/61 source and destination blob+mode rows match. Actual classification is 46 identical / 15 derived, while schema-8 summary declares 47 / 14. No runtime row is missing or hash/mode-mismatched.
- Against current Experiments main, pinned runtime rows are 33 unchanged / 20 changed / 8 absent.
- Original tests: 4/4 exact against pinned source and destination. Derived tests: 15/15 destination blobs exact. The migration map has only 14 derived-test rows and omits `voucher_txn_journal.sh`.
- Two map hashes are stale: `run_focus.sh` records `fa1f4f2c6393504499d50659d8bf980caf7ff85b`, actual `2b7b861ec63cf811d18d0e63b11a65efd1bec0e9`; `member_txn_journal.sh` records `01dc9c65ae9d74eaafb403d47aebcd20edd14390`, actual `d04df3c6f3ada60b9fda8c8c04230dd31e37019a`.
- Four in-scope PisoWiFi legal artifacts (first-party LICENSE, QR vendor LICENSE, TailAdmin LICENSE and NOTICE) are exact blob+mode matches. Seven other source legal files are outside this PisoWiFi-only intake, not missing in-scope counterparts.
- Manifest destination branch pin `feature/pisowifi-cleanup-stabilization` is stale; live PR #26 branch is `integration/ecosystem-nonproprietary-candidate-20261111`.
- All five candidate workflows remain CANCELLED. No staging, destination write or move occurred. COE #26 remains FROZEN.

## 6. Other roles and CI

| Role / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; CORE untouched. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Build [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and native auth [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | Build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL; API21/23 smoke [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), native auth [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows release [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM acceptance not established. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head workflow. |

## 7. Governance, access and validation

- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains 11 routes / `DRAFT_REVIEW_ONLY`; PHX-MASTER target is `null`. Five bounded in-memory route assertions PASS. No ownership route changed.
- GitHub reports `protected=false` and required-check enforcement `off` for Experiments main, development and active v0.6, and COE main. Repository administration must verify/enforce protection.
- Root `AGENTS.md`, the Cloud Artifact Policy and Storage Recovery Handover were read. The full 1,308-item Library inventory did not contain canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` or newer corrections. No Google Drive connector/action is exposed. v3–v7 copies were not substituted; no private IDs/data were copied to GitHub.
- Automation inventory exposes active `Phoenix Master Hourly Development` and `Blaze Hourly Production Development`, not the exact title `Blaze Production Continuation`. CORE remained read-only to PHX-MASTER; no competing CORE work or new automation was started.
- Master Python suite, `verify_coordination.py`, local repository tests and Master CI were NOT RUN. The GitHub connector offers no workflow-dispatch action; authenticated non-Codex checkout is unavailable. Source/tree comparisons and in-memory assertions are not repository tests.

## 8. Required next actions

1. **HARDWARE:** rebase/reconcile #378 against current #377 head `95ace123...`, preserve the append-only handovers, update #378/#379 exact-head descriptions and rerun the appropriate Poll/Mbed/Native/Full gates. Keep both PRs draft.
2. **CORE:** publish the canonical versioned authenticated configuration envelope and explicit revision semantics; no positive admission until independent authority/freshness exists.
3. **QA:** replace source-shape parity assumptions with semantic fail-closed tests for the approved contract; independently verify PAY-0745 and Controller parity at the same SHA.
4. **COE integration owner:** reconcile 46/15 summary, 15-to-14 derived-test map, voucher row, two stale hashes and destination branch pin before any staging proposal.
5. **Registry custodian / repository administrator:** provide authorized private registry v11/newer corrections and verify branch protection; provide an authenticated non-Codex validation environment.

**Final decision: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flash, physical test, real payment operation, financial migration or customer cutover occurred.
