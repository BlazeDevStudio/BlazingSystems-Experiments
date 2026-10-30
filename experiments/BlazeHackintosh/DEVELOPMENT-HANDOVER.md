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

## Successful alpha releases and CI gates (2026-10-18)

1. v0.1.0-alpha.1 scanner preview: published (initial 8 Linux/8 Windows tests).
2. v0.1.1-alpha.1 scanner inventory: published https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-scanner-v0.1.1-alpha.1 ; 14/14 tests on both platforms, source ecbfda73689495c68463eb7312d9a6b118362ced.
3. v0.1.2-alpha.1 scanner/EFI inspector: published https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.2-alpha.1 ; 25/25 tests on Linux and Windows, and Windows CLI smoke; run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080929664; source 83992059cfccfaf2a26458f098669ddbdf7defa6.

**Repository remains a draft PR #105 and intentionally not merged.**
**Next implementation step:** version-matched OpenCore 1.0.8 `ocvalidate` integration with trusted binary hashes and zero default execution of unverified binaries. Then source-controlled, hardware-constrained EFI generation with exact CPU/GPU/firmware evidence and full acceptance tests.
**Production blocker remains:** no version-matched validated, actually booted EFI or installation environment. Never advertise installer or production readiness yet.

## v0.1.3 (in development, not yet released)
- Added explicit approval gate for official ocvalidate, SHA-256 pinned to upstream OpenCore 1.0.8 RELEASE archive, verified --version check and fail-closed execution.
- Added offline ZIP verifier command and symlinked-config rejection.
- Added mock-only trust-model regression tests and CI plans to run the *actual* official checker against an intentionally invalid EFI fixture on Windows before publishing.
- No automatic downloads in application; CI fetches and verifies the upstream archive only inside disposable GitHub-hosted runner.
- No hardware boot testing, EFI generation or production claims. Await CI results before describing release v0.1.3 as published.

## v0.1.3 CI regression (run 39081553933)
First run failed 3/34 tests because mock ZIP contents compressed below the deliberate 1 KiB minimum archive size. Test fixtures now use incompressible random bytes to exercise the real digest gate. No production code trust limits were weakened. New CI required.

## v0.1.3 real upstream checker regression (run 39081613900)
All 34 unit tests passed on Linux and Windows and official release ZIP SHA-256 verified on Windows. The actual official ocvalidate --version check did not confirm 1.0.8; no binary was shipped. Added bounded exit-code and stdout/stderr diagnostic to distinguish actual upstream version format from execution errors before remediation.

## v0.1.3 upstream version discrepancy (run 39081701539)
Official RELEASE ZIP SHA256 verified. Actual ocvalidate.exe --version returned exit 4294967295, printed the **exact 1.0.8 banner**, followed by `Failed to read --version`. Added narrow banner-based fallback ONLY if archive is already hash-verified, plus regression tests for 1.0.8 accepted and 1.0.7 rejected. Official schema-validation smoke rerun required. No release claim yet.


## Verified v0.1.3-alpha.1 release checkpoint — 2026-10-18
- Source release commit: `a672a926590fe69c82f8c8719b18421b5773da4e`
- PR remains draft #105, isolated in branch `blazehackintosh-v0.1.0-foundation`.
- Published scanner/validator-only experimental GitHub prerelease:
  https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.3-alpha.1
- Windows toolkit EXE SHA-256: `0f0b26726b7c6d71a265cdc3f4be0d2fa3975f6319170c8f88fd49a3604f66af`.
- Offline browser UI ZIP SHA-256: `0ff549f02dce3d6becc3522c717f9e8f9049aa71cc65aa1da894c73c51568b13`.
- Verified CI workflow: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39081813252
- **36/36 unit tests passed on Linux and Windows.**
- GitHub Actions downloaded official OpenCore 1.0.8 RELEASE ZIP, verified published SHA-256, executed real version-matched official ocvalidate against deliberately invalid synthetic EFI, and confirmed rejection.
- After PyInstaller packaging, the Windows EXE repeated the same real official validation smoke test and passed.
- Project does not distribute OpenCore binaries or macOS. User must independently acquire upstream licensed components.
- No actual EFI generator; no verified config on physical hardware; no USB IMG, live ISO, multi-boot migration or disk-write workflows. Experimental toolkit only.

