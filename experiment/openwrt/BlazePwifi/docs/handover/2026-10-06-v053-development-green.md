# BlazePwifi v0.5.3-dev.1 — Green Development Candidate

Date: 2026-10-06

## Purpose

This record opens the post-v0.5.2 development line without rewriting the frozen v0.5.2 production release.

Full BlazePwifi is the active development target. The Standalone Rental profile remains reference-only.

## Frozen production baseline

- Production release: v0.5.2
- Exact application candidate: `bf2992977fe8504d21b107df02826032c31d3a62`
- Production BlazeRental lineage: `BlazeRental-production-lineage2`
- Permanent production certificate SHA-256:
  `1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`
- v0.5.2 tag/release and dedicated signing/recovery workflows were not modified.

## Development identity

- VERSION: `0.5.3-dev.1`
- BlazeRental versionName: `0.5.3-dev.1`
- BlazeRental development versionCode: `50290`
- Development iteration range reserved: `50290–50298`
- v0.5.2 forward-install rollback rescue: `50299`
- Final v0.5.3 production code reserved: `50300`

The rescue is built from the exact frozen v0.5.2 application candidate, with only Android version metadata raised.

## Implemented hardening

### Full admin security

- CSRF is sent in both the form body and `X-Blaze-CSRF` header.
- Requests use same-origin credentials and no-store caching.
- A stale CSRF session is refreshed and the mutation is retried once.

### Rental QR architecture

Two different setup flows are now explicit:

1. **Binding QR**
   - for an already-installed BlazeRental APK;
   - carries short-lived server/enrollment/device binding information;
   - manual/lower anti-bypass deployment path.

2. **Device Owner Provisioning QR**
   - for Android Setup Wizard on a new/factory-reset phone;
   - carries the DPC component, published APK download location, package checksum, minimum version and Blaze provisioning extras;
   - high-security Device Owner deployment path.

The provisioning flow pins the local BlazePwifi TLS certificate when the default self-signed admin certificate is used.

### Retry-safe enrollment

- A provisioning/binding enrollment request nonce is persisted by BlazeRental until permanent identity is committed.
- A dropped enrollment response can be retried with the same nonce and returns the same issued identity.
- A different nonce cannot recover that identity or mint another device.
- Enrollment responses are HMAC-authenticated with the one-time token before the permanent device identity is accepted.
- Temporary redemption data is removed after the device proves possession of its permanent secret.

### Insert Coin and timer behavior

The customer interfaces now distinguish two independent clocks:

- purchased/session time remaining;
- coin-insertion reservation time remaining.

BlazeRental unpaid runtime visibly shows:

- `BLAZERENTAL`
- `00:00:00`
- `TIME FINISHED`
- `INSERT COIN`

The active coin window shows a live MM:SS countdown, selected Vendo, accepted pulse count and peso value. `DONE INSERTING` closes the authoritative server reservation.

The captive portal has the same separate session/coin-window model, including recovery of an active reservation after refresh.

### Accounting integrity

- Coin-window timing is server-authoritative.
- Rental coin progress is tracked server-side.
- Only accepted non-duplicate signed Vendo pulses increase lease/progress.
- Replay of the same event does not add time or progress twice.
- Repeated coin-window open requests for the same Rental device reuse the live target instead of resetting its nonce/progress.
- Done/expiry removes target and progress state.

## Exact green candidate

Application/development candidate:

`ee427f67d8f33d965c84fd675f80e78653a7c91d`

Full workflow run:

`37486090360` — **PASS**

The run passed:

- validation/security/config/integration/stress;
- Android current APK build;
- exact frozen-v0.5.2 rescue APK build;
- Device Owner Android emulator;
- browser QR + dual-CSRF + session timer + coin-window timer runtime audit;
- ESP8266 build and simulation;
- ESP32 build and simulation;
- Ruijie firmware and simulation;
- x86_64 firmware and QEMU simulation;
- required Orange Pi builds/simulations;
- transactional update bundle;
- final candidate gate.

## Runtime Android evidence

Artifact: `BlazePwifi-v0.5-android-simulation`

The audit reports release `0.5.3-dev.1` and passed:

- locked Blaze gate;
- unpaid drawer blocking;
- unpaid Home escape blocking;
- secret admin;
- daily-driver mode;
- normal Launcher3 behavior when unrestricted;
- notifications/Clear All;
- Device Owner status;
- ordinary uninstall defense;
- no fatal crash.

The retained locked-state UI dump and screenshot visibly contain:

- `BLAZERENTAL`
- `00:00:00`
- `INSERT COIN`

Audited APK SHA-256:

`a11de0373481747b95c3d1c07e707e419cb4b992b3e337c8a1cfb4a2cfa518f5`

## Current artifacts

- `BlazePwifi-android-current`
- `BlazePwifi-current-update`
- `BlazePwifi-current-candidate-gate`
- `BlazePwifi-v0.5-browser-simulation`
- `BlazePwifi-v0.5-android-simulation`
- platform firmware/simulation artifacts from run `37486090360`

These are development/validation artifacts. They are not a new production v0.5.3 release.

## Release guard

Do not publish v0.5.3 production from this development identity.

Before a future production v0.5.3:
- finalize the intended release scope;
- move Android to versionCode `50300` / versionName `0.5.3`;
- run the full exact-candidate matrix again;
- use the permanent Lineage 2 production signer;
- verify signing fingerprint and package upgrade compatibility;
- generate provisioning checksum/QR from the final signed APK;
- publish only after the exact signed candidate and recovery path are green.
