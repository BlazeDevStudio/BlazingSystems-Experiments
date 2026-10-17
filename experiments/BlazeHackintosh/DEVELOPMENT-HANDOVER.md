# BlazeHackintosh — active development handover

**Checkpoint date:** 2026-10-18
**Repo:** BlazingSystems/BlazingSystems-Experiments
**Branch:** blazehackintosh-v0.1.0-foundation
**Project path:** experiments/BlazeHackintosh/
**Milestone:** 1 — research, audit, scanner, taxonomy schema and initial UI preview
**Target release:** v0.1.0 Experimental; full installer NOT YET RELEASED.

## Completed in this checkpoint
- Scoped new, isolated BlazeHackintosh codebase on an experimental branch.
- Read-only CLI scanner and explicit CPU SKU mapping; fail-closed fallback.
- 31 family reference entries; schema and test checks.
- Working offline manual-reference UI and bundled licensed Lucide SVGs.
- GitHub Actions for Python tests and Windows console scanner build.
- Source ledger, compatibility caveats, known blockers and basic operator docs.

## Current blockers
No hardware-specific EFI generator, version-matched ocvalidate, kext dependency
resolver, installer downloader, image builder, safe migration system, live ISO,
compiled Windows GUI or physical acceptance testing. No fake releases.

## Design constraints
Never claim successful boot from matching a CPU name.
No destructive disk operation without device confirmation, backup and rollback.
No uploading diagnostics. No distributing macOS binaries.

## Test evidence
See docs/TEST-EVIDENCE.md and actual GitHub Actions run status. The automated
workflow must complete before any Windows executable is described as built.

## Next actionable step
Implement exact GPU/PCI ID inventory and validated per-SKU hardware manifests,
then build a constrained OpenCore 1.0.8 EFI candidate generator using official
Sample.plist and a matching ocvalidate binary. Begin with Intel Haswell after
GPU/firmware evidence; do not emit IMG files prior to reproducible EFI checks.

## Continuation process
Inspect the latest branch head and CI run before any new edits.
Update this handover after every substantial change. Preserve independent projects.
 
## Verified CI evidence (source baseline)
- Foundation source commit: `5fd30edb6a5806d0f77bdc1ac3c57263d0ba6bfa`
- Linux test job: success, 8 unit tests.
- Windows test job: success, 8 unit tests.
- Windows PyInstaller scanner build: success and CLI smoke-test success.
- GitHub Actions run: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39073023855
- Windows artifact ID: 12115877209, approximately 8.2 MB downloadable through Actions.
- No physical boot tests or EFI/IMG validation.

The scanner-only alpha prerelease publishing workflow is being added in the next
commit; the release does not exist until the job reports success. Do not treat
this prerelease as the full v0.1.0 Hackintosh installer.

## 2026-10-18 continuation — v0.1.1 inventory candidate
- Expanded read-only Windows discovery: GetFirmwareType (UEFI/BIOS), GPU and physical network PCI vendor/device IDs, storage model/size/interface and memory.
- Expanded Linux best-effort lspci numeric IDs, network devices, RAM and lsblk disk model/size/interface.
- Added explicit missing-inventory evidence and privacy regression tests.
- Offline UI accepts local scanner JSON and prepopulates hardware fields without uploads.
- Updated scanner-only prerelease automation for tag v0.1.1-alpha.1, retaining the separate v0.1.0-alpha.1 release.
- Release evidence and downstream CI job conclusions must be added after the candidate passes.

### Regression triage
Initial v0.1.1 Actions run 39080305411 failed a case-sensitive privacy
sentence assertion. Corrected test; also upgraded checkout/setup-python major
Actions to Node24-capable releases. Await updated CI before release claim.


## v0.1.2 candidate — read-only EFI structural inspector
- Added \`efi_validator.py\`, runnable standalone and through \`blazehackintosh.py validate-efi\`.
- Checks config.plist parse, root section presence, loader location, enabled ACPI/driver/tool/kext references, disabled-entry handling and component duplicates.
- Rejects absolute, parent and externally redirected paths. Does not execute a binary, write EFI, download macOS or generate EFI.
- Added 11 extra unit tests, scheduled on Linux and Windows through existing CI.
- Alpha tag \`blazehackintosh-toolkit-v0.1.2-alpha.1\` planned subject to CI success. No claim of ocvalidate result or boot validation.

## v0.1.2 CI regression triage
Run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080788463 passed 25/25 unit tests on both platforms, and PyInstaller built the toolkit EXE. The workflow then failed because PowerShell's external-command failure behavior interpreted the intentionally nonzero (`2`) exit code for an incomplete EFI fixture as a shell failure before checking `$LASTEXITCODE`. The smoke test now uses Python `subprocess.run(check=False)` to verify the return code and inspect its JSON. New release eligibility must still pass a fresh workflow run.
