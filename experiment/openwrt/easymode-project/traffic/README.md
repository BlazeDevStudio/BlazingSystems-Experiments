# EasyMode 7.0.2 — Traffic Intelligence

Release candidate under validation. Do not infer production readiness from a filename.

One lightweight ucode collector and plain JavaScript dashboard serve Generic, AP, Router, Cellular, Switch and PC editions. Existing EasyMode management is preserved. Open `/traffic/` and use the OpenWrt administrator credentials; no password is bundled.

## Install and recover

The offline archive contains real architecture-independent OpenWrt **IPK** packages for the 24.10 runtime. It assumes the dependencies listed by `install.sh` are already installed from the matching device feed. It does not contain target-specific dependency binaries. Extract one edition archive and run `sh install.sh` on the router, or run `Update-EasyMode.bat` on Windows with OpenSSH available. The script backs up settings before installation. Firmware flashing is a separate deliberate action.

No `.apk` package is published until an APK toolchain/signature and clean install are verified. An Android APK is unrelated. Older OpenWrt including Chaos Calmer cannot run this ucode subsystem and is rejected. No R281 or EW1200G Pro image is implied by the universal package.

Upgrade: install the core and exactly one edition. UCI configuration is preserved by opkg. Changing edition requires removal of the previous edition marker package; retain the core. Uninstall the edition and `easymode-traffic` through opkg; the service stops, its observer table is removed and owned DNS logging is restored. Private history remains in `/etc/easymode-traffic` unless deleted in Settings or deliberately removed by the administrator. The pre-install settings archive is private and must not be published.

## What is measured

- WAN receive = download, transmit = upload. Logical WAN/IPv6 interfaces sharing a device are deduplicated; selected parent interfaces are rejected when a lower child is also selected. Configure logical WAN/LAN names for unusual layouts.
- WiFi counters measure local link activity separately. Bridged AP/switch editions do not fabricate internet consumption.
- Detailed accounting is opt-in, bounded, sampled nftables counters in an isolated observer table. No packet verdict, NAT setting or acceleration setting is changed. Standard flow offloading disables detailed measurement; vendor accelerators may also limit it. Expired/full counters and collection gaps cause undercount and are disclosed.
- Domain observations are off by default. Enable only after notifying users. A local DNS service restart is required when changing its logging. One dnsmasq instance is supported. Observations reuse the existing bounded OpenWrt RAM log, avoiding an unbounded tmpfs file; queries remain visible in administrator system logs until the ring rotates, separately from EasyMode history deletion. Client/IP DNS associations expire after 60 seconds; shared addresses remain unknown. DNS queries are not proof of visits. Encrypted DNS, VPNs, CDNs and connection reuse limit attribution. No TLS interception, URLs or content are collected.
- Application names are inferred service categories, never claims about installed apps. Advanced DPI is not bundled.
- Daily history uses UTC, with configurable retention and capacity. State is private, bounded and checkpointed every 30 minutes; recent history can be lost on sudden power loss. Billing warnings do not enforce quotas.

## Security

Every measurement API uses rpcd administrator ACLs. JSON requests carry a session bearer, not ambient cookie authentication. The UI requires a password and does not ship credentials. Same-origin requests, output escaping, bounded validated settings, CSV formula protection and private files protect collected metadata. Do not expose router administration directly to the internet. No external analytics or cloud tracking is used.

## Verification and source

See `HANDOVER-v7.md`, `traffic/TEST-REPORT.md` and GitHub Actions for exact tested status. Package construction is deterministic Python tooling on the build host; Python/Node are not installed on the router. Firmware uses the official pinned OpenWrt ImageBuilder only for documented profiles. Physical hardware installation is **NOT HARDWARE VERIFIED** unless explicitly recorded.