**Next development:** evidence-scoped hardware manifests and per-component kext/ACPI requirements, generator architecture with exact OpenCore 1.0.8 Sample.plist, and safe output-directory-only EFI assembly followed by both structural and official validation. Before any IMG or internal-disk writing, add backup/rollback and disposable virtual-disk tests.

## v0.1.4 candidate staged for CI (no release claims yet)
- Explicit profile gates for exact i5-4570/i7-4770 Haswell UEFI, sole 8086:0412 iGPU and macOS 12 research selection.
- New `plan-haswell` (no writes) and `stage-haswell-efi` commands. Requires explicit acknowledgement, unmodified OpenCore 1.0.8 ZIP, private local SMBIOS identity, user-approved three kexts, two SSDTs and HfsPlus.efi.
- Stages under NEW BlazeEFI-* folder only; fails closed on missing source, symlinks, oversized/special files, hash failure, ocvalidate rejection or existing destination. Includes per-file hash manifest and DO-NOT-INSTALL marker.
- Tests use fake/invalid kexts, SSDTs and HFS; CI staging will be intentionally NON-BOOTABLE and never distributed. Official ocvalidate schema pass is not hardware acceptance.
- New release target `blazehackintosh-toolkit-v0.1.4-alpha.1` gated by actual Linux/Windows test suites, genuine OpenCore schema check, source CLI and compiled EXE staging tests. Previous v0.1.3 is preserved.

## v0.1.4 CI regression 39091033215
48 Linux tests passed; Windows failed 8 new builder tests because `Path.resolve() != Path.absolute()` rejected an ordinary Windows runner temporary parent directory (path alias/canonicalization difference), before checking real input files. Guard now requires an existing non-symlink parent and a NEW BlazeEFI-* child, without invalid canonical-string equality. Re-run mandatory; no release claim yet.


## Verified v0.1.4-alpha.1 release — 2026-10-18
- Source release commit: `d04487c43b6e8287b0166ea5bf032e2e02beabe9`.
- Actual published prerelease: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.4-alpha.1
- Windows EXE `BlazeHackintosh-Toolkit.exe` (9,219,416 bytes), SHA-256:
  `a8c9b7606c005ee5d070b720aab1b0d5d5619fb8cb40b3badc2aa20af4af706e`.
- Offline browser UI ZIP (12,849 bytes), SHA-256:
  `1a8e6aeed52db707b6cd8e3ae2dd3f75557d0c0a5cc2dfe9061c4ff2f74b80a8`.
- Windows Action artifact ID 12123006774, containing the compiled CLI toolkit.
- Verified validation workflow: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39091108747
- **48 Python unit tests passed on Linux; 48 passed on Windows.**
- Real upstream OpenCore 1.0.8 RELEASE ZIP SHA-256 gate passed; genuine `ocvalidate`
  executed and rejected an intentionally invalid fixture.
- Genuine `ocvalidate` accepted the constrained Haswell reference configuration
  generated from the official 1.0.8 Sample.plist with synthetic kext/ACPI/HFS payloads.
  Both Python source and PyInstaller-packaged Windows EXE completed the staging smoke
  test. The synthetic payloads are **NOT real EFI boot components** and were not published.
- Operator-supplied actual kext/SSDT/HFS provenance, genuine SMBIOS identity,
  GPU framebuffer behavior, motherboard firmware compatibility, macOS installation,
  physical boot and data-safety on actual hardware remain UNVERIFIED.
- Draft PR #105 remains unmerged. No production, installer IMG, EFI migration,
  ESP write or boot-verified architecture release is claimed.

Next: enforce independently trusted component manifest hashes/licensing for all
user-supplied kext/ACPI/HFS files, then add compatible ACPI/device evidence checks,
real hardware trials and readback recovery tests before considering USB images.

