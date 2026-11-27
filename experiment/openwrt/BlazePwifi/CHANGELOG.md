# Changelog

## 0.5.3-dev.5 — development

- Enabled transactional **live ZeroTier activation/disable** for Full/Standard BlazePwifi targets while keeping Lite/Ruijie free of the ZeroTier runtime dependency.
- Added stable on-device ZeroTier identity preparation using `zerotier.global.secret`. The identity secret is never returned to the browser/API/logs; only the public 10-character node ID is exposed after admin re-authentication.
- Added strict ownership guards for modern OpenWrt ZeroTier UCI: BlazePwifi manages only `zerotier.blazepwifi`; foreign/custom ZeroTier network sections or legacy `.join` layouts are refused instead of overwritten.
- The untouched stock `earth` example network is pruned only when it is still exactly default, global ZeroTier is disabled and the secret is empty.
- Blaze-owned ZeroTier uses `allow_managed=1`, `allow_global=0`, `allow_default=0`, and `allow_dns=0`.
- Live apply succeeds only after the node is ONLINE/TUNNELED, the requested network reports OK, a real interface exists, an IPv4 address is assigned, mesh routes pass overlap/default-route safety validation, the restricted firewall/admin listener succeeds, and existing management/default-route signatures survive.
- ACCESS_DENIED, missing interface/address, unsafe managed routes, route capture, firewall/admin-listener failures, watchdog expiry, reboot interruption and transaction-ownership loss all fail closed and restore the previous network/firewall/remote/ZeroTier runtime state.
- ZeroTier and WireGuard cannot be active at the same time; active-transport conflicts are rejected before mutation.
- ZeroTier disable is allowed only from a local/non-ZeroTier management path and preserves the stable device identity for future re-enable.
- Rollback snapshots containing ZeroTier secret material are mode-restricted and deleted after successful finalize or rollback.
- Fixed a real pre-transaction mutation bug: an already-valid ZeroTier identity no longer rewrites/commits `global.secret` before the rollback snapshot. Existing config remains byte-stable until a transaction actually begins.
- Rebuilt the ZeroTier transaction engine from the last clean sealed source after detecting a malformed duplicate tail; the authoritative engine again has one function set and no content after its EOF seal.
- Management Console browser flow now covers prepare/show node ID, staged profile save, live ZeroTier apply/status, and safe disable without exposing secret identity material.
- Exact green application candidate: `29a3815e81c9bd7db54c8f60eb6f579c818f34ad`.
- Push workflow `37540065074` — PASS; PR #25 merge-tree workflow `37540072921` — PASS, including validation, ZeroTier survival, browser runtime, Android build, Device Owner emulator, x86 QEMU, ESP8266/ESP32, Ruijie, required Orange Pi targets, update bundle and final candidate gate.
- Development identity: `0.5.3-dev.5` / Android versionCode `50294`.
- Frozen v0.5.2 production/tag/signing/recovery workflows and `profiles/standalone-rental` remain untouched.

## 0.5.3-dev.4 — development

- Added a reviewed **Pisonet Members metadata export/import** workflow for migration into BlazePwifi central member authority.
- Export format `BLAZE_MEMBER_METADATA_V1` contains only username, enabled state, banked seconds, update timestamp, label and source metadata. Passwords, verifier hashes, salts, KDF scheme and rounds are deliberately absent.
- Added two-stage import: Admin + CSRF preview first, then Admin + fresh password re-authentication to apply the exact reviewed preview.
- Import preview tokens are short-lived, single-use, bound to the current authenticated admin session and source IP, and pinned to the member global revision so any intervening member mutation invalidates the preview.
- Added explicit collision policies: abort on any collision, skip existing members, or metadata-only update. Existing password verifier material is never replaced by an import.
- Newly imported members are created disabled with `reset_required` authentication state and must receive an administrator password reset before they can be enabled.
- Import apply is transactional across members, member-event history and global revision. Any mid-import failure restores all three snapshots.
- Added duplicate-username, malformed-field, size/member-count and bounded-bank-time rejection.
- Fixed a pre-existing empty optional-label TSV parsing defect across member authentication, password reset, balance changes, transfers, public listing, SoftTimer snapshots and metadata export.
- Added BusyBox-safe migration parsing/decoding and Base64-safe browser chunking for larger import files.
- Added browser runtime coverage for verifier-free export download, collision preview, reviewed re-authenticated apply, disabled reset-required imported account and dual CSRF transport.
- Development identity advanced to `0.5.3-dev.4` / Android versionCode `50293`.
- Exact green application candidate: `723c9c2191542e6f6867ee5fbbc31083590b49f2`, workflow `37527877646` — PASS, including Device Owner emulator, x86 QEMU and final candidate gate.
- Frozen v0.5.2 production/tag/signing/recovery workflows and `profiles/standalone-rental` remain untouched.

