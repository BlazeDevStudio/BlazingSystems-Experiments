# BlazePwifi v0.4.0 Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement the child plans in the listed order.

**Goal:** Deliver BlazePwifi v0.4.0 with a Launcher3-derived BlazeRental HOME launcher, revisioned rental policy/QR administration, validated hardware builds, environment simulation, configured backups, and production release assets.

**Architecture:** The work is split into four plans because Android launcher integration, shell/server policy, target builds/simulation, and publication each have distinct failure domains. Interfaces between plans are fixed below so each plan can be implemented and reviewed independently.

**Tech Stack:** Android Launcher3 o-mr1, Java, Android DevicePolicyManager/LockTask/NotificationListenerService, POSIX shell/UCI/uHTTPd, TailAdmin static UI, Arduino ESP8266/ESP32, OpenWrt ImageBuilder, GitHub Actions, Android Emulator, QEMU.

**Spec:** `experiment/openwrt/BlazePwifi/docs/superpowers/specs/2026-10-05-blazepwifi-v0.4-launcher-design.md`

## Execution order

1. `2026-10-05-blazepwifi-v0.4-android-launcher.md`
2. `2026-10-05-blazepwifi-v0.4-server-admin.md`
3. `2026-10-05-blazepwifi-v0.4-build-simulation.md`
4. `2026-10-05-blazepwifi-v0.4-release-backups.md`

## Cross-plan interfaces

- Android consumes the rental policy response defined by the server/admin plan: `policy_revision`, `launcher_mode`, allowed/hidden packages, preferred Vendo, timer/quick-control/notification/admin-gesture settings, phone-admin verifier, lease and signature.
- Server/admin consumes Android inventory/capability reports and compare-and-set policy writes from the Android plan.
- Build/simulation consumes the final Android project, server rootfs, ESP sources and build scripts from the first two plans without changing their user-visible behavior.
- Release/backups consumes only artifacts whose corresponding build/simulation gates pass.

## Global constraints

- v0.3.0 remains preserved as the rollback release.
- Required v0.4 outputs: signed APK, ESP8266/ESP32 BIN+INO, Ruijie sysupgrade/config backup, x86 BIOS+UEFI images, Orange Pi Zero 3/One/PC images, checksums/manifests, validated backup images.
- No public signing private key, permanent enrollment secret, or plaintext phone-admin password.
- EW1200G Pro remains a Lite target; heavy UI features may be omitted there rather than breaking flash/RAM limits.
- Build/simulation validation must be distinguished from physical hardware validation.

## Stop conditions

Do not publish v0.4.0 if the signed APK, x86 BIOS/UEFI QEMU boot, required Orange Pi image validation, Ruijie image validation, ESP8266/ESP32 builds, or required browser/Android simulation gates are red.
