# BlazePwifi v0.5.3-dev.3 — Transactional WireGuard Green Candidate

Date: 2026-10-07

## Scope

This development slice enables **live WireGuard remote management** for Full BlazePwifi with transactional apply/rollback and management-path survival protections.

Full BlazePwifi remains the active target.

`profiles/standalone-rental` remains outside Full BlazePwifi development scope. Current `main` contains a newer Standalone Rental RC4 audit/documentation commit; dev.3 does not modify or replace those files.

## Development identity

- VERSION: `0.5.3-dev.3`
- BlazeRental versionName: `0.5.3-dev.3`
- BlazeRental versionCode: `50292`
- Development range remains `50290–50298`
- Frozen v0.5.2 forward-install rescue remains `50299`
- Final v0.5.3 production code remains reserved at `50300`

No v0.5.3 production release/tag/signing operation is part of this development milestone.

## Live WireGuard safety model

### Key material

- The device WireGuard private key is generated on the BlazePwifi appliance.
- It is stored with restrictive permissions.
- The browser/API never accepts, returns or displays the private key.
- The Management Console may show only the device public key after explicit admin re-authentication.

### Network ownership

Dev.3 owns only named Blaze sections:

- network interface: `blazewg`
- network peer: `blazewg_peer`
- firewall zone: `blazewg`
- firewall admin rule: `blazewg_admin`

Existing LAN, WAN, EasyMode and unrelated operator sections remain outside dev.3 ownership.

### Route rejection before apply

Live apply is rejected when the profile would:

- install `0.0.0.0/0`;
- install an overly broad IPv4 route;
- overlap an existing directly connected network;
- capture the current administrator source path;
- start from an administrator session already routed through the Blaze WireGuard interface;
- proceed without a usable default route.

Dev.3 live apply intentionally validates IPv4 management routes first. IPv6 live-route activation remains outside this slice.

### Transaction and rollback

Before mutating the live configuration, BlazePwifi records:

- network config snapshot;
- firewall config snapshot;
- prior remote runtime state;
- current default-route signature;
- current administrator-route signature;
- staged profile hash.

A pending transaction marker is written before interface activation.

A detached watchdog is armed before the risky part of the transaction. If the request dies, hangs or never finalizes, the watchdog restores the previous state.

A boot-time guard also restores the previous snapshot if the router reboots while a transaction is still pending.

When updating an already-active Blaze WireGuard deployment, rollback restores the **previous active tunnel/runtime state**, not merely generic files.

## Success requirements

A live WireGuard apply is accepted only after all of these pass:

1. WireGuard UCI sections are written.
2. The `blazewg` interface starts.
3. Firewall reload succeeds.
4. A real WireGuard handshake is observed.
5. The dedicated remote-admin listener starts when Management permission is enabled.
6. Default route signature remains unchanged.
7. The current administrator route signature remains unchanged.

If any check fails, the previous network/firewall/runtime state is restored.

## Dedicated remote admin listener

Remote management does **not** rebind or restart the normal LAN admin uHTTPd during apply.

Dev.3 uses a dedicated WireGuard-only HTTPS service bound to the tunnel address.

Its document root contains only:

- `admin.html`
- admin JavaScript assets
- vendor assets required by the admin page
- `admin`
- `admin-login`
- `admin-logout`
- `admin-session` CGI endpoints

The remote listener does not expose the normal captive-portal, Rental or Vendo CGI endpoints.

## Remote Terminal permission

When a request arrives through the WireGuard management listener:

- Remote Terminal permission is enforced server-side.
- Disabling Remote Terminal prevents terminal API use over the remote listener.
- Local/LAN admin behavior remains unchanged.

## Management Console flow

The dev.3 console supports:

1. Generate/show this BlazePwifi device public key.
2. Configure the remote WireGuard hub/peer.
3. Save and validate the staged profile.
4. **Test & Apply WireGuard**.
5. Show activation state and verified handshake timestamp.
6. Show when the live tunnel is active but newer staged changes are not yet applied.
7. Disable live WireGuard from a local/non-WireGuard management path.

ZeroTier profile configuration remains available, but **live ZeroTier activation remains staged-only** in dev.3.

## Regression coverage

The dev.3 validation line includes coverage for:

- transaction rollback/watchdog ownership;
- boot recovery;
- IPv4 admin-source recognition;
- route-helper state isolation;
- route-overlap rejection;
- private-key config permissions;
- exact restricted-admin CGI allowlist;
- WireGuard listener isolation;
- staged/live activation state;
- browser management flow;
- transaction-engine authoritative EOF integrity.

## Exact green candidate

Runtime candidate before documentation-only commits:

`c60645729e6fbd9b9af6db8b11af13c3b58b7ae3`

Full workflow:

`37516557416` — **PASS**

The exact run passed:

- validation/security/config/integration/stress;
- dev.3 WireGuard transaction tests;
- Playwright browser runtime;
- Android current/rescue build;
- Android Device Owner emulator;
- x86_64 build and QEMU;
- ESP8266 and ESP32;
- Ruijie;
- required Orange Pi targets;
- update bundle;
- final candidate gate.

A second full run on the same runtime SHA, `37515722404`, also passed.

## Integration rule

At this point `main` is one commit ahead only because of a newer Standalone Rental RC4 documentation/audit commit. That commit changes only files under `profiles/standalone-rental` and has no file overlap with dev.3.

Do not force-update `main`.

Use a normal integration branch/PR so:

- the Standalone RC4 documentation remains exactly preserved;
- Full BlazePwifi dev.3 is preserved;
- the combined merge tree receives a fresh full CI matrix;
- no v0.5.2 production signing/recovery history is changed.
