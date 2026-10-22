# OpenWrt Rental Standalone — v0.5.2-rental.2-rc.10

The installer is intentionally **network-neutral**. It does not change WAN, LAN, Wi-Fi, cellular, repeater, DNS, or firewall UCI configuration during Standalone installation.

After installation:

- existing router/basic UI stays where the device already provides it;
- BlazePwifi Rental management is added at `https://LocalIP/rental/`;
- BlazeRental phones use `http://LocalIP`;
- authenticated remote ESP coinslot interfaces use `http://LocalIP:4455/cgi-bin/vendo`.

## R281 / EasyMode path

When the Windows OneClick installer detects `/tmp/sysinfo/board_name = notion,r281`, it automatically runs `install-r281.sh`.

That R281-specific entry verifies:

- OpenWrt 24.10.x;
- uHTTPd home `/www`;
- CGI prefix `/cgi-bin`;
- existing HTTPS :443.

The Windows deployer extracts the bundle with plain BusyBox-supported `tar -xzf ... -C ...` and then enters the archive's single top-level directory. No GNU-only archive options are used.

## Full conversion

The complete BlazePwifi payload remains installed but the hotspot core stays disabled. Conversion to full BlazePwifi is explicit:

```sh
/usr/sbin/blazepwifi-rental-upgrade --full
```

Only that conversion step may activate BlazePwifi hotspot/firewall ownership.


## Fresh-install Rental login

```text
Username: admin
Password: admin
```

Existing admin accounts are preserved. The normal password-change action still requires a stronger password.


## 0.5.2-rental.2-rc.7 UI hotfix

Rental mutations now submit CSRF through both the custom header and form body, with one authenticated token refresh/retry on mismatch. This specifically fixes QR enrollment creation on R281/uHTTPd paths where custom CGI headers may not be reliable.


## QR enrollment architecture

This release candidate deliberately separates:

- **Standard Enrollment QR** — for BlazeRental already installed; binding only.
- **Device Provisioning QR** — for Android Setup Wizard on a new/factory-reset phone; exact DPC APK URL/checksum plus one-time server binding extras.

Device Provisioning is fail-closed when exact APK metadata is not installed.


## RC8 provisioning boundary

Standard Enrollment and Device Provisioning are independent contracts. Device Provisioning uses an exact release APK/checksum and is still a prerelease path.

The provisioning metadata includes `GMS_DPC_APPROVED`. When it is `0`, the server/API/UI require an explicit acknowledgement and label the custom-DPC QR for AOSP/non-GMS or explicitly supported test devices only. Google-certified devices may block a non-approved custom DPC during Setup Wizard.

The Setup Wizard package checksum is canonical padded Base64URL SHA-256 and is cross-checked against the exact published APK.


## RC8 secure enrollment

RC8 QR generators use schema v2 and the RC8 APK requests enrollment protocol 2. The server no longer transmits the new long-lived device secret to an RC5 client. Both peers derive it from the one-time enrollment secret, request nonce and server-issued device ID, and the phone verifies the server's HMAC-signed enrollment response before persisting identity.


## RC8 rebind safety

A phone with an existing permanent Rental identity will not accept a new Standard Enrollment QR directly. The administrator must use the explicit Transfer action first. This prevents a scan or transient enrollment failure from destroying a working device binding.


## RC8 strict server-origin contract

Before creating either QR type, the OpenWrt backend now rejects a missing host, nonnumeric or out-of-range port, malformed/unbracketed IPv6 authority, userinfo, paths, queries, fragments, backslashes and control/whitespace forms. BlazeRental independently applies the same origin rules again before enrollment data is committed locally.


## RC8 stable-promotion boundary

RC8 adds an explicit provisioning target scope to release metadata and API responses. A non-GMS-approved custom DPC is restricted to `aosp_non_gms_or_explicit_oem_only`; a GMS-approved production identity may declare `gms_and_supported_aosp`.

The stable-promotion gate verifies the actual APK signer certificate with `apksigner` and requires physical validation evidence to match the exact APK bytes, signer, target scope, and GMS approval state.


## RC9 provisioning callback identity

The first valid Device Provisioning callback pins the pending server origin, one-time
token and certificate pin. Exact Android Setup Wizard callback replays are accepted
idempotently; any changed security identity is rejected until an explicit reset/transfer
or appropriate factory reset clears the state.
