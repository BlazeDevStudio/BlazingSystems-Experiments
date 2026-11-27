# Handover Log — 2026-10-06 — v0.5.0 Integrated Into Main

## Success

The full released BlazePwifi v0.5.0 implementation is now integrated into the repository default branch.

## Conflict reconciliation

Original implementation-to-main PR #11 exposed conflicts because main had 18 newer commits.

The main-only delta was audited and reduced to 16 paths:
- BlazePwifi handover/spec logs;
- offline preview ZIP/README;
- unrelated Easymode encrypted release files.

A two-parent integration commit was constructed from the complete v0.5 implementation tree while overlaying those 16 main paths byte-for-byte.

Integration SHA:
`09710a6d093f125a444c86bc686985edbfc89553`

Integration tree:
`d8fe2e6b6fca5ee3f619bc1d2e8ab35c4abcc850`

## Validation

Exact integration build run:
`37396023917`

Result: **PASS**

It passed:
- static/security/config/integration validation;
- BlazeRental Android build;
- Android Device Owner emulator;
- browser simulation;
- ESP8266/ESP32 build + simulation;
- Ruijie build + simulation;
- x86 build + QEMU simulation;
- required Orange Pi builds + simulations;
- final candidate gate.

## Merge

PR #12:
`release: integrate BlazePwifi v0.5.0 into main`

Result: **MERGED**

Main merge commit:
`06ddc5909b178d316f0f4d6fb8104f64da9a1be9`

The resulting main tree is exactly the already-validated integration tree.

Superseded conflicted PR #11 was closed without merging.

## Release/signing boundary

GitHub Release `v0.5.0` remains a validated prerelease pinned to exact RC9 candidate:
`66e159b65b6d8fb5f74dd981dc73d46db7229adc`

The tag was not moved during main integration.

Production `BlazeRental.apk` remains absent because locked v0.4 signing identity recovery is still unavailable. Signing run `37327439782` attempt 2 failed safely and explicitly refused certificate rotation.

## Next action

When the exact locked v0.4 signer is restored:
1. rerun the v0.5 locked signer against RC9/build run `37326542666`;
2. verify exact fingerprint;
3. add production `BlazeRental.apk` + signing manifest/fingerprint to v0.5.0;
4. verify release checksums/assets;
5. promote v0.5.0 out of prerelease.

Until then, keep TEST/unsigned Android assets clearly labeled and do not rotate the certificate.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi after the v0.5.0 main integration.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest file under experiment/openwrt/BlazePwifi/docs/handover/.
3. Verify main contains merge commit 06ddc5909b178d316f0f4d6fb8104f64da9a1be9 or a descendant and that the full BlazePwifi v0.5 implementation exists on main.
4. Verify integration run 37396023917 passed for exact SHA 09710a6d093f125a444c86bc686985edbfc89553, including Android Device Owner and final candidate gate.
5. Verify PR #12 is merged and PR #11 remains closed/unmerged.
6. Verify GitHub Release v0.5.0 still targets exact validated RC9 candidate 66e159b65b6d8fb5f74dd981dc73d46db7229adc and has not been silently retagged.
7. Verify locked-signing run 37327439782 remains blocked only by unavailable exact v0.4 signing material; never rotate the production Android certificate silently.
8. If the locked signer is now available, rerun production signing against the existing validated RC9/build run rather than rebuilding unnecessarily, then promote the release after verifying assets/checksums.
9. Preserve all main-only preview/handover/Easymode files and the approved v0.5 architecture.
10. Update PROJECT_HANDOVER.md and add a dated handover log after every meaningful success/failure, always leaving a fresh Audit & Reconcile prompt.
```
