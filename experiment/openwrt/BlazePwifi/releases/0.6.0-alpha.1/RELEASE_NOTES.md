# BlazePwifi v0.6.0-alpha.1 — DEVELOPMENT / LAB TEST ONLY

**THIS IS A GITHUB PRE-RELEASE OF REAL CI-BUILT ARTIFACTS, NOT A PRODUCTION-APPROVED v0.6.0. DO NOT INSTALL ON CUSTOMER DEVICES, LIVE COIN/RENTAL SERVERS, OR ANY DEVICE WITH VALUABLE EXISTING TIME/CREDIT.**

The source code and firmware inside these test artifacts still report development version `0.5.3`; the Windows SoftTimer installer retains its own `0.4.0` version. This tag captures the v0.6 *development work*, not a versioned safe upgrade path. The supported updater intentionally rejects `0.6` until real balance migration is validated. Do not rename the binaries to 0.6, bypass guards, import real DBs, or use the Android CI/debug APK to update a currently managed rental phone.

## Actually included

The assets named `*-LAB-ONLY.zip` contain unmodified GitHub Actions build outputs from one exact branch commit, optionally including Ruijie/OpenWrt firmware image candidates, Orange Pi image candidates, x86 image candidates, ESP8266/ESP32 INO/BIN, OpenWrt package, Android CI TEST APK, current update bundle (with v0.6 safeguards), and Windows PisoNet SoftTimer installer. **Each asset is provided for separate isolated disposable-lab verification**, not deployed/field tested. Binary internals retain their original respective source version. A SHA-256 file and JSON asset manifest provide provenance. The release gate requires the complete Full Actions candidate matrix and same-SHA Windows build SUCCESS; it does not assert real hardware power-cut success.

## Improvements to evaluate

- Original lightweight/offline BlazeFusion admin command center, mobile responsive layout, keyboard-search navigation, accurate server connectivity status, and more legible operator controls inspired by (not copied from) MIT CoreUI and Metis dashboard design patterns.
- Two genuinely different rental QR generation pathways: ordinary on-device binding versus factory-reset managed Android Device Owner setup, with HTTPS/certificate-pin and APK-checksum metadata validation on the managed route. Tokens hidden in the browser unless deliberately revealed, QR expiry/close clearing, stale response defense.
- Native Launcher3-based BlazeRental on-device administrator security panel showing management mode, enrollment, server transport and certificate trust, without exposing device secrets. Managed Device Owner operation fails closed when server certificate pin is absent.
- Development-only paid replay and receipt-error containment tests; the **real runtime financial journal is not crash atomic**. A persistent uncertainty marker prevents blind retries but cannot guarantee paid time is not ambiguous after a power loss.

## PRODUCTION BLOCKERS — why this cannot yet be v0.6.0

1. Member/rental and ordinary coin paid changes require a single authenticated, crash-recoverable, exact-once durable journal; current member/rental error path may leave an altered balance behind a quarantine marker.
2. Existing 0.5.x accounts, v1 controller IDs, lease records, vouchers and protected admin credentials require a *proven*, quiesced, backed-up/recoverable migration. The updater correctly prevents unsafe 0.6 upgrade.
3. Managed Android needs source-compatible owner-controlled permanent **Lineage-2 signed current AND rescue** artifacts, verified fingerprints and hardware Android Setup Wizard enrollment. **CI TEST APK is not compatible with production update/signing identity.**
4. Actual supported routers, Orange Pi, legacy/UEFI x86, ESP coin controllers and rented Android phones need first-install + restart + power-cut recovery + at least 30-device test acceptance, including all payment boundaries. CI/QEMU/Playwright is not physical hardware signoff.
5. Source version and Android versionCode need the final production bump *after* migration/signing/hardware acceptance.

## Source, inspection and issue tracking

Repository: https://github.com/BlazingSystems/BlazingSystems-Experiments
Development PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/30
Full cross-product research: `experiment/openwrt/BlazePwifi/docs/V060_COMPETITIVE_SYSTEM_AUDIT.md`
Release decisions and outstanding risks: `experiment/openwrt/BlazePwifi/docs/RELEASE_DECISION_0.6.0.md`
Open P0 financial issues: #31 and #32.

**Production release `v0.6.0` does not exist, and this lab prerelease is not a replacement. The prior `v0.5.2` production and Standalone Rental release assets are frozen and unchanged.**
