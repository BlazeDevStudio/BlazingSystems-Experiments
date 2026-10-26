# BlazeNetMonitor v0.2.2 — taskbar overlay and compact resize preview

**Blaze Systems** · Independent Windows 10 / Windows 11 / Windows Arm64 network monitor inspired by the functional concept of Florian Gilles' classic NetSpeedMonitor. No original binary, source code, logo, or proprietary assets are included.

## What it does

- Resizable, movable **freeform network-speed widget** with original orange live sparklines, upload/download indicators, and selectable active network interface.
- **Two independent configurable status dots**: ICMP, HTTPS HEAD, DNS lookup, and TCP connect; separate host / URL / port per dot.
- **Hover network dashboard**: selected interface, IPv4, uptime, current status, response time, recent packet loss, jitter, and session/day/month traffic totals.
- Startup toggle, bits vs bytes, connection table, and copyable diagnostic summary from tray/context menu.
- Saves configuration and totals under `%LOCALAPPDATA%\BlazeSystems\BlazeNetMonitor\state.json` without admin privileges.
- Entirely offline local administration; only target probes contact configured hosts.

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