## 0.5.3-dev.3 — development

- Enabled transactional **live WireGuard activation/disable** for Full BlazePwifi while keeping ZeroTier live activation staged-only.
- Added on-device WireGuard private-key generation/storage with restrictive permissions. The private key is never accepted from or returned to the browser; only the device public key is exposed after explicit admin re-authentication.
- Added Blaze-owned UCI sections for the live tunnel and firewall path so dev.3 does not replace or take ownership of existing LAN/WAN/EasyMode network sections.
- Blocked unsafe WireGuard routing before apply: no default/full-tunnel routes, no overly broad routes, no overlap with directly connected networks, and no route that would capture the current admin source path.
- Added transactional network/firewall/runtime snapshots, a detached rollback watchdog, and boot-time recovery for any apply/disable interrupted by process failure or reboot.
- A candidate WireGuard apply is accepted only after the interface starts, firewall reload succeeds, a real WireGuard handshake is observed, and the default/current management route signatures remain unchanged.
- Failed apply/disable restores the previous network/firewall/runtime state, including a previously active Blaze WireGuard tunnel when updating an existing deployment.
- Added a dedicated WireGuard-only remote-admin HTTPS service with a restricted web root containing only the admin page/assets and admin CGI endpoints. The normal LAN admin uHTTPd and captive-portal/Rental/Vendo CGI surface are not rebound or exposed through this listener.
- Enforced Remote Terminal permission server-side for requests arriving through the WireGuard management listener; local/LAN admin behavior remains unchanged.
- Added explicit Management Console controls for local WireGuard public-key generation, staged profile save, **Test & Apply WireGuard**, live activation/handshake status, and safe disable from a local/non-WireGuard path.
- Added WireGuard runtime dependency to Full BlazePwifi image/install paths.
- Added regression coverage for route helper isolation, IPv4 admin-source recognition, private-key config permissions, exact restricted-admin CGI allowlist, watchdog ownership, transaction-engine EOF integrity, rollback behavior and browser management flow.
- Development identity advanced to `0.5.3-dev.3` / Android versionCode `50292`.
- Exact green branch candidate: `c60645729e6fbd9b9af6db8b11af13c3b58b7ae3`, workflow `37516557416` — PASS.
- Frozen v0.5.2 production/tag/signing/recovery workflows remain untouched.

## 0.5.3-dev.2 — development

- Added a hardened Advanced Terminal to the Full BlazePwifi Management Console. It is disabled by default and requires admin role, fresh password re-authentication, CSRF, current admin-session/IP binding, short TTL/idle expiry, one active session per admin, one command at a time, bounded runtime/output and audit logging.
- Advanced Terminal session tokens remain only in browser memory and are discarded on close/disable/error/reload; they are never written to localStorage/sessionStorage or shown in the DOM.
- Background/detached commands and high-risk appliance lifecycle/storage commands such as reboot, sysupgrade, firstboot/jffs2reset, mtd and fw_setenv are blocked from Advanced Terminal so those operations can remain behind dedicated guarded controls.
- Terminal command audit records executable name plus command SHA-256 instead of full command text to reduce accidental secret persistence in audit logs.
- Expanded Safe Tools with WAN status, NTP/clock status, latency/jitter sampling, TCP port checks, local neighbors, controller status, services and recent system logs while preserving the allowlisted diagnostic model.
- Added a validated Worldwide Remote Access profile for Disabled, WireGuard and ZeroTier modes with separate Monitoring, Management and Remote Terminal permissions, node/site identity, source CIDR allowlist, heartbeat/offline thresholds and transport-specific public configuration.
- Remote profiles never accept or expose a WireGuard private key. Saving a profile requires admin re-authentication and is serialized/crash-safe.
- Live WireGuard/ZeroTier network/firewall activation remains intentionally safety-locked in dev.2. The profile can be validated/staged, but transport apply/rollback must pass a separate network-survival matrix before activation is enabled.
- Browser runtime audit now exercises remote-profile save, password re-authentication, terminal enable/open/execute/close, dual CSRF transport and confirms no console errors.
- Fixed a real Remote Access edit race where an unconditional delayed startup refresh could reset the selected mode while the operator was editing; remote configuration now loads only on page entry/explicit refresh/save, stale responses are suppressed, and the authoritative save response is rendered immediately.
- Added dynamic console-operations security tests for password re-authentication, session binding, close/disable behavior, blocked commands, command concurrency, remote-profile validation and absence of private-key storage.
- Development identity advanced to `0.5.3-dev.2` / Android versionCode `50291`; frozen v0.5.2 production/recovery workflows remain untouched.

