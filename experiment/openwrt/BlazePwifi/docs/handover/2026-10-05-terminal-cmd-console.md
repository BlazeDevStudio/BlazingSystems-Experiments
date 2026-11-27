# Handover Log — 2026-10-05 — Terminal / CMD Console Requirement

## Approved addition

Add a Terminal / CMD capability to the BlazePwifi Management Console.

## Design

Two levels:

1. Safe Commands
   - curated/allowlisted diagnostics and admin commands;
   - preferred default for normal console use.

2. Advanced Terminal
   - optional owner-only shell;
   - disabled by default;
   - fresh re-authentication;
   - short-lived session;
   - audit logging;
   - output/time/concurrency limits;
   - rate limits and brute-force protections;
   - optional LAN-only/local-management restriction.

Captive-portal users must never get terminal access.

## Security boundary

Prefer dedicated Management Console controls for destructive operations. Use raw shell only where necessary. On Lite OpenWrt devices, prefer a lightweight streamed command runner over a heavy terminal framework.

## Repository change

Updated:
`experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`

Commit:
`832165170f7f01f0141248b8dae4e5f03d684e70`

## Development status

Implementation remains paused while requirements are being collected.

## Next action

Continue specification review until the owner explicitly resumes development.

## Audit & Reconcile prompt

```text
@GitHub Reconcile and continue BlazePwifi from the repository state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest handover log.
3. Verify commit 832165170f7f01f0141248b8dae4e5f03d684e70 is present.
4. Audit the Terminal/CMD requirement against the current admin authentication, roles, CSRF, rate-limiting and Lite-target constraints.
5. Preserve the two-level model: Safe Commands by default, Advanced Terminal optional and owner-only.
6. Ensure captive-portal users can never reach terminal functionality.
7. Prefer dedicated UI controls for destructive actions and keep raw shell tightly gated.
8. Do not resume implementation unless the owner explicitly says to continue.
9. Update the canonical handover and create a dated log after the next meaningful change.
10. Include a fresh Audit & Reconcile prompt after every successful milestone.
```
