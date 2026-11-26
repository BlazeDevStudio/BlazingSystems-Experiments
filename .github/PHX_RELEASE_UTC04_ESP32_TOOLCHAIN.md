# PHX-RELEASE UTC04 — ESP32 toolchain lock and retained CI provenance

Activation: 2026-11-26 UTC04  
PR: [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291)  
Branch: `phoenix/release-publisher-isolation-20261115`  
Starting HEAD: `9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30`  
Latest source/test/workflow HEAD: `f556769bec30dea156f223f760547f76d99693ca`; final handover branch HEAD: `4edbe5529276069ecfe8d1cb97473bb9475e0860`  
Base PR #242: `a7e27fe50e13326a7258bbaed1388594141ddda3`; #291 still targets former base `734b89d9e7792247e8376335c3f3685500ab3f89`.

**Disposition: SOURCE/TEST/WORKFLOW COMMITTED / STATIC CONTRACT CHECKS PASS / EXACT-HEAD ACTIONS NOT TRIGGERED / QA REVIEW PENDING / PRODUCTION NO-GO.** Strict NO Codex. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment.

## MASTER assignment and observed gap

PHX-MASTER UTC03 audit [3b7198d1](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3b7198d1d1ddc1651f95bb8065253ba8e68ae46b) assigns PHX-RELEASE complete ESP32 toolchain/package pinning, core-4 binary and manifest retention, and the two-clean-build reproducibility investigation. PHX-HARDWARE owns source identity/build intent; PHX-QA independently reviews evidence.

