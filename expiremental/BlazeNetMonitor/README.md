# BlazeNetMonitor v0.2.9 — streamlined settings and Windows Connections selector

**Blaze Systems** · Independent Windows 10 / Windows 11 / Windows Arm64 network monitor inspired by the functional concept of Florian Gilles' classic NetSpeedMonitor. No original binary, source code, logo, or proprietary assets are included.

## What it does

- Resizable, movable **freeform network-speed widget** with original orange live sparklines, upload/download indicators, and selectable active network interface.
- **Two independent configurable status dots**: ICMP, HTTPS HEAD, DNS lookup, and TCP connect; separate host / URL / port per dot.
- **Hover network dashboard**: selected interface, IPv4, uptime, current status, response time, recent packet loss, jitter, and session/day/month traffic totals.
- Startup toggle, bits vs bytes, connection table, and copyable diagnostic summary from tray/context menu.
- Saves configuration and totals under `%LOCALAPPDATA%\BlazeSystems\BlazeNetMonitor\state.json` without admin privileges.
- Entirely offline local administration; only target probes contact configured hosts.

## v0.2.9 — concise settings, graph types and Windows Connections (October 27, 2026)

- Removed the three unwanted marketing/disclaimer phrases from **About**. It now gives a short functional description, developer contact, PayPal QR and one Open PayPal action.
- Display copy formerly saying **Auto adaptive** is now simply **Adaptive** in Graphs and Metrics, without changing the stored `Auto` preference or saved configurations.
- **Seven graph drawing types:** Line, Smooth, Filled, Bars, Steps, Dots, and Impulse. Upload/download graph colors, history length, and refresh cadence continue working.
- **Network adapter dropdown:** Defaults to the adapter names actually displayed by the Windows **Network Connections** shell folder (the virtual folder that `ncpa.cpl` opens). The names are discovered dynamically, never hardcoded to LAN/Wi-Fi. Adapters disconnected in Windows remain listed; an adapter which is visible but unavailable is shown as unavailable instead of silently selected. **Advanced network adapters** shows additional interfaces from `NetworkInterface.GetAllNetworkInterfaces()` including VPN/virtual/tunnel adapters.
- If shell COM enumeration cannot run in a restricted Windows session, no guessed interfaces flood the default view. The UI explains the fallback, and Advanced mode gives access to the adapters exposed by .NET.
- An exact-head Windows test checks the native Network Connections mapping when the shell is available; this is still subject to manual verification on machines where `ncpa.cpl` differs from the hosted Windows runner.

## v0.2.8 — PayPal splash clarity and About QR crop fix (October 27, 2026)

- **Startup card:** Removed opacity animation entirely so the complete center-screen QR remains **fully opaque**, visible for 11 seconds unless closed by Esc, Not now, or Open PayPal. This avoids the barely-visible flash observed in v0.2.7.
- **About:** Fixed the real clipping cause: v0.2.7's QR renderer always allocated at least **200x200** while About displayed it in a **154x154** image box, clipping portions of the matrix. New image is rendered to its requested dimensions, at **240x240** in a 240x240 Zoom-mode PictureBox. The surrounding panel scrolls at nonstandard DPI.
- Removed the **Show donation QR card** button and **Every launch / First launch / Never** dropdown from About. The QR is already fully visible in About. The donation splash still has a "Don't show on startup" checkbox, and can still be reopened using the right-click tray menu.
- Owner-specific PayPal destination and two independent network monitoring targets remain unchanged.
- **CI gate:** Windows GDI+ QR raster checks at 154/240/352px, splash alpha/layout inspection and About no-crop/no-selector check precede release packaging. Automated tests do not establish real-world PayPal scanning on a mobile phone.

## v0.2.7 — Creator donation QR finalized (October 26, 2026)

This release corrects the earlier donor-QR design. The image attached by Blaze Systems owner Loumer Cabaluna Manreal was decoded and verified to contain a PayPal QR destination. The same destination is now hardcoded for **every** copy of the app. Visitors never choose, upload, or replace the donation QR. To prevent losing scan quality at different DPI, the app renders a crisp 41x41 error-correction-H QR matrix corresponding to that verified uploaded image; the visual pixels are reconstructed, not an exact photographic copy of the original image. The owner name is displayed above the QR and the colors mirror the supplied black/blue/white QR.

