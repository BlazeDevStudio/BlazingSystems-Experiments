# PHX-MASTER UTC04 — exact Hardware, P0, COE and role/CI audit

**Task:** `PHX-MASTER-20261128T04Z-HW371-P0-COE26-EXACT-PROVENANCE`  
**Timestamp:** 2026-11-28T04:37Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repository provenance and integration matrices only.  
**Policy:** Strict NO CODEX. No subsystem source branch, COE destination, hardware, payment system, secret or release artifact was modified.

## 1. Live repository identity

| Repository / ref | Exact HEAD |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments active v0.6 `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master coordination audit-start `phoenix/master-coordination` | `696852a64b096d8502cf08dda36bf759eb813b62` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 candidate `integration/ecosystem-nonproprietary-candidate-20261111` | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Experiments and COE default branches are `main`. Experiments `main`, development, v0.6 and Master branch endpoints report `protected=false`; the repository rulesets endpoint returned an empty list. Repository administration must independently establish protected-branch enforcement.

## 2. Control plane and Master PR

- Issue [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) is OPEN. The latest current-date Master checkpoint before this activation is UTC03; no `PHX-MASTER-20261128T04Z-HW371-P0-COE26-EXACT-PROVENANCE` or current-date UTC04 Master message ID existed at audit start.
- Cleanup [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN with 0/7 accepted tracks. No mass move, rename or deletion is authorized.
- Existing [Master PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) remains OPEN / DRAFT / UNMERGED. Audit-start head `696852a64b096d8502cf08dda36bf759eb813b62`; base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; 266 changed paths, all under `coordination/phoenix/`; compare is 694 ahead / 1 behind, merge base `f4e8a891`. No rebase, retarget or merge.
- The current role/ownership manifest `coordination/phoenix/OWNERSHIP_ROUTES.json` is blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, status `DRAFT_REVIEW_ONLY`. PHX-MASTER remains `coordination/phoenix/` only, target null. Its source_ref is historical `f4e8a891`, not current main. The manifest was not changed without the registry custodian.
- The uploaded README_FIRST and COMMUNICATION_PROTOCOL were read. README_FIRST explicitly says a prompt does not wake dormant chats; BLAZE-COMMS/1 requires one active run per role/scheduled hour, exact-head revalidation and a unique factual checkpoint. The repository `AGENTS.md` requires the private registry, artifact manifest and sync ledger before artifact creation. No artifact or private record was created.

## 3. Current role-owned PRs and exact-head CI

All role branches remain owner-controlled and unmerged.

| Owner / PR | Exact head | Current exact-head CI |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [Build #43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [native auth #43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | APK #45622918340, API #45622918364 and native auth #45622918551 PASS; [build #45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL: mandatory handover freshness and ESP32 compile `mbedtls/sha256.h` missing |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows synthetic #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED |
| HARDWARE #366 | `07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9` | Poll deny #46059524018 PASS; Mbed #46059523991 PASS; Full #46059524022 FAIL |
| HARDWARE #367 | `85142129ed9336710539ea573ebf8f7a41cb2dd8` | Poll deny #46095032998 PASS; Mbed #46095033011 PASS; Full #46095032997 FAIL |
| HARDWARE #368 | `9885c81d934922fe35777d5c8f7245766b622255` | Poll deny #46095152313 PASS; Mbed #46095152451 PASS; Full #46095152346 FAIL |
| HARDWARE #369 | `6febf546b818d97ae7d1cfae0af5e6d07b11bd05` | Focused #46100665938 PASS; Mbed #46100665996 PASS; Full #46100665973 FAIL at controller parity |
| HARDWARE #370 | `b0fed471b00b88bdc03e0721547667db5edc5ec0` | Poll deny #46104494354 PASS; Mbed #46104494345 PASS; Full #46104494394 FAIL |
| HARDWARE #371 | `18a3fa470970e729a02920607562f4b9a1e50d34` | Poll deny [#46106458815](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46106458815) PASS; Mbed [#46106458810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46106458810) PASS; Full [#46106458816](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46106458816) FAIL |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic #43633486963 PASS; not native COM acceptance |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run |
| RELEASE #291 / #242 | `bf339a76964a1abe2412fac45392fe06a8e66418` / `36c0d0bb3e58786359555b307bb784f720f023ce` | No exact-head workflow runs/statuses |

HARDWARE has two separate active draft chains: deny-latch alias #367 → #368 → #369, and config-lab cleanup #366 → #370 → #371. #371 changes the Hardware workflow, handover ledgers and three host-lab modules only; no production .ino or shared API changed. Its Full validation reaches `tests/controllers.sh` and fails at the unchanged literal `config_revision` presence assertion (blob `53a7af25fdee9a650e10e870c4204e0fb43239c6`, line 21). The validate job is 140860278070. Android plus 13 firmware/platform jobs pass; downstream simulation/update/sign/publication stages are skipped. QA owns the assertion correction; do not add a decoy field to deny-only firmware.

The active separate production-development automation was observed and left untouched. CORE #252 was read-only; no competing CORE task or worker was started.

## 4. P0 #177 — current source still reproduces the ordering defect

Issue [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) remains OPEN. Its body pins stale v0.6 SHA `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed`; the live branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`.

