# Handover Log — 2026-10-05 — Remote Monitoring / Remote Management

## Approved addition

Add configurable remote monitoring and remote management to BlazePwifi.

## Supported modes

Exactly two first-class remote-access modes:

1. **WireGuard VPN — recommended/default selection when enabling remote access**
   - lightweight and well-supported on OpenWrt;
   - owner-controlled;
   - supports site-to-site and outbound-to-hub topology;
   - suitable for nodes behind NAT/CGNAT when the BlazePwifi node initiates the tunnel to an owner-controlled hub.

2. **ZeroTier — easy-mesh alternative**
   - simpler NAT/CGNAT traversal and multi-site mesh enrollment;
   - configurable Network ID and routing/firewall scope;
   - no hard-coded account/network dependency.

Remote access itself remains disabled until explicitly configured.

## Configurability

No vendor/account/endpoint/key/subnet/route is hard-coded.

Monitoring, management and terminal permissions are independently configurable.

Remote services/modules can be allowed or denied individually.

## Security

- Do not expose the Management Console directly on public WAN by default.
- Bind remote management to LAN/VPN/overlay interfaces.
- Support source-IP/subnet allowlists.
- Re-authenticate for high-risk actions.
- Audit all remote state-changing actions.
- Apply rate limits/session limits/timeouts equally to remote access.
- Local management and captive portal must continue if the remote tunnel fails.

## Fleet monitoring fields

Node/site label, online status, last seen, WAN/tunnel health, resource health, session counts, controller/rental-device status, firmware/version, alerts and backup state.

## Repository change

Updated:
`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`

Commit:
`eb266a619a090fd06b06ea2fd1caf6a89244bd86`

## Development status

Implementation remains paused while requirements are being collected.

## Next action

Continue specification review until the owner explicitly resumes development.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue BlazePwifi from the repository state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest handover log.
3. Verify commit eb266a619a090fd06b06ea2fd1caf6a89244bd86 is present.
4. Audit the Remote Access / Fleet Management requirements against the existing authentication, firewall, VPN, WAN/LAN/VLAN, terminal, alerts and backup architecture.
5. Preserve exactly two first-class remote access modes: WireGuard as recommended/default selection and ZeroTier as the easy-mesh alternative.
6. Keep remote access disabled until the owner configures it; do not hard-code any vendor account, endpoint, key, subnet or route.
7. Ensure the Management Console is not exposed directly to public WAN by default.
8. Preserve independent Monitoring, Management and Terminal permissions plus high-risk re-authentication and audit logging.
9. Do not resume implementation unless the owner explicitly says to continue.
10. Update PROJECT_HANDOVER.md and add a dated handover log after the next meaningful change, including a fresh Audit & Reconcile prompt after every success.
```