- Start app: display a **center-screen** card for about 7 seconds with fade-in/out, owner QR, and: **“Your support helps keep this free project improving. Any amount is deeply appreciated.”**
- The card is dismissible immediately via **Not now** / Esc; **Open PayPal** opens the official destination and closes the card; **Don't show on startup** permanently disables automatic startup prompts.
- **Settings → About** allows **Every launch (default)**, **First launch only**, or **Never**. Old installations will display the card on the next launch unless opted out; the user's saved network settings remain untouched.
- **Tray / widget right-click → Support development · PayPal QR** always reopens the donation card, even when automatic prompts are disabled.
- About shows a small QR, "Open creator's PayPal", the Facebook link `https://fb.me/manrealloumer`, and a donation card preview. No donation-QR file browser remains.
- The QR destination is stored offline in `DonationSplashPolicy.cs`; no network request is needed to draw or scan the code. The optional Open PayPal action launches the destination through the user's normal browser; no automatic donation takes place.
- The network widget, probe timers, session tracking and status lights continue operating while the splash is displayed.
- **Privacy:** The PayPal URL is a public payment destination, not a credential; the app does not collect card details, accept payments itself, or route through Blaze Systems servers.
- **Testing:** Core unit tests enforce one fixed donation destination, QR finder matrix, and popup policy. GitHub CI packages x64/x86/ARM64 and Lite. Actual Windows desktop interactions and payment processing have not been certified.

## v0.2.6 UX cleanup and install options (October 26, 2026)

- **Health targets:** Default labels are now **Target 1** and **Target 2**. Legacy default labels `Primary DNS`/`Secondary DNS` migrate visibly, preserving custom names. Each protocol selection changes the grey `PlaceholderText` and label; it never writes the example as an address. Input drafts persist within the edit session across protocol switches.
  - ICMP: `1.1.1.1 or example.com`
  - HTTPS: `https://www.example.com`
  - TCP: `example.com` plus visible **Port**
  - DNS: `example.com`
  - TCP Port disappears for ICMP/HTTPS/DNS, with protocol-specific validation upon saving.
- **Adapter dropdown:** Only currently enumerated physical Ethernet/Wi-Fi adapters by default, whether connected or disconnected. Virtual/VPN/tunnel/loopback interfaces are hidden to avoid clutter, with **Also show virtual, VPN and tunnel adapters** opt-in. Device Manager-disabled adapters that Windows does not expose via NetworkInterface cannot be enumerated by this version.
- **Streamlined controls:** Removed the duplicate speed-unit selector from General; Metrics remains the single place to configure units. Horizontal offset hides when freeform mode is selected. Windows-themed tabs and a small blue network-speed icon now follow the Blaze Systems blue palette.
- **First-run experience:** Shows only on a fresh installation and only once. Upgrading earlier settings never triggers the welcome screen again. Donation QR is optional; **the original verified PayPal QR was not found in recoverable prior files** and the installer contains no fabricated payment URL. If the authentic QR is imported using About → Import authentic PayPal QR, the QR is stored locally under `%LOCALAPPDATA%\\BlazeSystems\\BlazeNetMonitor\\paypal-donation.png`, or may be packaged as `paypal-donation.png` beside the EXE after verification.
- **About:** Creator and Facebook link `https://fb.me/manrealloumer`, donation QR image if available, and clear version / integration disclosures.
- **Package size:** x64 **lite** uses a framework-dependent .NET 10 Windows Desktop Runtime app and is smaller at the cost of installing the matching .NET Desktop Runtime. The full x64/x86/ARM64 portable packages remain self-contained. Avoid trimming WinForms blindly because it is not a safely supported size reduction.
- **QA:** Added deterministic input/placeholder/adapter-filter checks; Windows GUI build and launch checks do not prove all real pointer, DPI, combobox or onboarding behavior.

## v0.2.5 — General website favicon support (October 26, 2026)

- **Not limited to Cloudflare and Google:** Enter an ordinary domain such as `www.facebook.com`, `www.wikipedia.org`, `github.com`, or a complete HTTPS URL as a health target. The two special DNS resolver IP mappings remain solely to provide meaningful vendor icons for numeric DNS endpoints.
- With **Settings → Metrics → Show round website favicons** enabled, the application first checks each target's public HTTPS `/favicon.ico`. If the server redirects to a public CDN, up to four validated HTTPS redirects are followed. If missing or unreadable, the official homepage's `<link rel="icon" href="...">` and related icon declarations are checked, including relative and HTTPS CDN URLs.
- Circular 32×32 normalized images appear beside their **separately colored** network status dot. If the icon cannot be loaded, only the dot appears; the monitoring probe still works. Supported images depend on Windows GDI+ decoders (ICO, PNG, JPEG, GIF).
- For narrower user-resized widgets, icon rendering is now allowed from about 150–160 logical pixels. If both icon and speed readout appear cramped, increase the widget width.
- Right-click the widget or tray menu → **Refresh website favicons** to retry a previously unavailable logo. Logos are retrieved only when opted in, on startup, when the target/settings change, or upon explicit retry.
- Privacy and safety: Public HTTPS origins only; no private/local addresses or redirected credentials, non-HTTPS downgrades, or unusual ports; DNS addresses are checked before connecting. Icons are decoded to small memory-only bitmaps; images and HTML have byte limits. No third-party favicon retrieval API or remote database.
- Some websites deny automated retrieval, rely exclusively on SVG icons, or do not publish a usable icon. Those cases retain the normal status dot. Real-world Facebook favicon retrieval has not yet been confirmed on the user's machine.