## 0.5.3-dev.1 — development

- Full BlazePwifi admin mutations now send CSRF through both the custom header and form body, use same-origin/no-store requests, refresh stale sessions and retry a CSRF mismatch once.
- Rental setup is split into two explicit QR modes: low-security binding for an already-installed BlazeRental APK, and Android Device Owner provisioning for factory-reset Setup Wizard.
- Device Owner provisioning binds to the published signed BlazeRental APK checksum and pins the local BlazePwifi self-signed TLS certificate for secure post-provision enrollment.
- Enrollment is retry-safe across dropped responses: the same persisted request nonce returns the same issued identity, a different nonce is rejected, and the response is authenticated before BlazeRental commits the permanent identity.
- BlazeRental and the PisoWiFi captive portal now expose separate server-authoritative purchased-time and insert-coin countdowns.
- Rental coin windows track signed pulse count and centavo value, suppress replayed Vendo events, preserve the active target across repeated open requests, and remove expired/closed progress atomically.
- BlazeRental displays received pulse/value progress and a real Done Inserting action while preventing overlapping coin-window opens.
- Runtime validation now asserts the visible unpaid 00:00:00 / INSERT COIN gate, live portal timer ticks, both QR modes, dual CSRF transport, Device Owner behavior and exact installed development version.
- Current CI artifacts use neutral development channels so post-v0.5.2 builds cannot be mistaken for the frozen v0.5.2 production release.
- Rollback rescue for this development line is built from the exact frozen v0.5.2 production application candidate with a forward-only rescue versionCode.

## 0.3.0 — production

- Production phone-rental enforcement: Device Owner lock-task allowlist, server-authoritative lease, coin targeting, app policy, phone-admin password verifier and PC QR provisioning.
- Managed ESP8266/ESP32 controller policy with verified first-boot Wi-Fi setup and reconnect fallback.
- Permanent production GitHub Release assets for supported router/SBC/x86/Android/controller targets.

- Added capability-tier architecture: Lite for constrained routers, Standard for Orange Pi/SBC deployments and Full for x86 systems.
- Began public-tree cleanup and neutral reference documentation.
- v0.3 implementation plan adds hardened admin sessions/lockouts, configurable portal builder/templates, ESP32, Linux GPIO/Orange Pi support, BlazeRental Android management and GitHub Release asset packaging.
- Successful targets remain publication-gated: no placeholder firmware or installer files are released.

## 0.2.0-rc.2 — 2026-10-04

- Final RC2 hardening: atomic persistent-state replacement, kernel flock serialization, durable coin-target/ESP pending-event recovery, local firewall-zone rules, repeated regression/stress gates and fail-closed clock synchronization checks.
- Reconciled publicly observable prepaid-hotspot behavior and open integration examples without redistributing closed commercial binaries.
- Replaced MAC-only balances with browser device-token accounts that survive private/random MAC rotation.
- Added server-side pause/resume with optional pause lifetime limit.
- Made coin events target-bound, signed and idempotent across lost acknowledgements.
- Separated durable voucher-use markers from bounded coin replay history.
- Kept high-frequency Vendo heartbeat state in RAM while making short active coin-window records durable.
- Added dynamic IPv4/IPv6 walled-garden sets for provider hosts.
- Kept BlazePwifi forwarding subordinate to firewall4 policy.
- Added HTTPS-only local administration with local certificate generation.
- Bound local service listeners to the configured LAN address rather than WAN-facing wildcard addresses.
- Secured ESP8266 setup AP with generated WPA2 credentials and automatic shutdown after provisioning.
- Added automatic single-Vendo selection and explicit multi-Vendo selection.
- Added v0.1 state migration, crash-safe legacy claims, kernel-backed flock serialization, same-filesystem atomic replacement and concurrency/replay stress tests.
- Added ESP8266 LittleFS journaling for unacknowledged coin events.
- Added local firewall-zone service rules and clean uninstall removal.
- Added executable-mode auditing.
- Added verified Ruijie bootstrap/custom sysupgrade packaging and x86 BIOS/UEFI ImageBuilder outputs.

## 0.1.0-alpha.1 — 2026-10-04

- Initial BlazePwifi implementation.
- OpenWrt 25.12.x installer with apk package handling.
- nftables captive portal and paid-MAC authorization set.
- Persistent credit and session accounting.
- Configurable rate table.
- Client portal and token-protected admin status page.
- ESP8266 remote-Vendo firmware and authenticated API.
- Ruijie RG-EW1200G Pro v1.1 and x86_64 deployment profiles.
- GitHub Actions static validation and release-bundle workflow.
