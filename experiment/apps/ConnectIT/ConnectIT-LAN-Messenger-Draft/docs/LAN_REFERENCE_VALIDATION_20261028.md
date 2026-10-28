# LAN Messenger CI reference and ConnectIT integration — 2026-10-28

## Exact source provenance

**Latest verified native-build reference:** Flutter LAN Messenger `0.3.2+15`, exact Git commit `7d8a08afb39bab8d001fce3d3ba33706e034fcb1`, draft PR #228, [GitHub Actions run 40610141383](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40610141383). Android and Windows build and tests completed SUCCESS on that run, including Android two-emulator WebRTC tests. This is **not** certification of physical hardware reliability or ConnectIT integration.

Newer source `0.3.3+16`, exact head `a9f8745fb08f10c9bc8bede458eb35103c03e7e1` in draft PR #229, contains additional unverified Windows crash/liveness fixes. It is not treated as a newer *verified built artifact*.

**Android CI artifact:** id `12782503073`, downloaded original CI ZIP SHA256 `ada88114f93b8cbf6d44f24ea70b04b39b61e2b0381951fa0007a4fab9dd7790`; inside: arm64-v8a, armeabi-v7a, x86_64 preview APKs. **Windows CI artifact:** id `12782732402`, original CI ZIP SHA256 `dba580ec6bf21bba902afa3b8403bc5b4562caffd595027e373fa8887dca5e1d`; inside an `LAN-Messenger-Windows-Optimized.zip` carrying `lan_messenger.exe`, Flutter DLLs and assets. Both original ZIPs passed local ZIP CRC read tests; no Android emulator/Windows process was launched in the ConnectIT environment.

## Separate build-track evidence

1. `test/lan_build_dummy_e2e.py` is an *executable protocol dummy*, using the real standalone Go Master and two real standalone Go Seeds in localhost. It provisions distinct first-device credentials, uses separate X25519 E2E keys with HKDF domain separation and AES-256-GCM, verifies authenticated sender, moves encrypted text through two Seeds, catches bit-flipped ciphertext, rejects file relay kinds, and confirms delivery after Master shutdown. Peer keys are manually provisioned for the test, **not** centrally authenticated directory keys.
2. `integration/lan_v032_staging` contains a real API-level `LanNode`/`Intercom` adapter, but is **never imported into LAN Messenger's main.dart** and defaults to disabled. Its test build has been staged on a separate draft PR #230: https://github.com/BlazingSystems/BlazingSystems-Experiments/pull/230. It has no permission to merge into the existing app.
3. Run any new Flutter compile/tests on the exact isolated PR head, not only the older baseline. A baseline CI success does **not** validate the new adapter. No evidence of a new PR-head Flutter compile was available at document creation.

## What the test does NOT establish

- No actual binary was modified to add ConnectIT. The unmodified APK/EXE cannot log into the Master or send a ConnectIT Seed message.
- The Go/Python protocol dummy is NOT LAN Messenger Flutter process integration, and does not validate Android secure key storage, per-user directory trust, SecureBind UI, PiP, native Windows calls or WebRTC internet P2P.
- The two-Seed relay still uses mesh-shared secret and needs node-specific federation trust, revocation propagation, peer-identity pinning, congestion/retention controls, authenticated discovery, multi-hop routing tests and resilience testing before production.
- Existing LAN Messenger remains fully independent; when ConnectIT is disabled, LAN discovery, calls and file transfers use the original code only.

## Reproduce

- From each Go server root: `go test ./...`.
- With Python `cryptography` package installed, place the three extracted ConnectIT packages as sibling directories and run `cd ConnectIT-LAN-Messenger-Draft && python test/lan_build_dummy_e2e.py`.
- In a *throwaway copy* of LAN Messenger `7d8a08a`, add the two files under `integration/lan_v032_staging/lib/connectit/` and `integration/lan_v032_staging/test/` to `lib/connectit/` and `test/`, then `flutter analyze && flutter test`. No existing LAN Messenger file changes are necessary.
