# Evidence ledger

The repository contains Python `unittest` cases in `Tests/test_foundation.py`.
Tests examine research-only catalog classifications, known-model mapping, unknown CPU
fallback, no boot/EFI claim, malformed catalog, PCI-device ID stripping and scan privacy.

The GitHub Actions workflow `.github/workflows/blazehackintosh-foundation.yml` runs
the unit suite on Linux and Windows, exercises scanner CLI, and attempts a PyInstaller
Windows console build. Check the actual run results; workflow existence is NOT a pass.

**Physical boot tests: NONE.**
**EFI package structural validation: NOT APPLICABLE (generator absent).**
**USB/ESP/IMG boot checks: NONE.**
**Destructive-drive hardware test: NONE.**

When CI succeeds, document the actual workflow run URL, commit SHA, job conclusions
and artifact hashes. Never infer physical compatibility from CI.
 
## Verified first automated run — 2026-10-18 (local UTC+08)
- Source commit: `5fd30edb6a5806d0f77bdc1ac3c57263d0ba6bfa`
- Workflow run: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39073023855
- Linux `linux-tests`: **success**; 8 tests passed.
- Windows `windows-console-scanner`: **success**; 8 tests passed,
  PyInstaller produced `BlazeHackintosh-Scanner.exe`; CLI catalog/evaluation
  smoke tests passed.
- Actions artifact: `BlazeHackintosh-v0.1.0-experimental-windows-cli`
  (artifact ID `12115877209`, 8,182,882 bytes compressed).
- Artifact ZIP SHA-256 logged by GitHub Actions:
  `18daa863348bec8c227ea4a4b1110bcf24eeac788ac38c24d54332a32e216e13`.

This constitutes source and build automation evidence only. **NO physical boot
test, EFI validation, recovery ISO test or destructive disk test occurred.**

## v0.1.1 inventory candidate evidence
Expanded inventory, privacy and HTML-presence tests were added after first passing
v0.1.0-alpha.1 release. No passing results for this later revision are asserted here.
Check the new workflow run and artifact before any claims of v0.1.1 release.

### CI regression found and fixed (run 39080305411)
The first v0.1.1 CI run failed 1 of 14 Linux unit tests because the
privacy-disclosure sentence used lowercase "serial numbers" while an existing
test asserted uppercase "Serial numbers". This was a test wording-only mismatch:
the sensor and PCI privacy tests passed. The test now performs a case-insensitive
assertion. No successful run for this fix is asserted until subsequent Actions.

## v0.1.2 EFI inspector
The read-only validator adds isolated temp-directory fixtures for config.plist
parsing, missing components, duplicate enabled components, disabled entries,
unsafe path rejection and categorical non-claims about boot/ocvalidate.
Do not label the v0.1.2 candidate green until actual CI results are verified.

## v0.1.2 CI regression triage
Run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080788463 passed 25/25 unit tests on both platforms, and PyInstaller built the toolkit EXE. The workflow then failed because PowerShell's external-command failure behavior interpreted the intentionally nonzero (`2`) exit code for an incomplete EFI fixture as a shell failure before checking `$LASTEXITCODE`. The smoke test now uses Python `subprocess.run(check=False)` to verify the return code and inspect its JSON. New release eligibility must still pass a fresh workflow run.

## Confirmed scanner and structural-inspector releases — 2026-10-18 (Asia/Manila)

**v0.1.1-alpha.1** (scanner inventory):
- Test run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080356869: Linux and Windows jobs successful; 14 tests per platform; Windows packaged scanner CLI.
- Verified prerelease: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-scanner-v0.1.1-alpha.1
- Release target commit: ecbfda73689495c68463eb7312d9a6b118362ced.

