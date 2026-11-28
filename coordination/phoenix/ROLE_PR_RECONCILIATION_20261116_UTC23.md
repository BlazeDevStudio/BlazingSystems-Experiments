# PHX-MASTER — live role PR/CI and hardware-stack reconciliation

**Snapshot:** 2026-11-16T23:34Z (2026-11-17 07:34 PHT)  
**Role:** PHX-MASTER  
**Task:** #172 / #266 / #288 — current owner/CI reconciliation and overlapping hardware-stack hold  
**Status:** DRAFT / PRODUCTION NO-GO

## 1. Exact repository and branch identity

| Ref | Exact SHA |
|---|---|
| Experiments default branch `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development branch `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master draft branch before this audit `phoenix/master-coordination` | `8201deb9198a8416a6546584a9a8f5789526ad84` |
| COE default branch `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

The Master PR remains open and draft, based on Experiments main. The default, development, Master and COE refs were read independently; no SHA was inferred from prior checkpoints.

## 2. Routing and cleanup boundary

- Root `AGENTS.md` on Experiments main and the Master branch is the same blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`.
- Current `OWNERSHIP_ROUTES.json` is blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, status `DRAFT_REVIEW_ONLY`, source ref `f4e8a891...`, destination candidate PR #26 at `b382d233...`.
- The Master route is `coordination/phoenix/` only, with no runtime destination. No route authorizes recursive copy.
- Cleanup issue #266 remains open. This activation mapped active PR overlap and stack ancestry only; it did not perform mass moves, source deletion or a complete dead-file inventory.

## 3. Live role PR and CI observations

These are per-commit GitHub Actions observations, not proof of combined integration acceptance.

| Role | Current PR heads | Observed CI |
|---|---|---|
| MASTER | #288 `8201deb9198a8416a6546584a9a8f5789526ad84` | No PR-triggered workflow runs returned |
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Run [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) success |
| RENTAL | #240 `a7d113fb8ae3f0c5e838e64d31cae7a154e37b56`; #289 `68928774d0d7cf65adb26bc6b54199a3159d066c`; #287 `a4fffd01c8fb1818c32a53522e0590c1dc8a77cd` | #240 runs 40910311141/40910311159 success; #289 runs 43653329235/43653329229 success; #287 run 43754089203 success |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Run [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) success |
| HARDWARE | #294 `8cbd4ecec6fcc4a5b0c758c300de986abee5cf40`; #314 `556adc20ef0cfd355089aff3b979c0169af79bdd`; #315 `953b743f3edc26671ddf7a457c2a4a4ac0de093f`; #316 `888e6941e3a7a81641682c23d937f97d8117d2ea`; #283 `a87567291e80006f3f30cea81fc20e8b299b95e8` | #294 runs 43669122948/43669122828 success; #314 runs 43782088731/43782088748 success; #315 runs 43963997471/43963997475 success; #316 focused lab 43972511337 success, full build 43972511250 failure; #283 run 43634101437 success |
| QA | #267 `ff5367990c2d27b8ebbb822ee208251af0c890e2`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`; #279 `8f476ef05893193325ef3d1f65a35e144ae7a568` | #267 run 41452247439 success; #292 and #279 have no PR-triggered runs returned |
| RELEASE | #242 `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 `2c4edff231d9b2819415086825530d80b8801307` | #242 run 40882814472 success; #291 run 43744993487 success |

COE PR #26 has five queued candidate-head workflows, not completed CI: 43096752609, 43096752632, 43096752800, 43096752563 and 43096752557. Master #288 has no PR-triggered workflow runs.

## 4. HARDWARE #294 / #314 / #315 / #316 overlap and ancestry

The PR file lists establish that #315 and #316 both modify the same two production sketches:

- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`

Their bases differ: #315 is based on #314 head `556adc20...`; #316 is based on #294 head `8cbd4ece...`. Compare #314 head against #294 head shows #294 is an ancestor and 107 commits behind #314. Comparing #315 head `953b743f...` against #316 head `888e6941...` reports **diverged** histories (10 commits ahead / 108 behind; common base #294 head). These are parallel review stacks, not a safe linear merge. Do not merge either independently, cherry-pick by filename, or overwrite one stack with the other.

### #316 validation failure is confirmed and bounded

- Focused source-extracted poll-response lab run [43972511337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511337): success.
- Full build run [43972511250](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43972511250): failure in validation job 133668043447 at **Controller protocol parity**.
- Exact job log reports `acceptPollResponse was not declared in this scope` for both ESP8266 and ESP32. The existing #294 source-extraction harness compiles the modified loop but does not extract/declare the new helper. ESP32 and ESP8266 firmware compile jobs themselves completed success.
- The new #316 lab is not yet wired into the shared validation workflow. PHX-QA owns that harness; Master did not modify QA files.

### Provisional keyless-auth contract mismatch

The #316 patch initializes `signatureOk=true`, then verifies a response signature only inside `if(String(cfg.key).length())`. With an empty key, signature verification is skipped; a response containing `"ok":true` can proceed to update `insertMode` and `activeTarget`.

This conflicts with the **provisional** default-deny requirement already recorded in [Architecture Contracts §6.1](ARCHITECTURE_CONTRACTS.md): an empty/unprovisioned key is not an authentication success and no keyless `ok=true` response may authorize coin intake. Owner review is still pending, so this is recorded as a source-level contract mismatch, not as physical acceptance or a production exploit finding. PHX-CORE and PHX-HARDWARE must agree the policy; PHX-QA must add an empty-key negative case.

The #315 handover/issue checkpoint also records that `journalRecoveryRequired` is RAM-only. A same-boot inhibit does not prove cross-reboot non-replayability. Durable rejected-event disposition remains a PHX-CORE / PHX-HARDWARE interface question with independent QA required.

## 5. QA freshness

QA PR #292 head `75a3f66d...` contains verifier blob `a8a989964c45ab9aef5719e8d17ba3f6fc66e773`; current Master head contains verifier blob `3a6d0ca34cad54cd113abbda17d90898603547b3`. They are not identical. The branch comparison shows 63 Master-only commits and 6 QA-only commits since common base `add087f84a2fda6f6aedf9938e38394f2b2c27be`. The QA README's 4/4 claim references a different older verifier blob `903df403...`, not current Master. Do not label #292 as current-head GREEN; it has no PR-triggered workflow run.

## 6. P0 blockers and registry access

Issues #31 (member ledger replay/atomicity), #32 (rental receipt/lease crash consistency), #34 (physical acceptance), #43 (independent freshness witness) and #177 (coin pulse during synchronous poll) remain open. Required independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts and 30-device/24-hour soak remain unverified. **PRODUCTION NO-GO**.

The exact private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible through the current connected tool surface. Exact-name Library search did not return v11; older Library registry files were not substituted. The AGENTS.md storage-policy/handover links could not be retrieved through the connected GitHub file reader. No private Drive contents or identifiers were published.

## 7. Execution limits and next owner actions

- No local Master test suite was executed: `git ls-remote` failed because this runtime could not resolve `github.com`. Source/tree inspection and GitHub Actions observations above are not local test execution.
- PHX-HARDWARE: reconcile #315/#316 into one owner-controlled stack; implement default-deny for an empty key if the shared contract is confirmed; persist rejected-event disposition across reboot.
- PHX-QA: update the canonical extraction harness to include `acceptPollResponse()`; rerun both boards' failure matrix at the consolidated exact SHA, including empty key and reboot/failure cases.
- PHX-CORE: define single-authority replay and durable rejected-event semantics with HARDWARE; review keyless admission policy.
- PHX-MASTER: refresh this routing/CI snapshot after owner checkpoints; keep destination PR #26 review-only until exact source/destination parity, licenses, imports, tests and rollback are independently verified.
- Registry custodian: restore authorized private Drive access to v11 and newer corrections without publishing private identifiers.

No Codex, subsystem source edit, source migration, merge, release, signing, secret provisioning, hardware flash, physical test, customer action or live financial operation occurred.
