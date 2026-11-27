# v0.4.0 asset contract

| Target | Production output |
|---|---|
| Android | BlazeRental.apk, QR setup/provisioning sample, signer certificate/fingerprint, signing manifest |
| ESP8266 | BlazePwifi-Vendo-ESP8266.bin + INO |
| ESP32 | BlazePwifi-Vendo-ESP32.bin + INO |
| Ruijie RG-EW1200G Pro v1.1 | sysupgrade, recovery initramfs when available, default-config backup |
| x86_64 | BIOS/UEFI-capable OpenWrt disk images |
| Orange Pi Zero 3 | disk images |
| Orange Pi One | disk images |
| Orange Pi PC | disk images |
| Orange Pi Zero | disk images |
| Orange Pi Zero 2 | disk images |
| Orange Pi Zero 2W | disk images |
| Orange Pi PC2 | disk images |
| Orange Pi PC Plus | disk images |
| Orange Pi One Plus | disk images |

The final release also contains `SHA256SUMS`, `RELEASE-MANIFEST.json`, `CANDIDATE-GATE.json`, compressed validation evidence, and the encrypted BlazeRental signing-key recovery payload.

Simulation evidence includes machine-readable audit output plus screenshots/logs where the environment supports them. Structural or QEMU validation is not described as physical-board boot testing.


## Direct flashable IMG assets

The production release exposes the commonly requested raw EXT4 disk images directly, without requiring extraction from the target bundles:

- `openwrt-25.12.5-x86-64-generic-ext4-combined.img` — x86_64 legacy BIOS.
- `openwrt-25.12.5-x86-64-generic-ext4-combined-efi.img` — x86_64 UEFI.
- `openwrt-25.12.5-sunxi-cortexa7-xunlong_orangepi-one-ext4-sdcard.img` — Orange Pi One.
- `openwrt-25.12.5-sunxi-cortexa7-xunlong_orangepi-pc-ext4-sdcard.img` — Orange Pi PC.
- `openwrt-25.12.5-sunxi-cortexa53-xunlong_orangepi-zero3-ext4-sdcard.img` — Orange Pi Zero 3.
- `DIRECT-IMAGES-SHA256SUMS` — SHA-256 checksums for the direct raw image assets.

The target tarballs remain available because they carry the complete image variants used by the validated build pipeline.
