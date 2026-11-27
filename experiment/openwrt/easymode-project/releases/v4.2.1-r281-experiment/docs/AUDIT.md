# Easy Mode / LuCI reconciliation

Audit date: 2026-10-04. Platform: Notion R281, OpenWrt 24.10.8, Linux 6.6.144. Preserve the user's current source and settings. Tests used actual browser controls and native UCI/LuCI readbacks; private reports remain on the owner's laptop.

| Area | Evidence | Limit |
|---|---|---|
| Navigation | Every main tab/subtab opened; browser error collection empty; Advanced reached LuCI and logout returned to login | Destructive system actions not executed |
| Wi-Fi scan | Both radios returned networks; asynchronous status remained responsive; all enabled result buttons populated the form | Scanning can interrupt the shared AP/STA radio briefly |
| Dedicated repeater | Actual browser Apply passed; separate bridge client obtained upstream DHCP and portal HTTP 302; home route stayed cellular; home DNS stayed cellular | Virtual bridge client, not a physical repeater Wi-Fi client |
| Captive portal | Failed return path reproduced; trace showed inbound TTL 1; scoped compatibility rule changed portal HTTP 000 to 302 | Paid/login internet access not purchased or bypassed |
| Whole-network relay | Isolated UCI fixture checked DHCP/RA changes, restoration, NAT disabled and backup SSID isolation | No live whole-LAN migration during this audit |
| SMS | Easy Mode inbox retrieved; native LuCI listed 35 inbox rows; earlier authorized test send was accepted by modem; local-number and 5454 controls checked | Modem acceptance is not delivery confirmation; USSD no response |
| SMS settings | SM, ME and original storage saved and read back; clear-history confirmation canceled | User messages preserved |
| Wi-Fi/Piso | Home and Piso saves completed; original values preserved; Piso link reached Modes | No physical Piso server/VLAN traffic test |
| Ports | Current standard mode reapplied; browser management-confirmation transaction passed | Alternative physical port modes not activated |
| Policy | Balance/failover and backup toggle saved/read back and restored | Only one verified internet source; real dual-uplink balance pending |
| APN/antenna | Existing APN and automatic antenna mode applied; connectivity verified | External antenna selection not exercised without antenna verification |
| Bands/CA | All/Clear/individual/Detect controls checked; supported bands matched LuCI; live require-CA trial saw CA, measured slower speed, restored bands and verified internet | Cannot compel tower scheduling or guarantee speed improvement |
| Diagnostics | API and actual browser ping/diagnose/download completed; last browser ping 0% loss and download 6.30 Mbps | Single-stream test, not a line-rate certification |
| Design/session/logs | Themes, session save, refresh and all log filters exercised; UCI readback checked | No factory reset performed |
| Recovery probes | Isolated namespace reproduced wrong route under outage policy; source-specific oif rule restored gateway routing while unbound traffic stayed blocked | Long-term cellular stability still needs observation |
| Memory | Approximately 25–31 MiB available during relevant checks; no swap or observed OOM | Low signal/data-path stalls can occur without memory exhaustion |

## Root causes corrected

1. Nested synchronous iwinfo RPC from the same rpcd service caused scan timeouts. Scans now run in a separate bounded worker.
2. Late asynchronous modem results could replace a newer page. Rendering now verifies the navigation generation.
3. The router regex engine rejected the band field's large repetition bound. Length and character validation are separate now.
4. `set -u` broke jshn initialization in diagnostic workers. Worker exit now publishes a final failure instead of leaving a permanent pending result.
5. relayd's local default route could capture router-originated traffic. Rules preserve learned relay host routes while retaining normal home routing.
6. A captive portal sent TTL-1 replies that expired in the IPv4 pseudo-bridge. Compatibility is restricted to that relay's upstream client subnet.
7. The process check misidentified a running relayd on this BusyBox build. A verified `pidof` check replaces it.
8. Recovery probes bound to a device could lose their gateway under an unreachable default policy. Dedicated source routes now isolate these probes from the home policy.

The virtual test harness also needed a stable bridge MAC: attaching a randomly addressed veth could otherwise change the bridge address cached by relayd. This was corrected in the harness, not worked around in the user network.

## Review and release state

Source underwent local review, syntax checks, isolated configuration tests and live browser/device tests. An independent reviewer could not run because of tool quota; no independent-review claim is made. There is no new reset-persistent firmware or one-click flash release in this revision. Older feature requests not present in the current live baseline, including configurable LED effects, remain pending.
