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
