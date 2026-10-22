# BlazePwifi Project Handover

**Last updated:** 2026-10-22  
**Repository:** BlazingSystems/BlazingSystems-Experiments  
**Development state:** BlazePwifi v0.5.1 is published and fully build-validated as a prerelease from exact candidate `65f87d775793a1fdc09a9522cf752349f68c3b41`. Transactional no-reflash updates and rollback are included. Android production signing remains blocked only by unavailable exact locked v0.4 signing material.

## Current focused Rental audit — 2026-10-22

**Immutable latest provisioning prerelease:** `v0.5.2-rental.2-rc.10`, exact release target `047b4ac798e75b69d324eb802013fdaf7695bb91`. The dedicated Rental release run `39742380175` passed. This is TEST-signed for device provisioning and must not be represented as a production Device Owner release.

**Unreleased continuation branch:** `blazepwifi-rental-v0.5.2-rc11-network-audit`, based on RC10. Security transport commit `4f3f5cf75ff33ab8ada1a110858ea3f58bdc853f` rejects HTTP redirects, limits all rental API JSON responses to 256 KiB, and guarantees connection cleanup. The JUnit suite covers oversized, exact-limit and normal responses plus stream closure. CI started at run `39745189497`; consult the latest run on this branch for its actual status before claiming success.

**Remaining release blockers:** physical Android Setup Wizard provisioning evidence, locked long-term production APK signing continuity and target-specific GMS/OEM compatibility. Do not upgrade a production-signed managed device with a TEST-signed RC APK. Continue only the Rental provisioning/enrollment transport and signing boundaries in this branch; other BlazePwifi subsystems should remain untouched.

**Detailed log:** `docs/handover/2026-10-22-rental-rc11-transport-audit.md`.

## Active v0.5.1 maintenance target

The owner requested a maintenance release that eliminates full-system reflashing for ordinary feature/revision upgrades and adds safe rollback for BlazePwifi and BlazeRental.

Implemented on `blazepwifi-v0.5.1-implementation`:

- Transactional BlazePwifi overlay updater with exact SHA-256 verification.
- Configurable HTTPS update source, size bound, stability grace and rollback retention.
- Last-known-good snapshots before file replacement.
- Immediate health-check rollback and boot-health rollback guard.
- Manual rollback from Management Console → Updates & Recovery.
- Idempotent configuration migration; normal feature bundles do not overwrite persistent operator/session state.
- One-time v0.5.0 → v0.5.1 no-reflash bootstrap updater.
- Build-time `BlazePwifi-v0.5.1-update.tar.gz` generation.
- BlazeRental v0.5.1 version code `50100`.
- BlazeRental managed updater verifies SHA-256, package name and installed signing identity.
- Previous APK/version metadata retained; new build becomes stable only after a 30-second launcher health window.
- Known-good v0.5.0 rollback rescue is rebuilt from exact RC9 source `66e159b65b6d8fb5f74dd981dc73d46db7229adc` using recovery-only version code `50101`.
- Repeated failed boots while a Rental update remains pending can stage the configured rescue APK.
- Native Rental Admin update/check/rollback controls.
- Central Rental Update Manager in the BlazePwifi console.
- Locked v0.5.1 production signer workflow signs both current and rescue APKs with the exact existing certificate and refuses rotation.
- v0.5.1 release workflow supports validated prerelease publication if the locked signer remains unavailable.

Full firmware/sysupgrade remains reserved for base-system changes such as kernel, bootloader, partition/ABI or filesystem changes that cannot safely be delivered as an overlay.

## Current v0.5.1 release status

