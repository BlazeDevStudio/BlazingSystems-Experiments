# Handover Log — 2026-10-05 — Worldwide Remote Access Clarification

## Clarification

The owner clarified that Remote Monitoring / Remote Management means **true worldwide access** to the BlazePwifi/PisoWiFi system.

Expected behavior:

- Owner can open the BlazePwifi Management Console from mobile data, another city, or another country.
- The owner does not need to be connected to the local LAN.
- This should still work when the site is behind NAT/CGNAT, provided one of the configured outbound tunnel methods is active.
- The preferred UX is browser access to the console through a private VPN/overlay path rather than exposing the admin page directly to public WAN.

## Supported transport choices remain

- WireGuard — recommended/default when remote access is enabled.
- ZeroTier — easy-mesh alternative.

## Repository change

Updated:
`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`

Commit:
`f66060eabe94a23ad8bdcad0dcdd1b8d40a50687`

## Next action

Continue requirements gathering until the owner explicitly resumes implementation.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi remote-management requirements.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md and the newest handover log.
2. Verify commit f66060eabe94a23ad8bdcad0dcdd1b8d40a50687 is present.
3. Preserve the requirement that remote management means worldwide browser access, not merely LAN/VPN-local access.
4. Ensure the design supports sites behind NAT/CGNAT using outbound WireGuard-to-hub or ZeroTier.
5. Do not expose the Management Console directly to the public WAN by default.
6. Preserve independent Monitoring, Management and Terminal permissions plus audit/rate-limit protections.
7. Do not resume implementation unless explicitly instructed.
8. Update the handover after the next meaningful change and include a fresh Audit & Reconcile prompt after success.
```
