# BlazePwifi v0.6.0-alpha.2 — PAID-SAFETY DEVELOPMENT / DISPOSABLE LAB ONLY

**DO NOT INSTALL ON LIVE CUSTOMER ROUTERS, ACTIVE VENDO OR PISONET CASHIERS, PAID RENTAL PHONES, OR ANY DEVICE HOLDING MONEY, CUSTOMER TIME, ACCOUNTS OR SECRETS. This is a real CI-compiled development prerelease, NOT production v0.6.0.**

This release publishes actual artifacts from one exact GitHub commit after the full build matrix and separately built Windows SoftTimer installer have both completed successfully at that exact SHA. The external release manifest lists the source SHA, workflow runs, each asset size/SHA-256 and explicit unsafe-production flags. If either pipeline fails, the release must not be published.

The *internal* OpenWrt application version remains **0.5.3**, native Android Launcher3 versionName **0.5.3** / versionCode **50300**, and Windows BlazePisonet SoftTimer **v0.4.0**. Do not misrepresent these internal packages as fully migrated, versioned 0.6.0 production builds. The Android archive contains CI TEST/development APK builds **NOT** verified against the owner's permanent Lineage-2 production signer. They cannot substitute for current/rescue production APKs or managed Device Owner provisioning on customers' phones. The 0.6-family overlay updater must continue to refuse unverified financial-state migration.

## Functional improvements since the frozen alpha.1 source

- **P0 Wi-Fi coin accounting:** No false successful coin-credit ACK after account write, rename or durability failure. Existing shared paid-state uncertainty marker now quarantines ambiguous Wi-Fi payments, including repeated retry attempts.
- **P0 hotspot payment windows:** Repeated start by the same device reuses its live target nonce instead of invalidating already-inserted coins. Target creation/closure checks storage failures and rejects conflicting rental/other-device windows.
- **P0 captive voucher/session actions:** Buy-time, pause, resume, disconnect and voucher redemption check persistent money/session write results and refuse success or network unlock when storage is uncertain. Client binding also checks account persistence before legacy cleanup.
- **P0 coin replay lifetime:** New target-scoped coin receipt IDs are kept for the entire active payment target even when historical display-receipt limits are exceeded. A synthetic signed-coin test accepts 12 events against a history setting of 8, credits a voucher, rejects replay of the oldest signed event and compacts expired display history. These are *software-level* safeguards; they are not a v1 migration for historical old receipt formats or a physically tested exact-once powercut protocol.
- **P0 PisoNet member replay:** Signed member bank, restore and transfer replay responses refuse to acknowledge disputed financial state until an authenticated operator reconciles it.
- **P1 updater extraction:** Reject archive traversal, special/link members, duplicate tar names, duplicate/malformed manifests and escaping destinations before unpacking. Existing v0.5.x update/rollback compatibility and enforced 0.6 upgrade refusal are retained.
- **Product UX inherited from alpha.1:** Native Launcher3-based Android admin/binding security information; separate factory-reset Device Owner QR from lower-trust standard binding QR; HTTPS/certificate-pin checks and expiring hidden secrets; original offline lightweight BlazeFusion operator console and portal redesign.

All specific code and tests are tracked in draft GitHub [PR #30](https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/30), `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` and canonical `docs/handover/CURRENT_STATE.md`. Targeted accounting and archive hardening CI passed on development source before assembling this release; the publish workflow independently requires **fresh exact-SHA Full+Windows CI**, not historical green checks.

## Actual downloadable lab assets (only when the GitHub release exists)

Nine nonempty `*-LAB-ONLY.zip` packages from GitHub Actions: OpenWrt core bundle, Android CI TEST, ESP8266, ESP32, Ruijie RG-EW1200G Pro firmware, x86_64 firmware, Orange Pi Zero 3 firmware, current OpenWrt development update bundle, and Windows BlazePisonet SoftTimer x64 installer bundle. `RELEASE_NOTES.md`, `MANIFEST.json` and `SHA256SUMS` provide provenance. Other Orange Pi optional CI images are build evidence and are **not** falsely listed as release assets.

These packages are for isolated disposable benches with no customer credits. Never flash vendor-specific recovery images without verifying model/board revision and a known-good physical recovery route. The Windows EXE is an installer candidate, not proof that USB-RS232/COM signals or kiosk anti-bypass behavior work on all PCs.

## Why production v0.6.0 is still blocked

1. **No unified authenticated crash-atomic paid journal** yet for member, rental and hotspot balances plus original durable receipts under unexpected power loss. Fail-closed uncertainty containment improves safety but is not all-or-nothing physical durability.
2. **No real customer-v1 irreversible-risk elimination:** paid account, member, voucher, rental identity, controller event/replay history, PIN/credentials and network configuration must be migrated under quiescence using verified encrypted backup and rollback. Old receipt IDs that aged out cannot be reconstructed automatically.
3. **No permanent owner Lineage-2 signed current AND higher-version-code rescue Android APK proof.** No completed OEM factory-reset Device Owner QR provisioning, anti-bypass and trusted on-device admin recovery matrix.
4. **No physical target acceptance:** Ruijie, x86 BIOS+UEFI, Orange Pi, ESP pulse electronics, Windows serial and Android phones must pass actual install/reboot/WAN/VLAN/30-device concurrent paid soak/power cut and recovery. GitHub Actions, QEMU, mocks and browser tests are not hardware evidence.
5. Runtime, installer and Android version metadata remain at pre-0.6 internal versions; current v0.6 update is intentionally blocked. Production tag `v0.6.0` must not be created until all P0 and signing/hardware gates pass.

**GitHub development branch:** `blazepwifi-v0.6.0-audit-foundation` · **Frozen prior prerelease:** `v0.6.0-alpha.1` · **Planned actual lab tag:** `v0.6.0-alpha.2`. Previous official v0.5.2 releases, Standalone Rental and alpha.1 must remain unchanged.
