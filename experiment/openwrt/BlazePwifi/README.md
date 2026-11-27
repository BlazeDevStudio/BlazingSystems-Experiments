# BlazePwifi

BlazePwifi is an open-source prepaid Wi-Fi, captive-portal, coin-controller and managed rental-device platform for OpenWrt, Orange Pi, x86 PCs, ESP8266/ESP32 and Android.

Current production release: **0.3.0**  
OpenWrt build baseline: **25.12.5**

## Capability tiers

- **Lite** — constrained OpenWrt routers: hardened accounting, sessions/vouchers, compact admin and portal editor, network/VLAN controls and ESP controller support.
- **Standard** — Orange Pi/SBC: Lite features plus richer administration, libgpiod controller agent and Android-rental services.
- **Full** — x86_64: Standard features plus the full admin/portal experience, larger retention and fleet-oriented rental management.

Heavy features are not forced onto small routers.

## Build-validated targets

The CI matrix builds and checksum-verifies:
- Ruijie RG-EW1200G Pro v1.1
- x86_64 legacy BIOS and UEFI
- Orange Pi Zero 3
- Orange Pi One
- Orange Pi PC
- ESP8266
- ESP32
- BlazeRental Android APK

Additional Orange Pi targets are attempted independently and are published only when their build succeeds.

## Security and user handling

BlazePwifi includes:
- browser-backed user identity that survives normal private/random MAC changes;
- durable balances and timed sessions;
- pause/resume and one-time vouchers;
- target-bound signed/idempotent coin events and replay protection;
- persistent pending-event recovery;
- HTTPS-only local administration by default;
- generated first-boot admin credential, not a universal password;
- per-IP/per-account brute-force lockouts with escalation;
- secure HttpOnly SameSite admin sessions;
- CSRF checks and Admin/Operator/Viewer roles;
- audited money, configuration and rental operations;
- fail-closed behavior when router time is not synchronized.

## Portal and admin

Lite targets keep a compact native shell. Standard/Full targets use a capability-gated Tabler core admin shell; optional heavy chart/plugin bundles are excluded.

The customer portal keeps the first view simple: remaining time, Insert Coin, voucher and rates. Non-sensitive device/network details are below the primary actions.

Static previews live in [portal-templates](portal-templates/).

## Controllers

ESP8266 and ESP32 use one target-bound accounting protocol. Orange Pi/SBC controllers use libgpiod instead of deprecated sysfs GPIO.

Pins, polarity, debounce, pulse grouping, controller identity, ports, VLANs, network interfaces, rates and portal appearance are configuration rather than production source edits.

## BlazeRental

Package: **com.blazesystems.blazerental**

BlazeRental supports:
- factory-reset QR Device Owner provisioning for strongest management on owned/authorized devices;
- normal APK installation as an explicitly lower-security fallback.

Rental time remains authoritative on the BlazePwifi server. Enrollment tokens are one-time and exchanged for per-device authentication.

## Installation

See [docs/INSTALL.md](docs/INSTALL.md) for:
- first-login/bootstrap credentials;
- VLAN/interface examples;
- ESP8266/ESP32 pin examples and electrical warnings;
- Orange Pi imaging and GPIO discovery;
- x86 BIOS/UEFI imaging;
- Ruijie bootstrap/sysupgrade guidance;
- Android QR/manual provisioning;
- checksum verification.

Default local endpoints:
- Portal: http://LAN_IP:8080/
- Admin: https://LAN_IP:8443/admin.html
- Vendo API: http://LAN_IP:4455/cgi-bin/vendo

## Releases

Versioned source indexes live under [releases](releases/). Large generated installers and firmware are attached to the matching GitHub Release instead of being committed into Git history.

The release pipeline keeps direct installable assets such as APK, BIN, IMG.GZ, INO and TAR.GZ files, plus per-target ZIP archives, manifest.json and SHA256SUMS. Failed optional targets are never replaced by placeholders.

## Validation boundary

CI success is build validation. Production deployment still requires physical boot/recovery, electrical, captive-client, brownout and sustained-load testing on the exact hardware revision.

## Repository map

- openwrt/rootfs — OpenWrt runtime
- installer — OpenWrt installer/uninstaller
- esp8266 and esp32 — controller firmware
- linux-agent — Orange Pi/SBC GPIO agent and profiles
- android/BlazeRental — Android DPC/companion
- portal-templates — static interface previews
- build — reproducible image/UI preparation
- tools — provisioning helpers
- tests — security/accounting/persistence/UI gates
- releases — versioned release indexes

## Publication policy

The public repository contains original project code and documented/open-source integration patterns. It does not redistribute closed commercial binaries, licensing systems, private keys, confidential databases, proprietary artwork or private controller firmware.
