# EasyMode 4.2.4 — system-wide device access update

Incremental source update for the existing R281 EasyMode 4.2.3 installation, deployed 8 October 2026. This folder is not a standalone firmware or a replacement for the encrypted installer.

Settings → Device access provides:
- Off, blocklist, and allowlist policies for client internet traffic.
- Per-device Allow/Block buttons, manual MAC entries, and saved offline entries.
- Coverage of routed clients arriving on the R281's local bridges: Ethernet LAN, home Wi-Fi, dedicated repeater, and local VLAN bridges.
- IPv4/IPv6 inet firewall filtering before the normal forwarding chain; router-local administration/DHCP/DNS remain reachable.
- Atomic rule replacement, validated unicast MAC addresses, deduplication, 128-entry limit, empty-allowlist rejection, and rollback if saving fails.
- No resident daemon. Boot and firewall-reload hooks restore /etc/blaze/access.json.

The feature defaults to Off. It blocks forwarding rather than Wi-Fi association, and also restricts other routed traffic from the blocked client. It cannot identify separate clients hidden behind another NAT router, stop MAC spoofing, or police traffic that is only switched and never passes through this router's IP forwarding path. Firewall flow offloading must remain disabled; applying an active policy rejects an already-enabled software offload setting. Ordinary reboot persistence is implemented; hardware factory-reset persistence is not established by this update.

## Repeater audit
The user explicitly requested separate client access rather than shared portal time. The device's saved portal_identity setting was changed from shared to separate; this removed the shared-login SNAT behavior without restarting Wi-Fi. No upstream authentication, credit purchase or anti-repeater bypass was attempted.

At approximately 21:25–21:35 PHT, the station associated successfully and received upstream DHCP. The router's own portal request returned HTTP 302 then 200 after following the redirect. One isolated downstream test client also obtained an upstream IP, but its portal request timed out. This reproduces a per-client relay/portal incompatibility, not a proven “illegal repeater” detection.

Separate-address relayd is still an IPv4 pseudo-bridge; it cannot make an ordinary three-address Wi-Fi uplink preserve every downstream MAC. A literal transparent wireless bridge requires compatible WDS/4-address support at both ends, or an Ethernet connection to the upstream network. See [OpenWrt's relayd guide](https://openwrt.org/docs/guide-user/network/wifi/relay_configuration) and [WDS guide](https://openwrt.org/docs/guide-user/network/wifi/wifiextenders/wds). The portal rejection remains unresolved in separate mode. UI wording now states this limitation and explicitly identifies shared mode as sharing login/time.

## Validation
- Native ucode validation tests: malformed/multicast MAC rejection, duplicate normalization, invalid scope rejection, empty allowlist rejection, off/allow/deny rendering.
- Isolated network namespaces on the R281: simulated Ethernet client baseline, deny → blocked forwarding, local router reachability retained, unlisted deny client allowed, allowlisted client allowed, unlisted allow client blocked, off restored connectivity.
- These tests caught and fixed stale nftables set membership on policy replacement; the table is now replaced in one nftables transaction.
- JavaScript syntax, ucode compilation, shell syntax and fw4 check passed.
- Browser login, Settings → Device access, saving a blocklist with an unused test MAC, Allow button, and returning to Off verified against the saved JSON and running nftables state.
- Every deployed changed source file matched its local copy at deployment.
- Cellular connectivity remained available; no router reboot/flash or user device block was left enabled.
- Physical wired clients, authenticated paid captive sessions, and post-reboot/reset behavior were not tested.

## Files and deployment context
The root directory contains only changed/new files, to layer over the existing 4.2.3 source; retain the rest of that release. The live device additionally has:
- enabled /etc/init.d/blaze-access;
- firewall include blaze_access: type script, path /usr/libexec/blaze-access-apply, fw4_compatible 1;
- initial private access.json with Off and an empty list;
- blaze.repeater.portal_identity=separate.

Current private backups were retained on the user's laptop. No credentials, identities, live access lists, private logs, or firmware images are included. New settings are not baked into the older reset-defaults firmware.

