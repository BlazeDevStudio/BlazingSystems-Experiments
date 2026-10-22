# BlazePwifi Standalone Rental Server

Latest stable server line: **v0.5.2-rental.1**  
Provisioning architecture candidate: **v0.5.2-rental.2-rc.11**

The provisioning candidate keeps two independent Android onboarding modes:

- **Standard Enrollment QR** — BlazeRental already installed; scanned inside BlazeRental; server binding only; no Device Owner claim.
- **Device Provisioning QR** — Android Setup Wizard on a factory-reset phone; exact APK/checksum; Device Owner only where the platform permits that DPC; then server binding.

RC9 carries the RC5 protocol hardening, all RC6 durability/rebind safeguards, RC7 strict-origin parity and RC8 signer/target-scope promotion hardening. RC9 additionally pins the first accepted pending Device Provisioning identity so a changed Setup Wizard callback cannot replace it.

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


## RC8 target scope

Android Device Provisioning QR is implemented on the **OpenWrt Rental Server** path in RC8.

ESP8266/ESP32 Rental Server mode continues to support manual one-time server/token enrollment, but does not yet render Standard Enrollment QR or Android Device Provisioning QR. The release manifest declares this explicitly rather than implying OpenWrt/ESP feature parity.


## RC8 promotion hardening

RC8 retains RC7 origin validation and additionally verifies the actual APK signing certificate during stable-promotion checks. It also binds provisioning metadata and physical validation evidence to an explicit target scope so a non-GMS-approved custom DPC cannot be promoted with a universal GMS compatibility claim.

## RC10 authenticated status/lease boundary

Status responses may update paid lease time only after the response policy signature, device-ID binding, policy revision monotonicity and durable policy write have passed. Repeated signed status responses at the same revision can refresh lease time without rewriting settings; revisions older than the accepted policy are rejected. Device Owner Setup Wizard compliance requires a verified follow-up policy sync. This remains a TEST prerelease pending physical Setup Wizard validation.

## RC11 release identity

RC10 is immutable and intentionally contains only the earlier authenticated-lease correction. The final Device Owner source/callback guard, modern Android receiver-race isolation and persisted signed-policy gate were completed after that tag was published. Those changes belong to RC11, using TEST APK versionCode 50212. Production signing and physical Setup Wizard validation remain outstanding.