Exact current source readback:
- ESP8266 sketch blob `12c4bb82b6fddafe813674a0b5f692c1d3634073`: `post("poll")` at line 354, first `digitalRead(runCoinPin)` at line 357; HTTP timeout is 3500 ms at line 263.
- ESP32 sketch blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d`: `post("poll")` at line 314, first `digitalRead(runCoinPin)` at line 318; HTTP timeout is 3500 ms at line 230.

The previous insert state is still used by `applyOutputs()` during the synchronous poll; no pre-poll coin-relay inhibit or edge capture is present in these active v0.6 files. P0 pulse-loss risk remains OPEN. The historical host reproduction is simulated only, not electrical/physical evidence. CORE owns authenticated controller poll/receipt semantics; HARDWARE owns firmware; QA owns independent validation; Master owns the interface contract only.

## 5. COE #26 — exact pinned intake and destination remain frozen

[COE integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains OPEN / DRAFT / FROZEN. COE main is only 3 tree entries / 2 blobs; candidate is 286 entries / 207 blobs and 205 changed paths. All five candidate workflows are CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609 and #43096752632.

### Runtime and source-pin findings

- `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f` pins Experiments source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization`; actual PR #26 branch is `integration/ecosystem-nonproprietary-candidate-20261111`.
- All 61 runtime rows match the pinned source blob, destination blob and Git mode. Actual classifications are 46 byte-identical / 15 derived, while the manifest summary incorrectly says 47 / 14.
- Current Experiments main vs the pinned source: 33 unchanged / 20 divergent / 8 missing across those 61 paths. Candidate destination vs current main: 25 same / 28 different / 8 missing. The candidate is not current-main-equivalent.
- Four original tests: `portal.sh` and `security.sh` are byte-identical; `config.sh` and `integration.sh` are derived.
- All 15 derived-test manifest blobs and modes match actual destination files. Statuses: 11 NOT_RUN, 4 PENDING_CI_RUN. `MIGRATION_MAP.md` has only 14 derived-test rows and omits `tests/voucher_txn_journal.sh` (manifest blob `4277a56af800b930135745bb942d62b6d580cb99`). Two mapped hashes are stale: `run_focus.sh` map `fa1f4f2c6393504499d50659d8bf980caf7ff85b` vs intake `2b7b861ec63cf811d18d0e63b11a65efd1bec0e9`; `member_txn_journal.sh` map `01dc9c65ae9d74eaafb403d47aebcd20edd14390` vs intake `d04df3c6f3ada60b9fda8c8c04230dd31e37019a`.
- Pinned source has 10 LICENSE/NOTICE artifacts; candidate has 4 exact counterparts. Six missing: root `NOTICE.md`, Android Launcher `LICENSE`, Android Launcher `assets/license.html`, jsqr vendor `LICENSE`, UI QRCode `LICENSE`, UI Tabler `LICENSE`.
- Current v0.6 ESP8266/ESP32 source blobs `12c4bb82...` / `29f1125d...` differ from candidate blobs `c8be98f72596681e36a3ad1f8939bf8046c96887` / `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`. The candidate contains both .ino files even though `docs/audits/HARDWARE_FIRMWARE_AUDIT.md` says they were not copied. Treat this as a material documentation/tree contradiction, not an approved import.
- No migration staging, copy, move, overwrite, cherry-pick, rebase or retarget occurred.

### COE role CI

- COE RELEASE #35 at `bc57ba8ecc5245ce538c6770a45bb25e2b8b5ef3`: case-collision #45897198239 PASS; ImageBuilder #45897198204 FAIL because `bwrap` is absent; Hardware/Shared #45897198326 FAIL because ten profiles lack an approved site-scoped RFC 4193 ULA /48.
- COE CORE #45 at `9d76a134c1f6512aa40c20ec4d247306a71a8cce`: overlay/shell #44295049727 and case-collision #44295049903 PASS.
- COE INTERCON #49 at `aeb8ff11b2f5db9a5f86280ab62ab988245f3919`: Stage 5.1 #44646341873 and case-collision #44646341992 PASS; Hardware/Shared #44646341922 FAIL because ESP32 compile cannot find `mbedtls/sha256.h`.

## 6. Registry, execution and blockers

- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json`, newer corrections, artifact manifest and sync ledger were NOT RECOVERED. The Google Drive connector is not exposed in this runtime; Library search surfaced only older v3–v7 snapshots. No older snapshot was substituted and no private IDs/data were published.
- GitHub tree/blob/mode, PR, branch, workflow, job and log inspections were executed read-only. Existing owner CI results above are real hosted runs, not Master-triggered tests.
- Master Python suite and `verify_coordination.py` were NOT RUN. An ordinary non-Codex `git clone` attempt failed because this execution environment could not resolve `github.com`; no local checkout was available.
- Cleanup #266 remains 0/7. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified.

## 7. Next owner actions

1. QA: replace the stale `config_revision` presence assertion with source-linked deny-only vectors and rerun Full on the exact successor SHA.
2. HARDWARE: refresh #371 and #369 handovers/PR descriptions after terminal CI; keep production firmware and shared APIs under Hardware/Core ownership.
3. CORE + HARDWARE + QA: define and independently verify authenticated controller poll/register/receipt semantics and resolve P0 #177 on owner branches.
4. COE integration owner: reconcile the source/destination branch pins, manifest summary, two stale test-map hashes, missing voucher test map, six missing license/notice artifacts and firmware-audit contradiction before any staging.
5. Registry custodian / repository administrator: provide authorized v11 plus newer corrections, artifact manifest and sync ledger; verify effective branch protection; provide a non-Codex Master test environment.

**Disposition:** COE #26 FROZEN. Cleanup #266 OPEN / 0-of-7. P0 #177 OPEN. Production NO-GO. No merge, release, signing, secret provisioning, hardware flash, physical test, real payment operation or financial migration.
