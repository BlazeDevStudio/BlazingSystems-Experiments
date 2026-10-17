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
