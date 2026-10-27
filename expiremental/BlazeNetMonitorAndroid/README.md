# BlazeNetMonitor Android — v0.1.8 Preview

## Final disposition — INCOMPLETE (nonblocking notification visuals)

**Owner decision, 2026-10-27:** BlazeNetMonitor Android v0.1.8 is **fully working for the owner's monitoring use**, but the originally requested precision of the notification's target-health dots and target website logos is **INCOMPLETE** on the owner's device. The status describes visual polish and OEM-specific rendering, **not a broken monitoring function**.

- **Repository remains experimental:** `BlazingSystems/BlazingSystems-Experiments`, folder `expiremental/BlazeNetMonitorAndroid/`. Do not migrate to the completed-project repository.
- **Release tag:** [`blazenetmonitor-android-v0.1.8-INCOMPLETE`](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazenetmonitor-android-v0.1.8-INCOMPLETE).
- **Freeze the proven working APK:** This release is a second label for the **identical, debug-signed v0.1.8-preview.1 APK**, built from source commit `dd3728b20408563f05f8038cbb64e6bf653b4b69`, SHA-256 `2ad0bd08ce413233df3ca6bc6af8716b228c4eadb0e0061041bbdad28bfdf2ad`. Do not rebuild and silently claim binary equivalence.
- **Verified on CI:** Android APK build, JVM unit checks and Android 15 emulator foreground smoke. **Owner reports:** monitoring functionality works. These are distinct evidence types. Physical long-duration soak and universal OEM notification visual fidelity are not certified.
- **Incomplete items:** exact readability/visibility of both independently colored health dots and target website logos in the notification shade on the owner's phone. Website-provided favicons and OEM notification scaling can vary; fallback globes may be used.
- **No source/feature modifications** for this status decision. This is a preview release with an accepted visual limitation, not a Play Store production-signoff or a claim of verified device-wide behavior.


**Blaze Systems · Native Android port of BlazeNetMonitor v1.0.0**

Original completed Windows source: https://github.com/BlazingSystems/BlazingSystems-Projects/tree/main/networking/blazenetmonitor

## What works in this first Android build

- Native Java Android application (not WebView). Android 8.0+ (API 26) with target SDK 35.
- One-second **device-wide** network speed readout (Rx/down and Tx/up), from Android `TrafficStats`, all network interfaces combined.
- Seven compact live graph styles: Smooth, Line, Filled, Bars, Steps, Dots, Impulse; blue download and orange upload.
- Session counters (this monitoring process), daily and monthly counters for **monitored activity only** (persisted across app restarts), and Speed units Bits / Bytes.
- Two independently configured health targets: HTTPS HEAD, TCP connect, DNS resolve, and **Reachability** (Android `InetAddress.isReachable` may not use raw ICMP).
- **One ongoing notification** with a readable **download-only numerical status-bar icon**; no health dots or second upload/download notification. Expanded Android shade shows both labelled speeds, two connection-health states, session/day/month totals, optional large Blaze Systems logo, and Stop.
- Download speed updates in the status bar, and both speeds plus target-health status update in the notification shade (nominally every two seconds; Android may throttle rendering). No floating widget, display-over-other-apps permission, or auto-start-at-boot.
- Original fixed owner PayPal QR and developer Facebook profile. No donation recipient changes.

## Important platform differences

1. **Device-wide counters**: Android `TrafficStats.getTotalRxBytes/TxBytes` sum network-layer traffic over all device interfaces since boot. Speed is calculated from monotonic counter deltas each second. Traffic traversing VPNs or tethering might be counted differently from carrier billing. The interface deliberately does not claim per-adapter or per-application accuracy.
2. **Top 5 apps since restart** is **not in this preview**. Android does not provide an ordinary third-party app unfettered historical per-application traffic; `TrafficStats` for other UIDs returns UNSUPPORTED on Android 7+. A later implementation would need the user to grant Usage Access for `NetworkStatsManager`, with OS and OEM-specific limits and no fabricated data.
3. **Background policy**: Continuous monitoring is started by the user with a foreground notification, declared as `specialUse` with its explicit subtype for review. Android may stop background processing in battery-saving modes. There is no BOOT_COMPLETED receiver or background-start workaround. Distribution through Google Play may require an additional foreground-service eligibility review; this preview is for local sideloading/testing.
4. **Status-bar speed icon:** A single monochrome bitmap displays **download speed only** as short digits without health dots or arrows. Android/SystemUI determines its tint, placement, space and visibility. Full units, upload, targets and traffic totals appear in the shade; nothing is drawn as an overlay.
5. **Internet probes** contact only the endpoints the user configured. HTTPS has a 2.5-second timeout and rejects cleartext; DNS is subject to the OS resolver and may block longer on some devices. This preview is not a network security auditor.
6. Debug-signed APK, **not a Play Store signed production release**. Verify permission prompts and battery settings on your physical phone.

