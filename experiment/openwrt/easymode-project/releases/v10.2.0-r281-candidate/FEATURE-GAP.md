# QManager feature reconciliation for EasyMode R281

Reviewed 2026-10-26 against [QManager's public README](https://github.com/dr-dolomite/QManager) at commit `7bad6f8f48b02241e1767b3a208c2290d7a1dbc9`, the R281 EasyMode v10 source, and the running R281 portal. This is a feature comparison, not a source-code merge. QManager's [license](https://github.com/dr-dolomite/QManager/blob/main/LICENSE) includes a Commons Clause restricting sale, so the candidate contains no QManager source or artwork.

Legend: **Present** means the R281 portal already offers a meaningful equivalent; **Added** means this 10.2 candidate adds it; **Partial** means a narrower EasyMode feature exists; **Gap** means no verified EasyMode equivalent. Separate LuCI or Traffic Intelligence capabilities are called out explicitly.

| QManager capability | EasyMode status | Reconciliation |
| --- | --- | --- |
| Live signal, bands, modem identity | Present, added | EasyMode displays RSRP, RSRQ, SINR, RSSI, active bands and read-only modem identity. This revision adds a 24-hour signal-history view from cached samples. Per-antenna 4×4 values remain a gap. |
| Network events | Added, partial | New journal records route changes, SIM address changes, watchdog actions and cached cell/band changes. Full modem registration history remains a gap. |
| Latency, jitter, packet loss, history | Added, partial | New two-target loss/average RTT and HTTPS sampling has up to 24 hours of RAM history. Jitter, hourly aggregates and persistence across reboot remain a gap. |
| Live bandwidth and traffic usage | Partial | EasyMode links to its separate Traffic Intelligence module. The R281 home dashboard does not yet show a live WebSocket throughput chart. |
| LTE/NR band locking | Present | Hardware-detected band lists with rollback and optional speed comparison. |
| Tower and exact frequency locking | Gap | Requires modem-specific AT command mapping, safe rollback, and field validation before exposure. |
| APN management and carrier presets | Partial | Current APN can be edited with rollback; saved named APN profiles and presets remain a gap. |
| Custom SIM profiles and full scenarios | Gap | Define a versioned configuration schema and transaction/rollback before one-click activation. |
| Network priority and mode | Partial | EasyMode has multi-WAN source priority/failover/balancing. Cellular RAT/operator preference controls remain a gap. |
| Cell and neighbor scanner | Gap | Existing Wi-Fi scanner is different; cellular scan needs modem capability detection and bounded AT operations. |
| Frequency calculator | Gap | Can be added without modem writes after LTE/NR channel mapping is verified against standards. |
| SMS and USSD | Present | Includes threaded messages, contacts, SIM inbox archiving, backup and USSD. |
| IMEI read, backup, write, toolkit | Partial | Identity is read-only. Write/clone functions are excluded from this candidate pending explicit product/legal/hardware review. |
| FPLMN and MBN controls | Gap | Hardware-specific and potentially service-disruptive; require modem support detection, backup and recovery. |
| Ethernet speed and duplex control | Partial | Current link speed is shown; manual negotiation control is absent. |
| TTL/HL, MTU, IP passthrough, DNS override | Gap in EasyMode | Some advanced network settings may be reachable in LuCI. An EasyMode UX needs validation and transactional rollback. |
| Video optimizer and traffic masquerade | Gap | Carrier-traffic manipulation is outside the current reliability work and should be assessed separately. |
| Connection watchdog | Added | Multi-target checks, data reconnect, radio re-registration, and durable-budget last-resort reboot. No automatic SIM-slot failover is claimed. |
| Email and SMS downtime alerts | Gap | Requires private notification configuration, deduplication and recovery/outage policy. |
| Phantom WAN guard | Gap | Add only after a detected netifd retry-loop case on the R281; do not disable arbitrary profiles. |
| Scheduled radio low-power mode | Gap | Needs schedule/timezone semantics and an emergency management path. |
| Tailscale or other VPN control | Gap | Keep installation and authentication separate from the router's core recovery path. |
| In-app software updates | Gap | Needs signed or hash-verified release metadata, rollback and channel policy. The current archive installer is manual. |
| Searchable system logs | Present | EasyMode has OpenWrt log filtering; the new event journal retains key network transitions in RAM. |
| Dark/light themes and responsive layout | Present, improved | Existing themes remain. This revision adds a desktop rail, directly visible mobile main destinations, native sub-section selection and a Traffic Intelligence mobile view picker. |
| Authenticated local portal | Present | Uses OpenWrt administrator sessions; no separate QManager authentication stack was copied. |
| Direct AT terminal and setup wizard | Gap | Both need clear permission boundaries and recovery-aware design. |

## Recommended implementation order after 10.2

1. **Reliability proof:** finish the hardware gates in `HANDOFF.md`, add outage/recovery summaries and alert delivery, then decide whether to make reboot enabled by default in a general release.
2. **Modem workflows:** add read-only cell/neighbor scan and verified frequency calculator; then APN profiles and transactional tower/frequency controls for the actual installed modem.
3. **Network and product operations:** bring advanced DNS/MTU/IP passthrough into EasyMode with rollback, and add verified in-app updates and configuration export/import.
4. **Broader hardware:** replace board-specific assumptions with capability profiles before claiming parity on other OpenWrt routers.

This release does **not** claim complete QManager feature parity. The gaps above are tracked so they can be implemented independently without removing current EasyMode features or mislabeling a partial control as complete.
