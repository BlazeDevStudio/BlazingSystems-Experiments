# PAY-0722 — v2 OpenWrt target signing custody / hardware admission decision

**Decision status: NO-GO / no production issuer (12 October 2026 Asia/Manila).**
Owner project: Full BlazePwifi, issue #31; dependencies #43 and #34.
This is a build/release acceptance specification, not authority to migrate paid balances or enable `member_v2_*`.

## What is proven versus missing

PAY-0720 compiled Windows client can verify a pinned **public** P-256 SPKI ACKP1 envelope while refusing an untrusted sender; it has no private-key API. PAY-0721 proves OpenWrt **SDK cross-compile/link** of ephemeral P-256 EVP sign + verify against real target libcrypto on MIPS MT7621, x86/64 and AArch64. Neither proof demonstrates the executable can run on an actual router, nor signer custody, secure provisioning, atomicity or independent freshness.

OpenWrt's `openssl-util` **installs a command-line executable** and depends on `libopenssl`/`libopenssl-conf`; it is not an HSM/TPM-backed key provider, signer service or protected identity. The Full ImageBuilder currently requests `openssl-util` on x86/SBC but **not** Ruijie. An SDK-linked ELF is not automatically installed in any Full image. Enabling production signing from this evidence would be unsound.

## Decision and per-target constraints

| Hardware | Actual command-line/runtime admission | Proposed non-exportable custody | State |
| --- | --- | --- | --- |
| Ruijie RG-EW1200G Pro (MT7621) | `openssl-util` absent from requested image list; no physical ELF test | No proven onboard protected signer, TPM, RPMB or monotonic storage | **UNSUPPORTED FOR PRODUCTION v2 UNTIL OWNER TEST EVIDENCE** |
| x86/64 PC server | ImageBuilder requests tool only; no real booted target probe | TPM 2.0 + hardware-bound nonexportable P-256 key through reviewed PKCS#11/provider **if actually present and tested** | **NOT PROVEN** |
| Orange Pi Zero3 (AArch64) | ImageBuilder requests tool only; no physical runtime probe | Independently provisioned secure-element / hardware signer **if actually present and tested** | **NOT PROVEN** |
| Other routers/ESP nodes | No PAY-0721 target binary proof | Unknown | **NOT ADMITTED** |

TPM2-PKCS11 is an example of an interface to an **actual TPM 2.0**, not evidence these devices possess or safely expose one. A root-only PEM file on flash does not become non-exportable through file permissions, encryption using a locally stored passphrase, or putting the key in an APK/installer. A signing key must **never** be generated in public CI or committed to firmware, Git, update bundles, online QR, a Windows client or backup exports.

## Exact owner/operator-only physical runtime prerequisite (no production payments)

New **off-device source only**: `tools/v060_p256_physical_runtime_probe.sh`. It is never installed by BlazePwifi firmware. The operator must use an owner-controlled, isolated, **noncustomer** OpenWrt 25.12 target and manually choose and copy the correct official-SDK `p256-primitive-probe-TARGET` ELF from the checked build artifacts. Verify the artifact using its SHA256 manifest **and trusted workflow/source commit context**. An unsigned checksum by itself cannot prove publisher identity.

After the operator verifies the source/run digest, the isolated test target copy must be owned by the invoking UID, a **single-link regular nonsymlink file with chmod 0500 (read/execute owner only)**. The wrapper validates this before execution. Run only on an owner-isolated machine with trusted root operators; even this guard and matching checksum are not cryptographic artifact provenance or a defense against compromise by the same privileged owner.

After placing the selected LAB binary at a private isolated `/tmp/blaze-v2-p256-probe-UNIQUE` location and arranging execution permission, the operator may run:

```sh
sh v060_p256_physical_runtime_probe.sh --operator-isolated-target --candidate /tmp/blaze-v2-p256-probe-UNIQUE --sha256 LOWERCASE_64_HEX_SHA256
```

The script does **not** install packages, write keys, read BlazePwifi financial state, send network packets, or modify UCI. It rejects calls without operator consent, non-OpenWrt/unsupported architecture, wrong candidate path, absent/mismatched hash, missing bounded `timeout`, and unexpected binary output. The existing PAY-0721 binary generates an **ephemeral in-memory-only key** to sign and verify fixed *nonfinancial* probe bytes; the wrapper only reports success on exact output and prints all production gates as zero/unverified. **This is a live test only when actually executed on the device by the owner; CI runs a host refusal test, not hardware.** Only capture the redacted output; never attach secrets, token PINs, private files or customer ledgers.

A PASS would establish a small *runtime crypto primitive* prerequisite. It does not establish key custody, performance under load, TPM availability, HMAC controller sequencing, source receipt fsync, restore freshness, power interruption or customer v0.6 admission. No physical result has been supplied as of this checkpoint.

## Minimum signer and ledger architecture before implementation/activation

1. **Signer selection:** for each exact hardware/SOC, demonstrate trusted nonexportable key custody (secure element / TPM 2.0 under an appropriately restricted dedicated signing process), software package dependencies, entropy, resource limits, after-reboot identity stability, noninteractive operation and recoverability. If impossible for a target, reject v2 there instead of silently substituting a file PEM.
2. **Owner-controlled public pin:** provision stable `key-id` + **SPKI DER** certificate/public-key hash into Windows SoftTimer out of band; no trust-on-first-use, no download of new pin from the same unauthenticated signing endpoint. A lost-ACK pending receipt forbids silent rotation. Device-owner rental provisioning QR is separate from SoftTimer public-key enrollment.
3. **Money authority first:** a single authenticated, crash-atomic member balance+receipt journal with retained event ID and controller sequence (no truncation as UI history rotates). Only after durable commit, expected controller identity, ledger revision, external freshness witness and key validation may the server construct and sign `ACKP1`. A signing service must not independently decide or mutate balance.
4. **Error/replay:** log a key ID and request digest in authority; repeat a lost ACK by signing the **same immutable committed receipt**; mismatched source, amount, sequence, member or controller fails closed. Uncertain durability, missing witness or signer unavailability means **no success ACK**, no Windows pending-operation clearing, and no v1 fallback.
5. **Independent rollback witness (#43):** the signing key or signature does not prevent a valid old ledger snapshot from being restored. Require an authenticated, external monotonic high-water commitment physically separated from restorable member journal; proof on target and recovery must precede production.
6. **Release acceptance (#34):** isolated physical power cuts before/after durable boundary, boot/restart and controller resend, 30+ client/24h, trusted provisioning and signing identity checks, approved backup/key recovery with no private key export, owner-reviewed v1 migration with dry run and explicit no-downgrade. Record exact hardware model, firmware, SHA and redacted observed outputs in a private test record.

**NO-GO constants remain:** `VERSION=0.5.3`, `CUSTOMER_INSTALL_AUTHORIZED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `PRODUCTION_v0.6.0_RELEASED=0`. Real `cgi-bin/vendo` continues rejecting every signed `member_v2_*` before heartbeat or money mutation; the public Windows verifier cannot convert that rejection into a paid success.

**Useful references:** OpenWrt's official `package/libs/openssl/Makefile` `Package/openssl-util` declares command-line utility and `libopenssl-conf` dependence; `tpm2-software/tpm2-pkcs11` documents PKCS#11 interface to TPM 2.0, not hardware presence. Source evidence: `docs/V2_TARGET_P256_CRYPTO_CAPABILITY.md`, `docs/V2_PUBLIC_SERVER_ACK_TRUST.md`, `tests/v060_v2_public_ack_runtime_boundary.sh`.
