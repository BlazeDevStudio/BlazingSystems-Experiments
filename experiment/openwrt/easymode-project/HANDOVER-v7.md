# EasyMode 7.0 continuation log

## Checkpoint 1 — discovery (2026-10-10)
- Authoritative public repository: BlazingSystems/BlazingSystems-Experiments.
- Development branch: easymode-v7-production; base fd351ace52f465ce9689961734178af145cd3447.
- Workspace: C:/Users/Blaze/Documents/Codex/EasyMode-v7.
- Current working router application: releases/v4.2.6-r281-consolidated/root. Preserve it and its management functions. The 5.0.0-alpha.1 universal toolkit is incomplete scaffolding, not a replacement for that application.
- Six editions exist: generic, ap, router, cellular, switch, pc.
- No existing EasyMode CI image builder. Windows host has neither WSL nor Docker. GitHub connector provides Git object writes, but no release upload or workflow dispatch; local Git credentials are unavailable. Build/release workflow on a development branch is the intended Linux execution path, subject to actual permission verification.
- No physical flashing is authorized for this assignment. R281 is a community OpenWrt 24.10.8 build; marketing name alone does not establish compatibility with official ImageBuilder profiles. PC x86/64 is the initial official image target; virtual boot tests must precede publication.

## Architecture decisions
- One plain JavaScript dashboard, one ucode collector/accounting library and authenticated rpcd API; no React, Node or Python dependency on routers.
- WAN interface counters are deduplicated by L3 device. WiFi counters measure link activity separately. AP/switch editions cannot infer invisible upstream usage.
- Optional bounded nftables flow counters operate in an isolated observer table without changing verdicts, NAT or acceleration. Detailed accounting is unavailable when forwarding offload prevents measurement. Existing nlbwmon can provide a separate device-accounting adapter; never add its totals to WAN totals.
- DNS observations are disabled by default. Domain matches are observations, never proof of a visit; unique recent flow associations may be estimated, ambiguous/shared addresses remain unknown. No URLs, content or TLS interception.
- Private bounded RAM state, batched persistent checkpoints, explicit retention/deletion, no telemetry. Capability limitations are part of the API.

## Current status
Discovery complete. Implementation, executable tests, packages, firmware and release remain pending. No production readiness claim.

## Next exact action
Implement pure accounting and attribution tests, collector, supervised service and admin RPC; then build the shared dashboard and edition packages. Establish CI execution early. Record actual test and build results below.

## Checkpoint 2 — implementation and package construction
- Shared source is in traffic/root; no React/Node/Python runtime on the router. Root and all six edition manifests now identify v7.
- Implemented WAN/sysfs collection, wireless/client observation, sampled nft flow accounting, bounded private history, opt-in dnsmasq observation, local service inference, rpcd ACL API and eight-view dashboard. Existing installed management is preserved with one navigation link added only during installation.
- Built 13 IPK/archive artifacts locally in dist-v7. These are validation candidates, not production releases.
- Actual executed results are in traffic/TEST-REPORT.md. No v7 software was installed on the physical router; isolated tests only.
- Linux CI bootstrap passed. Next: push implementation, run full ImageBuilder/QEMU pipeline, resolve failures, then publish only after acceptance review.

## Checkpoint 3 - CI builds and integration hardening
- Implementation pushed at dea8a1f2e491bc46919ae8630310b2f2096d69b5; subsequent CI fixes at b02c5be3bed601446b7ab21bb7d07b910f313173 and 885d8b28ad3e1d8b20798c85417e85e97014720d.
- Official pinned ImageBuilder successfully generated BIOS and UEFI x86/64 images. Full integration gate is still pending, so no tag/release exists.
- Test harness corrected for OpenWrt's trailing fwtool certificate record; x86 generic does not contain a board metadata record because SUPPORTED_DEVICES is empty in the official recipe. This is not manufacturer-signed firmware.
- Added real VM browser tests and controlled DNS/forwarding attribution tests. Changed browser module extension to .js for uhttpd MIME compatibility.
- Added bounded five-minute WAN rollups, all-time aggregate counters, explicit unavailable device values, DHCP identity-reuse protection, structural state validation and unknown WAN attribution.
- Next: complete BIOS/UEFI and package integration checks; document exact results before publication. Physical R281 remains unchanged.


## Checkpoint 4 - physical R281 preview delivered (2026-10-12)
- Supersedes the earlier statements that the R281 is unchanged: core and Cellular v7.0.0-1 IPKs are installed on the physical R281, OpenWrt 24.10.8. URL: http://192.168.1.1/traffic/. Original management remains at /. No firmware flash or reboot performed.
- IPK tar creation lacked directory entries. Real opkg installation exposed missing parent directories; fixed the builder and successfully reinstalled. Never use the earlier package artifacts.
- Current device configuration has aggregate, detailed flow and DNS collection enabled, interval 30 seconds, retention 31 days, entity limit 64. Detailed/DNS options were already enabled when this continuation connected; preserve the administrator's choices.
- Verified fresh live WAN/device counters, bounded DNS observations, actual nft JSON parsing, private authenticated RPC and denial without authentication. All eight views render on the actual router; browser console reported no errors. Live counters grow during real laptop traffic; concurrent usage prevents a byte-exact isolated transfer assertion.
- Applied hardening to the physical router: bounded DNS bindings, bounded domain client identities, avoid advancing domain timestamps for zero-byte flows, disclose saturated flow counters. No network, DNS, firewall service restart required for this file update.
- 29 accounting/attribution assertions pass on real R281 ucode; collector compiles. Available RAM observed around 22-27 MB; no current collector error. This is a sample, not a memory-leak or long-term stability certification.
- Private router backups and observations remain outside Git under C:/Users/Blaze/Documents/Codex/2026-09-29/con/outputs/R281-v7-preview-20261011-033222. Never publish that folder.
- Source branch: easymode-v7-production. Last remote before this checkpoint: 23d52a7d26f13587d0cba4e36a6050271799eb89.
- Release remains blocked: latest CI 38079512294 built x86 BIOS/UEFI images but its VM SSH setup failed before integration assertions. Improved failure reporting; actual root cause still needs console evidence. No v7.0.0 release/tag published; reset-proof firmware and physical reboot tests remain unverified.
- Next exact action: inspect the next CI VM console diagnostics, resolve virtual networking/SSH setup, complete installation/upgrade/security/firmware tests, then publish verified assets. Keep on-router work incremental and resource-conscious.


