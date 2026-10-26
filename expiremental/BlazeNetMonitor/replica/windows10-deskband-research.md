# BlazeNetMonitor — Windows 10 native DeskBand host research
Date: 2026-10-26
Status: **design / gated**. No native DeskBand DLL is shipped in v0.2.0; OS detection is live and unit tested.

## Real integration versus imitation
- Microsoft's `CATID_DeskBand` component category + `IDeskBand` / `IObjectWithSite` / `IPersistStream` interfaces give real classic taskbar toolbars. They are COM in-process components and appear in Windows 10 taskbar Toolbars menu after correct registration. A separate registered host is necessary.
- NetSpeedMonitor historically used the classic toolbar behavior; known Windows 10 workarounds use installation compatibility mode. This does NOT imply stock Windows 11 supports DeskBand.
- CSDeskBand (https://github.com/dsafa/CSDeskBand) is an **MIT-licensed** reference implementation for WinForms/WPF DeskBands; upstream documents COM registration and Win10 x64 testing. Do not copy its source without retaining its MIT license/attribution.
- TrafficMonitor (https://github.com/zhongyang219/TrafficMonitor/wiki/Taskbar-Window) instead reports embedding its own window as a taskbar child, with documented security-software and Start-menu failure modes. Merely setting `SetParent` is not the same as a registered DeskBand or documented taskbar layout contract; avoid calling that fully native.
- Alternative modern examples: NetSpeedTray (https://github.com/erez-c137/NetSpeedTray) and NetSpeedCat (https://github.com/LITTOMA/NetSpeedCat). Their claims do not establish our app works similarly.

## Capability gate implemented
`BlazeNetMonitor.Core.WindowsVersionPolicy` classifies:
- Windows NT 10 build 10240 through 21999: classic Windows 10 candidate.
- NT 10 build 22000 and later: Windows 11 or later, **no automatic DeskBand**.
- All unrecognized versions: conservative external/tray fallback.

The `IsNativeHostReady` predicate requires both Windows 10 eligibility *and* a verified installed host; detection alone does not mean successful COM registration. This version ships no host installer, and must not display “native integrated” status.

## Next Windows 10 native-host implementation gate (not yet satisfied)
1. Design an out-of-process .NET 10 monitor with a versioned, nonblocking, read-only current-user IPC snapshot feed. The in-Explorer component must not sample network, persist counters, or run probes.
2. Create a dedicated Win32 or .NET Framework 4.8 DeskBand COM server, minimal UI only, `CATID_DeskBand`, `IDeskBand2`, `IObjectWithSite`, `IPersistStream`. Ensure Explorer architecture (x64/x86) matches; avoid downloading or loading unverified foreign code.
3. Install/uninstall COM registration per-user when possible, with explicit user consent, complete rollback, and a guard that refuses on Windows 11/unknown build.
4. Test taskbar toolbar appearance and resize, Explorer crash/restart, logoff/login, auto-hide, single/multiple taskbars, DPI changes, renderer process failure, timer shutdown, privilege boundaries and Windows 10 build 19045.
5. Keep freeform/widget fallback working when any host check fails; do not automatically modify Explorer as part of the preview install.

## UX scope delivered in freeform preview
- User can enter **Resize / move widget**, drag all four edges/corners (plus middle), finish/save, or cancel/restore original bounds.
- Persist geometry and opacity; no polling-induced snap-back.
- System/light/dark theme, taskbar-vs-app Windows theme registry preference, accent, high contrast.
- Responsive graphs; two distinct health dots, speed counters and hover panel preserved.
- Native Win10 DeskBand remains an explicit backlog milestone, not a claimed feature.

## Primary references
- https://learn.microsoft.com/en-us/windows/win32/shell/band-objects
- https://github.com/dsafa/CSDeskBand
- https://github.com/zhongyang219/TrafficMonitor/wiki/Taskbar-Window
- https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setparent
- https://bradshacks.com/netspeedmonitor-windows-10/
- https://github.com/erez-c137/NetSpeedTray
- https://learn.microsoft.com/windows/apps/desktop/modernize/apply-windows-themes
