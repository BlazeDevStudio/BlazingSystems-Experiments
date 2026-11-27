# PHX-HARDWARE — ESP32 Mbed TLS 3/4 compatibility

Updated: 2026-11-27T03:43:06Z  
Role: PHX-HARDWARE  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
Branch: `phoenix/hardware-storage-preflight-device-separation-20261126-utc23`  
PR: [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356) (OPEN / DRAFT / UNMERGED)  
Base: `blazepwifi-v0.6.0-audit-foundation` at `2fbd2475e9f54878c316fa7cea2f228386b0e859`  
Source/test commit: `050f0f0ca53533e8609ff0cb63e414538a50d132`

## Defect and correction

The old ESP32 sketch unconditionally included `mbedtls/sha256.h`. The ESP32 Arduino 4.0.0 build no longer exposes the legacy SHA module, causing the exact-head Full build failure.

The sketch now selects its provider by `MBEDTLS_VERSION_MAJOR`:
- Mbed TLS 3: checked `mbedtls_sha256_*` sequence.
- Mbed TLS 4: PSA `psa_crypto_init` + `psa_hash_compute(PSA_ALG_SHA_256)`.

Both paths reject provider errors. A 64-character hexadecimal digest validator is applied before request construction. Missing key/ID or invalid digest produces an empty body, and `post` refuses to open/send HTTP when that body is empty. Existing action semantics and request fields remain unchanged.

## Regression evidence

Test-first RED commit: `f0bc8001d3fbbbfe852129b8566d8465165dd86d`; source-contract failed on the missing provider selector as expected.

GREEN source-contract:
- Push [#45935603861](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935603861), job `140297982426`: PASS.
- PR [#45935608508](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935608508), job `140297996882`: PASS.
- Seven negative mutations rejected: missing version selector, PSA init failure guard, PSA status/length check, legacy status check, invalid digest guard, empty-body guard, unsupported-version deny.

The pinned ESP32 target matrix uses Arduino CLI 1.6.0 and Espressif index commit `8f6bee9761f7b15cce27b79cbd1ae199d0df2adf`, with exact core versions 3.3.13 and 4.0.0. Each job stages the canonical packaged source twice, compares staged trees, builds twice, and compares application image hashes.

At this handover checkpoint, matrix jobs were still running:
- Push: #45935603861 jobs `140297982713` (4.0.0) and `140297982791` (3.3.13).
- PR: #45935608508 jobs `140297996749` (4.0.0) and `140297996953` (3.3.13).

No target-build PASS is claimed until terminal results are read.

## Evidence boundary and blockers

`SIMULATED_ONLY=1`; `COIN_ADMISSION_ENABLED=0`. This is compile and source-contract CI, not runtime crypto acceptance, physical hardware acceptance, or proof of production controller authorization.

150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent release signoff remain outstanding. No flash, live money, production migration, release or deployment occurred.

## Next exact action

Read the four matrix job terminal results and refreshed Full run after this handover commit; request PHX-QA independent review; keep PR #356 DRAFT and unmerged.
