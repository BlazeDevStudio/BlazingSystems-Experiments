# Handover Log — 2026-10-05 — v0.5 Locked Signing Blocked Safely

## Validated application candidate

Candidate SHA:
`66e159b65b6d8fb5f74dd981dc73d46db7229adc`

Validated build run:
`37326542666` — PASS

## Locked production signing attempt

Workflow:
`BlazeRental v0.5 locked production sign`

Run:
`37327439782`

Result:
**FAILED SAFELY**

Failure point:
`Restore exact locked v0.4 production identity`

Evidence:

`Locked v0.4 signer recovery requires BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM.`

`Refusing to rotate the production certificate.`

## Interpretation

GitHub Actions still does not have either:

- the exact locked v0.4 production keystore via `BLAZERENTAL_KEYSTORE_B64` + password, or
- the matching offline transfer private key via `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM`.

The signing workflow correctly refused to create a different certificate.

No production Android APK was signed or replaced.

Locked fingerprint remains:

`C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

## Release decision

Proceed with the designed v0.5.0 **prerelease** path using:

- exact green build run `37326542666`;
- exact candidate SHA `66e159b65b6d8fb5f74dd981dc73d46db7229adc`;
- signing run ID `0`.

The prerelease may contain:
- `BlazeRental-v0.5.0-TEST.apk`;
- `BlazeRental-v0.5.0-release-unsigned.apk`;
- firmware/controller outputs;
- evidence/manifests/checksums.

It must **not** contain a file named `BlazeRental.apk` presented as production-signed until the locked signer is restored.

## Next action

Publish v0.5.0 prerelease from the exact green candidate, verify release assets/manifests/checksums, then update PROJECT_HANDOVER.md and create the final release log.

## Audit & Reconcile prompt

```text
@GitHub Audit and reconcile BlazePwifi v0.5.0 signing/release state.

1. Verify candidate SHA 66e159b65b6d8fb5f74dd981dc73d46db7229adc and build run 37326542666 are green.
2. Verify signing run 37327439782 failed only because the locked v0.4 signer/recovery key was unavailable.
3. Preserve locked production fingerprint C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24.
4. Do not rotate certificates silently and do not label a TEST/unsigned APK as production.
5. Publish/verify the v0.5.0 prerelease using signing_run_id 0.
6. Confirm RELEASE-MANIFEST.json reports production_signed=false and signing_run_id="0".
7. Verify BlazeRental-v0.5.0-TEST.apk, unsigned APK, CANDIDATE-GATE.json, firmware assets and SHA256SUMS are present.
8. Update PROJECT_HANDOVER.md with exact release state and signing blocker.
9. If the owner later restores the locked signer, rerun signing against the same validated candidate or a newly validated successor before replacing production APK.
10. Leave a fresh Audit & Reconcile prompt after the release milestone.
```
