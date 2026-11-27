# BlazeRental Provisioning / Enrollment Audit

Audit target: BlazePwifi 0.5.2 Standalone Rental RC7 candidate and the active Launcher3-based BlazeRental DPC.

## Security boundary

Two QR formats are intentionally separate and must never be treated as interchangeable.

### Standard Enrollment QR

- Scanner: BlazeRental in-app scanner.
- Prerequisite: BlazeRental is already installed.
- Purpose: one-time Rental Server binding only.
- Schema: `blazerental.enrollment.v2`.
- Payload: Rental Server URL, one-time enrollment token, device label, and the server certificate SHA-256 pin when HTTPS is used.
- Does not request or claim Device Owner.
- RC5-generated tokens require enrollment protocol 2 and cannot be downgraded to the legacy protocol-1 secret-transport response.

### Android Device Provisioning QR

- Scanner: Android Setup Wizard enterprise QR provisioning.
- Prerequisite: new/factory-reset, unprovisioned, owned or explicitly authorized phone.
- Purpose: install and verify the DPC, provision Device Owner where Android/OEM policy permits it, then bind BlazeRental to the Rental Server.
- Admin-extras schema: `blazerental.provisioning.v2`.
- Includes the exact DPC component, exact APK HTTPS download URL, canonical URL-safe Base64 SHA-256 APK checksum, minimum version code, one-time Rental Server enrollment material, server certificate SHA-256 pin, and optional Wi-Fi.
- Rental Server URL must be HTTPS.
- Provisioning is rejected if the local Rental Server certificate cannot be fingerprinted and pinned.

## RC6 safeguards retained by RC7

- Android Setup Wizard may redeliver identical provisioning extras. RC6 introduced and RC7 retains preservation of an in-progress enrollment request nonce/device identity instead of resetting state on the repeated callback.
- Standard Enrollment on an already-bound phone fails closed. The working permanent identity remains intact until the administrator explicitly uses Transfer.
- Standard Enrollment scanner state errors are no longer all reported as the wrong QR type; Device Provisioning QR, already-bound state, and local storage failure have distinct handling.
- Expired or malformed abandoned enrollment rows are purged under the enrollment lock whenever a new QR token is created.
- RC6 introduced and RC7 retains a capped active enrollment table (default 512, bounded configurable range 16-4096) so repeated unused QR generation cannot grow R281 state without bound.
- QR generation fails closed if token creation, durable persistence, or enrollment capacity checks fail; an empty token is never rendered into a QR.
- Rental Server URLs embedded in either QR contract are origin-only. Userinfo, non-root paths, query strings, and fragments are rejected so the client API path cannot be redirected by URL ambiguity.
- Android repeats the same origin validation before persisting Standard Enrollment or Device Provisioning data.

## RC7 origin-parity finding

- The OpenWrt admin backend now validates a non-empty server host and a numeric port in the 1-65535 range when supplied.
- Bracketed IPv6 origins are supported; malformed bracket forms and unbracketed multi-colon authorities are rejected.
- Userinfo, path, query, fragment, backslash, whitespace and control-character authority forms are rejected before token/QR generation.
- BlazeRental Standard Enrollment repeats origin and TLS-pin validation in the persistence layer so a future caller cannot bypass scanner validation.

## Corrected findings

1. Standard Enrollment and Device Provisioning are distinct backend actions and UI flows. Compatibility aliases map only to Standard Enrollment.
2. The active APK source is `android/BlazeRentalLauncher/`; the older `android/BlazeRental/` project is reference/legacy only.
3. Android 12+ integrated provisioning is implemented through `GET_PROVISIONING_MODE` and `ADMIN_POLICY_COMPLIANCE`, with legacy provisioning completion retained for older supported Android.
4. Provisioning activities are protected by `android.permission.BIND_DEVICE_ADMIN`.
5. Device Owner provisioning cannot complete merely because Android assigned Device Owner. BlazeRental must persist valid provisioning extras, reach the intended Rental Server, complete one-time enrollment, and obtain a valid server response.
6. The in-app Standard Enrollment scanner explicitly rejects Device Provisioning payloads.
7. Device Provisioning uses an exact release-bound APK URL/checksum/version record. Missing or inconsistent metadata fails closed.
8. Device Provisioning is administrator-only. Standard Enrollment remains available to the intended operator role.
9. Google-certified-device/custom-DPC limitations are surfaced in metadata, API, and UI; the server requires an explicit acknowledgement when the DPC is not declared approved.
10. The OpenWrt/R281 path remains network-neutral: Standalone does not take ownership of network, wireless, or firewall configuration.

## Secure enrollment protocol v2

RC5-generated Standard and Device Provisioning tokens are stored with minimum protocol 2.

The APK authenticates enrollment with:

```text
enroll_v2|request-nonce|one-time-token
```

