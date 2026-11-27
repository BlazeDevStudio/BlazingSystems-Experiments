# Legacy ASApp behavior map -> BlazePisonet SoftTimer

This document records the clean-room behavior mapping used for SoftTimer. It is intentionally about observable behavior and architecture, not proprietary source-code copying.

| Legacy behavior observed | SoftTimer treatment |
|---|---|
| Hard-coded/special COM1 expectation | Replaced by Device Manager enumeration and device identity binding |
| Direct PC Timer through RS-232 modem-control signals | Implemented as Internal PC Timer provider |
| External Allan/Piso timer-board monitoring | Implemented as External Timer Board provider |
| DSR/DTR/RTS-oriented hardware path | Generalized to configurable modem-control signals plus DTR/RTS outputs |
| Low-level keyboard hook | Implemented while customer lock screen is active |
| `BlockInput`-style customer restriction | Replaced by multi-monitor kiosk overlays + keyboard filtering to keep recovery safer |
| Ctrl+Alt+Delete -> return -> Home admin path | Preserved conceptually; Windows retains SAS ownership and Home is accepted only in a short post-secure-screen window |
| Disable Task Manager | Optional reversible HKCU policy while locked |
| Disable Registry Editor | Optional reversible HKCU policy while locked |
| Disable logoff | Optional reversible HKCU policy while locked |
| Disable shutdown/restart UI | Optional reversible Explorer policy while locked |
| Process/application blocking | Configurable process-name guard while locked |
| Website blocking | Managed hosts block with explicit SoftTimer begin/end markers |
| Secure application directory | Replaced by Program Files installation + protected ProgramData state |
| Startup registration | Clearly named scheduled task |
| Helper/service + vhost watchdog chain | Clearly named SoftTimer watchdog plus recovery scheduled task |
| Remaining-time temp text files | Replaced by atomic JSON state replacement + backup |
| Shared-folder member database | Replaced by local hashed standalone members or BlazePwifi-authoritative central members with revisioned metadata sync and idempotent balance events |
| Member login/logout and banked time | Implemented locally |
| Member time transfer | Implemented in timer engine and management UI |
| Warning sound | Implemented with configurable threshold, optional WAV path and fallback Windows warning sound |
| Promo rate UI | Pricing is currently seconds-per-pulse; promotion/rate engine is planned after the first hardware-stable line |
| Coin counter | Durable accepted-pulse counter |
| Lock-screen wallpaper / shop / PC name / banners | Implemented with Blaze-themed UI and optional wallpaper |
| Auto shutdown at zero | Optional |
| Idle-user shutdown | Optional |
| Unusual/repetitive input shutdown | Basic high-volume keyboard trigger included; richer mouse-pattern analysis remains planned |
| Three scheduled notifications | Implemented with three editable windows, selected days, overnight handling, messages, lock and shutdown actions |
| Hidden/obfuscated registry configuration | Not copied; configuration is explicit and auditable |
| Universal default admin password | Explicitly rejected; operator sets password |
| Antivirus exclusion instructions | Not required by design |
| Fake Microsoft task name | Explicitly rejected; tasks are named BlazePisonet SoftTimer |

## Release philosophy

The goal is behavioral parity where it is useful, but safer implementation where the legacy technique is fragile or misleading. SoftTimer should never require weakening antivirus, disguising persistence, or renaming a USB adapter to COM1.
