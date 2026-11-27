# Handover Log — 2026-10-06 — v0.5.1 Safe Update Architecture

## Owner request

Release v0.5.1 with:
- feature/revision updates that do not require reflashing the whole BlazePwifi system;
- safe fallback/rollback to the previous stable, longer-running version when an update is bad;
- equivalent update/recovery handling for BlazeRental;
- completion of remaining Rental-app reliability work rather than leaving it stuck in an unfinished candidate loop.

## Implemented architecture

### BlazePwifi

Normal feature revisions use a transactional overlay bundle rather than a complete firmware image.

Safety sequence:
1. Download from configured HTTPS update source.
2. Verify exact bundle SHA-256.
3. Validate archive paths and per-file manifest.
4. Snapshot files being replaced into persistent rollback storage.
5. Apply allowlisted files.
6. Run migration idempotently without replacing customer/operator state wholesale.
7. Run immediate health checks.
8. Mark the new version as pending.
9. Boot guard continues health checks.
10. Promote to stable only after configured grace.
11. Automatic or manual rollback restores the preserved previous version.

Full firmware/sysupgrade remains for kernel/bootloader/partition/base-ABI/filesystem changes.

A one-time bootstrap script allows v0.5.0 systems, which predate the updater, to install the v0.5.1 transactional updater without a full reflash.

### BlazeRental

Normal v0.5.1 version code:
`50100`

Rollback rescue:
- exact known-good v0.5.0 RC9 application source:
  `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- recovery-only version code:
  `50101`
- version name:
  `0.5.0-rescue-for-0.5.1`

This lets Android accept the rollback code as a forward package install instead of an ordinary downgrade.

The Rental updater verifies:
- HTTPS source;
- exact SHA-256;
- package identity;
- exact published versionCode;
- same signing certificate as the installed BlazeRental.

The current APK is copied to private app storage before install. A new build is only promoted to stable after a 30-second successful launcher health window. Repeated boots before promotion can trigger a published rescue APK.

Native Rental Admin includes:
- Check BlazePwifi for update
- Install available update
- Roll back to last stable rescue

The management console includes a central BlazeRental Update Manager.

## Security boundary

Production normal/rescue APKs must use the exact locked v0.4 production signing identity. v0.5.1 signing workflow refuses silent certificate rotation.

Update actions remain authenticated/role/CSRF protected and are not exposed to captive-portal users.

## Test coverage added

- `tests/v051_update.sh` performs a real temporary transactional apply + rollback test.
- `tests/v051_android_source.sh` locks same-signer, rescue, versioning, boot fallback and health-window source contracts.
- v0.5 regression contracts remain enabled and maintenance-compatible.
- Existing Android Device Owner emulator and platform simulation matrix remains required.

## Current development branch

`blazepwifi-v0.5.1-implementation`

## Next action

1. Validate shell/static tests after admin CGI repair.
2. Finish CI artifact naming and v0.5.1 release/signing workflow validation.
3. Cut exact RC1 branch from a stable implementation head.
4. Run full matrix including Android Device Owner emulator.
5. Fix only evidence-backed failures; create new RC when necessary.
6. When green, attempt locked signing.
7. Publish and verify `v0.5.1`; use prerelease/test+unsigned Android labeling if the locked signer is still unavailable.
8. Integrate the released code back into `main`.

## Audit & Reconcile prompt

```text
@GitHub Audit and continue BlazePwifi v0.5.1 Safe Updates & Recovery.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read experiment/openwrt/BlazePwifi/docs/handover/2026-10-06-v051-safe-update-architecture.md.
3. Inspect branch blazepwifi-v0.5.1-implementation and the newest exact candidate/RC branch.
4. Audit the transactional BlazePwifi updater: SHA validation, path allowlist, snapshots, health gate, boot guard, stability promotion, retention and manual rollback.
5. Audit the one-time v0.5.0 bootstrap and confirm it does not require full firmware reflashing.
6. Audit BlazeRental updater: same package/signing identity verification, version code 50100, exact RC9 rollback-rescue code with versionCode 50101, health-window promotion and repeated-boot rescue.
7. Preserve the existing v0.5 launcher/Device Owner/rental security behavior and run the full existing emulator/simulation matrix.
8. Never silently rotate the production Android signer. If unavailable, keep production APK absent and label TEST/unsigned artifacts clearly.
9. Publish v0.5.1 only from an exact green candidate SHA, verify all release assets/checksums/manifests, then integrate into main.
10. Update PROJECT_HANDOVER.md and add a dated log after every meaningful failure/fix/success, always including a fresh Audit & Reconcile prompt.
```
