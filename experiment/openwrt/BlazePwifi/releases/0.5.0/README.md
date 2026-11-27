# BlazePwifi v0.5.0 — Management Console & BlazeRental Launcher

BlazePwifi v0.5.0 is the first release built around the redesigned BlazeRental launcher model and the expanded BlazePwifi Management Console.

## BlazeRental v0.5

- Application branding is now **BlazeRental** with the LCM Blaze icon.
- Normal Launcher3 home pages are preserved.
- The custom-left area is owned by BlazeRental:
  - far-left BlazeRental / Insert Coin gate;
  - Notifications page beside it;
  - normal Launcher3 Home beyond the managed boundary.
- Unpaid Rental Mode fails closed: Home and All Apps cannot be entered.
- Paid time or **Use device as is** restores the normal launcher experience.
- Daily-driver mode can be selected during first setup without BlazePwifi enrollment.
- Notifications include **Clear All**.
- QR enrollment preview preserves camera aspect ratio and uses a stable scan frame.
- On-device admin brute-force protection now escalates and reapplies its penalty after reboot attempts.
- Device Owner, persistent HOME, Lock Task and existing managed-device restrictions remain the strongest deployment path.

## Management Console v0.5

The console is expanded into a real appliance-management shell with dedicated areas for:

- Dashboard
- Clients & Sessions
- Sales & Reports
- WAN & Internet
- LAN / VLAN / Wi-Fi
- Worldwide Remote Access
- Vouchers & Rates
- Rental Devices
- Coin Controllers
- Portal Designer
- Multimedia Manager
- BlazeGames Manager
- Storage
- Backups
- Tools & Terminal
- Alerts & Logs
- System & Security

Live v0.5 management functions include the existing rental/controller/voucher/portal controls plus hardware/runtime detection, storage visibility, WireGuard/ZeroTier capability/status reporting, and allowlisted diagnostic commands (Ping, traceroute, DNS, routes, interfaces, Wi-Fi, storage, uptime, and a speed test when a supported local helper is installed).

Advanced modules remain capability-aware: controls that depend on optional hardware, storage, VPN packages or a configured remote hub do not pretend that missing capabilities are available.

## Customer portal

- Preserves a simple child-friendly Insert Coin / Buy Time / Voucher first view.
- Adds **Movies** and **Games** entry points for locally managed content.
- Movies/Games pages distinguish free access from content requiring active, unpaused paid time.
- Adds safe status information such as hotspot VLAN, configured speed limit, router load, available RAM and uptime.
- Default Blaze portal remains the intended undeletable/fallback portal.
- Core UI remains framework-light: no mandatory Bootstrap, jQuery or CDN runtime.

## Security posture

v0.5 is designed for strong abuse resistance rather than making impossible guarantees such as “DDoS proof.”

- authenticated roles and CSRF checks for management state changes;
- allowlisted diagnostic commands with validated targets and bounded output;
- escalating on-device admin lockouts;
- no captive-portal terminal access;
- remote Management Console is intended to stay off public WAN and be reached through configured private WireGuard or ZeroTier paths;
- Device Owner remains the recommended rental-phone deployment mode.

## Signing

BlazeRental keeps package ID `com.blazesystems.blazerental`.

The release process first attempts to use the locked v0.4 production certificate. If that identity is unavailable to GitHub Actions, the release must **not silently rotate certificates**. In that case the Release assets identify the Android TEST APK and unsigned release APK explicitly until the owner restores the locked signer.

## Validation

The release candidate must pass the exact-SHA BlazePwifi build matrix, source contracts, browser/security simulations, Android Device Owner emulator audit, firmware builds/simulations and candidate gate before publication.