## 2026-10-18 — v0.1.5 integrity hardening candidate
- Most recent verified release remains `blazehackintosh-toolkit-v0.1.4-alpha.1` (48 Linux and Windows tests, official OpenCore 1.0.8 ocvalidate).
- New `component_manifest.py` validates a complete SHA-256 ledger for ALL three required kext bundles, two required ACPI SSDTs, and the user-supplied HfsPlus.efi; rejects undeclared/missing/duplicate paths, symlinks, altered hashes, unsafe sizes and missing operator-asserted HTTPS source, release and license information.
- Builder now requires `--component-manifest`; verifies inputs before staging and verifies copied outputs before accepting the configuration. Research output embeds SHA-256 of the ledger and correctly warns that source authenticity is **not** independently confirmed.
- Added six builder regressions: tampering, missing ledger, missing entry, missing declared license, extra ACPI input, honest integrity labeling.
- CI release target: `blazehackintosh-toolkit-v0.1.5-alpha.1` if and only if all source tests, Windows packaging and real upstream 1.0.8 ocvalidate smoke pass. Do not label this release production.
- Production blockers remain: genuinely verified component publishers/signatures/licenses, target-specific ACPI/GPU checks, broader CPU coverage, full GUI, installer preparation, disk migration/rollback, physical boot proof and final production acceptance.

### v0.1.5 first CI regression (run 39092875131)
Linux first run failed: 17 builder tests invoked new mandatory component-manifest argument without updating their fixture generator. The source builder safety gate rejected every missing argument; no prerelease published. Fixture setup now supplies a complete per-file synthetic ledger. Rerun Linux/Windows and genuine OpenCore CI mandatory.

## Verified v0.1.5-alpha.1 publication — 2026-10-18

- **Release is live:** https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.5-alpha.1
- Release source commit: `dad67964dd43de7040048d222cfe76b9c9ee6cf2`.
- Linux 54/54 tests and Windows 54/54 tests passed.
- Source Python + packaged EXE completed official OpenCore 1.0.8 schema validation of intentionally NON-BOOTABLE research fixtures.
- Workflow run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39092948759
- EXE asset `BlazeHackintosh-Toolkit.exe`, 9,225,236 bytes; SHA-256 `04ba1d1d42ceb728a2bbf8f32520ba2ab72d6166f3338aeb90c0706bf6659cb6`.
- Offline UI ZIP 13,127 bytes; SHA-256 `902a57e898b6f5eacf3390e3f496bc5aef6c8e01b2da84b800c0b18d326ab793`.
- GitHub Actions artifact ID `12123431324` (Windows compiled toolkit).
- New integrity ledger catches substitution/missing entries and rejects altered source/copy hashes. **Operator-declared source URLs and licensing still not independently authenticated**.
- No physical boot/USB readback/live ISO, production-grade GUI, all-family EFI database or safe internal-disk migration. **Production release remains blocked; PR #105 draft and unmerged.**

Next action: independent release-publisher signature/source verification, missing hardware/ACPI evidence, GUI and robust non-destructive installation tooling. Every release-gate blocker must remain in handover until verified resolved.

## Hourly continuation production acceptance tracker — 2026-10-18
- Added complete 26-item machine-readable gate catalog (`Production/RELEASE-GATES.json`) and fail-closed `release-readiness` CLI.
- 3 currently marked verified (read-only scan, version-pinned ocvalidate, test/Windows toolkit CI) backed by actual GitHub run; 23 production gates remain incomplete or blocked.
- Code-enforced exact required gate IDs prevent dropping unfinished jobs from the checklist; verified gates must include HTTPS evidence and all `required` fields remain true.
- Windows packaged EXE now bundles the gate catalog, and CI verifies `release-readiness` refuses production status (exit 2).
- This checker cannot independently assess evidence truth; physical hardware boot proof, signed assets, user-permitted disk operations and all remaining components still must be completed and reviewed.
- The user requested an hourly continuation automation; continue from this ledger and update it with genuine evidence at each milestone until a final non-alpha production release is live and verified, rather than silently closing jobs.

