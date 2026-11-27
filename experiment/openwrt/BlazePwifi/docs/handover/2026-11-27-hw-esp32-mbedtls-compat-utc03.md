# PHX-HARDWARE — ESP32 Mbed TLS 3/4 compatibility

Updated: 2026-11-27T03:48:51Z  
Role: PHX-HARDWARE  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
Branch: `phoenix/hardware-storage-preflight-device-separation-20261126-utc23`  
PR: [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356) (OPEN / DRAFT / UNMERGED)  
Base: `blazepwifi-v0.6.0-audit-foundation` at `2fbd2475e9f54878c316fa7cea2f228386b0e859`  
Current source/test commit: `414048cdc390c7ade2207661ca7e5009c413389e`

## Defect and correction

The ESP32 sketch unconditionally included `mbedtls/sha256.h`, which is unavailable in the Arduino ESP32 core 4.0.0 Mbed TLS 4 environment.

The sketch now selects the provider by `MBEDTLS_VERSION_MAJOR`:
- Mbed TLS 3: checked `mbedtls_sha256_starts/update/finish/free` sequence.
- Mbed TLS 4: PSA `psa_crypto_init` + `psa_hash_compute(PSA_ALG_SHA_256)`.

Both providers reject initialization/status/output-length failures. A 64-character hexadecimal validator rejects malformed output; `signedBody` returns empty on invalid digest; `post` refuses an empty body before opening/sending HTTP.

**Registration compatibility correction:** the provisional empty-key/empty-ID guard was removed in commit `414048cdc390c7ade2207661ca7e5009c413389e`. The existing setup path calls `post("register")`; first-boot registration may be the bootstrap path. This compile-compatibility change must not silently redefine the provisioning contract or block the existing register request. No request fields/action semantics or poll trust behavior were changed.

## Regression tests

The source-contract lab `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_sha256_compat_lab.py` verifies:
- Mbed TLS 3/4 provider selector and isolated headers.
- PSA initialization/status/output-length checks.
- Mbed TLS 3 return-code checks.
- SHA-256 output format validation.
- Invalid digest and empty-body fail-closed ordering.
- A negative mutation rejecting a newly introduced empty-key/empty-ID guard in this compatibility patch.
- Seven unsafe source mutations are rejected (the final suite includes the bootstrap-preservation mutation).

The workflow `.github/workflows/phx-hw-active-v06-esp32-core-compat.yml` pins Arduino CLI 1.6.0 and the Espressif package-index commit `8f6bee9761f7b15cce27b79cbd1ae199d0df2adf`, and compiles exact staged source twice on ESP32 cores 3.3.13 and 4.0.0.

## Exact-head evidence

Earlier source head `050f0f0ca53533e8609ff0cb63e414538a50d132` passed both matrix versions, but contained the provisional empty-key/empty-ID guard; it is superseded and is not the final source evidence.

Current corrected source `414048cdc390c7ade2207661ca7e5009c413389e`:
- Push matrix [#45936317966](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936317966): source-contract job `140300234891` PASS; target jobs `140300234637` (3.3.13) and `140300234916` (4.0.0) were IN PROGRESS at this checkpoint.
- PR matrix [#45936322663](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936322663): source-contract job `140300249152` and target jobs `140300249338` (4.0.0), `140300249386` (3.3.13) were IN PROGRESS at this checkpoint.

Prior docs head `496b4855fa19a6e88623b6a5060200731da39045`:
- Matrix push [#45935926733](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935926733) and PR [#45935932053](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935932053) PASS on cores 3.3.13 and 4.0.0, with byte-identical clean A/B application images. This was before the registration-preservation correction.
- Storage preflight push/PR [#45935926748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935926748) / [#45935932042](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935932042) PASS.
- Full [#45935932101](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45935932101) passed validation and all 14 target/platform build jobs but was cancelled before simulation/release jobs completed after the next source commit. Not a Full PASS.

## Evidence boundary and blockers

`SIMULATED_ONLY=1`; `COIN_ADMISSION_ENABLED=0`. Compile CI does not establish runtime crypto correctness, physical acceptance or production controller authorization.

150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain NOT TESTED / NOT ACCEPTED. No flash, live money, production migration, release or deployment occurred.

## Next exact action

Read terminal matrix and Full results for `414048cdc390c7ade2207661ca7e5009c413389e`, refresh PR body and UTC03 checkpoint, and request independent PHX-QA review. Keep PR #356 DRAFT and unmerged.
