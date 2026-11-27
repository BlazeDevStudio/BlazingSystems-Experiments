# Handover Log — 2026-10-05 — v0.5.0 RC9 Candidate Gate PASS

## Exact validated candidate

Branch:
`blazepwifi-v0.5.0-rc9`

Commit:
`66e159b65b6d8fb5f74dd981dc73d46db7229adc`

Build run:
`37326542666`

Result:
**PASS**

Final candidate gate:
`v04_candidate_gate` — PASS

## Required validation results

The exact RC9 SHA passed:

- static/security/config/integration validation;
- BlazeRental Android APK build;
- Android Device Owner emulator audit;
- browser Management Console/portal audit;
- ESP8266 build + simulation;
- ESP32 build + simulation;
- Ruijie firmware build + simulation;
- x86_64 firmware build + QEMU simulation;
- required Orange Pi firmware builds + simulations;
- retained v0.4 compatibility contracts;
- v0.5 launcher/console source contracts;
- exact candidate gate.

## Key artifact IDs

- Candidate gate: `11351899683`
- BlazeRental Android build: `11352033229`
- Android emulator evidence: `11352761808`
- Browser evidence: `11351948709`
- x86 simulation: `11352462804`
- Ruijie simulation: `11352945781`

## Android behavior now validated

- unpaid cold start lands on BlazeRental far-left gate;
- unpaid app-drawer and horizontal escape attempts remain contained;
- secret timer hold opens native Initial Setup;
- local admin password can be created;
- Use device as is works without BlazePwifi enrollment;
- normal Launcher3 Home and All Apps work in unrestricted mode;
- Notifications page is adjacent and contains Clear All;
- far-left BlazeRental page remains reachable;
- Device Owner remains active and ordinary uninstall is blocked;
- no BlazeRental fatal crash detected.

## Next action

Attempt locked production signing using the existing v0.4 production certificate identity.

Build run:
`37326542666`

Candidate SHA:
`66e159b65b6d8fb5f74dd981dc73d46db7229adc`

If the locked signer is unavailable, do not rotate certificates silently. Record the blocker and publish only according to the explicit release policy.

## Audit & Reconcile prompt

```text
@GitHub Audit and reconcile the validated BlazePwifi v0.5.0 RC9 candidate.

1. Read PROJECT_HANDOVER.md and this handover log.
2. Verify build run 37326542666 concluded success and head SHA is 66e159b65b6d8fb5f74dd981dc73d46db7229adc.
3. Verify candidate-gate artifact 11351899683 and Android emulator evidence 11352761808 belong to that exact run/SHA.
4. Preserve RC9 as the immutable validated application candidate; do not add application changes to it.
5. Attempt production signing only with the locked v0.4 production certificate fingerprint C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24.
6. Never silently rotate the Android signer.
7. If signing succeeds, use the exact signing run plus build run 37326542666 and candidate SHA 66e159b... for v0.5.0 publication.
8. Verify release assets, RELEASE-MANIFEST.json, CANDIDATE-GATE.json, signing manifest and SHA256SUMS after publication.
9. Update PROJECT_HANDOVER.md and add signing/release handover logs for every result.
10. Leave a fresh Audit & Reconcile prompt after the final release milestone.
```
