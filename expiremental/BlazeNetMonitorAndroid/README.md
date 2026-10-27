# BlazeNetMonitor Android — v0.1.1 Preview

**Blaze Systems · Native Android port of BlazeNetMonitor v1.0.0**

Original completed Windows source: https://github.com/BlazingSystems/BlazingSystems-Projects/tree/main/networking/blazenetmonitor

## What works in this first Android build

- Native Java Android application (not WebView). Android 8.0+ (API 26) with target SDK 35.
- One-second **device-wide** network speed readout (Rx/down and Tx/up), from Android `TrafficStats`, all network interfaces combined.
- Seven compact live graph styles: Smooth, Line, Filled, Bars, Steps, Dots, Impulse; blue download and orange upload.
- Session counters (this monitoring process), daily and monthly counters for **monitored activity only** (persisted across app restarts), and Speed units Bits / Bytes.
- Two independently configured health targets: HTTPS HEAD, TCP connect, DNS resolve, and **Reachability** (Android `InetAddress.isReachable` may not use raw ICMP).
- Notification-backed foreground monitoring. The OS-managed **status bar** shows the monitoring notification icon. Pull down to see the compact live speed strip in this order: **Target 1 dot · upload speed · download speed · Target 2 dot**. Expand the notification for At a Glance health, session/day/month data totals, and a Stop action.
- Both speeds and the two target-health colors update as new samples arrive (nominally every two seconds; Android System UI may throttle presentation). No floating widget, display-over-other-apps permission, or auto-start-at-boot.
- Original fixed owner PayPal QR and developer Facebook profile. No donation recipient changes.

## Important platform differences

1. **Device-wide counters**: Android `TrafficStats.getTotalRxBytes/TxBytes` sum network-layer traffic over all device interfaces since boot. Speed is calculated from monotonic counter deltas each second. Traffic traversing VPNs or tethering might be counted differently from carrier billing. The interface deliberately does not claim per-adapter or per-application accuracy.
2. **Top 5 apps since restart** is **not in this preview**. Android does not provide an ordinary third-party app unfettered historical per-application traffic; `TrafficStats` for other UIDs returns UNSUPPORTED on Android 7+. A later implementation would need the user to grant Usage Access for `NetworkStatsManager`, with OS and OEM-specific limits and no fabricated data.
3. **Background policy**: Continuous monitoring is started by the user with a foreground notification, declared as `specialUse` with its explicit subtype for review. Android may stop background processing in battery-saving modes. There is no BOOT_COMPLETED receiver or background-start workaround. Distribution through Google Play may require an additional foreground-service eligibility review; this preview is for local sideloading/testing.
4. **Status bar limitation:** Standard Android apps cannot place a four-part text-and-dot strip **inside the top status bar beside Wi-Fi/battery**. Android reserves that area for system-controlled indicators and small notification icons. This app provides your exact order and changing numbers in the compact **notification shade**, and the expanded shade is At a Glance. The small top-bar icon itself is monochrome and not a speed strip. No overlay or invasive accessibility-service workaround is used.
5. **Internet probes** contact only the endpoints the user configured. HTTPS has a 2.5-second timeout and rejects cleartext; DNS is subject to the OS resolver and may block longer on some devices. This preview is not a network security auditor.
6. Debug-signed APK, **not a Play Store signed production release**. Verify permission prompts and battery settings on your physical phone.

## Installation

Use the APK from [BlazeNetMonitor Android Preview Releases](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazenetmonitor-android-v0.1.1-preview.1). Android must be allowed to install the downloaded APK. Open the app, tap **Start monitoring**, allow Notifications if requested, then swipe down on the notification shade to view live upload/download speeds and expand the card for At a Glance. The first time the donation card appears, it is optional; it can be reopened from Support.

Do not install unknown third-party APKs claiming to be Blaze Systems. Source and hash are in the GitHub release.

## Build

```bash
gradle :app:testDebugUnitTest :app:assembleDebug --no-daemon
```

Uses Android Gradle Plugin 8.7.3, Gradle 8.9, JDK 17 and Android SDK 35. Debug APK output:
`app/build/outputs/apk/debug/app-debug.apk`.

The first CI verifies JVM traffic arithmetic tests, compiles the APK, checks SDK/package/permissions, checks the output hash, and publishes an Android preview. **This does not replace a physical-device acceptance test.**

## Planned parity items

More reliable interface-specific byte accounting on supported Android API levels, optional per-app historical usage with explicit Usage Access, a stronger probe history tracker, user-selectable graph colors/period, and device/battery acceptance tests. These require Android-specific implementation and must not be claimed as shipping features of preview 0.1.0.

## v0.1.1 notification layout acceptance

- Standard Android **status bar remains OS-controlled**; no claim that an app may render arbitrary full-speed text next to the battery/Wi-Fi icons.
- In the collapsed notification shade, left and right dots indicate Target 1 and Target 2 quality, with **upload then download**, both continuously refreshed.
- The expanded card displays both target states and monitored totals. Notification shades vary by device manufacturer, and some may truncate custom collapsed content.
- Android manifest no longer requests `SYSTEM_ALERT_WINDOW`. The obsolete floating overlay source is removed.
- CI validates that the compiled package has no overlay permission and that all four compact notification fields exist in the correct order. Emulator launch and physical-device status bar behavior remain separate checks.
