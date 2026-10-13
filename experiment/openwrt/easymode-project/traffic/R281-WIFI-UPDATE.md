# R281 SSID management and recovery update

For **notion,r281, OpenWrt 24.10.8, existing EasyMode 4.2.6** only. This is an application update, not firmware and not factory-reset persistent.

WiFi → SSIDs & networks lists access points and edits names, passwords and enabled state individually. New SSIDs choose LAN, dedicated WiFi repeater, or configured PisoWiFi VLAN. Unconfigured bindings are disabled. Primary network roles remain under their existing setup tabs. SSID application verifies AP startup and arms a 90-second management-access rollback. Keep EasyMode open while reconnecting after saving.

Cellular checks allow more response time, retain an addressed uplink if every probe fails, check again before recovery, and increase repeated recovery cooldown from 5 to 10 to 20 minutes. Verified backup connections retain priority. No band, APN or offload changes.

Repeater AP includes a direct upstream HTTP portal link. Automatic phone captive-portal popups are not guaranteed. Separate-identity relayd requires upstream support; this update neither shares login credits nor bypasses portal controls.

## Install or recover

Copy the archive to the router, extract it into a new directory, and run `sh install.sh --check`. Review compatibility, then run `sh install.sh --apply`. It backs up the affected installation and configuration to a private archive under `/root`, installs application files, refreshes rpcd and the health service, and preserves current configuration. It performs no firmware flash, reboot or WiFi restart. Actual later SSID saves reload WiFi.

To restore, extract the printed backup path into `/` as administrator, then restart rpcd and blaze-health. Restore from a wired LAN connection. Preserve that private backup off the router; never upload it publicly.

## Verified / unverified

- Physical R281: application deployed, hashes compared, API lists current SSIDs and rejects unavailable bindings, active AP readiness passes; no live network configuration modified by validation.
- 13 isolated UCI checks cover binding, validation and identity restrictions; two mocked routing scenarios exercise actual health functions.
- Browser: SSID add/edit controls and portal link render. Cellular checks and upstream portal respond.
- Archive payload and hashes verified. Installer dry-run tested; the archive's apply/rollback path is **not independently hardware exercised** (deployment used a backed-up direct file update).
- A phone later associated: upstream DHCP and learned return routes worked; its DNS/HTTP requests were observed leaving the upstream station but no IP replies returned. Gateway ARP replies and router-originated HTTP worked. This isolates the failure beyond the local forwarding path, but does not establish the upstream policy. Separate-identity portal access remains **UNRESOLVED**; no shared-login substitution was applied.
- New AP radio reload/timeout rollback, reboot/reset persistence and long-term cellular stability remain **NOT HARDWARE VERIFIED**.

Build with `python traffic/tools/build-r281-update.py`. Traffic Intelligence packages are rebuilt separately with `python traffic/tools/build.py`; they preserve the existing management application.