## Installation

Use the APK from [BlazeNetMonitor Android Preview Releases](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazenetmonitor-android-v0.1.8-preview.1). Android must be allowed to install the downloaded APK. Open the app, tap **Start monitoring**, allow Notifications if requested, then swipe down on the notification shade to view live upload/download speeds and expand the card for At a Glance. The first time the donation card appears, it is optional; it can be reopened from Support.

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

## v0.1.5 notification layout acceptance

- The **status bar shows changing numeric speeds** via two dynamic bitmap notification small icons, following the documented approach of Internet Speed Meter-like utilities; OS controls whether both fit and in what order.
- In the notification shade, left and right health symbols indicate Target 1 and Target 2 quality, with **upload then download**, both refreshed regularly. The main At a Glance uses the standard Android template for stability.
- The expanded standard notification displays target states and totals. Target website favicons are in the main app's Connection Health section; the notification has status dots instead of website images. Logos are fetched from the configured website's public icon links, without using a third-party favicon proxy. Notification shades vary by device manufacturer, and some may truncate custom collapsed content.
- Android manifest no longer requests `SYSTEM_ALERT_WINDOW`. The obsolete floating overlay source is removed.
- CI validates that the compiled package has no overlay permission and that all four compact notification fields exist in the correct order. Emulator launch and physical-device status bar behavior remain separate checks.

## v0.1.5 monitoring startup and target logos

- Initial service promotion uses a standard Android notification. Rich custom content is posted afterward to avoid delaying foreground-service startup. If a notification update fails synchronously, the OS notification replaces it and the error is logged.
- Start failures are recorded and displayed in the Android activity rather than disappearing without feedback.
- Expanded At a Glance includes the configured websites' official logos when compatible image data can be retrieved. ICO-only, SVG-only or blocking sites fall back to the globe. Target-colored dots remain in the compact strip.
- Actual reproduction of the crash on the user's own Android device remains unverified until new APK field testing. Android emulator testing is an independent acceptance gate.

## v0.1.5 — native notification crash correction (October 27, 2026)

- Removed all RemoteViews/custom notification inflation from the running service. The old custom notification contained a generic View divider, which can cause Android to kill the app asynchronously after posting the notification.
- Notifications continue using OS-owned InboxStyle, not custom RemoteViews, to reduce Android SystemUI rejection. Two changing bitmap small icons render each numeric speed plus a tiny health mark in the status bar. Expanding the main notification shows both targets and session/day/month totals.
- Target website favicons are shown beside the two targets inside Connection Health, without sending images to SystemUI. A generic globe is used when no compatible icon is available.
- Local uncaught-Java-exception recorder and About -> Crash diagnostics -> Copy diagnostics, private storage, manual copy only, max 10 KB; OS kills without Java errors may leave nothing.
- Build/test acceptance does not establish stability on the user's specific phone. Please confirm real-world foreground monitoring after installing the new preview.

## v0.1.5 — Live status-bar speed numbers

