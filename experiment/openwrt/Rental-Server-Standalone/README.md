# Rental Server Standalone

Standalone BlazeRental-compatible manual-time testing server for the Notion R281.

Version: **0.1.2**

## Purpose

This project adds only a rental management/test layer to an existing R281 EasyMode installation. A coin slot is not required: the operator can create one-time enrollment tokens and manually add, set, expire, rename, or revoke rental-device time.

Expected local routes after installation:

- `http://ROUTER_IP/` — existing EasyMode, unchanged
- `http://ROUTER_IP/admin` — existing LuCI/admin, unchanged
- `http://ROUTER_IP/rental/` — Rental Server Standalone operator dashboard
- `http://ROUTER_IP/cgi-bin/rental` — BlazeRental Android API

## Safety boundary

The installer is pinned to `notion,r281` and OpenWrt `24.10.x` by default. It verifies the existing uHTTPd document root and CGI prefix, then reuses them without editing uHTTPd.

It does not change `/etc/config/network`, `/etc/config/firewall`, `/etc/config/wireless`, `/etc/config/uhttpd`, `/etc/config/blaze`, EasyMode, LuCI, modem/APN/band settings, relay/repeater settings, Piso networking, or WAN/failover policy.

The only optional package action is installing `openssl-util` when the OpenSSL CLI required for BlazeRental HMAC-SHA256 authentication is missing.

## Install

Copy or download `install.sh` onto the R281 and run as root:

```sh
chmod +x install.sh
./install.sh
```

If the `root/` payload is beside the installer, it is copied locally. If only `install.sh` is downloaded, it fetches the three checksum-pinned payload files from this repository.

After installation the script prints the Rental admin token. Open `/rental/`, enter the token, create an enrollment token, and use the router base URL in BlazeRental manual setup.

## Uninstall

```sh
./install.sh --uninstall
```

State under `/etc/blazepwifi-rental` is preserved by default. To remove it too:

```sh
./install.sh --uninstall --purge
```

## v0.1.1 checksum fix

v0.1.0 accidentally embedded the pre-GitHub SHA-256 values for the two CGI payloads. The files themselves were correct; the installer correctly aborted rather than installing unverified content. v0.1.1 updates those two pinned hashes and keeps payload verification enabled.

## v0.1.2 R281 dashboard authentication fix

Some R281/uHTTPd CGI environments do not reliably pass the custom `X-Blaze-Rental-Admin` request header through to CGI. The dashboard now submits the same admin token in the POST body as `admin_token` as well as the header. The server already validates this field against the local token file, so authentication remains exact-token based.

## Validation boundary

Host-side protocol and syntax tests passed. Physical R281 installation, actual Android enrollment, Device Owner/manual APK behavior, and lease refresh still require device testing.

This is deliberately a rental test server, not the full BlazePwifi hotspot/coinslot deployment.