**v0.1.2-alpha.1** (scanner + read-only EFI inspector):
- Test run https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080929664: Linux and Windows jobs successful; 25 tests per platform; packaged Windows CLI passed scanner tests and expected invalid EFI rejection.
- Verified prerelease: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.2-alpha.1
- Release target commit: 83992059cfccfaf2a26458f098669ddbdf7defa6.
- Packaged Windows toolkit SHA-256: 9a069d1de3e0cbbb1238d3efcf54e59709d876224175a1b0170214a0ff00c193.
- Offline UI ZIP SHA-256: 76dd71e39e3a667cdc6276d32f336f4dbb2ce876c78ca10b13608bc18b02a5bd.
- Failure note: first attempt run 39080788463 succeeded at unit tests and building the EXE but did not pass the PowerShell smoke test because it treated an **expected failure exit code** as a job error. This was fixed with captured subprocess assertion; run 39080929664 succeeded.

**Still not verified:** OpenCore ocvalidate matching version, a generated EFI, binary authenticity, an EFI partition or image boot test, any macOS installer, and real hardware boot. A structural reference check passing does not change those classifications.

## v0.1.3 gate (pending)
Unit tests mock upstream execution; separate Windows CI must fetch pinned official archive, verify SHA-256, confirm actual checker version, and observe an intentionally invalid EFI fixture rejected before any prerelease. A valid ocvalidate result on a real user configuration, physical EFI boot, and macOS compatibility still require independent evidence.

## Verified v0.1.3 alpha release — CI run 39081813252
- Source commit `a672a926590fe69c82f8c8719b18421b5773da4e`.
- Linux **36 tests passed**; Windows **36 tests passed**.
- Official OpenCore 1.0.8 RELEASE archive hash pinned and verified in GitHub-hosted Windows CI.
- Actual native upstream ocvalidate invocation on invalid EFI fixture: **expected error confirmed**, both from Python source and compiled Windows CLI.
- All Windows build and publish gates completed; real prerelease present:
  https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.3-alpha.1
- Windows executable digest `0f0b26726b7c6d71a265cdc3f4be0d2fa3975f6319170c8f88fd49a3604f66af`.
- Offline UI digest `0ff549f02dce3d6becc3522c717f9e8f9049aa71cc65aa1da894c73c51568b13`.
- **None** of these tests establishes physical boot, valid SMBIOS/hardware matches, installer compatibility, or a safe disk migration.

## v0.1.4 research builder (pending CI)
Additional unit regression cases exercise explicit acknowledgement, fail-closed CPU/GPU/firmware gates, input file types, symlink refusal, destination non-overwrite, temporary-file cleanup and research classification. Windows Actions will use exact upstream RELEASE asset to build a candidate with deliberately fake kext/ACPI/HFS components and run real official ocvalidate. The fixtures are intentionally non-bootable and must NEVER be uploaded as a ready-to-use EFI.


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

CI staging validates the file layout and OpenCore schema, **not** UEFI execution or actual kext/SSDT functionality.

## v0.1.5 integrity gate candidate — awaiting CI
Haswell candidate staging now requires a complete SHA-256 ledger of every user-supplied component file. Input and staged file bytes must match ledger digests. Missing entries, unexpected ACPI files, symlinks, invalid declared provenance/ license fields and tampered bytes cause fail-closed rejection. These checks are local content integrity only, not cryptographic vendor attestation. Expanded regression tests and Windows real ocvalidate smoke must pass before any release claim.

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

## Verified production-readiness tracker CI — 2026-10-18
- Code branch commit `f89bb1026cb8ffe17a37aff3cd7c280e32c8c767` adds machine-readable 26-mandatory-gate tracker and bundled CLI production-readiness check.
- GitHub Actions https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39093338423: **58/58 Linux unit tests passed, 58/58 Windows unit tests passed**.
- Real official OpenCore 1.0.8 schema staging and compiled Windows toolkit smoke tests passed, using intentionally non-bootable third-party fixtures.
- The packaged EXE `release-readiness` command correctly exited 2 and emitted `production_ready:false`, because 23 required production gates remain open or blocked.
- GitHub Actions build artifact ID: `12124025596` (`BlazeHackintosh-v0.1.5-experimental-windows-toolkit`). This is a CI build artifact, **not a new production GitHub Release**.
- The last independently verified downloadable prerelease remains https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.5-alpha.1
- Production remains blocked: no physical macOS boot acceptance, verified component publisher signatures, safe disk migration/recovery, full Windows GUI, installer media or final signing.