- GitHub Release: `v0.5.1` — **published prerelease**
- Release ID: `404404262`
- Release page: `https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.1`
- Exact validated candidate: `65f87d775793a1fdc09a9522cf752349f68c3b41`
- Validated build run: `37425063793` — **PASS**
- Validate/static/security/integration/stress: PASS.
- Transactional update/rollback regression: PASS.
- BlazeRental v0.5.1 update contract: PASS.
- Android APK build: PASS.
- Android Device Owner emulator: PASS.
- Browser, ESP8266, ESP32, Ruijie, x86 and required Orange Pi simulations: PASS.
- Final candidate gate: PASS.
- Release workflow run: `37426030884` — **PASS**
- Release target remains exact candidate SHA `65f87d775793a1fdc09a9522cf752349f68c3b41`.
- Update assets include:
  - `BlazePwifi-v0.5.1-update.tar.gz`
  - `BlazePwifi-v0.5.1-update-bootstrap.sh`
  - `BlazePwifi-v0.5.1-update-bootstrap.sh.sha256`
- Android validation/recovery assets include:
  - `BlazeRental-v0.5.1-TEST.apk`
  - `BlazeRental-v0.5.1-release-unsigned.apk`
  - `BlazeRental-v0.5.0-rescue-for-v0.5.1-TEST.apk`
  - `BlazeRental-v0.5.0-rescue-for-v0.5.1-release-unsigned.apk`
- Locked signing run `37425929657` failed safely at `Restore exact locked v0.4 production identity` because the exact keystore / `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` remains unavailable.
- The signing workflow refused certificate rotation. Therefore production `BlazeRental.apk` and signed rescue APK are intentionally absent.
- Locked production fingerprint remains:
  `C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`
- Canonical release log:
  `docs/handover/2026-10-06-v051-release-published.md`

## v0.5.1 main integration status

- BlazePwifi v0.5.1 is integrated into `main`.
- Published release candidate remains `65f87d775793a1fdc09a9522cf752349f68c3b41`.
- Published release build run: `37425063793` — PASS.
- Published release workflow: `37426030884` — PASS.
- Reconciled main integration SHA: `e081c6bdfc41d22ac07f918c4cbc62a745bca883`.
- Reconciled integration build run: `37426701445` — PASS, including Android Device Owner emulator, x86 QEMU and final candidate gate.
- Pull request `#14` — merged.
- Main merge commit: `1aa8926563e6dccb6a512a035e8f6f662b997d57`.
- Main merge tree: `f1c0194f8039577bad88a6e93b02d9b837e228c2`, exactly matching the green integration tree.
- Post-merge main build run: `37427339687` — PASS, including Android Device Owner emulator, x86 QEMU and final candidate gate.
- All 19 newer main-only standalone-rental/release files were preserved byte-for-byte.
- Superseded conflicting PR `#13` was closed without merging.
- GitHub Release `v0.5.1` remains pinned to exact candidate `65f87d775793a1fdc09a9522cf752349f68c3b41`; main integration did not retag or rewrite the release.
- Production Android signing remains blocked only by unavailable exact locked v0.4 signing material.

## Main branch integration status

- Full BlazePwifi v0.5.0 implementation is integrated into `main`.
- Conflict-resolved integration SHA: `09710a6d093f125a444c86bc686985edbfc89553`.
- Integration CI run: `37396023917` — PASS, including Android Device Owner emulator and final candidate gate.
- Pull request: `#12` — merged.
- Main merge commit: `06ddc5909b178d316f0f4d6fb8104f64da9a1be9`.
- The merge tree is exactly `d8fe2e6b6fca5ee3f619bc1d2e8ab35c4abcc850`, the same tree validated on the integration branch.
- All 16 main-only paths were preserved byte-for-byte, including the offline preview artifacts, handover logs, and unrelated Easymode encrypted-release files.
- Superseded conflicted PR `#11` was closed without merging.
- The `v0.5.0` tag/release remains pinned to validated RC9 candidate `66e159b65b6d8fb5f74dd981dc73d46db7229adc`; integrating code into main did not move or rewrite the release tag.
- Production Android signing remains intentionally blocked until the exact locked v0.4 signer is restored.

## Current v0.5.0 release status

