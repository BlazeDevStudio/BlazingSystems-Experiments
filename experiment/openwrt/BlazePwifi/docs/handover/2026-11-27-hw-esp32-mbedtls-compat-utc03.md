# PHX-HARDWARE — ESP32 Mbed TLS 3/4 compatibility

Updated: 2026-11-27T03:57:28Z  
Role: PHX-HARDWARE  
Repository: BlazeDevStudio/BlazingSystems-Experiments  
Branch: `phoenix/hardware-storage-preflight-device-separation-20261126-utc23`  
PR: [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356) (OPEN / DRAFT / UNMERGED)  
Base: `blazepwifi-v0.6.0-audit-foundation` at `2fbd2475e9f54878c316fa7cea2f228386b0e859`  
Current source/test commit: `414048cdc390c7ade2207661ca7e5009c413389e`  
Current docs head: `0cf729e3708f719b87b5006b1712b39a52a17eef`

## Defect and correction

The ESP32 sketch unconditionally included `mbedtls/sha256.h`, which is unavailable in the Arduino ESP32 core 4.0.0 Mbed TLS 4 environment.

The sketch now selects the provider by `MBEDTLS_VERSION_MAJOR`:
- Mbed TLS 3: checked `mbedtls_sha256_starts/update/finish/free` sequence.
- Mbed TLS 4: PSA `psa_crypto_init` + `psa_hash_compute(PSA_ALG_SHA_256)`.

Both providers reject initialization/status/output-length failures. A 64-character hexadecimal validator rejects malformed output; `signedBody` returns empty on invalid digest; `post` refuses an empty body before opening/sending HTTP.

**Registration behavior preservation:** source inspection confirmed the existing setup path calls `post("register")`; first-boot registration may be the bootstrap path. The provisional empty-key/empty-ID guard was removed in commit `414048c`. This compatibility change does not redefine provisioning or alter request fields/action semantics.

## Regression and exact-SHA evidence

The source-contract lab `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_sha256_compat_lab.py` rejects eight unsafe mutations:
- missing version selector;
- missing PSA initialization failure guard;
- missing PSA status/output-length check;
- missing legacy Mbed TLS status check;
- missing invalid-digest deny;
- introduction of an empty-key/empty-ID bootstrap deny;
- missing empty-body HTTP deny;
- missing unsupported-version deny.

### Corrected source/test SHA `414048cdc390c7ade2207661ca7e5009c413389e`

- Push matrix [#45936317966](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936317966): source-contract job `140300234891` PASS; ESP32 core 3.3.13 `140300234637` PASS; ESP32 core 4.0.0 `140300234916` PASS.
- PR matrix [#45936322663](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936322663): source-contract `140300249152` PASS; core 3.3.13 `140300249386` PASS; core 4.0.0 `140300249338` PASS.
- Clean A/B application SHA-256: core 3.3.13 `0212a6ad1d428ad7be5710b551d4710b6620baf0700bdaab86b58b086ed95dbe`; core 4.0.0 `3f40193818dfc45e417e64666b583751d04fc706fa48c899a6cd349e1385d282`.

### Current docs head `0cf729e3708f719b87b5006b1712b39a52a17eef`

- Push matrix [#45936438399](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936438399): source-contract `140301209367` PASS; core 3.3.13 `140301209428` PASS; core 4.0.0 `140301209082` PASS.
- PR matrix [#45936443708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936443708): source-contract `140301233345` PASS; core 3.3.13 `140301232987` PASS; core 4.0.0 `140301233211` PASS.
- Both cores used staged source tree SHA-256 `d62d786c00f1845f857fafc1d1dce9d7a90e16ca3c130751a12fd388fd09a6df`. Docs-head clean A/B application SHA-256: core 3.3.13 `308f0f1f97038c1346b2a6737432c068cfbda20a15b1f6d3c44fdd68ef27f9c0`; core 4.0.0 `742d6729355ef365757d70db3e978c28a7be1be8e0f4e1d77f09fd5a47fc3944`. Each pair was byte-identical.

## Full integration and storage evidence

- Full PR [#45936443886](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936443886) completed SUCCESS at docs head `0cf729e`: validation job `140300788918` PASS; 14/14 target/platform build jobs PASS; 9/9 v0.4 synthetic simulations PASS; update bundle job `140301744469` PASS. Production import/signing, sign handoff, prerelease and release jobs were SKIPPED.
- Storage preflight PR [#45936443677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936443677), job `140300635005` PASS: `CHANGE_LEDGER_DELETED_LINES=0`, `CHANGE_LEDGER_APPEND_ONLY_PASS`, STORCHK-0674 physical-parent matrix PASS, `SIMULATED_ONLY=1`.
- Native synthetic journal gate [#45936443771](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45936443771) PASS.

## Evidence boundary and blockers

These are CI VERIFIED / SIMULATED results only. They do not establish runtime cryptographic correctness or physical acceptance. 150 controlled power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain NOT TESTED / NOT ACCEPTED. No flash, live money, production migration, release or deployment occurred. Production remains NO-GO.

## Next exact action

Request PHX-QA independent review of the Mbed TLS provider and ledger guard; PHX-MASTER refreshes stale #356 pins in PR #288; PHX-HARDWARE resumes the next owned unblocked task and does not change poll/coin admission before CORE's authenticated #177 contract. Keep PR #356 DRAFT and unmerged.