## Verified production-readiness tracker CI — 2026-10-18
- Code branch commit `f89bb1026cb8ffe17a37aff3cd7c280e32c8c767` adds machine-readable 26-mandatory-gate tracker and bundled CLI production-readiness check.
- GitHub Actions https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39093338423: **58/58 Linux unit tests passed, 58/58 Windows unit tests passed**.
- Real official OpenCore 1.0.8 schema staging and compiled Windows toolkit smoke tests passed, using intentionally non-bootable third-party fixtures.
- The packaged EXE `release-readiness` command correctly exited 2 and emitted `production_ready:false`, because 23 required production gates remain open or blocked.
- GitHub Actions build artifact ID: `12124025596` (`BlazeHackintosh-v0.1.5-experimental-windows-toolkit`). This is a CI build artifact, **not a new production GitHub Release**.
- The last independently verified downloadable prerelease remains https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.5-alpha.1
- Production remains blocked: no physical macOS boot acceptance, verified component publisher signatures, safe disk migration/recovery, full Windows GUI, installer media or final signing.

## 2026-10-18 continuation: read-only staged-file audit candidate

At branch head fd0468bd1e52e373118033be3c8a3300bb8b477b, PR #105 was draft; recent CI 39093445086 and 39093442190 succeeded. Added standalone stage_audit.py and ten disposable-fixture tests. The audit compares local research staging files to their unsigned manifest, rejects missing/extra paths and changed hashes or safety markers. Windows smoke_stage.py now checks a good synthetic stage and a deliberately modified file. Pending fresh CI verification. This is not publisher authentication, USB/ESP image readback, safe migration, or physical boot. Keep 26 required gates and all 23 unresolved requirements unchanged. Next: verify new CI; connect this readback groundwork to safe disposable-image tests and independent upstream component authenticity checks.

### Verified readback-audit CI checkpoint

Commit 5d66e9b5f6003bb653681b62052613a579346446 passed https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39096082439 and parallel PR run 39096084391. Both Linux and Windows ran 68/68 unit tests successfully. Windows compiled the existing console toolkit, ran real pinned official OpenCore 1.0.8 ocvalidate on synthetic Haswell research staging, and ran the new standalone Python readback auditor on an intact candidate and then after deliberate config.plist tampering (expected rejection). The existing v0.1.5-alpha.1 release was preserved, not replaced. New standalone stage_audit.py is NOT bundled into the released EXE. Production gates remain 3 verified and 23 unresolved. Next: independent supplier attestation and safe disposable-image verification.

## 2026-10-19 — committed publisher-verifier regression tests (cross-platform CI)
- Current publisher regression source commit: `ffc5c5c390032d52d0923ac61e9314c32e1615b4`; prerequisite static-test commit: `8005d4af5e4e90d2952a5d36df7cc69118d6f29d`.
- Added `Tests/test_publisher_signature_static.py` (7 platform-independent tests) and `Tests/test_publisher_signature.py` (28 OpenSSL-backed real Ed25519 signing and tamper-rejection tests using ephemeral synthetic keys and bytes).
- Verified source-commit Actions runs: PR https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39205370943 and branch push https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39205366619; both **completed successfully**. 108 Python unit tests passed on Linux and 108 on Windows; actual OpenSSL-backed Ed25519 positive/negative tests ran successfully on both platforms. Windows console EXE packaging and official OpenCore 1.0.8 synthetic fixture checks passed. No new release was published; the pre-existing v0.1.5-alpha.1 prerelease was preserved.
- `publisher_signature.py` was previously committed and was not replaced by the tests. Passing a synthetic Ed25519 signature verifies the verifier's behavior, **not independent publisher identity, actual component authenticity, license clearance, OpenSSL runtime dependency provenance, or physical boot compatibility**. `component-auth` remains blocked.
- Unmerged local candidates (NOT in this CI): component provenance/ZIP audits, GPT/ESP image auditor, Tkinter GUI with privacy filters, Windows GUI Actions workflow and process-tree smoke. These require review, sequential integration, actual Windows GUI compilation/smoke and dedicated cross-platform CI before any release claim.
- Next action: integrate the standalone research-only component provenance validator, with explicit independent trust requirements, followed by the GUI and image-readback candidates. Keep draft PR #105 and all outstanding mandatory gates unresolved until evidence meets their individual definitions.

