# BlazePwifi Standalone Rental Server

Latest stable server line: **v0.5.2-rental.1**  
Latest audited provisioning candidate: **v0.5.2-rental.2-rc.9**

> **Source-boundary note:** RC9 is an immutable prerelease on its own tag/release and provisioning branch. The current `main` runtime source is not the RC9 runtime baseline. Use the RC9 release/tag for RC9 testing; this page is a discovery/index page only.

RC9 keeps two intentionally separate Android onboarding contracts:

- **Standard Enrollment QR** — BlazeRental is already installed; scan inside BlazeRental; server binding only; no Device Owner claim.
- **Device Provisioning QR** — scan from Android Setup Wizard on a new/factory-reset phone; Android receives the exact DPC APK URL/checksum and provisioning extras, then BlazeRental completes secure server enrollment.

Current RC9 security properties include:

- Standard schema `blazerental.enrollment.v2` and Device Provisioning schema `blazerental.provisioning.v2`;
- enrollment protocol v2 with retry-safe one-time redemption and no long-lived device secret transported in the enrollment response;
- HMAC-authenticated enrollment response before permanent identity is committed;
- HTTPS server certificate pinning and strict origin-only URL validation for Device Provisioning;
- exact APK SHA-256, Android package checksum, signer fingerprint and version bound into release evidence;
- Android 12+ provisioning-mode/compliance integration;
- explicit custom-DPC/GMS scope instead of claiming universal Google-certified-device compatibility;
- first accepted pending Device Provisioning identity pinned to the exact server origin, one-time token and certificate pin;
- exact Setup Wizard callback replay is idempotent, while changed token/server/pin callbacks fail closed;
- stable-promotion gate verifies the actual production APK signer and requires physical Setup Wizard evidence.

RC9 is **TEST-signed** and remains a prerelease. Physical factory-reset Setup Wizard validation and production-signing continuity are still required before stable promotion.

RC9 Device Provisioning is currently an **OpenWrt Rental Server** feature. ESP8266/ESP32 continue to support their Rental Server / coin-interface roles and manual one-time enrollment, but RC9 does not claim Android Device Provisioning QR parity on ESP.

Fresh Standalone Rental console credentials remain `admin / admin`. The Windows package contains the OneClick installer and the Windows admin-password reset tool.

Standalone OpenWrt installation remains network-neutral: it does not take ownership of `network`, `wireless`, or `firewall`.

## Current candidate

- Release: https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.2-rental.2-rc.9
- Release notes: [releases/v0.5.2-rental.2-rc.9.md](./releases/v0.5.2-rental.2-rc.9.md)
- Release history: [releases/README.md](./releases/README.md)

For implementation-level RC9 audit details, inspect `PROVISIONING-AUDIT.md` from the **RC9 tag**, not the older file currently present on `main`.