## v0.2.4 preview changes (October 26, 2026)

- **Settings dropdown stability:** live-preview changes no longer restyle ComboBox controls during selection. Theme dialog restyling is deferred until its native dropdown is closed; the taskbar overlay's periodic topmost promotion is also suspended while Settings is open.
- **Graphs:** Four types (**Line**, **Filled**, **Bars**, **Steps**), separate upload and download HEX colors, optional graph duration (**Auto**, 15/30/60/120/300/600 seconds) and refresh speed (**1/2/5 seconds**). History-window sizes use the selected refresh interval, and graph samples reset if cadence changes; traffic totals do not.
- **Metrics:** A separate Metrics tab offers **Auto adaptive**, speed-only, latency, packet loss, jitter and today's totals. At micro/taskbar sizes the live upload and download rates take priority; secondary metrics appear when the window has room. Automatic history choices prefer 30/60/120 seconds by layout. The rate-unit selection includes Auto/Bits/Bytes.
- **Dot history:** Status tracks the most recent 12 probes (latency trends) and 6 probes (recent packet loss/jitter), with baseline latency, two consecutive failed probes for red, severe issues for orange, moderate degradation or recovery for yellow, green after healthy recovery, and blue only after a continuous verified streak lasting at least 24h and crossing a local calendar day. A missed sampling gap revokes the blue streak.
- **Circular favicon badges:** Metrics → **Show round website favicons** is off by default. When enabled, favicon icons are fetched once upon app start or settings save from the official target origin's HTTPS `/favicon.ico` URL. IPv4 DNS targets 1.1.1.1/1.0.0.1 map to one.one.one.one, and 8.8.8.8/8.8.4.4 map to dns.google. All other numeric IPs and local/internal targets are rejected for icon fetching. Hostname connections validate public resolved addresses before connecting; no redirects, a 96 KiB image cap, a short timeout, and memory-only decoded icons. Unsupported hosts or absent favicon.ico simply retain the status dot.
- **Privacy/security:** Favicons make optional outbound HTTPS requests distinct from probes. They are never fetched when disabled and their image cache is memory-only. Redirects are prohibited and no third-party favicon aggregation service is used.
- **Continued limitations:** A result of green or yellow does not prove or disprove the connection's streaming capacity. ICMP-blocking networks may require a different probe protocol. On Windows 11 the taskbar mode remains an independent overlay rather than genuine Explorer integration.

### Validation boundaries

GitHub CI compiles self-contained Windows x86/x64/ARM64 executables, runs algorithm and settings persistence checks and an x64 GUI process launch smoke check. Real-world settings dropdown interaction, diskless favicon fetching, taskbar overlap, color-key transparency, multi-monitor behavior and 24h blue status require Windows hardware testing.


## v0.2.3 Transparent widget, graphs and recovery (October 26, 2026)

- **Backgroundless mode:** Settings → Appearance → Transparent background (text, dots and graphs only). WinForms `TransparencyKey` makes the entire canvas transparent while keeping painted glyphs/indicators visible. **Important:** transparent/empty regions let pointer clicks pass to the underlying window; right-click the system-tray icon or use the painted widget content to open settings. Color-key anti-alias fringe behavior depends on Windows compositor/theme and needs device QA.
- During **Resize / move** the form temporarily becomes opaque, restoring a complete draggable edit surface. Upon Finish/Cancel, the transparency setting is restored. High-contrast Windows accessibility settings override the backgroundless effect.
- **Both live traffic sparklines display at every supported widget height (24 px and higher)** whenever Show Graphs is enabled, including in a narrow widget. A visible line track is shown until at least two traffic samples exist.
- **Inside taskbar overlay:** an opt-in foreground Z-order guard attempts non-activating HWND_TOPMOST recovery approximately every two seconds and after placement events; it does not inject into Explorer. This cannot guarantee a position above every Windows 11 topmost taskbar element or reserve tray/icon space. **Use the tray menu → Recover above taskbar (safe)** when Windows 11 covers the overlay.
- **Already running:** starting a second v0.2.3 EXE requests the existing v0.2.3 session to open Settings rather than launching another. When replacing **an older v0.2.x version**, manually exit the older session via the hidden tray icons first—older instances do not implement this request.
- **Recovery:** context/tray menu includes Bring widget in front and Recover above taskbar (safe). Fullscreen application auto-hide remains enabled by default; the Z-order recovery does not intentionally bypass fullscreen suppression.
- All existing two-dot quality states, freeform resize, theme and independent hover opacity settings are retained.

