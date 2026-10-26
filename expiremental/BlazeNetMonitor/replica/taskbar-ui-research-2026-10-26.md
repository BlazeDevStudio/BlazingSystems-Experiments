# BlazeNetMonitor: taskbar and UI research (2026-10-26)

Current v0.1.0 has fixed dark colors in Theme.cs and a 452×55 topmost WinForms window in MonitorForm.cs. The "inside taskbar" setting repositions a window rather than integrating with the Windows taskbar layout.

Windows 11 does not publish a general-purpose API for inserting a custom text monitor into its taskbar. Supported alternatives include the notification area. Windows 10 supports older deskband extensions; these are not a reliable cross-version Windows 11 strategy. Community shell customization approaches are possible but fragile across system updates and should be strictly optional.

Recommended direction:
1. Theme = System/Light/Dark/Custom, system accent and contrast-aware display.
2. Opacity setting, compact speed and two-dot view, adjustable font, accessible health labels.
3. Reliable tray icon and non-overlapping, DPI-aware fallback on Win10/11.
4. Investigate version-specific optional taskbar hosts separately; do not present a topmost overlay as embedded.
5. Maintain separate builds/QA for UI, taskbar integration, and real devices. Never claim a CI build proves desktop compatibility.

The ~47 MB standalone Windows package includes the .NET runtime. Offer a smaller framework-dependent build with clear runtime requirements before considering a native code rewrite.

References:
- https://www.microsoft.com/en-ph/windows/windows-11-specifications/
- https://learn.microsoft.com/en-us/windows/win32/shell/taskbar
- https://learn.microsoft.com/en-us/windows/win32/shell/taskbar-extensions
- https://learn.microsoft.com/en-us/windows/win32/shell/abm-gettaskbarpos
- https://learn.microsoft.com/windows/apps/desktop/modernize/apply-windows-themes
- https://learn.microsoft.com/en-us/dotnet/core/deploying/single-file/
- https://github.com/zhongyang219/TrafficMonitor/wiki/Option-Settings
- https://github.com/zhongyang219/TrafficMonitor/blob/master/UpdateLog/update_log_en-us.md

Status: research only. No native taskbar integration is claimed.
