# BlazePwifi v0.6.0-alpha.3 — accounting safety candidate · LAB ONLY

**NOT A PRODUCTION RELEASE. DO NOT INSTALL THESE BUILDS ON LIVE CUSTOMER ROUTERS, PAID WIFI-VENDO OR PISONET MACHINES, RENTED ANDROID PHONES, OR DEVICES HOLDING VALUABLE TIME, CREDITS, CONFIGURATION OR PRIVATE KEYS.**

This is a genuine GitHub Actions-built **development prerelease** incorporating safety fixes added after the immutable alpha.2. It is not a safe v0.5.2→v0.6.0 production upgrade. The supported updater **still intentionally blocks** unproven 0.6-family migrations.

**Internal version truth:** OpenWrt runtime continues to report source **0.5.3**, BlazeRental Android Launcher3 CI TEST build **0.5.3 / versionCode 50300**, and Windows BlazePisonet SoftTimer **0.4.0**. The Android CI APK is NOT the owner's permanent Lineage-2 signed production current/rescue pair. No owner private key, production fingerprint compatibility or Device Owner OEM factory-reset acceptance is asserted.

## What changed after alpha.2

**Paid member accounting / anti-data-loss**
- Prevent ordinary authenticated admin member DELETE from erasing positive banked paid seconds. Delete is allowed only at verified zero balance. A partial member-delete storage/audit failure stops financial operations under persistent operator-reconciliation quarantine, rather than falsely acknowledging success.
- Improve Members management UX: paid-time accounts show why delete is unavailable. The UI fetches the authoritative current server balance again before confirming deletion, resisting stale cashier pages.
- Protect all member-row rewrites against incomplete read, corrupted/duplicated member TSV, truncated awk-copy, failed append, rename or synchronization. No partial source snapshot is allowed to replace other members' paid time. Admin create/update/password operations now propagate audited storage errors rather than giving success on failure.
- Separate **untrusted metadata imports** from authoritative financial migration: an old unsigned export is forbidden from overwriting an existing member's newer banked seconds. New accounts with claimed nonzero imported paid time are refused until a verified, quiesced ledger migration exists. Truly zero-time profiles remain importable disabled until a password reset. The UI explains refusals instead of silently dropping or minting credit.
- Preserve the alpha.2 live signed-controller replay protection, coin-window idempotency, charged session/voucher write refusals and updater archive traversal/link defenses.

**Authenticated transaction research**
- Add a separate **synthetic/off-device** controller-HMAC envelope test on the prototype v2 journal. Tests cover per-controller keys, signed monotonic sequences, transfer/rental replay, forged payloads, stale sequence and crash/lost-ACK injection.
- **This is NOT installed OpenWrt authentication or crash-atomic financial journaling.** The lab-only fixture uses OpenSSL CLI in a /tmp-only disposable directory, which is not production-appropriate key handling and does not prove target flash fsync/dirsync.

**Admin / Rental foundations**
- Continue the distinct device-owner/provisioning QR vs ordinary binding QR, Launcher3 admin trust panel, HTTPS pin checks, and lightweight responsive BlazeFusion admin UI from alpha.2. This release is not a new production-signed Android app.

## Expected GitHub release assets

Only if the exact versioned candidate passed its own GitHub Actions release gate, the GitHub release includes nine nonempty `*-LAB-ONLY.zip` files: full BlazePwifi OpenWrt bundle, current update bundle, Ruijie RG-EW1200G Pro firmware, x86_64 firmware, Orange Pi Zero 3 firmware, ESP8266 firmware, ESP32 firmware, Android CI TEST APK package and Windows BlazePisonet SoftTimer x64 installer. The remaining three assets are `RELEASE_NOTES.md`, `SHA256SUMS`, and `MANIFEST.json`, with exact source SHA and same-source Full/Windows workflow IDs. Optional Orange Pi images may build in CI but are NOT implicitly included in these nine assets.

Read the release manifest to identify precisely which source and CI run produced each file. Verify each SHA-256 before using a disposable development device. Never flash recovery/incompatible model images simply because a ZIP exists.

## Non-negotiable production blockers — v0.6.0 does NOT exist as a production release

1. **All paid stores** (Wi-Fi credit, rental lease/phone, member bank/transfer, controller events) must migrate to one authenticated server-authoritative, crash-recoverable, durable exactly-once transaction engine, rather than separate TSVs with a fail-closed quarantine marker. Prove fsync, parent-directory durability and powercut reboot behavior on exact target filesystems.
2. Existing customer v1 credit, event ID, device bindings, vouchers, admin passwords and network configuration require source-specific operator-approved quiescence, encrypted private backup, verified migration and safe rollback. Old dropped receipt IDs cannot be reconstructed and silently declared safe.
3. A **real current AND higher-version-code rescue** BlazeRental APK must be signed with the unchanged owner-controlled Lineage-2 production key. Verify signing fingerprints, factory-reset Android Device Owner enrollment, binding restrictions and OEM anti-bypass with devices in hand.
4. Actual model-specific OpenWrt/Ruijie, Orange Pi, BIOS/UEFI x86, ESP coinslot electronics, Windows COM/kiosk and Android phones must pass installation, WAN/VLAN, repeated physical power loss, credit recovery and at least 30 concurrent clients under supervised test conditions.
5. Only after all P0 gates may actual OpenWrt/APK/installer version metadata be bumped and a separate **production** `v0.6.0` tag published.

**Development repo:** https://github.com/BlazingSystems/BlazingSystems-Experiments · **PR #30:** https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/30 · canonical handover: `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`.

Historical releases `v0.5.2`, `v0.6.0-alpha.1` and `v0.6.0-alpha.2` remain immutable and separate from this laboratory candidate.
