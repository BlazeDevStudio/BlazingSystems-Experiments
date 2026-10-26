# BlazeNetMonitor v0.1.0 — development preview

**Blaze Systems** · Independent Windows 10 / Windows 11 network monitor inspired by the functional concept of Florian Gilles' classic NetSpeedMonitor. No original binary, source code, logo, or proprietary assets are included.

## What it does

- Always-on-top, compact **taskbar-adjacent network speed widget** with original orange live sparklines, upload/download indicators, and selectable active network interface.
- **Two independent configurable status dots**: ICMP, HTTPS HEAD, DNS lookup, and TCP connect; separate host / URL / port per dot.
- **Hover network dashboard**: selected interface, IPv4, uptime, current status, response time, recent packet loss, jitter, and session/day/month traffic totals.
- Startup toggle, bits vs bytes, connection table, and copyable diagnostic summary from tray/context menu.
- Saves configuration and totals under `%LOCALAPPDATA%\BlazeSystems\BlazeNetMonitor\state.json` without admin privileges.
- Entirely offline local administration; only target probes contact configured hosts.

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

Requires .NET 8 SDK on a Windows machine (not required for the self-contained published EXE).

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

GitHub Actions builds the test harness and a self-contained `BlazeNetMonitor.exe` for x64 and x86 and uploads each as an artifact. No third-party binaries or drivers.

## UI interaction

- **Hover** the widget for glance status and transfer counters.
- **Click one of the two dots** to configure the checks; **right-click** for the context menu.
- Tray icon **double click** to configure even if the overlay is obscured.
- General settings supports **above-taskbar** (recommended) or **taskbar-area overlay** (experimental, could overlap taskbar icons). The latter is **not native shell/deskband integration**.

## Compatibility and limitations

- Intended Windows 10 and Windows 11 desktop (WinForms) with per-monitor DPI awareness. Builds on Windows hosted runners are **not Windows 10/11 installation tests**.
- **Future Windows versions are a compatibility goal, not a guarantee.** Avoids undocumented Explorer injection, custom shell DLLs, privileged drivers, or taskbar reparenting. Placement may still require changes when Microsoft changes taskbar behavior.
- The main monitor currently assumes an ordinary primary-monitor taskbar; vertical/multiple taskbars need more work.
- Traffic counters count **adapter-wide bytes**, including local network activity, not per-app or ISP-billed usage. Selected adapter is a single adapter at a time; changing it resets the delta baseline.
- Health assessment is based on probes only; not a throughput benchmark.
- Development preview: no installer, code signing, manual Windows 10/11 hardware test report, or validated release as of initial commit.

## Attribution

Independent project by Blaze Systems. Original historical NetSpeedMonitor by Florian Gilles; referenced for user-facing functional concepts only. Do not redistribute original NetSpeedMonitor binaries or artwork as part of this application.
