# R281 log audit — 2026-10-19

Collected current `logread`, `dmesg`, health history, network interface state, routes, process/memory state, and cellular/Wi-Fi status over authenticated SSH. Raw diagnostics are kept on the operator workstation only and are not included in this release.

The router was on OpenWrt 24.10.8, uptime 16h37 at collection, with 30,252 KiB `MemAvailable`, 90,624 KiB overlay free, and LTE on `eth1`. The current cellular health state was online, route present, and ping probe successful. `logread` contained 998 entries; current-boot kernel logs showed no modem USB reset/error or memory exhaustion event.

Health history contains 51 failed samples across this boot, including a six-sample failure burst ending around 07:49 PHT; two reconnect attempts had occurred. The data interface was subsequently up and successful again. The available system log did not identify the underlying carrier-side cause or record a radio detach for that burst. This warrants longer monitoring; it does not prove tower fault, SIM lock, or a specific app-triggered outage.

Older outage captures show repeated cellular DHCP renewal requests with no renew reply, followed by lease expiry and immediate reacquisition of the same private IPv4 address. `netifd` then raised the dynamic interface and reloaded the firewall. This is a short DHCP transition, not evidence that the carrier rotated the address during that event. A separate earlier packet capture of renewal behavior did not establish a workaround; no static addressing or DHCP suppression was introduced.

Candidate fixes: (1) remove the stale high-priority EasyMode unreachable default route when no source has an address, allowing normal netifd routes to work as soon as a lease returns; (2) automatic SIM recovery now reconnects the data session only and never cycles RF/changes cell selection. Cellular IP changes are counted per boot in health status so future outages can be correlated without recording browsing data or full IP-change history.

The v10 application was installed on the verified R281 after a private rollback archive was created. `/etc/blaze/easymode-version` reports `10.0.0`; the root page identifies v10.0.0; JavaScript and CSS assets return HTTP 200; health and SMS-archive services are running; SIM ping passed immediately after installation. The SIM address and route remained available. No reboot, radio reset, network/Wi-Fi config edit, or firmware flash occurred. The backup is `/root/easymode-before-v10-20261019-081032.tar.gz`.

Validated against the running router: shell syntax, four mocked health-routing/recovery regression cases, module/script syntax and import checks, exact-board/release installer preflight, plus post-install version/homepage/assets/services and read-only SIM probe checks. No full per-file readback/hash comparison was performed. Long-term stability, hardware reset persistence, and other boards remain unverified.
