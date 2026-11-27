# Standalone Rental Releases

## Provisioning candidate

### v0.5.2-rental.2-rc.7

RC7 supersedes RC6 for physical provisioning testing without modifying the immutable RC6 tag.

Additional RC7 hardening:
- strict OpenWrt Rental Server authority validation before either QR is generated;
- numeric port bounds (1-65535) and bracketed IPv6 handling;
- rejection of missing host, malformed IPv6, userinfo, path, query, fragment, backslash, whitespace and control-character origins;
- BlazeRental repeats origin and TLS-pin checks inside the persistence boundary, independent of the scanner;
- Android package identity is `0.5.2-rental.2-rc.7`, versionCode `50208`.


### v0.5.2-rental.2-rc.6

RC6 supersedes RC5 for testing without modifying the immutable RC5 tag.

Additional hardening:
- Android provisioning callbacks are idempotent when Setup Wizard redelivers identical extras;
- an already-bound phone cannot silently destroy its permanent identity by scanning a new Standard Enrollment QR;
- administrators must use the explicit Transfer action before rebinding;
- Standard Enrollment scanner errors distinguish Device Provisioning QR, already-bound state, and local-storage failure;
- Android package identity is `0.5.2-rental.2-rc.6`, versionCode `50207`.

### v0.5.2-rental.2-rc.5

RC5 supersedes RC4 for testing. It keeps the separated Standard Enrollment / Device Provisioning architecture and closes the first-enrollment transport exposure:

- Standard Enrollment schema `blazerental.enrollment.v2`;
- Device Provisioning admin-extras schema `blazerental.provisioning.v2`;
- enrollment protocol 2 derives the long-lived device secret from the one-time token, nonce and server-issued device ID;
- the long-lived device secret is not transmitted over LAN HTTP;
- the APK verifies an HMAC-signed enrollment response before storing identity;
- the consumed one-time enrollment secret is removed from local storage;
- Android package identity is `0.5.2-rental.2-rc.5`, versionCode `50206`.

### v0.5.2-rental.2-rc.4

RC4 keeps the separated Standard Enrollment / Device Provisioning architecture, requires administrator role for Device Provisioning QR generation, and fixes canonical padded Base64URL checksum parsing in the immutable release assembler.

### v0.5.2-rental.2-rc.3

RC3 supersedes RC2 without modifying older tags/assets.

Key hardening:
- canonical padded Base64URL APK checksum for Android Setup Wizard;
- exact APK SHA-256 + signer-certificate SHA-256 published in release evidence;
- OpenWrt tar/OneClick and EW1200G/x86 firmware share the same exact provisioning metadata generator;
- explicit `GMS_DPC_APPROVED` state and API/UI acknowledgement gate;
- non-approved custom DPC QR is labeled for AOSP/non-GMS or explicitly supported test targets only;
- Standard Enrollment and Device Provisioning remain separate contracts.

### v0.5.2-rental.2-rc.2

Atomic one-time enrollment claims, release-package TEST APK identity, and executable provisioning/race CI.

### v0.5.2-rental.2-rc.1

First published provisioning split candidate; preserved unchanged.

## Latest stable

### v0.5.2-rental.1

CSRF/QR mutation hotfix for the previous single-enrollment-QR flow.

## Older

- v0.5.2-rental
- v0.5.2-rental-rc.2
- v0.5.2-rental-rc.1
