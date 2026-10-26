# EasyMode 7.0 validation record

## 2026-10-26 — 7.0.2 attribution and small-screen update
- The shared backend recognizes additional app-specific domains and uses a neutral Meta-services label for shared `fbcdn` traffic. DNS observations without byte evidence are shown separately; no website/app traffic is fabricated from a hostname alone.
- On the R281, 39 accounting assertions passed before installation. The Cellular edition reports 7.0.2-1 for both core and edition packages, its service is running, and `wwan_4` remained up. The other five editions were rebuilt and checked offline, not installed on their target hardware.
- The live 390 px Websites and Apps screens show named-traffic coverage, the latest router DNS lookup, and DNS-only rows. The observed named coverage was 1% of 3.83 GB; encrypted DNS and cached client lookups limit attribution. A ChatGPT DNS-only row and a Facebook estimated-traffic row appeared in the Apps view.
- OpenWrt reported a pre-existing update-guard permission warning and a package post-install `Command failed: Not found` message. Services subsequently ran, but those warnings and full restore/rollback remain open validation items.

## 2026-10-26 — 7.0.1 navigation and installer update
- Shared Traffic UI now uses a native view picker at 390 px; the R281 browser switched Overview to Devices and rendered live device data. Wider navigation remains available.
- All six edition archives were rebuilt with package SHA-256 files and checked for package contents and checksums. The Cellular edition was installed on the R281; both packages report 7.0.1-1, the service is running and the cellular default route stayed active. The other five editions are build-verified only.
- The installer now requires exactly one edition package in its folder, verifies both package hashes, and backs up settings. During the live install, OpenWrt's backup reported a permission warning for the pre-existing `/etc/init.d/blazepwifi-update-guard`; package installation continued and the backup archive was created. That unrelated guard and rollback restoration have not been repaired or tested here.
- The old `/traffic/` document remained in browser cache after the package update; the EasyMode link uses `/traffic/?v=7.0.1-mobile2` to request the latest mobile page and assets.

## 2026-10-19 R281 log audit and EasyMode v10 application profile
- Read-only capture reviewed current-boot `logread`, `dmesg`, cellular and Wi-Fi interface status, address/route state, health history, services, processes, memory and storage. The R281 was online via SIM at capture: 30,252 KiB MemAvailable and 90,624 KiB overlay free. No modem USB reset/error or memory exhaustion appeared in the captured kernel log.
- Health history recorded 51 failed probe samples during 16h37 uptime, including a six-sample burst, and two recovery attempts. Current-boot logs did not establish a cell-tower fault or correlate a rotating SIM address with the burst. Historical DHCP renewal losses reacquired the same private address after a brief lease gap.
- Fixed the route recovery path so an unavailable source no longer leaves a high-priority unreachable default route; automatic SIM recovery no longer escalates to a radio/RF reset. Added per-boot SIM IPv4 change count/time for future correlation.
- Four route/recovery regression assertions passed on the R281 using the candidate script copied only to `/tmp`; shell syntax passed. Exact-target v10 installer preflight passed checksum, shell and Ucode validation. Application update was installed on notion,r281 / OpenWrt 24.10.8 with private rollback archive. Version file reports 10.0.0; homepage displays v10.0.0; app/style HTTP assets return 200; health and SMS archive services are running; SIM ping passed immediately after deployment.
- No reboot, network/Wi-Fi config write, radio reset, firmware flash, or SMS send. The archive is an application update, not firmware. Extended stability observation, factory reset, and other hardware remain NOT VERIFIED.

## 2026-10-10 checkpoint
- 17 pure accounting/attribution assertions PASS on the R281 OpenWrt 24.10.8 ucode runtime, using only `/tmp/emti-test` files.
- 5 executable Node tests PASS: aggregation, date filters, billing boundaries, escaping/CSV injection, unavailable values.
- Collector, DNS controller and rpcd plugin compile on that runtime.
- Isolated read-only collector detected 2 deduplicated upstream devices, 4 wireless interfaces and 2 observed clients. No installed application, network configuration or firmware changed. Initial CPU conversion defect was found and corrected.
- Generated observer rules pass `nft --check` on R281; rules were NOT installed there.
- Deterministic package builder produced core plus six edition IPKs and six offline archives. These await clean-install validation.
- GitHub Linux validation environment established successfully at de0189ddd58e609b525c03eb0b3aa46f982a87b4.

## Pending acceptance evidence
GitHub VM installation/upgrade/uninstall; private RPC/CSRF tests; real forwarded counters; DNS lifecycle; corruption recovery; BIOS/UEFI boot; UI mobile/live/error behavior; uploaded checksum verification. Physical hardware deployment remains NOT HARDWARE VERIFIED. No v7 release is published at this checkpoint.


## 2026-10-12 physical preview checkpoint (supersedes earlier deployment status)
- R281 OpenWrt 24.10.8: real Core/Cellular IPK installation succeeded after fixing missing tar directory entries. Management UI retained; monitoring /traffic/ returns its assets with correct MIME types.
- Real HTTP API: unauthenticated snapshot denied; administrator authentication returns fresh data. Service enabled and running; no current collector error.
- Real browser: signed in; Overview, WiFi, Internet Data, Devices, Websites, Apps, Reports and Settings render; no console errors observed. Destructive settings actions were not exercised on the user's live network.
- Real forwarded per-device counters and domain estimates populated. Laptop counters increased during actual traffic. Controlled 1 MiB test endpoint returned HTTP 403; a smaller OpenWrt download succeeded, but background traffic prevents exact-byte attribution validation. Do not describe this as an isolated throughput accuracy test.
- 29 accounting assertions pass in R281 ucode; modified collector compiles; JS syntax check passes.
- Physical reboot, factory reset, exact byte accuracy, exhaustive IPv6/VLAN/offload testing and long-term memory stability are still NOT VERIFIED.
- GitHub run 38079512294: package/image builds pass; VM SSH connection fails before integration tests. Production release gate remains failed. No v7 release is published.


