# Handover Log — 2026-10-06 — v0.5 Locked Signing Retry Still Blocked

## Status

BlazePwifi `v0.5.0` remains published as a validated GitHub prerelease from exact green RC9 candidate:

- candidate SHA: `66e159b65b6d8fb5f74dd981dc73d46db7229adc`
- build run: `37326542666` — PASS
- release workflow: `37327843195` — PASS
- release ID: `403831689`

## Signing retry

Locked production signing workflow run:

`37327439782`

was retried as `run_attempt=2` on 2026-10-06.

Result: **FAILED SAFELY** at:

`Restore exact locked v0.4 production identity`

Evidence:

- `Locked v0.4 signer recovery requires BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM.`
- `Refusing to rotate the production certificate.`

No production APK was replaced.
No signing identity was rotated.
The published v0.5 prerelease remains unchanged.

## Current release assets

Android assets intentionally remain:

- `BlazeRental-v0.5.0-TEST.apk`
- `BlazeRental-v0.5.0-release-unsigned.apk`

`BlazeRental.apk` is intentionally absent until the exact locked v0.4 production signing identity is restored.

Locked fingerprint:

`C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

## Safest next action

Restore either:

- repository secrets containing the exact locked v0.4 PKCS12 keystore/password, or
- `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM` matching the encrypted recovery handoff.

Then rerun locked signing against the same green RC9 candidate. Do not rebuild or retag the application unless source changes are made.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi v0.5.0 from the published prerelease state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest file under experiment/openwrt/BlazePwifi/docs/handover/.
3. Verify GitHub Release v0.5.0 still targets exact candidate 66e159b65b6d8fb5f74dd981dc73d46db7229adc.
4. Verify build run 37326542666 and release run 37327843195 remain successful.
5. Verify locked-signing run 37327439782 attempt 2 failed only because the locked signer/recovery private key was unavailable.
6. Never rotate the production Android certificate silently.
7. If the exact locked signer is now available, rerun the v0.5 locked signing workflow against RC9 without rebuilding the application.
8. If signing succeeds, refresh v0.5.0 with BlazeRental.apk, signing manifest/fingerprint, verify assets/checksums, and promote out of prerelease.
9. If signing remains unavailable, leave the prerelease untouched and preserve TEST/unsigned labeling.
10. Update PROJECT_HANDOVER.md and add a dated handover log after the next meaningful success/failure, including a fresh Audit & Reconcile prompt.
```
