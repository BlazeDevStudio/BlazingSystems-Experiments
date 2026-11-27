# BlazePwifi Standalone Rental Server

Latest stable server line: **v0.5.2-rental.1**  
Provisioning architecture candidate: **v0.5.2-rental.2-rc.7**

The provisioning candidate keeps two independent Android onboarding modes:

- **Standard Enrollment QR** — BlazeRental already installed; scanned inside BlazeRental; server binding only; no Device Owner claim.
- **Device Provisioning QR** — Android Setup Wizard on a factory-reset phone; exact APK/checksum; Device Owner only where the platform permits that DPC; then server binding.

RC7 carries the RC5 protocol hardening and all RC6 durability/rebind safeguards, and additionally adds:

- idempotent repeated Android provisioning callbacks without resetting in-progress nonce/device state;
- protection against accidental Standard Enrollment rebinds: an already-bound phone must use the explicit Transfer action first;
- secure enrollment protocol v2: the long-lived device secret is derived independently on server and phone and is never transmitted in the enrollment response;
- HMAC-authenticated enrollment response before the APK persists device identity;
- immediate removal of the consumed one-time enrollment token from phone storage;

- canonical padded Base64URL SHA-256 provisioning checksum;
- exact signer-certificate and APK digests in release evidence;
- one metadata builder shared by OpenWrt tar/OneClick and prebuilt firmware images;
- explicit custom-DPC/GMS compatibility gating;
- GMS approval state in provisioning metadata and API responses;
- AOSP/non-GMS / explicit-test warning when the custom DPC is not approved.

Google-certified Android devices can block non-approved DPCs during enterprise Setup Wizard provisioning. The project does not describe this custom-DPC path as universally production-compatible. See [PROVISIONING-AUDIT.md](./PROVISIONING-AUDIT.md).

Fresh Standalone Rental console credentials remain `admin / admin`. The Windows package includes the one-click administrator reset tool.

Standalone OpenWrt installation remains network-neutral: it does not take ownership of `network`, `wireless`, or `firewall`.


## RC7 target scope

Android Device Provisioning QR is implemented on the **OpenWrt Rental Server** path in RC7.

ESP8266/ESP32 Rental Server mode continues to support manual one-time server/token enrollment, but does not yet render Standard Enrollment QR or Android Device Provisioning QR. The release manifest declares this explicitly rather than implying OpenWrt/ESP feature parity.


## RC7 origin-parity hardening

OpenWrt now validates Rental Server authorities before QR creation with the same practical constraints enforced by BlazeRental: non-empty host, numeric 1-65535 port when present, bracketed IPv6, and no userinfo/path/query/fragment/backslash ambiguity. BlazeRental repeats origin and TLS-pin checks inside the persistence boundary, not only in the QR scanner.
