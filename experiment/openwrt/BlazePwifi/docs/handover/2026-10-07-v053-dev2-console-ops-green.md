# BlazePwifi v0.5.3-dev.2 — Console Operations Green Candidate

Date: 2026-10-07

## Scope

This development slice completes the first operational Management Console expansion after the v0.5.3-dev.1 Rental/QR/timer hardening.

Full BlazePwifi is the active target. `profiles/standalone-rental` remains reference-only and was not modified.

## Development identity

- VERSION: `0.5.3-dev.2`
- BlazeRental versionName: `0.5.3-dev.2`
- BlazeRental development versionCode: `50291`
- Development range remains `50290–50298`
- Frozen v0.5.2 forward-install rescue remains `50299`
- Final v0.5.3 production versionCode remains reserved at `50300`

No v0.5.3 production release/tag/signing action was performed.

## Advanced Terminal

Advanced Terminal is implemented for the Full Management Console with these guardrails:

- disabled by default;
- admin role required;
- current admin password re-authentication required to enable/open;
- existing auth lockout system reused;
- CSRF required for state-changing actions;
- terminal token bound to current authenticated admin session and source IP;
- one active terminal session per admin;
- short absolute TTL and idle expiry;
- one command at a time across the appliance;
- bounded command runtime using `timeout`;
- bounded captured output;
- no detached/background jobs;
- high-risk appliance lifecycle/storage commands are blocked from the raw terminal path;
- terminal token exists only in page-memory and is not stored in localStorage/sessionStorage or rendered into the DOM;
- close/disable invalidates terminal sessions;
- audit log stores command verb + command SHA-256 instead of full command text.

High-risk operations such as reboot, sysupgrade, firstboot/jffs2reset, raw mtd and fw_setenv remain reserved for dedicated guarded controls.

## Safe Tools expansion

The allowlisted diagnostic layer now includes:

- Ping
- latency/jitter sample
- Traceroute
- DNS lookup
- TCP port check
- WAN status
- NTP/clock status
- Routes
- Interfaces
- Local neighbor table
- Wi-Fi status
- Coin-controller status
- Storage
- Services
- Recent system logs
- Uptime
- Speed test when a supported helper is installed

Safe Tools remain separate from Advanced Terminal.

## Worldwide Remote Access profile

The Management Console now supports a validated/staged remote profile with modes:

- Disabled
- WireGuard — recommended
- ZeroTier — easy mesh

Profile fields include:

- node name and site label;
- source CIDR allowlist;
- heartbeat and offline thresholds;
- separate Monitoring, Management and Remote Terminal permissions;
- WireGuard public endpoint/port;
- WireGuard tunnel address;
- WireGuard hub **public** key;
- allowed management routes;
- keepalive, DNS and MTU;
- ZeroTier network ID.

The profile does **not** accept or expose a WireGuard private key.

Saving the profile:
- requires admin role;
- requires current-password re-authentication;
- uses the existing lockout/audit system;
- is serialized and stored with restrictive permissions;
- validates the selected mode before accepting it.

## Deliberate safety boundary

Live WireGuard/ZeroTier network/firewall activation is **not enabled in dev.2**.

The profile is validated and staged, but applying it to live interfaces/routes/firewall remains safety-locked until a separate network-survival implementation proves:

- atomic apply/rollback;
- management-path preservation;
- firewall fail-closed behavior;
- timeout/health rollback;
- reboot recovery;
- malformed-profile rejection;
- WireGuard and ZeroTier package/version compatibility;
- no captive-portal/LAN isolation regression.

This is intentional. The browser cannot currently disconnect the appliance by saving a remote profile.

## Exact green candidate

Final repaired branch SHA:

`e917171d2a3875fd54183d552c02f8afcdb7862f`

Branch workflow:

`37500821733` — **PASS**

Reconciled PR #18 synthetic merge tree:

`dee385974b7142afa4e8a56fc47d611f62a10ccf`

PR merge-tree workflow:

`37500829258` — **PASS**

The final branch run and reconciled PR merge-tree run passed:

- static/security/config/integration validation;
- the new dev.2 console-operations shell security test;
- accounting/replay stress;
- Playwright browser runtime audit;
- Android current/rescue builds;
- Android Device Owner emulator;
- ESP8266 and ESP32 build/simulation;
- Ruijie build/simulation;
- required Orange Pi build/simulation targets;
- x86_64 build and QEMU simulation;
- transactional update bundle;
- final candidate gate.

## Browser runtime evidence

The browser audit exercised and passed:

- staged WireGuard profile save;
- password re-authentication;
- terminal enable;
- terminal session open;
- bounded `console-ok` command;
- terminal close;
- dual CSRF transport;
- both Rental QR modes;
- portal session timer;
- portal Insert Coin timer;
- no console JavaScript errors.

The retained audit reports:

- `remote_profile_saved=true`
- `advanced_terminal_session=true`
- `dual_csrf_transport=true`
- `portal_session_countdown_live=true`
- `portal_coin_window_countdown_live=true`
- `console_errors=false`

## Android regression evidence

Device Owner emulator passed `0.5.3-dev.2` using:

`candidate/android/BlazeRental-0.5.3-dev.2-ci.apk`

This confirms the Management Console changes did not regress the previously green BlazeRental Device Owner gate/timer behavior.

## Remote profile race found during reconciliation

The first PR browser merge-tree audit exposed a real operator-edit race: a delayed unconditional startup `loadRemote()` could overwrite the Remote Access mode selector after the operator had already chosen WireGuard.

The final repair:
- removed background startup loading of editable Remote Access configuration;
- keeps page-entry / explicit-refresh loading;
- suppresses stale asynchronous remote-load responses by generation;
- renders the authoritative `remote_config_set` response immediately before follow-up reconciliation;
- adds source regression gates forbidding the old startup preload;
- instruments the browser audit to prove the save request reached the server and the stored mode became `wireguard`.

Both the final branch browser audit and PR #18 merge-tree browser audit passed after this repair.

## Integration note

At candidate completion, repository `main` contained four newer unrelated BlazePisonet SoftTimer commits after the branch point.

Therefore dev.2 must **not** be force-fast-forwarded over `main`.

Integration must use normal Git reconciliation/PR merge so:
- the SoftTimer history is preserved;
- Full BlazePwifi dev.2 is preserved;
- Standalone remains untouched;
- the combined tree receives a fresh full CI matrix before being accepted on `main`.
