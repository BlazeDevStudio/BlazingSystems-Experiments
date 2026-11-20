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

- [Compatibility matrix #44531465685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531465685), exact release source/test HEAD `69619210865259918ed74e081427ba960539af7a`: **COMPLETED SUCCESS**. Both jobs verified Hardware commit `984ea8ff65a93b7da6e22fc2e1943acaf56100ca`, ESP32 sketch blob `528187f68aaad7d76a690bbf1cbe338165ad3839`, Arduino CLI archive size `20,111,675` and SHA-256 `321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250`, and installed CLI binary SHA-256 `5897b56f5eac106e60c902d6444f2923e918885aaeb119fc4b44ff9db5003ba8`. Core 3.3.13 compile **PASS**: program `1,042,228` bytes (79%), globals `49,952` bytes (15%), binary SHA-256 `1bcd57524d9059ed4c45f12d3b6e836d016b416386cd1ea250de6bf079645926`. Core 4.0.0 compile **PASS**: program `1,096,177` bytes (83%), globals `52,568` bytes (16%), binary SHA-256 `70b01ba160d3586e500589fb54e259161fe56ff07f0599862c97caa4992fade4`. These are hosted CI compile outputs only, not physical hardware acceptance.
- [BlazePwifi build #44531465762](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44531465762): CI-0701 release guard, full `validate`, ESP32 and ESP8266 jobs **SUCCESS**. The overall run was later **CANCELLED** by the documentation-only successor; job summary: 16 SUCCESS, 10 CANCELLED, 4 SKIPPED. Do not call the overall run successful.
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

1. **PHX-RELEASE:** at the next activation inspect documentation-head runs queued after this handover commit; do not duplicate the completed exact-source matrix unless the pinned hardware source/sketch blob changes.
2. **PHX-PISONET:** fix the uninitialized `$buildWorkflow` in its own negative self-test; RELEASE must not edit it.
3. **PHX-QA:** independently review the current #327 deny-only poll fixture and the exact-source compatibility evidence.
4. **PHX-HARDWARE:** reconcile its latest #327 workflow/lab state; do not treat focused lab PASS as Full validation.
5. **PHX-INFRA:** provide an approved disposable Bubblewrap runner with unprivileged UID namespaces for COE #31.

No merge, real-key signing, release tag, publication, hardware flashing, financial migration, customer deployment or production approval occurred. Physical 150-power-cut acceptance and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO.**


## UTC15 exact-source provenance directory race hardening — 2026-11-19T15:31:29.609Z

### Release-owned defect and correction
The artifact admission path validated the artifact directory by pathname, then later created `BUILD-PROVENANCE.json` and rewrote `SHA256SUMS` with pathname-based temporary files and replacement. A parent-directory swap to a symlink after admission could redirect the provenance write outside the originally admitted artifact directory.

A deterministic test now reproduces that race by replacing the artifact parent after source metadata collection. Before the fix, the test observed an unexpected `BUILD-PROVENANCE.json` in the external directory.

The corrected implementation:
- Opens every artifact-root path component with `O_DIRECTORY | O_NOFOLLOW` and retains the admitted directory descriptor.
- Inventories nested directories and hashes/reads regular files relative to pinned directory descriptors; symlinks and special entries fail closed.
- Rechecks that the public artifact path still resolves to the same device/inode as the admitted directory.
- Creates the provenance sidecar relative to the pinned descriptor and publishes it with descriptor-relative atomic create-if-absent linking.
- Rewrites `SHA256SUMS` with descriptor-relative temporary creation and `os.replace`, then fsyncs the pinned directory.
- Refuses admission when required descriptor-relative/no-follow operations are unavailable.

No manifest schema, source identity fields, artifact classification, signer, firmware source, or production authorization was changed.

### Test-first and implementation commits
- Regression test: [`eeeccda8310487163f9b9c616c4c8b9fa6e24a4c`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/eeeccda8310487163f9b9c616c4c8b9fa6e24a4c).
- Expected RED: [Actions #44553821583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44553821583), job `135664363343`. Existing 20 provenance tests passed; the new test failed because the external directory received `BUILD-PROVENANCE.json`.
- Source correction: [`9631bdc9e17c029f806eccf7c5f6a3482baa3bd6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9631bdc9e17c029f806eccf7c5f6a3482baa3bd6).
- Existing payload-mutation test adapter updated for descriptor-relative writer: [`60325634e8359e22c7708403632244d3e876ef0b`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/60325634e8359e22c7708403632244d3e876ef0b).
- Exact source/test HEAD: `60325634e8359e22c7708403632244d3e876ef0b`.

### Exact-source GitHub Actions
- [BlazePwifi build #44554209399](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44554209399): **SUCCESS**. CI-0701 job `135665772770` passed; provenance 21/21; release workflow concurrency 4/4; Arduino archive verifier 8/8; full `validate` passed; all 14 OpenWrt target jobs passed; ESP32 and ESP8266 builds passed; Android build passed; update bundle passed; all nine v0.4 simulations passed. Production signing and release publishers were skipped.
- [ESP32 compatibility #44554209602](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44554209602): **SUCCESS** for both ESP32 core 3.3.13 and 4.0.0, pinned to HARDWARE commit `984ea8ff65a93b7da6e22fc2e1943acaf56100ca` and sketch blob `528187f68aaad7d76a690bbf1cbe338165ad3839`. This is hosted compilation, not physical-board acceptance.
- [Windows release #44554209402](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44554209402): **FAILURE** in PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is uninitialized. Exact .NET SDK assertion passed (`8.0.425`); package parity self-test passed; Windows publisher skipped. PHX-RELEASE did not modify PISONET.
- No full CI conclusion is inferred from a job-only pass; the listed run conclusions above are from the live run records.

### Live ownership and provenance reconciliation
- Experiments PR #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; PR #291 remains OPEN/DRAFT on the existing release branch. Source/test HEAD is `60325634e8359e22c7708403632244d3e876ef0b`; this handover commit becomes the documentation head.
- MASTER PR #288 is OPEN/DRAFT at `7f3ccbc3278c8f86b745bb4c8aecc3b8623da58b`. Routing remains `DRAFT_REVIEW_ONLY`; release workflow route remains `reimplementation-review`. No migration, route promotion, or destination write occurred.
- COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five PR workflows queued and zero jobs. COE #31 remains OPEN/DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 remains at `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`. The child packager still correctly rejects all ten profiles pending the approved site ULA authority; the Bubblewrap runner remains unavailable/blocked. No networking prefix was invented.
- The canonical private Drive registry v11 itself was not retrieved. A private Library checkpoint references its name and prior canonical status as metadata only; that checkpoint is not a substitute for the registry and no private contents were copied into GitHub.

### Next owner actions
1. PHX-QA: independently review the descriptor-relative inventory/read/write changes and race regression.
2. PHX-CORE / PHX-MASTER: maintain the existing freshness/ownership route; do not require PHX-RELEASE to edit CORE-owned records.
3. PHX-PISONET: repair `$buildWorkflow` initialization in its negative self-test.
4. PHX-INFRA: provide an authorized Bubblewrap-capable disposable runner for COE #31/#35.
5. PHX-CORE / COE integration owner: approve the site-scoped ULA provisioning authority before PHX-RELEASE resumes profile packaging.

No merge, real-key signing, tag, publication, hardware flash, financial migration, or customer deployment occurred. Physical 150-power-cut acceptance and 30-device/24-hour soak remain **NOT TESTED**. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC16 — reject hard-linked artifact payloads (2026-11-19T16:18Z)

### Verified release-provenance defect

The descriptor-relative artifact inventory admitted a regular file even when its inode had multiple hard links. A payload path inside the artifact directory could therefore alias an inode also named outside that tree. The provenance writer hashed and manifested that entry as an ordinary payload; an external alias could expose content not independently owned by the admitted artifact tree or mutate the same inode during later handling.

### Test-first history and correction

- Regression commit [`bac542e3df75cb325f819f6e57535b47e52666ae`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bac542e3df75cb325f819f6e57535b47e52666ae) adds an external-hardlink fixture, regenerates the existing checksum manifest, and requires admission to fail without changing SHA256SUMS, creating BUILD-PROVENANCE.json, or modifying the external file.
- Expected RED: [PR run #44564359785](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44564359785), CI-0701 job `135701938049`. The prior 21 provenance tests passed; the new test failed exactly with `AssertionError: ProvenanceError not raised`. This reproduced the admission gap on the pre-fix writer.
- Source correction [`90165b173179e9b36c73f98e06cfd5e0a06a3fe3`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/90165b173179e9b36c73f98e06cfd5e0a06a3fe3) adds a single-link requirement to descriptor-relative artifact reads/hashes and includes `st_nlink` in file/directory identity comparisons. The check is applied before and after opening/reading so a link-count change during inventory is rejected as well. Hard-linked artifact files are not admitted.
- Exact source/test SHA: `90165b173179e9b36c73f98e06cfd5e0a06a3fe3`.

### Exact-source GitHub Actions at handover update

- BlazePwifi PR run [#44564586389](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44564586389): CI-0701 job `135702737165` **SUCCESS**; the provenance suite reports **22 tests PASS**, including the new external-hardlink rejection. Immutable action pins, release concurrency, Arduino CLI archive verifier, ESP32 compatibility workflow contract, board-core pins and CI-0701 classifier steps also **PASS**. ESP8266 job `135702877914` **SUCCESS**. At this handover update, `validate`, Android, ESP32 and several OpenWrt target jobs were still **IN_PROGRESS/QUEUED**; no overall run-level SUCCESS is claimed.
- ESP32 compatibility PR run [#44564586180](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44564586180): both core jobs were **QUEUED** at this read; no compile result is claimed.
- Windows PR run [#44564585852](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44564585852): handover job **SUCCESS**; `build-windows` was **IN_PROGRESS**; publisher was not executed. No Windows result is inferred.
- Test-only RED run [#44564359785](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44564359785) is intentionally failing evidence, not a source-head failure.

### Ownership, provenance and next actions

- This UTC16 change touched only `.github/scripts/test_build_provenance.py`, `.github/scripts/write_build_provenance.py`, and this PHX-RELEASE handover. No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source/handovers were edited by this task.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 remains OPEN/DRAFT on `phoenix/release-publisher-isolation-20261115`, based on #242. MASTER #288 remains OPEN/DRAFT at `7ac132361b29de8c0bff86d337a79e3cab989b33`; ownership routes remain `DRAFT_REVIEW_ONLY`, and the release workflow route remains `reimplementation-review`.
- COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; COE #31 remains OPEN/DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child packager #35 remains OPEN/DRAFT at `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`. The ULA guard continues to reject all ten profiles until CORE/MASTER approve the site-scoped RFC 4193 authority; the mandatory Bubblewrap sandbox remains blocked by runner capability.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found after paginating 1,422 Library entries (8 pages); no older registry was substituted and no private contents were copied.
- PHX-QA: independently review single-link admission and the descriptor-relative race behavior at the exact source/test SHA.
- PHX-PISONET: repair its own `$buildWorkflow` negative-self-test variable; RELEASE does not edit that test.
- PHX-INFRA: provide an approved disposable Bubblewrap-capable runner; PHX-CORE/MASTER and COE integration owner: resolve site ULA provisioning authority before profile packaging resumes.

No merge, real-key signing, tag, publication, hardware flash, payment migration or customer deployment occurred. CI remains synthetic evidence only; physical 150-power-cut acceptance and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC17 — remove unused provenance inventory wrappers

**Disposition:** Behavior-neutral release-source cleanup committed on the existing PR #291 branch. Exact source/test SHA `36056d08b4ff7de6f692c5c83b55c1e335cda070`; exact-source BlazePwifi workflow [#44576439303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44576439303) completed **SUCCESS** with 27 jobs SUCCESS and 5 intentionally skipped. PR #291 remains OPEN / DRAFT / UNMERGED.

### Scope and change

The provenance writer had two unreferenced wrappers, `_inventory(root)` and `_verify_checksum_manifest(root, files)`, which reopened the artifact root by pathname and duplicated the descriptor-relative entry points. Repository-local reference inspection found no call sites beyond the definitions. Removed only those two wrappers; `_inventory_at` and `_verify_checksum_manifest_at` remain the descriptor-relative implementation used by `write_provenance`.

No runtime packaging behavior, manifest schema, checksum format, firmware source, shared interface, signer policy, publisher permission or production authorization changed.

### Test-first evidence

- Test-only commit [`c5df946a9dfa2f9dc04b18f60be46d5bb64b3db9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c5df946a9dfa2f9dc04b18f60be46d5bb64b3db9) added `test_no_unused_path_reopening_inventory_wrappers_remain`.
- Expected RED [#44576256907](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44576256907): 23 tests ran; 22 existing tests passed and the new test failed exactly because `_inventory` still existed (`AssertionError: True is not false`). Other release guards passed before the provenance test stopped the job.
- Source cleanup commit [`36056d08b4ff7de6f692c5c83b55c1e335cda070`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/36056d08b4ff7de6f692c5c83b55c1e335cda070) removed exactly the two unused functions.
- Exact-source CI-0701 in [#44576439303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44576439303) passed: provenance 23/23, release concurrency 4/4, Arduino archive verifier 8/8, immutable action pin guard, exact ESP32 compatibility workflow contract, and CI-0701 fail-closed classifier contract.
- Full exact-source workflow #44576439303 completed **32 jobs: 27 SUCCESS / 5 SKIPPED / 0 FAILED**. Mandatory handover freshness, handover fail-closed regression, full validation, Android build, ESP32 and ESP8266 builds, all OpenWrt target builds, update bundle, nine v0.4 simulations and v0.4 candidate gate completed successfully.
- The five skipped jobs were `production_import_signed_apk`, `publish_prerelease`, `publish_release`, `production_sign_handoff`, and `publish_v060_lab_preview`. No signing or publication ran.
- The x86_64 BIOS/UEFI QEMU audit passed. Its simulation artifact was uploaded as ID `14558250689`, provider-reported SHA-256 `4f85e9532aca589cc91d69d55387e0e996f6da264056277a36528248f77c0633`. This is a hosted simulation artifact, not an independently downloaded production binary or physical acceptance evidence.

### Separate Windows release result

[Windows run #44576453544](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44576453544): shared handover gate PASS; exact .NET SDK `8.0.425` PASS; package parity PASS; PISONET-owned `tests/ReleaseSigning/negative-selftest.ps1` failed because `$buildWorkflow` is uninitialized. Windows build and publisher were skipped. PHX-RELEASE did not edit the PISONET-owned test or source.

### Live ownership and cross-repository state

- MASTER PR #288: head `b1a38cea83a9bfe877acd795730079d65ed3bf25`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`; release workflow route remains `reimplementation-review`. No migration or ownership promotion.
- Experiments PR #242: `734b89d9e7792247e8376335c3f3685500ab3f89`; PR #291 source/test head `36056d08b4ff7de6f692c5c83b55c1e335cda070`; base remains #242.
- COE #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`; eight existing workflows remain QUEUED with zero executed jobs.
- COE #31: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; hardware/shared and case-collision jobs passed, mandatory Bubblewrap namespace setup failed at unprivileged UID-map creation. No privileged or unsandboxed fallback.
- COE #35: `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`; 116 packager tests passed, but all ten appliance profiles correctly fail closed pending approved site-scoped RFC 4193 ULA authority. Its sandbox run failed because Bubblewrap is absent (exit 125); case-collision passed; firmware compilation was skipped after profile validation failed.
- COE #35's current `tools/RELEASE_PACKAGER_HANDOVER.md` blob `399ed14e9dd516a25fcebfdb41a29e526dc11d0b` still ends at its UTC05 section despite the later #35 head and ULA gate. This handover needs a separate release-owned refresh; no COE file was changed in this UTC17 task.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the authorized Library search. No older registry snapshot was substituted and no private contents were copied.

### Ownership and next actions

This UTC17 task changed only `.github/scripts/test_build_provenance.py`, `.github/scripts/write_build_provenance.py`, and this PHX-RELEASE handover. PR #291 already contained inherited CORE handover/ledger changes from earlier branch history; those CORE files were not modified by this task.

- PHX-QA: independently review the one-entry-point cleanup and exact-source provenance suite.
- PHX-PISONET: initialize `$buildWorkflow` in its own negative self-test; RELEASE does not edit it.
- PHX-CORE / PHX-MASTER: approve site-scoped ULA provisioning authority before COE profile packaging can pass.
- PHX-INFRA: provide an approved unprivileged Bubblewrap-capable disposable runner.
- PHX-RELEASE: refresh the stale COE #35 release-packager handover in a separate scoped activation after re-reading its current head and handover ownership.

No merge, tag, signing, publication, hardware flash, payment migration or customer deployment occurred. Hosted CI/QEMU simulations are not physical hardware acceptance. The protected signer, independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**

## PHX-RELEASE UTC19 — protect every write-privileged BlazePwifi publisher (2026-11-19T19Z)

**Disposition:** Four write-privileged BlazePwifi import/publisher jobs now fail closed unless the event is a push to the exact approved ref, GitHub reports that ref as protected, and a role-specific repository approval variable is exactly true. Existing PR #291 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Live control plane and ownership

- Issue #172 and cleanup-first #266 were reread. MASTER PR #288 advanced to 2e082bbc583e2c0079b136b10f651b70ef30d751; its ownership-routes manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY. PHX-RELEASE's BlazePwifi workflow route remains reimplementation-review, not migration permission.
- Experiments PR #242 remains OPEN/DRAFT at 734b89d9e7792247e8376335c3f3685500ab3f89. PR #291 branch phoenix/release-publisher-isolation-20261115 is based on #242; exact source/test head for this task is de6aa394d1b879c339119f63bca7c52c8177b002.
- COE #26 remains b382d233ff06c8791b1028bed3c617cc7b670d12; #31 remains 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; child #35 is d41f3231e0eae6cf0c62d19f430818e30372162e; child #44 is 582fd5d5e83e36b36546ac28534740298ba94af4. #35's site-ULA gate and mandatory Bubblewrap infrastructure blocker remain; #44's per-appliance random ULA does not establish a shared site-scoped prefix. No COE file or cross-repository route was changed in this task.

### Defect and bounded correction

The four jobs in .github/workflows/blazepwifi-build.yml that receive contents: write were previously gated by a ref name and commit-message marker, but not by an explicit push-event check, github.ref_protected, or a separate role-specific approval variable. This left the write boundary dependent on branch-name matching alone.

The workflow now requires all of the following before any of those four jobs can start:

| Job | Additional approval variable |
|---|---|
| production_import_signed_apk | BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED |
| publish_prerelease | BLAZEPWIFI_PRERELEASE_APPROVED |
| publish_release | BLAZEPWIFI_PRODUCTION_RELEASE_APPROVED |
| publish_v060_lab_preview | BLAZEPWIFI_LAB_PREVIEW_APPROVED |

Each job also requires github.event_name == 'push', its pre-existing exact ref, github.ref_protected == true, and its existing commit-message marker. The separate Windows publisher retains its existing protected-ref and SOFTTIMER_RELEASE_APPROVED gate.

No repository variable was created or changed by PHX-RELEASE. The new variables are explicit future administrative gates; setting one is not evidence of an independent freshness witness, QA/MASTER approval, signer custody, financial migration or physical acceptance. The variables must remain unset/false until the appropriate owners authorize their lane.

### Live branch-protection evidence

The public branch API was read for main, blazepwifi-v0.3.0-production, blazepwifi-v0.3.0-design, and blazepwifi-v0.6.0-audit-foundation. All four report protected=false; required-status-check enforcement is off. The repository rulesets endpoint returned an empty list. The classic branch-protection detail endpoint returned 403 to the connected GitHub integration, so its internal configuration could not be inspected. The branch metadata is sufficient to establish that github.ref_protected is currently false for each of these refs. The new publisher conditions therefore fail closed today even if an approval variable were already true.

### Test-first history and correction notes

- Initial test-only commit 582b5449c64b51f419cf1ae7c18987ef2f83f6a0 introduced a static guard for all four write-privileged jobs. Its first newline matcher was malformed; it was corrected before relying on any RED result.
- Corrected test-only commit 8267e7047b234d246bebf1506403a5e62a68d183 produced the expected RED in [#44597624463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44597624463): CI-0701 failed in RELEASE-CONCURRENCY with four subcases, one for each write-privileged job, because the old conditions lacked the required push/protected-ref/approval predicates. The four publisher jobs were skipped in PR validation.
- Workflow correction 8538a4075d123ebb296a477aa4fcf399b0010931 added the push, protected-ref and role-specific approval gates to all four jobs.
- The first post-fix run [#44597802331](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44597802331) exposed a stale assertion in the existing test that required if: github.ref to be the first predicate. Test correction de6aa394d1b879c339119f63bca7c52c8177b002 now checks the exact ref independently of the preceding safety predicates. This is a test-harness compatibility correction, not a workflow bypass.

### Exact-source Actions at de6aa394

- Push run [#44597947750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44597947750): overall **FAILURE**, not Full CI success. CI-0701 / RELEASE-CONCURRENCY **PASS**; ESP32 **PASS**; ESP8266 **PASS**; Android **PASS**; all 11 OpenWrt target jobs **PASS**. Mandatory validate **FAILED** at the CORE-owned handover freshness gate: source/workflow changes were newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md; last recorded checkpoint was 12c89d189225cc461efddc84723cbfb3adf6e83c. The workflow archived exact-SHA handover evidence despite the failure. Update bundle and v0.4 simulations were skipped after validation failed. All signing and publisher jobs were skipped.
- PR run [#44597961905](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44597961905): CI-0701 / RELEASE-CONCURRENCY **PASS**; validate **FAILED** at the same CORE-owned handover freshness gate; ESP32 and Android **PASS**; ESP8266 **FAILED** because the runner's pinned Arduino CLI archive download returned a transient connection reset (Errno 104), not a source/compiler error. Most target jobs had passed; one target was still in progress at this handover update. No overall PR-run success is claimed.
- Windows PR run [#44597961801](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44597961801): handover freshness **FAILED** at the same CORE-owned gate; Windows build and publisher **SKIPPED**. This run did not reach PISONET's negative self-test. The earlier #291 Windows run [#44581603605](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44581603605) separately failed in PISONET-owned negative-selftest.ps1 because $buildWorkflow is uninitialized; PHX-RELEASE did not edit that test.
- On the exact-source push run, production_import_signed_apk, publish_prerelease, publish_release, production_sign_handoff, and publish_v060_lab_preview were all **SKIPPED**. No publisher, signer, tag or release was invoked.

### Private provenance and next owner actions

- Exact Library search for BLAZE_PROJECT_REGISTRY_v11_20261027.json returned older v3/v4/v5/v6/v7 entries but not canonical v11. No older snapshot was substituted; no private file contents or identifiers were copied into GitHub.
- **Repository administrator:** configure and verify protected release admission for main and the three release refs, including required checks/reviews and a protected approval path. The current branch metadata reports all four unprotected.
- **PHX-MASTER / PHX-QA:** independently review the four publisher predicates and the role-specific approval-variable contract. MASTER keeps the reimplementation route review-only until an explicit decision.
- **PHX-CORE:** refresh its own BlazePwifi PROJECT_HANDOVER.md, CURRENT_STATE.md and CHANGE_LEDGER.md after this workflow change; PHX-RELEASE did not edit those CORE-owned records or bypass the freshness gate.
- **PHX-PISONET:** initialize $buildWorkflow in its own negative self-test; RELEASE can rerun the Windows workflow after PISONET and CORE resolve their respective blockers.
- **PHX-INFRA / COE integration / CORE / MASTER:** retain the existing Bubblewrap and site-ULA authority blockers on COE #31/#35/#44; no prefix or sandbox fallback was invented.

No merge, real-key signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Physical 150-power-cut acceptance and the 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**



## PHX-RELEASE UTC20 — workflow-wide token inheritance guard

**PR #291 branch:** `phoenix/release-publisher-isolation-20261115`  
**Base:** PR #242 branch `draft/softtimer-future-release-signing-pipeline-20261029@734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test commit:** `c668996b396c7427e3f97d81308067fe7ffce7b7`  
**Scope:** `.github/scripts/test_release_workflow_concurrency.py` only.

The current BlazePwifi workflow already has workflow-level `permissions: contents: read`, while four publisher jobs have explicit job-level write grants and their existing push/ref-protection/role-approval/marker gates. The prior concurrency test counted explicit job-level writes but did not assert the workflow-wide default. A future top-level `contents: write` plus per-job overrides could therefore weaken the default boundary without being detected by that assertion.

Added two release-owned guard tests:
- `test_blazepwifi_workflow_default_token_scope_is_read_only` requires the complete workflow-level permission map to be exactly `{"contents":"read"}`.
- `test_workflow_default_permission_guard_rejects_inherited_write_mutation` changes that default to `contents: write` in a synthetic in-memory workflow and proves the guard rejects it.

No workflow behavior, publisher configuration, repository variables, secrets, application code or product paths changed. This is guard coverage, not a runtime defect fix; the current workflow default was already read-only, so no product RED was expected.

### Exact-source Actions

- CI-0701 job [135855484128](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44607642181) **SUCCESS** at exact source/test SHA `c668996b396c7427e3f97d81308067fe7ffce7b7`: RELEASE-CONCURRENCY **7/7 PASS**, provenance **23/23 PASS**, Arduino CLI archive verifier **8/8 PASS**.
- PR build [#44607642181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44607642181): at last read, **24 jobs success, 4 skipped, 2 in progress, 0 failed**. Remaining jobs were the x86 QEMU audit and Android-emulator simulation. The overall run was still in progress; no terminal SUCCESS is claimed.
- Push build [#44607627688](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44607627688): at last read, **24 success, 4 skipped, 2 in progress, 0 failed**; Android-emulator and x86 QEMU simulations remained in progress. No terminal conclusion is claimed.
- ESP32 compatibility [#44607642013](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44607642013) **SUCCESS**, both ESP32 core 3.3.13 and 4.0.0 legs. This workflow still pins HARDWARE source `984ea8ff65a93b7da6e22fc2e1943acaf56100ca`, while live HARDWARE PR #327 head is `fc4c9055be9680f9b7a7b7765c9435a63ff4a8ac`. The passing run is therefore for the older pinned source, not current #327 acceptance. PHX-MASTER / PHX-HARDWARE must nominate the candidate source SHA before RELEASE updates the compatibility pin.
- Windows [#44607642048](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44607642048) **FAILURE** in PISONET-owned `negative-selftest.ps1`: `$buildWorkflow` was unset. .NET SDK 8.0.425, package parity, release concurrency, immutable action pins and checkout-credential checks passed; Windows publisher was **SKIPPED**. RELEASE did not edit PISONET paths.

### Live gates and cross-repository state

- Main and release refs `main`, `blazepwifi-v0.3.0-production`, `blazepwifi-v0.3.0-design`, and `blazepwifi-v0.6.0-audit-foundation` all report `protected=false`; repository rulesets list is empty. Publisher jobs remain fail-closed.
- MASTER PR #288 head `b6ee424b897701bf1c550076610203d45f1a13f2`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and RELEASE workflow routing remains `reimplementation-review` to COE #26.
- PR #291 currently has 16 changed paths, including three CORE-owned handover paths and two PISONET-owned test paths. Those are pre-existing branch contents, not changed in this activation. This activation changed only the RELEASE-owned test file and handover. MASTER and the respective owners must reconcile/split those foreign paths before any merge; no review has been submitted.
- COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`: five workflows remain queued, zero jobs executed.
- COE #31 head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`: shared firmware/hardware checks and case-collision guard passed; mandatory ImageBuilder sandbox failed closed, exit 125, because `bwrap: setting up uid map: Permission denied`.
- COE #35 head `d41f3231e0eae6cf0c62d19f430818e30372162e`: 117 packager tests pass (two intentional skips), all ten profiles reject missing approved site-scoped RFC 4193 ULA authority, sandbox fails closed, case-collision guard passes. No prefix was invented.
- Canonical private Drive registry v11 was not found through the authorized Library surface; older v3-v7 snapshots were not substituted and no private contents were copied.

### Next owner actions

- **Repository administrator:** establish and verify branch protection, required checks/reviews and the protected release approval path.
- **PHX-MASTER / PHX-QA:** review the workflow-default permission guard and resolve the mixed-ownership PR #291 path set.
- **PHX-MASTER / PHX-HARDWARE:** nominate the exact current Hardware candidate SHA for the release compatibility matrix.
- **PHX-PISONET:** initialize `$buildWorkflow` in its own negative self-test.
- **PHX-CORE / COE integration:** resolve site-scoped ULA provisioning authority.
- **PHX-INFRA:** provide the approved unprivileged Bubblewrap namespace runner.

PR #291 remains OPEN / DRAFT / UNMERGED. No merge, signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. Physical 150-power-cut acceptance and the 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**

## PHX-RELEASE UTC22 — guard all SoftTimer production signing steps (2026-11-19T22Z)

**Disposition:** release-owned regression coverage added to the existing #291 branch. The SoftTimer workflow itself was not changed; all three existing production sign/verify steps were already guarded. The test now prevents any one of those gates being removed or weakened. PR #291 remains OPEN / DRAFT / UNMERGED; **PRODUCTION NO-GO**.

### Exact source and ownership

- Live control plane #172, cleanup-first #266, owner execution prompt, and MASTER #288 routes were reread. MASTER #288 exact head 9bff8bb8b47783d860be3725c139b58a576c7333; route manifest blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY. PHX-RELEASE owns Phoenix build/signing workflow controls and release tests; this is not a workflow migration.
- Experiments #242 remains 734b89d9e7792247e8376335c3f3685500ab3f89; #291 branch phoenix/release-publisher-isolation-20261115 is based on #242 and now points to 68ed7543e274a813920e7b8b841bdd48b15fe1c5.
- SoftTimer release workflow blob inspected at this source: 545c308568da2c434180d231ea9b0d62e83720cd. It has three production sign/verify steps (portable EXEs, native Setup, final signed-package verification). Each currently requires push to refs/heads/main, github.ref_protected == true, env.VERSION != 0.4.0, and vars.SOFTTIMER_RELEASE_APPROVED == true.
- Only .github/scripts/test_release_workflow_concurrency.py and this PHX-RELEASE handover changed in this task. No PISONET source/test/installer path, CORE handover, QA test path, HARDWARE firmware, or MASTER coordination path was edited.

### Regression coverage and test history

The previous test test_windows_build_is_explicitly_read_only_and_publisher_isolated checked the separate write-privileged publisher job but did not individually protect all three production Authenticode steps.

- Test commit [38be13df](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/38be13dffca7213a818488556cfcf72b93331c14) added a helper and synthetic mutation test. Its first CI run [#44625878212](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625878212) FAILED in the new guard: the regex/newline matcher was over-escaped and only found the first signing step. This was a PHX-RELEASE test-harness defect, not a product/workflow failure; no signing or publisher ran.
- Correction commit [68ed7543](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/68ed7543e274a813920e7b8b841bdd48b15fe1c5) fixed the matcher. The test now asserts the exact three reviewed sign/verify step names and exact guard expression, then mutates one approval predicate in-memory and proves the guard rejects it. It does not execute signing commands or access credentials.

### Exact-source Actions at 68ed7543

- PR BlazePwifi build [#44625985862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625985862), CI-0701 job 135919834672: SUCCESS. Release concurrency/signing guard suite 8/8 PASS; provenance suite 23/23 PASS; Arduino archive verifier 8/8 PASS; action pin checks passed (52 BlazePwifi, 3 ESP32 compatibility, 6 SoftTimer external action invocations); ESP32 workflow contract and observed board-core pin checks passed.
- The overall PR build #44625985862 was still QUEUED at last read; remaining target jobs had not completed. No Full CI success is claimed.
- Push build [#44625978005](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625978005) remained IN_PROGRESS at last read. Some targets had passed, while Android, x86_64, Ruijie, several Orange Pi targets, ESP32 and mandatory validation were still running. No terminal conclusion is claimed.
- Windows release [#44625985860](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625985860): shared handover job 135919891611 SUCCESS; build-windows job 135920011848 was IN_PROGRESS after checkout. The new exact-head run had not yet reached the PISONET negative self-test at last read. The prior head's PISONET $buildWorkflow failure remains an owner issue, not modified here.
- ESP32 compatibility [#44625986102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625986102) was PENDING; no compatibility conclusion is claimed.

### Release gate and remaining blockers

- Experiments main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b currently reports protected=false; repository rulesets endpoint is empty. Therefore the SoftTimer github.ref_protected == true signing condition cannot pass on the current main ref.
- SOFTTIMER_RELEASE_APPROVED is an administrative approval variable, NOT an independent freshness witness. No independently verifiable freshness-witness job, artifact, signature, or interface is defined in the current SoftTimer release workflow/ownership routes. PHX-RELEASE did not invent a variable or treat manual approval as witness evidence. MASTER/CORE must define the authoritative witness contract before real-key signing can be enabled.
- MASTER #288 9bff8bb8... remains DRAFT; COE #26 b382d233..., parent #31 59ed44d0..., and active COE #35 7b9706d8... remain draft. #35's site-scoped ULA and Bubblewrap runner blockers remain unchanged.
- Canonical private Drive registry v11 was not available through the authorized Library search. No older snapshot was substituted; no private contents or identifiers were copied to GitHub.

No merge, real-key signing, tag, publication, hardware flash, payment migration, or customer deployment occurred. Physical 150-power-cut acceptance and 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**

**Next owner actions:** PHX-QA independently reviews the signing-step guard; MASTER/CORE define the independent freshness-witness interface and protected signer authority; repository administrator establishes protected main and required checks; PHX-PISONET owns its negative-selftest variable defect; RELEASE rechecks exact-head Windows and full-build runs before any later checkpoint.

### UTC22 terminal CI status refresh — 2026-11-19T22:12Z

This section supersedes the earlier "not yet reached" observation for the exact source/test head 68ed7543e274a813920e7b8b841bdd48b15fe1c5.

- Windows PR run [#44625985860](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625985860) completed **FAILURE**. Shared handover job 135919891611 passed. Windows build job 135920011848 passed checkout, .NET SDK 8.0.425 verification and package-parity self-test, then failed in the PISONET-owned negative-selftest.ps1 because $buildWorkflow is uninitialized. Windows publisher job 135920807292 was **SKIPPED**. PHX-RELEASE did not modify the PISONET test.
- BlazePwifi PR run [#44625985862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625985862) and push run [#44625978005](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625978005) remained nonterminal at last read. Their CI-0701 guard job passed on the exact source/test head; remaining full target/validation jobs had not completed. No Full CI success is claimed.
- ESP32 compatibility PR run [#44625986102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44625986102) remained in progress on the older pinned HARDWARE source 984ea8ff65a93b7da6e22fc2e1943acaf56100ca; it is not current hardware acceptance.
- The handover-only docs head is now 6f109f376c8e610231cdc2439dd24cb74fba4c57. Its push BlazePwifi run [#44626285917](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44626285917) was pending and ESP32 compatibility push [#44626285919](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44626285919) was in progress at last read. These are not yet terminal evidence.


## PHX-RELEASE UTC23 — refresh ESP32 compatibility to live HARDWARE #327 (2026-11-19T23Z)

**Disposition at handover update:** SOURCE PIN CORRECTED / STATIC RELEASE GUARD PASS / EXACT HARDWARE MATRIX RUNNING / PR OPEN-DRAFT-UNMERGED / PRODUCTION NO-GO.

### Exact source identity and ownership

- Experiments PR #291 branch `phoenix/release-publisher-isolation-20261115`, base PR #242 `734b89d9e7792247e8376335c3f3685500ab3f89`.
- PR #291 source/test head after the two code commits: `ba5fc403270429bc9068b599dd22dfda216a1a5f`; handover-only successor will follow this record.
- Live PHX-HARDWARE PR #327 head at the final pre-write refresh: `06c1cdaa47f2a33594354b014bd0b7445f894aaa`.
- ESP32 sketch path: `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`; exact blob at #327 head: `a59c986f6fe6e0ecb0069f3829b54df93ed0d96d`.
- Previous release matrix pinned older source `984ea8ff65a93b7da6e22fc2e1943acaf56100ca` and sketch blob `528187f68aaad7d76a690bbf1cbe338165ad3839`. Its earlier green runs are historical-source compile evidence only, not current #327 qualification.
- MASTER PR #288 head `a7f41020706934a9240bf763350322afd705095e`; `coordination/phoenix/OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. PHX-RELEASE owns this release compatibility workflow/test/handover; no workflow migration or shared interface change is authorized by this task.

### Test-first correction

- Test commit [`517887ab`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/517887abdfeef89e89941e34cb75b49da77cb016) updates the static test's expected HARDWARE #327 source SHA and ESP32 sketch blob.
- Expected RED: [push #44635924628](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44635924628), CI-0701 job `135954284574`, failed specifically at `RELEASE-TOOLCHAIN exact ESP32 core compatibility workflow contract`: the workflow still lacked the new exact source SHA/blob. The action-pin, concurrency, provenance and Arduino archive verifier steps passed. This is the intended stale-pin reproduction, not a compiler failure.
- The test-only commit also triggered old-workflow matrix runs [PR #44635924603](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44635924603) and [push #44635929876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44635929876); both completed SUCCESS against the old `984ea8ff` source pin. They are explicitly **not** current #327 source evidence.
- Workflow correction [`ba5fc403`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ba5fc403270429bc9068b599dd22dfda216a1a5f) updates the job label, checkout ref, independent `EXPECTED_SOURCE_SHA`, and `EXPECTED_SKETCH_BLOB` to the exact current #327 head/blob. The matrix remains read-only, uses immutable actions, disables persisted checkout credentials, pins Arduino CLI 1.6.0 and verifies its archive bytes; it does not upload, flash, sign or publish.

### Exact-source Actions after the correction

- CI-0701 in [BlazePwifi PR run #44636008556](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44636008556), job `135954580887`: **SUCCESS**. The exact compatibility workflow contract and release action-pin, concurrency, provenance and Arduino CLI archive-verifier guards passed.
- Current-source compatibility [PR run #44636008662](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44636008662) and [push run #44635999237](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44635999237): **both COMPLETED SUCCESS**. Both legs checked out #327 `06c1cdaa47f2a33594354b014bd0b7445f894aaa`, verified ESP32 sketch blob `a59c986f6fe6e0ecb0069f3829b54df93ed0d96d`, verified Arduino CLI 1.6.0 archive size `20,111,675` / SHA-256 `321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250`, and installed CLI binary SHA-256 `5897b56f5eac106e60c902d6444f2923e918885aaeb119fc4b44ff9db5003ba8`. Core 3.3.13 compile **PASS**: program `1,043,128` bytes (79%), globals `49,960` bytes (15%), binary SHA-256 `fbcd0ee86cd2fa404128612a55ca8bb06d1ee2c7b8731fef1e20700663c3ee21`. Core 4.0.0 compile **PASS**: program `1,097,053` bytes (83%), globals `52,576` bytes (16%), binary SHA-256 `70b01ba160d3586e500589fb54e259161fe56ff07f0599862c97caa4992fade4`. These are hosted CI compile outputs for the exact #327 source, not physical-board acceptance.
- The broader BlazePwifi run [#44636008556](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44636008556) later completed **CANCELLED** when the documentation-only successor superseded it. CI-0701, mandatory validation, ESP32, ESP8266, Ruijie and returned Orange Pi jobs were SUCCESS; Android and several remaining simulation/publisher jobs were CANCELLED. This is not an overall Full CI pass. The subsequent handover-head BlazePwifi run #44636503500 and compatibility run #44636503480 were still in progress at the last read; they are docs-head checks, not substitutes for the terminal source/test results above.
- Windows [run #44636008405](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44636008405): handover PASS; build failed in PISONET-owned `tests/ReleaseSigning/negative-selftest.ps1` because `$buildWorkflow` is uninitialized under StrictMode; publisher skipped. PHX-RELEASE did not modify the PISONET subtree.
- Current HARDWARE #327 Full run [#44632263889](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44632263889) failed at QA-owned `Controller protocol parity`; ESP32, ESP8266, Android and returned target jobs passed. This is not a Full validation pass and the release compile matrix does not replace QA review or hardware acceptance.

### Cross-repository and provenance status

- COE integration #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; parent release packager #31 remains OPEN/DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; active child #35 remains OPEN/DRAFT at `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`. The existing site-scoped ULA authority and Bubblewrap runner blockers remain; no cross-repository migration was attempted.
- The authorized Library listing scanned 1,422 entries and returned older registry snapshots v3–v6, but no canonical `BLAZE_PROJECT_REGISTRY_v11_20261027.json`. A separate checkpoint snapshot references the v11 title, but is not the canonical registry and was not substituted. No private Drive contents or identifiers were copied to GitHub.

### Next owner actions

1. PHX-QA independently reviews the exact-current-source 3.3.13/4.0.0 compile results once both matrix runs terminate.
2. PHX-HARDWARE/MASTER notify RELEASE if #327 advances; refresh the pin before any subsequent matrix claim.
3. PHX-QA repairs the current #327 default-deny controller fixture; do not relax firmware poll admission.
4. PHX-PISONET initializes `$buildWorkflow` in its own negative self-test; RELEASE reruns Windows after that owner correction.
5. PHX-MASTER retains the #291 reimplementation-review route and reconciles mixed-owner paths before any merge.

No merge, signer use, tag, publication, hardware flash, financial migration or customer deployment occurred. Physical 150-power-cut acceptance and the 30-device/24-hour soak remain NOT TESTED. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC00 — refresh exact-source ESP32 compatibility to live HARDWARE #327 (2026-11-20T00Z)

**Disposition:** stale release pin corrected; exact-source two-core compile matrix PASS; docs-head static revalidation queued by this handover commit; application-image digest selection remains a separate follow-up. PR #291 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Exact source identity

- Experiments PR #291 branch: `phoenix/release-publisher-isolation-20261115`; base PR #242 at `734b89d9e7792247e8376335c3f3685500ab3f89`.
- PR #291 parent before this handover update: `4e7bd4e5a406646bc648419ca4d0cadc62c129cc`.
- Live HARDWARE PR #327 docs/PR head: `38a1a29bfd163ca1226b2a431f49b8f4911eed48`.
- Exact HARDWARE source/test commit pinned by the release matrix: `9ef753a38226fcdf56b0903680a5110348027110`. The current #327 head is one documentation-only commit beyond this source/test commit.
- ESP32 sketch path: `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`; exact Git blob at the pinned source commit: `33081c5094ffdd19d935fc888d52ae01ff23325b`.
- Previous release pin `06c1cdaa...` / sketch blob `a59c986f...` was stale after the namespace-open fail-closed HARDWARE change. The earlier old-source matrix run [#44644738582](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44644738582) completed SUCCESS, but only against the old pin and is not current-source qualification.

### Test-first correction

- Test commit [`9e2b2360`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9e2b236015c6ce788fce115fd114108b3797d068) changed the static compatibility contract to require the current HARDWARE source SHA and sketch blob.
- Expected RED: push [#44644738607](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44644738607), CI-0701 job `135984324453`: action pins, concurrency checks, 23 provenance tests and 8 Arduino archive-verifier tests passed; the exact ESP32 compatibility contract failed specifically because the workflow still contained the old source SHA/blob. This was the intended stale-pin reproduction, not a compiler failure.
- Workflow correction [`4e7bd4e5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4e7bd4e5a406646bc648419ca4d0cadc62c129cc) updates the job label, exact checkout ref, `EXPECTED_SOURCE_SHA`, and `EXPECTED_SKETCH_BLOB` to `9ef753a...` / `33081c...`. Only release-owned workflow/test paths were changed; no HARDWARE source was edited.

### Exact-source matrix

[Compatibility push run #44644854479](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44644854479): **OVERALL SUCCESS**, both matrix jobs completed SUCCESS.

- Both jobs verified source commit `9ef753a38226fcdf56b0903680a5110348027110` and sketch blob `33081c5094ffdd19d935fc888d52ae01ff23325b`.
- Both verified Arduino CLI archive size `20,111,675`, archive SHA-256 `321ee249f44c78053234fec0f36101092bc6021bf24939e15e0cc2449c5ed250`, and installed CLI SHA-256 `5897b56f5eac106e60c902d6444f2923e918885aaeb119fc4b44ff9db5003ba8`.
- ESP32 core 3.3.13 job `135985553120`: **SUCCESS**; program storage `1,043,720` bytes (79%); globals `49,960` bytes (15%).
- ESP32 core 4.0.0 job `135985553045`: **SUCCESS**; program storage `1,097,721` bytes (83%); globals `52,576` bytes (16%).

**Artifact-digest limitation discovered:** the workflow currently hashes the first `*.bin` returned by `find ... -print -quit` and does not log the selected filename. The marker digest is therefore not yet proven to identify the sketch application image; it must not be copied into a release `SHA256SUMS` or described as the app firmware digest. The two marker hashes matched earlier first-found values despite different sketch source blobs, reinforcing that this selection needs a separate release-owned follow-up: select the exact expected application `.ino.bin`, require exactly one candidate, and log path, size and SHA-256. That follow-up was not changed in this activation.

### Cross-repository / owner status

- MASTER PR #288 head `52cb1a68f256c3f50969e5b23ccc1f57a3bf2782`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`. The release route to COE `.github/workflows/pisowifi-ci.yml` is `reimplementation-review`; no workflow migration or COE source copy is authorized.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five sampled workflows remain QUEUED with no jobs returned.
- COE parent release packager #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; its sandbox run [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap and passed host preflight, but the unprivileged namespace probe failed with `bwrap: setting up uid map: Permission denied`, exit 125; sandbox packaging tests were skipped.
- COE child #35 remains `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`; profile admission remains fail-closed without approved site-scoped RFC 4193 ULA authority, and sandbox evidence is not accepted.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not surfaced by exact-name Library search; results only included older v3–v7 snapshots. No older snapshot was substituted and no private contents or identifiers were copied to GitHub.
- Existing PR #291 includes pre-existing CORE/PISONET-owned paths. This activation touched only `.github/scripts/test_phx_release_esp32_core_compatibility.py`, `.github/workflows/phx-release-esp32-core-compatibility.yml`, and this release-owned handover.

### Next actions

1. Reconcile the docs-head CI triggered by this handover commit; record CI-0701 and compatibility matrix outcomes separately.
2. PHX-QA independently reviews the exact-source two-core compile evidence; it remains hosted CI evidence, not physical-board acceptance.
3. PHX-RELEASE's next bounded task should address unambiguous application-image selection and digest provenance.
4. PHX-HARDWARE/MASTER notify RELEASE if #327 advances beyond `38a1a29...`; refresh the source/test pin before claiming later-source qualification.
5. PHX-PISONET owns the current Windows negative-selftest failure (`$buildWorkflow` uninitialized); RELEASE must not modify PISONET files.
6. PHX-INFRA/CORE/MASTER/COE integration retain the sandbox, ULA, migration and ownership blockers.

No merge, signer use, tag, publication, hardware flash, payment migration or customer deployment occurred. The protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC01 — exact ESP32 application-image identity and digest admission (2026-11-20T01Z)

**Disposition:** the compatibility matrix no longer hashes an arbitrary first-found `.bin`. It now selects exactly one named sketch application image, rejects ambiguous/unsafe candidates, and emits the selected filename, byte length and SHA-256. Focused CI, both ESP32 core builds and the broader BlazePwifi CI workflow completed successfully on the pre-handover source head. PR #291 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Scope and exact source

- Experiments PR #291: branch `phoenix/release-publisher-isolation-20261115`, base PR #242 `734b89d9e7792247e8376335c3f3685500ab3f89`.
- Source/test head before this handover append: `6a7e5c585bdbf86b1443e670b47af10e8391ef55`.
- Current PHX-HARDWARE PR #327 head at final refresh: `1d461f2c5fad1ea411ab89bab8d1a1f4e73dce1c`.
- The compatibility workflow still pins HARDWARE commit `9ef753a38226fcdf56b0903680a5110348027110` and sketch blob `33081c5094ffdd19d935fc888d52ae01ff23325b`. A live compare from that commit to #327 head is four commits ahead and lists only two handover documents plus two ESP8266 files; the ESP32 sketch blob remains identical. This matrix therefore proves the same ESP32 sketch blob and current ESP32 subtree content, but it does **not** claim checkout of the latest overall #327 HEAD. A future pin refresh is a separate bounded task and must preserve exact source/blob assertions.

### Test-first history and implementation

- Test-only commit [`5ab58fab`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5ab58fab1806aea4eab931944c0434120b0b842a) added negative/positive controls before the helper existed. Expected RED: [BlazePwifi run #44652840061](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44652840061), CI-0701 job `136011724024`, failed because the helper was absent and the workflow still selected the first arbitrary `*.bin`; immutable action pins, concurrency guards and 23 provenance tests passed.
- Helper commit [`8d5d75b`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8d5d75b408604b8be261af815b402d14b6dd6588) added `.github/scripts/verify_esp32_application_image.py`. It requires exactly one top-level `*.ino.bin`, the exact `BlazePwifiVendo32.ino.bin` filename, a non-empty regular file, link count one, no symlinked output directory, and stable file identity while streaming SHA-256.
- Workflow commit [`f8d29787`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f8d2978726618e1c85412b6a51317b8fde86bfe6) first wired the helper but contained a source-authoring mistake that left escaped `\u0024` text instead of GitHub matrix expressions. CI-0701 run [#44653135382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653135382) correctly failed its static workflow contract. Corrected in [`154a64db`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/154a64dbd3ea6637b2723225ac9d768cadaec92a).
- The next CI-0701 run [#44653228258](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653228258) found a test assertion that expected the marker to appear as one literal source string, while the helper assembled it from adjacent strings. This was a test-harness assertion defect, corrected in [`b83f8dbf`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b83f8dbf543f9a8f3212791bdb1b99f60e2b2c44).
- Workflow path filters were updated to include the helper itself in [`6a7e5c5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6a7e5c585bdbf86b1443e670b47af10e8391ef55), so future helper-only changes trigger compatibility validation.

### Exact-source verification at `6a7e5c5`

- Focused CI-0701 in [BlazePwifi run #44653465446](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653465446), job `136013811877`: **PASS**. Action pin guards, provenance suite, Arduino archive verifier, exact-source compatibility contract and new app-image synthetic controls passed.
- New synthetic controls: valid exact image with unrelated bootloader/partition `.bin` files; missing image; wrong sketch name; multiple `.ino.bin` candidates; empty image; symlinked image; hard-linked image; and symlinked output directory. All passed; marker: `PHX-ESP32-APP-IMAGE-TESTS-PASS`.
- Exact compatibility workflow [run #44653465461](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653465461): **2/2 jobs PASS**.
  - Core 3.3.13, job `136013844074`: selected `BlazePwifiVendo32.ino.bin`, `1,043,872` bytes, SHA-256 `9fba7a8126505359ff5fe3f424f43e509b3e57152b83a183a138110c6bf96c2e`.
  - Core 4.0.0, job `136013843742`: selected `BlazePwifiVendo32.ino.bin`, `1,097,872` bytes, SHA-256 `9cdfbd5191cf4ce30325ba0497f66c136ae391c00271c22bd492a608fa1dec94`.
- The broader BlazePwifi workflow [run #44653465446](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653465446) completed **SUCCESS: 26 successful jobs, 4 intentionally skipped**. The skipped jobs were production import, production signing handoff, release publishing and prerelease publishing. This is hosted CI/simulation evidence only.
- Windows run [#44653465426](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653465426): handover PASS; PISONET-owned `build-windows` FAILED because `$buildWorkflow` is uninitialized in `negative-selftest.ps1`; publisher SKIPPED. PHX-RELEASE changed no PISONET files.

### Live ownership and cross-repository status

- MASTER PR #288 is now `1bd30098d961b6dd2f0e971423ae8e4d36407f9b`, OPEN/DRAFT. Its `OWNERSHIP_ROUTES.json` remains unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with MASTER target null and RELEASE's COE workflow route `reimplementation-review`.
- COE integration #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`; MASTER's UTC01 checkpoint freezes migration staging. Five unique workflows remain queued with zero jobs returned.
- COE release-packager #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`. Its shared/contracts and ESP32/ESP8266 compile jobs plus case-collision guard pass, but the mandatory sandbox fails closed: Bubblewrap exists, yet unprivileged user-namespace setup is denied (`bwrap: setting up uid map: Permission denied`, exit 125).
- Canonical private Drive registry v11 and newer corrections remain unavailable through the authorized Library/Drive surface. Older v3–v7 snapshots were not substituted; no private identifiers or contents were copied to GitHub.
- PR #291 still contains pre-existing foreign CORE/PISONET paths. This activation changed only RELEASE-owned scripts, compatibility workflow and this RELEASE handover. No other role's handover or implementation was edited.

### Next owner actions

1. **PHX-QA:** independently review the exact application-image selector, symlink/hard-link defenses, byte-count/hash evidence and two-core matrix.
2. **PHX-MASTER / PHX-HARDWARE:** decide whether the matrix must pin the latest overall #327 HEAD `1d461f2...`; if yes, refresh the exact commit/blob contract in a separate task. Current ESP32 sketch blob is unchanged, but the current workflow does not checkout the latest overall PR head.
3. **PHX-PISONET:** fix its own uninitialized `$buildWorkflow` negative self-test; RELEASE reruns Windows after the owner correction.
4. **PHX-INFRA / COE integration / MASTER:** resolve the Bubblewrap namespace capability and keep COE #26 frozen until MASTER explicitly reopens it and provenance plus destination CI are accepted.

No merge, signing, release tag, publication, hardware flash, financial migration or customer deployment occurred. Independent protected signer/freshness witness, durable accounting and migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


## UTC01 terminal docs-head verification and reproducibility warning — 2026-11-20T01Z

**PR #291 docs head before this handover note:** `a27a1fc50b7448503cd0970a11106fbc67605ac5`  
**Exact source/test head:** `6a7e5c585bdbf86b1443e670b47af10e8391ef55`  
**HARDWARE checkout used by the matrix:** `9ef753a38226fcdf56b0903680a5110348027110`  
**ESP32 sketch blob:** `33081c5094ffdd19d935fc888d52ae01ff23325b`

### Terminal documentation-head Actions

- Compatibility run [#44654506216](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44654506216): **COMPLETED SUCCESS**, both exact-core jobs passed.
  - ESP32 core 3.3.13, job `136017305629`: selected `BlazePwifiVendo32.ino.bin`, 1,043,872 bytes, SHA-256 `58057db3c2a07553a4c2e84bba9f0427344aa7af801330f5f581d2b228bf6e7b`.
  - ESP32 core 4.0.0, job `136017306039`: selected `BlazePwifiVendo32.ino.bin`, 1,097,872 bytes, SHA-256 `a3a9ede7289936d728ba8ff2fb8512d952e6c405097e72c1e85b16adebb63f04`.
  - Both logs contain the exact application filename, byte count and SHA-256 marker. These are ephemeral CI build outputs, not published or signed artifacts.
- BlazePwifi docs-head run [#44654506263](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44654506263): **COMPLETED SUCCESS**, 26 successful jobs and 4 intentionally skipped. CI-0701 job `136017305816` passed the 8 Arduino archive-verifier tests, the application-image positive/negative controls and the exact compatibility contract; validation job `136017377986` passed. The four skipped jobs were production APK import, production signing handoff, release publishing and prerelease publishing.
- Windows run [#44654506207](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44654506207): handover PASS; PISONET-owned `negative-selftest.ps1` FAILED because `$buildWorkflow` is uninitialized; `publish-release` was SKIPPED. No PISONET file was changed.

### Reproducibility is not established

The source/test-head compatibility run [#44653465461](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44653465461) and the docs-head run [#44654506216](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44654506216) used the same pinned HARDWARE commit, same ESP32 sketch blob and same core versions. A Git comparison confirms the only commit between source/test head `6a7e5c5` and docs head `a27a1fc` changed this handover file only.

The application image sizes are identical between those runs, but the SHA-256 values differ:

| Core | Source/test-head SHA-256 | Docs-head SHA-256 |
|---|---|---|
| 3.3.13 | `9fba7a8126505359ff5fe3f424f43e509b3e57152b83a183a138110c6bf96c2e` | `58057db3c2a07553a4c2e84bba9f0427344aa7af801330f5f581d2b228bf6e7b` |
| 4.0.0 | `9cdfbd5191cf4ce30325ba0497f66c136ae391c00271c22bd492a608fa1dec94` | `a3a9ede7289936d728ba8ff2fb8512d952e6c405097e72c1e85b16adebb63f04` |

The pinned ESP32 sketch source contains no `__DATE__`, `__TIME__` or `__TIMESTAMP__` tokens. The cause of the byte-level drift is **not established**; it may be a generated framework/toolchain/build-environment input, but no cause is asserted. The workflow currently retains only log hashes, not the binary bytes needed for a diff. Do not call this a reproducible build and do not reuse one run's digest as a stable release digest.

**Next release-owned action:** perform a controlled same-commit, same-toolchain double build and compare the exact application-image bytes; preserve both outputs long enough to identify the differing regions. Only then choose a deterministic-build correction. Do not modify HARDWARE source or add an unverified timestamp override.

### Live source and governance limits

- Current HARDWARE PR #327 head is `1d461f2c5fad1ea411ab89bab8d1a1f4e73dce1c`. Compared with the pinned `9ef753a...`, it is four commits ahead; the changed paths are two handover documents and two ESP8266 lab files. No ESP32 sketch path changed, so the pinned ESP32 subtree/blob remains the same; the workflow still does not checkout the latest overall #327 commit.
- MASTER #288 remains OPEN/DRAFT at `1bd30098d961b6dd2f0e971423ae8e4d36407f9b`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, and the BlazePwifi workflow route is `reimplementation-review`, not a blind copy.
- COE #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows QUEUED with zero jobs. COE #31 sandbox remains blocked by unprivileged Bubblewrap UID-map denial (exit 125); child #35 profile validation remains blocked because approved site-scoped RFC 4193 ULA authority is undefined.
- Canonical private Drive registry v11 was not retrievable through the authorized Library surface in this activation. A prior checkpoint metadata reference is not the registry itself; no older v3–v7 snapshot was substituted and no private identifiers or contents were copied.

PR #291 remains OPEN / DRAFT / UNMERGED. No merge, signing, release tag, publication, hardware flash, financial migration or customer deployment occurred. Independent protected signer/freshness witness, durable accounting/migration, QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC02 — current HARDWARE pin and clean double-build reproducibility gate (2026-11-20T02Z)

**Disposition:** release-owned compatibility source pin refreshed to the live PHX-HARDWARE #327 candidate; two independent clean builds are now compared byte-for-byte for each ESP32 core. The exact-source test contract passes. Both core matrix jobs correctly **FAIL CLOSED** because the two application images differ despite equal sizes. This reproduces a real build-reproducibility defect; it does not fix or explain it. PR #291 remains OPEN / DRAFT / UNMERGED. **PRODUCTION NO-GO.**

### Exact source identity and ownership

- Experiments PR #291 branch phoenix/release-publisher-isolation-20261115; base PR #242 734b89d9e7792247e8376335c3f3685500ab3f89.
- Exact source/test head at this checkpoint: c3ec59999f5b1e4aa16405ecb122f140a2c019f3.
- Release compatibility workflow now checks out current HARDWARE PR #327 head a2b7903b4009fd7182247e11a7d2954a79cb9bbd and independently verifies ESP32 sketch blob 1a4b8fba8df210201ae77f23bfef55674abfb59e.
- HARDWARE #327 is OPEN / DRAFT / UNMERGED, seven commits ahead of the previous Release pin. Its latest Full run [#44657641509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44657641509) passed ESP32 and ESP8266 target jobs but failed its validation job at QA-owned Missing poll signature check; this is not a Full CI pass.
- No HARDWARE source, QA fixture, CORE, PISONET, MASTER or shared interface file was changed by RELEASE.

### Test-first and implementation history

- Test-only commit [a86943e5](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a86943e541460cabeb4a4b968f561db6c490e47b) moved the expected source/blob to the live #327 candidate and added the double-build contract and negative controls. Expected RED [#44659060375](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659060375), CI-0701 job 136032459214: failed because the workflow still carried the old HARDWARE SHA/blob; 23 provenance and 8 Arduino archive tests passed.
- Helper [ada348f9](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ada348f97619adcf7cd071f5523590cadd477997) added a no-follow, regular-file-only byte comparator. It rejects symlinks, hard links, wrong filenames, same-inode inputs and empty images; on mismatch it records both lengths, both SHA-256 values and the first differing byte offsets/values.
- Workflow [7644a359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7644a3591c381bf349f63af5d480b48b0cce7ba1) refreshed the exact HARDWARE checkout/blob and performs two arduino-cli compile --clean invocations with the same FQBN, core, source directory and build path, preserving separate output directories for comparison. [b6d4dc5f](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b6d4dc5f2815e86f18838f589ced7ab27ed4fdbf) explicitly creates the build workspace.
- Test-harness corrections: [3582c0e7](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3582c0e72d72c6c18b5776fbb916d0a32bb3c0f4) expects the two --clean application-verifier invocations; [c3ec5999](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c3ec59999f5b1e4aa16405ecb122f140a2c019f3) counts each output directory once in the compile command and once in its image verifier.
- Intermediate CI-0701 failures are retained as test-harness failures, not product failures: [#44659213363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659213363) rejected the old compile-command assertion after --clean was introduced; [#44659321100](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659321100) rejected the initial output-dir occurrence count. Both assertions were corrected above.

### Exact-source CI-0701

[Current-head BlazePwifi run #44659445870](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659445870), job 136033761990: **SUCCESS**.

- Release concurrency: 8/8 PASS.
- Provenance: 23/23 PASS.
- Arduino CLI archive verifier: 8/8 PASS.
- Application-image positive/negative controls: PASS.
- Reproducibility helper positive/negative controls: PASS.
- Exact-source compatibility workflow contract: PASS.
- Board-core pin guard: PASS.

Markers in the exact job log include PHX-ESP32-APP-IMAGE-TESTS-PASS, PHX-ESP32-REPRODUCIBILITY-TESTS-PASS and PHX-RELEASE-ESP32-COMPAT-PASS.

### Controlled double-build result — reproducibility FAILED CLOSED

First exact-source matrix run [#44659321097](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659321097), workflow commit b6d4dc5f:

| Core | Each image size | First SHA-256 | Second SHA-256 | Result |
|---|---:|---|---|---|
| ESP32 3.3.13 | 1,043,904 bytes | 84b0a343c91554b377999242463e5dde37106a76bec6022771c017c78244a323 | 23a4660f1a8922db19b9e358e9c3aac300dee8677573f02c45b37d16fa199e9e | FAIL |
| ESP32 4.0.0 | 1,097,936 bytes | e7aef0be304477ee907a8617b951b88bfc3b8b1c85ccd490672c7a934de2f838 | 91aa9934f1e2a47e1463b0665e642276a787eb8cf14a5f02a275efd5a8229140 | FAIL |

Both jobs verified the exact HARDWARE commit and sketch blob, verified the pinned Arduino CLI archive, installed the requested core, completed both compile commands, and passed the per-build application-image filename/size/SHA checks. The final comparator rejected both pairs because the bytes differed. Sizes were equal within each core.

- Core 3.3.13 job 136033495338: first differing byte at offset 176; first 16 differing byte pairs were logged.
- Core 4.0.0 job 136033494905: first differing byte at offset 176; first 16 differing byte pairs were logged.
- The current #291 head's follow-on matrix [#44659445469](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659445469) is IN PROGRESS at this handover; it is not yet counted as a terminal result.
- The current full BlazePwifi run #44659445870 is also IN PROGRESS beyond CI-0701. Its ESP32 and ESP8266 target jobs have passed; validation and remaining platform jobs have not yet reached terminal status.

The current HARDWARE ESP32 sketch was checked for __DATE__, __TIME__ and __TIMESTAMP__; none of those tokens occurs in the sketch. The differing field's cause is **not established**. The offset may be in generated image metadata, but no attribution is made. No SOURCE_DATE_EPOCH, timestamp override, linker patch or other unverified normalization was applied. The two binary files remained present in their separate runner output directories until comparison; they were not uploaded or published.

**Do not use either digest as a stable release manifest/checksum value. Do not call the build reproducible.** Next RELEASE task: capture the two binaries or an expanded bounded byte/section diff around offset 176, identify the exact differing field and its producer, then add a test before any deterministic-build correction. Keep the current source pin until #327 advances; refresh exact commit/blob before future claims.

### Other exact-head failures and owner routing

- Windows run [#44659445453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44659445453): handover PASS; PISONET-owned negative-selftest.ps1 failed because $buildWorkflow is uninitialized; publisher skipped. RELEASE changed no PISONET file.
- MASTER #288 current head at this checkpoint: b6dd2dc3a81bd51ce82f60efaf06b5b7d236d23c. OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY; RELEASE route is .github/workflows/blazepwifi-build.yml → COE .github/workflows/pisowifi-ci.yml, reimplementation-review.
- Experiments #242 remains 734b89d9e7792247e8376335c3f3685500ab3f89; #291 is c3ec59999f5b1e4aa16405ecb122f140a2c019f3, OPEN / DRAFT / UNMERGED, with zero independent submitted reviews.
- COE #26 remains b382d233ff06c8791b1028bed3c617cc7b670d12; #31 remains 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; child #35 remains a draft. COE's approved site-scoped ULA authority and Bubblewrap-capable unprivileged runner remain unresolved; #26 integration staging remains frozen.
- Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json was not surfaced by authorized Library search; only older v3–v7 snapshots appeared. No older registry was substituted and no private contents/identifiers were copied.

No merge, signer use, tag, publication, hardware flash, payment migration or customer deployment occurred. Protected signer and independent freshness witness, durable financial accounting/migration, independent QA/MASTER approval, approved production binaries, 150 physical power cuts and 30-device/24-hour soak remain unproven. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC03 — ESP32 app-descriptor-aware reproducibility diagnostics

**Current PR #291 source/test head:** 773e3acbbb0f76cca01d8204485019d4026de792  
**Branch:** phoenix/release-publisher-isolation-20261115  
**Base:** #242 734b89d9e7792247e8376335c3f3685500ab3f89  
**State:** OPEN / DRAFT / UNMERGED. No submitted independent PR reviews.

### Scope and commits

Only two release-owned source files changed for this task:
- .github/scripts/verify_esp32_reproducible_build.py
- .github/scripts/test_phx_release_esp32_core_compatibility.py

Test-first and correction history:
- [5acd4071](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5acd407145c03866671fe43ba77fe5c0a559f6e5) added synthetic ESP32 app-descriptor controls; expected RED on build [#44666735775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44666735775), CI-0701 job 136057732007, because the old helper had no descriptor classification/range output.
- [89acdf45](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/89acdf453a65160ce9e70eed028952e2ce6486f2) first added descriptor-aware parsing and complete contiguous diff ranges. Its CI-0701 attempt exposed a reversed segment-header read size/offset; this was a helper implementation defect, not a product failure.
- [fd931364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/fd9313648d663aa3ceed4d1dd1eb70c8928f3a23) corrected the segment-header read to 8 bytes at image offset 24.
- [773e3acb](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/773e3acbbb0f76cca01d8204485019d4026de792) isolated the invalid-app-descriptor-magic regression so only the magic field changes in that control.

The helper now validates the ESP image header, first segment length and ESP_APP_DESC_MAGIC_WORD; reports total differing bytes, all bounded contiguous ranges, first differing bytes and both embedded app_elf_sha256 values; and classifies only a verified field-only difference as ESP_APP_DESC_APP_ELF_SHA256_ONLY. It still rejects every non-identical image. It does not normalize, zero, ignore or bless any changed field. No raw firmware/ELF binaries were uploaded or published.

### ESP-IDF field provenance

The field location is now source-grounded, not inferred from the first differing byte:
- esp_image_header_t is 24 bytes and the first segment header is 8 bytes; the application descriptor therefore begins at image offset 32.
- ESP_APP_DESC_MAGIC_WORD is 0xABCD5432.
- esp_app_desc_t places app_elf_sha256[32] 144 bytes into the descriptor, so its image offset is 176.
- Espressif documents this field as the SHA-256 of the application ELF.

Checked official Espressif headers for [ESP-IDF v5.1](https://github.com/espressif/esp-idf/blob/v5.1/components/esp_app_format/include/esp_app_desc.h), [v5.5.2](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_app_format/include/esp_app_desc.h) and [v6.0](https://github.com/espressif/esp-idf/blob/v6.0/components/esp_app_format/include/esp_app_desc.h), plus the [ESP-IDF App Version documentation](https://docs.espressif.com/projects/esp-idf/en/v5.1/esp32/api-reference/system/misc_system_api.html#app-version). The field layout is consistent across these versions.

### Exact-source CI-0701

Both exact-head build jobs passed the release-owned guard suite at 773e3ac:
- Push [#44667029029](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667029029), CI-0701 job 136058699974: SUCCESS.
- PR [#44667034403](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034403), CI-0701 job 136058717961: SUCCESS.

Both logs report:
- Shared workflow action-pin guard: 52 invocations PASS.
- ESP32 compatibility workflow action-pin guard: 3 invocations PASS.
- SoftTimer workflow action-pin guard: 6 invocations PASS.
- Provenance negative controls: 23/23 PASS.
- Application-image positive/negative controls: PASS.
- Reproducibility helper controls (including ELF-SHA-only, other-content and invalid-magic classifications): PASS.
- Exact ESP32 source/blob and 3.3.13/4.0.0 workflow contract: PASS.

### Actual exact-source matrix — still non-reproducible

PR [#44667034127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034127) and push [#44667029116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667029116) both completed FAILURE at the byte-for-byte reproducibility gate for both ESP32 core versions. The current HARDWARE sketch source is exact a2b7903b4009fd7182247e11a7d2954a79cb9bbd; sketch blob 1a4b8fba8df210201ae77f23bfef55674abfb59e.

PR-run diagnostics:
| Core / job | Image size | First SHA-256 | Second SHA-256 | Different bytes / ranges |
|---|---:|---|---|---|
| 4.0.0 / 136058898186 | 1,097,936 | b6a41e1833c1d0389d081008e19231424fee6ee3262b6fcd862243b57394275e | 374463ab53e0002352bb4451a5b2df51b0cc421e3efd67a549f22d33151588bd | 67; 176-207, 9716-9717, 1097903-1097935 |
| 3.3.13 / 136058898493 | 1,043,904 | 0ecb1f2212f9494be0e84804ba9375b960654ae0cf851dd4c125a2df72675f47 | 97f88c4ba5e6f8d455482db168ffe49b58c2d31d4673abf66450fca5537b4235 | 67; 176-207, 9670-9671, 1043871-1043903 |

Both are classified OTHER_IMAGE_CONTENT_DIFF, not ELF-SHA-only. The embedded ELF hashes differ, but there are also 2-byte in-image differences and a trailing 33-byte difference range. The cause of the small in-image ranges and trailer is not established; no timestamp override, linker change, metadata normalization or binary substitution was attempted.

The independent push run reproduced the failure with different SHA pairs:
- Core 4.0.0 job 136058907154: 67 differing bytes; ranges 176-207, 9714-9714, 9716-9717, 1097903-1097919, 1097921-1097935.
- Core 3.3.13 job 136058907560: 68 differing bytes; ranges 176-207, 9668-9668, 9670-9671, 1043871-1043903.

The app descriptor parser therefore explains the stable offset-176 field, but the actual firmware mismatch is broader. Neither core image is accepted as reproducible; none of these digests may be used as release SHA256SUMS entries.

### Broader build and unrelated owner failures

- Push full build [#44667029029](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667029029): CI-0701 PASS; validate job 136058773377 SUCCESS (all 131 steps); all 14 firmware/platform target jobs SUCCESS; Android SUCCESS; update bundle SUCCESS; most v0.4 simulations SUCCESS. x86 simulation and Android-emulator simulation were still IN_PROGRESS at last read. Production sign handoff, release publisher and prerelease publisher SKIPPED. Overall run remains IN_PROGRESS; no terminal overall success claimed.
- PR full build [#44667034403](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034403): CI-0701 PASS; validate job 136058788582 SUCCESS; all target jobs and Android SUCCESS; update bundle and most simulations SUCCESS. x86 and Android-emulator simulations were still IN_PROGRESS at last read. Production sign/publish jobs SKIPPED. Overall run remains IN_PROGRESS.
- Windows [#44667034154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034154): PISONET-owned negative-selftest.ps1 still fails because $buildWorkflow is unset; publish-release SKIPPED. No PISONET file changed.

### Ownership, provenance and next action

- Current #291 head 773e3acbbb0f76cca01d8204485019d4026de792, base #242 734b89d9e7792247e8376335c3f3685500ab3f89; PR OPEN/DRAFT/UNMERGED.
- MASTER #288 current head 965d786ec0b0f00e04ccef27182228f1f2f869f0; coordination/phoenix/OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 keeps the route DRAFT_REVIEW_ONLY and PHX-RELEASE → COE #26 as reimplementation-review. No migration was performed.
- #242 head 734b89d9; #327 head a54ea8a6 is four commits ahead of source/test commit a2b7903b, but those commits touch only the HARDWARE workflow and handover, not the ESP32 sketch; the tested source/blob pin remains valid.
- COE #26 head b382d233; COE #31 head 59ed44d0. ULA authority and Bubblewrap-capable unprivileged runner remain external packaging blockers.
- Repository rulesets API returned []; the connected GitHub integration could not read classic branch protection for the slash-containing branch. Effective branch protection is UNKNOWN, not assumed.
- Canonical private Drive registry v11 was not surfaced by the authorized Library search; older v3–v7 snapshots were not substituted or copied.
- No independent PR reviews are recorded on #291 or MASTER #288.

**Next PHX-RELEASE action:** inspect the small in-image ranges (9716-9717 on core 4.0.0; 9670-9671 on core 3.3.13) and the trailing 33-byte image region without publishing raw binaries; correlate them with the actual ESP image/ELF section map before changing any build flags. Preserve the fail-closed comparator until a source-grounded deterministic correction passes both cores.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment. Protected signer/freshness witness, durable financial accounting/migration, independent QA/MASTER approval and physical 150 power-cut / 30-device 24-hour soak remain unproven. **PRODUCTION NO-GO.**


### UTC03 post-checkpoint exact-run readback — 2026-11-20T03:27Z

This follow-up supersedes only the earlier "in progress at last read" status for the two source/test-head full BlazePwifi runs; it does not change the compatibility matrix result.

- Exact source/test-head push full build [#44667029029](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667029029), HEAD 773e3acbbb0f76cca01d8204485019d4026de792: **COMPLETED SUCCESS**. Job counts: 26 SUCCESS, 0 FAILURE, 4 SKIPPED. The four skipped jobs are signed-APK import, production sign handoff, release publishing and prerelease publishing. The 26 successes include CI-0701, all 131 validation steps, all 14 target jobs, Android, update bundle and all v0.4 simulations. This is hosted CI/simulation evidence only.
- Exact source/test-head PR full build [#44667034403](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034403), same HEAD: **CANCELLED** after a successor push. Job counts: 24 SUCCESS, 0 FAILURE, 4 SKIPPED, 2 CANCELLED. The cancelled jobs were v0.4 x86 and Android-emulator simulations. Do not call this PR run a terminal green result.
- Exact source/test-head compatibility PR [#44667034127](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667034127) and push [#44667029116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667029116) both completed FAILURE because both ESP32 core legs failed byte-for-byte reproducibility. This remains the controlling release-integrity result; a green broader build does not override it.
- New documentation-head workflows after handover commit 0c7293af: compatibility [#44667764065](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667764065) IN_PROGRESS; Windows [#44667764212](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667764212) IN_PROGRESS after handover PASS; BlazePwifi [#44667764115](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44667764115) IN_PROGRESS with docs-head CI-0701 job 136061249189 PASS and remaining target/validation jobs queued at last read. No docs-head terminal outcome is claimed.

No new runtime, firmware, shared-interface, PISONET or hardware source change was made in this follow-up.


### PHX-RELEASE UTC04 — refresh stale ESP32 compatibility source pin (2026-11-20T04Z)

**Role lock:** PHX-RELEASE / 2026-11-20T04Z. **PR #291:** OPEN / DRAFT / UNMERGED. **Production:** NO-GO.

#### Exact upstream source identity

- MASTER #288: `965d786ec0b0f00e04ccef27182228f1f2f869f0`; route manifest remains `DRAFT_REVIEW_ONLY`.
- Experiments #242: `734b89d9e7792247e8376335c3f3685500ab3f89`.
- Experiments #291 branch: `phoenix/release-publisher-isolation-20261115`; base #242; pre-change head `d0ac4dba3bdd04e3f16ee2b3d3bd44d47a5f203c`.
- HARDWARE #327 current docs/PR head: `bcd7757663ae6c1227b4fed65ad8a9674a35bd31`. Its latest firmware source commit on that branch is `369007bcbc684a0923a586e991f3aa0667cda105` (`fix(hardware): hold poll-drain inhibit through pulse sampling`), which changes the ESP32 and ESP8266 sketches plus hardware-owned labs.
- Exact ESP32 sketch Git blob at source commit `369007b`: `1458f32881d3b340f1101dd0215618b54c1b688b`.

#### Test-first release-owned correction

The compatibility workflow still pinned HARDWARE `a2b7903b4009fd7182247e11a7d2954a79cb9bbd` / sketch blob `1a4b8fba8df210201ae77f23bfef55674abfb59e`. The current #327 firmware sketch had advanced; old compatibility results therefore did not qualify the current candidate.

- Test-first commit [`873adbb6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/873adbb6e8dec2b248fb9acaa08711ffe7488600) updates only the release-owned static contract to require exact source `369007b` and sketch blob `1458f328`.
- Expected RED [push run #44673015632](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44673015632), CI-0701 job `136078171421`: **FAIL as expected** at `RELEASE-TOOLCHAIN exact ESP32 core compatibility workflow contract`; log explicitly reports both new expected values missing from the still-old workflow. Action-pin, concurrency, provenance and Arduino archive-verifier steps passed before the intended failure; downstream target jobs were skipped.
- Workflow correction [`55b07821`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/55b0782107f37dae28e2a27ddbae32008920f2b4) changes only the release-owned compatibility workflow's source checkout ref, independent expected source SHA, sketch blob pin and source label. Read-only permissions, immutable action pins, two-core matrix and fail-closed reproducibility comparison remain unchanged.
- Exact current source/test workflow HEAD: `55b0782107f37dae28e2a27ddbae32008920f2b4`.

#### Exact-head CI status at handover

- Compatibility PR [#44673130966](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44673130966): PENDING.
- Compatibility push [#44673124219](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44673124219): PENDING.
- BlazePwifi full PR [#44673131079](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44673131079): QUEUED; CI-0701 job `136078552460` PASS, target/validation jobs QUEUED.
- Windows PR [#44673130939](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44673130939): IN_PROGRESS; not a RELEASE source change.
- Previous old-pin compatibility run [#44670365345](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44670365345) failed both ESP32 cores at byte-for-byte reproducibility comparison after compilation. It is historical evidence for the old source pin only, not a result for current #327 source `369007b`.
- Previous broader full build [#44670365371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44670365371) completed with successful validation/target/simulation jobs and production sign/publish jobs skipped. It does not override strict compatibility failure and is not production evidence.

No current-source reproducibility pass is claimed until both pending matrix legs complete. Preserve the comparator; do not normalize embedded hashes or change compiler/linker flags without identifying the source of byte drift.

#### Ownership / external blockers

- MASTER #288's `OWNERSHIP_ROUTES.json` routes `.github/workflows/blazepwifi-build.yml` to COE `.github/workflows/pisowifi-ci.yml` as `reimplementation-review`; manifest is `DRAFT_REVIEW_ONLY`. No workflow copy/migration performed.
- COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`: five PR workflows remain queued, zero jobs executed.
- COE #31 head `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 head `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`. #31 shared/case guards passed, mandatory Bubblewrap sandbox failed closed on runner namespace setup; no unsandboxed fallback. No current #35 head Actions run was returned.
- #266 still requires cleanup-first ownership discipline; its RELEASE task is limited to build/version/manifest/signing configuration in #242. No broad move/deletion or teammate handover rewrite.
- Canonical private Drive registry v11 was not surfaced by exact-title/content search or the bounded Library listing. Older v3–v7 snapshots were not substituted; no private contents or identifiers copied to GitHub.

#### Next action

Read terminal outcomes of #44673130966/#44673124219 at exact source/test SHA `55b07821`. If both compile but reproducibility still fails, preserve the failure and continue byte/ELF-section diagnosis on the new exact HARDWARE source. PHX-QA independently reviews the release pin and compatibility evidence; PHX-MASTER retains migration and release-gate authority.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC05 — ESP32 segment-aware reproducibility diagnostics (2026-11-20T05Z)

**Role lock:** PHX-RELEASE/2026-11-20T05Z.  
**PR:** [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), OPEN / DRAFT / UNMERGED.  
**Branch:** phoenix/release-publisher-isolation-20261115.  
**Base:** #242 at 734b89d9e7792247e8376335c3f3685500ab3f89.  
**Exact source/test HEAD:** a7ad93d4a55292a3e281a6fe2d9ba46543a23070 (the following handover commit is documentation-only).

### Bounded RELEASE-owned change

The strict two-clean-build comparator previously reported differing byte ranges but did not map those ranges to ESP image segments or the image footer. Added a read-only ESP image layout parser and segment-aware difference descriptions to .github/scripts/verify_esp32_reproducible_build.py.

- Test-first commit [4ca429b3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4ca429b3a4517de1436652ea9438715e1d0b0228) adds synthetic two-segment image cases for the observed offsets, a second segment, checksum byte and appended SHA.
- Implementation commit [a7ad93d4](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a7ad93d4a55292a3e281a6fe2d9ba46543a23070) reports segment file ranges, load addresses, segment-relative offsets, checksum offset and optional appended SHA range.
- The comparator remains byte-for-byte and fail-closed. No hash field is normalized, no build flag is changed, and no binary is uploaded.
- The test-only commit did not return a separate pre-fix RED Actions run; do not claim an observed RED. Final exact-head CI did execute the added tests successfully.

The parser follows Espressif's documented 24-byte image header, 8-byte segment headers, padded checksum byte and optional appended 32-byte SHA. References: [ESP-IDF App Image Format](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/app_image_format.html) and [esptool Firmware Image Format](https://docs.espressif.com/projects/esptool/en/latest/esp32/advanced-topics/firmware-image-format.html).

### Exact upstream source and core matrix

- HARDWARE #327 current branch/docs head: b6304208d65548a9cfe371504badf03ae3e15dcf; exact source/test head: 2f89326d5b555ffdb2bfaba0a404483d665aa614.
- ESP32 firmware source commit pinned by RELEASE: 369007bcbc684a0923a586e991f3aa0667cda105; sketch blob: 1458f32881d3b340f1101dd0215618b54c1b688b.
- A live compare from 369007b to current #327 head is eight commits ahead; changed paths are the Hardware quarantine workflow, ESP8266 poll-loop labs and Hardware handovers. The ESP32 sketch blob remains unchanged. The existing pin is still the exact ESP32 firmware-source commit; it was not blindly refreshed to a documentation-only head.
- Main BlazePwifi build core pins remain ESP8266 3.1.2 and ESP32 3.3.13; CI guard enforces both. The separate ESP32 compatibility probe tests 3.3.13 and 4.0.0. 4.0.0 is a compatibility probe, not an approved production release target.

### Exact-source Actions

- Release guard suite: [BlazePwifi build #44680793729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44680793729), CI-0701 job 136103425511: **PASS**. Logs show PHX-ESP32-REPRODUCIBILITY-TESTS-PASS, PHX-RELEASE-ESP32-COMPAT-PASS and RELEASE-TOOLCHAIN-PASS (ESP8266 3.1.2 / ESP32 3.3.13).
- Main build run #44680793729: validation and all 14 target/platform jobs **PASS**; update bundle and ESP simulations observed **PASS**. At the last read Android emulator and x86 simulation were still in progress, so the overall run was not yet terminal. Production signing/import/publish jobs were skipped.
- Strict compatibility: [#44680793567](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44680793567) **FAILED CLOSED on both cores** after both independent compiles and exact application-image admission succeeded.

Core 4.0.0, job 136103828979:
- Image size: 1,098,176 bytes for each build.
- SHA-256: f2d09a65d61977a1b7347595d22ba6d8478bb7701f4c83316ba08b0291c4b0df vs 28de82f40333bf7efd0d23ca21fe7cef8ffd0d615cbb8f872c4b7a336719ca8e.
- 67 differing bytes: 176-207, 9716-9717, 1098143-1098175.
- The non-descriptor drift is in segment 0, load address 0x3f400020, segment-relative offsets 9684-9685.
- Six segments were parsed. Checksum offset 1098143; appended SHA 1098144-1098175.

Core 3.3.13, job 136103829429:
- Image size: 1,044,096 bytes for each build.
- SHA-256: fe0d13a41a4b9095f6d718edc96db0033658f1d99992ccdd251d921e9933f8b3 vs 6f5926336794e44484be1bb9bc08546b703c75effd908205305888cf43332217.
- 71 differing bytes: 176-207, 9668-9668, 9670-9671, 761836-761838, 1044063-1044095.
- Non-descriptor drift: segment 0 at load address 0x3f400020, segment-relative offsets 9636 and 9638-9639; segment 3 at load address 0x400d0020, segment-relative offsets 565196-565198.
- Six segments were parsed. Checksum offset 1044063; appended SHA 1044064-1044095.

The 32-byte app_elf_sha256 field and final checksum+appended-SHA footer change along with the underlying image. They are not accepted as independent root causes. The persistent non-descriptor segment bytes are the next diagnostic target. No root cause is claimed.

### Other exact-head CI and owner routing

- Windows [#44680793680](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44680793680): handover **PASS**; Windows build **FAIL** at negative-selftest.ps1 because $buildWorkflow is uninitialized; publisher **SKIPPED**. This is PISONET-owned; no PISONET file changed.
- MASTER #288 current branch head: 2a2f6bf0926676250aed007c1a001605173bb6c0. OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY; BlazePwifi build workflow route is reimplementation-review. No migration.
- COE #26 head b382d233ff06c8791b1028bed3c617cc7b670d12: five workflows remain queued, zero jobs executed.
- COE #31 head 59ed44d0b911e176f1a95b9cf5585ef811ffd31b: shared validation and case-collision jobs pass; mandatory Bubblewrap sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) fails closed at bwrap: setting up uid map: Permission denied (exit 125). No unsandboxed fallback.
- #242 base remains 734b89d9e7792247e8376335c3f3685500ab3f89; #266 cleanup-first remains open. No inherited CORE, RENTAL, PISONET, HARDWARE, QA or MASTER files changed in this activation.
- Private Drive registry v11 was not found after full Library pagination. Older v3–v7 snapshots were not substituted. The owner prompt 06_RELEASE_ENGINEERING(1).txt is present and was read; no private registry contents were copied or published.

### Next owner action

At the next activation, preserve or print the first and second .elf outputs before the second clean build overwrites the build directory, then compare ELF files and use the pinned Xtensa objdump -h section table to map the non-descriptor segment offsets to exact ELF sections. Keep the current byte comparator fail-closed. Do not apply timestamp, linker or hash-normalization workarounds until the changing section/field is identified.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC08 — POSIX nm size-less row parser correction (2026-11-20T08Z)

**PR #291:** OPEN / DRAFT / UNMERGED. Branch `phoenix/release-publisher-isolation-20261115`. Base `734b89d9e7792247e8376335c3f3685500ab3f89`.

### Exact defect and test-first correction
- Current source/test head at activation start: `df189b079a89f52b6152e613f5f5a32817c05f04`.
- The exact-head compatibility run [#44697909618](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44697909618) failed both ESP32 core legs at the release-owned ELF-symbol inspector test; compilation and reproducibility comparison were skipped.
- The existing size-less POSIX nm regression fixture had an over-escaped newline. Test-only commit [`1cf6bbcc`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1cf6bbccd89f0e5b3a1c41dc2763d8938897dc19) corrected the fixture to a real newline. Expected RED was reproduced in [#44701544520](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44701544520): both cores fail at the intended parser case with `ValueError: malformed POSIX nm row`; 9/10 symbol tests pass, and the size-less row is the one error.
- Implementation commit [`a7ed8ff0`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a7ed8ff01c5b7d2a6621cbe31eb45063fef4bf88) makes the POSIX nm size column optional and maps both an absent size and the explicit `?` size marker to `None`. It preserves strict rejection of malformed rows and 32-bit overflow.

### Exact-source Actions at source/test HEAD `a7ed8ff01c5b7d2a6621cbe31eb45063fef4bf88`
- Compatibility [#44701833387](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44701833387): both exact HARDWARE source legs installed the requested core, passed section-inspector tests and passed all 10 ELF-symbol tests. Both then **FAILED CLOSED** at the unchanged byte-for-byte application-image comparison. This is not a parser failure.
  - ESP32 4.0.0 / esp-x32 2512: `.flash.rodata`, 9,480 nm symbols; observed drift addresses map to the section but have no containing sized symbol (`NEAREST_ONLY`). Nearest symbols are absolute linker boundary symbols around `0x3f400150`.
  - ESP32 3.3.13 / esp-x32 2610: `.flash.rodata`, 9,148 nm symbols; observed addresses have no containing sized symbol (`NEAREST_ONLY`), nearest `_flash_rodata_start` at `0x3f400120`.
  - The reproducibility comparator still reports `OTHER_IMAGE_CONTENT_DIFF`; core 4.0.0 differs at 176–207, 9716–9717 and footer 1098143–1098175 (67 bytes). Core 3.3.13 differs at 176–207, 9668, 9670–9671 and footer 1044063–1044095 (68 bytes). No root cause is established; comparator remains fail-closed.
- Full BlazePwifi [#44701833382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44701833382): **COMPLETED SUCCESS**, 26 successful jobs, 0 failed, 4 production import/sign/publish jobs skipped. All target jobs, validation, ESP32/ESP8266 builds, Android, update bundle and simulations passed. Hosted CI/simulation only.
- Windows [#44701833371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44701833371): handover PASS; package-parity self-test PASS; build-windows **FAIL** at PISONET-owned `negative-selftest.ps1` because `$buildWorkflow` is unset; publisher SKIPPED. No PISONET file was changed by PHX-RELEASE.

### Current ownership / provenance
- MASTER PR #288: `737f42b40cc25c718aa1f1964165f53a50988bd0`; current `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`, PHX-RELEASE route `reimplementation-review`. No migration or route promotion.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 remains OPEN/DRAFT at this handover predecessor.
- COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, five workflows queued / zero jobs. COE #31 remains OPEN/DRAFT at `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; hardware/shared and case-collision jobs pass, while Bubblewrap namespace preflight fails closed with UID-map Permission denied (exit 125).
- Private Drive registry v11 was not surfaced by exact-name Library search; older v3–v7 and October registry snapshots were not substituted. No private contents or identifiers were copied to GitHub.
- PR #291 has no submitted independent review. Its changed-file set includes pre-existing PISONET paths; this activation changed only the two RELEASE-owned ELF-symbol files and this RELEASE-owned handover.

### Next action
Preserve both exact-build ELF files separately and inspect the pinned Xtensa `.flash.rodata` section bytes around the observed file offsets against the section's actual file offset, linker map and read-only symbol table. The current nm output supplies only nearest linker-boundary symbols, not containing symbols. Do not infer ownership from a nearest predecessor, modify compiler/linker flags, normalize hashes, or weaken byte equality until the changed bytes are attributed. PHX-QA should independently review the parser and diagnostics; PHX-MASTER retains migration/release gate authority.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC09 — exact ELF section-byte comparison added (2026-11-20T09Z)

**PR #291:** OPEN / DRAFT / UNMERGED.  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test HEAD:** `c468f1a6d5a9d365c1088998f6ddc650ae104ca2`  
**Hardware firmware source:** `369007bcbc684a0923a586e991f3aa0667cda105`  
**Exact ESP32 sketch blob:** `1458f32881d3b340f1101dd0215618b54c1b688b`

### One release-owned task

Added a bounded exact-section byte comparator for the two preserved ELF outputs. It parses each build's pinned `objdump -h` section table independently and uses each ELF's own file offset; it does not assume section offsets are identical between ELF files.

- Test-first commit: [`f655c784`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f655c784116a028d301d6275a3dc992d842dafc5).
- Expected RED: [compatibility run #44710641754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710641754), both core jobs failed at the new synthetic tests because the initial comparator reused the first ELF's section file offset for the second ELF. Logs show the two intended offset-independence regressions failed; four other validation cases passed.
- Corrected helper/workflow/test commit: [`c468f1a6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c468f1a6d5a9d365c1088998f6ddc650ae104ca2).
- New files: `.github/scripts/compare_esp32_elf_sections.py` and `.github/scripts/test_compare_esp32_elf_sections.py`.
- Existing read-only compatibility workflow now compares `.flash.appdesc` and `.flash.rodata` from the separately preserved first/second ELF files. Section differences are diagnostic output only; the exact application-image comparator remains the authoritative fail-closed gate.
- Seven synthetic tests cover identical content at different ELF offsets, exact differing ranges, app-descriptor comparison, missing/duplicate sections, layout mismatch and truncated section bounds.

### Exact-source Actions at source/test HEAD `c468f1a6d5a9d365c1088998f6ddc650ae104ca2`

- PR compatibility [#44710956522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710956522): **COMPLETED FAILURE** on both cores at the strict application-image comparator. Exact HARDWARE source/blob, Arduino CLI archive, installed core, section tests, symbol tests and all seven new section-comparison tests passed.
- Both new section-comparison tests report `.flash.appdesc` **IDENTICAL** between the two ELF builds. The final binary's embedded `app_elf_sha256` and appended checksum/SHA are downstream image-generation values, not differences in the ELF app-descriptor section itself.
- ESP32 core 3.3.13 / esp-x32 2610:
  - `.flash.rodata`: 131,668 bytes; SHA-256 `97d292cda41c983dd080de78ed88cf777c4376032047cece087cd2ba7e274133` vs `ce0cd3e785acb8601ac34d8a98d0674678f89e4e6b72c80f5d40c50a3e3d7b6b`.
  - Four differing bytes at section offsets 9379–9380 and 9382–9383; ELF file offsets 13763–13764 and 13766–13767. Observed byte pairs are ASCII digits `29` / `30` and `51` / `26`.
  - Final application image: 1,044,096 bytes each; 69 differing bytes, ranges 176–207, 9667–9668, 9670–9671 and 1044063–1044095.
- ESP32 core 4.0.0 / esp-x32 2512:
  - `.flash.rodata`: 140,536 bytes; SHA-256 `e0389f2c3eee8cb8d67d17c6f0da7381da3b767087018bb62471d2d6b63db25a` vs `e1e0d7189cf3a1c5c3b1d17afc2b0415f374917f24dffe5d8b41a96b2e524032`.
  - Three differing bytes at section offsets 9426 and 9428–9429; ELF file offsets 13810 and 13812–13813. The differing bytes are also ASCII digits.
  - Final application image: 1,098,176 bytes each; 68 differing bytes, ranges 176–207, 9714, 9716–9717 and 1098143–1098175.
- The `.flash.rodata` differences are consistent with a time-like string changing between the two compile invocations, but the surrounding bytes and exact producer have not yet been captured. This is a hypothesis, not an established root cause. The earlier source scan covered the sketch only; it did not prove that all included framework/library inputs are free of `__TIME__`, `__DATE__` or generated timestamps.
- Push-triggered duplicate compatibility run [#44710949354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710949354) was automatically queued for the same source/test commit; it is not a separate implementation or acceptance claim.

### Other exact-head CI

- Full BlazePwifi [#44710956565](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710956565): CI-0701 and validation **PASS**; ESP8266, ESP32, Android, all observed target builds and update bundle **PASS**. At this handover update, browser, x86, ESP8266 and Ruijie simulation jobs were still running. Production signing/import/publish jobs were **SKIPPED**; overall run not yet terminal and is not claimed as SUCCESS.
- Windows [#44710956654](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710956654): handover and package-parity PASS; PISONET-owned `negative-selftest.ps1` **FAIL** because `$buildWorkflow` is unset; publisher **SKIPPED**. No PISONET source was changed.

### Current ownership / cross-repository blockers

- MASTER #288 current head: `129aa462322fb0bff2aedec524f42bb829fd7f4b`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY`; PHX-RELEASE build workflow route remains `reimplementation-review`. No migration or shared-interface change.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`, based on `blazepwifi-v0.6.0-audit-foundation@6d4c9b487af4d768c4d7627654d119417fcc6e00`. #291 remains OPEN/DRAFT on that #242 head.
- COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`; five PR workflows remain queued with zero jobs executed.
- COE #31 is now extended by release-owned child PR #35 at `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`. Its latest source/docs CI reports 118 packaging tests PASS / 2 intentional skips, but 10/10 profile admission fails closed because approved site-scoped RFC 4193 ULA authority is unset; mandatory Bubblewrap sandbox also fails closed because the hosted runner lacks usable Bubblewrap/UID-map setup (exit 125). No firmware artifact or hardware acceptance.
- COE #44 ULA installation-first-boot draft is at `582fd5d5e83e36b36546ac28534740298ba94af4`; synthetic UCI section-type tests passed, but site-level ULA authority remains unresolved and the mandatory sandbox is unavailable. It does not authorize integration.
- COE #31/#35/#44 remain draft-only; no cross-repository files were copied or modified.
- Private Drive registry v11 was not surfaced by the authorized exact-name Library search. Older registry snapshots were not substituted and no private contents were copied to GitHub.
- PR #291's existing changed-file set includes pre-existing PISONET-owned paths; this UTC09 task changed only RELEASE-owned scripts/workflow and this RELEASE handover. No PISONET, CORE, RENTAL, HARDWARE, QA or MASTER implementation was modified.

### Next release-owned action

Capture a bounded ASCII/hex context window around the `.flash.rodata` offsets above from each preserved ELF, then identify the exact string and producer. Search the complete pinned source/framework/library inputs and generated build files for compile-time or generated time values. Do not add timestamp overrides, `SOURCE_DATE_EPOCH`, linker changes, hash normalization or comparator exceptions until the producer is identified and a source-linked regression exists.

No merge, real-key signing, release tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


### UTC09 docs-head CI follow-up — 2026-11-20T09:35Z

This is a documentation-only reconciliation; no source/test or workflow implementation changed after `c468f1a6d5a9d365c1088998f6ddc650ae104ca2`.

- Windows docs-head [#44711905542](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44711905542) completed **FAILURE**: handover PASS; PISONET-owned `negative-selftest.ps1` fails because `$buildWorkflow` is unset; publisher SKIPPED. This does not belong to PHX-RELEASE.
- Compatibility docs-head [#44711905559](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44711905559): both exact-core jobs are still IN PROGRESS. No terminal result is claimed.
- Full-build docs-head [#44711905643](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44711905643): CI-0701 PASS; ESP8266 and observed target jobs are passing; validation, ESP32, Android and several target jobs remain in progress. Production signing/import/publish jobs are skipped. No overall result is claimed.
- Push-triggered compatibility docs-head [#44711898736](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44711898736) remains IN PROGRESS; push full-build docs-head [#44711898823](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44711898823) remains PENDING. These are automatic push/PR event duplicates, not additional implementation work.
- Source/test-head PR compatibility [#44710956522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710956522) and push compatibility [#44710949354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710949354) both completed FAILURE at the strict application-image comparator after all diagnostic tests passed.
- Source/test-head full build [#44710956565](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710956565) was CANCELLED by the successor docs-only push: 24 successful jobs, 2 simulation jobs cancelled, 4 production jobs skipped, zero failed jobs. It is not an overall SUCCESS.


## PHX-RELEASE UTC11 — deterministic ESP32 compile-time metadata and wiring regression guard

**Date:** 2026-11-20 UTC11  
**PR:** [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test HEAD:** `0d4a3c9213a253d64f54de296af306386f915d82`

### Owned change

The existing exact-source ESP32 compatibility workflow already applied a deterministic `SOURCE_DATE_EPOCH` derived from the pinned HARDWARE commit. This activation added a release-owned static regression guard in `.github/scripts/test_phx_release_esp32_core_compatibility.py` so that the working configuration cannot silently regress.

- Commit [`0d4a3c92`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0d4a3c9213a253d64f54de296af306386f915d82): requires the compiler capability probe before compilation; derives the epoch from `git -C hardware-source show -s --format=%ct HEAD`; requires `SOURCE_DATE_EPOCH`, `LC_ALL=C`, and `TZ=UTC` before both clean builds; verifies both source-date-epoch scripts remain in push and pull-request path filters.
- The guard runs three synthetic negative mutations and requires rejection: missing epoch export, wall-clock epoch, and export moved after the first clean build.
- No firmware source, workflow behavior, package payload, signer, publisher permission, or other role-owned source was changed in this activation.

### Exact-source CI

- Compatibility [run #44728953554](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44728953554): **SUCCESS**. Both ESP32 core jobs passed, including the new wiring guard.
- Core 4.0.0 job `136263448366`: `PHX-ESP32-SOURCE-DATE-EPOCH-WIRING-PASS`; compiler probe PASS; `PHX-ESP32-ELF-SECTION-COMPARE-IDENTICAL`; `PHX-ESP32-REPRODUCIBILITY-PASS`. Image size 1,098,464 bytes; repeated-build SHA-256 `edbe9ed6b3539ee9b6339fb6df3db7095d95a51531e7621ddd6a7e7299555f4d`.
- Core 3.3.13 job `136263462181`: same PASS states. Image size 1,044,352 bytes; repeated-build SHA-256 `8e5198060ebb4b7a0fdbb85561933d00ff3fa5472e2e3d85a7f5a0eba7a26b36`.
- Both builds used `SOURCE_DATE_EPOCH=1795166700`, derived from exact HARDWARE source commit `dc02efea6590045155bf50f16fdd2d3924f6b415`. The pinned core metadata source is `cores/esp32/chip-debug-report.cpp` blob `c462e8a8bab21910c6e499d7450c3e8903196836` (line 215), with `main.cpp` blob `fee28f101a5ce8ba686bba518f1f964ff5a485f9` calling the report at lines 55 and 58. The helper confirmed the compiler honors the pinned epoch for both core versions.
- The previously differing `.flash.rodata` and final application images are now identical between the two clean builds for each core. This is hosted-CI reproducibility evidence, not approval of production binaries.

### Current surrounding state and ownership

- HARDWARE #327 live head: `89442ce681df965b16c80f73055236a0d842fe0c`. The release pin remains `dc02efea...` with sketch blob `849a2c63...`; comparison from the pinned source commit to the current #327 head shows only two host-lab paths and three handover paths changed, not the pinned ESP32 sketch. The #327 Full workflow still fails at the QA-owned stale positive `Missing poll signature check`; focused Hardware jobs pass. No physical hardware acceptance is inferred.
- BlazePwifi full build [run #44728953513](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44728953513): at the last read, all firmware/platform targets and validation had passed; four simulation jobs remained in progress. Production import/sign/publish jobs were skipped. This run is not recorded as terminal success.
- Windows [run #44728953500](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44728953500): failed in the PISONET-owned SoftTimer negative self-test; publisher skipped. The PISONET owner retains the `$buildWorkflow` correction. No PISONET path was edited.
- MASTER #288 head `3d75d241263576c3913a6388a26d9d761324a957`; `OWNERSHIP_ROUTES.json` remains `DRAFT_REVIEW_ONLY` (blob `e4db324315a1b3543f3ec17a148fbf960170fcb29`). Release workflow migration remains `reimplementation-review`; no cross-repository copy or migration was performed.
- COE #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`, with five workflows queued and zero jobs executed. COE #31 remains parent `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 is at `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`. Child #35 case-collision passes; mandatory Bubblewrap sandbox fails closed and shared Hardware/Contracts CI fails. Site-scoped ULA authority and an approved namespace-capable runner remain absent.
- The accumulated #291 diff still contains PISONET-owned SoftTimer test paths and separate BlazePwifi handover/ledger paths outside this activation's scope. This activation changed only the release-owned compatibility test. PISONET and MASTER must resolve those existing PR paths before integration; no rehome or ownership transfer was attempted.
- No independent submitted reviews on #291 were present at this read.

### Provenance and evidence limits

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not surfaced by a complete recursive Library listing. A November 9 checkpoint referencing v11 and older v5–v7 snapshots appeared, but none was substituted for canonical v11. No private contents were copied into GitHub.

**Disposition:** The deterministic two-core reproducibility gate is now PASS at exact source/test HEAD. This is not a release approval. No merge, real-key signing, release tag, publication, hardware flash, payment migration, or customer deployment occurred. **PRODUCTION NO-GO.**

**Next:** PHX-QA reviews the exact-source reproducibility evidence and existing stale Hardware positive fixture; PHX-PISONET fixes its own negative self-test; PHX-MASTER resolves ownership contamination and migration review. PHX-RELEASE refreshes the in-progress full-build run before any further release-source change.

## PHX-RELEASE UTC12 — runtime Arduino board-core identity admission

**Date:** 2026-11-20 UTC12  
**PR:** #291 — OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/release-publisher-isolation-20261115  
**Base #242:** 734b89d9e7792247e8376335c3f3685500ab3f89  
**Exact source/test head:** b73a7cfc2ffbc78e3101fbe92cd2c8ab4c9f7f61

### Owned correction

The BlazePwifi build already pinned ESP8266 esp8266:esp8266@3.1.2 and ESP32 esp32:esp32@3.3.13, but the build steps only printed arduino-cli core list. The workflow recorded the pinned version as provenance without failing if the actually installed package row did not match.

- Test guard commit [3cb58926](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3cb589267fe76f1c5cc2bbd776317c690caba437) extends .github/scripts/test_release_artifact_action_pins.py to require, for both board-core install steps, capture of arduino-cli core list, exact package-row extraction, exact installed-version comparison, a fail-closed error marker, and a verified identity marker.
- Expected RED: [BlazePwifi run #44735144744](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44735144744), CI-0701 job 136284533347, at test-only commit 3cb58926. The immutable-action pin step failed with ten intended assertions: five missing runtime checks for ESP8266 3.1.2 and five for ESP32 3.3.13. The ESP32 compatibility and SoftTimer Windows runs triggered from that test-only head were cancelled/failed separately; no green claim is attached to them.
- Workflow implementation commit [a92a3e12](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a92a3e123a0991323400e02b64a04e93660aeda4) added the runtime package-row checks. A source readback caught an over-escaped shell newline before final validation; an intermediate contents update produced no blob change. Final correction [b73a7cfc](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b73a7cfc2ffbc78e3101fbe92cd2c8ab4c9f7f61) restores the single-backslash printf newline format so awk receives real line-separated core-list rows. The final exact-source logs confirm the output and installed version.
- Only RELEASE-owned .github/scripts/test_release_artifact_action_pins.py, .github/workflows/blazepwifi-build.yml, and this RELEASE handover were changed. No firmware, product handover, CORE, RENTAL, PISONET, HARDWARE, QA, MASTER or COE source was edited.

### Exact-source GitHub Actions

- [BlazePwifi build #44735445100](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44735445100), exact head b73a7cfc: CI-0701 job 136285544527 PASS, including immutable action pins, release provenance/checksum tests, ESP32 compatibility workflow contract and board-core pin checks. ESP8266 job 136285621065 PASS: actual arduino-cli core list showed esp8266:esp8266 3.1.2, emitted RELEASE-TOOLCHAIN-CORE-PASS, compiled, wrote exact-source provenance and uploaded its CI artifact. ESP32 job 136285621053 PASS: actual list showed esp32:esp32 3.3.13, emitted its identity marker, compiled, wrote provenance and uploaded its CI artifact. Android and all 11 firmware target jobs also PASS.
- The full build is FAILURE, not overall PASS: 15 jobs succeeded, 13 were skipped, and one failed. The failed validate job 136285620949 stopped at the mandatory product handover freshness gate because .github/workflows/blazepwifi-build.yml is newer than experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md (last checkpoint 0f2e67b3794b2469523b51ced2ba4ec4a334e84b). Static validation was skipped after the gate. The product handover/CURRENT_STATE/CHANGE_LEDGER are outside this activation's RELEASE-owned scope; PHX-CORE must refresh its own live record before a new full validation. Simulations, update bundle, candidate gate, production import/sign/publish and preview publishing were skipped.
- [Exact-source ESP32 compatibility #44735445022](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44735445022) SUCCESS on both core legs for exact HARDWARE source dc02efea6590045155bf50f16fdd2d3924f6b415, sketch blob 849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e, and SOURCE_DATE_EPOCH=1795166700. Core 3.3.13 produced identical two-build application images of 1,044,352 bytes, SHA-256 8e5198060ebb4b7a0fdbb85561933d00ff3fa5472e2e3d85a7f5a0eba7a26b36. Core 4.0.0 produced identical two-build images of 1,098,464 bytes, SHA-256 edbe9ed6b3539ee9b6339fb6df3db7095d95a51531e7621ddd6a7e7299555f4d. Both passed exact hardware source/sketch verification, compiler epoch probes, ELF section/symbol tests and the strict image comparator. This is hosted-CI reproducibility evidence, not production binary approval.
- [Windows run #44735444878](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44735444878) FAILURE at the shared product handover freshness gate before the PISONET build; build and publisher skipped. The prior exact-head Windows run [#44730774194](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44730774194) passed handover but failed the PISONET-owned negative-selftest.ps1 because $buildWorkflow was unset; PHX-PISONET owns that file and correction. No PISONET path was edited.

### Current cross-role source and governance state

- MASTER #288 is OPEN/DRAFT at 7f804b678ed81fa633edc87c60ae08433fbbcc89; route manifest blob e4db324315a1b3543f3ec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY. The .github/workflows/blazepwifi-build.yml destination route is reimplementation-review. No workflow migration, copy or merge.
- HARDWARE #327 is OPEN/DRAFT at e759f70325523fe6429170e8b4396e335f574c8b, 17 commits ahead of the pinned firmware source. Compare shows only two host-lab files and five handover files changed; current ESP32 sketch blob still equals 849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e. Focused relay/output [#44732030253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44732030253) and quarantine/readback [#44732030243](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44732030243) PASS. Full [#44732030246](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44732030246) FAILS at QA-owned Missing poll signature check; board compile jobs passed, downstream release/simulation jobs skipped. The firmware source pin remains blob-identical, but QA's inherited positive fixture must be corrected by PHX-QA.
- COE integration #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows are queued with zero jobs. COE release parent #31 remains 59ed44d0b911e176f1a95b9cf5585ef811ffd31b; child #35 is 7b9706d898fb5f36c6ed96504aefd04dc59bdc1b. Child #35 case-collision [#44617783021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617783021) PASS; mandatory ImageBuilder sandbox [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) FAILS CLOSED because Bubblewrap is unavailable; shared/firmware [#44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050) FAILS at all-profile admission because approved site-scoped RFC 4193 ULA authority is unset. Packager default APPROVED_SITE_ULA_PREFIX=None is intentionally fail-closed; no synthetic or invented production prefix was substituted. PHX-CORE/COE + MASTER own ULA authority/interface; PHX-INFRA owns the approved namespace-capable runner.
- PR #291's accumulated 26-file diff still contains pre-existing product handover paths and PISONET-owned PublisherMockCli.ps1 / negative-selftest.ps1. This activation did not touch them. PHX-MASTER must resolve ownership contamination before integration; PHX-PISONET and PHX-CORE retain their own files. No independent PR reviews were present.
- Canonical private Drive registry v11 was not surfaced through authorized Library search; older snapshots were not substituted and no private content was copied to GitHub.

### Next exact actions

1. PHX-CORE updates its product handover/CURRENT_STATE/CHANGE_LEDGER for the RELEASE workflow change, without RELEASE editing CORE-owned paths; then rerun the full exact-head validation.
2. PHX-PISONET fixes its own $buildWorkflow negative-selftest variable; PHX-QA fixes the stale positive poll-signature fixture without weakening default-deny; PHX-MASTER resolves #291's existing cross-role path contamination and keeps the route review-only.
3. PHX-RELEASE retains the new runtime core-version admission guard and requests independent QA/Master review. Do not duplicate the completed core pin/runtime assertion or two-core reproducibility work.

No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC13 — race-safe ESP32 application-image admission

**Date:** 2026-11-20 UTC13  
**PR:** #291 — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/release-publisher-isolation-20261115\`  
**Base #242:** \`734b89d9e7792247e8376335c3f3685500ab3f89\`  
**Exact source/test HEAD:** \`55abc784617ea83fc01a44c55e4f6d473a95764a\`

### Defect and correction

The release-owned \`.github/scripts/verify_esp32_application_image.py\` previously validated the final output directory with path-based operations. A symlinked ancestor component could still resolve to a real final directory, and the directory path was not pinned/rechecked while the image was being hashed.

The verifier now:
- rejects \`..\` path components and requires descriptor-relative, no-follow directory operations;
- walks every absolute path component using \`O_DIRECTORY | O_NOFOLLOW\` and \`dir_fd\`;
- pins the output directory and parent descriptors;
- enumerates and opens the application candidate relative to the pinned directory;
- rejects symlinked or hard-linked/non-regular image files;
- compares file identity before/open/after hashing; and
- verifies the output directory still resolves to the pinned device/inode and has not changed before returning the digest.

Only two RELEASE-owned files changed for this task:
- \`.github/scripts/verify_esp32_application_image.py\`
- \`.github/scripts/test_phx_release_esp32_core_compatibility.py\`

No CORE, RENTAL, PISONET, HARDWARE, QA, MASTER, firmware, or product handover path was modified.

### Test-first history and failed attempts retained

- Test-only commit [\`5721524c\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5721524c3ba8adc2acb411f7c8f9bf2a783e63ce) introduced parent-symlink and directory-replacement regressions. [Push run #44742907835](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44742907835) failed at the new negative assertions: the old verifier accepted the symlinked ancestor and replacement case. The first race-injection mechanism was not yet proven; later test-only refinements replaced it with a deterministic final-identity-check injection.
- Initial implementation [\`34d04287\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/34d04287f7ad01368b1e7f23bc77af2c4561e7ab) failed [#44743160562](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743160562) because the image-file open referenced a no-follow flag outside its helper scope. Narrow correction [\`74b87d49\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/74b87d494c063e30e190a7fe161cd71fd11229d5) uses the already-verified \`os.O_NOFOLLOW\` flag.
- Intermediate race-test injection attempts were not triggered and correctly failed closed: [#44743348602](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743348602), [#44743575415](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743575415), and [#44743715182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743715182). The test was refined to replace the real directory immediately before the final descriptor-identity check.
- Final test commit [\`55abc784\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/55abc784617ea83fc01a44c55e4f6d473a95764a) produced the final source/test HEAD. The CI marker confirms both parent-symlink and directory-swap controls now pass.

### Exact-source GitHub Actions

**Release compatibility — terminal PASS on both events**
- Push [#44743856372](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743856372): SUCCESS; ESP32 core 3.3.13 and 4.0.0 jobs both PASS.
- PR [#44743865929](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743865929): SUCCESS; ESP32 core 3.3.13 and 4.0.0 jobs both PASS.
- Both use exact HARDWARE source commit \`dc02efea6590045155bf50f16fdd2d3924f6b415\`, sketch blob \`849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e\`, and \`SOURCE_DATE_EPOCH=1795166700\`. Current HARDWARE #327 head \`85c54fea5136da182b173c4d89900b22cf61d2b5\` still has the same sketch blob; the pin was not changed.
- Core 3.3.13: two clean images, 1,044,352 bytes each, SHA-256 \`8e5198060ebb4b7a0fdbb85561933d00ff3fa5472e2e3d85a7f5a0eba7a26b36\`; section comparator reports identical.
- Core 4.0.0: two clean images, 1,098,464 bytes each, SHA-256 \`edbe9ed6b3539ee9b6339fb6df3db7095d95a51531e7621ddd6a7e7299555f4d\`; section comparator reports identical.
- Both jobs passed exact source/sketch verification, Arduino CLI archive verification, epoch/compiler checks, ELF section/symbol inspection, the new application-image parent-symlink/directory-swap tests, and strict two-build comparison.

**Full BlazePwifi build — still IN PROGRESS at this handover update**
- Push [#44743856415](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743856415): CI-0701 job 136313996893 PASS; validate job 136314102831 PASS; ESP32, ESP8266, Android, all firmware target jobs, and update bundle PASS. Most simulations PASS. x86 QEMU simulation and Android emulator were still running. Production import/sign/publish jobs SKIPPED. Overall run has no terminal conclusion yet.
- PR [#44743866052](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743866052): CI-0701 job 136314032055 PASS; validate job 136314136188 PASS; ESP32/ESP8266, all firmware target jobs, Android build and update bundle PASS. Remaining x86/OrangePi PC/Android-emulator simulation jobs were still running. Production import/sign/publish jobs SKIPPED. Overall run has no terminal conclusion yet.
- These in-progress simulation jobs are not counted as passing or failing, and no overall Full SUCCESS is claimed.

**Out-of-scope Windows result**
- [Windows run #44743865923](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44743865923): handover PASS; package parity and its synthetic self-test PASS; PISONET-owned \`negative-selftest.ps1\` fails because \`$buildWorkflow\` is unset; publisher SKIPPED. PHX-PISONET owns the correction. No PISONET file was changed.

### Live governance and provenance

- MASTER #288: head \`52b7c023ea414e2df504e943425a9d0957c8c2d9\`; \`OWNERSHIP_ROUTES.json\` remains \`DRAFT_REVIEW_ONLY\`. PHX-RELEASE workflow route remains \`reimplementation-review\`; no migration/copy/merge was performed.
- Experiments #242: head/base \`734b89d9e7792247e8376335c3f3685500ab3f89\` / \`6d4c9b487af4d768c4d7627654d119417fcc6e00\`.
- Experiments #291: current source/test head \`55abc784617ea83fc01a44c55e4f6d473a95764a\`; OPEN / DRAFT / UNMERGED. Its accumulated diff still contains pre-existing non-RELEASE paths; those were not touched or rehomed.
- COE integration #26: head \`b382d233ff06c8791b1028bed3c617cc7b670d12\`; eight PR/push workflow runs remain QUEUED with zero executed jobs.
- COE #31 parent: \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`; child #35: \`7b9706d898fb5f36c6ed96504aefd04dc59bdc1b\`. Child case-collision guard PASS; mandatory Bubblewrap sandbox FAILS CLOSED; Hardware/shared-contract CI FAILS. No sandbox success or ULA authority is inferred.
- Canonical private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` was not present in the complete recursive Library listing (1,222 entries). Only the prior checkpoint metadata pointer surfaced. No older registry was substituted and no private contents were copied into GitHub.
- No independent PR #291 review was present at the live review read.

### Next owner actions

1. PHX-QA independently reviews the new descriptor/path admission tests and exact-source compatibility evidence.
2. PHX-PISONET fixes its own \`$buildWorkflow\` negative-self-test variable.
3. PHX-MASTER resolves the accumulated #291 cross-owner path contamination and confirms the review-only migration route.
4. PHX-RELEASE refreshes the two in-progress full-build runs before deciding whether any additional release-source change is needed; do not repeat the completed path-safety or two-core reproducibility tests.

**Production remains NO-GO.** No merge, signing, release tag, publication, hardware flash, payment migration, or customer deployment occurred.


## PHX-RELEASE UTC13 — canonical SHA256SUMS path admission

**Date:** 2026-11-20 UTC13  
**PR:** #291 — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base #242:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test HEAD:** `dcb905333c8963fb139eeeefa72471738c874fb8`

### Defect and bounded correction

`.github/scripts/write_build_provenance.py` checked `PurePosixPath.parts` for empty and dot components after constructing a `PurePosixPath`. That constructor normalizes interior `.` components, repeated separators and trailing separators before the check. The checksum parser therefore accepted multiple textual names that collapse to one canonical artifact path.

The normalizer now checks the raw slash-separated components before constructing `PurePosixPath`. It rejects interior dot components, empty components/repeated separators, trailing separators and repeated leading dot prefixes. One leading `./` remains accepted for normal `sha256sum` compatibility. No artifact bytes, hashes, build inputs, source pins or production gates were changed.

Only two RELEASE-owned source/test files changed for this task:
- `.github/scripts/test_build_provenance.py`
- `.github/scripts/write_build_provenance.py`

### Test-first history, including test-authoring correction

- Initial test commit [`cfd301f1`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/cfd301f1eecdfe9417c3f8949cf22f5bae6ef740) had an over-escaped newline fixture. [Run #44746263315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746263315) failed at the malformed fixture (`nested/payload.bin\\n`) before exercising the intended path assertions. This is recorded as a test-authoring error, not defect evidence.
- Fixture correction [`e112839f`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e112839fbd9cad3adeaa7c5a6cb3801abb3d4baa) used an actual newline escape. Expected RED [PR run #44746430882](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746430882) and push [#44746421472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746421472) then failed exactly at the four non-canonical path subcases: `nested/./payload.bin`, `nested//payload.bin`, `nested/`, and `././nested/payload.bin`. The canonical leading-`./` positive case and the other 23 tests passed.
- Source correction [`dcb90533`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dcb905333c8963fb139eeeefa72471738c874fb8) validates raw path components before path-object normalization.

### Exact-source GitHub Actions

- Push/full run [#44746545580](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746545580): CI-0701 completed SUCCESS. The release provenance step reports 24 tests PASS, including the new canonical-path regression. At the latest inspection, validation, Android build, ESP32, ESP8266, all OpenWrt target builds and update bundle were PASS; 24 of 30 jobs were successful, four production import/sign/publish jobs were SKIPPED, and two simulations remained IN_PROGRESS (Android emulator and x86 QEMU). The overall run had no terminal conclusion; do not call the Full run SUCCESS.
- PR compatibility [#44746554825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746554825): SUCCESS; ESP32 core 3.3.13 and 4.0.0 both passed exact HARDWARE source/sketch verification, pinned toolchain checks, ELF inspection and two-clean-build reproducibility.
- Windows [#44746554630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44746554630): handover PASS; package parity and synthetic package self-test PASS; PISONET-owned `negative-selftest.ps1` fails because `$buildWorkflow` is unset; publisher SKIPPED. PHX-PISONET owns this correction. No PISONET file was changed.

### Live governance and cross-repository provenance

- MASTER PR #288 head `52b7c023ea414e2df504e943425a9d0957c8c2d9`; `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`. PHX-RELEASE route is `.github/workflows/blazepwifi-build.yml` → COE `.github/workflows/pisowifi-ci.yml`, kind `reimplementation-review`. No workflow migration/copy/merge occurred.
- Experiments #242 remains OPEN / DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 remains OPEN / DRAFT / UNMERGED at `dcb905333c8963fb139eeeefa72471738c874fb8`.
- The accumulated #291 diff still contains pre-existing non-RELEASE paths: CORE `PROJECT_HANDOVER.md`, `CHANGE_LEDGER.md`, `CURRENT_STATE.md`, and PISONET `PublisherMockCli.ps1` / `negative-selftest.ps1`. They were not changed or rehomed by PHX-RELEASE; MASTER must reconcile ownership before integration. No independent PR #291 review was present at the live review read.
- COE integration #26 remains at `b382d233ff06c8791b1028bed3c617cc7b670d12`; eight push/PR workflows remain QUEUED with zero executed jobs.
- COE #31 remains parent `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap but failed at unprivileged UID-map setup (`Permission denied`, exit 1). COE #35 head `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`; sandbox [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) fails closed because Bubblewrap is not installed; shared/hardware CI also fails. COE #44 head `582fd5d5e83e36b36546ac28534740298ba94af4`; its sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) also fails closed because Bubblewrap is not installed, while its shared CI and case-collision guard pass. #44 is based on older #35 head `1a5be48d2845781b0b07bad39a37f8440cea4d4f`, not current #35 `7b9706d8`; do not infer it is reconciled or integrated.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not present in the complete recursive Library listing (1,422 entries). No older registry snapshot was substituted; no private file contents were copied to GitHub.

### Next actions and limits

1. PHX-RELEASE refreshes the two in-progress full-build simulations and the latest PR-triggered full run before reporting a terminal Full result.
2. PHX-PISONET fixes its own `$buildWorkflow` negative-self-test variable.
3. PHX-MASTER reconciles #291's accumulated CORE/PISONET path contamination and confirms the review-only migration route.
4. PHX-QA independently reviews release manifest path admission and exact-source evidence.
5. Registry custodian restores authorized read-only access to canonical v11.

No CORE, RENTAL, PISONET, HARDWARE, QA or MASTER implementation was modified. No merge, real-key signing, release tag, publication, hardware flash, real payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC14 — reject Windows drive-qualified SHA256SUMS paths

**Date:** 2026-11-20 UTC14  
**PR:** #291 — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/release-publisher-isolation-20261115`  
**Base #242:** `734b89d9e7792247e8376335c3f3685500ab3f89`  
**Source/test commit:** `0db99526477dd81f94d3f446165f90fc90defdbe`

### Defect

The SHA256SUMS normalizer already rejected POSIX absolute paths, traversal, repeated separators, backslashes and dot-segment aliases. It still accepted drive-qualified strings such as `C:/Windows/System32/kernel32.dll`, `C:relative/payload.bin` and `z:/payload.bin`, because `PurePosixPath` does not treat Windows drive syntax as absolute.

A manifest consumed by Windows tooling could reinterpret these names as drive-absolute or drive-relative paths. This is a cross-platform manifest portability and path-boundary defect, not a claim that the current Linux descriptor-relative verifier escaped its pinned artifact root.

### Test-first evidence

- Test commit [`41feea83`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/41feea83e5d9510236abaa80d311abba686896d7) adds three drive-prefix negative cases.
- Expected RED: [push Actions #44752458273](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752458273), CI-0701 job `136343546813`. The provenance suite ran 24 tests: 21 passed and exactly the three new drive-prefix cases failed because `ProvenanceError` was not raised. The Full workflow failed at this intended test; downstream jobs were skipped. This is the reproduced regression, not a product-build failure.

### Correction

- Implementation commit [`0db99526`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0db99526477dd81f94d3f446165f90fc90defdbe) rejects a leading ASCII drive designator (`^[A-Za-z]:`) after the permitted single leading `./` normalization and before `PurePosixPath` construction.
- No artifact payload, digest algorithm, source pin, toolchain, signer, publisher permission or production gate changed.
- Only RELEASE-owned source/test paths were changed for this defect: `.github/scripts/test_build_provenance.py` and `.github/scripts/write_build_provenance.py`.

### Exact-source verification

- [Push/full run #44752661476](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661476): CI-0701 job `136344233077` COMPLETED SUCCESS. Exact-source release provenance suite: **24/24 PASS**, including the three new Windows drive-prefix rejection cases; toolchain pin guard PASS. At this handover update the overall Full workflow remains IN_PROGRESS: validation job `136344431673` and several target builds/simulations are still running. ESP8266, Orange Pi PC, Orange Pi Zero3 and Orange Pi Zero target jobs have completed SUCCESS. Do not claim overall Full SUCCESS yet.
- [ESP32 compatibility #44752661483](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661483): both core jobs are IN_PROGRESS; no terminal result claimed.
- [Windows release #44752661501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661501): handover PASS; build-windows FAIL at the PISONET-owned `negative-selftest.ps1` with `The variable '$buildWorkflow' cannot be retrieved because it has not been set.`; publisher SKIPPED. PHX-PISONET owns this correction; no PISONET path was changed.

### Current governance and provenance

- MASTER #288 head `962e1179aae8f49551f151bf4721e1524f690c38`; base main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; all 128 changed paths are under `coordination/phoenix/`. The current `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` remains `DRAFT_REVIEW_ONLY`; the PHX-RELEASE workflow route is `reimplementation-review`, not a copy/move command.
- Experiments #242 remains OPEN/DRAFT at `734b89d9e7792247e8376335c3f3685500ab3f89`; #291 remains OPEN/DRAFT/UNMERGED. Its accumulated 26-path diff still includes pre-existing CORE handover paths and PISONET test paths. No such path was changed in UTC14. No independent PR #291 review is submitted; MASTER must resolve ownership contamination before integration.
- COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, with five queued workflows and zero executed jobs. COE #31 remains parent `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; child #35 `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`; #44 `582fd5d5e83e36b36546ac28534740298ba94af4` is based on an older #35 head and is not reconciled.
- COE #31 sandbox run [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) installed Bubblewrap but failed the unprivileged UID-map probe: `bwrap: setting up uid map: Permission denied`, exit 125. Child #35 [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877) fails closed because Bubblewrap is absent (exit 125); child #44 [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) also fails closed because Bubblewrap is absent. No unsandboxed fallback was introduced.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not present in a complete recursive Library metadata listing of 1,422 entries. No older registry was substituted; no private registry content or identifiers were copied to GitHub.

### Next owner actions

1. PHX-RELEASE refreshes Full run #44752661476 and compatibility #44752661483 to terminal states; do not rerun the completed provenance test suite unnecessarily.
2. PHX-QA independently reviews the cross-platform manifest-path guard.
3. PHX-PISONET fixes `$buildWorkflow` in its own negative self-test.
4. PHX-MASTER reconciles the inherited CORE/PISONET paths in #291 and confirms the review-only workflow reimplementation route.
5. COE integration/PHX-INFRA provide an authorized bubblewrap-capable unprivileged user-namespace runner; CORE/MASTER must establish site-scoped ULA authority before the COE packager can progress.

No merge, signing, tag, publication, hardware flash, payment migration or customer deployment occurred. **PRODUCTION NO-GO.**


### UTC14 CI terminal-state correction — source/test and documentation heads

This addendum supersedes the earlier UTC14 observation that Full run #44752661476 was still in progress.

- Source/test commit `0db99526477dd81f94d3f446165f90fc90defdbe`, push run [#44752661476](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661476):
  - CI-0701 job `136344233077`: COMPLETED SUCCESS; exact provenance suite **24/24 PASS**, including all three new drive-prefix negative cases; toolchain pin guard PASS.
  - Overall Full run: **CANCELLED** after the subsequent handover-only commit `67da5dfc88dc481e39c69cb836f73d6860330aaa` superseded it. This is not an overall Full SUCCESS.
  - Completed target jobs before cancellation: ESP8266, x86_64, Orange Pi PC, Orange Pi Zero3, optional Orange Pi Zero, optional Orange Pi Zero2W, optional Orange Pi One Plus, optional Orange Pi PC2, optional Orange Pi PC Plus, optional Orange Pi Zero2 — all SUCCESS.
  - Validation, Android, ESP32, Orange Pi One, Ruijie, update bundle, simulations, signer handoff and publishers were cancelled; production import was skipped.
- ESP32 compatibility run [#44752661483](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661483): both core jobs remained IN_PROGRESS at the last source-head inspection; no terminal result claimed.
- Windows source-head run [#44752661501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44752661501): handover PASS; build-windows FAIL at PISONET-owned `$buildWorkflow` negative self-test; publisher SKIPPED.
- Handover-head runs triggered by commit `67da5dfc88dc481e39c69cb836f73d6860330aaa`: Full [#44753134011](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753134011) has CI-0701 SUCCESS and validation/targets still IN_PROGRESS; compatibility [#44753133883](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753133883) pending; Windows [#44753134031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44753134031) running. These are not terminal passes.

The SHA256SUMS drive-prefix defect is fixed at the source/test head and its exact provenance suite is green. Full-build and ESP32 compatibility acceptance remain pending until terminal documentation-head results. Do not duplicate the completed test or source correction.


## PHX-RELEASE UTC15 — reject checksum path line-boundary characters

**Date:** 2026-11-20 UTC15  
**PR:** #291 — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/release-publisher-isolation-20261115\`  
**Base #242:** \`734b89d9e7792247e8376335c3f3685500ab3f89\`  
**Starting PR head:** \`2db8b2cb65dc1e755b92e26364a6918d05b2da5f\`  
**Final source/test head:** \`60ee0d25bde9aba36f472f33c72149c45f5c3d08\`

### Defect and correction

The checksum path normalizer accepted POSIX filenames containing vertical tab, form feed, U+001C–U+001E, NEL, U+2028 and U+2029. Python \`str.splitlines()\` treats those characters as record boundaries when parsing the generated SHA256SUMS text. A single filesystem path could therefore be split into multiple textual records, making generated manifests ambiguous and non-round-trippable.

The normalizer now rejects those eight line-boundary characters in addition to the existing backslash, LF, CR and NUL exclusions. Canonical paths and the intentional single leading \`./\` remain supported. No digest algorithm, artifact bytes, build inputs, source pins, signer, publisher permission or production gate changed.

### Test-first and source history

- Test commit [\`91b8fcea\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/91b8fcea7392b0f22f1af1faf05376f4897152f0) initially placed the new method after the test runner; it was not executable as a test. This is a test-authoring error, not RED evidence.
- Intermediate test-layout corrections [\`602f9ae5\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/602f9ae5debe37ad71f20b2e13f6dbec492b2a9a) and [\`946c89ff\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/946c89ffad11648dc9a422de99d5108ca0dee4e5) left one correctly placed test method inside \`BuildProvenanceTests\`; exact readback confirms one method occurrence.
- Initial source commit [\`4935647a\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4935647a3d69e1d89bf72f99954fabed059afec7) over-escaped the Python string literals and did not preserve the prior one-backslash/LF/CR/NUL exclusions. It is superseded by the corrected source commit below; do not treat it as accepted.
- Final source correction [\`60ee0d25\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/60ee0d25bde9aba36f472f33c72149c45f5c3d08) uses actual Python escape literals for all 12 forbidden characters. Exact GitHub readback confirms the source block and test method placement.

### Verification limits

- A local focused Python reproduction of the exact normalizer logic passed: canonical leading \`./\` accepted; 12 forbidden characters rejected; seven previously guarded path-alias/drive cases rejected. This is a bounded local reproduction, **not** execution of the full repository suite.
- \`fetch_commit_workflow_runs\` for final source/test SHA \`60ee0d25bde9aba36f472f33c72149c45f5c3d08\` returned zero PR-triggered runs. The connected GitHub actions surface does not expose workflow dispatch; therefore no exact-source GitHub Actions RED or GREEN is claimed for this change.
- Prior baseline at PR head \`2db8b2cb65dc1e755b92e26364a6918d05b2da5f\`: Full BlazePwifi [\#44757444298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44757444298) SUCCESS (26 successful jobs; four production import/sign/publish jobs skipped); ESP32 compatibility [\#44757444336](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44757444336) SUCCESS (both core legs); Windows [\#44757444435](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44757444435) FAILURE in PISONET-owned \`negative-selftest.ps1\`, publisher SKIPPED. These runs predate the UTC15 source change and are not evidence for the new code.

### Governance and next action

- MASTER #288 current head at the opening audit: \`13c671fa727c8f02d846358c1cd011aec0e67ea9\`; route manifest blob \`e4db324315a1b3543fec17a148fbf960170fcb29\` remains \`DRAFT_REVIEW_ONLY\`. Release workflow migration is \`reimplementation-review\`; no migration/copy/merge occurred.
- Cleanup-first #266 remains a coordination checklist; release scope is limited to build/version/manifest/signing configuration.
- PR #291 still accumulates inherited CORE and PISONET paths. PHX-MASTER must reconcile ownership before integration; PHX-QA must independently review this new manifest guard.
- COE #26 remains frozen with five queued workflows and zero executed jobs. COE #31 sandbox fails at unprivileged UID-map setup; #35 sandbox fails closed because Bubblewrap is unavailable; #44 sandbox likewise fails closed and remains ancestry-diverged from #35. No unsandboxed fallback or arbitrary site ULA was introduced.
- Canonical private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` was not surfaced by exact-name Library search. The November 9 checkpoint and v6/v7 snapshots are historical provenance only; none was substituted and no private contents were copied to GitHub.

Next: obtain an authorized exact-head Actions run (or owner-provided CI result) for source/test SHA \`60ee0d25...\`, then have PHX-QA independently review. Keep #291 draft. No merge, signing, tag, publication, hardware flash, payment migration or customer deployment. **PRODUCTION NO-GO.**

## 2026-11-20 UTC16 — observed Arduino compiler provenance and isolated release tests

**Scope:** RELEASE-owned build provenance only. No product firmware, CORE, RENTAL, PISONET, HARDWARE, QA or MASTER source was modified.

### Defect and implementation

The exact-head CI preview artifacts previously emitted \`toolchain.compiler_version: null\` even though ESP8266/ESP32 builds had succeeded. The release provenance writer now obtains expanded Arduino build properties for the exact FQBN and local library search path, resolves the selected C and C++ compiler executables, invokes each with \`--version\`, and fails closed if \`compiler.path\`, \`compiler.c.cmd\`, \`compiler.cpp.cmd\`, an executable or a version string is missing.

The manifest now records:
- \`compiler_version\` (observed C++ compiler first line)
- \`compiler_c_version\`
- \`compiler_c_binary\` and \`compiler_cpp_binary\`
- \`compiler_version_source\`

Absolute runner paths are not serialized. The build's installed Arduino CLI version, pinned board-core version, FQBN and sketch remain recorded.

### Source/test/workflow commits

- Test-first assertions: [fa65373e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/fa65373e0410db281fff1fcb66883e75c3188239)
- Test fixture newline correction: [bc0d9884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bc0d9884a646d941d3f19b678af8da9d8ba14dfd)
- Compiler discovery and manifest fields: [f6dd4782](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f6dd4782bc06fa509230dd1175a70bcbb2e247b5)
- Pass the exact build library directories into provenance collection: [1267309e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1267309e2ead4d8b8c0afb85745ab51de94aca2b)
- Add isolated provenance job and its action-pin count: [501c3602](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/501c360299eaf4cda48453a8ad2cd8aa3129c34c), [f016732e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f016732e13f25ceaae8c97d83cfac1c6401f3106)
- Update the compatibility guard for the third read-only checkout: [93bbf19e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/93bbf19e610051977045d04e5acd54881c34c31c)

The isolated \`provenance\` job in \`.github/workflows/phx-release-esp32-core-compatibility.yml\` runs the provenance, Arduino CLI archive-verifier and immutable-action-pin regression suites independently of the product handover gate. It has read-only contents permission, a pinned checkout action and no publisher/signing permissions.

### Exact-source CI evidence

At exact PR head \`93bbf19e610051977045d04e5acd54881c34c31c\`, [Full run #44773037406](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773037406) reported:
- CI-0701: PASS; the release provenance suite ran **27 tests**, all PASS.
- Arduino CLI archive verifier: **8 tests**, all PASS.
- ESP32 compatibility workflow static contract: PASS after updating the expected checkout count to three.
- CI-0701 classified the source/test/workflow change as \`RUN_FULL\`, not docs-only.
- The main \`validate\` job failed closed at the CORE-owned product freshness gate before product validation: \`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md\` is older than the current source/workflow changes; last checkpoint \`a978cb4835c4de9d6b1e58f0db4c4887acae8b0c\`. RELEASE did not edit that CORE-owned file.
- ESP8266, ESP32 and OpenWrt target jobs were still running at the last inspection; no terminal result is claimed here.
- Windows run #44773037473 failed at the same CORE handover freshness gate; PISONET build and publisher were skipped.

The preceding exact-source build run [#44772444197](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44772444197) completed both ESP board jobs successfully and produced preview artifacts:
- ESP8266 artifact [#14647828087](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44772444197/artifacts/14647828087): installed core \`esp8266:esp8266@3.1.2\`; C and C++ compiler \`xtensa-lx106-elf-gcc/g++ (GCC) 10.3.0\`; all **10** SHA256SUMS entries matched the archived files.
- ESP32 artifact [#14648362103](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44772444197/artifacts/14648362103): installed core \`esp32:esp32@3.3.13\`; C and C++ compiler \`xtensa-esp-elf-gcc/g++ (crosstool-NG esp-14.4.0_20261030) 14.4.0\`; all **24** SHA256SUMS entries matched the archived files.

These are hosted CI preview artifacts and checksum readbacks, not approved production binaries or hardware evidence. The later compatibility workflow run [#44773037343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773037343) was pending behind an earlier compatibility matrix run at last inspection; its new isolated provenance job has no terminal result yet.

### Current ownership and blockers

- Experiments PR #291 remains OPEN / DRAFT / UNMERGED at \`93bbf19e610051977045d04e5acd54881c34c31c\`, based on #242 \`734b89d9e7792247e8376335c3f3685500ab3f89\`. Independent submitted reviews: none.
- The accumulated PR diff still includes inherited CORE product handover paths and PISONET Windows test paths. Those paths were not modified in this task and must be reconciled by MASTER/owners before integration.
- MASTER #288 is \`cf134056e7a2bef95c6a2b0727cad81e46e4de8a\`; ownership manifest remains \`DRAFT_REVIEW_ONLY\`, release workflow route remains \`reimplementation-review\`.
- COE #26 remains \`b382d233ff06c8791b1028bed3c617cc7b670d12\` with five queued workflows and zero jobs. COE #31 remains \`59ed44d0b911e176f1a95b9cf5585ef811ffd31b\`; its mandatory Bubblewrap sandbox failed closed at unprivileged UID-map setup (\`Permission denied\`, exit 125), while shared Hardware/Contracts CI and case-collision checks passed.
- The complete 1,422-entry Library metadata listing did not surface canonical \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\`; v5/v6/v7 are not substitutes. No private registry contents were copied.
- The earlier PISONET-owned negative self-test error (\`$buildWorkflow\` unset) remains outside RELEASE ownership; no PISONET file was changed.

**Next owner actions:** CORE must refresh its product handover and rerun the exact-head Full validation; PHX-MASTER must reconcile inherited CORE/PISONET paths and review the release route; PHX-QA must independently review compiler provenance and checksum admission; PHX-INFRA must provide a namespace-capable sandbox runner for COE #31.

**PRODUCTION NO-GO.** No merge, signing, tagging, publication, hardware flashing, financial migration or customer deployment occurred. Physical 150-power-cut and 30-device/24-hour acceptance remain untested.

### UTC16 follow-up — exact provenance workflow and docs-head status

The source/test head is \`93bbf19e610051977045d04e5acd54881c34c31c\`; the current PR documentation head before this follow-up is \`c0e0feefc52c9ea9ebe7d974d7b39d2273f9a6e0\`. The new isolated provenance job did not remain pending: [compatibility run #44773037343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773037343), job **#136416265318**, completed SUCCESS at the source/test head.

Exact job evidence:
- \`test_build_provenance.py\`: **27/27 PASS**, including observed compiler C/C++ version fields, missing-\`compiler.cpp.cmd\` fail-closed behavior, and reuse of the exact local library search paths.
- \`test_arduino_cli_archive_verifier.py\`: **8/8 PASS**.
- \`test_release_artifact_action_pins.py\`: PASS; 52 BlazePwifi, 4 compatibility-workflow and 6 SoftTimer external action invocations pinned to reviewed immutable commits.
- The compatibility workflow's two exact HARDWARE source matrix jobs (ESP32 3.3.13 and 4.0.0) were still in progress at this inspection. The earlier matrix run [#44772443932](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44772443932) completed both core jobs SUCCESS.

[Full run #44773037406](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773037406) at source/test head \`93bbf19e\`:
- CI-0701 PASS and classified the change as RUN_FULL.
- ESP8266 build PASS; nine OpenWrt firmware targets PASS.
- Main validate FAILED at the CORE-owned \`PROJECT_HANDOVER.md\` freshness gate; ESP32, Android, Ruijie, x86_64 and downstream simulations/publish jobs were cancelled or skipped after the gate. Do not report this as a full build success.
- The docs-head Full run [#44773325211](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773325211) had CI-0701 PASS; ESP32/ESP8266 and other build jobs were still running, with validate queued.
- Docs-head compatibility run [#44773325027](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773325027) was pending behind the earlier matrix run.
- Windows docs-head run [#44773324800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44773324800) failed at the same CORE product handover freshness gate; Windows build and publisher were skipped.

No CORE/PISONET handover or implementation was edited to bypass these gates. The source/test task is verified by the dedicated release-owned workflow; overall product Full remains failed until CORE refreshes its own handover.