## 2026-10-19 — real OpenCore 1.0.8 ZIP read-only audit, scoped CI proof
- Added independent read-only `archive_integrity.py` audit plus `Tests/test_archive_integrity.py` and `docs/ARCHIVE-INTEGRITY.md` in source commit `29a285505daef68642b1a6791882665663531f2b`. 17 synthetic unit cases passed on Linux and Windows in runs 39210621940/39210614609.
- Real official OpenCore 1.0.8 release archive ZIP audit wired into Windows CI in `5d845bfe8be55f5096db09a5b39e5df530ba81cf`.
- First real Windows checks failed specifically at cross-platform `Path.lstat()` versus opened-handle `os.fstat()` identity comparison, despite correct pinned SHA-256; see https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39210737623. Fixed using stable size/regular-file checks across Windows path and handle metadata, preserving SHA-256 before/after, post-open handle fingerprint and symlink/reparse refusal. Commit: `881d1081d1c49c8a6a85e883abc445d2af01b8d9`. Added regression for Windows inode alias, but Windows TOCTOU/race immunity is **not** claimed.
- VERIFIED PR CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211050624: **126/126 Linux Python tests; 126/126 Windows tests; Windows compiled console EXE and pinned real official OpenCore 1.0.8 ocvalidate synthetic staging**. GitHub-hosted Windows runner downloaded the actual release ZIP, confirmed SHA-256 `2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b`, exact size 10,544,084 bytes, ZIP structure and CRC with **306 entries (258 file contents inspected)**; no extracted components distributed. This checks actual bytes against pinned GitHub API metadata, NOT independently authenticated publisher identity.
- Preexisting v0.1.5-alpha.1 remains the latest published prerelease. Native Windows GUI compilation, authenticated publisher provenance/licenses, image readback, recovery, physical boot and full installer remain unverified. Production gates remain **3 verified / 23 unresolved**, PR draft/unmerged.
- NEXT: reconcile full unmerged component-provenance manifest candidate with this newly integrated ZIP auditor, then integrate privacy-preserving Windows GUI candidate and prove actual compiled window launch via CI. Do not weaken production gate requirements.

## 2026-10-19 — actual upstream metadata integration verified in GitHub CI
- Integrated strict offline component release metadata validator `component_provenance.py`, five-component upstream release API snapshot and `Tests/test_component_provenance_scope.py` (18 regressions) in commit `81616eae3039d2fd702b0224c9a2e5446e813aa2`. Only metadata and locally supplied ZIPs are inspected; no download/execution/installation is performed by this module.
- Snapshot pinned versions from direct official GitHub release and LICENSE.txt blob reads: OpenCorePkg 1.0.8, Lilu 1.7.2, VirtualSMC 1.3.8, WhateverGreen 1.7.1, AppleALC 1.9.8; HfsPlus.efi excluded, licensing not cleared. GitHub source license blobs and API asset SHA256 values are NOT supplier-signed attestations.
- Windows Actions began running the strict manifest inspector against the **actual downloaded OpenCore 1.0.8 ZIP** in commit `3ac40c4fe36f90bfabd5aea23fbf831f7ed40bf3`.
- Verified full CI PR run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211916219 and push run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211909404: **144/144 Linux and 144/144 Windows unit tests passed**; real OpenCore 1.0.8 ZIP SHA256/size and 306 central entries / 258 streamed files checked, `metadata_structure_valid:true`, `zip_structure_valid:true`, `component_auth_gate_satisfied:false`, `publisher_identity_independently_verified:false`. Official pinned ocvalidate synthetic staging and Windows **console** EXE packaging passed.
- Pre-existing v0.1.5-alpha.1 release remains experimental and is NOT a functional GUI/installer production release. The manifest and validator do not establish real third-party signing key ownership, redistribution permission or EFI boot viability.
- Production gates remain 3/26 verified and 23 unresolved. Next: independently authenticate supplier keys and actual permitted components; integrate the pending native GUI + Windows window-launch CI in reviewed order; investigate disposable ESP/GPT image readback, backup and recovery without touching real disks.

