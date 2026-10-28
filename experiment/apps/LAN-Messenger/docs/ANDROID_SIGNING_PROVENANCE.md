# Android APK signing provenance and upgrade continuity

## Verified problem

The current public v0.3.1–v0.3.5 preview packages were built on separate
ephemeral GitHub Actions runners after `flutter create --platforms=android`.
The generated Flutter Android project uses **debug keystore signing** for
local release-variant builds unless a persistent signing configuration is
provisioned. Distinct runner-generated certificates prevent normal
`adb install -r` / in-place upgrades for the same application ID.

A different signing certificate is **not** evidence of malware; it is
nevertheless a production-release and data-preservation blocker. Do not
recommend uninstalling a prior app without warning that it removes its
app-private identity and conversation state.

## What this draft implements

- A matching **public** certificate pin is **not** proof that a persistent
  private release keystore was securely provisioned. Accordingly, the report
  explicitly marks `release_signing_certified=false`,
  `signing_key_provenance=unverified`, and
  `upgrade_continuity_certified=false` until a separate release-key
  provisioning and evidence gate exists.

- `tool/apk_signing_audit.py` runs the platform `apksigner verify
  --verbose --print-certs` on every real compiled ABI APK.
- Requires exactly one signer for each APK and the same public SHA-256
  certificate fingerprint across ARM32, ARM64, and x86_64.
- Publishes `SIGNING-PROVENANCE.json` as a separate entry in the
  existing Android CI artifact, without key material.
- Public GitHub Actions repository variable
  `LAN_MESSENGER_ANDROID_SIGNER_SHA256`, if set, is an **enforced** expected
  signer fingerprint: mismatches fail the Android job, blocking dependent
  emulators and evidence-gated publisher.
- When the variable is absent, the audit labels builds **unpinned developer
  previews**. Their passing CI does not establish upgrade continuity.
- To require a pin in a future production-only workflow, set environment
  `LAN_REQUIRE_PINNED_SIGNER=1` for the audit invocation. No change to
  current preview semantics is implied by this draft.

## What it does not implement

This audit does NOT provision a permanent signing key or turn the debug-key
build into a production-signed APK. Setting the public expected fingerprint
alone does not sign anything. The owner must separately arrange a **single
securely backed-up, stable release keystore** and encrypted credentials via
the repository's authorized secret manager, update the generated Gradle
release signing configuration, then verify all ABI APK fingerprints against
the intended public pinned digest.

Never place a `.jks`, `.keystore`, unencrypted password or base64 private
key in a public Git repository, commit, workflow output or build artifact.
Never copy a private debug keystore between unrelated users or forks.

## Phone installation debugging

Inspect the package-installer diagnostic before attributing every
`App not installed` to signing: `INSTALL_FAILED_UPDATE_INCOMPATIBLE`
signals a signing mismatch on update, but `NO_MATCHING_ABIS`, insufficient
storage, Play Protect policy and device constraints are distinct cases.
An uninstalled app should not normally retain a conflicting signing
certificate for that user, so physical `App not installed` still needs
the phone's installer failure reason.

## Verification

The unit self-test uses synthetic public fingerprints, including missing
and malformed certificate output. Real CI uses official Android SDK
`apksigner` for each compiled APK and fails on mismatches; release
readiness still requires normal build, Android install, WebRTC voice/video,
peer-death recovery, and physical Windows crash acceptance.
