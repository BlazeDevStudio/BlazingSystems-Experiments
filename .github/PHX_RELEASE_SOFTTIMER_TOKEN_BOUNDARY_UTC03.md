# PHX-RELEASE - SoftTimer publisher permission isolation

Activation: 2026-11-26 UTC03
Repository: BlazeDevStudio/BlazingSystems-Experiments
PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242
Branch: draft/softtimer-future-release-signing-pipeline-20261029
Base: blazepwifi-v0.6.0-audit-foundation at 6d4c9b487af4d768c4d7627654d119417fcc6e00
Starting release head: 734b89d9e7792247e8376335c3f3685500ab3f89
Source/test commit: 7193b3ba068748f23fdd8a460596ecefc6e6456b

## Finding

The SoftTimer release workflow granted contents: write at workflow scope. The same-repository pull_request build executes PR-controlled PowerShell scripts, so the build job inherited a write-capable GITHUB_TOKEN even though it only needs repository read access and artifact upload.

## Implemented source boundary

- Workflow-wide GITHUB_TOKEN permission is contents: read.
- Handover and build-windows jobs explicitly retain contents: read.
- build-windows no longer contains the GitHub Release publishing step or GH_TOKEN.
- publish-release is a separate job with contents: write and actions: read; it is restricted to push on main with SOFTTIMER_RELEASE_APPROVED=true and a non-empty, non-frozen SOFTTIMER_RELEASE_VERSION.
- All three build-side signing/final-verification steps require SOFTTIMER_RELEASE_VERSION to equal the workflow VERSION.
- The build artifact now includes the Setup EXE, portable ZIP, SHA256SUMS and both signed portable executables.
- The isolated publisher checks out github.sha without persisting checkout credentials, downloads the artifact from the same run, checks source SHA and version identity, verifies Authenticode and checksums again, then refuses an existing immutable tag before release creation.
- GH_TOKEN is exposed only to the final release-creation step in the isolated publisher job.

## Test and verification record

- Test-first regression assertions were added before the source correction in commit 6bb5a4e51d0e3f4b95ced59ea5d884336f156893.
- That intermediate test-only commit contained malformed duplicated test content due an escaped replacement string. The final source/test commit restores the original negative-selftest body from 734b89d9 and adds exactly one permission-boundary regression block. Final readback: 11,310 characters, 199 lines, one new boundary block and one publisher-boundary assertion.
- Static structural assertions against the final workflow/test content passed: workflow and build permissions are read-only; publisher write permission is isolated; signing steps require version equality; uploaded artifacts include both binaries needed for publisher re-verification.
- Exact-source Actions runs for 7193b3ba were not returned: zero workflow runs and zero commit statuses. The older run 40882814472 is for pre-change SHA 734b89d9, so it is not evidence for this change. On that historical run, build and handover jobs passed while signing and publishing were skipped.
- A PowerShell runtime was unavailable in the execution environment. The PowerShell regression was not executed locally, and no hosted RED or GREEN is claimed.

## Configuration and stack constraints

- The new SOFTTIMER_RELEASE_VERSION repository variable is an additional release gate. Its live value was not inspected or changed. It must match VERSION and must not be set to authorize a release without the owner's explicit gate.
- PR #291 is a child draft based on the former PR #242 head 734b89d9. This parent branch has advanced; no rebase, retarget, merge or force-push was performed. PHX-MASTER must reconcile the child stack before further integration.
- PR #242 remains DRAFT. No real PFX, production signing key, release token, tag, GitHub Release, hardware flash, payment migration or customer deployment was used.

Disposition: DRAFT / INDEPENDENT REVIEW REQUIRED / EXACT-HEAD CI NOT VERIFIED / PRODUCTION NO-GO.

Next owner task: PHX-INFRA or repository administrator to run the SoftTimer workflow on the final PR #242 head using an authorized workflow_dispatch or PR Actions trigger; PHX-QA independently reviews the permission boundary and test; PHX-MASTER reconciles child PR #291 without overwriting its source.

## UTC03 follow-up — read-only SoftTimer publisher version admission