## 2026-10-19 — Windows-native Tk research workbench CI verified (unreleased)
- Source HEAD for new GUI and Windows display workflow: `8fc6717ca8490bf5e6695e055a7c635ef7cef674`; PR #105 remains **open/draft**. Reused locally staged `desktop_gui.py`, privacy safeguards, 31 headless tests, 11 Windows smoke-helper tests, native Windows process-tree HWND smoke, and isolated no-release-permission Actions workflow. No third-party GUI framework added (Tkinter stdlib; PyInstaller 6.16.0 only for packaging).
- Test-first local integration: absent GUI source produced expected failing headless import; installing staged source resulted in **42/42 local Linux tests passed**; synthetic Linux Xvfb window smoke opened and closed without scanning/writes.
- GitHub Actions **BOTH full foundation workflows successful**: PR https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214560638 and push https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214554240; **186/186 Linux and 186/186 Windows Python tests**, original pinned official ocvalidate on intentionally unbootable fixtures, and Windows console packaging.
- Separate **BOTH native GUI Windows acceptance workflows successful**: PR https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214560499 and push https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214554302. A real GUI EXE displayed a visible Win32 top-level window owned by launched EXE/process tree; graceful WM_CLOSE and process exit 0 observed.
- Push GUI artifact `BlazeHackintosh-UNRELEASED-Windows-Research-GUI-CI`, Actions artifact ID `12168891986`, expires 2026-10-26, bundled EXE 12,348,004 bytes, SHA-256 `f8a86cef1ebf53f91b2c469f2d5486587e7d3f85a9ac526fa17521382aeed6ac`. Downloaded CI ZIP SHA-256 `032b391188ffe16a4fbb806956c757e9f200588391f1a4d461a331bf5ca3f033`; recomputed EXE hash matches recorded GUI-SHA256.txt. **No release was published**, do not call this full Windows Setup Assistant or installer.
- Remaining mandatory `windows-gui` gate is still BLOCKED: full beginner/expert installation functionality, online/offline verified source handling, hardware-specific EFI and user-approval disk workflows are missing. Upstream publisher identities and rights, real ESP/GPT readback, physical boot and data-safety acceptance also missing. Keep 3/26 gates verified, 23 unresolved; latest existing v0.1.5-alpha.1 only.
- Next work: prioritize official operator-safe offline component acquisition and verified per-component attribution, then image readback on disposable disk images; do not add a second GUI toolkit or speculative framework. Do not promote gates from CI window creation.

## 2026-10-19 — disposable GPT/ESP image audit CI and Windows file-handle fix
- Read-only `image_audit.py` and disposable 40 MiB synthetic GPT/ESP/FAT32 fixture tests first entered draft PR #105 in `10b2091752aa2ae49d0079459d27154d3b8eb658`; the file inspector never accepts physical disk devices and never writes or mounts images. It checks protective MBR, primary/backup GPT CRCs and consistency, partition bounds, FAT32 BPB, FAT/FSInfo samples and operator-provided SHA-256, but NOT actual EFI contents, FAT filesystem integrity, rollback, safe flashing or boot.
- During review a Windows portability defect was found: `lstat` path inode and opened `fstat` inode can differ. A focused regression was committed FIRST in `432153bb5453a953755b2ebb947576265b94192a` and Linux CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222279657 observed **expected RED** (AttributeError missing shared `_same_opened_file`). The minimal change `fb6c1d1607dc9a8473b6ae6b8ac9a13553f61d86` reused `archive_integrity._same_opened_file` already verified on Windows; no second helper/third-party dependency was added.
- **Verified GREEN cross-platform CI**: push https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222341172 and PR https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222346177, each completed success with 237/237 Python tests on Linux and Windows; official OpenCore ZIP/synthetic ocvalidate checks and existing Windows CONSOLE EXE still pass. Native GUI CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222346195 also succeeded with actual Windows visible HWND and graceful close; that is unchanged research GUI functionality, not installer acceptance.
- Microsoft FAT32 specification v1.03 (2000) places `FSI_TrailSig` at byte 508, value `0xAA550000`, not byte 496 (reserved). Committed image auditor checks byte 508; see https://www.cs.fsu.edu/~cop4610t/assignments/project3/spec/fatspec.pdf (pp.21–22) and docs/IMAGE-AUDIT.md.
- Still **3 of 26 mandatory gates verified, 23 unresolved**. No physical readback or boot acceptance, no real filesystem verification, no licensed/authenticated EFI release images, no signed non-alpha release. Next: build/test genuine disposable ESP/USB image write/readback/rollback in virtual files only; authenticate component sources separately before any distribution.

