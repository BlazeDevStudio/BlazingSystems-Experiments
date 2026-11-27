# BlazePwifi v0.5.3 — Rental Hardening, Remote Operations & Central Members

BlazePwifi v0.5.3 promotes the validated v0.5.3 development line to production identity.

## Major changes

### BlazeRental and Android onboarding
- Separate Binding QR and Device Owner Provisioning QR flows.
- Factory-reset provisioning uses the signed production APK and exact package checksum.
- Enrollment is retry-safe and authenticates the returned permanent identity before storage.
- Separate server-authoritative rental-time and Insert Coin reservation countdowns.
- Accepted coin pulse/value progress is visible and replayed events cannot add credit twice.

### Management Console
- Dual CSRF transport with stale-session refresh/retry.
- Advanced Terminal is disabled by default and requires fresh admin re-authentication, session/IP binding, bounded runtime/output and single-command concurrency.
- Expanded safe diagnostics.
- Remote Access supports WireGuard and ZeroTier with separate Monitoring, Management and Remote Terminal permissions.

### Transactional remote access
- WireGuard private key and ZeroTier secret identity remain on-device.
- Browser/API exposes public identity only.
- Live apply is transactional with snapshots, watchdog/reboot recovery, route-survival checks and safe rollback.
- Remote admin uses a restricted tunnel-only HTTPS service.
- WireGuard and ZeroTier live transports are mutually exclusive.

### Central BlazePisonet SoftTimer members
- BlazePwifi is the central member and banked-time authority when integration is enabled.
- Member CRUD, password reset, balance changes, transfers and event history are centralized.
- Integrated authentication/balance mutation fail closed when BlazePwifi is unreachable.
- Metadata migration is verifier-free, preview-first, collision-aware and transactionally rollback-safe.

## Android production identity
- Package: com.blazesystems.blazerental
- Production versionName: 0.5.3
- Production versionCode: 50300
- Certificate lineage: BlazeRental-production-lineage2
- Required SHA-256 certificate fingerprint:
  1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25

Devices already running v0.5.2 Lineage 2 can accept v0.5.3 as a normal same-package, same-certificate upgrade.

## Android rollback rescue
The recovery APK uses the exact frozen v0.5.2 application source and the same Lineage 2 certificate.

- recovery versionName: 0.5.2-rescue-for-0.5.3
- recovery versionCode: 50301

The recovery code is higher than production 50300 so Android can install the known-good rescue after a failed v0.5.3 deployment.

## QR onboarding assets
- `BlazeRental-Binding-QR.html` is for an **already-installed** BlazeRental app. It contains only binding details: server URL, one-time enrollment token, device label, and optional TLS certificate pin. It does not download/install an APK and does not grant Device Owner.
- `BlazeRental-DeviceOwner-Provisioning-QR.html` is for a **factory-reset / unprovisioned** Android device. It contains Android enterprise provisioning fields and the checksum of the exact signed production APK.
- Device Owner provisioning is HTTPS-only for both the BlazePwifi server URL and APK download URL; standard Binding QR remains the separate already-installed flow.
- These generators are intentionally separate. The standard Binding QR must never be treated as a Device Owner provisioning QR.
- `BlazeRental-provisioning-SAMPLE.json` is a non-operational reference with placeholder token/pin values. No scannable sample Device Owner QR image is published, to prevent accidental provisioning with dummy enrollment data.

## Device Owner provisioning
Production Device Owner QR/provisioning assets are generated only after production signing and use the exact signed BlazeRental.apk.

The release stage verifies the provisioning package checksum against the signed APK before publication.

Never generate production provisioning QR assets from the unsigned/CI APK.

## Required release validation
Publication requires one exact candidate commit to pass:
- static/security/config/integration/replay validation;
- WireGuard and ZeroTier network-survival suites;
- central member and migration regression;
- browser runtime;
- Android current and rescue build;
- Android Device Owner emulator;
- ESP8266/ESP32;
- Ruijie;
- required Orange Pi targets;
- x86 QEMU;
- transactional update bundle;
- final candidate gate;
- Lineage 2 signing fingerprint/package/version verification;
- signed provisioning-checksum validation;
- signed rescue validation.

## Scope guard
profiles/standalone-rental is a separate reference/release line and is not modified by this Full BlazePwifi release.
