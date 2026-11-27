# BlazePwifi Standalone Rental Server v0.5.0-rental-rc.1

This prerelease introduces the standalone Rental Server edition derived from the integrated BlazePwifi v0.5.0 codebase.

## OpenWrt targets

- Notion R281 / EasyMode on OpenWrt 24.10.x
- Ruijie RG-EW1200G Pro v1.1 on OpenWrt 25.12.x
- generic OpenWrt 24.10.x / 25.12.x wireless-capable devices

The OpenWrt bundle contains the **complete BlazePwifi v0.5 software payload**. Rental Standalone mode activates only rental management, Android rental API and coinslot/controller services. Hotspot/captive-portal functionality stays dormant on disk and can later be activated with the included full-conversion command.

No network, wireless or firewall UCI package is modified during Rental Standalone installation.

## ESP targets

- ESP8266: standalone rental server, 2 logical local/multi-coin slots, up to 6 enrolled rental devices
- ESP32: standalone rental server, 4 logical local/multi-coin slots, up to 18 enrolled rental devices

ESP firmware implements the BlazeRental enrollment/status flow and v3 policy signature format directly without OpenWrt. It can switch between authoritative Standalone Rental Server mode and MultiCoin Controller mode for a remote BlazePwifi server.

ESP firmware cannot become the full Linux/OpenWrt BlazePwifi server.

## Included release assets

- OpenWrt universal standalone bundle
- R281, EW1200G Pro and generic installer entry scripts
- ESP8266 INO + compiled BIN
- ESP32 INO + compiled binaries
- compatible BlazeRental v0.5 TEST APK when available from the v0.5.0 release
- manifest and SHA256SUMS

## RC boundary

CI compilation/static validation is required before publication. Physical device installation, flash-space validation, coinslot electrical isolation and long-duration lease/power-loss testing remain required before this line is promoted out of RC.
