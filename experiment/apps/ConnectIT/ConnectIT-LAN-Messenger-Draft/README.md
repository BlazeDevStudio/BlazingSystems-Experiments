# ConnectIT v0.1.2 REVOCATION INTEGRATION — DEVELOPMENT / NO-GO

revocation integration contract and preserved LAN transport; source/testing details under docs/REVOCATION*.md. Existing v0.1.1 baseline remains below. Do not use as production service.

# ConnectIT LAN Messenger Draft 0.1.0 — INDEPENDENT INTEGRATION PREPARATION

**Do not merge into LAN Messenger yet.** This archive provides source-level Flutter/Dart interfaces, policy guards, draft settings UI, protocol specification, compatibility notes and ConnectIT original vector branding. The actual LAN Messenger app is still undergoing call PiP, Windows crash, file-transfer resume and routed-LAN stabilization. No existing Flutter code was overwritten.

## Source lineage

- Blaze Messenger Seed 0.2.0 source: archived in owner's LAN-Messenger Google Drive folder and examined before adapting its relay behavior. New Master and Seed archives are separate executables.
- Existing LAN Messenger v0.3.1 preview branch: `release/lan-messenger-v031-preview`; this is not a direct dependency and no source changes were made.
- Existing LAN Messenger identity (static X25519 on LAN) is NOT a ConnectIT-issued account/device credential. This draft requires explicit linking; never reuse legacy peer IDs as ten-digit account identities.

## Draft package

- `lib/connectit/connectit_protocol.dart`: identity, discovery and SecureBind domain types.
- `lib/connectit/connectit_service.dart`: typed authority, satellite, LAN and direct P2P ports.
- `lib/connectit/hybrid_adapter.dart`: LAN-first adapter that preserves existing local calls/files and only uses Seeds for encrypted text.
- `lib/connectit/mini_seed_policy.dart`: opt-in, Wi-Fi, cellular, battery, background and quota policy values. No background service implemented.
- `example/connectit_settings_page.dart`: source-level Flutter UI, intentionally not wired to a server.
- `test/contract_test.dart`: portable Dart assertions; **NOT executed here** (Flutter/Dart SDK unavailable).
- `protocol/CONNECTIT_PROTOCOL_v1.md`: exact implemented subset, canonical signed messages, SecureBind and v1 extension gaps.
- `assets/`: original vector logo, light/dark/mono, PNG sizes, Windows ICO and adaptive icon resources.

## Integration stages (do not skip)

1. Stabilize and independently test LAN Messenger on physical Windows/Android pairs, especially PiP, call teardown, Windows unexpected exits, permission flows and large file resume. Preserve existing offline behavior.
2. Add a separate, default-disabled `ConnectIT` feature flag and `MasterAuthorityPort` implementation; pin the Master public key, store new Ed25519 key in platform keystore, explicitly link legacy LAN identity to the account after user consent.
3. Implement an independently audited E2E encryption/key verification scheme. Do not pass plaintext to Seed APIs or consider the current LAN X25519 peer discovery to be authenticated by ConnectIT.
4. Implement signed device SecureBind with local PIN confirmation and complete server notification delivery/recovery, then test original-device security actions.
5. Add relay text-only routing and deduplication with per-Seed cursors. Introduce privacy-preserving five-hop discovery only after the federation security contract is established.
6. Add authenticated direct WebRTC ICE/STUN file transfer (resume+checksum) and audio/video, with **no TURN/Seed payload fallback**. Preserve original LAN mode on internet failures.
7. Hardware acceptance: network hop across main ISP/PisoWiFi L3 NAT, connectivity change, CGNAT error UI, 1GB relay, Windows native crashes, Android PIP and background policy, safe migration/rollback.

## Branding deployment

`connectit-logo-master.svg` is original geometric SVG. Use `connectit-app-icon.svg` for square launcher icon. Adaptive Android foreground PNG is center-safe with separate background and sample `android-adaptive-icon.xml`; copy resources into the Android project's `res/drawable*` and `res/mipmap-anydpi-v26` paths as appropriate. Windows uses `connectit.ico`. Keep SVG and PNG sources; the original LAN Messenger brand is not replaced.

## Compatibility / test truth

The runnable Go Master/Seed subset is interoperable in tested localhost flows; Flutter side is **interface-only**. `test/contract_test.dart` has NOT been executed; no Android APK, Windows Flutter binary, working network stack, E2E encryption implementation or app integration is claimed.

## v0.1.1 temporary LAN Messenger test dummy

The verified native-build reference is LAN Messenger `0.3.2+15` at `7d8a08afb39bab8d001fce3d3ba33706e034fcb1`; run `40610141383` is successful for Windows and Android. Later draft `0.3.3+16` PR #229 lacks verified exact-head binary evidence in this handout. `integration/lan_v032_staging/` provides an **additive, disabled-by-default** adapter against the real `LanNode` and `Intercom` API; it does not replace the APK/EXE, change `main.dart`, or alter existing LAN behavior.

`test/lan_build_dummy_e2e.py` is a runnable local protocol dummy with two distinct registered clients, manual X25519 trust fixture, real AES-256-GCM ciphertext, Ed25519 sender authentication, 2-Seed federation, tamper detection and Master-offline receipt. It is not the Flutter native binary; do not call its success a physical LAN Messenger integration test. Run from this package directory after rebuilding the other two package binaries: `python test/lan_build_dummy_e2e.py`. Requires Python cryptography package.