- **Corrected prior limitation:** Android can show changing speed digits inside small notification icons. Internet speed meters achieve this by rasterizing text and updating `Notification.setSmallIcon(Icon.createWithBitmap(bitmap))`. BlazeNetMonitor now does that independently in native Java.
- Two notifications supply the two icon slots: left is **health dot + upload**; right is **download + health dot**. The status-bar glyphs are *monochrome* and each icon is limited to a small 24dp logical slot; to fit, numbers are abbreviated (e.g., `1.2M`). The exact order and spacing are subject to SystemUI/OEM and the user's other notifications.
- The main notification shade uses the full upload/download labels, health indicators and At a Glance summary. An extra low-importance download notification exists so the operating system has two changing small icons. Both are removed when monitoring stops.
- Start Monitoring crash is still under investigation on the owner's device. The Java exception recorder in About → Crash diagnostics is available; compilation and unit tests are not evidence that the real-device crash is fixed.
- Builds remain **debug-signed previews** and retain the completed Windows v1.0.0 untouched.

## v0.1.5 — Safe foreground start with dynamic icons

- Promotes the service immediately using a static framework icon so no bitmap generation can delay Android's foreground-service startup requirement.
- Once running, uses the Android status-bar dynamic-small-icon technique for two numerical upload and download indicators, with tiny monochrome target health marks. The UI still shows full speeds and colored target states in the expanded notification.
- SystemUI may coalesce, reorder or hide small icons based on status bar space and OEM configuration; this is a native Android status bar feature, not an overlay.
- The user's prior service-termination report remains a field-verification gate. Debug-signed preview; see About → Crash diagnostics for Java crash information if the problem persists.


## v0.1.6 — single notification with clear download indicator

- Fixes reported duplicate notifications in v0.1.5. A single foreground notification ID 101 replaces the dual notification arrangement; on startup, obsolete ID 102 is canceled so in-place updates clean up leftover cards.
- Status-bar notification icon contains the download-speed number only. The small glyph has no health dots or arrows, leaving more space for readable digits.
- One standard Android InboxStyle notification contains download and upload speeds, clearly named Target 1 and Target 2 health states, session/day/month totals, an optional large Blaze Systems logo and Stop.
- Android can choose whether/how to display the large logo or expanded text. Neither custom RemoteViews nor floating overlays are used.
- Android emulator regression checks the app's active notification records: exactly ID 101 and no 102 or extra auto-group summary. Device-specific legibility and reliability still require physical-device acceptance.


## v0.1.7 — expanded notification target logo and health-dot correction

- User field report: v0.1.6 removed tiny dots from the status bar, but this also left **no visible health dots or individual website logos inside the notification shade**. The one large notification icon was the app logo, not two independent website favicons.
- Expanded notification now uses native Android **BigPictureStyle**, containing a bounded RGB_565 image with two large, real-colored Target 1 / Target 2 health dots, two separately loaded HTTPS site-favicon bitmaps when available, human-readable connection labels/details, both speeds and session/day/month traffic totals. An explicitly drawn globe is the fallback when a real favicon is not retrievable or supported. No proprietary/web icon is fabricated.
- Favicons are fetched asynchronously from the configured sites, rechecked periodically and when their target settings change. Fetching cannot delay initial foreground-service promotion. A failure to render the rich image falls back to the standard text InboxStyle instead of crashing the service. Website icons are shown in the rich shade card, **not** in the tiny monochrome status bar.
- One persistent notification ID 101 remains; legacy 102 is canceled. Download-only number stays in the status bar. The Blaze app logo still uses the standard notification largeIcon field, but OEM SystemUI may omit it independently of the rich card.
- BigPictureStyle dimensions/scaling, rounded-corner clipping, notification collapse, typography and background throttling vary across Android versions/OEMs. Android 15 CI captures a screenshot of the expanded notification shade. CI launch, compilation and image attachment evidence cannot replace owner physical-device verification.


## v0.1.8 — compact rich shade and broader favicon support

- An actual Android 15 emulator screenshot of v0.1.7 proved visible large health dots but showed the MONTH total cropped by SystemUI. The rich notification bitmap is now only 426px high and includes all three traffic totals.
- Google and Cloudflare favicon requests failed with `UnknownHostException` in that emulator, so it showed honest globe fallbacks. Real logo retrieval still needs working HTTPS/DNS. The favicon loader now supports embedded PNG frames in .ico containers, with bounded-header validation and JVM tests.
- One ID 101 foreground notification and download-only small status icon remain. OEM physical appearance is not yet accepted.