Observed: 2026-11-26T03:50Z  
PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242  
Branch: draft/softtimer-future-release-signing-pipeline-20261029  
Base: blazepwifi-v0.6.0-audit-foundation @ 6d4c9b487af4d768c4d7627654d119417fcc6e00  
Final source/test HEAD: 9351dd053d4e2ed2349a25f3c5b6d37a308edf93

### Finding and correction

The write-capable publish-release job previously started on an approved main push whenever SOFTTIMER_RELEASE_VERSION was non-empty and not 0.4.0. It did not compare that repository variable with the workflow VERSION until a later verification step. A mismatched version therefore started a job with contents:write/actions:read and only then failed its step-level version check.

A new release-admission job now runs with contents:read only. It is restricted to an approved main push with a non-empty, non-frozen release-version variable, compares the workflow VERSION against SOFTTIMER_RELEASE_VERSION, and emits an approved=true/false output. The write-capable publisher now needs both build-windows and release-admission and runs only when the read-only admission output is true. Existing downloaded-artifact source, signature, checksum and immutable-tag verification remains in place.

No repository variables, signing secrets, PFX material, real signer, tag, release or publication were read, changed or used.

### Commit and test-authoring record

- Initial test insertion [c8d67970](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c8d67970e71ca2df687e9ef1d381bcf6e53d4640) was malformed; not valid test or RED evidence.
- First repair [9d2eee81](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9d2eee81a6c1e220e6de32e1954b34d1608b1413) still had an over-escaped assertion; not accepted.
- Second repair [7cb6918d](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7cb6918d698dffae58df73b660d6c78684323223) simplified that assertion but retained duplicated test content; not accepted.
- Workflow correction [6ac94f96](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/6ac94f9686465e02d5a4e792578831ec20579812).
- Final test reconstruction [9351dd05](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9351dd053d4e2ed2349a25f3c5b6d37a308edf93) rebuilt from the verified 199-line pre-change file and adds the release-admission assertions; final test file is 221 lines. This clean test reconstruction followed the workflow commit because the earlier test-authoring attempts required repair. No expected RED or executed PowerShell test is claimed.

### Static checks and exact-source CI

Static source assertions against workflow/test HEAD 9351dd05 passed for: workflow-wide contents:read; build job read-only; admission job read-only and before publisher; exact VERSION comparison; publisher dependency on positive admission output; and contents:write confined to the publisher job. The test source contains the matching admission assertions.

No pwsh or powershell executable is available in the current execution environment. Exact-head GitHub Actions lookup for 9351dd05 returned zero workflow runs, zero commit statuses and zero check-runs. The connected GitHub actions expose GET/read and rerun-existing-run operations, but no workflow_dispatch/repository_dispatch operation; with no existing run, there is nothing to rerun. Historical run 40882814472 belongs to pre-change SHA 734b89d9 and is not evidence for this change. Therefore hosted RED/GREEN remains NOT VERIFIED.

### Live stack / owner action

PR #242 is OPEN / DRAFT / UNMERGED at source/test HEAD 9351dd053d4e2ed2349a25f3c5b6d37a308edf93, 52 commits ahead / 0 behind its base. PR #291 remains OPEN / DRAFT on the former #242 base 734b89d9; #242 has advanced eight commits beyond that base. PHX-MASTER owns child-stack reconciliation; no rebase, retarget, force-push or merge was performed.

Next: PHX-INFRA or a repository administrator manually triggers .github/workflows/blazepisonet-softtimer-release.yml for exact PR #242 head 9351dd05; PHX-QA independently reviews the job-permission boundary and negative self-test; PHX-MASTER reconciles #291's stale parent base before integration.

No merge, real signing, tag, GitHub Release, hardware flash, payment migration or customer deployment. **PRODUCTION NO-GO.**


## PHX-RELEASE UTC16 — immutable SoftTimer action pins and checkout credential isolation

Observed: 2026-11-26T16:28:30.929Z  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242  
Branch: `draft/softtimer-future-release-signing-pipeline-20261029`  
Base: `blazepwifi-v0.6.0-audit-foundation` @ `6d4c9b487af4d768c4d7627654d119417fcc6e00`  
Starting head: `a7e27fe50e13326a7258bbaed1388594141ddda3`  
Source-fix head before handover: `3b08e7eb5cd63b94f09141c35dd924b1c0c5cf7f`