- GitHub Release: `v0.5.0` — **published prerelease**
- Release ID: `403831689`
- Release page: `https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/v0.5.0`
- Exact validated candidate: `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- Candidate branch: `blazepwifi-v0.5.0-rc9`
- Validated build run: `37326542666` — PASS
- Final candidate gate: PASS
- Release workflow run: `37327843195` — PASS
- Release-stage artifact: `11352224246`
- Tag `v0.5.0` points exactly to the validated RC9 commit.
- `RELEASE-MANIFEST.json`: `candidate_gate=passed`, `production_signed=false`, `signing_run_id=0`.
- Android release assets currently include:
  - `BlazeRental-v0.5.0-TEST.apk`
  - `BlazeRental-v0.5.0-release-unsigned.apk`
- A production `BlazeRental.apk` is intentionally absent until the locked v0.4 signer is restored.
- Locked signing run `37327439782` failed safely because `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` / exact keystore was unavailable; it refused certificate rotation. A second attempt on 2026-10-06 (`run_attempt=2`) reached the same protected restore step and failed for the same reason, again without altering the release or rotating the certificate.
- Locked production fingerprint remains:
  `C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`
- Canonical final release log:
  `docs/handover/2026-10-05-v050-release-published.md`

## Current target

BlazePwifi is being developed as a complete PisoWiFi + Android rental-device platform with a full management console, customizable captive portal system, coin/Vendo controllers, vouchers, sales, networking/WAN/LAN/VLAN management, backups, multimedia, BlazeGames management, and BlazeRental Launcher3 integration.

## Current BlazeRental direction

Approved redesign direction:

- Rename the launcher/app from Rootless Pixel Launcher branding to **BlazeRental**.
- Use the approved LCM/BlazeRental icon family for APK/app branding and wider Blaze ecosystem branding where appropriate.
- Restore normal Launcher3 behavior instead of the current three-page rental replacement.
- Far-left page: BlazeRental / Insert Coin portal.
- Next page: Notifications.
- Then normal Launcher3 home pages.
- Swipe-up All Apps is allowed only while rental time is valid or `Use device as is` is enabled.
- Unpaid rental mode fails closed to the BlazeRental Insert Coin page.
- `Use device as is` must be available as a daily-driver mode and must not require BlazePwifi enrollment.
- Notifications page needs Clear All.
- On-device admin must be redesigned as a polished native Android management UI.
- QR scanner must preserve camera aspect ratio and use a stable scan frame.
- Rental Insert Coin appearance/sounds must be customizable from the on-device admin.

## Portal / management-console direction

- Core UI must not depend on Bootstrap, jQuery, CDN, or heavy framework runtimes.
- Factory Blaze portal is permanent/undeletable and acts as fallback.
- Portal Designer must support Add Portal Template and custom HTML/CSS/JS/media/sounds.
- LPB-style behavior should be supported through a compatibility layer without copying LPB visual design.
- Default portal must be child-friendly at first glance and expose richer safe network/device/system details when scrolled.
- Management Console should become a complete operating console, not a small admin page.
- Console richness includes Alerts, Scheduler/Automation, Announcements, Theme/Branding management, Audit Logs, Role-based Accounts, Import/Export, Template Sandbox/Safe Preview, API/Webhooks, Hardware Capability page, File/Asset Manager, Recovery/Fallback tools, Data Usage/Quota, Reports, Search/Quick Actions, Notes/Tags, and Multi-profile/Presets.
- Add a dedicated **Tools** module: ping, traceroute, DNS test, speed test, WAN reachability, port check, NTP test, Wi-Fi scan, interface diagnostics, controller tests, latency/jitter/packet-loss testing, safe local discovery, logs, service tools, storage cleanup, and diagnostics export.


## Management Console terminal / command tools

Approved design direction:

- Add a **Terminal / CMD** area to the Management Console.
- Do **not** expose an unrestricted web shell by default.
- Provide two levels:
  - **Safe Commands**: curated/allowlisted commands and guided tools for common admin tasks.
  - **Advanced Terminal**: optional owner-only shell with explicit enablement, re-authentication, timeout, audit logging, and strong rate/concurrency limits.
- Safe Commands should cover common operations such as:
  - ping, traceroute, nslookup/dig, route/ip status;
  - interface/WAN/LAN/VLAN status;
  - Wi-Fi scan/status;
  - storage/mount/USB status;
  - process/service status;
  - log viewing/tailing;
  - package/version checks;
  - network diagnostics;
  - controller diagnostics;
  - read-only hardware/runtime inspection.
- Dangerous/destructive actions should use dedicated Management Console controls or guarded command wrappers rather than raw arbitrary shell wherever practical.
- Advanced Terminal must be owner/admin-role restricted, disabled by default on Lite/public-facing deployments, and protected with:
  - fresh password re-authentication;
  - short-lived terminal session;
  - CSRF/session binding;
  - command audit history;
  - output/time limits;
  - idle timeout;
  - concurrent terminal/session limits;
  - brute-force/rate-limit protections;
  - no anonymous or portal-side access;
  - optional LAN-only/local-management restriction.
- Terminal access must never be exposed to captive-portal users.
- On constrained OpenWrt devices, prefer a small streamed command runner rather than a heavy full browser terminal emulator.


## Remote monitoring / remote management

Approved design direction:

- Add a dedicated **Remote Access / Fleet Management** section to the Management Console.
- The primary user goal is **true worldwide access**: the owner must be able to open and manage their BlazePwifi/PisoWiFi system from anywhere on the Internet (for example from mobile data, another city, or another country) without needing to be on the local LAN.
- The preferred UX is a normal browser-accessible remote console reached through the configured private overlay/VPN path, not direct public-WAN exposure of the admin page.
- Remote monitoring/management should work even when the BlazePwifi site is behind NAT/CGNAT, provided one of the supported outbound tunnel methods is configured.
- Do not hard-code a vendor, account, endpoint, address, key, subnet, route, or management scope. All remote-access parameters must be owner-configurable.
- Remote access is **disabled by default** until the owner explicitly configures it.
- When Remote Access is enabled, offer exactly two first-class modes:
  1. **WireGuard VPN — Recommended/default selection**
     - preferred for BlazePwifi because it is lightweight, OpenWrt-native/well-supported, owner-controlled, and suitable for site-to-site or outbound-to-hub management;
     - support a BlazePwifi node behind NAT/CGNAT by allowing it to initiate an outbound WireGuard tunnel to an owner-controlled hub/VPS/router;
     - configurable endpoint/FQDN, port, peer/public keys, optional preshared key, tunnel address, allowed IPs/routes, persistent keepalive, DNS, MTU, reconnect/health-check and management subnets;
     - private keys remain local and are never displayed after creation/export unless the owner explicitly rotates/reprovisions them.
  2. **ZeroTier — Easy-mesh alternative**
     - intended for simpler NAT/CGNAT traversal and multi-site mesh enrollment;
     - configurable Network ID, authorization state, managed IP/routes, local interface/firewall scope, low-bandwidth option where supported, and reconnect/health state;
     - no hard-coded ZeroTier account/network dependency.

- Monitoring and management permissions must be independently configurable:
  - Remote Monitoring only (read-only metrics/status);
  - Remote Management (configuration changes);
  - Remote Terminal (separate advanced permission, off by default).
- Remote-access scope should be configurable per service/module:
  - Dashboard/status;
  - alerts/events;
  - clients/sessions;
  - sales/reports;
  - backups;
  - portal/templates;
  - rental devices;
  - controllers;
  - network/WAN/LAN/VLAN;
  - system/firmware;
  - tools;
  - terminal.
- Add optional fleet-style status:
  - node name/site/location label;
  - online/offline;
  - last seen;
  - WAN health;
  - tunnel health/last handshake;
  - public/overlay/tunnel IPs where appropriate;
  - CPU/RAM/storage/temp;
  - active clients/sessions;
  - controller/rental-device health;
  - firmware/version;
  - alerts and backup status.
- Configurable heartbeat/refresh interval, offline-alert threshold, reconnect behavior, telemetry retention and alert severity.
- Remote management must bind to LAN/VPN/overlay interfaces only by default and must **not expose the Management Console directly to the public WAN**.
- Support configurable allowlists for remote management source addresses/subnets.
- Re-authentication should be required for high-risk actions such as firmware updates, factory reset, backup restore, credential/key changes and Advanced Terminal.
- Maintain complete audit logging of remote sessions and state-changing actions.
- Rate limits, session limits, timeouts and abuse controls apply equally to remote access.
- If the VPN/overlay fails, local LAN management and the captive portal must continue working normally.

## Networking / operations requirements captured

- Multiple WAN modes including Ethernet, WISP when Wi-Fi hardware is available, USB Ethernet, dual-WAN load balancing and failover.
- LAN/PisoWiFi AP modes including VLAN, second Ethernet, USB Ethernet, bridge/router modes.
- Voucher generator/designer/export.
- Rental settings and QR provisioning.
- Rental customization.
- Sales reporting.
- Device management.
- Manual/automatic backups with retention limits, download/import/restore.
- Sessions, rates, controllers, diagnostics, system/security and hardware-capability-aware controls.

## Wi-Fi portal multimedia / games direction

Approved portal additions:

- Wi-Fi portal may expose **Movies/Multimedia** and **Games** sections.
- These sections apply to the Wi-Fi portal, not the BlazeRental launcher unless explicitly added later.
- Multimedia page contents are entirely controlled by the administrator.
- Each media item can be configured as:
  - free to view, or
  - requires an active paid session with time actively running (paused time does not qualify).
- Add a **Multimedia Manager** to the Management Console:
  - detect removable USB storage when available;
  - allow supported internal/SSD/SD storage on larger builds;
  - choose multimedia storage target;
  - upload/import/delete/rename media;
  - folders/categories/collections;
  - poster/thumbnail/metadata management;
  - free-vs-paid-session access policy per item/category;
  - storage capacity/free-space/health view;
  - rescan/index storage;
  - safe eject/remount where supported;
  - media preview;
  - browser-native streaming with HTTP range support where practical;
  - no mandatory server-side transcoding on Lite targets.
- Add a **BlazeGames Manager** using the existing BlazeGames/offline arcade-emulator HTML project:
  - manage ROMs/content made available to users;
  - add/remove/enable/disable games;
  - categories/favorites/order/cover art/metadata;
  - storage target selection;
  - free-vs-active-session access policy;
  - emulator/core compatibility metadata;
  - per-game launch/test;
  - save-state/storage policy where supported;
  - keep Lite targets lightweight.
- Only administrator-supplied/licensed media and ROMs should be distributed; BlazePwifi should not ship copyrighted third-party content by default.

## Security / abuse-resistance requirements

The system must be designed to strongly resist brute-force and denial-of-service abuse, while avoiding claims of being literally “brute-force free” or “DDoS proof.”

Required controls include:

- escalating admin/login lockouts and rate limits;
- persistent lockout state where appropriate;
- strong password verification and secure secret storage;
- role/session controls, CSRF protection, nonces on state-changing APIs;
- request/body/upload size limits;
- connection/concurrency limits suitable for the hardware;
- per-client/IP/session token-bucket throttling for sensitive endpoints;
- login/API backoff and abuse detection;
- upload quotas and storage quotas;
- bounded logs and bounded backup/media retention;
- timeouts against slow/idle connections;
- fail-closed rental and policy behavior;
- static asset caching and lightweight portal rendering for constrained devices;
- audit/security event logging;
- safe recovery path for the owner.

## v0.5.0 implementation state

Implementation resumed by explicit owner instruction on 2026-10-05.

Current branch: `blazepwifi-v0.5.0-implementation`

Completed in the first v0.5 launcher milestone:

- Version bumped to 0.5.0 / Android versionCode 50000.
- User-visible Rootless Pixel/Launcher3 branding replaced with BlazeRental.
- Approved LCM icon added and wired as the APK launcher icon.
- Added one authoritative `canUseDevice()` gate: unrestricted OR valid paid lease.
- Added `BlazeLeftPanel` using Launcher3 custom-left content rather than deleting normal workspace pages.
- Unpaid rental state blocks leaving Blaze content for normal Home.
- Paid/unrestricted state restores normal Launcher3 chrome/interactions.
- Notifications gained Clear All support.
- First setup now offers `USE DEVICE AS IS · NORMAL LAUNCHER` without BlazePwifi enrollment.
- Legacy Google overlay is disabled so Blaze owns the custom-left gesture surface.

Next: complete v0.5 tests/emulator flow, QR scanner/native admin polish, rich Management Console/portal modules, then exact-SHA build and v0.5.0 release staging/publish.

## Last validated application candidate

BlazePwifi v0.5.0 RC9:

- Candidate SHA: `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- Build run: `37326542666` — PASS
- Candidate gate: PASS
- Android Device Owner emulator: PASS
- Browser/platform simulations: PASS
- Published as GitHub prerelease `v0.5.0`.

