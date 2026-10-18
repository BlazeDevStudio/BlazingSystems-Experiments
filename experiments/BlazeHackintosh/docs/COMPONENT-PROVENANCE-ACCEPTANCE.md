# Component provenance acceptance — production gate (unverified)

This is an acceptance contract, **not proof that any component is authentic**. The current operator-authored component_manifest.py checks integrity against operator-provided hashes and asserted URLs, not publisher identity.

## Required evidence for each component

- Record exact component filename, semantic version, upstream project/release URL, download URL, and license text with redistribution obligations.
- Record SHA-256 of the downloaded release archive **and** each selected binary, and record which archive member produced the binary.
- Authenticate publisher identity using an independently established trust anchor (e.g. verified signed release or signed checksum manifest with pinned public-key fingerprint). An HTTPS URL alone or an operator-entered digest is not authentication.
- Record trust-anchor acquisition and key-rotation procedure, signature validation command/tool version, expected signing identity, and raw verification evidence. Reject missing, revoked, expired, mismatched, or unverifiable signatures; do not silently downgrade to unsigned acceptance.
- If upstream publishes no verifiable signature, mark provenance **unverified** and block production. Reproducible builds may provide additional assurance but do not automatically establish identity.
- Verify downloaded artifacts before extraction; reject archive traversal, links, duplicate paths and ambiguous member selection. Verify the exact extracted binary hash again after staging.
- Check licenses and notices for OpenCore, kexts, ACPI SSDTs, and filesystem drivers independently. Do not bundle Apple macOS installer binaries.

## Acceptance test matrix

Valid signed fixture with pinned fingerprint must pass; altered archive, altered detached signature, wrong signer, revoked key, missing signature, incorrect release version, untrusted redirect, duplicate archive member, path traversal, and post-extraction tampering must fail closed. Tests must run on Linux and Windows, including a packaged-toolkit smoke test. Keep synthetic test signatures distinct from genuine upstream trust anchors.

## Release evidence required

Per-component source/license/signature ledger, pinned trust-anchor fingerprints, cross-platform CI results, reviewer signoff, and reproducible archive hashes. Until all exist, keep `component-auth` **blocked** in `Production/RELEASE-GATES.json`. Successful OpenCore `ocvalidate` or local SHA-256 checks do not change this gate.
