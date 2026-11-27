# BlazePwifi v0.4.0 — Launcher Edition

BlazePwifi v0.4.0 is the major Launcher Edition update. BlazeRental is rebuilt around the preserved Launcher3 codebase rather than the earlier stripped-down browser/intent-launcher approach.

## Production outputs

The v0.4.0 release contains:

- `BlazeRental.apk` — signed Launcher3-based rental launcher.
- QR/Device Owner provisioning helper files.
- ESP8266 and ESP32 controller firmware (`.bin` + `.ino`).
- Ruijie RG-EW1200G Pro v1.1 sysupgrade and recovery image.
- x86_64 OpenWrt BIOS/UEFI images.
- Direct raw `.img` assets for x86 BIOS/UEFI, Orange Pi Zero 3, Orange Pi One and Orange Pi PC, plus `DIRECT-IMAGES-SHA256SUMS`.
- Orange Pi Zero 3, One and PC image bundles.
- Additional validated Orange Pi family images: Zero, Zero 2, Zero 2W, PC2, PC Plus and One Plus.
- SHA256 manifests and simulation/audit evidence.
- Encrypted BlazeRental signing-key recovery material.

## BlazeRental behavior

Rental Mode provides three fixed Launcher3 workspace pages: rental/timer, safe quick controls, and mirrored notifications. The app drawer is lease-gated and package-policy filtered. Device Owner provisioning is the strongest deployment mode; manual APK installation remains supported with lower anti-bypass strength.

The on-device admin supports app allow/hide policy, binding/enrollment, administrator password, secret admin access, initial-setup transfer and “use device as is” mode. The BlazePwifi server admin uses the local TailAdmin-based interface and generates QR enrollment payloads.

## Signing compatibility

The final v0.4 production APK uses a new locked production certificate. It is intended for clean/factory-reset provisioning and is **not an in-place Android update over v0.3**. See `SIGNING.md` for the exact fingerprint and recovery rules.

## Validation scope

A build is not called production-ready merely because it compiles. The release requires source/unit validation, Android emulator Device Owner testing, browser UI simulation, ESP binary/protocol checks, Ruijie firmware inspection, x86 BIOS/UEFI QEMU boots and Orange Pi image/rootfs/qemu-user audits.

These automated checks do not pretend to be physical-board testing where no real board was attached.
