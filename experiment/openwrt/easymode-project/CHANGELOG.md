# Changelog

## 10.0.0 — R281 application profile (2026-10-19)
- Recreated the installed R281 EasyMode application as a versioned, reproducible source snapshot and reversible OpenWrt app-update archive.
- Added cellular IP-change count/time to the live health state for future outage correlation without retaining a full IP history.
- Removed stale high-priority unreachable default routes when no WAN has an address, avoiding a route blackhole after a transient DHCP lease transition.
- Restricted automatic SIM recovery to data-session reconnects; it no longer cycles RF or triggers cell re-registration. Manual radio operations remain administrator-controlled.
- Installer is limited to the verified Notion R281 / OpenWrt 24.10.8 profile, preserves UCI settings and private histories, and does not reboot or reload the network.
- Verified package preflight and installation on the R281. This is not firmware, does not survive factory reset on the stock image, and does not claim parity on other boards.

## 5.0.0-alpha.1
- Established EasyMode Core + six edition profile architecture.
- Added hardware/capability detector and non-destructive edition recommendation.
- Added transactional OpenWrt installer framework.
- Added offline HTML `/ubus` connection installer UI with truthful browser limitations.
- Added Windows PowerShell installer using built-in OpenSSH/SCP.
- Added package-manager detection for `opkg` and `apk`.
- Added static tests and release manifests.
- Preserved 4.1.4 as canonical real-hardware baseline pending 5.x verification.
