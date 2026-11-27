# Starting EasyMode 6.0 from the running R281

The owner wants revisions based on this installed feature set. Use this consolidated application's `root/` as the starting point. Do not substitute the incomplete universal `5.0.0-alpha.1` toolkit based on its larger version number. Keep the older snapshots for reference.

## Preserved application

HTML, plain CSS and browser ES modules; uhttpd serves the UI, RPC requests use OpenWrt ubus/rpcd authentication. The current API identifier remains `4.1` even though the application revision is `4.2.6`; it is not the release number. The `/admin/` redirect opens normal LuCI. Login uses existing OpenWrt credentials. No passwords are embedded here.

Preserve SMS conversations/shortcodes, USSD entry point, band controls and trial workflow, SIM/APN controls, antenna and device-identity pages, diagnostics, watchdog, home Wi-Fi, upstream/repeater/AP controls, VLAN/Piso bridge controls, failover/load balancing, system-wide client allow/block, session timeout, logs, appearance and signal LEDs. Controls may remain dependent on modem and upstream capabilities; merely preserving a page does not certify every operation on other hardware.

## Client-session implementation

- `client-sessions.uc`: pure monotonic-time state transitions. `total_seconds` already includes current session time; do not add the current counter again.
- `client-sample.uc`: hostapd associations plus local bridge neighbors, DHCP names/IPs, private atomic snapshots. Do not interpret stale leases as online.
- `blaze-client-sample`: bounded execution under flock and timeout. Cron runs once per minute, independent of whether the UI is open.
- RPC `status`: adds presence, session values and `client_tracking`. Freshness expires after 90 seconds; epoch times label history while uptime measures duration.
- Frontend uses the existing 15-second status refresh. Network → Clients preserves expanded history sections when refreshing. No extra polling loop was added.
- Runtime files: `/tmp/blaze-clients.json`; `/etc/blaze/client-sessions.json` for a 30-minute checkpoint. Both contain private device records; never commit or export them publicly by default.

## Runtime prerequisites and integration

Target verified: Notion R281, OpenWrt 24.10.8. The recorded package inventory is a reference from the live installation, not a minimal dependency list or permission to install every package. Core requirements include ucode with fs/uci/ubus modules, rpcd with ucode support, uhttpd/ubus, LuCI, hostapd ubus support, UCI, ip/iw tools, cron, flock and timeout. Modem features rely on the installed sms-tool, comgt/gcom, modemband and 3ginfo-lite packages/profiles; relay mode relies on relayd and matching network/firewall integration. Client access requires nftables/fw4 integration and disabled incompatible flow offloading.

The original modem-band helper at `/usr/libexec/blaze-modemband-original` is external package code (installed modemband `20260806-r1`, Cezary Jackiewicz); it is recorded as a dependency rather than vendored. Wrappers refer to `/usr/libexec/blaze-gcom.bin` and `/usr/libexec/blaze-sms-tool.bin`, the platform binaries preserved by the existing installation. Obtain matching binaries from their packages when building an installer; never replace them with the wrapper itself. The custom modem initialization helper reads a private key from the router; that key is intentionally absent.

The current UCI configuration, service symlinks, cron jobs, package-provided modem profiles and firewall hooks are not replaced by copying `root/`. Preserve the existing router configuration during development. For a clean installer, explicitly implement and test those integration steps and provide a reviewed configuration template. Preserve executable modes in SOURCE-MANIFEST.json. Merge the supplied cron line once; keep other applications' cron jobs. Create `/etc/blaze` with private permissions, preserve any existing histories, and reload rpcd after RPC code changes.

## Checks and limits

Run `ucode tests/client-sessions.uc` from this snapshot on a compatible runtime, and syntax-check `root/www/easy/app.js`. Use fixture tests for reboot/clock/retention rather than disconnecting the user's working router. Verify browser navigation, green status, advancing counters and expandable history against authenticated status. Keep private snapshots before deployment, check for intervening edits, and publish only files matching the verified result.

The theme and client-session changes do not add React, Bootstrap, external fonts or a permanent worker. The user requests careful Codex-credit use and preservation of the installed features.

Factory-reset persistence and regenerated flashable firmware remain separate work. The old encrypted 4.2.3 installer predates these updates. The universal installer family still lacks equivalent payload/integration; see `../../INSTALLER-RECONCILIATION.md`. Do not label this source snapshot as a brick-proof or generic installer.
