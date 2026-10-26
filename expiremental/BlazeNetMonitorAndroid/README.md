# BlazeNetMonitor Android — v0.1.0 Preview

**Blaze Systems · Native Android port of BlazeNetMonitor v1.0.0**

Original completed Windows source: https://github.com/BlazingSystems/BlazingSystems-Projects/tree/main/networking/blazenetmonitor

## What works in this first Android build

- Native Java Android application (not WebView). Android 8.0+ (API 26) with target SDK 35.
- One-second **device-wide** network speed readout (Rx/down and Tx/up), from Android `TrafficStats`, all network interfaces combined.
- Seven compact live graph styles: Smooth, Line, Filled, Bars, Steps, Dots, Impulse; blue download and orange upload.
- Session counters (this monitoring process), daily and monthly counters for **monitored activity only** (persisted across app restarts), and Speed units Bits / Bytes.
- Two independently configured health targets: HTTPS HEAD, TCP connect, DNS resolve, and **Reachability** (Android `InetAddress.isReachable` may not use raw ICMP).
- Opt-in notification-backed foreground monitoring. **Stop** button and notification action. No hidden background daemon, no auto-start-at-boot.
- Optional draggable system overlay; the user must grant Android's separate **Display over other apps** permission. Overlay remains hidden if permission is absent.
- Original fixed owner PayPal QR and developer Facebook profile. No donation recipient changes.

## Important platform differences

1. **Device-wide counters**: Android `TrafficStats.getTotalRxBytes/TxBytes` sum network-layer traffic over all device interfaces since boot. Speed is calculated from monotonic counter deltas each second. Traffic traversing VPNs or tethering might be counted differently from carrier billing. The interface deliberately does not claim per-adapter or per-application accuracy.
2. **Top 5 apps since restart** is **not in this preview**. Android does not provide an ordinary third-party app unfettered historical per-application traffic; `TrafficStats` for other UIDs returns UNSUPPORTED on Android 7+. A later implementation would need the user to grant Usage Access for `NetworkStatsManager`, with OS and OEM-specific limits and no fabricated data.
3. **Background policy**: Continuous monitoring is started by the user with a foreground notification, declared as `specialUse` with its explicit subtype for review. Android may stop background processing in battery-saving modes. There is no BOOT_COMPLETED receiver or background-start workaround. Distribution through Google Play may require an additional foreground-service eligibility review; this preview is for local sideloading/testing.
4. **No Windows taskbar, Windows SRUM, or Windows adapter enumeration** is reused on Android. The Android overlay is an independent floating panel.
5. **Internet probes** contact only the endpoints the user configured. HTTPS has a 2.5-second timeout and rejects cleartext; DNS is subject to the OS resolver and may block longer on some devices. This preview is not a network security auditor.
6. Debug-signed APK, **not a Play Store signed production release**. Verify permission prompts and battery settings on your physical phone.

## Installation

Use the APK from [BlazeNetMonitor Android Preview Releases](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazenetmonitor-android-v0.1.0-preview.1). Android must be allowed to install the chosen downloaded APK. Open the app, tap **Start monitoring**, allow Notifications if requested, and optionally enable **Show floating speed**. The first time the donation card appears, it is optional; it can be reopened from Support.

Do not install unknown third-party APKs claiming to be Blaze Systems. Source and hash are in the GitHub release.

## Build

```bash
gradle :app:testDebugUnitTest :app:assembleDebug --no-daemon
```

Uses Android Gradle Plugin 8.7.3, Gradle 8.9, JDK 17 and Android SDK 35. Debug APK output:
`app/build/outputs/apk/debug/app-debug.apk`.

The first CI verifies JVM traffic arithmetic tests, compiles the APK, checks SDK/package/permissions, checks the output hash, and publishes an Android preview. **This does not replace a physical-device acceptance test.**

## Planned parity items

More reliable interface-specific byte accounting on supported Android API levels, optional per-app historical usage with explicit Usage Access, a stronger probe history tracker, Android native home-screen widgets, user-selectable graph colors/period, and device/battery acceptance tests. These require Android-specific implementation and must not be claimed as shipping features of preview 0.1.0.