**Validation:** algorithm and persistence tests plus Windows CI compilation and an x64 launch smoke check are automated. Taskbar overlap behavior, colored glyphs and graphs on transparent backgrounds, DPI changes and mouse hit testing **must be verified on a physical Windows desktop**.

## v0.2.2 Taskbar placement and compact sizing (October 26, 2026)

**This is an overlay, NOT native Explorer taskbar integration.** The window remains a separate process.

- Three placement options in Settings → General: **Floating** (anywhere on the screen, including taskbar), **Above taskbar** (restricted to desktop working area), and **Inside taskbar (overlay)** (positions over the detected taskbar rectangle).
- Win32 `SHAppBarMessage(ABM_GETTASKBARPOS)` is used for the primary system taskbar; secondary-monitor fallback derives from `Screen.WorkingArea` exclusions. Automatic placement requires an available taskbar rectangle; manual freeform mode remains possible.
- Taskbar overlay is **explicitly user-selected** and can cover taskbar buttons or tray icons. No Explorer injection or COM registration.
- Right-click **Match taskbar height (overlay)** to measure the currently detected horizontal taskbar and fit the widget height with 2px top and bottom gaps while preserving its width.
- Resizing minimums changed from **210×52 px** to **124×24 logical pixels** (actual physical pixels depend on per-monitor DPI).
- At heights below 39 pixels the status dots become horizontal and both rates render in one row using compact units; taller layouts retain stacked/full text and graphs where space permits.
- Width/height, position and selected placement mode persist; changing opacity or theme in Settings does not reset the manual position in the same mode.
- Foreground fullscreen auto-hide and independent compact hover opacity from 0.2.1 are retained.

## v0.2.1 QA-driven fixes (October 26, 2026)

- **Taskbar occlusion:** move/resize and saved freeform locations are confined to the actual Windows **working area**, with 6 px handle safety padding. The old overlay-inside-taskbar mode is intentionally disabled until real shell integration is implemented.
- **At-a-glance:** smaller 356 × 226 px nonactivating status card with independently configurable 40–100% opacity.
- **Live settings:** dialog is **modeless**; the widget remains visible, counters and health probes keep running, and appearance/opacity/adapter/units preview immediately. Cancel restores prior behavior. Autosave persists the original settings until explicit Save.
- **Hover preview:** moving the at-a-glance opacity slider briefly shows the small panel at the current setting, then dismisses it automatically.
- **Fullscreen apps:** an independent visibility timer detects an external fullscreen foreground window on the widget's monitor and temporarily hides the widget and popup. Network sampling continues; it reappears without activating or stealing focus when the fullscreen foreground window is left. Enabled by default, configurable under Appearance.
- **Theme:** settings editor follows light/dark/high-contrast palette changes more consistently.
- Existing settings and dual target color rules are preserved; user hardware verification is still required.

### QA gates
- Pure regression checks cover screen bounds, fullscreen rectangle geometry, independent preview copy, theme/hover alpha persistence, quality logic and network counters.
- Windows CI compiles x64/x86/ARM64 self-contained EXEs and runs a 7-second x64 process launch smoke check.
- A Windows runner does **not** validate manual resizing, Z-order behavior on a real Windows 11 taskbar, UAC/Explorer interactions, fullscreen games, F11 browsing, mixed-DPI displays or accessibility. This remains a preview, not an accepted production release.

## Status-dot semantics

| Color | Status | Rules (recent observations) |
| --- | --- | --- |
| Gray | Unknown | No completed probe |
| Red | Down | Two consecutive failed checks |
| Orange | Unstable | Failure, loss >=20% once 4 samples, average latency >350ms, or jitter >100ms |
| Yellow | Degraded | Loss >=5% once 4 samples, average latency >180ms, or jitter >60ms |
| Green | Stable | None of the above |
| Blue | Continuously stable since yesterday | Green continuously for >=24h, crossing a local calendar day, with no recent probe gaps |