## 2026-10-13 activity timestamps
- 34 ucode assertions PASS including separate per-device DNS timestamps and opt-out cleanup; 8 Node tests PASS including ten-row expansion, identity isolation, timestamp ordering and stale/recent classification.
- Installed backend/UI on R281, collector compile passes, live API returns fresh activity for two identities with no collector error.
- Timestamps reflect sample observation time; not precise request time. Historical per-device timestamps are not reconstructed.

- Live browser verification: site table showed 10 rows, Show all expanded to 132 retained rows, Show 10 restored 10. Per-device page displayed 7 identity-specific timestamped domains. Apps displayed timestamp columns and 3 rows. No browser console errors. Browser cache version fix verified.

## 2026-10-13 WiFi management / reconnection
- R281 isolated UCI: 13 SSID assertions PASS. Live validated RPC rejects WAN and unconfigured Piso binding; wireless/network/blaze hashes remain unchanged. Existing AP readiness check PASS.
- Two routing scenarios PASS against actual health functions with route writes mocked: retain addressed uplink if probes fail; prefer verified wired backup. Backend compile, shell and browser JavaScript syntax checks PASS.
- Live browser verifies existing SSID list, add/edit forms, disabled unavailable binding, repeater portal link and Traffic WiFi management link. No new live SSID or radio reload test.
- Physical cellular probes pass after application update. Repeater phone obtains upstream address and return route; its DNS/HTTP packets leave upstream but no IP replies return. Router-originated portal request returns HTTP 302. Separate portal behavior remains unresolved; no shared-login change made.
- Package builder produces 13 updated traffic artifacts; narrow R281 management archive separately verified for content, modes, checksums and installer check-only compatibility. No archive apply/rollback, reboot, factory reset or long-term outage test claimed.

## 2026-10-14 — R281 site blocker installed

User priority changed from captive portal investigation to global/per-device site filtering, including transparent AP paths. Implemented in `releases/v4.2.6-r281-consolidated/root`: `sites.uc`, `sites-daemon.uc`, `sites-firewall.uc`, `sites-apply.uc`, init/helpers/fw4 include, authenticated blaze RPC and Settings → Site blocker UI. No alternate management implementation.

Configuration `/etc/blaze/sites.json`, default OFF; 32 device overrides, 512 domain entries total, 128 per policy. Domain suffix matching, deny/allow/off, overrides replace default. Bounded asynchronous ucode UDP/TCP resolver forwards to existing dnsmasq; bridge broute + explicit local DNAT intercept visible port-53 requests by client MAC. UDP listeners bind DNAT addresses to preserve reverse NAT across bridges. Rules reject stale mappings to other device profiles. Existing offloading requires explicit administrator disablement. No TLS interception, hidden telemetry or browsing-history log. Dependencies installed from matching official feeds: ucode-mod-socket and exact-kernel kmod-nft-bridge.

Verified on physical notion,r281 / OpenWrt 24.10.8: 14 parser/policy tests, 7 routed enforcement tests (UDP/TCP, block, allow-only, override exemption), software-bridge network-namespace baseline and refusal for IPv4/IPv6, service reload, boot-service enablement, unauthenticated RPC rejection (-32002 Access denied), browser add/edit/save/remove. IPv6 fixture needed a static neighbor because its isolated test bridge has no fw4 LAN zone; no production firewall neighbor permissions changed. Active one-override daemon measured 1508 KiB RSS. About 29 MiB available system RAM at sample. Package --check and --apply succeeded. An initial compile validation failure restored previous files; corrected module validation then applied successfully. No reboot or Wi-Fi reload. All temporary rules/namespaces removed; filtering left OFF with no domains/overrides.

Artifact: `dist-v7/EasyMode-R281-4.2.6-SSID-Sites-Recovery-20261014.tar.gz` and SHA256 sidecar. Build: `python traffic/tools/build-r281-update.py`. Includes prior SSID/recovery update and site subsystem; dependency packages must be installed first. This is an application archive, not flashable firmware. Installation preserves current policy and creates private rollback archive. No credentials/private logs included.

Limits: DNS-only; encrypted DNS/VPN/cache/direct IP/hardware switched paths bypass coverage. Physical phone AP path, TCP over isolated bridge, reboot and factory-reset survival NOT VERIFIED. Overlay is NOT reset-proof. Per-device policy removal can temporarily refuse old DNS conntrack mappings rather than apply another device's rule. Repeater captive-portal failure remains unresolved and separate. Previous four-address diagnostic did not establish upstream WDS support because local iw lacks those commands. No credit-sharing bypass implemented.

Repository branch `easymode-v7-production`; last published checkpoint before this change `020aaf6e5fdbad53a1aee565c8fed3fdbbb12e4b`. This checkpoint's commit is discoverable with `git log -1 --grep="Add R281 DNS site policies"`. Next exact work: physical AP client coverage and any stronger encrypted-DNS policy require separate validation; resume repeater investigation only after this user's prioritized feature handover. No v7 production release or new firmware claimed.
