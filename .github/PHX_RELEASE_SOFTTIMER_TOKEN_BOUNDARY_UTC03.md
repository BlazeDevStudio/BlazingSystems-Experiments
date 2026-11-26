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
