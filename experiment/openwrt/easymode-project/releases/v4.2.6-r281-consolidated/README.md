# EasyMode 4.2.6 — consolidated R281 application source

**Use this folder as the starting point for EasyMode 6.0 development.** It consolidates the running R281 application instead of requiring the earlier 4.2.3, 4.2.4 and 4.2.5 overlays. Version numbers identify revisions; they do not rank feature completeness. The installed application remains the functional reference.

`root/` contains the current HTML/CSS/JavaScript interface, authenticated RPC backend, application helpers and application service definitions. The source was copied from the live router, then the client-session feature was added and deployed. Current files were compared again with the router on 2026-10-10. See `SOURCE-MANIFEST.json` and `SHA256SUMS`.

This is an application development snapshot, not a flashable firmware image or a standalone installer for an unconfigured router. It excludes credentials, UCI network/Wi-Fi configuration, SMS, device history, calibration data, binaries supplied by external packages, and the separate BlazePWifi application. Existing package and service integration requirements are documented in `HANDOFF-6.0.md` and `PACKAGES-REFERENCE.txt`.

## Added client presence and sessions

- **At a glance → Your devices:** green Online marker and current session counter, with name, IP and MAC.
- **Network → Clients:** current session, accumulated observed time, last observation and expandable completed-session history.
- Samples Wi-Fi association and local bridge neighbor reachability once per minute. No traffic capture, browsing history, active scan, or new resident daemon.
- Retains up to 128 devices and 8 completed sessions per device. Totals include older completed sessions while the device record remains retained.
- Current state is in RAM; a private checkpoint is written every 30 minutes. Sudden power loss may lose the latest interval. Reboots and monitoring gaps are not credited as online time.
- Idle wired clients have a three-minute recent-observation allowance. Missing evidence is shown as **Not recently seen**. Failed/stale tracking is shown as **Unknown**. A DHCP lease alone is not an online signal.
- Times begin when tracking starts. They are approximate local presence times, not internet-access, captive-portal credit, or exact historical association durations. MAC randomization appears as another device. Long-inactive devices can be evicted at the device limit.

## Verification

`tests/client-sessions.uc` checks first observation, accumulation, disconnect/reconnect, wall-clock adjustment, reboot, monitoring gaps, wired expiry and retention limits. It passed on the R281's ucode runtime. The backend compiled, JavaScript syntax passed, all deployed files matched after readback, and authenticated status returned fresh observations. The initial collector sample took approximately 0.2 seconds with less than 1 KB of state for three known clients. On 2026-10-10, the running tracker had fresh observations and eight completed-session records.

The browser dashboard displayed two online devices and current counters. Network history was checked against the same authenticated data. No router/network reboot was needed. This feature was not burned into firmware; factory-reset persistence is not established by this update.

## Layout

| Location | Purpose |
|---|---|
| `root/www/` | Current lightweight UI and advanced-mode redirect |
| `root/usr/share/rpcd/` | EasyMode RPC object and access declaration |
| `root/usr/share/blaze/` | Application logic, including session accounting |
| `root/usr/libexec/` | Job, modem, networking and collection wrappers |
| `root/etc/init.d/` | Existing EasyMode health and device-access services |
| `integration/client-sessions.cron` | One line to merge into root crontab; do not overwrite other jobs |
| `tests/` | Session accounting tests |
| `HANDOFF-6.0.md` | Development handoff, dependencies and preserved behavior |

The CoreUI/Metis-inspired theme remains original plain CSS with no React or Bootstrap runtime; attribution is retained in `THEME-NOTICES.md`. Existing upstream package code retains its own licensing and is not relicensed by this snapshot.
