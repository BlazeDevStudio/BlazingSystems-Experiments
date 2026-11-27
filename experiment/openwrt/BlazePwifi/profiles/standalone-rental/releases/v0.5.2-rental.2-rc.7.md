# BlazePwifi Standalone Rental Server v0.5.2-rental.2-rc.7

RC7 is an immutable prerelease candidate. It supersedes RC6 for physical Device Provisioning testing without altering the RC6 tag or assets.

## RC7 additional hardening

- OpenWrt Standard Enrollment and Device Provisioning now use a strict Rental Server authority validator before a token is generated.
- Missing hosts, nonnumeric/out-of-range ports, malformed IPv6, userinfo, path, query, fragment, backslash, whitespace and control-character origins fail closed.
- Bracketed IPv6 with an optional valid numeric port is accepted.
- BlazeRental repeats origin validation and HTTPS certificate-pin requirements inside the persistence boundary, independent of the QR scanner.
- The executable provisioning audit includes positive and negative origin-authority regression cases.

## Security retained

- Standard Enrollment and Device Provisioning remain distinct QR contracts.
- Device Provisioning remains administrator-only.
- Device Provisioning requires HTTPS plus the pinned local Rental Server certificate.
- Protocol-2 enrollment does not transport the long-lived device secret.
- Response-loss retry with the same nonce reuses the same device identity.
- Protocol-1 downgrade against new tokens is rejected.
- Repeated Setup Wizard callbacks are idempotent.
- Rebinding requires explicit Transfer.
- Abandoned enrollment state is garbage-collected and bounded.
- Exact APK bytes, checksum, version and signer evidence are release-bound.
- R281/BusyBox installer and lock compatibility remains included.
- Standalone still does not take ownership of OpenWrt network/wireless/firewall configuration.

## Device Provisioning status

This RC uses an exact TEST-signed BlazeRental APK. It is **not production-ready**.

Stable promotion remains blocked until:

- the corrected APK is signed by the long-term BlazeRental production identity;
- a factory-reset physical Android device completes Setup Wizard provisioning;
- Device Owner is confirmed on-device;
- pinned HTTPS server identity succeeds;
- v2 server enrollment completes and the device appears on the intended Rental Server;
- representative supported Android paths are physically exercised.

Google-certified/GMS devices may refuse an unapproved custom DPC. The UI/API continue to require explicit acknowledgement for that test scope.