The long-lived device secret is never returned by the v2 enrollment response. Server and phone independently derive it as HMAC-SHA256 keyed by the one-time token over:

```text
device-secret-v2|request-nonce|device-id
```

The server response is authenticated over:

```text
enroll-response-v2|request-nonce|device-id|server-time|lease-until|kdf
```

The phone verifies that response before committing its permanent identity.

### Retry safety

Provisioning must survive loss of the first successful enrollment response.

For protocol 2:

- the phone persists one enrollment request nonce synchronously and reuses it until identity setup succeeds;
- the server records only the redeemed request nonce and device ID in the temporary enrollment record;
- the temporary record never stores the derived long-lived device secret;
- retry with the same nonce returns the same device identity and does not create a second device;
- retry with a different nonce is rejected as `enrollment already claimed`;
- the temporary token/redemption record remains only until the device proves possession of the derived permanent secret on its first authenticated status request;
- after that proof, the temporary redemption record is deleted.

This closes both the response-loss stranding problem and the protocol-downgrade path for RC5-generated QR tokens.

Legacy protocol 1 remains only for explicitly legacy enrollment records created without the protocol-2 requirement. New RC5 QR generators do not create such records.

## Pinned HTTPS Rental Server identity

Device Provisioning requires an HTTPS Rental Server URL plus the exact SHA-256 fingerprint of the local uHTTPd certificate.

The certificate pin is:

- generated by the OpenWrt Rental admin backend from the active local uHTTPd certificate;
- embedded in Device Provisioning admin extras;
- embedded in Standard Enrollment when HTTPS is used;
- validated and persisted synchronously by BlazeRental;
- enforced by a dedicated `HttpsURLConnection` trust manager and hostname verifier that accept the connection only when the peer certificate exactly matches the stored SHA-256 pin.

An HTTPS QR without a valid pin is rejected by the Standard scanner. Device Provisioning v2 rejects any admin-extras bundle that is not HTTPS or lacks a valid 64-hex pin.

### Certificate continuity

Normal Standalone reinstall reuses the existing uHTTPd certificate; the installer must not silently rotate an existing certificate. A deliberate certificate replacement changes the pinned server identity and therefore requires controlled device re-enrollment or an explicit future pin-rotation protocol.

## APK checksum and release binding

`PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM` uses canonical padded URL-safe Base64 SHA-256 for the exact APK bytes. For a SHA-256 digest this is 44 characters and ends with `=`.

The release also records the ordinary 64-hex APK SHA-256 separately. Device Provisioning metadata is generated only after the exact APK package ID, version code, version name, signature verification, and checksum pass.

The PC/offline provisioning generator follows the same contract as the server generator: HTTPS Rental Server, mandatory server certificate pin, schema v2, exact DPC component, exact APK URL/checksum, and minimum APK version code.

## Google-certified Android / custom DPC compatibility

Google-certified Android devices can restrict enterprise provisioning to approved/verified DPCs. BlazeRental must not advertise custom Device Owner provisioning as universally compatible on GMS/Play-Protect devices.

The release metadata carries `GMS_DPC_APPROVED`. When it is `0`, API and UI require an explicit custom-DPC acknowledgement and label the QR for AOSP/non-GMS or explicitly supported test targets only.

Production planning must treat this platform/policy limitation separately from technical correctness of the QR payload.

## Release/signing boundary

Provisioning changes remain release-candidate work until physical Setup Wizard validation is complete.

The CI provisioning APK is test-signed. The QR is exact-byte/checksum valid for that RC, but the TEST signing identity is not production signing continuity.

Do not promote Device Owner provisioning to stable production status until all of the following are true:

- the APK is signed by the locked long-term BlazeRental production identity;
- a factory-reset physical Android device completes Setup Wizard Device Provisioning;
- Device Owner is confirmed on-device;
- HTTPS certificate pin validation succeeds against the intended Rental Server;
- the one-time v2 enrollment completes and the phone appears on that server;
- a simulated/lab response-loss retry returns the same device identity;
- a protocol-1 downgrade attempt against a new token is rejected;
- a second authenticated sync retires the temporary redemption record and obtains/verifies server policy;
- the Standard scanner rejects the Device Provisioning QR;
- representative older and Android 12+ provisioning paths are exercised where supported.

## ESP scope

ESP8266/ESP32 remain valid Standalone Rental Servers and Remote Coin Slot Interfaces, but this RC does not claim Android Device Provisioning QR parity on ESP.

ESP onboarding remains a separate constrained path. If Device Provisioning is ever added to ESP, it must implement the same distinct QR schemas, exact APK metadata binding, HTTPS server identity rules where technically supportable, and explicit resource/security audit.

## Non-goals

The product does not claim resistance to bootloader unlock, recovery flashing, OEM service tooling, privileged platform exploits, or a user with physical access who can perform an authorized factory wipe.