## 2026-10-19 — disposable image roundtrip regression (no physical media)
- New regression-only tests in [commit ffdaa7b](https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/ffdaa7b898fc52ec6dc9d34015aa314d5cb2e78f) reuse the existing read-only `image_audit.audit_image()` and Python standard-library `shutil.copyfile` / `os.replace`. Two tests write only to autogenerated temporary .img files: intact copied image readback; deliberately corrupted copied GPT header rejected; restoration from temporary backup re-accepted; interrupted 1 MiB copy rejected. Source fixture remains unchanged.
- Independently verified green CI: [PR 39224322821](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39224322821) and [push 39224317558](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39224317558). Each ran 239 Linux and 239 Windows Python tests; existing synthetic ocvalidate checks and Windows console packaging remained green. Windows research GUI workflow 39224322794 also passed.
- This is a test-only local-file simulation. **No general-purpose image-writing API, FAT32 filesystem integrity/readback, actual USB/SSD data preservation, physical-device rollback, UEFI boot acceptance, supplier authorization, or production release was verified.** All 23 outstanding mandatory gates stay unresolved.
- Next: extend actual EFI file checks inside disposable FAT32 ESP images and build a separately reviewed, explicit-confirmation physical drive workflow only after durable backup/rollback test evidence. Never infer physical success from temporary file tests.

## 2026-10-30 — read-only FAT32 EFI payload readback (successor draft PR #257)
- Repository identity confirmed unchanged (GitHub repository id `1389289885`) after owner rename to `BlazeDevStudio/BlazingSystems-Experiments`. Previous draft PR #105 was manually closed **without merge** on 2026-10-24; it was not reopened. New isolated draft PR https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/257 targets the retained `blazehackintosh-v0.1.0-foundation` branch without modifying `main`.
- Test-first source: [RED test commit 75e6928](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/75e6928d189201ce64b1dc9a17f5ab880642a859), [run 40988387682](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988387682) observed expected `ModuleNotFoundError: esp_readback`. Implementation [commit e15f94d](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e15f94da1a7bd32bb6f0b67330a286dba058a34d) added read-only `esp_readback.audit_boot_efi()` in its own module, reusing the existing validated GPT/ESP image audit. No new runtime dependency.
- GREEN CI https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988558649 completed SUCCESS: **245/245 Linux tests and 245/245 Windows tests**; existing pinned OpenCore ZIP/synthetic official ocvalidate and Windows console packaging successful; scanner prerelease step skipped. Six new tests cover synthetic 700-byte multi-cluster `EFI/BOOT/BOOTX64.EFI`, wrong file/image digest, FAT chain cycle, absent EFI short-name directory and long-filename fail-closed.
- Tight acceptance: single FAT32 **8.3 short-name** path, exact operator-provided SHA-256 pins for the entire regular-file `.img` and EFI boot file, FAT mirror consistency, bounded directories/payload, same-handle image rehash, no device paths or writes. `physical_readback_verified=false`, `filesystem_verified=false`, `boot_verified=false`, `safe_to_flash=false` remain mandatory. The synthetic boot payload is not an EFI executable and no real physical hardware was tested.
- Next: independently review source + expand safe EFI content checks in synthetic FAT32 fixtures and only later integrate into actual installer workflows. Do not treat this PR as merged or use it to promote production gates.
