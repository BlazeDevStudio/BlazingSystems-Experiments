# BlazeSystems R281 Easy Mode

**4.2.3 experiment — native OpenWrt management on a Notion R281.** Tested on OpenWrt 24.10.8, Linux 6.6.144. This directory is a source revision of the existing installation, not a standalone firmware image or factory recovery kit.

## Separate repeater Wi-Fi

Open **Wi-Fi → Wi-Fi as internet**, scan and select the upstream, choose **Transparent IPv4 repeater**, then **Dedicated repeater Wi-Fi only**. Enter a name (default `BlazeSystems-Repeater`) and enable **Captive / Piso network** for an upstream login portal. Apply the connection.

Use **Wi-Fi → Repeater AP** to choose its name, radio, enable switch, and inherited home password, custom WPA2 password or open access. A blank custom password retains the stored custom key. These settings survive upstream reselection. Its clients receive addresses, gateway and DNS from upstream DHCP. Existing home Wi-Fi and Ethernet LAN retain their cellular/Ethernet routing and local DHCP. Upstream DNS is excluded from the home resolver. The dedicated repeater is excluded from home load balancing.

Captive mode accepts association plus DHCP without requiring public internet access. It does not repeatedly tear down a valid captive connection. A scoped IPv4 rule accommodates portal replies arriving with TTL 1. **Shared upstream login** compatibility additionally translates repeated clients to the station address, for portals that reject their relayed identities. Clients still receive upstream DHCP addresses, but the portal sees one shared connection/login. Choose separate identity only on an upstream that accepts it. This is not an authentication bypass or a full MAC bridge. The rule is removed when captive relay mode is disabled.

This uses OpenWrt relayd, an IPv4 pseudo-bridge. It is not a full Ethernet/MAC or IPv6 bridge. Address-preserving cellular fallback for repeated clients is not provided: use the existing home SSID/LAN for cellular. Whole-network repeater mode remains available, with an optional separate routed backup SSID. Overlapping home/upstream subnets are rejected in dedicated mode.

## Signal LEDs

**Settings → Signal LEDs** offers the modem default, CSQ/RSSI/RSRP/RSRQ/SINR thresholds, and timed or permanent asynchronous blinking. Three different kernel timer rhythms provide the dance effect without a fast AP polling loop. Timed mode restores the captured LED state and resumes the original modem LED service locally, even if the browser closes. Metric updates reuse the existing radio cache; stale/missing readings show zero LEDs. The defaults remain native modem control.

## Other changes

- Asynchronous, bounded Wi-Fi scans keep RPC responsive. Scan results recognize open, WPA, WPA2, WPA3 and mixed personal security; unsupported enterprise/WEP entries are identified.
- Late modem responses no longer overwrite a different tab after navigation.
- SMS inbox and send actions use the installed modem tools. Philippine `09…` numbers normalize to `639…` when the modem reports a Philippine operator; short codes remain unchanged.
- Band selection is validated against native modem capabilities. A speed/CA trial checkpoints the selection, reconnects, measures actual downloads, and restores the prior selection on a failed or slower trial. The tower still controls aggregation scheduling.
- Router-side ping, DNS/HTTPS diagnostics and download tests finish with a result or bounded failure. Only one test can run at a time.
- Failover/load balancing settings expose actual eligible sources. Captive Wi-Fi is excluded from internet balancing. Device-bound recovery probes have their own routes so an outage policy cannot block the probe itself.
- Bounded RAM-only probe history records brief failures and available memory; maximum approximately 128 KiB, without identifiers or flash writes.
- Light/dark December-blue themes, session settings, logs, APN, antennas, home Wi-Fi and port controls retain the newer live UI baseline.

## Evidence and limits

See [the audit](docs/AUDIT.md), [change history](CHANGELOG.md), and [implementation plan](docs/PLAN.md).

The owner verified physical-client DHCP but reported an unreachable portal. A bridge test client reproduced it on the newer upstream. Shared-login compatibility then passed HTTP 302 → 200, DNS, and eight CSS/JavaScript asset downloads. Separate identity reproduced the timeout. The actual repeater AP Save button completed and settings survived browser reload. Open/custom/inherited passwords, invalid inputs and upstream isolation passed UCI fixture tests. Router and home management routes remained on cellular/LAN. The browser's actual Apply control was exercised separately. The corrected path still needs a fresh physical-client portal login and sustained authenticated download test; no paid login or purchase was attempted.

Cellular outages are **not declared solved**. The latest capture contains 646 raw probe samples across 5.67 hours, including 15 failures earlier in the window; the most recent 134.7 minutes had no failed probe. This is sample-based evidence, not a guarantee of uninterrupted traffic. Captured outages had 25–30 MiB available RAM and registered LTE-A. A probe-routing flaw was corrected; longer observation is needed to separate subsequent radio/data-path failures from routing failures. Multi-uplink balancing was configured/read back, but simultaneous throughput with two working internet uplinks has not been measured. USSD returned no modem response with both the installed tool and an independent 40-second serial read. Sending currently supports basic Latin text within one SMS, not Unicode/multipart messages.

A private reset-default candidate image was built from the current installation. All 2,286 filesystem paths, hashes, owners, modes, symlinks and Linux device numbers passed an independent reader; factory structure was checked against byte-identical reconstruction of the original image; the device accepted sysupgrade -T. It has not been flashed or reset-tested. The native upgrade kit now includes fresh primary/backup network-key retrieval, an already-unlocked check, and guarded one-attempt unlock logic. The original vendor/Telnet migration flow remains a separate kit. Signal LED controls are implemented and tested. Actual new-image boot and reset testing remain pending the wired connection. Do not use these files as a sysupgrade archive or assert that a reset preserves them. The project stays in Experiments until the owner declares success.

## Source layout and dependencies

`root/` mirrors deployed paths. This overlay depends on the existing R281 board configuration, native modem/NCM support, LuCI, rpcd ucode/ACL support, ucode UCI/ubus/fs modules, iwinfo, curl, jsonfilter, jshn, flock and timeout. Repeater/multipath work additionally needs `relayd`, `luci-proto-relay`, `ip-full` and dependencies from the matching signed OpenWrt feed.

Existing modem dependencies are deliberately not bundled: `/usr/libexec/blaze-gcom.bin`, `/usr/libexec/blaze-sms-tool.bin`, `/usr/libexec/blaze-modemband-original`, 3ginfo-lite and the installed modem profiles. Do not replace these with arbitrary firmware binaries. The wrappers serialize access to these tools.

No device config, passwords, password hashes, unlock keys, SMS history, packet captures, private backups, firmware binaries or flasher archives are published here. Test credentials are read from the environment. Live tests require the owner’s authorization and can briefly interrupt Wi-Fi/data; preserve a private backup first. `tests/probe-route.sh` uses a temporary network namespace without changing the live router routes.

This source snapshot is intended for review and further packaging on this tested installation; it is not a generic installer for every R281 variant.
