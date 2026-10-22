BlazePwifi Standalone Rental Server - Windows One-Click Installer
Version: v0.5.2-rental.2-rc.11

1. Extract the ZIP completely.
2. Double-click Install-BlazePwifi-Rental.bat.
3. Enter the OpenWrt router IP/hostname, SSH username and password.
4. Confirm the router SSH host-key fingerprint on first connection.
5. The installer probes the board before deployment.
6. If it detects notion,r281 it automatically uses the R281/EasyMode-specific installation path.
7. Other supported OpenWrt devices use the generic target-detection path.

The R281 path is BusyBox-compatible and does not use GNU tar-only extraction options.

Normal Rental Standalone installation does not intentionally modify network, wireless or firewall UCI packages.

After installation:
  Rental console: https://ROUTER-IP/rental/
  Android server: http://ROUTER-IP

The SSH password is written only to a temporary local file for plink/pscp and is overwritten/deleted at the end of the run.

The package includes PuTTY command-line SSH tools (plink/pscp) solely for deployment. See the included PuTTY licence file.


Fresh-install Rental console credentials:
  Username: admin
  Password: admin

Existing admin accounts are preserved on upgrade. Change the default password later in Rental settings.


PASSWORD RESET:
  Double-click Reset-BlazePwifi-Admin-Password.bat.
  It works with Standalone Rental and full BlazePwifi.
  It resets only to:
    Username: admin
    Password: admin
  No manual file upload to the router is required.


HOTFIX 0.5.2-rental.2-rc.7:
- Fixes CSRF validation failures on mutating Rental admin actions such as QR enrollment.
- Sends CSRF in both HTTP header and POST body.
- Refreshes the authenticated session and retries once if a CSRF token becomes stale.


PROVISIONING RC:
  Standard Enrollment QR and Android Device Provisioning QR are separate.
  Device Provisioning uses the exact APK/checksum shipped with this release candidate.


DEVICE PROVISIONING RC8:
  Standard Enrollment QR and Android Device Provisioning QR are separate.
  Device Provisioning remains a release-candidate feature.
  The APK Setup Wizard checksum uses canonical padded Base64URL SHA-256.
  Google-certified Android may block a custom DPC that is not Android Enterprise approved.
  RC8 metadata declares that state and the Rental UI requires an explicit warning acknowledgement.
  Use the custom-DPC test path only on AOSP/non-GMS or an explicitly supported test device unless approval is declared.


RC8 ORIGIN HARDENING:
- OpenWrt validates Rental Server authorities before generating either QR type.
- Android independently re-validates the origin and TLS pin before persisting enrollment state.
- Missing hosts, nonnumeric/out-of-range ports, malformed IPv6, userinfo, paths, queries, fragments and backslashes are rejected.


RC8 PROMOTION HARDENING:
- Stable promotion verifies the actual APK signer certificate, not only metadata.
- Provisioning metadata exposes an explicit target scope.
- Non-approved custom DPC builds cannot claim universal Google-certified-device compatibility.


DEVICE PROVISIONING RC9:
  The first accepted pending provisioning identity is pinned to the exact server origin,
  enrollment token and certificate pin. Android may replay the exact same callback, but
  any changed callback identity is rejected until explicit reset/transfer or factory reset.
