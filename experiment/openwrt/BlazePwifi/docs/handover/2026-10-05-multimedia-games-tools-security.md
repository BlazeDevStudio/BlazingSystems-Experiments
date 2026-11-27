# Handover Log — 2026-10-05 — Multimedia, BlazeGames, Tools and Abuse Resistance

## Approved design changes

The owner approved expanding the BlazePwifi Management Console with all previously proposed richness features and additionally approved:

- Tools module (ping, traceroute, DNS, speed test, WAN tests, NTP, Wi-Fi scan, interface diagnostics, controller tests, latency/jitter/packet-loss, log/service/storage/diagnostic tools).
- Wi-Fi portal Movies/Multimedia section.
- Wi-Fi portal Games section backed by the existing BlazeGames offline arcade emulator HTML project.
- Multimedia Manager with storage detection/selection, upload/index/manage controls, and per-item free-vs-active-session access policy.
- BlazeGames Manager with ROM/game management, categories, metadata, storage target and free-vs-active-session access policy.
- Wider BlazeRental/LCM branding and rename away from Rootless Pixel Launcher.
- Strong brute-force and DoS resistance requirements across console, portal, APIs and upload/media surfaces.

## Security note

Do not claim the system is literally DDoS-proof or brute-force-proof. Implement strong resistance using bounded resources, rate limits, escalating lockouts, request/upload limits, concurrency limits, timeouts, audit logs and fail-closed behavior.

## Multimedia policy

Media may be:
- free, or
- accessible only while the user's paid session is active and time is running.

Paused time does not satisfy paid-media access.

Storage strategy:
- removable USB storage when present,
- internal/SSD/SD storage on larger builds,
- capability-aware selection in the Management Console.

Lite devices should avoid mandatory transcoding; prefer browser-native formats and HTTP range serving.

## BlazeGames policy

Use the existing BlazeGames HTML emulator direction. The console should manage which ROMs/games are available, metadata, categories, enable/disable state, storage location, and access policy.

Do not ship copyrighted third-party media or ROMs by default; use administrator-supplied/licensed content.

## Canonical handover update

Updated:
`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`

Commit:
`756c9d2e2a87ecb986dc8cc8cad36f1c9ce324bc`

## Current development status

Implementation is still paused while requirements are being collected.

## Next action

Continue specification review until the owner explicitly resumes development.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue BlazePwifi from the repository state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest file under experiment/openwrt/BlazePwifi/docs/handover/.
3. Inspect recent Git history and verify commit 756c9d2e2a87ecb986dc8cc8cad36f1c9ce324bc is present.
4. Audit the newly approved Management Console, Tools, Multimedia Manager and BlazeGames Manager requirements for conflicts, missing wiring, unsafe resource assumptions and Lite-target constraints.
5. Reconcile these requirements with the existing portal, rental, voucher, controller, WAN/LAN/VLAN, backup, sales and security architecture.
6. Preserve the rule that the factory Blaze portal is undeletable and the implementation remains framework-light.
7. Preserve the free-vs-active-session media/game access model; paused sessions must not count as active.
8. Preserve the abuse-resistance requirement without claiming literal DDoS/brute-force immunity.
9. Do not resume implementation unless the owner has explicitly said to continue development.
10. After the next meaningful success/failure/design change, update PROJECT_HANDOVER.md and add a dated handover log with a fresh Audit & Reconcile prompt.
```
