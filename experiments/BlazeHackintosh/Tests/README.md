# Tests

Run `python -m unittest discover -s Tests -v` from the project directory.
Tests additionally inspect OpenCore config.plist references, invalid/absent payloads,
missing boot components, enabled/disabled entries, duplicated drivers and malicious paths.
Tests cover minimum taxonomy count, explicit Intel/AMD SKU mappings, unknown CPU fallback,
Windows read-only mock inventory, network/GPU PCI ID extraction without PnP serial tails,
storage-size validation, explicit missing-evidence reporting and offline UI import presence,
unverified boot classification, malformed catalog rejection, device-ID redaction and scanner privacy fields.

This is software-unit-level evidence only, not verification of actual Hackintosh booting or image integrity.
Windows CLI packaging is separately handled by GitHub Actions.

Official-ocvalidate bridge tests use mocked subprocess execution and synthetic non-bootable fixtures; only CI's Windows smoke test downloads the genuine upstream asset, verifies its pinned SHA-256, and executes the version-matched utility after explicit invocation. Neither approach performs macOS boot tests.

Candidate staging tests check the exact restricted Haswell profile, missing dependencies, explicit user acknowledgement, no-overwrite output policy, symlink and ZIP ambiguity rejection, and robust cleanup. Windows CI is also configured to stage a deliberately non-bootable EFI folder and invoke the genuine matching ocvalidate before any new toolkit alpha release.

v0.1.5 tests add input/output SHA-256 ledger coverage; synthetic fixture source URLs and license declarations are intentionally **not proof** of publisher provenance. Actual Windows CI must run the synthetic-component staging smoke with a matching ledger and official ocvalidate.