## Staged research output readback — verified CI 39096082439 (68 Linux / 68 Windows tests)

Ten new disposable-fixture tests exercise local file consistency, tampering, missing and extra files, unexpected directories, safety marker/status changes, duplicate paths, traversal and malformed digests. Windows CI synthetic Haswell staging now calls standalone stage_audit.py and requires a modified config.plist to be rejected. This checks only an unsigned local ledger; publisher provenance, physical boot and recovery are NOT tested. This synthetic readback matrix passed in CI at commit 5d66e9b5f6003bb653681b62052613a579346446; physical boot and trusted provenance remain untested.

## Publisher verifier committed regression tests — 2026-10-19
- Static regression commit: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/8005d4af5e4e90d2952a5d36df7cc69118d6f29d
- OpenSSL-backed synthetic Ed25519 regression commit: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/ffc5c5c390032d52d0923ac61e9314c32e1615b4
- Verified PR run: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39205370943 — Linux tests **108/108**, Windows tests **108/108**, Windows console package and official OpenCore 1.0.8 research fixture checks **successful**. Publish job intentionally skipped on the PR event.
- Verified push run: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39205366619 — Linux/Windows unit tests, official checker smoke and Windows console packaging **successful**; release-publish step preserved the already-existing alpha tag and did not create a new production release.
- The actual OpenSSL-backed positive and negative signature cases ran on both Linux and Windows (not silently skipped); the tests use generated ephemeral Ed25519 keys, synthetic archives and pinned locally computed digests.
- Scope: testing the committed local signature-verification module against synthetic signatures only. **No real third-party publisher identity or license has been independently established; no verified component asset release bytes, Windows GUI EXE, physical ESP/USB readback, boot test, or macOS installer acceptance.** Do not change `component-auth`, `windows-gui`, or `hardware-acceptance` to verified.

## Verified read-only upstream ZIP audit — 2026-10-19
- Source `archive_integrity.py` and 17 synthetic regressions: commit https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/29a285505daef68642b1a6791882665663531f2b (successful PR/push CI 39210621940/39210614609).
- Failed real ZIP CI (Windows path-stat/fstat mismatch, no wrong-hash or payload bypass): https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39210737623. Corrected source commit: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/881d1081d1c49c8a6a85e883abc445d2af01b8d9 .
- **Verified PASS** https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211050624: 126/126 Python tests on Linux, 126/126 on Windows, actual official pinned OpenCore 1.0.8 archive downloaded into hosted Windows runner. SHA-256 `2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b`, size 10,544,084 bytes, `archive_hash_match:true`, `zip_structure_valid:true`, `zip_entries_seen:306`, `zip_members_checked:258` (CRC checked on streamed file data). OpenCore ocvalidate real native tool accepted only synthetic research fixture; compiled **console** toolkit packaging successful. This DOES NOT establish actual kext/SSDT function.
- No files extracted, no USB/internal drives written. Hash comes from GitHub-published metadata and an earlier project pin, **not independently authenticated publisher signature**. `component_auth_gate_satisfied:false`, `publisher_identity_verified:false`, and `license_clearance_verified:false` in CI report. No signed upstream publisher key, rights clearance, boot verification, real Windows GUI EXE or hardware image readback. Keep production gates unchanged.

