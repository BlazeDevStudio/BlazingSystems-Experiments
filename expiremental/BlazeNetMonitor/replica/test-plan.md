# BlazeNetMonitor test plan

| ID | Scenario | Type | Expected | Evidence status |
| --- | --- | --- | --- | --- |
| F01-H1 | Known 200/500 byte deltas in 2 seconds | automated | 100 up/250 down B/s | Not run (no local .NET SDK) |
| F01-E1 | Counter decrease / zero duration | automated | zero, never negative/spike | Not run |
| F01-N1 | No NIC / adapter switch / laptop sleep | Windows manual | zero rate, restart baseline | Not run |
| F02-H1 | Green/yellow/orange/red probe qualities | automated | defined thresholds | Not run |
| F02-E1 | Continuous 24h crossing day / sleep-gap | automated + manual | blue only after healthy streak | Not run |
| F02-N1 | Firewall blocks ICMP but HTTPS passes | Windows manual | independent dot status | Not run |
| F03-H1 | Edit two targets and save | Windows manual | both update, streak reset | Not run |
| F03-N1 | Empty/invalid HTTPS URL | Windows manual | inline warning, no save | Not run |
| F04-H1 | View and refresh live TCP/UDP list | Windows manual | endpoint refresh | Not run |
| F05-H1 | Session/day/month rollover | automated | correct counters | Not run |
| F05-E1 | Corrupt JSON | automated | defaults loaded | Not run |
| F05-N1 | Denied LocalAppData write | Windows manual | app stays active, log debug | Not run |
| UI-01 | 100%-200% DPI, dark/light, Windows 10/11, multitaskbar | Windows manual | legible, not overlapped | Not run |

Release gate: successful Windows build, headless tests, human Win10+11 installation proof, performance and taskbar-layout smoke. Automation does not replace physical testing.
