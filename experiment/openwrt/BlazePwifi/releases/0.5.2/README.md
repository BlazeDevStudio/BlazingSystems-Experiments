# BlazePwifi v0.5.2 — LCM Branding & Rental Time Alarms

BlazePwifi v0.5.2 is a maintenance and production-readiness release built from the exact validated candidate `bf2992977fe8504d21b107df02826032c31d3a62`.

## BlazeRental changes

- Production branding now uses the supplied **LCM** artwork for the BlazeRental app icon and native admin/setup branding.
- BlazeRental version: **0.5.2**
- Android versionCode: **50200**
- The release keeps the Launcher3-based rental gate, Device Owner provisioning, daily-driver mode, Notifications/Clear All, app allow/hide policy, managed updates, and rollback recovery from v0.5.1.

## Rental time alarms

BlazeRental now has three configurable on-device rental alarms:

1. **Near End**
   - default trigger: **10 minutes remaining**
   - default ring duration: **5 seconds**
2. **Urgent Add Credit**
   - default trigger: **3 minutes remaining**
   - default ring duration: **10 seconds**
3. **Time's Up**
   - trigger: **00:00**
   - default ring duration: **15 seconds**

The Admin console can configure trigger thresholds, ring duration, forced minimum alarm volume, and sound source.

Sound sources:
- built-in BlazeRental alarm;
- Android device alarm tones;
- custom local audio file.

The Android alarm picker explicitly disables the Silent choice.

### Audible-alarm behavior

Rental alerts use Android's **ALARM** audio stream, not ordinary media volume. While an alarm is active, BlazeRental repeatedly enforces the configured non-zero minimum alarm volume so volume-down cannot reduce that active alarm to zero. The previous alarm/ringer state is restored after the configured ring duration.

For Android/OEM **Total Silence / Do Not Disturb** modes, the on-device admin exposes **Grant DND Alarm Override**. When Android grants Notification Policy access, BlazeRental temporarily permits interruptions during the rental alarm and restores the previous interruption filter afterward.

No Android application can honestly guarantee an audible alarm against every vendor-specific firmware, powered-off device, broken speaker, or policy that the OS refuses to let it override. v0.5.2 therefore uses the strongest supported Android alarm/DND path instead of bypassing the OS.

Alarms fire once per credit/lease session and automatically re-arm when credit extends the lease. Time's Up also reapplies the rental gate for managed rental mode.

## No-reflash update path

The v0.5.1 transactional update architecture remains intact:
- verified overlay update bundles;
- exact SHA-256 verification;
- last-known-good snapshot;
- automatic health rollback;
- boot health guard;
- manual rollback;
- configurable stability grace and retention.

Existing compatible installations can use the v0.5.2 update bundle instead of a full firmware reflash. Kernel/bootloader/partition/base-OS changes still require the appropriate full image update.

## Android rollback rescue

The build includes an exact known-good **v0.5.1 rescue** source with only Android recovery version metadata raised to allow PackageInstaller recovery from v0.5.2.

Initial prerelease Android assets are intentionally:
- `BlazeRental-v0.5.2-TEST.apk`
- `BlazeRental-v0.5.2-release-unsigned.apk`
- `BlazeRental-v0.5.1-rescue-for-v0.5.2-TEST.apk`
- `BlazeRental-v0.5.1-rescue-for-v0.5.2-release-unsigned.apk`

Production signing is a **separate step after this release**. Older 0.5.1 APKs are not being newly production-signed.

## Validation

Exact candidate build run: `37443570618`

Required gates include:
- static/security/config/integration/stress validation;
- v0.3/v0.4/v0.5 compatibility contracts;
- v0.5.2 alarm and LCM branding source contract;
- PNG structure/CRC validation of the LCM production artwork;
- BlazeRental normal + rescue APK build;
- Android Device Owner emulator;
- browser simulation;
- ESP8266/ESP32 builds and simulations;
- Ruijie build/simulation;
- x86 build/QEMU simulation;
- required Orange Pi builds/simulations;
- final v0.5.2 candidate gate.

## Production signing

BlazeRental v0.5.2 establishes the new permanent **BlazeRental Production Lineage 2** certificate.

Fingerprint:

`1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`

Production signing run: `37448352082`

The production release includes:

- `BlazeRental.apk` — signed v0.5.2 production launcher;
- `BlazeRental-v0.5.1-rescue-for-v0.5.2.apk` — known-good rescue code signed with the same Lineage-2 certificate;
- signing certificate/fingerprint and verification logs;
- AES-256-GCM encrypted PKCS12 recovery backup;
- two RSA-OAEP-SHA256 wrapped recovery-key paths;
- production Device Owner QR/provisioning assets generated from the signed APK.

Both independent owner recovery keys were tested by decrypting the sealed backup and verifying the restored PKCS12 fingerprint against the signed APK certificate.

### Migration from the abandoned old signer

The earlier v0.4 certificate lineage is intentionally abandoned.

A phone containing BlazeRental signed by that older certificate cannot accept Lineage 2 as an ordinary APK signature update. Reprovision/factory reset is required for that migration.

Once a device is provisioned with **v0.5.2 Lineage 2**, all future production BlazeRental APKs must use this exact certificate.

Older 0.5.1 application releases are not being newly production-signed.
