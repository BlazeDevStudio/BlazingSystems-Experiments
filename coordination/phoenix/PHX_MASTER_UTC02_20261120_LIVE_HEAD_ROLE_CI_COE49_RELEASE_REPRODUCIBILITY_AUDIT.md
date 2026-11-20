# PHX-MASTER UTC02 — live-head, role-CI, COE #49 and release reproducibility audit

**Date:** 2026-11-20 02:40 UTC  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** Experiments #172/#266/#288, COE #26/#49, current role PRs and exact-head CI  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation was used.

## 1. Exact repository state at audit start

| Ref | Exact HEAD | Protection |
|---|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | `protected=false` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | `protected=false` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` (comparison-only) | `2fbd2475e9f54878c316fa7cea2f228386b0e859` | `protected=false` |
| Master `phoenix/master-coordination` before this run | `b6dd2dc3a81bd51ce82f60efaf06b5b7d236d23c` | `protected=false` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | `protected=false` |

Experiments PR #288 was OPEN/DRAFT at `b6dd2dc3a81bd51ce82f60efaf06b5b7d236d23c`, base `main@f4e8a891...`, with 115 changed paths. COE PR #26 was OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab...`, with 205 changed paths.

Live issue #172 is OPEN. Cleanup issue #266 is OPEN and still records the broad MASTER duplicate/dead-code inventory as incomplete; its MASTER checkbox remains unchecked. No mass move, delete, merge or subsystem source edit was performed.

## 2. Master-owned BLAZE-COMMS/1 validator

Current `coordination/phoenix/verify_coordination.py` blob: `3a6d0ca34cad54cd113abbda17d90898603547b3`. Current Master test file blob: `e8671fa33e602ed4b4d352bba637ab9827cb4650`. Current example envelope blob: `f7a8ad161df15fbf8eb07ce80f5a0fb327e528b4`.

The current validator accepts exactly one registered role ID or literal `ALL` in `to`; unknown, multi-recipient, case-variant and whitespace-padded strings are rejected. The Master test file already contains positive, negative, empty and non-string recipient cases. QA PR #292 remains OPEN/DRAFT at `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`, based on an older Master SHA `b1ca02e...`; no PR-triggered Actions run exists for #292.

**Local focused execution:** a disposable Python harness exercised the current source-extracted `validate_envelope` implementation and current example shape: 4 tests, 4 PASS, 0 FAIL, 0 ERROR. This is an extracted-function test, not execution of the complete repository test file, full Master suite, GitHub Actions or a full source checkout. QA's historical 4/4 source-pair result at verifier blob `903df403...` remains separate evidence; it is not silently relabeled as a current exact-head CI run.

## 3. Current role PR heads and Actions

| Role | PR / exact head | Current exact-head Actions |
|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS (scoped software validation) |
| RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS (scoped Windows CI) |
| HARDWARE | #327 `a2b7903b4009fd7182247e11a7d2954a79cb9bbd` | [#44657641425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641425) quarantine PASS; [#44657641548](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641548) relay/output PASS; [#44657641509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641509) Full FAIL |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS (scoped) |
| QA | #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered run returned; keep DRAFT |
| RELEASE | #291 `734ac932839428c6822397e61b4aa7eaab0c6984` | [#44660004702](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44660004702) BlazePwifi build PASS; [#44660004663](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44660004663) Windows FAIL; [#44660004710](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44660004710) ESP32 reproducibility FAIL on both core versions |

### Failure details requiring owner action

- HARDWARE #327 Full validation fails in `tests/controllers.sh` at `Missing poll signature check`. The source is deliberately default-deny; do not weaken firmware or add a fabricated positive signature marker. The focused quarantine and relay labs are not Full validation or physical acceptance.
- RELEASE #291 Windows job fails in PISONET-owned `negative-selftest.ps1`: `$buildWorkflow` is read before being set. The publisher job is skipped.
- RELEASE #291 reproducibility check builds the same #327 sketch twice with equal image sizes but different SHA-256 values. ESP32 core 3.3.13: `49550b7a...` vs `e3e30940...`; core 4.0.0: `342627a6...` vs `2f73e80d...`. The reproducibility guard is correctly RED; do not weaken it. PHX-RELEASE must identify nondeterministic build inputs and rerun both pinned cores.

## 4. COE destination staging — no migration proposed

COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab...`, 205 changed paths: `.github` 5, Hardware 4, Pisonet 47, Pisowifi 95, Rental 19, Shared 19, docs 9, tools 6, plus `.gitignore` 1. Five destination workflows remain QUEUED and expose zero jobs: #43096752609, #43096752632, #43096752800, #43096752563 and #43096752557. No completed exact-head destination CI is available.

The live `OWNERSHIP_ROUTES.json` blob remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, source ref `f4e8a891...`, destination candidate #26 `b382d233...`, and PHX-MASTER target `null`. It is a review map, not a copy/move authorization.

## 5. COE #49 Stage 5.1 — separate audit-only candidate

COE #49 is OPEN/DRAFT at `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`, stacked on #48 `8286548e...`; it changes no `Pisowifi/` backend path and is not based on #26.

- [Stage 5.1 run #44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873): all five jobs PASS, including static contract, signed-wire parser, bridge fault tests, ESP8266 compile and source-only package.
- [Case guard #44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992): PASS.
- [Shared Hardware #44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922): FAIL; ESP32 core 4.0.0 compile cannot find `mbedtls/sha256.h`; ESP8266 compile passes.
- PHX-HARDWARE ACKed audit-only review and explicitly declined COE source implementation ownership in [#49 comment 7028198239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/49#issuecomment-7028198239). No role ownership was reassigned.

### Cross-role contract blockers from the audit

1. Experiments `main@f4e8a891...` produces unsigned register/poll/coin replies; it has no approved `response_sig` producer for the #49 RouterV1 signature expectation. COE #26 has a separate candidate signature implementation, but its poll lacks authenticated server time and signed target-kind. #26 is not #49's base and is not deployed.
2. `Bridge.tick()` returns ACTIVE for an already-matching ESP session before recalculating the router expiry safety floor. A poll that still says insert=true can therefore bypass a shortened router-side TTL until the local ESP lease expires. Evaluate expiry/close floor before every ACTIVE return and deny when signed time/expiry is absent, stale or regresses.
3. The #26 rental backend can mutate rental progress before returning `rental:true`; a post-response rejection would be too late. The current test stubs the request method and does not prove real backend non-mutation.

Required owners: PHX-CORE defines authenticated server-time/TTL, target-kind and event-bound receipt contract plus canonical bytes/golden vectors; PHX-PISONET/COE owner moves expiry-floor evaluation before ACTIVE fast path; PHX-QA adds real backend no-mutation, TTL-shortening and clock rollback/skew regressions. Keep #49 LAB/DRAFT and #26 frozen.

## 6. Private registry and storage limitations

The accessible Library contains older registry snapshots, including v7, but exact canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in title/content search or the 100-item recent Library listing. No Google Drive connector is exposed in the available tool surface. Older snapshots were not substituted; no private registry contents or identifiers were published. Registry verification remains BLOCKED pending authorized custodian access.

## 7. Master disposition and next actions

- Master source ownership remains `coordination/phoenix/` only. No CORE/RENTAL/PISONET/HARDWARE/QA/RELEASE source branch was changed.
- Keep COE #26 frozen; no source file move/copy/cherry-pick is proposed. Exact per-file source/destination blob, mode, license, import/dependency, test identity and destination CI parity is not complete.
- Keep cleanup #266 MASTER inventory open; no mass move, deletion or whole-repo reformat.
- P0 owner actions: QA repairs the default-deny poll fixture; PISONET fixes `$buildWorkflow`; RELEASE fixes reproducibility inputs and reruns both ESP32 cores; CORE/PISONET/QA settle #49 server-time/target-kind/expiry and real backend no-mutation contracts; repository admin establishes protected branches; registry custodian restores v11 access.
- Production remains NO-GO pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates.

## 8. Verification classification

| Activity | Result |
|---|---|
| Live GitHub issues, branches, PRs, manifest and exact-head workflow metadata | INSPECTED |
| Role Actions job/log inspection | EXECUTED READ-ONLY; failures classified above |
| Local extracted-function recipient regression | 4/4 PASS |
| Full Master Python suite / `verify_coordination.py` | NOT RUN |
| Master GitHub Actions | NOT RUN / no Master-specific workflow triggered |
| COE #26 destination jobs | QUEUED; zero jobs available |
| Physical hardware, payment, power-cut or device-soak tests | NOT RUN |

**Initial Master branch head before this audit:** `b6dd2dc3a81bd51ce82f60efaf06b5b7d236d23c`. The final report commit and final remote branch head are recorded by the same-hour PR/issue checkpoint.

## 9. Commit and remote-readback record

Audit started from `b6dd2dc3a81bd51ce82f60efaf06b5b7d236d23c`. The following Master-only commits were returned in order:

- Report creation: `711c2c1ca26030dcae1540d1f43982fd006c7c59`.
- Audit summary: `29fa22cce381c701479f0a4e19f43cf8a3a88d89`.
- Integration matrix: `7bb96842727b505b92ad3d960bb27f1d7f609e08`.
- Role assignments: `f2a4e9b7e2219ef5e4b48d0c47c661b6e871f0c2`.
- Repository routing: `c88bbc71e63eb82e7b3c1d85950e4c3f68c891bc`.

Immediately before this final report update, PR #288 remote head readback was `c88bbc71e63eb82e7b3c1d85950e4c3f68c891bc`. The final report update is the last commit in this run; the exact final branch/PR head is confirmed by the follow-up PR readback and BLAZE-COMMS/1 checkpoint.


## 10. Additional AGENTS storage-control readback

Repository `AGENTS.md` requires checking the private project registry, artifact manifest and sync ledger before storage changes. The Library exposes an older root `BLAZE_PROJECT_REGISTRY.json` and `BLAZE_SYNC_LEDGER.json`, both dated `2026-10-26`, plus versioned registry snapshots v3–v7. These are stale historical snapshots, not the requested canonical v11 or newer corrections. `BLAZE_ARTIFACT_MANIFEST.json` was not located. No Drive connector is exposed, no upload or storage mutation was attempted, and no private IDs or registry contents were copied into GitHub. Canonical v11/newer-correction verification remains BLOCKED.
