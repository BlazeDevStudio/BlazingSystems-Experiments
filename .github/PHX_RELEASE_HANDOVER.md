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
