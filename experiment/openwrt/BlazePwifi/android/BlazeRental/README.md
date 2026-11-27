# BlazeRental Android client

Package: `com.blazesystems.blazerental`

Two installation modes are intentionally supported:

1. **Managed QR / Device Owner** — for freshly reset, owned/authorized rental phones. Android provisioning installs BlazeRental as the DPC. BlazeRental can then apply dedicated-device policies, persistent Home selection, lock-task allowlisting and supported user restrictions.
2. **Manual APK** — works without factory reset but does not become Device Owner. It is deliberately labeled lower-security because a normal user can potentially uninstall/disable/bypass it.

Rental time is server-authoritative. The client caches the last server time + lease expiry against Android's monotonic elapsed-realtime clock; after reboot the cached lease fails closed until the server is reached again.

The project does not claim to defeat bootloader unlock, recovery flashing, OEM service tools, or privileged exploits.
