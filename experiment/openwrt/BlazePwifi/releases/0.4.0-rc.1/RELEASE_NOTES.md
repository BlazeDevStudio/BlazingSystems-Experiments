# BlazePwifi v0.4.0-rc.1 — Launcher Edition

This prerelease contains the exact candidate that passed the v0.4 build and simulation gate.

## What is validated

- Launcher3-based BlazeRental HOME application in Android API 27 emulator.
- Device Owner / kiosk enforcement and ordinary-uninstall defence.
- Fixed Rental, Quick Controls and Notifications surfaces.
- Locked app-drawer behavior with no rental time.
- Secret timer-hold administrator entry and initial setup UI.
- TailAdmin-based BlazePwifi web administration.
- ESP8266 and ESP32 controller firmware compile + binary/protocol checks.
- Ruijie RG-EW1200G Pro v1.1 sysupgrade structure/rootfs checks.
- x86 BIOS + UEFI QEMU boot checks.
- Orange Pi Zero 3, One and PC image/rootfs/userspace checks.

## Android signing notice

`BlazeRental-v0.4.0-RC-ci.apk` is installable and is the exact APK exercised by the emulator gate, but it uses CI/test signing. It is for deployment testing, not the final update-compatible production APK.

The final `v0.4.0` release remains gated on the preserved BlazeRental production signing identity. The repository currently does not have the required private keystore secrets configured, so this prerelease intentionally does **not** pretend that CI signing is production signing.

## Firmware / images

The firmware and image bundles in this release are built from the same validated candidate commit. Raw `.img` files are included inside each platform image tarball alongside the original `.img.gz`.

Physical-device validation is not claimed where only emulator/QEMU/filesystem validation was possible.
