# Handover Log — 2026-10-06 — v0.5.1 Published

## Result

BlazePwifi `v0.5.1` is published as a validated GitHub prerelease.

Release:
`https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.1`

Release ID:
`404404262`

Exact released candidate:
`65f87d775793a1fdc09a9522cf752349f68c3b41`

Validated build run:
`37425063793`

Release workflow:
`37426030884`

Both build and release workflows completed successfully.

## What changed

v0.5.1 adds the requested no-reflash maintenance path for ordinary BlazePwifi feature/revision updates:

- transactional overlay update bundles;
- exact SHA-256 verification;
- configurable HTTPS update source;
- last-known-good snapshots;
- immediate rollback on failed apply/health checks;
- boot health rollback guard;
- configurable stability grace;
- bounded rollback snapshot retention;
- manual rollback through Management Console → Updates & Recovery;
- one-time v0.5.0 → v0.5.1 bootstrap updater;
- persistent operator/session state excluded from blind overlay replacement.

BlazeRental v0.5.1 adds:

- version code `50100`;
- centrally published update metadata;
- exact APK SHA-256 verification;
- exact package-name verification;
- installed signing-certificate equality check;
- Android PackageInstaller replacement;
- previous APK/version metadata retention;
- delayed health promotion after the launcher remains alive;
- repeated-failed-boot recovery trigger;
- rollback-rescue build based on known-good v0.5.0 code with recovery version code `50101`;
- native Admin update/check/rollback controls;
- central Rental Update Manager in BlazePwifi.

## Validation

Exact build run `37425063793` passed:

- static checks;
- legacy v0.3/v0.4 compatibility suites;
- BlazeRental production source gates;
- v0.5 launcher source contract;
- v0.5.1 transactional update/rollback regression;
- v0.5.1 BlazeRental update contract;
- server Rental API tests;
- security/config/integration tests;
- persistence/replay stress tests;
- Android APK build;
- Android Device Owner emulator;
- browser simulation;
- ESP8266/ESP32 simulations;
- Ruijie simulation;
- x86 simulation;
- required Orange Pi simulations;
- final candidate gate.

Custom BlazeRental package scan found no TODO/FIXME/HACK/placeholder markers under:
`android/BlazeRentalLauncher/src/com/blazesystems/blazerental/`

## Published update/recovery assets

- `BlazePwifi-v0.5.1-update.tar.gz`
- `BlazePwifi-v0.5.1-update-bootstrap.sh`
- `BlazePwifi-v0.5.1-update-bootstrap.sh.sha256`
- `BlazeRental-v0.5.1-TEST.apk`
- `BlazeRental-v0.5.1-release-unsigned.apk`
- `BlazeRental-v0.5.0-rescue-for-v0.5.1-TEST.apk`
- `BlazeRental-v0.5.0-rescue-for-v0.5.1-release-unsigned.apk`
- normal firmware/controller assets;
- `CANDIDATE-GATE.json`;
- `RELEASE-MANIFEST.json`;
- `SHA256SUMS`.

## Android production signing blocker

Locked signing run:
`37425929657`

Result:
**FAILED SAFELY**

Failure step:
`Restore exact locked v0.4 production identity`

The exact v0.4 production signer / `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` is still unavailable.

The workflow refused certificate rotation.

Therefore:
- no fake/replacement production certificate was generated;
- production `BlazeRental.apk` is intentionally absent;
- signed rollback-rescue APK is intentionally absent;
- the GitHub release remains a prerelease.

Locked expected fingerprint:

`C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

## Remaining limitations

- Runtime package replacement is validated by source contracts and Android build/emulator coverage, but a production-signed field update cannot be exercised until the exact production signing identity is restored.
- Full firmware/sysupgrade is still required for kernel, bootloader, partition layout, base ABI/filesystem, or incompatible target changes.
- Hardware field validation remains required for each physical target before calling it field-proven.

## Next action

1. Merge the v0.5.1 implementation and handover records into `main`.
2. Preserve the released tag at exact candidate `65f87d775793a1fdc09a9522cf752349f68c3b41`.
3. When the exact locked signer is restored, rerun the v0.5.1 signing workflow against build run `37425063793`.
4. Verify both normal and rescue APK fingerprints.
5. Refresh `v0.5.1` with production `BlazeRental.apk` + signed rescue and promote out of prerelease.
6. Do not rebuild or retag unnecessarily if the exact validated candidate is unchanged.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue BlazePwifi from the published v0.5.1 state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read experiment/openwrt/BlazePwifi/docs/handover/2026-10-06-v051-release-published.md and newer logs if present.
3. Verify GitHub Release v0.5.1 exists, is prerelease, and targets exact candidate 65f87d775793a1fdc09a9522cf752349f68c3b41.
4. Verify build run 37425063793 passed including v0.5.1 transactional update/rollback tests, BlazeRental update contracts, Android Device Owner emulator, platform simulations and final candidate gate.
5. Verify release run 37426030884 passed and update/bootstrap/Rental rescue assets are present.
6. Verify locked signing run 37425929657 failed only because the exact locked v0.4 signer/recovery private key was unavailable and that no certificate rotation occurred.
7. Preserve the update architecture: transactional overlay updates, last-known-good rollback, stability grace, bounded retention, v0.5.0 bootstrap updater, same-signer Rental APK verification, health promotion and rescue APK.
8. Preserve production signing identity C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24. Never silently rotate it.
9. Merge the v0.5.1 implementation/handover into main if not already integrated.
10. If the exact signer becomes available, sign the existing validated candidate and refresh/promote v0.5.1 without unnecessary rebuilds.
11. Update PROJECT_HANDOVER.md and add a dated handover log after every meaningful success/failure with a fresh Audit & Reconcile prompt.
```