## Verified strict offline upstream component manifest, actual OpenCore ZIP — 2026-10-19
- Source commits: [offline five-component manifest/validator](https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/81616eae3039d2fd702b0224c9a2e5446e813aa2) and [real Windows CI inspection](https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/3ac40c4fe36f90bfabd5aea23fbf831f7ed40bf3).
- Actual https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211916219 (PR) and https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39211909404 (push) **COMPLETED SUCCESSFULLY**, 144 Python tests on Linux and 144 on Windows. 18 added synthetic trust boundary checks include spoofed clearance, JSON duplicate keys/NaN, URL restrictions, wrong digests, ZIP hash matches without authentication, and HfsPlus.efi exclusion.
- Hosted Windows runner downloaded actual official OpenCorePkg 1.0.8 RELEASE ZIP and verified **10,544,084-byte** archive with upstream GitHub API SHA256 `2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b`, 306 entries and 258 streamed files. Real offline manifest validation and CRC inspection returned no errors.
- The program **explicitly returns** `publisher_identity_independently_verified:false`, `license_redistribution_cleared:false` and `component_auth_gate_satisfied:false`. GitHub API asset hash/size and LICENSE.txt blob identity are not independent publisher signing evidence. No real Lilu/VirtualSMC/WhateverGreen/AppleALC release ZIP bytes downloaded by this specific step, no hardware boot, no actual installed macOS, and no GUI or physical drive acceptance.

## Unreleased native Windows research GUI — real compiled GUI acceptance, 2026-10-19
- Source commit: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/8fc6717ca8490bf5e6695e055a7c635ef7cef674
- PR full cross-platform CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214560638 and push full cross-platform CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214554240 both **completed successfully**. Linux unit suite 186/186; Windows unit suite 186/186. They include 31 privacy/controller GUI regressions and 11 HWND smoke helper checks, plus prior archive/provenance/regression checks. Windows console packaging is separate from the GUI build.
- PR native GUI CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214560499 and push native GUI CI https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39214554302 **completed successfully**. Windows runner compiled a *windowed* PyInstaller Tkinter `BlazeHackintosh-Research-GUI.exe`; its HWND was visible, belonged to the launched EXE/process tree, and graceful close returned process exit code 0. Not merely unit-tested UI source.
- Downloaded push artifact ID `12168891986`, created 2026-10-19, expires 2026-10-26. CI artifact ZIP SHA-256 `032b391188ffe16a4fbb806956c757e9f200588391f1a4d461a331bf5ca3f033`, contains `BlazeHackintosh-Research-GUI.exe` (12,348,004 bytes) with independently recomputed SHA-256 `f8a86cef1ebf53f91b2c469f2d5486587e7d3f85a9ac526fa17521382aeed6ac` matching bundled `GUI-SHA256.txt`.
- Linux local controller/headless and HWND-helper 42/42 tests passed before commit; synthetic Xvfb Tk window displayed and exited. CI display smoke did not click Scan or test drive writes; GUI is a research workbench, **not** the complete Beginner/Expert Windows installer, and neither it nor console CI proves actual EFI usability/boot, upstream publisher/license authentication, safe USB/ESP migration/rollback or physical hardware compatibility. `windows-gui` mandatory gate stays blocked.

## Read-only 40 MiB synthetic GPT/ESP FAT32 image audit — Windows regression CI, 2026-10-19
- Original source: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/10b2091752aa2ae49d0079459d27154d3b8eb658 ; valid/invalid disk-like image fixtures are ordinary temporary `.img` files, never device paths.
- Superpowers RED: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222279657 at regression-test commit 432153bb5453a953755b2ebb947576265b94192a: missing image-auditor Windows identity helper caused 1 expected error in 237 tests. Fix: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/fb6c1d1607dc9a8473b6ae6b8ac9a13553f61d86; reused existing `archive_integrity._same_opened_file`.
- **Verified passing PR** https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222346177 and **push** https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222341172 at fix commit; each **237/237 Linux and 237/237 Windows tests passed**, including the simulated Windows path/handle identity regression, GPT CRC/partition overlap/bounds/ESP sample checks, official OpenCore 1.0.8 `ocvalidate` on intentionally nonbootable staging and Windows CONSOLE packaging.
- Separate native Windows GUI smoke https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222346195 succeeded with 31 Tk tests, 11 HWND helper tests and compiled windowed research GUI visible HWND + exit 0.
- FAT32 FSInfo trailing signature `FSI_TrailSig` must be at offset 508; source: Microsoft FAT32 specification v1.03 (2000), pp. 21–22, https://www.cs.fsu.edu/~cop4610t/assignments/project3/spec/fatspec.pdf . The baseline fixture and committed code use this offset.
- **Scope limit:** image source/expected digest fixture consistency and structural plausibility only. No actual filesystem integrity or EFI file checks, no physical drive readback, USB restore, recovery/rollback acceptance, publisher provenance, signed installer or boot test. `physical_readback_verified:false`, `filesystem_verified:false`, `boot_verified:false`, `safe_to_flash:false`. Do not mark esp-img or usb-img gates verified.