## Checkpoint 5 - timestamped site activity (2026-10-13)
- Added bounded per-network-identity domain activity (at most twice configured device capacity), separate DNS/estimated-flow timestamps, local-time UI formatting and recent observation labels. Resolve DNS identity at observation time; do not map retained IP history to a future DHCP owner.
- Site/app lists and per-device associated domains default to the ten most recent rows, with Show all / Show 10. Search and sorting happen before limiting. Expansion persists across refresh and resets on navigation.
- Timestamps are approximate collector observation times, not packet timestamps or proof of an open page. Latest retained activity is independent of the traffic usage-period filter. Per-device timestamps begin with this update; no invented historical backfill.
- Source paths: traffic/root/usr/share/easymode-traffic/{accounting,collect}.uc and traffic/root/www/traffic/{app,model}.js, index.html. Updated browser asset version to avoid stale cached modules.
- Deployed to physical R281 without reboot; private pre-update archive beside previous backups. 34 ucode accounting assertions and 8 Node model tests PASS; collector compiles. Live API has fresh per-device DNS activity, two identities, empty error log.
- Packages rebuilt for all six editions. Full firmware release still pending existing VM integration blocker; this change does not claim reset-proof installation.

- Live browser verification: site table showed 10 rows, Show all expanded to 132 retained rows, Show 10 restored 10. Per-device page displayed 7 identity-specific timestamped domains. Apps displayed timestamp columns and 3 rows. No browser console errors. Browser cache version fix verified.

## Checkpoint 6 - R281 WiFi management and recovery (2026-10-13)
- Installed on physical R281: SSID list/add/edit with LAN, dedicated repeater and configured PisoWiFi bindings. Authenticated existing blaze API validates network availability and preserves primary AP roles. New ssid.uc and ssid-check.uc use existing serialized jobs, configuration snapshots, AP readiness and 90-second browser-ack rollback.
- Preserved existing management; legacy home-WiFi batch operation now excludes custom SSIDs. Traffic WiFi view links to /?view=wifi. Repeater page includes validated upstream gateway HTTP link. No radio reload or router reboot during deployment.
- Health fixes: tolerate slower probes; retain an addressed route when all probes fail instead of blackholing internet; recheck before reconnect; progressively space repeated recovery at 5/10/20 minutes. Verified healthy backups retain priority. No APN, band or flow-offload changes.
- Tests: 13 isolated UCI checks; 2 routing scenarios using real health functions with mocked route writes; live RPC rejects WAN/unavailable Piso binding without config changes; active AP readiness succeeds; backend compiles and shell/JS syntax checks pass. Browser lists 3 existing APs, supports add/edit selection, preserves links. Actual new AP radio reload and timeout rollback NOT HARDWARE VERIFIED.
- Cellular probes working after deployment, no recovery attempts in the initial observation window. This is not long-term stability certification. Available memory sampled about 26-31 MB; no extra daemon installed.
- Repeater initially had no clients, then one phone associated. Upstream lease and learned return routes correct. Bounded packet-header inspection observed phone DNS/HTTP forwarded upstream without IP replies; ARP responses and router-originated HTTP 302 work. Failure is beyond local forwarding; exact upstream policy/return-path cause remains unknown. Separate-identity portal access unresolved. Do not enable shared login or change MAC identities to hide the issue.
- Source: releases/v4.2.6-r281-consolidated/root/{usr,www}; tests/build/docs in traffic. Build commands: python traffic/tools/build.py; python traffic/tools/build-r281-update.py. The latter makes a narrow application archive with compatibility/checksum checks and backup/rollback installer. Installer check-only path verified; apply/rollback not independently hardware exercised. It is not firmware or reset-proof.
- Private before-install backup and diagnostics: C:/Users/Blaze/Documents/Codex/2026-09-29/con/outputs/R281-Wifi-SSID-Management. Never commit that directory. Last successful remote before checkpoint: 57fa16e17ebc42f2d12368df0b2a6aedfb05ff29; this checkpoint commit is visible in Git history.
- Next exact action: resolve upstream support for separate relay clients (requires upstream configuration/access or an actual supported transparent bridge), then verify phone portal end-to-end. Observe cellular recovery across a real outage; do not claim stability from a short probe window. The broader v7 production release/VM/reset-persistence blockers above remain open.
