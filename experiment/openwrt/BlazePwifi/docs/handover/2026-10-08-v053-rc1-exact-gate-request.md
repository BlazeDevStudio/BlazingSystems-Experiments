# BlazePwifi v0.5.3 RC1 exact-candidate gate request — 2026-10-08

## Scope
- Full BlazePwifi / BlazeRental only; do not alter the Standalone Rental source tree or published releases.
- v0.5.2 Lineage-2 signer and recovery records remain frozen and authoritative.
- This handover is validation-only: it does not change runtime, signing identity, or release assets.

## Candidate and CI baseline
- RC1 branch: `blazepwifi-v0.5.3-rc1`.
- Previously frozen RC1 code/doc revision: `4737d1adaa117e6be6f3bea61b9a5ebbe4a496ae`.
- The initial RC1 GitHub Actions run `37670287555` was cancelled. A cancelled run is **not** an acceptable production release gate.
- The later green `main` run `37735854374` is not interchangeable with the RC1 candidate: it tracks a different commit and is not the exact candidate SHA.
- This documentation-only commit deliberately creates a new RC1 candidate SHA and triggers a clean full matrix. All subsequent signing/release input SHAs must refer to the new exact successful run.

## Mandatory production gates
1. `BlazePwifi build` passes completely on the **exact** RC1 commit, including `validate`, required hardware builds, browser runtime, Android Device Owner emulator, x86/Orange Pi/Ruijie simulations, and `v04_candidate_gate`.
2. Uploaded `BlazePwifi-current-candidate-gate/CANDIDATE-GATE.json` declares `release: 0.5.3`, `status: passed` and the identical candidate commit.
3. The frozen v0.5.2 recovery app source `bf2992977fe8504d21b107df02826032c31d3a62` is used for the separately-versioned rollback/rescue APK.
4. Signing uses only the existing `BlazeRental-production-lineage2` PKCS12 with fingerprint `1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`. Never generate or publish a replacement signer.
5. Only once the exact signer run passes may the guarded v0.5.3 release stage verify the signed APK/rescue, binding QR vs Device Owner provisioning QR, package SHA-256 checksum, SHA256SUMS and manifests, and publish.
6. If any gate is cancelled, skipped, unverified, or failed, production publishing remains blocked.

## Recovery and data handling
- Recovery A/B private keys and production keystore/password are never committed to Git or embedded in CI logs or release assets.
- Existing v0.5.2 production and Standalone Rental releases remain untouched.
- Physical boot/recovery and rental-bypass testing on each target device remain necessary beyond GitHub emulation.

## Reconciliation checkpoint
The next maintainer must check the latest RC1 workflow run and its exact commit SHA. Do not treat green development-branch or Standalone Rental CI as proof that v0.5.3 RC1 passed.
