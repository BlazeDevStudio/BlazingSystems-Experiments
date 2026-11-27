# BlazePwifi production-readiness audit

Release candidate: 0.2.0-rc.2

## Audit scope

The audit covers the OpenWrt runtime, captive portal/API, nftables enforcement, persistent accounting, Vendo protocol, ESP8266 firmware, installer/upgrade path, first-boot provisioning, ImageBuilder pipeline, and CI tests.

## Findings fixed in v0.2

| Finding | Risk | Resolution |
|---|---|---|
| MAC-only account identity | Private/random MAC could lose purchased time | Persistent 128-bit browser device token; MAC is now a replaceable network binding |
| Coin ACK loss | Retry could double-credit | Stable ESP event nonce plus server idempotency marker |
| Coin event reusable for another customer | Credit theft/replay | Signature includes active coin-window target nonce |
| Voucher marker shared bounded coin history | Old voucher could eventually become reusable | Voucher markers are retained; only coin markers are bounded |
| Vendo heartbeat persisted every poll | Excessive flash writes | Online Vendo state moved to /tmp |
| Coin target only in RAM | Router brownout could orphan a physically inserted coin | Short coin-window records are persisted atomically; expired targets are cleaned automatically |
| Blaze gate ran before normal firewall4 forwarding | Policy ordering ambiguity | Blaze forward hook moved to priority 10, after firewall4 |
| No payment walled garden | E-payment portals unusable without session | Dynamic IPv4/IPv6 walled garden added |
| Admin token on HTTP | Local token disclosure risk | HTTPS-only admin listener on LAN address |
| ESP setup AP was open | Nearby reconfiguration risk | Per-device WPA2 password plus AP auto-shutdown |
| v0.1 MAC state had no migration path | Upgrade could orphan balances | One-time MAC-to-device-token claim migration |
| Cross-filesystem temp files | `/tmp` → `/etc` move was not a guaranteed atomic rename | Persistent account/voucher/target temp files now stage on the state filesystem |
| Stale/racy global lock | Crashed or concurrent CGI could wedge or overlap accounting | Kernel `flock` serializes writers and is automatically released on process exit |
| Zero-balance visitors persisted | Account file could grow from casual portal views | Read-only visits stay non-persistent until a money/session action |
| ESP/router brownout during coin ACK | Coin could be lost or duplicated | Durable router target + ESP LittleFS event journal + idempotent server marker |
| Runtime scripts stored non-executable | Direct-flash image could boot with unusable service/CGI files | Git executable modes are audited and re-applied before release |
| Local services behind restrictive zone | Portal/Vendo/admin could be unreachable | Installer creates explicit rules on configured local firewall zone only |
| Firmware artifacts lacked local checksum/install image | Deployment integrity/install gap | Per-target SHA256SUMS plus Ruijie initramfs+sysupgrade and x86 BIOS+EFI checks |

## Automated gates

1. Static shell/hardening and executable-mode validation.
2. Accounting integration test, repeated three times per release run.
3. Persistence/replay/migration/concurrency stress test, repeated three times per release run.
4. ESP8266 NodeMCU compilation.
5. OpenWrt 25.12.5 Ruijie RG-EW1200G Pro v1.1 ImageBuilder.
6. OpenWrt 25.12.5 x86_64 ImageBuilder.
7. Release bundle and SHA-256 artifacts.

## Remaining physical validation before calling a specific appliance field-proven

- Flash and recover an actual RG-EW1200G Pro v1.1.
- Measure actual coin-acceptor pulse polarity, width and debounce requirements.
- Verify relay/LED GPIO electrical levels with the chosen ESP8266 board.
- Real power-cut testing during coin acknowledgement, ESP flash journaling and router state replacement (software-level reboot/tmpfs-loss paths are covered automatically).
- Sustained multi-client traffic and portal load.
- Real captive-portal behavior on Android, iOS, Windows and ChromeOS.
- Real e-payment provider flows for any configured walled-garden domain list.
- WAN/LAN/VLAN topology used by the intended installation.

The codebase is treated as a release candidate until those hardware/site tests are complete.
