# R281 EasyMode application update

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
- Archive payload and hashes verified. Latest combined archive --check and --apply tested on the R281. An initial compile-check failure restored previous files before the corrected installer passed.
- A phone later associated: upstream DHCP and learned return routes worked; its DNS/HTTP requests were observed leaving the upstream station but no IP replies returned. Gateway ARP replies and router-originated HTTP worked. This isolates the failure beyond the local forwarding path, but does not establish the upstream policy. Separate-identity portal access remains **UNRESOLVED**; no shared-login substitution was applied.
- New AP radio reload/timeout rollback, reboot/reset persistence and long-term cellular stability remain **NOT HARDWARE VERIFIED**.

Build with `python traffic/tools/build-r281-update.py`. Traffic Intelligence packages are rebuilt separately with `python traffic/tools/build.py`; they preserve the existing management application.

## 2026-10-14: Advanced site blocker

Settings → Site blocker adds default deny-list / allow-only DNS policies and up to 32 per-MAC overrides, with subdomain matching. A device override replaces the default. Filtering is OFF on first installation. No browsing history is retained. Existing device internet-access control remains separate.

Dependencies must already be installed: `ucode-mod-socket` and the **exact running kernel's** `kmod-nft-bridge` from matching official OpenWrt feeds. This small application archive does not include dependency packages or firmware. It preserves existing site policies. Use --check before --apply.

Actual R281 checks: 14 policy/parser assertions; 7 routed UDP/TCP DNS enforcement checks; isolated on-device software bridge baseline and blocked DNS tests for IPv4 and IPv6. Browser add/edit/save/remove controls checked. Physical phone AP traffic, hardware-switch-only forwarding, reboot and factory reset are NOT VERIFIED. This overlay installation is NOT factory-reset persistent.

Limits: ordinary port-53 DNS only. DoH/DoT, VPNs, cached/direct IP connections, hardwired switch bypass and MAC changes can evade filtering. Allow-only DNS is not an allow-only internet firewall. CDN/login dependencies may need extra domains. IPv6 interception fails closed if no management IPv6 address exists. Existing offloading must be explicitly disabled by the administrator; the installer does not change it. Removing/reordering device overrides can temporarily reject old DNS flows until conntrack expires; cross-device old mappings fail closed. Bridge tests use isolated virtual clients on the physical R281, not a claim of full physical AP testing.

To remove filtering immediately: disable it in Settings, or stop `/etc/init.d/blaze-sites`. For application rollback, stop/disable that service, restore the printed private backup, then restart rpcd and blaze-health. Do not publish backups.


## 2026-10-14: Login permissions and Management settings

The update installer now restores a normal umask before copying web assets, so `/www/easy/app.js` remains readable by uhttpd (0644). A restrictive umask had left it 0600 and caused HTTP 403, which stopped EasyMode JavaScript and made login appear broken. Management settings is the last Settings item and links to LuCI's account page to change the shared OpenWrt root password. That password is used by EasyMode, LuCI and SSH. A separately authenticated vendor portal is outside this root-account change.

## 2026-10-15: SMS sync, unread threads, and backup

Messages automatically refresh the modem inbox every 30 seconds while the EasyMode Messages screen is visible. Incoming messages not yet opened are highlighted and carry an unread count. Thread read markers and contact names are stored in that browser's local storage. SMS settings can export or restore an EasyMode JSON backup containing contacts and available inbox/sent messages; restored messages are local snapshots and are never re-sent. Backups contain private message text and phone numbers. This update does not delete messages from SIM/modem storage.

The browser backup is limited to 1,000 incoming and 1,000 sent messages and 500 contacts. Import validates the JSON and stores the restored history only in the browser. It cannot restore data to a replacement SIM or modem; use the modem's own storage for that. Automatic refresh queries the configured ME or SM storage and does not guarantee carrier delivery/read receipts.

No voice call or SMS test was performed while building this archive. The router was not reachable from the development laptop during this update. The implementation and archive are therefore not live-installed or hardware-verified.
