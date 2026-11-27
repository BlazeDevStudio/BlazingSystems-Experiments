# BlazePwifi Standalone Rental Server v0.5.2-rental.2-rc.4

RC4 continues the provisioning architecture audit and keeps RC1/RC2 immutable.

## RC4 corrections

- uses canonical padded Base64URL SHA-256 for `PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM`;
- publishes exact APK SHA-256, Setup Wizard checksum, and TEST signer-certificate SHA-256;
- OpenWrt tar/OneClick and EW1200G/x86 firmware receive provisioning metadata through the same release-metadata builder;
- adds `GMS_DPC_APPROVED` to the metadata/API contract;
- requires explicit acknowledgement before generating a Device Provisioning QR when the DPC is not declared approved for GMS provisioning;
- labels that path for AOSP/non-GMS or explicitly supported test targets rather than implying universal Android compatibility.

## Google-certified Android limitation

Google-certified Android can block a custom DPC that is not approved for Android Enterprise provisioning. BlazeRental RC4 does not claim universal Device Owner provisioning support on those devices.

Official policy reference:
https://support.google.com/work/android/answer/16694822

## QR contracts

**Standard Enrollment QR**
- scanned inside already-installed BlazeRental;
- schema `blazerental.enrollment.v1`;
- 10-minute one-time server binding token;
- no Device Owner claim.

**Device Provisioning QR**
- scanned from Android Setup Wizard on new/factory-reset devices;
- schema `blazerental.provisioning.v1`;
- exact HTTPS TEST APK asset;
- canonical padded Base64URL SHA-256 package checksum;
- Android integrated provisioning activities;
- one-hour one-time server enrollment token;
- explicit custom-DPC/GMS warning gate.

## Promotion boundary

Still a prerelease. Stable promotion requires physical Setup Wizard validation on intended hardware/Android versions, production signing continuity, and a supported policy/compliance path for the intended deployment environment.


## RC4 target scope

Device Provisioning QR in this candidate is **OpenWrt-server only**. ESP8266/ESP32 Rental Server mode keeps manual one-time token enrollment and does not claim QR provisioning parity in RC4. This limitation is encoded in the release manifest.


## TEST signer lifecycle

The RC4 provisioning APK uses a release-build TEST signing identity. It is intended for disposable physical Setup Wizard validation. In-place upgrades between provisioning RCs are not guaranteed; a factory reset may be required when testing a later RC. Stable promotion still requires production signing continuity.


## RC4 release-integrity correction

RC4 is a new immutable candidate because RC3 already exists.

Additional RC4 corrections:

- Device Provisioning QR generation is restricted to administrators; Standard Enrollment remains available to operators.
- The release assembler preserves canonical padded Base64URL APK checksums instead of truncating the trailing `=` during metadata parsing.
- Android package identity is `0.5.2-rental.2-rc.4` with versionCode `50205`.
- The dedicated Rental provisioning pipeline and the repo-wide BlazePwifi build are both required to remain green.

This remains a TEST-signed provisioning candidate. `production_ready:false` and physical Android Setup Wizard validation remain mandatory before production promotion.