- Core-4 run [#45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648), job 139665996232: compile PASS; binary SHA-256 `ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e`.
- Prior core-4 run [#45742944327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45742944327), job 139652109745: compile PASS at source/test SHA `d3168ccb`; same sketch blob, binary SHA-256 `f9489e1df0d075cbfce549120c37af2778c53cb055f165c14a1d790623293c31`.
- Runner image versions differed (`20261116.376.1` and `20261116.133.1`). This is an observed difference, not a proven cause. The source/test commits also differed; matching sketch blob alone does not prove identical full source inputs.
- MASTER reports zero retained artifacts from both runs. Root cause remains unestablished; no compromise is inferred.

## RELEASE-owned implementation

1. Added [ESP32 toolchain lock](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6173a2f2dc5f523611be2c0d8678fbc07d60dbae): cores 3.3.13 and 4.0.0; 18/19 Linux tool dependencies with SHA-256 archive checksums; five Arduino CLI builtins per core; Arduino CLI 1.6.0 archive identity; dfu-util 0.11.0-arduino5 checksum.
2. Espressif package index is pinned to immutable commit `8f6bee9761f7b15cce27b79cbd1ae199d0df2adf`, Git blob SHA-1 `b3325781b813ec0b4dbc7cccc1913f53aa685004`.
3. Added [toolchain verifier/provenance capture](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9639a58c9f231c7eec3a0f85429ed60563b24572). It checks the index blob, platform metadata, tool archive URLs/checksums/sizes, installed versions, builtins, Arduino CLI and core versions. Capture records runner image, compiler versions, source/sketch identity, package-index hashes, both binary/ELF SHA-256 values and SHA256SUMS. Manifest marks evidence HOSTED_CI_ONLY and production_authorized=false.
4. Updated [ESP32 compatibility workflow](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/986b4f14d53ccb9aca3cbbd1fea2abf2360b4cd7): immutable package index, lock verification before compile, capture after the two builds, and immutable `actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9` retention for 14 days.
5. Added `test_esp32_toolchain_lock.py`; updated `test_phx_release_esp32_core_compatibility.py` and `test_release_artifact_action_pins.py`. Both push and pull_request path filters include the new lock/script/test. Final path-filter correction: [22963e0a](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/22963e0aaf726dcf0d709898ba219973b5be65ab). The final compiler capture uses the exact explicit compiler/objdump/nm paths already used by the workflow: [f556769](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f556769bec30dea156f223f760547f76d99693ca).

## Verification status and blockers

Static repository assertions passed: lock JSON parses; both core versions and all archive checksums are present; pinned URL/blob match; both path filters include the new files; lock verification precedes compilation; capture/upload follow compilation with `if: always()`; upload action is pinned and retention is 14 days.

**Exact-source Actions are not verified.** No PR-triggered workflow runs or combined statuses were returned for code head `f556769` or final handover head `4edbe552`. No expected RED/GREEN, hosted lock verification, artifact upload or clean-build result is claimed. The available GitHub connector does not expose workflow_dispatch. PHX-INFRA/repository administrator must dispatch `PHX Release ESP32 core compatibility` and `BlazePwifi build` for final PR #291 head `4edbe552`. No local execution of the new Python regression suite is claimed.

The workflow still preserves HARDWARE's existing pin `7da74f9d1768a42fc6c15be368eeddae29035d4f` / sketch blob `c07aba7d518ef7eb5d536aafdd77ef6193e676cb`. HARDWARE/MASTER must approve the canonical source SHA/blob before RELEASE refreshes them. No hardware source or sketch was changed.

PR #291 compares 871 commits ahead / 9 behind the live #242 head (merge base remains 734b89d9); it has 36 changed paths. The accumulated stack includes inherited non-RELEASE paths such as BlazePwifi project handovers/change ledger and SoftTimer PowerShell tests. Those paths were not edited in this activation. No rebase, retarget, force-push or merge was performed; MASTER owns stack reconciliation.

## Live control plane and provenance

- MASTER #288: OPEN / DRAFT; [OWNERSHIP_ROUTES.json](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/3b7198d1d1ddc1651f95bb8065253ba8e68ae46b/coordination/phoenix/OWNERSHIP_ROUTES.json) has 11 routes and remains DRAFT_REVIEW_ONLY. The explicit PHX-RELEASE route is only `.github/workflows/blazepwifi-build.yml` → `.github/workflows/pisowifi-ci.yml`, kind `reimplementation-review`; the new compatibility workflow/lock remain draft release work under the MASTER assignment, not a migration or merge.
- Cleanup-first #266: OPEN, 0/7 tracks complete; RELEASE track remains bounded to PR #242 build/version/manifest/signing configuration.
- PR #242 head: `a7e27fe50e13326a7258bbaed1388594141ddda3`; its UTC03 SoftTimer handover records no exact-head Actions for the publisher admission change.
- PR #291 remains OPEN / DRAFT / UNMERGED.
- COE #26 remains FROZEN with five queued workflows and zero jobs. COE #31 exact runs: shared/board validation [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) PASS (ESP32 and ESP8266 compile jobs PASS), case-collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) PASS, sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) FAIL at unprivileged Bubblewrap namespace preflight. COE #35: shared [#45742049762](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45742049762) FAIL at all-profile admission (ULA authority missing; board builds skipped), sandbox [#45742051077](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45742051077) FAIL because Bubblewrap is unavailable (namespace/package tests skipped), case-collision [#45742049684](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45742049684) PASS. No COE writes or subsystem changes.
- The actual private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered. Only an earlier checkpoint referencing v11 was surfaced; it was not substituted for the registry. No private contents or identifiers were copied into GitHub.

## Next owner actions

1. PHX-INFRA/repository administrator: dispatch both named workflows at exact PR #291 head `4edbe552`; record every job and artifact ID.
2. PHX-HARDWARE + PHX-MASTER: approve the canonical source commit and sketch blob.
3. PHX-MASTER: reconcile the nine-commit stale #291 base (870 commits ahead / 9 behind) without discarding child history.
4. PHX-QA: independently review the lock, verifier, tests, retained artifacts and cross-run comparison.
5. Registry custodian: restore authorized provenance-only access to the actual Drive v11 registry.

**PRODUCTION NO-GO:** protected signer, independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved target binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. No signing, publishing, hardware flashing, payment migration or customer deployment occurred.