### Finding

The RELEASE-owned SoftTimer workflow used mutable major-version action refs for all six external action uses. Two of its three checkout steps also retained the default persisted GitHub token credential. The workflow-wide and build-job permissions were already read-only, and the isolated publisher checkout already disabled credential persistence; this increment closes the remaining checkout gaps and makes all action versions immutable.

### Bounded change

- Added `.github/scripts/test_softtimer_release_action_pins.py`, a RELEASE-owned static guard. It checks every external action ref against a reviewed immutable commit and requires all three checkout steps to set `persist-credentials: false`.
- Added the script path to the existing PR/push path filters and wired the guard into the read-only handover job before the shared handover checks.
- Pinned all six workflow action uses to exact upstream tag commit SHAs verified through the official action repositories:
  - `actions/checkout` v4.2.2 — `11bd71901bbe5b1630ceea73d27597364c9af683` (3 uses).
  - `actions/setup-dotnet` v4.3.1 — `67a3573c9a986a3f9c594539f4ab511d57bb3ce9`.
  - `actions/upload-artifact` v4.6.2 — `ea165f8d65b6e75b540449e92b4886f43607fa02`.
  - `actions/download-artifact` v4.3.0 — `d3f86a106a0bac45b974a628896c90dbdf5c8093`.
- Added `persist-credentials: false` to the handover and Windows build checkouts. The publisher checkout already had it.

No PISONET application, installer, PowerShell test, product behavior, signer, secret, repository variable, tag, release, COE destination or hardware source was modified. This is a CI supply-chain/credential-boundary change only.

### Commits and local test record

- New static test file: [`1498dc40`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1498dc4007232f041785d2df16eb934796181ae2).
- Test wiring / path-filter commit: [`1251bdfe`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1251bdfe98b44b59870cb7aa3e29ec965c7fb378).
- Source correction: [`3b08e7eb`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3b08e7eb5cd63b94f09141c35dd924b1c0c5cf7f).

The committed guard was exercised locally against the exact six action-reference lines and three checkout blocks extracted from the PR workflow:
- Test-first snapshot at `1251bdfe`: **2 tests failed as expected** — mutable action tags and two checkouts persisting credentials.
- Corrected snapshot at `3b08e7eb`: **2 tests passed** — all four action repositories use the reviewed commit SHA and all three checkout steps disable credential persistence.

This is a local Python static-guard result, not GitHub Actions evidence.

### Exact-head Actions status

