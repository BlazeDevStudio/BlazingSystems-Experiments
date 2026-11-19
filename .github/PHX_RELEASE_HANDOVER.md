# PHX-RELEASE UTC04 — Arduino CLI archive byte verification

**Checkpoint:** 2026-11-19 UTC04  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Draft:** [PR #291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base:** #242 at `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test HEAD:** `4cf10bbfe27f9fee8ba1248e132aca06b0a27a6c`  
**Disposition:** Arduino CLI archive and installed executable byte identity verified in exact-source CI; shared workflow remains blocked by the CORE-owned handover freshness gate. PRODUCTION NO-GO.

## Scope and ownership

This activation changed only release pipeline verification:

- `.github/scripts/verify_arduino_cli_archive.py` — new read-only archive verifier.
- `.github/scripts/test_arduino_cli_archive_verifier.py` — eight synthetic negative/positive controls.
- `.github/scripts/test_release_artifact_action_pins.py` — static guard for the verifier invocation and pinned release provenance.
- `.github/workflows/blazepwifi-build.yml` — run the verifier in both ESP build jobs and run the verifier unit suite in CI-0701.

No CORE handover, PISONET test, HARDWARE source, application source, network configuration, financial state, MASTER coordination file, signer, publisher permission or production artifact was changed. The existing PR contains inherited cross-role files; this activation did not edit those paths.

The MASTER #288 route manifest at `d26000d4498739f87bb99ef2037ddcf5020d8a99` marks the BlazePwifi build workflow as `reimplementation-review` to COE #26. The manifest remains `DRAFT_REVIEW_ONLY`; no workflow migration or destination copy was attempted.

## Finding

The pinned `arduino/setup-arduino-cli` action and explicit `version: "1.6.0"` input proved the reported CLI version, but did not independently verify the downloaded archive bytes or that the installed executable matched the upstream release asset.

GitHub release metadata for Arduino CLI v1.6.0 (published 2026-11-10) reports:

- Asset: `arduino-cli_1.6.0_Linux_64bit.tar.gz`
- Size: `20,111,675` bytes
- SHA-256: `321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250`
- Tag commit: `50a0e80da` (GitHub release page reports a verified signature)
- Release API `immutable=false`

The asset digest is GitHub release API metadata pinned in source. It is an integrity pin, not a detached Arduino publisher signature. The release's mutable status is preserved as a limitation.

## Implementation

The release-owned helper:

1. Downloads only the fixed v1.6.0 Linux x64 asset URL.
2. Requires the exact expected content length when supplied and exact archive byte count.
3. Verifies the pinned SHA-256 before parsing the archive.
4. Reads exactly one regular root `arduino-cli` tar member; it does not extract or execute archive contents.
5. Compares the installed executable bytes to that member using SHA-256.
6. Fails closed on download, size, digest, tar-member, file-type or installed-binary mismatch.

Both ESP32 and ESP8266 jobs invoke this check after setup and before installing their board core. Existing `arduino-cli version` checks remain and still require 1.6.0. The CI static guard requires both invocations and the pinned URL, size and digest.

## Test-first history

- Test-only commit: [`3eee751`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3eee751b05d8af02c7c0660e24883316cd931342).
- Expected RED: [push run #44457792353](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44457792353), exact test-only SHA `3eee751`; CI-0701 failed at the new suite because the verifier module was intentionally not yet present (`ModuleNotFoundError: verify_arduino_cli_archive`). The action-pin guard passed first.
- Source/test correction: [`4cf10bb`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4cf10bbfe27f9fee8ba1248e132aca06b0a27a6c).
- Exact-source CI-0701 ran the new suite: **8 tests PASS**, including digest mismatch, size mismatch, missing/duplicate/symlinked binary member, installed-binary mismatch and pinned-provenance controls. The existing external-action pin guard also passed.

## Exact-source GitHub Actions at `4cf10bb`

Primary exact-source push run: [#44458039847](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44458039847) — overall **FAILURE**, not green.

- CI-0701 action/toolchain/archive-verifier checks: **PASS**.
- New archive verifier suite: **8/8 PASS**.
- ESP32 compile/upload job: **PASS**.
- ESP8266 compile/upload job: **PASS**.
- All 11 OpenWrt firmware target jobs: **PASS**.
- Android job: **PASS**.
- Mandatory `validate`: **FAIL** at the CORE-owned handover freshness gate.
- Update-bundle and v0.4 simulation jobs: **SKIPPED** after validation failure.
- Production import, signing handoff and publication: **SKIPPED**.

Both ESP board logs report:

```text
RELEASE-ARDUINO-ARCHIVE-PASS:
size=20111675
archive_sha256=321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250
binary_sha256=5897b56f5eac106e60c902d6444f2923e918885aaeb119fc4b44ff9db5003ba8

arduino-cli Version: 1.6.0
Commit: 50a0e80da
Date: 2026-11-10T15:30:50Z
```

The same binary SHA-256 was observed in both board jobs. This proves the hosted CI installed executable matched the checksum-pinned archive member on those runs; it is not physical firmware acceptance.

PR run [#44458045764](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44458045764) at the same source SHA also passed CI-0701, ESP32 and ESP8266 jobs and the 11 target jobs; its Android job was still running at the last read. Its `validate` job failed at the same CORE handover freshness gate.

Windows run [#44458045708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44458045708): handover failed at the same CORE-owned freshness gate; Windows build and publisher were skipped. The earlier PISONET-owned StrictMode `$buildWorkflow` failure on #44440710823 is separate historical evidence and was not reached by this run.

The exact gate says source/workflow changes are newer than `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`; last checkpoint reported by the gate is `e241582890f7096c8e9807acd24b764a515632b7`. PHX-CORE/MASTER must update their own `PROJECT_HANDOVER.md`, `CURRENT_STATE.md` and `CHANGE_LEDGER.md`. PHX-RELEASE did not edit or bypass those files.

## Rollback and next owners

Rollback is limited to reverting the release-owned test-first and source commits on this draft branch; do not revert inherited CORE/PISONET work or rewrite shared handovers.

Next actions:

1. **PHX-CORE / PHX-MASTER:** refresh the CORE-owned BlazePwifi handover records after the workflow change and rerun exact-head validation.
2. **PHX-QA:** independently review the archive verifier, digest provenance, tar-member admission and installed-binary comparison.
3. **PHX-MASTER:** approve/reject the workflow reimplementation route before any cross-repository migration.
4. **PHX-RELEASE:** retain this verifier; do not repeat the completed Arduino CLI version-pin or archive-integrity task.

No real signer, release tag, publication, hardware flash, financial migration or customer deployment occurred. Physical 150 power-cut acceptance and 30-device/24-hour soak remain untested. **PRODUCTION NO-GO.**

## PHX-RELEASE UTC06 — exact-source ESP32 core compatibility matrix

**Task:** MASTER/HARDWARE handoff through issue #172, task `#172/#327`. **Status:** release-owned compatibility workflow fixed and exact-source CI verified on both requested ESP32 cores. PR #291 remains OPEN / DRAFT / UNMERGED. PRODUCTION NO-GO.

### Source identity and scope

- Experiments PR #291 branch: `phoenix/release-publisher-isolation-20261115`; base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`.
- Exact HARDWARE source commit: `0e5514adb0088649eca8bec9df6215faa50b556c`.
- Exact sketch: `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`, Git blob `c29483f0761ca6e2db0573bd12d6bfa502f12434`.
- Current HARDWARE PR #327 head at inspection: `4bb584b887dcff441686c7e26a057fcc5cb1d548`; its sketch path resolves to the same blob `c29483f0761ca6e2db0573bd12d6bfa502f12434`. No HARDWARE source was changed.
- The existing branch already contained the release-owned read-only 3.3.13/4.0.0 matrix workflow and static guard at head `b2b523dce7c994d4c8431ea3d7651990f4fb8493` (12 commits ahead of the handoff base `63f9952ce783a007546b09daa5ea4847f32fb505`). No duplicate workflow was created.

### Defect and test-first correction

The compatibility workflow compiled the exact sketch under both requested cores, but its final provenance marker used a doubled dollar before the GitHub matrix expression. After expression substitution, Bash treated `$3` or `$4` as a positional parameter under `set -u`, so both jobs failed after compilation.

- Test guard commit [`ba258377`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ba25837706f68864cf2bbb6d7b18a187ed173a0e) rejects the doubled-dollar expression and requires the matrix expression. Expected RED: [#44474437973](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44474437973), CI-0701 failed at the new guard with `build marker adds a second dollar before the matrix expression`; the defect was reproduced before the workflow correction.
- Source fix [`77dc879`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/77dc87956d0a782597945cb4aa7b98a9a89719ca) removed the extra dollar, leaving the matrix expression as a quoted literal after GitHub substitution.
- The first post-fix CI exposed a test-harness parser issue: the action-ref regex matched only `- uses:` but this workflow uses named steps with a following `uses:` key. That failure was in the new guard, not the build. Parser correction [`7688cb2`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7688cb25019b1045dd8f88ad335fe7fe0b5835cf) accepts both action YAML forms.
- Earlier exact-source run [#44473417412](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473417412) showed both core installs and compile commands succeeded, then each job failed only at the shell marker (`$4: unbound variable` for 4.0.0 and `$3: unbound variable` for 3.3.13).

### Final exact-source verification

**Source/test HEAD:** `7688cb25019b1045dd8f88ad335fe7fe0b5835cf`. **Docs-only successor before this release-handover update:** `8304fc66feb0bb3c8fffe63612432542b0eb795f`.

- Exact source/test compatibility run [#44474715198](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44474715198): **SUCCESS**, both matrix jobs completed.
- Docs-successor compatibility rerun [#44475241107](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44475241107): **SUCCESS**, both matrix jobs completed.
- Both runs checked out the exact source commit and verified sketch blob `c29483f0761ca6e2db0573bd12d6bfa502f12434`, installed Arduino CLI 1.6.0, verified the pinned archive (20,111,675 bytes; SHA-256 `321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250`), verified the requested core version and compiled the exact sketch.
- ESP32 core 3.3.13: compile PASS; program 1,042,632 bytes (79%); globals 49,952 bytes (15%); binary SHA-256 `fbcd0ee86cd2fa404128612a55ca8bb06d1ee2c7b8731fef1e20700663c3ee21`.
- ESP32 core 4.0.0: compile PASS; program 1,096,577 bytes (83%); globals 52,568 bytes (16%); binary SHA-256 `70b01ba160d3586e500589fb54e259161fe56ff07f0599862c97caa4992fade4`.
- Both jobs verified the installed Arduino CLI executable SHA-256 `5897b56f5eac106e60c902d6444f2923e918885aaeb119fc4b44ff9db5003ba8` against the pinned archive member.
- Main BlazePwifi source/test-head run [#44474715174](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44474715174): CI-0701 job `135392344823` PASS, including immutable-action pins, 8 Arduino archive-verifier tests, the ESP32 matrix guard, observed board-core pins and negative classifier contract. ESP32/ESP8266 compile-upload jobs and all 11 OpenWrt target jobs PASS. The overall run was CANCELLED after the mandatory validate job FAILED at the CORE-owned handover freshness gate; Android was cancelled and downstream simulations/update bundle/production import were skipped.
- After CORE updated its own handover records in separate commit `8304fc66`, docs-successor run [#44475241319](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44475241319) passed CI-0701, the mandatory handover freshness gate and the full `validate` job. ESP32 and ESP8266 compile/upload jobs and all 11 OpenWrt target jobs passed. Android was cancelled; most downstream simulations and update-bundle/publish/sign jobs were cancelled or skipped, while the Ruijie v0.4 simulation remained in progress at last read. The overall run was still in progress, not a completed Full acceptance, and no release was published.
- Windows run [#44475241122](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44475241122): handover freshness PASS; PISONET-owned `RELEASE-SIGN test fail-closed negative controls` FAILED; Windows build and publisher SKIPPED. PHX-RELEASE did not modify PISONET tests.

### Ownership, rollback and next actions

Only release-owned `.github/scripts/test_phx_release_esp32_core_compatibility.py`, `.github/workflows/phx-release-esp32-core-compatibility.yml`, and this release handover were changed for this task. The separate commit `8304fc66` changed CORE-owned `PROJECT_HANDOVER.md`, `CURRENT_STATE.md` and `CHANGE_LEDGER.md`; PHX-RELEASE did not edit those files. Their new UTC06 text still says the 4.0.0 leg is in progress, which is superseded by the successful docs-successor run #44475241107. PHX-CORE should reconcile its own records.

The workflow remains read-only (`contents: read`), uses immutable action commits, disables persisted checkout credentials, and does not upload, flash, sign or publish. Rollback is limited to reverting the release-owned test/fix commits on this draft branch; retain the prior compatibility workflow and HARDWARE source history. Do not revert inherited cross-role files.

Next actions: **PHX-QA** independently review both core compile results and the static guard; **PHX-CORE** update its own handover status and complete the still-running full validation; **PHX-PISONET** repair the Windows release-sign negative-control failure; **PHX-HARDWARE** owns any firmware compatibility change; **PHX-MASTER** refresh #172/#288 exact-head references and confirm the reimplementation-review route. Do not bypass ownership gates.

Canonical private Drive registry v11 remains unavailable through the authorized Library surface; older registry snapshots were not substituted and no private contents were copied.

**No merge, signing, release tag, publication, hardware flash, payment migration or customer deployment. Physical 150 power-cut and 30-device/24-hour soak evidence remains NOT TESTED. PRODUCTION NO-GO.**


## 2026-11-19 UTC08 — exact PR head/base SHA provenance

**Owner / scope:** PHX-RELEASE only. Existing draft PR #291 branch `phoenix/release-publisher-isolation-20261115`; base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER files were changed.

**Defect:** Prior `BUILD-PROVENANCE.json` recorded `GITHUB_SHA` (the PR merge checkout, e.g. `6096ab31bd0d31ac2cd50ced990734a3d5866517`) and branch names, but omitted the exact pull-request head and base commit SHAs. The artifact could not independently name both the candidate source head and its base.

**Test-first / implementation:**
- Test commit [`1d0d92f4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1d0d92f4e704096beaf977141912227a9384b0d4) added five regression checks for PR head/base fields, push identity, malformed/missing PR SHAs and workflow env wiring. Expected RED [#44486067782](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486067782): 16 tests ran; 4 failures and 2 errors exposed the missing fields/validation/wiring. The job failed at the intended regression.
- Source fix [`2dc56c91`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2dc56c91c44d03019cfa4071908b1575b3b3291e) validates exact 40-hex `PHX_SOURCE_HEAD_SHA` and, for PR events, exact `PHX_SOURCE_BASE_SHA`; push/dispatch source head must equal `GITHUB_SHA`. The manifest now distinguishes checkout `source.commit` from `source_head_sha` and `source_base_sha`.
- Workflow commit [`21fdedb4`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/21fdedb4c87e729bb31ba48f4a96d6036db7556d) exports `github.event.pull_request.head.sha || github.sha` and `github.event.pull_request.base.sha || ''` at workflow scope.
- Exact source/test HEAD: `21fdedb4c87e729bb31ba48f4a96d6036db7556d`.

**Exact-source CI:**
- PR build [#44486231372](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231372): CI-0701 job `135430268606` SUCCESS; 16 provenance tests and 8 Arduino CLI archive-verifier tests passed. ESP32, ESP8266, Android and all 11 OpenWrt target jobs completed SUCCESS. Overall workflow conclusion FAILURE solely because the mandatory CORE handover freshness gate failed in validate job `135430754580`; downstream update-bundle/simulation/publish jobs were skipped.
- Push build [#44486226486](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486226486): all 11 OpenWrt targets, ESP32, ESP8266 and Android SUCCESS; validate failed at the same CORE freshness gate; update-bundle and simulations skipped.
- ESP32 compatibility [#44486231288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231288): SUCCESS for core 3.3.13 and 4.0.0.
- Windows release [#44486231303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231303): FAILED at the same CORE freshness gate; Windows build and publisher skipped.

**Artifact readback:** Downloaded CI artifacts into an ephemeral inspection workspace only; no firmware or private artifact was copied into the repository. Parsed each `BUILD-PROVENANCE.json` and ran `sha256sum -c SHA256SUMS`; every listed entry passed.
- Ruijie artifact [ID 14511280783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231372/artifacts/14511280783): 5 checksum entries; `source_head_sha=21fdedb4...`, `source_base_sha=734b89d9...`.
- ESP32 artifact [ID 14510054456](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231372/artifacts/14510054456): 24 checksum entries; same exact head/base.
- ESP8266 artifact [ID 14510746699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231372/artifacts/14510746699): 10 checksum entries; same exact head/base.
- Orange Pi PC2 artifact [ID 14510632648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486231372/artifacts/14510632648): 5 checksum entries; same exact head/base.
- All four manifests classify artifacts as `CI_PREVIEW_ONLY`; `production_authorized=false`, signing NOT_PERFORMED, hardware acceptance NOT_TESTED and financial migration NOT_PERFORMED. The `source.commit` remains the exact GitHub merge-checkout commit; the new fields identify the PR head and base separately.

**Current cross-repository state:** MASTER #288 head `75319bb34a44cfa442f46d462664154b2926bb34`; route remains `reimplementation-review` / `DRAFT_REVIEW_ONLY`. Experiments #242 head `734b89d9`; #291 head `21fdedb4`. COE #26 head `b382d233` has five queued workflows; #31 head `59ed44d0` and #35 head `5047af8b` still fail mandatory sandbox because Bubblewrap is unavailable. Canonical private Drive registry v11 was not available through the authorized Library surface; older registry versions were not substituted.

**Blocker / next owner:** CORE's `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` freshness gate still cites checkpoint `dd62b3b468690fcfa3add9268d4ddd6842f3cc8a` and rejects the newer release script/workflow commits. PHX-CORE must update its own PROJECT_HANDOVER/CURRENT_STATE/CHANGE_LEDGER and rerun exact-head validation. PHX-RELEASE did not edit CORE-owned records or bypass the gate. PHX-QA should independently review the new provenance fields.

No merge, signing, tagging, publication, hardware flashing, payment migration or customer deployment occurred. Production remains NO-GO.

## 2026-11-19 UTC09 — reject symlinked provenance directory ancestors

**Owner / scope:** PHX-RELEASE only. Existing Experiments PR #291 branch `phoenix/release-publisher-isolation-20261115`, base PR #242 `734b89d9e7792247e8376335c3f3685500ab3f89`. Current source/test head before this documentation commit: `dbd31da279be4dcbb9fffb765c64ec70422c16af`. PR remains OPEN / DRAFT / UNMERGED. This task changed only `.github/scripts/test_build_provenance.py`, `.github/scripts/write_build_provenance.py`, and this release-owned handover. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER path was edited.

### Finding and bounded correction

`_require_directory()` previously used `lstat()` only on the final path component. A normal directory reached through a symlinked parent could therefore be admitted as an artifact root or ImageBuilder work directory. The provenance helper could inventory that redirected tree and write its manifest/checksum output there.

The helper now rejects parent traversal and checks each absolute directory component with `lstat()`, requiring every component to be a real directory. The same admission check protects both the artifact root and ImageBuilder work directory. This is a static path-component check at admission; it is not claimed as a race-free directory-descriptor sandbox or a replacement for the mandatory ImageBuilder sandbox.

### Test and correction history

- Initial regression commit [`f59f909`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f59f9095905b61fb08c84e4cf85b878795647638) added artifact-root and ImageBuilder-workdir symlinked-parent cases, but the methods were initially appended after the module's `__main__` guard. Run [#44495691007](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44495691007) ran the existing **16** provenance tests; it did **not** discover the two new cases. This was a test-authoring placement error, not a RED result.
- Registration correction [`3aacebc`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3aacebcaa9d19f17b7b0d788cabb567d4ea5f196) moved both tests inside `BuildProvenanceTests` before the main guard. A second test-only cleanup [`7d16459`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7d16459131265d444677db31519c47a28c51c1b7) removed an unreachable duplicate copy. Exact file readback now shows **18 registered tests**, including both new cases.
- The registration-corrected run [#44495882957](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44495882957) remained PENDING with no jobs returned at the last read. No expected RED is claimed.
- Source correction [`dbd31da`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dbd31da279be4dcbb9fffb765c64ec70422c16af) adds component-by-component directory admission and parent-traversal rejection.
- Exact source-head BlazePwifi run [#44496513759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44496513759) was QUEUED with no jobs returned at the last read. Compatibility run [#44496513841](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44496513841) was PENDING. The new source fix is **NOT YET CI-VERIFIED**.
- Separate Windows run [#44496513769](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44496513769): handover PASS; `build-windows` FAILED at PISONET-owned `RELEASE-SIGN test fail-closed negative controls`; publisher SKIPPED. No PISONET file was changed.
- Prior baseline at PR head `99bac64`, before this task, [#44491825954](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491825954) passed shared validation, 11 OpenWrt target jobs, ESP32/ESP8266, Android, update bundle and its completed v0.4 simulation jobs; signing and publishing were SKIPPED. That prior pass does not validate the new `dbd31da` change.

### Current cross-repository state and next action

- MASTER #288 HEAD `1decd7715c4bac46673f673c49f27bfeca160a4e`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and the BlazePwifi workflow route remains `reimplementation-review` to COE #26. No migration or destination copy was attempted.
- Experiments #242 HEAD `734b89d9`; #291 now carries this release work. COE #26 HEAD `b382d233` still has five queued workflows with no combined acceptance.
- COE #31 HEAD `59ed44d0` and child #35 HEAD `5047af8b` remain open drafts. Their mandatory ImageBuilder sandbox runs fail closed because Bubblewrap is unavailable; no sandbox packaging regression pass is claimed.
- Canonical private Drive project registry v11 was not surfaced by the authorized Library search. No older snapshot was substituted or copied.
- **Next:** PHX-RELEASE must re-read the live #291 head and inspect [#44496513759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44496513759). Require the two new regressions to be discovered and pass on the exact source head before marking this task verified; if the workflow remains queued, PHX-INFRA/repository administration must resolve the Actions queue. PHX-PISONET owns the separate Windows negative-control failure. PHX-QA should independently review path admission.

No merge, signing, tag, publication, hardware flash, financial migration or customer deployment occurred. Physical 150 power-cut and 30-device/24-hour soak evidence remains NOT TESTED. **PRODUCTION NO-GO.**



## 2026-11-19 UTC09 — protect active OpenWrt publication runs from push cancellation

**Owner / scope:** PHX-RELEASE only. Existing Experiments draft PR #291 branch `phoenix/release-publisher-isolation-20261115`, base PR #242 `734b89d9e7792247e8376335c3f3685500ab3f89`. Source/test head: `cd545fe527c3b52ad251528706f744e9a5672241`. Current PR head before this handover update: `9b26671efe6138bb4dfe14c10db520902dff6cb8`. Only `.github/scripts/test_release_workflow_concurrency.py`, `.github/workflows/blazepwifi-build.yml`, and this release-owned handover were changed for this task. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was edited.

### Finding and bounded correction

The workflow-level concurrency group uses `${{ github.workflow }}-${{ github.ref }}`, but `cancel-in-progress: true` applied to every event. A newer push or manual dispatch on the same ref could therefore cancel a running workflow while a write-privileged import or publisher job was active. The workflow has four `contents: write` jobs: `production_import_signed_apk`, `publish_prerelease`, `publish_release`, and `publish_v060_lab_preview`.

The release-owned workflow now uses:

```yaml
cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Only superseded PR validation runs remain cancellable. Push and workflow-dispatch runs are preserved. Existing branch and commit-marker conditions, permissions, artifact assembly, signer and publisher steps were not changed. This is a workflow-policy correction; no live release/publisher job was executed.

### Test-first history

- Test-only commit [`8512bc9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8512bc9079c203450645e054d76cec7044706b96) added the concurrency regression and wired it into CI-0701 while leaving the old `true` setting in place. Expected RED was reproduced in both [push #44499334413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44499334413) and [PR #44499348565](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44499348565): the new push/dispatch cancellation assertion failed against the old setting; the existing publisher branch-gate assertion passed. Downstream build jobs were skipped after CI-0701 failed.
- Workflow fix [`43de5d0`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/43de5d0d2d8630586729e81a1ae455a951da2b43) restricts cancellation to `pull_request` events.
- Test coverage expansion [`cd545fe`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/cd545fe527c3b52ad251528706f744e9a5672241) verifies all four write-privileged jobs retain their explicit branch and commit-marker gates.

### Exact-source and docs-successor CI

- Exact source/test push [#44499983485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44499983485), head `cd545fe527c3b52ad251528706f744e9a5672241`: CI-0701 **PASS**, including both concurrency tests and the existing release action/provenance/archive/toolchain guards. ESP32, ESP8266, Android and all 11 OpenWrt target jobs **PASS**. Mandatory `validate` **FAILED** at the CORE-owned freshness gate; it reported checkpoint `347251769a65b51744142f12fa0ff74e08d1f188`. Update-bundle, v0.4 simulations, signing and publishing were skipped. Overall run conclusion: FAILURE due to that freshness gate, not the concurrency guard or build matrix.
- The exact-head PR run [#44499994944](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44499994944) was cancelled after a docs-only successor advanced the PR. This is expected PR-only cancellation under the new policy. The push run above was not cancelled and completed.
- CORE then advanced its own `PROJECT_HANDOVER.md`, `CURRENT_STATE.md` and `CHANGE_LEDGER.md` in three documentation commits after `cd545fe`; PHX-RELEASE did not edit those paths. Current docs successor PR head is `9b26671efe6138bb4dfe14c10db520902dff6cb8`. Docs-successor [PR run #44500190019](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500190019): CI-0701, mandatory freshness, full `validate`, ESP32, ESP8266, Android and all 11 OpenWrt target jobs **PASS**; update bundle, Android emulator, browser, ESP32/ESP8266, Ruijie and Orange Pi simulations **PASS**. The v0.4 x86 simulation was still in progress at the last read. Production sign handoff and both publisher jobs were **SKIPPED**; the overall run was not yet terminal.
- Windows [#44500190062](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500190062): CORE handover **PASS**; PISONET-owned `negative-selftest.ps1` failed because `$buildWorkflow` was unset; Windows build failed and publisher was skipped. No PISONET file was changed.
- The independent ESP32 compatibility run [#44500189960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500189960) passed both scoped core legs, but it still identifies the older HARDWARE source `0e5514adb008`; do not treat it as current #327 source acceptance.

### Cross-repository state and next owners

- MASTER draft PR #288 head `1decd7715c4bac46673f673c49f27bfeca160a4e`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and the release route remains `reimplementation-review`. No migration or destination copy was attempted.
- Experiments #242 base/head `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 current docs head `9b26671efe6138bb4dfe14c10db520902dff6cb8`.
- COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`: five PR workflows remain QUEUED with zero jobs; no integration acceptance.
- COE #31 head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`: sandbox run [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap but failed closed because the unprivileged UID map was denied (`bwrap: setting up uid map: Permission denied`, exit 125).
- COE #35 head `5047af8b5a8296e06294bbda6bf42a6baea2294d`: sandbox run [#44465377807](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377807) failed closed because Bubblewrap was not installed (exit 125). Shared-contract and case-collision jobs passed on both #31 and #35.
- Canonical private Drive project registry v11 was not surfaced by the authorized Library search. A historical checkpoint mentioning v11 is not the canonical registry and was not used; no private contents were copied.
- Branch-protection endpoint returned 403 to this integration; visible repository rulesets query returned an empty list. Protected branch admission therefore remains unverified here.

**Next actions:** PHX-CORE should reconcile its own handover entries to the terminal docs-successor run #44500190019; PHX-QA should independently review the concurrency guard; PHX-MASTER should confirm the release reimplementation route. PHX-PISONET owns the unset `$buildWorkflow` negative-selftest failure. PHX-INFRA/repository administration owns the Bubblewrap namespace runner gap. Do not bypass these gates.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. Physical 150 power-cut and 30-device/24-hour soak evidence remains NOT TESTED. **PRODUCTION NO-GO.**


### UTC09 terminal validation update — handover-head push #44501500375

The handover-head push run [#44501500375](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501500375), exact docs head `82a7e7e9226b0a267750ca3caef638e9afd0c6f6`, has now completed its primary validation/build jobs:

- CI-0701: **PASS** (includes the 2 release concurrency tests and existing release action/provenance/archive/toolchain guards).
- Mandatory handover freshness and full `validate`: **PASS**.
- ESP32, ESP8266 and Android: **PASS**.
- All 11 OpenWrt target builds: **PASS**.
- Update bundle: **PASS**.
- v0.4 Ruijie simulation: **PASS**.
- v0.4 Android emulator, browser, x86, ESP32/ESP8266 and Orange Pi simulations: still **IN_PROGRESS** at this read.
- Production sign handoff, prerelease publisher and release publisher: **SKIPPED**.

The source/test head remains `cd545fe527c3b52ad251528706f744e9a5672241`; this run validates its docs successor and the release handover. The overall Actions run is still IN_PROGRESS because the listed v0.4 simulations have not all reached terminal results. No signing or publication occurred.


---

## PHX-RELEASE UTC10 — provenance payload snapshot consistency

**Task:** Prevent a successful artifact admission when payload bytes change after the first verified inventory but before the final checksum manifest is written.

**Repository / draft:** `BlazeDevStudio/BlazingSystems-Experiments`, PR [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), OPEN / DRAFT / UNMERGED.  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base PR #242:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test HEAD:** `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`  
**Scope:** `.github/scripts/test_build_provenance.py`, `.github/scripts/write_build_provenance.py`, this release-owned handover only. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source/handovers were modified.

### Defect and correction

Before this change, `write_provenance()` verified the initial artifact inventory against the existing `SHA256SUMS`, wrote `BUILD-PROVENANCE.json` using that initial inventory, then re-inventoried the directory and rewrote `SHA256SUMS` from the later inventory without requiring the payload entries to remain identical. A payload mutation in that interval could therefore be blessed by the new checksum file while the provenance manifest retained the earlier file digest.

The source now:
1. Re-inventories after writing the provenance file.
2. Removes only the newly generated `BUILD-PROVENANCE.json` entry from that comparison.
3. Requires every original payload path, size and SHA-256 to match the initial verified inventory.
4. Fails closed before rewriting `SHA256SUMS` if payload bytes drift.
5. Re-inventories again after checksum writing and refuses success if the artifact tree changed during that write.

A failed admission leaves the original `SHA256SUMS` untouched; the incomplete preview is not admitted for upload.

### Test-first history

- Regression-only commit: [`c2e95ce2`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c2e95ce2e4267754b8befb102e6ce90ad5541f49).
- Expected RED push [#44503641063](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503641063) and PR [#44503653635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503653635): CI-0701 reached the new regression; **18 existing provenance tests passed and the new mutation test failed exactly because `ProvenanceError not raised`**. Action-pin and concurrency guards passed. Downstream jobs were skipped after CI-0701 failed.
- Source correction: [`ffe4ea8f`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf).

### Exact-source GitHub Actions

Push run [#44503860587](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587), exact source/test HEAD `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`:

- CI-0701: **PASS**; provenance suite **19/19 PASS**, including the new payload-drift regression.
- Mandatory CORE handover freshness and full `validate`: **PASS** (all 133 job steps completed successfully).
- ESP32 and ESP8266 compile/provenance/upload: **PASS**.
- Android build: **PASS**.
- All 11 OpenWrt firmware target jobs, including optional target variants: **PASS**.
- Update bundle: **PASS**.
- Completed v0.4 simulations at last read: Ruijie, ESP32, ESP8266, browser and Orange Pi PC/One/Zero3: **PASS**.
- v0.4 x86 and Android-emulator simulations: **IN_PROGRESS** at last read; overall Actions run remains **IN_PROGRESS**, not terminal SUCCESS.
- Production import, production sign handoff, prerelease publisher and release publisher: **SKIPPED**.

The PR-event build [#44503871218](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503871218) was still queued/in progress at the last read; the push run above is the exact-source evidence used for this task.

### Actual artifact readback

Downloaded three artifacts from push run #44503860587 and independently inspected their ZIP contents. For each, every `SHA256SUMS` entry matched the actual ZIP member bytes, every manifest file SHA-256 and size matched the actual payload, the checksum set exactly covered payload plus `BUILD-PROVENANCE.json`, and the source commit was the exact tested HEAD `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`.

- ESP8266 artifact [14518906459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14518906459): 9 manifest payload files / 10 checksum entries — **PASS**.
- ESP32 artifact [14518526948](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14518526948): 23 manifest payload files / 24 checksum entries — **PASS**.
- Ruijie artifact [14519345289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503860587/artifacts/14519345289): 4 manifest payload files / 5 checksum entries — **PASS**.

All three manifests classify the outputs as `CI_PREVIEW_ONLY`, with `production_authorized=false`, `signing=NOT_PERFORMED`, and `hardware_acceptance=NOT_TESTED`. These are CI preview artifacts, not production binaries or physical-device acceptance.

### Separate cross-owner failure and live routing

Windows run [#44503871056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503871056): shared handover **PASS**; Windows build **FAIL** at PISONET-owned `RELEASE-SIGN test fail-closed negative controls` because `$buildWorkflow` was unset; publisher **SKIPPED**. PHX-RELEASE did not edit the PISONET test path.

MASTER PR #288 current route manifest remains `DRAFT_REVIEW_ONLY`; `.github/workflows/blazepwifi-build.yml` remains `reimplementation-review` to COE #26. No migration or destination copy was attempted. COE #26 remains five queued workflows / zero executed jobs. COE #31 sandbox remains blocked by hosted unprivileged UID-map denial; child #35 sandbox remains blocked by missing Bubblewrap on its runner. Canonical private Drive registry v11 remains unavailable through the authorized Library surface; no older registry snapshot was substituted or copied.

### Next actions / rollback

1. **PHX-QA:** independently review the payload snapshot equality check and artifact admission behavior at exact source HEAD.
2. **PHX-MASTER:** confirm the workflow reimplementation route and preserve the review-only migration boundary.
3. **PHX-PISONET:** repair the unset `$buildWorkflow` negative-selftest variable in its own source/test ownership.
4. **PHX-INFRA:** provide an approved disposable Bubblewrap-capable runner with unprivileged namespaces for COE #31/#35.
5. **PHX-RELEASE:** retain the snapshot-consistency fix; do not repeat it. Re-read exact source/test and docs heads before further work.

Rollback is limited to reverting this activation's source correction `ffe4ea8f` and its test-first commit `c2e95ce2` in reverse order on the existing draft branch. Do not revert inherited CORE/PISONET files or rewrite their handovers.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. Physical 150 power-cut acceptance and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC11 — Windows build token-scope isolation

**Date:** 2026-11-19 UTC11  
**Repository / draft:** `BlazeDevStudio/BlazingSystems-Experiments`, [PR #291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), OPEN / DRAFT / UNMERGED.  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base:** PR #242 at `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Exact source/test HEAD:** `6ce1ee152d49de330ed0f31c3786799284545474`  
**Release workflow source commit:** `a2e3a816e2074448a38df645d6b105978f283a28`  
**Disposition:** Explicit job-level read-only token scope is implemented and its static guard passes exact-source CI. Full validation remains blocked by the CORE-owned handover freshness gate. PRODUCTION NO-GO.

### Finding and bounded correction

The Windows release workflow already declared workflow-level `permissions: contents: read` and granted `contents: write` only to the separately gated `publish-release` job. The candidate-producing `build-windows` job nevertheless inherited its read-only scope from the workflow default rather than declaring its own job-level boundary. A future workflow-level permission expansion could therefore broaden the job that handles candidate binaries and signing inputs.

The release-owned workflow now declares:

```yaml
  build-windows:
    needs: handover
    runs-on: windows-latest
    permissions:
      contents: read
```

The only `contents: write` grant remains in `publish-release`, whose job condition still requires a push to protected `main`, `SOFTTIMER_RELEASE_APPROVED == 'true'`, and the validated `future_release_eligible == 'true'` output. No signing secret, publisher condition, PISONET source/test file, or application code was changed.

### Test-first history

- Initial guard/test commit: [`a9b72e5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a9b72e57862471314f26f84287e6c664f41cbbb8).
- Test matcher/escaping correction: [`8e91812`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8e91812002ae2eb9df0c707db21571fe1c75a67b).
- Expected RED: [PR run #44516441755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516441755), exact test-only head `8e91812`. The new assertion failed because `build-windows` lacked its own `contents: read` declaration; the two existing concurrency/branch-gate tests passed. This is the reproduced permission-scope gap.
- Workflow correction: [`a2e3a81`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a2e3a816e2074448a38df645d6b105978f283a28).
- Test assertion indentation correction: [`6ce1ee1`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6ce1ee152d49de330ed0f31c3786799284545474). This was test-harness-only; it aligned the expected YAML indentation with the actual job block and did not change workflow behavior.

### Exact-source GitHub Actions

[Push run #44516909992](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516909992), source/test HEAD `6ce1ee152d49de330ed0f31c3786799284545474`:

- CI-0701 job `135535170502`: **SUCCESS**.
- External action pin guard: **PASS** for all three release workflows (52 BlazePwifi, 3 ESP32 compatibility, 6 Windows release invocations).
- Release concurrency/token-scope tests: **3/3 PASS**, including explicit Windows build read-only permission, single publisher write grant, and protected-main/approval/output gate.
- Build provenance tests: **20/20 PASS**.
- Arduino CLI archive verifier tests: **8/8 PASS**.
- The exact-source push run later completed with overall **FAILURE** because the mandatory `validate` job failed at the CORE-owned handover freshness gate. CI-0701, Android, ESP32, ESP8266 and all **14 platform/firmware target jobs** completed **SUCCESS**; update bundle, all v0.4 simulations/candidate validation, production import, signing handoff and publishers were **SKIPPED** after the gate. No terminal overall SUCCESS is claimed. Windows docs-head run [#44517414407](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44517414407) also failed at the same freshness gate; Windows build and publisher were skipped.

Full `validate` job `135535252602` **FAILED** at the mandatory handover freshness gate:

```text
handover gate: source/workflow changes newer than
experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md
handover gate: last checkpoint commit
ed15cee698382e1fbc980adb3ac7f5aa8858971d
```

This gate is CORE-owned. PHX-RELEASE did not edit `PROJECT_HANDOVER.md`, `CURRENT_STATE.md`, or `CHANGE_LEDGER.md`.

Windows release run [#44516576226](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516576226) at workflow source commit `a2e3a81` also failed at the same freshness gate; `build-windows` and `publish-release` were **SKIPPED**. Thus the new permission boundary is statically verified in CI, but the Windows build job has not executed on this head. No Windows artifact or publisher result is claimed.

### Other live dependencies and next owners

- MASTER PR #288 remains OPEN / DRAFT; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. The BlazePwifi workflow route remains `reimplementation-review` to COE #26.
- COE #26 remains five queued PR workflows with zero jobs; no integration acceptance.
- COE #31 sandbox remains failed closed at unprivileged UID-map setup (run [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263)); no privileged or unsandboxed fallback.
- The canonical private Drive project registry v11 was not retrievable. The accessible Library `BLAZE_PROJECT_REGISTRY.json` is an older 2026-10-26 schema 1.0 snapshot, not v11; it was not substituted as current provenance and no private contents or identifiers were copied into GitHub.

**Next:** PHX-CORE/MASTER refresh their own authoritative handover records after this workflow source change, then PHX-RELEASE reruns the exact-head Windows workflow. PHX-QA independently reviews the job permission isolation. PHX-MASTER continues the release workflow migration review.

No merge, signing with real keys, release tag, publication, hardware flash, payment migration or customer deployment occurred. Physical 150 power-cut acceptance and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC12 — exact Windows .NET SDK selection

**Disposition:** release-owned workflow/test correction committed; static CI guard passes; actual Windows build is blocked before the SDK step by the CORE-owned handover freshness gate. PR #291 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Verified defect

At exact pre-fix PR head `af144e2c44c2a66959dd0ce088694c08ab415639`, Windows run [#44519155116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44519155116) installed .NET SDK `8.0.425` via setup-dotnet, but the subsequent `dotnet --version` selected `8.0.427`. The workflow's generated `global.json` used `rollForward: latestPatch`, so the configured SDK was not exact.

### Test-first history and implementation

- Test-first commit [`96ee6d4d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/96ee6d4dab7739ea20a9fd74b0fb067cfb6cc7c5) introduced `test_windows_sdk_is_exactly_pinned_and_verified`.
- Initial test step extraction was itself incorrect and failed at the parser assertion in [#44522980589](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44522980589); this was a test-harness failure, not evidence about the SDK fix.
- Step-boundary parser corrections: [`4c05e609`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4c05e609579f81ba220d88eab1603d41a534bd57) and [`f4e26486`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f4e26486a356ab28882f05e168930c164dcc84e2).
- Expected RED [#44523235222](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44523235222): the new assertion failed exactly because `rollForward` was `latestPatch`, not `disable`; the three existing release workflow tests passed.
- Workflow fix [`c8515191`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c851519136d299183d61c1b56836b68cd3e92561): changes global.json to `rollForward: disable`, captures `dotnet --version`, fails unless the selected version is exactly `8.0.425`, and emits `RELEASE-DOTNET-SDK-PASS` only after the check.
- The first post-fix test run [#44523353689](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44523353689) exposed an overly specific assertion expecting a combined PowerShell condition; the implementation correctly uses separate exit-code and version checks. Test assertion correction [`49682d01`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/49682d014d02b52cee34a419bb5e172c9d38d825) now checks both fail-closed conditions independently.

### Exact-source CI and current blocker

- Final source/test HEAD: `49682d014d02b52cee34a419bb5e172c9d38d825`.
- Push run [#44523478193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44523478193): CI-0701 completed SUCCESS; the four release concurrency/permission/SDK guard tests passed. Remaining full matrix jobs were still queued or running at the last read; no overall run conclusion is claimed.
- PR run [#44523487472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44523487472): CI-0701 completed SUCCESS; the same four tests passed. Full build jobs remained in progress at the last read.
- Windows PR run [#44523487584](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44523487584): **handover job FAILED before build-windows**. The gate reports `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` is older than `.github/workflows/blazepisonet-softtimer-release.yml`; last checkpoint `261139934215ded167c9e3a676b2fb7c8140c90e`. `build-windows` and `publish-release` were SKIPPED. The fixed SDK runtime check therefore has **not yet executed** on this head.

### Scope and owner actions

Only release-owned files changed in this UTC12 task:
- `.github/scripts/test_release_workflow_concurrency.py`
- `.github/workflows/blazepisonet-softtimer-release.yml`

No PISONET product code or tests, CORE handover, financial logic, signer credentials, hardware source, shared interface or MASTER coordination file was edited.

**PHX-CORE / PHX-MASTER:** refresh their own authoritative handover records after the release workflow change, then request an exact-head Windows rerun. **PHX-QA:** independently review exact SDK selection and workflow fail-closed behavior. PHX-RELEASE must not bypass the freshness gate or edit CORE-owned records.

No real signing, publisher execution, release tag, publication, hardware flash, financial migration or customer deployment occurred. This correction is CI/static-guard evidence only until the Windows SDK step executes. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC13 — exact-current Hardware #327 ESP32 compatibility pin

**Date:** 2026-11-19 UTC13  
**PR:** [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), OPEN / DRAFT / UNMERGED / PRODUCTION NO-GO.  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base PR #242:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Release source/test HEAD:** `69619210865259918ed74e081427ba960539af7a`  
**Scope changed in this task:** `.github/scripts/test_phx_release_esp32_core_compatibility.py`, `.github/workflows/phx-release-esp32-core-compatibility.yml`, and this release-owned handover only.

### Verified stale-source defect and correction

The compatibility workflow previously passed both ESP32 cores only against historical PHX-HARDWARE commit `0e5514adb0088649eca8bec9df6215faa50b556c` and sketch blob `c29483f0761ca6e2db0573bd12d6bfa502f12434`. That did not qualify the live Hardware PR #327 candidate.

At task start, live PR #327 API head was `984ea8ff65a93b7da6e22fc2e1943acaf56100ca`; the exact ESP32 sketch blob read from that commit was `528187f68aaad7d76a690bbf1cbe338165ad3839`. The test now requires those exact values, and the release workflow checks out that immutable commit, independently asserts the same source SHA and sketch blob, and labels both core jobs with the pinned source prefix.

- Test-first commit: [`01642aa`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/01642aa3613406277c279ed778c31ec91d10fe57).
- Expected RED: [BlazePwifi run #44531336928](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531336928), job `135585148690`, step `RELEASE-TOOLCHAIN exact ESP32 core compatibility workflow contract`: **FAILED as intended** because the unchanged workflow lacked the newly required #327 source SHA and sketch blob. The 20 provenance tests and 8 Arduino CLI archive-verifier tests passed; the downstream compatibility-contract step was the specific failure.
- Workflow fix: [`6961921`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/69619210865259918ed74e081427ba960539af7a).
- The test and workflow still use immutable action pins, read-only permissions, disabled persisted credentials, and no upload/sign/publish operation.

### Exact-source CI status at handover update

- [Compatibility matrix #44531465685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531465685), exact release source/test HEAD `6961921`: both jobs are **IN PROGRESS**. For both ESP32 core 3.3.13 and 4.0.0, checkout of the exact pinned Hardware commit, sketch-blob assertion, Arduino CLI archive-byte verifier, and exact core installation have **PASSED**; the actual sketch compile step is still running. No compile PASS is claimed yet.
- [BlazePwifi build #44531465762](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531465762): CI-0701 release guard **SUCCESS**; ESP32 and ESP8266 build/artifact jobs **SUCCESS**; full `validate` was still **IN PROGRESS** at this read. No overall run conclusion is claimed.
- [Windows release #44531465730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531465730): shared handover **SUCCESS**; .NET 8 SDK pin step **SUCCESS**; Windows job **FAILURE** in the PISONET-owned `tests/ReleaseSigning/negative-selftest.ps1` because `$buildWorkflow` is unset; publisher **SKIPPED**. PHX-RELEASE did not edit PISONET files.
- Earlier docs-head Windows run [#44527914604](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44527914604) independently logged `RELEASE-DOTNET-SDK-PASS: 8.0.425`; the current Windows failure is not the SDK pin.

### Live cross-role state and limitations

- During this activation, Hardware PR #327 advanced from pinned commit `984ea8ff` to current PR API head `dc264660942612d577e9eef4e2f6536bb4671bd1`. Exact compare shows the only intervening change is `.github/workflows/phx-hardware-quarantine-byte-readback.yml`; the ESP32 sketch blob remains `528187f68aaad7d76a690bbf1cbe338165ad3839`. Thus the compatibility run tests the same exact sketch bytes as current #327, but is pinned to the earlier immutable PR snapshot, not the later Hardware workflow tree.
- Current #327 Full build [#44531136753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136753) **FAILS** at QA-owned `Controller protocol parity` / Missing poll signature check; all 13 firmware/platform target jobs, ESP32, ESP8266 and Android **PASS**; downstream simulations, signing and publishing **SKIPPED**. Focused quarantine [#44531136592](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136592) and relay/output [#44531136572](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531136572) **PASS**. These are CI/source-extracted results, not physical acceptance.
- MASTER #288 remains OPEN/DRAFT at `d52d346e51d135615833f4f843204b36e0f78a99`; `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; the release workflow route remains `reimplementation-review`. No source/destination migration or route promotion occurred.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; exact-head Windows run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) has handover/build **SUCCESS**.
- COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five PR workflows remain **QUEUED** with no jobs returned.
- COE #31 remains OPEN/DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Shared/hardware and case-collision runs [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) / [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) **SUCCESS**. Mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) **FAILED CLOSED** after host tests passed: `bwrap: setting up uid map: Permission denied`; package regressions were skipped, no privileged or unsandboxed fallback.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the authorized Library/connector surface. Older v7 and other snapshots were not substituted; no private contents or identifiers were copied to GitHub.

### Next owner actions

1. **PHX-RELEASE:** record terminal status of #44531465685 at the next activation; if either exact-core compile fails, preserve the log and correct only the release-owned compatibility workflow/test.
2. **PHX-PISONET:** fix the uninitialized `$buildWorkflow` in its own negative self-test; RELEASE must not edit it.
3. **PHX-QA:** independently review the current #327 deny-only poll fixture and the exact-source compatibility evidence.
4. **PHX-HARDWARE:** reconcile its latest #327 workflow/lab state; do not treat focused lab PASS as Full validation.
5. **PHX-INFRA:** provide an approved disposable Bubblewrap runner with unprivileged UID namespaces for COE #31.

No merge, real-key signing, release tag, publication, hardware flashing, financial migration, customer deployment or production approval occurred. Physical 150-power-cut acceptance and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO.**
