# BlazePwifi v0.6.0-alpha.4 — authenticated session and prepaid safety · LAB ONLY

**NOT PRODUCTION. DO NOT INSTALL ON ACTIVE CUSTOMER Wi-Fi VENDO, PISONET CASHIERS, RENTAL PHONES OR ROUTERS HOLDING PAID TIME, RECEIPTS, PRIVATE KEYS OR BUSINESS CONFIGURATION.**

This is a **real downloadable CI development prerelease**, produced and published only after fresh, exact-same-source Full platform AND Windows SoftTimer installer GitHub Actions pass. Verify `MANIFEST.json`, `SHA256SUMS` and asset digests before using disposable lab hardware. Source and release history for alpha.1, alpha.2, alpha.3 and shipped v0.5.x remain immutable.

**The embedded application versions have NOT been upgraded to production v0.6.0:** OpenWrt runtime is still **0.5.3**, Android Launcher3 CI TEST APK is **0.5.3 / versionCode 50300**, and Windows BlazePisonet SoftTimer is **0.4.0**. The Android current ZIP is **NOT verified to be signed by the owner's permanent Lineage-2 production signing key** and cannot be used as a signed current/rescue Device Owner upgrade pair. The 0.6-family on-device upgrader still refuses unapproved conversion of v1 paid state.

## What changed since the published alpha.3

### Wi-Fi, members and rental money safety
- Refuse malformed, duplicate, truncated or symlinked `accounts.tsv` financial state instead of atomically replacing it with ambiguous credit records. Signed coin ACKs, voucher/session changes and ambiguous payments remain fail-closed under a persistent paid-state quarantine.
- Prevent a second device identity from claiming a MAC already associated with paid credit. A protected replay regression verifies the original 700 fictional credit units and legacy source rows survive untouched. Old v1 sources are preserved for proper verified migration, not silently erased on collision.
- Preserve member banked paid seconds against stale metadata imports and user deletion; display the current balance and confirm it again before enabling Delete. Refuse unsigned imported positive balances for new accounts until a separately authenticated financial migration exists.
- Harden full member/admin credential changes and rental leases against partial file copies, failed rename, missing receipts, replay-collision and false successful replies.
- Harden standalone R281 rental/hotspot controller enrollment, time accounting and coin nonce handling with signed-source and failed-write regressions. A passing synthetic fixture does not replace supervised R281 electronics testing.

### Authentication, security and recovery
- Protect full and R281 admin session data from incomplete copy, failed storage rename and forged success on logout or session revocation.
- **Revoke existing sessions before committing a password change** on the full management CGI, standalone R281 Rental admin and privileged shell reset/bootstrap commands. A failed revoke leaves the old password unchanged; a failed subsequent verifier write leaves the old password usable for a fresh login but invalidates prior sessions.
- Fail closed if cryptographically secure randomness cannot provide complete tokens/salts, rather than minting predictable administrator, Device Owner or rental credentials.
- Preserve the split trust levels of managed factory-reset provisioning QR and lower-security standard binding QR, native Launcher3 admin trust panel and the lightweight BlazeFusion console developed earlier.

### Crash-recovery research now included in the source tree
- Synthetic-only isolated controller HMAC sequence fixture and checksum-framed atomic money/receipt model, including a native Linux `fsync(candidate)` → `renameat()` → `fsync(parent directory)` test. The combined fixture tests interrupted commit, lost ACK replay and debit/transfer/rental account conservation.
- A strictly redacted, read-only **synthetic v1 source inventory** for checking accounting formats before migration.
- **None of those fixtures is a deployed, authenticated production OpenWrt journal.** Native tests run in disposable marked `/tmp` directories and do not prove real NAND/eMMC/SD filesystem persistence after sudden power loss.

## Real expected downloadable assets (conditional on the release gate)

Nine nonempty `*-LAB-ONLY.zip` archives (BlazePwifi core bundle, current update bundle, Ruijie firmware, x86_64 firmware, Orange Pi Zero 3 firmware, ESP8266 firmware, ESP32 firmware, Android CI TEST APK package and Windows SoftTimer Setup EXE package). `MANIFEST.json`, `SHA256SUMS` and `RELEASE_NOTES.md` bring the total to **12 actual GitHub release assets**. Other optional Orange Pi images built during CI are not implicitly listed as downloadable assets. Each file's exact size/digest and original source+Windows workflow IDs must be checked against the manifest and GitHub API, not inferred from a successful badge.

## Stop gates before any REAL production v0.6.0

1. A unified **authenticated, crash-atomic, fsync-confirmed server ledger** for paid Wi-Fi credit, PisoNet member transactions, rental leases, controller monotonic sequences and immutable receipts must replace the split v1 TSV stores. Exact-once after lost controller ACK/power loss must be demonstrated on supported hardware.
2. A **quiesced, private, reversible and verified v1 customer financial migration** must preserve banked balances, issued vouchers, controller replay IDs and trusted credentials, backed up encrypted with tested restore. Old missing receipt IDs cannot be invented.
3. Permanently signed current **and rescue** Android APKs must match the actual owner's Lineage-2 certificate and be tested under OEM factory-reset Device Owner QR enrollment, kiosk escape/recovery and real device binding.
4. Real Ruijie/OpenWrt routers, Orange Pi, BIOS/UEFI x86, ESP coin electronics, Windows RS232/USB serial ports, and Android phones require controlled physical acceptance: WAN/VLAN, install/rollback, power-cuts, recovery and at least 30 concurrent clients.
5. The true production `v0.6.0` tag may be issued **only after** each blocker closes, the embedded runtime/app version numbers are honestly updated, owner signing proves continuity and real deploy/rollback is verified.

The release exists solely for developer testing and source provenance. **No customer-install authorization and no production v0.6.0 release is claimed.**

GitHub: https://github.com/BlazingSystems/BlazingSystems-Experiments

Development PR: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/30
