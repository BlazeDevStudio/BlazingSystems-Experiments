# BlazePwifi v0.4.0 production checklist

The final release must be assembled only from a validated build and a matching signed APK manifest.

- [x] Main BlazePwifi build run passed for candidate `1373eaa8ee8e95abbc2d0cbf5565d8ed28d2a750`.
- [x] `BlazePwifi-v0.4-candidate-gate` passed.
- [x] Launcher3 Android emulator Device Owner audit passed.
- [x] Browser admin simulation passed without console/page errors.
- [x] ESP8266 and ESP32 compiled-binary parsing and controller protocol checks passed.
- [x] Ruijie RG-EW1200G Pro v1.1 firmware structure/rootfs audit passed.
- [x] x86 BIOS and UEFI QEMU boot audit passed.
- [x] Orange Pi Zero 3, One and PC image/rootfs/qemu-user audits passed.
- [x] Optional Orange Pi family images built successfully; final release workflow re-audits their rootfs/qemu-user compatibility before publication.
- [x] Production BlazeRental APK verifies with v1, v2 and v3 signing.
- [x] v0.4 fresh production certificate identity is locked and recorded.
- [x] Encrypted signing-key recovery material is retained without committing plaintext private key material.
- [ ] Final production release workflow stages assets, generates SHA256SUMS, and publishes tag `v0.4.0`.

No physical-board boot claim is made where validation is structural, QEMU, Android emulator, or userspace-only.
