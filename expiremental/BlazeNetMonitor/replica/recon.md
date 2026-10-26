# Replica recon — 2026-10-26

## Scope and source ledger

| Evidence | Proves | Limitation |
| --- | --- | --- |
| User-provided screenshots in conversation, 2026-10-26 | Taskbar speed widget, two-dot status enhancement, desired hover panel | Composite screenshot is not original source-code evidence; no verified exact pixel dimensions |
| https://www.trisunsoft.com/pc-freeware-recommended/net-speed-monitor.htm | Classic toolbar feature, version and author | Third-party review; old software behavior only |
| https://netspeedmonitor.freedownloadscenter.com/windows/ | Current speed, totals, connections table, daily/monthly statistics | Third-party review, possible omissions |
| https://learn.microsoft.com/en-us/windows/win32/shell/taskbar-extensions | Deskband and notification area historical API | Does not promise modern taskbar support |
| https://techcommunity.microsoft.com/discussions/windows11/how-to-bring-back-the-classic-quick-launch-bar-in-windows-11/4482288 | Windows 11 classic toolbar removed | Community discussion |
| https://learn.microsoft.com/en-us/dotnet/api/system.net.networkinformation.networkinterface.getipv4statistics?view=net-10.0 | Supported adapter counter API | Not throughput-benchmark behavior |

## Observed user journeys

| ID | Surface | Entry | Purpose | Controls / states |
| --- | --- | --- | --- | --- |
| S01 | Taskbar speed panel | launch | compact up/down speed, sparkline | dot 1/2, rate units, unknown/active/zero/error |
| S02 | Hover info | hover S01 | adapter, totals, uptime | two target rows; full/error/empty |
| S03 | Settings | dot or context menu | adapter, status hosts/ports, startup/display preferences | invalid URL; save or cancel |
| S04 | Connections | context menu | list TCP/UDP endpoints | refresh/error/empty |

| ID | Flow | Path | Errors |
| --- | --- | --- | --- |
| F01 | See live traffic | S01 | no adapter, counter reset, new adapter, sleep |
| F02 | View health at glance | S01 → S02 | no probe yet, blocked ping, fail, poor quality, multi-day stability |
| F03 | Configure probes | S01 → S03 → S01 | malformed URL, bad port, rename, changes reset status |
| F04 | Inspect connections | S01 → S04 | API failure, nothing connected |
| F05 | Persistent statistics | S01 → S02 | date rollover, settings corruption, restart |

**Boundary:** independent reimplementation of observable functions, not binary disassembly or source reuse. No original appearance, branding, or taskbar extension is copied.