For exact PR head `3b08e7eb5cd63b94f09141c35dd924b1c0c5cf7f`:
- PR-triggered workflow runs: **0**.
- Combined commit statuses: **0**.
- Branch run history contains 35 older runs; the latest returned run [#40882814472](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40882814472) executed source `734b89d9`, not this head. It is not valid RED/GREEN evidence for this increment.
- The connected GitHub Actions interface exposes run/job reads and reruns of existing runs, but no workflow-dispatch operation. There is no exact-head run to rerun. No historical run was relabelled as current.

Therefore exact-source hosted RED/GREEN remains **NOT VERIFIED**. Existing Windows/PowerShell release tests also remain unverified at this new head. The next owner action is for PHX-INFRA or a repository administrator to trigger the workflow for the exact current #242 head using an authorized mechanism, then record the actual job outcomes.

### Live ownership / blockers

- PR #242 remains OPEN / DRAFT / UNMERGED.
- PR #291 remains OPEN / DRAFT on its old parent base `734b89d9`; #242 has advanced beyond that base. PHX-MASTER owns stack reconciliation. No rebase, retarget, force-push or merge was performed.
- MASTER #288 remains the coordination authority; the 11-route ownership manifest is `DRAFT_REVIEW_ONLY`. RELEASE has no migration or integration authority.
- Cleanup-first #266 remains OPEN / 0-of-7; this task is one bounded RELEASE contribution, not a completed global cleanup track.
- COE #26 remains FROZEN; COE #31/#35 are separate packager integration drafts and were not modified in this increment.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found after the authorized Library inventory was paged to completion. No older registry snapshot or checkpoint was substituted.

### Next owner actions

1. PHX-INFRA / repository administrator triggers and verifies the exact-head SoftTimer workflow.
2. PHX-QA independently reviews the action pin map, checkout credential boundary and static guard.
3. PHX-MASTER reconciles PR #291's stale parent base before any integration.
4. Registry custodian restores authorized provenance-only access to private Drive v11.

No signing, tag, GitHub Release, hardware flash, real-payment migration, customer deployment, merge or publication. **PRODUCTION NO-GO.**


---

## PHX-RELEASE UTC17 — checkout credential guard must inspect YAML with mapping (2026-11-26T17:15Z)

**Disposition:** one RELEASE-owned CI guard false-positive was reproduced and corrected on the existing SoftTimer draft [PR #242](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242). The prior test searched the entire checkout step block for a line containing persist-credentials: false. Text inside a run: | script or another nested field could satisfy that assertion even when the checkout action had no with.persist-credentials input.

### Bounded correction

The guard now:
- requires exactly one checkout-step with: mapping;
- scans only that mapping, stopping at the next peer step key;
- accepts exactly one direct persist-credentials: false entry;
- rejects a script-text false positive, missing/duplicate entries, and any non-false value.

The three real workflow checkout steps remain unchanged and already specify the correct direct with.persist-credentials: false input. No PISONET product, installer, PowerShell test, publisher permission, secret, signer, or release behavior was changed.

### Test-first and source evidence

- Test-first commit [f4fb4a0f](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f4fb4a0f8df24ebb56d48a82b9ff25f8210b4fae) adds a synthetic malformed checkout whose run: script contains the misleading text, plus a positive direct-with fixture.
- Local RED reproduction against the previous broad predicate: the malformed run: text was incorrectly accepted. This was a focused local Python reproduction, **not** a hosted Actions run.
- Source correction [e97048fb](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e97048fbae6894eb15433fe62dd1ec85b7ad6e45) restricts the guard to the direct YAML with: mapping.
- Local focused post-fix checks: malformed run: text rejected; direct with.persist-credentials: false accepted. This is a narrow local check, **not** a full workflow or PowerShell test run.

### Exact-head CI and stack status

- Final source/test HEAD: e97048fbae6894eb15433fe62dd1ec85b7ad6e45.
- PR #242 remains OPEN / DRAFT / UNMERGED. Current base is blazepwifi-v0.6.0-audit-foundation@6d4c9b487af4d768c4d7627654d119417fcc6e00; GitHub reports mergeable=false.
- Exact-head PR Actions runs: **zero returned**. Combined commit statuses: **zero returned**. Do not treat older branch runs as evidence for this SHA.
- No PowerShell runtime test, Windows build, signing, tagging or publishing was performed.
- Child PR #291 still targets the older #242 snapshot 734b89d9e7792247e8376335c3f3685500ab3f89; MASTER owns reconciliation. No rebase, retarget, force-push or merge was performed.

### Next owner actions

1. PHX-QA independently reviews the guard's YAML-scope parsing and regression at e97048fb.
2. PHX-INFRA / repository administrator enables or triggers the authorized exact-head PR workflow and records actual jobs.
3. PHX-MASTER reconciles #242's advanced base and #291's stale parent relationship without overwriting source history.

**Disposition:** local focused guard behavior verified; hosted exact-head CI NOT VERIFIED; independent QA pending; draft only; PRODUCTION NO-GO.


---

## PHX-RELEASE UTC20 — discover id-first checkout steps in the credential guard (2026-11-26T20:10Z)

**Scope:** one RELEASE-owned static CI guard correction on the existing SoftTimer draft [PR #242](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242). Branch `draft/softtimer-future-release-signing-pipeline-20261029`; base `blazepwifi-v0.6.0-audit-foundation@6d4c9b487af4d768c4d7627654d119417fcc6e00`. The PR remains OPEN / DRAFT / UNMERGED and GitHub reports `mergeable=false`.

### Finding

The checkout credential guard's step splitter recognized only list items beginning with `- name:` or `- uses:`. GitHub Actions also permits a step to begin with `- id:` and declare `uses:` as a later mapping key. An additional id-first checkout could therefore be omitted from the exact-three checkout count and from the credential-persistence assertion.

### Test-first and correction history

- Regression-only commit [`b7cdaaa5`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b7cdaaa50a978217e03a5d0c132f9f6ff31d850f) adds a fixture with three correctly configured checkout steps plus a fourth id-first checkout whose `persist-credentials` is true. The prior step splitter returned only three checkout blocks for four checkout steps in a focused local reproduction. This is local source-logic evidence, not a hosted Actions RED run.
- Source correction [`ed500ebd`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ed500ebd4ff072b21071ebffe20e59b95d17bc18) now splits on every step list item at the workflow's six-space indentation and discovers checkout actions whether `uses:` is the first or a later step key. The existing real-workflow check uses the same discovery helper.
- Follow-up matcher normalization [`faf4c09f`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/faf4c09fea81914ab2a94f660b5dc4ab3070c368) corrected the exact YAML key-spacing expression after source inspection; no failing test is attributed to this cleanup.
- Focused local GREEN at final code/test HEAD `faf4c09f`: all four fixture checkout steps discovered; a direct `persist-credentials: false` checkout accepted; the id-first `persist-credentials: true` checkout rejected. Three focused assertions passed. This was not a full unittest run, PowerShell run, or Windows build.

### Exact-head hosted CI status

- Test-only commit `b7cdaaa5`: PR-triggered workflow runs 0 returned; combined statuses 0.
- Final code/test commit `faf4c09f`: PR-triggered workflow runs 0 returned; combined statuses 0.
- The existing workflow path filter includes `.github/scripts/test_softtimer_release_action_pins.py`, but the connected GitHub Actions interface exposes run/job reads and reruns, not a workflow-dispatch operation. No older run is attributed to either new SHA.
- Therefore hosted exact-head RED/GREEN, Windows/PowerShell runtime validation, signing, tagging and publication remain NOT VERIFIED / NOT PERFORMED.

### Current stack and owner boundaries

- MASTER PR #288: `ed6bb786c08d360a611e0e6c5c0505fa90d9b477`, OPEN / DRAFT. MASTER retains the release-stack and ownership reconciliation authority.
- PR #291: `bf339a76964a1abe2412fac45392fe06a8e66418`, OPEN / DRAFT, based on old #242 snapshot `734b89d9e7792247e8376335c3f3685500ab3f89`. Exact compare against #242 code/test head `faf4c09f`: **876 ahead / 19 behind, diverged**; merge base remains `734b89d9`. Its accumulated diff includes inherited CORE and PISONET paths. No rebase, retarget, force-push or merge was performed.
- COE integration #26 remains FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`; its five PR workflows remain queued with zero jobs.
- COE parent #31 remains `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`; parent shared validation and case-collision pass, but its mandatory sandbox fails at the unprivileged Bubblewrap UID-map probe (Permission denied / exit 125). Parent results are not child acceptance.
- COE child #35 remains `6413e557eb2e552513eedae2bc6559646278b2f2`, **488 ahead / 0 behind** parent #31. Exact final-head shared validation passes the 257-test packaging/tool suite with two intentional skips and one synthetic profile, then fails closed at 10/10 site-ULA admissions; ESP32/ESP8266 compilation is skipped. Sandbox host preflight passes 48/48 then fails because Bubblewrap is unavailable (exit 125); case-collision passes. This child remains separate from #242 and #26.
- Authorized Library title search did not surface private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json`. No older registry snapshot was substituted and no private contents or identifiers were copied.

### Next owner actions

1. PHX-QA independently reviews the id-first checkout discovery and credential guard at code/test SHA `faf4c09f`.
2. PHX-INFRA / repository administrator runs the exact-head #242 workflow through an authorized mechanism and records real jobs.
3. PHX-MASTER reconciles #291's stale parent and inherited CORE/PISONET path overlap; do not rebase or merge from RELEASE.
4. Registry custodian restores authorized provenance-only access to private Drive v11.

No PISONET product/installer code, shared workflow, secrets, signer material, CORE, RENTAL, HARDWARE, QA, MASTER or COE #26 destination source changed. No merge, signing, tag, publication, hardware flash, real payment migration or customer deployment occurred. **PRODUCTION NO-GO.**