**Important:** 'yellow: can browse but not stream' is a **quality heuristic**, not a verified bandwidth test. ICMP-blocking websites can be reachable; switch to HTTPS or TCP. DNS success proves name resolution, not end-to-end browsing. A missed-probe gap >max(15 seconds, 3 × configured interval) resets the blue-stability streak.

## Build and run

Requires .NET 10 SDK on a Windows machine (not required for the self-contained published EXE).

```powershell
cd src/BlazeNetMonitor
dotnet run
```

Test core algorithms without external NuGet packages:

```powershell
dotnet run --project tests/BlazeNetMonitor.Tests/BlazeNetMonitor.Tests.csproj
```

Publish a portable single-file 64-bit EXE:

```powershell
dotnet publish src/BlazeNetMonitor/BlazeNetMonitor.csproj -c Release -r win-x64 -p:PublishSingleFile=true -p:SelfContained=true -o dist/win-x64
```

GitHub Actions builds the test harness and a self-contained `BlazeNetMonitor.exe` for x64, x86, and Arm64 and uploads each as an artifact. No third-party binaries or drivers.

## v0.2 appearance and freeform editing

- Right-click the widget and choose **Resize / move widget**. The four highlighted grips indicate that editing is active; drag a boundary/corner to resize or drag the center to move.
- Choose **Finish resize / move** from the menu, or double-click the widget, to save its size and location. **Cancel resize** restores the initial bounds.
- In **Settings → Appearance**, use **Save and resize / move widget** to enter edit mode; adjust **opacity 40–100%**, **System/Light/Dark** theme, Windows accent, and graphs.
- The compact view automatically drops graphs when height is below 82 px. High-contrast mode overrides transparency for legibility.
- The new position is persisted per-user and does not snap back during sampling. If the screen is disconnected, the widget returns to the visible screen.

### Windows version and genuine DeskBand

Windows 10 (NT 10 build 10240–21999) is classified as **eligible for classic DeskBand** using a tested OS policy. **Eligibility does not mean DeskBand is installed or active**. This release does **not yet ship the native COM Shell DLL or registration flow**, so Windows 10 users receive freeform/tray mode rather than a fake "embedded" widget. Windows 11 (build 22000+) fails closed to freeform/tray mode, with any optional shell extension a separate, later project. Never run undocumented Explorer injection automatically. See `replica/taskbar-ui-research-2026-10-26.md`.

## UI interaction

- **Hover** the widget for glance status and transfer counters.
- **Click one of the two dots** to configure the checks; **right-click** for the context menu.
- Tray icon **double click** to configure even if the overlay is obscured.
- Above-taskbar placement remains constrained to usable desktop space; inside-taskbar overlay is opt-in and constrained to monitor bounds, not Explorer child controls. Its Z-order is best-effort and cannot guarantee compatibility with taskbar updates.

## Compatibility and limitations

- .NET 10 LTS is actively supported through November 2028; regular Windows 10 Home/Pro reached end of OS support in October 2025. Windows 10 application runtime support is best-effort unless the Windows edition/build is still supported by Microsoft.


- Intended Windows 10 and Windows 11 desktop (WinForms) with per-monitor DPI awareness. Builds on Windows hosted runners are **not Windows 10/11 installation tests**.
- **Future Windows versions are a compatibility goal, not a guarantee.** Avoids undocumented Explorer injection, custom shell DLLs, privileged drivers, or taskbar reparenting. Placement may still require changes when Microsoft changes taskbar behavior.
- The legacy taskbar-adjacent placement still assumes a conventional primary taskbar; freeform positioning persists independently and can move between monitors.
- Traffic counters count **adapter-wide bytes**, including local network activity, not per-app or ISP-billed usage. Selected adapter is a single adapter at a time; changing it resets the delta baseline.
- Health assessment is based on probes only; not a throughput benchmark.
- Development preview: no installer, code signing, manual Windows 10/11 hardware test report, or validated release as of initial commit.

## Attribution

Independent project by Blaze Systems. Original historical NetSpeedMonitor by Florian Gilles; referenced for user-facing functional concepts only. Do not redistribute original NetSpeedMonitor binaries or artwork as part of this application.
\n> Historical notice: v0.2.6's QR import feature was retired in v0.2.7. Visitors cannot replace the creator's PayPal destination.\n