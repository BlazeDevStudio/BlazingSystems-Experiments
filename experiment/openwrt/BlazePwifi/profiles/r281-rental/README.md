# BlazePwifi R281 Rental Profile

This is the full **rental-service deployment profile** of BlazePwifi for the Notion R281 / EasyMode environment.

It is not the earlier standalone test hub. The server core in this profile reuses the exact shared BlazePwifi 0.3.0 blobs from commit `28a2a5378e339e401ceaf2433caccccf0e47cd48`: `common.sh`, `auth.sh`, `config.sh`, `rental.sh`, `controller.sh`, the signed BlazeRental app API, and the ESP8266/ESP32 vendo API.

The R281 profile adds only routing/install adapters and a rental-focused management console. It deliberately does not take ownership of EasyMode networking.

## Routes

- `http://ROUTER_IP/` — existing EasyMode
- `http://ROUTER_IP/admin` — existing R281/LuCI administration
- `https://ROUTER_IP/rental/` — BlazePwifi Rental management
- `http://ROUTER_IP/cgi-bin/rental` — BlazeRental Android API
- `http://ROUTER_IP:4455/cgi-bin/vendo` — BlazePwifi ESP coin-controller API

Opening `http://ROUTER_IP/rental/` redirects to HTTPS for the management login. The Android API remains available over the local HTTP base URL because Device Owner/manual clients use HMAC-signed requests and local self-signed TLS is not universally trusted by Android.

## Kept from BlazePwifi

Enrollment, signed leases, Android package inventory, allowed-app policy, preferred vendo, managed-device admin password, controller protocol/configuration, HMAC authentication, manual lease controls, roles, CSRF, session expiry, login lockout, security audit, rental event history, and rental timing configuration.

## Intentionally excluded

Hotspot captive-portal accounting, customer Wi-Fi session accounting, voucher sales, nftables hotspot authorization, walled-garden management, hotspot portal builder and hotspot firewall ownership. Those are not part of the Android rental service and would conflict with the existing R281 EasyMode network stack.

## R281 safety boundary

The installer does not write `/etc/config/network`, `/etc/config/firewall`, `/etc/config/wireless`, `/etc/config/blaze`, or EasyMode files. It creates/updates only the BlazePwifi rental UCI package and an additive `uhttpd.blazepwifi_rental_vendo` listener for port 4455.

Existing files are backed up under `/root/blazepwifi-r281-rental-backups/`.

## Existing test-hub migration

If the old `/etc/blazepwifi-rental/state` test state is present and the real BlazePwifi rental state is empty, the installer migrates enrolled devices, enrollment records and policy state so already-enrolled test phones can continue using the real server.

## Version

- BlazePwifi core: 0.3.0
- R281 rental profile: 0.3.0-r281.1
- Source baseline: 28a2a5378e339e401ceaf2433caccccf0e47cd48
