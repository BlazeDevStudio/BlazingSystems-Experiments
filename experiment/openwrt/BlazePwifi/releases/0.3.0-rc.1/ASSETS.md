# Release assets

The GitHub Release for `v0.3.0-rc.1` is expected to contain successful outputs from these families.

| Family | Direct assets |
|---|---|
| Source | `BlazePwifi-0.3.0-rc.1.tar.gz`, source/target ZIP archives |
| Ruijie | official checksum-verified OpenWrt bootstrap `.bin`, BlazePwifi sysupgrade `.bin` |
| x86_64 | squashfs/ext4 combined BIOS `.img.gz`, squashfs/ext4 combined UEFI `.img.gz` |
| Orange Pi | successful profile `*-sdcard.img.gz` images |
| ESP8266 | compiled firmware `.bin` plus `.ino` source |
| ESP32 | compiled firmware `.bin` plus `.ino` source |
| Android | `BlazeRental.apk`, provisioning sample JSON/PNG, provisioning tools |
| Portal | `BlazePwifi-portal-templates.tar.gz` |
| Integrity | `SHA256SUMS`, `manifest.json` |

A missing optional target means that target did not pass its build gate; the release workflow does not create placeholder binaries.
