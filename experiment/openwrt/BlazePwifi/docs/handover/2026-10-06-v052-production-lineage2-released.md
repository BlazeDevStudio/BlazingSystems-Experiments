# Handover Log — 2026-10-06 — v0.5.2 Production Lineage 2 Released

## Result

BlazePwifi **v0.5.2** is now a full production GitHub release using the new permanent BlazeRental Production Lineage 2 certificate.

Release:
`https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.2`

Release ID:
`404545281`

Exact frozen application candidate:
`bf2992977fe8504d21b107df02826032c31d3a62`

Exact validated build:
`37443570618` — PASS

Production signing:
`37448352082` — PASS

Production promotion:
`37448830953` — PASS

The release is no longer marked prerelease.

## v0.5.2 product changes

- supplied LCM artwork is used for BlazeRental production branding;
- BlazeRental 0.5.2 / versionCode 50200;
- Near End alarm defaults to 10 minutes remaining / 5-second ring;
- Urgent Add Credit alarm defaults to 3 minutes remaining / 10-second ring;
- Time's Up alarm triggers at 00:00 / 15-second ring;
- alarm thresholds, durations, minimum volume and sound source are configurable;
- built-in/device/custom sounds are supported;
- device ringtone picker disables Silent;
- active rental alarms use STREAM_ALARM and enforce a nonzero minimum volume while ringing;
- DND Notification Policy access can temporarily allow the alarm through Total Silence when the OS grants access;
- prior audio/DND state is restored after alarm playback;
- alarms fire once per lease and re-arm when credit extends the lease;
- existing transactional no-reflash updates and rollback remain intact.

## Production signing identity

Lineage:
`BlazeRental-production-lineage2`

Permanent certificate SHA-256 fingerprint:

`1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`

Production BlazeRental.apk SHA-256:

`d0ad20bed00ea304db9bff45928542fed574070d416ed65b4fbf3d8ba23d7102`

Production rescue APK SHA-256:

`a1c8d759405842b85879c77e9525b1a6e9c4f6d62eb8bda9b0abc60fb899d513`

Signing artifact:
`11404278200`

## Recovery architecture

The production P12/password are not stored in Git.

The signer backup is encrypted with AES-256-GCM and its AES key is independently wrapped to two RSA-3072 recovery public keys using RSA-OAEP-SHA256.

Recovery A:
- public key committed to Git;
- private key retained in the owner's private ChatGPT Library at `/BlazePwifi Signing Recovery/`.

Recovery B:
- public key committed to Git;
- private key packaged as an independent owner/offline recovery copy.

Both Recovery A and Recovery B were actually tested end-to-end:
1. decrypt wrapped AES key;
2. decrypt authenticated signer backup;
3. extract P12/password;
4. read the P12 certificate;
5. verify fingerprint equals the permanent Lineage-2 fingerprint.

Both drills PASS.

Permanent entry point:
`experiment/openwrt/BlazePwifi/SIGNING_RECOVERY.md`

Machine-readable identity:
`.github/blazerental-v052-production-identity.json`

Recovery helper:
`experiment/openwrt/BlazePwifi/tools/recover-blazerental-v052-lineage2.sh`

## Release assets

Production release now includes:

- `BlazeRental.apk`;
- `BlazeRental-v0.5.1-rescue-for-v0.5.2.apk`;
- signing certificate/fingerprint;
- signing verification logs;
- signing/recovery manifests;
- encrypted production signer backup;
- Recovery A/B wrapped AES-key assets;
- both recovery public keys;
- unseal helper;
- production Device Owner QR setup HTML;
- production provisioning sample JSON/PNG;
- no-reflash v0.5.2 update assets;
- firmware/controller assets;
- release manifest and release-level SHA256SUMS.

## Validation evidence

Build run `37443570618` passed:
- compatibility/static/security/config/integration/stress suites;
- v0.5.2 LCM/alarm contracts;
- LCM PNG structure/CRC validation;
- Android normal + v0.5.1 rescue APK build;
- Android Device Owner emulator;
- transactional v0.5.2 update/rollback tests;
- browser/ESP/Ruijie/x86/Orange Pi simulations;
- final v0.5.2 candidate gate.

Signing run `37448352082` passed:
- exact candidate/run verification;
- one-time Lineage-2 key creation;
- main and rescue APK signing;
- v2/v3 APK signature verification;
- package/version verification;
- certificate export/fingerprint capture;
- dual encrypted recovery creation.

Release run `37448830953` passed:
- exact build/signing input verification;
- signed asset import;
- release-level rechecksums;
- production QR/provisioning generation;
- GitHub release asset upload;
- prerelease flag cleared only after signed/recovery/QR assets were verified present.

## Signing workflow issue and fix

The first Lineage-2 workflow definition had an invalid YAML heredoc indentation, so GitHub created zero-job failures and ignored its path filter.

No signing identity was created by those failures.

The workflow was repaired in commit:
`bce91e118f4729932b2c39af5192b97aaeebcb65`

The successful one-time signing request then ran as `37448352082`.

The successful signing artifact's internal SHA256SUMS referenced two temporary aligned APK files that were deleted before upload. Every retained artifact verified correctly. The workflow bookkeeping was fixed in:
`1fd5720a101a3d88bbe05e70158736983fbbad6e`

The published release recomputed a clean release-level SHA256SUMS.

## Migration boundary

The abandoned v0.4 production certificate cannot update in place to Lineage 2.

Existing devices using the old certificate require reprovision/factory reset for migration.

Once a device is provisioned with v0.5.2 Lineage 2, every future production BlazeRental APK must use the exact permanent fingerprint above.

Do not generate another production signer.

## Next action

1. Reconcile the v0.5.2 implementation branch with current `main`.
2. Preserve any main-only signing-audit/handover documents.
3. Merge the full v0.5.2 application, release tooling, production identity, recovery docs/helpers and final handover into `main`.
4. Do not move the v0.5.2 tag away from candidate `bf2992977fe8504d21b107df02826032c31d3a62`.
5. Keep Recovery A private material outside Git and keep Recovery B offline.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue BlazePwifi from the v0.5.2 production Lineage-2 state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read experiment/openwrt/BlazePwifi/docs/handover/2026-10-06-v052-production-lineage2-released.md and any newer logs.
3. Verify GitHub Release v0.5.2 exists, is NOT prerelease, and targets exact application candidate bf2992977fe8504d21b107df02826032c31d3a62.
4. Verify build run 37443570618 passed, including v0.5.2 alarm/LCM contracts, Android Device Owner emulator, transactional update/rollback, platform simulations and final candidate gate.
5. Verify signing run 37448352082 passed and the permanent production fingerprint is 1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25.
6. Verify production BlazeRental.apk SHA-256 is d0ad20bed00ea304db9bff45928542fed574070d416ed65b4fbf3d8ba23d7102.
7. Verify release run 37448830953 passed and the release contains signed main/rescue APKs, signing/recovery manifests, encrypted dual-recovery signer backup, production QR/provisioning assets and release-level SHA256SUMS.
8. Preserve .github/blazerental-v052-production-identity.json and SIGNING_RECOVERY.md. Never silently rotate Lineage 2.
9. Recovery A private material belongs only in the owner's private ChatGPT Library; Recovery B is the owner/offline copy. Neither belongs in Git.
10. Existing old-v0.4-signed devices require reprovision/factory reset to migrate to Lineage 2.
11. Continue normal BlazePwifi development from v0.5.2, keeping future production BlazeRental releases on this exact signing identity.
12. Update PROJECT_HANDOVER.md and add a dated handover log after every meaningful success/failure, each with a fresh Audit & Reconcile prompt.
```
