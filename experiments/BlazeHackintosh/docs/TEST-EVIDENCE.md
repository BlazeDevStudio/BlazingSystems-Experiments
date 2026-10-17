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
