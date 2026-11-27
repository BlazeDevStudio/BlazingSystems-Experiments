# PHX-MASTER UTC06 — exact live-head, Hardware stack, and COE #26 provenance audit

**Observed:** 2026-11-27T06:39:04Z  
**Role:** PHX-MASTER  
**Scope:** coordination/phoenix, architecture/interface contracts, cross-repository provenance and integration matrix only.  
**Execution boundary:** NO CODEX. No subsystem source branch, production configuration, payment system, secret, hardware or migration was operated.

## 1. Exact branch and PR pins

| Ref | Exact observed head |
|---|---|
| Experiments `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` at audit start | `0f533470087aaa69d8d0cec9f879576cf74d7030` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 is OPEN / DRAFT / UNMERGED, head `0f533470087aaa69d8d0cec9f879576cf74d7030`, base `main`, 248 changed paths. The current comparison against Experiments main is **652 ahead / 1 behind** (merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`). No rebase was attempted. The 248 changed paths are all under `coordination/phoenix/`.

The routing manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER target is null. Its `source_ref` is historical `f4e8a891`, not current main. No route or owner was changed.

## 2. New Hardware exact-head delta

### #355 — docs head advanced, source/test unchanged

- PR #355 branch: `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`
- Current branch/docs HEAD: `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`
- Source/test commit: `444c9a68a0da5a1e2c89839afee9705bf37219f2`
- Base #354: `fc842342596786e072630179acfbbc4feeb2ba02`
- The 9f7a8ecb advance is documentation-only; the firmware/test source checkpoint remains 444c9a68.

Exact-head CI:
- [Poll intake deny #45948626013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948626013): **PASS**.
- [Mbed TLS matrix #45948625942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948625942): **3/3 PASS**.
- [Full #45948625969](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948625969): **FAIL**. Validation reaches `tests/controllers.sh:21`, which requires literal `config_revision` in both sketches. The candidate intentionally discards unauthenticated register/poll responses and has no `config_revision` consumer. All 14 target/platform jobs and Android pass; aggregate Full remains failed.
- [Native #45948626003](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45948626003): **FAIL** at `tests/v060_vendo_sequence_contract.py:20`, which requires literal active `clearPending(true/false)` callsites. Do not add unsafe clear calls merely to satisfy callsite presence.

The two failing assertions are QA-owned. PHX-QA must reconcile tests with the deny-only / pending-evidence-preservation invariant; PHX-CORE must publish the authenticated register/poll receipt and disposition contract before any positive response consumer or pending clear. HARDWARE retains firmware ownership.

### #357 — parent stack is stale

- Child head: `94cbb9d2ae74da6e5fa3380b21665091cdfabe70`.
- PR #357 base SHA: `0adb541ae43143d6fc242f3746f56f71a3040d47`.
- Its base branch is the #355 branch; the live base ref now points to `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`.

This is a verified one-documentation-advance stack mismatch. #357 was not rebased, retargeted, force-pushed or otherwise modified by MASTER.

- [Full #45939854153](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45939854153): FAIL.
- [Native #45939854159](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45939854159): FAIL.
- Poll #45939854156: PASS.
- Mbed #45939854178: 3/3 PASS.

**Next owner action:** HARDWARE must restack/rebase #357 onto the current #355 base (or explicitly replace the stack) using its own branch, then rerun exact-head CI. MASTER will not alter the Hardware branch.

### #356 remains a separate successful CI candidate

Docs head `0ea32d31`, source/test `414048cd`. Preflight #45940999149, Mbed #45940999085, Full #45940999134 and Native #45940999113 all completed successfully. Full reports 26 successful jobs, zero failed, four production-related skips. This is CI VERIFIED / SIMULATED only, not physical storage, coin, power-cut or soak acceptance.

## 3. P0 #177 remains open on active v0.6

The active v0.6 branch was re-read at `2fbd2475`, not inferred from #355.

| Board | Exact source blob | Synchronous poll | First coin sample |
|---|---|---:|---:|
| ESP8266 | `12c4bb82b6fddafe813674a0b5f692c1d3634073` | line 354 | line 357 |
| ESP32 | `29f1125d52ff474a0d028ad41f7af201be1f0f9d` | line 314 | line 318 |

Both set a 3,500 ms HTTP timeout. The synchronous poll remains before the first coin sample; the active v0.6 source still parses poll response fields after the blocking call. #355's branch-local deny work is not a merged fix to active v0.6. Issue [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN. No coin slot, relay, physical pulse, power-cut or payment system was operated.

## 4. COE #26 — current destination CI is cancelled, not queued

- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- PR #26 head: `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Recursive trees: source #355 `9f7a8ecb` = **2,422** entries; destination #26 = **286** entries; both trees complete and non-truncated.
- Five destination workflow runs are terminal **CANCELLED**, not queued: #43096752563, #43096752800, #43096752557, #43096752609, #43096752632. Current commit check-runs = **0**; commit statuses = **0** (state reports pending). There is no current exact-head destination CI evidence.

### File-by-file route comparison at current source/destination heads

Counts compare relative paths and exact Git blob SHAs; these are audit counts, not copy instructions.

| Route | Source | Destination | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | 13 | 1 | 0 | 1 | 12 | 0 |
| PisoWiFi tests | 151 | 19 | 2 | 2 | 147 | 15 |
| CORE library | 20 | 20 | 14 | 6 | 0 | 0 |
| Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| Rental Android | 983 | 8 | 0 | 0 | 983 | 8 |
| Rental server | 12 | 4 | 0 | 1 | 11 | 3 |
| Pisonet | 44 | 47 | 16 | 9 | 19 | 22 |

### SOURCE_INTAKE / MIGRATION_MAP revalidation

At COE #26 head, `Pisowifi/SOURCE_INTAKE.json` is blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8; `MIGRATION_MAP.md` is blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9`.

- Source pin: Experiments `6d4c9b487af4d768c4d7627654d119417fcc6e00`.
- Intake destination branch: `feature/pisowifi-cleanup-stabilization` at `331e14bc63e163148f09813da0fdbf4d13581a19`; recorded pre-manifest head `cf59b41e5273bcc42acf59a7971481670e4b2611`.
- Live PR #26 instead targets `integration/ecosystem-nonproprietary-candidate-20261111` at `b382d233`. These are distinct destination branches.
- The 61 runtime rows' pinned source and destination blob IDs all match their actual trees. Actual status count is **46 byte-identical / 15 derived**, while the summary declares **47 / 14**.
- The 4 original test rows record two derived tests and two byte-identical tests. The 15 derived test records comprise **11 NOT_RUN and 4 PENDING_CI_RUN**, all without hardware evidence; `hardware_tested=false` and `full_ci_tested=false`.
- Current #26 workflows are cancelled with zero checks, so historical `executed_in_ci` labels in the intake are not current exact-head CI evidence.

### Licensing

The source tree contains 10 LICENSE/NOTICE/license.html paths; the destination contains 4 mapped counterparts. Four mapped counterparts are byte-identical (project LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE). Six source-side paths have no matching destination path: root NOTICE, BlazeRentalLauncher LICENSE, Launcher `assets/license.html`, jsQR LICENSE, UI QRCode LICENSE and UI Tabler LICENSE. The #26 PR description's statement that licensing conflicts are resolved is not supported by this exact-path audit; legal/integration owner review is required.

**Disposition:** COE #26 remains FROZEN. No file was staged, copied, moved, overwritten, cherry-picked or promoted. The manifest remains DRAFT_REVIEW_ONLY.

## 5. Other live role CI

| Role | Live head | Exact current CI | Boundary / next owner |
|---|---|---|---|
| PHX-CORE #252 | `c82705f2` | Build #42698139210 SUCCESS | CORE retains financial/poll/receipt authority; no Master source edits. |
| PHX-RENTAL #328 | `10fc200b` | API21/23 #45622918364, auth/installer #45622918551, APK identity #45622918340 SUCCESS; shared build #45622918468 FAILURE | RENTAL owns shared-build correction. |
| PHX-PISONET #255 | `d01fd164` | Windows synthetic #42462978704 SUCCESS | Native COM acceptance NOT TESTED. |
| PHX-HARDWARE #355 | docs `9f7a8ecb`; source/test `444c9a68` | Poll #45948626013 PASS; Mbed #45948625942 3/3 PASS; Full #45948625969 FAIL at `tests/controllers.sh:21` (`config_revision`); Native #45948626003 FAIL at PAY-0745 active-clear assertion | QA owns semantic test reconciliation; CORE publishes authenticated disposition contract; Hardware owns firmware. |
| PHX-HARDWARE #356 | docs `0ea32d31`; source/test `414048cd` | Preflight #45940999149, Mbed #45940999085, Full #45940999134 and Native #45940999113 SUCCESS | CI VERIFIED / SIMULATED only; no physical acceptance. |
| PHX-HARDWARE #357 | `94cbb9d2`; PR base `0adb541a` | Poll #45939854156 PASS; Mbed #45939854178 3/3 PASS; Full #45939854153 and Native #45939854159 FAIL | Base is stale: its base ref now points to #355 `9f7a8ecb`; Hardware must restack/rebase without force-push and rerun exact-head CI. |
| PHX-QA #290 / #292 | `5c29d159` / `75a3f66d` | #290 #43633486963 SUCCESS; #292 no exact-head runs | QA owns independent semantic review and exact-head refresh. |
| PHX-RELEASE #242 / #291 | `36c0d0bb` / `bf339a76` | No exact-head workflow runs | RELEASE owns signing/publisher gates and handover. |
| COE RELEASE #35 | `bc57ba8e` | Case #45897198239 SUCCESS; Sandbox #45897198204 and shared Hardware #45897198326 FAILURE | COE RELEASE owns ULA/sandbox and shared-Hardware correction. |
| COE CORE #45 | `9d76a134` | Overlay #44295049727 and case #44295049903 SUCCESS | Synthetic vectors only; no financial acceptance. |
| COE INTERCON #49 | `aeb8ff11` | Stage 5.1 #44646341873 and case #44646341992 SUCCESS; shared Hardware #44646341922 FAILURE | Separate LAB candidate; not canonical financial authority. |
| COE integration #26 | `b382d233` | Five workflows CANCELLED; zero check-runs and zero commit statuses | FROZEN; no staging or migration. |

## 6. Master verification and limits

- Master branch start head: `0f533470087aaa69d8d0cec9f879576cf74d7030`; Master Actions returned **zero runs and zero commit statuses** at that head.
- PR #288 changed-file enumeration: 248/248 paths are under `coordination/phoenix/`.
- Read-only source/tree/manifest/intake comparisons were performed using connected GitHub reads. No Master product test suite or `verify_coordination.py` execution is claimed; there is no authenticated local checkout in this execution surface.
- Cleanup issue #266 remains OPEN / 0-of-7.
- The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. The available Library search did not expose the canonical registry and no Google Drive connector action is available in this run. No older registry was substituted; no private registry contents or IDs were copied into GitHub.
- The separate active `Blaze Production Continuation` automation owns CORE per the user's coordination directive. CORE source was not touched and no competing CORE work was started.

## 7. Owner actions and safety decision

1. **PHX-HARDWARE:** restack #357 onto current #355 head and rerun exact-head CI; refresh its PR/base references.
2. **PHX-QA:** reconcile `tests/controllers.sh:21` and PAY-0745 assertions with deny-only and pending-evidence-preservation semantics; do not demand unsafe `clearPending` callsites.
3. **PHX-CORE:** publish the authenticated register/poll receipt and pending-disposition contract; no Master implementation of CORE authority.
4. **COE integration owner + legal:** reconcile PR #26's branch pins, route/blob matrix, six missing license/notice paths and 15 derived tests; obtain terminal exact-head CI before any staging.
5. **Registry custodian:** restore authorized access to canonical private Drive v11 and newer corrections.
6. **PHX-MASTER:** run the coordination Python suite when an authenticated checkout or Master CI execution becomes available.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No merge, release, firmware flash, secret provisioning, real-payment operation, financial migration, physical test, rebase or force-push occurred.
