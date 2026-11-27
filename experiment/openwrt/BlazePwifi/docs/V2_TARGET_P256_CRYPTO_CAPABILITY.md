# PAY-0721 — OpenWrt target P-256 signing primitive feasibility (LAB ONLY)

**Status: IMPLEMENTED_UNTESTED / NOT a production signer.** Source issue [#31](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/31), blocked dependencies #43 independent antirollback and #34 real hardware. No live v2 member payments.

## Exactly what is tested

- `tools/v060_p256_target_capability_probe.c` uses **the official OpenSSL EVP API** to generate a disposable P-256 key entirely in volatile process memory, ECDSA/SHA-256 sign fixed nonfinancial probe bytes, serialize **public-only** SPKI DER, destroy the private key *before* verification, verify the signature and reject altered bytes. It never produces a BlazePwifi `ACKP1`, contains no persistent server private-key format or provisioning code, and refuses compilation without `BLAZE_V2_P256_CAPABILITY_LAB_ONLY`.
- `tests/v060_p256_target_capability_probe.sh` builds and runs the **host** program and requires its explicit `PRODUCTION_SIGNER_AVAILABLE=0`, `PRIVATE_KEY_PERSISTED=0`, `CUSTOMER_PAID_ACK_AUTHORIZED=0` fields; an unguarded compile must fail.
- `openwrt/lab-native/Makefile` compiles the identical source using the existing official OpenWrt 25.12.5 SDK **target** compiler and the matching target OpenSSL libcrypto. Only laboratory `blazepwifi-v2-native-lab` artifacts are produced, never the customer image `PACKAGES` set. Compile-time group-name and EVP ECDSA calls are required by `-Werror`.
- `tools/v060_cross_compile_native_lab.sh` locates the compiled P-256 ELF for each target, asserts correct machine architecture with `readelf -h`, dynamic target `libcrypto` dependency with `readelf -d`, emits checksums and `MANIFEST.txt` explicitly denying physical target runtime and private-key custody evidence.

| Image kind | SDK compile target | Customer ImageBuilder `openssl-util` requested | Physical P-256 signing/key custody |
| --- | --- | --- | --- |
| Ruijie RG-EW1200G Pro | ramips/mt7621 MIPS | **No** | **UNVERIFIED / NO-GO** |
| x86_64 | x86/64 X86-64 | Yes (package request only) | **UNVERIFIED / NO-GO** |
| Orange Pi Zero3 | sunxi/cortexa53 AArch64 | Yes (package request only) | **UNVERIFIED / NO-GO** |

An SDK **crosscompiled** libcrypto-dependent ELF is not proof that the signed OpenWrt image actually installs the requisite crypto modules, that P-256 runs under target OpenSSL/entropy/memory constraints, or that a server's private key can be protected against ordinary user access, backup leakage, restoration/rollback, firmware update, or compromise. It is not proof of a secure element, TPM, RPMB, or an independent high-water witness.

## Mandatory unresolved integration

The real signed `cgi-bin/vendo` still rejects every `member_v2_*` request before heartbeat/money mutation, so it cannot issue an `ACKP1`. The Windows public-key verifier exists but is not wired to a trusted P-256 production server response. Before any protected server signer could be enabled: (1) prove real target OpenSSL runtime and entropy/performance; (2) design off-device/private-key custody and out-of-band Windows pin distribution/rotation, no signer private key in CI; (3) integrate a **single crash-atomic, independently fresh** member+receipt authority with authenticated controller sequence; (4) simulate injected after-commit lost ACK, target fsync, and actual power interruption, then 30+ clients/24 hours; (5) owner-authorized auditable v1 migration. User-facing customer upgrade/production 0.6 remains DENIED.

**Source audit scope:** one target SDK primitive check, not more HMAC/ACK fixtures. If a target cannot crosscompile/link EC primitives, record the exact target failure and gate it unsupported. Do not silently add `openssl-util` to constrained Ruijie image or claim secure private-key storage.

**Handover:** [CURRENT_STATE](handover/CURRENT_STATE.md), [CHANGE_LEDGER](handover/CHANGE_LEDGER.md), [PAY-0720 public ACK wire](V2_PUBLIC_SERVER_ACK_TRUST.md).
