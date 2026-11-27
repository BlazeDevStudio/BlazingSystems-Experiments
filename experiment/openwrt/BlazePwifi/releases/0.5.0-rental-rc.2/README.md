# BlazePwifi Standalone Rental Server v0.5.0-rental-rc.2

This RC supersedes the rc.1 ESP multi-slot design and aligns the release with the finalized Standalone Rental architecture.

## OpenWrt
- Notion R281: one-click SSH/manual installer on the existing validated OpenWrt/EasyMode system.
- Ruijie RG-EW1200G Pro v1.1: one-click SSH/manual installer plus CI-built standalone sysupgrade BIN.
- Generic OpenWrt 24.10.x/25.12.x: one-click SSH/manual installer.
- x86_64: CI-built BIOS and UEFI OpenWrt disk images.

The complete BlazePwifi v0.5 software payload is installed, but only rental-related management is activated. Existing router routes stay intact; Rental management is added at `https://LocalIP/rental/`. BlazeRental phones use `http://LocalIP`.

Rental Standalone installation does not write the network, wireless or firewall UCI packages. Full conversion is explicit and preserves configuration/state before activating BlazePwifi hotspot/firewall ownership.

**R281 firmware image note:** rc.2 does not publish a new R281 firmware BIN/IMG because the repository does not yet contain a public hardware-validated R281 image build path. R281 is installer-first rather than shipping a falsely labeled or insufficiently validated image.

## Windows one-click installer
The primary OpenWrt deployment asset contains the BAT launcher, GUI-assisted PowerShell deployer, pinned OpenWrt bundle, and PuTTY plink/pscp utilities. It prompts for router IP, SSH user/password and first-connection host-key approval, then uploads, installs and opens `/rental/`.

## ESP8266 / ESP32
One lightweight admin console is served at `http://assigned-ip/`.

Three modes:
1. Rental Server
2. Rental Server + Local Coin Slot
3. Remote Coin Slot Interface

The rental branch expects **one physical coinslot per ESP by default**. Modes 1 and 2 can bind additional remote ESP coin interfaces. Remote coin mode uses the same signed BlazePwifi vendo protocol as OpenWrt/full BlazePwifi.

First boot validates Wi-Fi association + DHCP before saving, shows the assigned IP and reboots. Five failed saved-Wi-Fi attempts trigger recovery AP on the next boot. Internet/DNS failure alone does not disable the reachable local rental server.

## RC validation boundary
CI gates static/network-neutral checks, ESP8266 and ESP32 compilation, EW1200G Pro sysupgrade build/checksum, x86 BIOS/UEFI image build/checksum, and release packaging. Physical flashing, electrical isolation and long-duration/power-loss validation are still required before promotion from RC.