Previous v0.4 validated candidate remains `d2ee5e0c0493500ce6a0578b9cad5da0775be65e` with build run `37287301792`.

Do not replace or relabel the v0.5 TEST APK as production-signed. Production Android upgrade compatibility requires the existing locked v0.4 signing certificate.

## Latest preview artifact

An offline single-file Management Console + PisoWiFi Insert Coin + BlazeRental Insert Coin UX mockup was packaged as:

`preview/BlazePwifi_Offline_Management_Console_Preview.zip`

Mock login:

- username: `admin`
- password: `blaze1234`

This is a design mockup only and does not change production behavior.

## Resume rule

Before continuing implementation in a future chat:

1. Read this file.
2. Read the newest file in `docs/handover/`.
3. Inspect the current Git history and active implementation branch.
4. Reconcile repository state with these approved decisions.
5. Do not discard or redesign approved decisions unless the owner explicitly changes them.

## Logging rule

Update this handover at meaningful state changes: requirements, decisions, code/config changes, commits, tests, failures, fixes, workflow/build/release results, artifacts, blockers and exact next steps. Do not log every tool call.

### Mandatory success logging

Every successful milestone must also record:

- What changed and why.
- Exact files/areas touched.
- Commit SHA(s).
- Tests/audits performed.
- Successful workflow/build/release IDs when applicable.
- Any remaining known risks or limitations.
- Exact next recommended action.
- A ready-to-copy **Audit & Reconcile prompt** for a new chat.

Use this default prompt structure and specialize it to the latest milestone:

```text
@GitHub Reconcile and continue the BlazePwifi project from the repository state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest file under experiment/openwrt/BlazePwifi/docs/handover/.
3. Inspect the recent Git history, current implementation branch, relevant workflow results, release/assets, and files changed by the latest milestone.
4. Audit the latest successful change instead of assuming it is correct. Check for regressions, incomplete wiring, security/UX conflicts, stale documentation, and mismatches with approved requirements.
5. Reconcile repository state with the approved project target and decisions in the handover logs.
6. Preserve completed/approved decisions unless the owner explicitly changed them.
7. If the latest success has a test/build/release artifact, verify the exact SHA/run/artifact before building on top of it.
8. Continue from the exact NEXT ACTION recorded in the newest handover log.
9. Update PROJECT_HANDOVER.md and add a new dated handover log after every meaningful success, failure, blocker, or design change.
10. For every successful milestone, include a new Audit & Reconcile prompt in the handover log for the next chat.
```

Failures should also be logged when meaningful, including reproduction/evidence, suspected cause, what was tried, and the safest next action.
