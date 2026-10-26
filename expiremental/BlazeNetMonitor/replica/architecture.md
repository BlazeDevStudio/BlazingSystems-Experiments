# Architecture — 2026-10-26

**Stack:** .NET 10 WinForms (Windows-native application) and .NET 10 headless core. No NuGet dependencies and no elevated privileges. C# managed memory, no network driver or COM shell injection.

**Flow:** `NetworkMonitor.Sample()` reads `NetworkInterface.GetIPv4Statistics()` monotonic adapter counters; `MonitorMath.Compute()` computes bytes/s from wall-independent `Stopwatch` duration. `NetworkMonitor.Probe()` independently probes targets in parallel via ICMP/HTTPS/DNS/TCP and updates `QualityTracker` states; `MonitorForm` paints speed and dot colors; `InfoForm` shows up-to-date hover stats. `Storage` saves locally as atomic-replace JSON, and `SettingsForm` edits settings.

**Data:** AppSettings (one current local user), ProbeTarget (2 per settings), TargetHistory (sample list and stable streak), TrafficTotals (session / day / month). No SQL or HTTP API needed. Filenames scoped to current Windows user; no cloud data is sent.

**Security:** No remote code execution, shell injection, server, telemetry, admin privilege, persistence service, or borrowed binary. Target URLs are user-entered; HTTPS-only accepted for HTTP checks. Registry autostart is HKCU, user can turn off. Unlimited probe endpoints could be misused by a bad actor with local desktop access; this utility probes only 2 configured targets every 3+ seconds.

**Major design tradeoff:** Windows 11 removed official classic taskbar toolbars. Use portable topmost overlay by WorkArea, with user-selectable optional on-taskbar overlay. No guarantee of full shell parity, especially on vertical/multiple monitors.

**Milestones:** M1 source+headless algorithm tests; M2 successful Windows runner build and downloadable EXE; M3 Windows 10+11 manual smoke and networking quality testing; M4 signed installer and release.
