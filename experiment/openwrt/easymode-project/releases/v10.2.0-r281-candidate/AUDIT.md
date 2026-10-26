# EasyMode and R281 connectivity audit — 2026-10-26 PHT

## Evidence

| Source | Observation | Limit |
| --- | --- | --- |
| Two pasted Windows continuous-ping captures | 1.1.1.1: 503 replies, 280 timeouts, 4 local errors, longest timeout run 87, median reply 104 ms; 8.8.8.8: 346 replies, 132 timeouts, longest run 5, median reply 74 ms. | The captures lack per-packet timestamps and are client-side; they cannot attribute loss to the modem, carrier, Wi-Fi, or remote target. |
| Authenticated R281 read-only SSH inspection | Board `notion,r281`, OpenWrt 24.10.8, EasyMode 10.0.0. At about 16:00 PHT, cellular health was online via `eth1`, with 8.8.8.8 or HTTPS often succeeding when 1.1.1.1 did not. | Current boot and bounded RAM history only. |
| Fresh router-side probes | Ten packets to 1.1.1.1 lost 30%; ten to 8.8.8.8 lost 10%; HTTPS generate_204 returned HTTP 204 in about 0.72 seconds. | One short sample; does not establish long-term service quality or prove reboot is the recovery cause. |
| Current-boot `logread`, health CSV, routes, and kernel ring | Health samples after the boot's initial link acquisition were successful. No current-boot modem USB reset or OOM appeared in the inspected kernel lines. `logread` was dominated by DNS query entries, so earlier diagnostic entries had rolled out. | A log buffer dominated by query logging cannot reconstruct the previous outage or reboot cause. |

## Findings and response

| Priority | Finding | Revision |
| --- | --- | --- |
| P1 | The v10 page said radio re-registration was automatic, while its watchdog launched only data reconnects. | Recovery stages now match the interface: data reconnect, radio re-registration, controlled reboot. |
| P1 | A naive reboot-on-ping-failure would reboot during target-specific loss even when HTTPS and another target work. | Three probe methods remain; the reboot helper performs a final independent cellular probe and refuses to reboot while a backup uplink is healthy. |
| P1 | Repeated reboot could leave the R281 unavailable for long periods. | Durable two-per-24-hour limit, 90-minute spacing, minimum uptime, valid clock, and pending-configuration guards. |
| P2 | A binary online status hides heavy loss and latency. | Added a separate quality sampler and a bounded 24-hour RAM history. Quality is informational; it does not alone trigger recovery. |
| P2 | DNS query logging rapidly rolls older `logread` entries away. | Added a separate bounded network event journal. Query logging was not changed because other installed monitoring may depend on it. |
| P2 | Tabs and subtabs were troublesome on small screens; the horizontal strip hid choices. | Added five directly visible main destinations, a native sub-section picker, remembered sub-sections, and a mobile view picker in Traffic Intelligence. |

The 10.2.0 application update was installed on the R281 with a rollback archive at `/root/easymode-before-v10.2-20261026-165405.tar.gz`. Traffic Intelligence Cellular 7.0.2 was also installed. No induced outage, test reboot, radio reset, network reload, or firmware flash was performed. The cellular default route remained on `eth1`; health, quality and the responsive portal were verified. A separate private reset-persistent sysupgrade image is staged and tested but not flashed. See [HANDOFF.md](HANDOFF.md) for evidence and remaining gates.
