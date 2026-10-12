# EasyMode 7.0 compatibility

| Platform | Delivery | Verification / restriction |
|---|---|---|
| OpenWrt 24.10.8 | Core IPK + one of six edition IPKs | Linux CI integration gate required before release |
| Other OpenWrt 24.10 | Same interpreted packages if dependencies are available | Exact release NOT HARDWARE VERIFIED |
| x86/64 generic BIOS | Combined squashfs disk image | Official pinned ImageBuilder; QEMU boot gate |
| x86/64 generic UEFI | Combined squashfs disk image | Official pinned ImageBuilder; QEMU/OVMF boot gate; Secure Boot not configured |
| R281 notion,r281 | Package update only | Isolated ucode/collector/rule syntax tested on 24.10.8; installation NOT HARDWARE VERIFIED |
| EW1200G Pro | Package only if the runtime matches | Exact board revision/profile not verified; no firmware image |
| Orange Pi / other SBC | Package only if the runtime matches | No verified SBC profile/toolchain in the existing toolkit; no image produced |
| Chaos Calmer / older OpenWrt | Not supported | Required ucode/rpcd runtime unavailable; do not force-install |
| APK-only OpenWrt | Not supported by these IPKs | No validated APK signing/build path; installer stops without changes |

No BIN is interchangeable across routers. PC combined images are entire disk images, not R281/TFTP/router-factory firmware. Writing one to a disk destroys that disk's existing contents; use a separate target disk and preserve recovery media. Do not use a PC image on a router. See official OpenWrt x86 installation guidance for matching BIOS/UEFI boot. Keep your original image and a settings backup for rollback.

Firmware is an unofficial EasyMode customization of OpenWrt, not manufacturer-signed firmware. SHA-256 identifies the published artifacts; the upstream x86 trailer is not a certificate of device compatibility.

## Measurement restrictions

- WAN counters include network overhead, and only count observations since monitoring started. Billing totals are estimates, not provider invoices. The configurable cap is an all-WAN advisory threshold, not a per-provider quota or access enforcement rule.
- Five-minute WAN bins provide a bounded recent window; daily/device/domain reports use UTC day buckets. Capacity and retention trimming are disclosed in the API.
- Sampled per-device counters can miss expired entries, overflowed bounded sets and collection gaps. No installed app or person identity is claimed. Randomized MACs remain separate identities.
- Standard flow offloading prevents detailed accounting and is left unchanged. Aggregate interface accounting remains available; vendor accelerators can also affect visibility.
- AP/switch hardware bridge forwarding may bypass Linux counters. Only visible link/client measurements are displayed.
- Domain logging requires one dnsmasq instance. Encrypted DNS, VPNs, CDNs, connection reuse and unavailable observations leave traffic unknown. Advanced DPI, exact URL history and TLS interception are not provided.
- Cellular provider metrics remain available through the established management interface where its modem integration supports them. Monitoring does not claim a universal modem AT-command implementation.
- Built firmware retains the application through factory reset, but reset intentionally restores defaults and removes history/settings. Ordinary package installations do not become reset-proof merely by installing an IPK.