## Disposable ordinary-file GPT image copy/corruption/restore — CI 2026-10-19
- Test-only commit: https://github.com/BlazingSystems/BlazingSystems-Experiments/commit/ffdaa7b898fc52ec6dc9d34015aa314d5cb2e78f
- Successful PR https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39224322821 and branch push https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39224317558; **239/239 Python tests on Linux and 239/239 on Windows**, including both new temporary-file tests, previous OpenCore 1.0.8 schema fixture and Windows console package smoke.
- Actual operations under `TemporaryDirectory`: standard-library copy into temporary .img, audit digest/GPT/ESP; deliberately damage copied GPT header, audit rejects; restore temporary backup via `os.replace`, audit accepts; separately reject an interrupted partial image write. No user-specified destination devices, USB targets, mounts, partition changes or real boot media.
- Limits: this verifies a disposable-file corruption/rollback *regression test*, **not a production imaging/migration implementation or physical USB roundtrip**. `physical_readback_verified=false`, `filesystem_verified=false`, `boot_verified=false`, `safe_to_flash=false`. No production gate was promoted.

## Read-only FAT32 EFI BOOTX64.EFI file-content readback — 2026-10-30
- New draft successor PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/257 (old PR #105 remained closed/unmerged).
- TDD RED https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988387682 at test-only commit `75e6928d189201ce64b1dc9a17f5ab880642a859`: 240 discovered tests, expected one import failure because the module was not yet present.
- TDD GREEN https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988558649 at implementation commit `e15f94da1a7bd32bb6f0b67330a286dba058a34d`: **245/245 Linux and 245/245 Windows Python tests passed**, official OpenCore fixture and existing Windows console packaging jobs succeeded. No new alpha or production release.
- Tests construct a disposable synthetic FAT32 root with short-name `EFI/BOOT/BOOTX64.EFI`; its 700 payload bytes span FAT clusters 5 and 6. Read-back hashes the file bytes against an independently supplied expected digest while confirming the full regular-file disk image hash. Cases reject file-data tampering despite a recalculated image hash, a cyclic FAT chain, missing path, unsupported LFN entry and wrong image hash.
- The pass is a narrow regular-file ZIP-free FAT32 *specific-file* inspector, **not** a general filesystem consistency test, a signed/authenticated EFI release, a bootable USB image, physical disk readback, rollback acceptance, or a verified boot. All production gates remain unchanged.

## FAT32 EFI directory/file cluster cross-link rejection — CI 2026-10-30
- RED regression commit https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1429f318bb2ce49d465f5f2dc078b6767f7037ef, https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41005316485: **247 discovered, 2 expected FAIL**. Both malformed synthetic FAT32 regular-file .img fixtures were previously accepted as matching the SHA-256 pins despite reusing a directory cluster for `EFI/BOOT` or `BOOTX64.EFI`.
- GREEN commit https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c06e8e56d23e630400049671e23f1f48c783497f, https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41005392462: **247/247 Linux and 247/247 Windows unit tests passed**. Existing official OpenCore 1.0.8 synthetic ocvalidate checks, other release metadata tests and Windows console packaging passed.
- One shared `used_clusters` set rejects cycles and cross-links among clusters traversed in exactly the designated `EFI/BOOT/BOOTX64.EFI` path. No general filesystem walk, source-signature trust proof, real EFI executable, physical ESP or disk imaging. Production `esp-img`, `usb-img`, `release-security` and hardware acceptance gates remain unchanged.
