# PAY-0720 — public-verifiable member server acknowledgment (WORK IN PROGRESS)

**State:** Real Windows SoftTimer verifier shipped as source/compiled app; NO v2 payment sender, server signer or customer authority. Issues #31/#43/#34 remain blocking.

## Proposed wire contract (v2 only)

The application accepts exactly ten tab-delimited ASCII fields, with at most one final LF:

```text
ACKP1<TAB>COMMIT|REPLAY<TAB>key-id<TAB>controller<TAB>sequence<TAB>controller:sequence<TAB>request-sha256-lowercase-hex<TAB>result-seconds<TAB>member-revision<TAB>signature-base64-DER
```

The *signed bytes* are exactly (UTF-8/ASCII):

```text
BLAZEPWIFI-MEMBER-V2-ACK/ECDSA-P256-SHA256/1<LF>
ACKP1<TAB>...<TAB>member-revision<LF>
```

Only nine ACK fields are signed; the tenth carries the RFC3279 DER P-256 ECDSA/SHA-256 signature. The client requires a locally pre-provisioned **SubjectPublicKeyInfo DER base64** pin and a key ID. It verifies curve OID `1.2.840.10045.3.1.7`, canonical numbers, signature encoding, exact controller, sequence, immutable event identity `controller:sequence`, pending request SHA-256 fingerprint, result, revision, outcome, and domain. Signature/receipt verification is not acceptance of server durability, witness freshness, or key provisioning.

The client must never receive a private key or accept a downloaded/advertised/TOFU public key as its trust anchor. Key rotation or key-ID changes are forbidden while an unresolved member financial transaction exists. Prior synthetic symmetric ACKV1/ACKV2 **cannot substitute** for `ACKP1`.

## Live safeguards and tests

- Actual Windows source: `V2MemberServerAckVerifier.cs`, `AppConfig.cs`, `AppController.cs`, `BlazePwifiClient.cs`, `Program.cs`; compiled app has public-key `VerifyData` only and a read-only headless verification probe.
- The separate `tests/V2PublicAckProbe` signs disposable in-memory test data with an ephemeral key, then launches the compiled WinExe and checks forged/wrong key, tampered amount/revision/context, replay identity mismatch, downgrade, algorithm mismatch, unsupported key rotation, invalid encoding, and valid `COMMIT` and `REPLAY`.
- Existing real `BlazePwifiClient.CallDetailedWithNonce` still BLOCKS `member_*` when v2 is required. OpenWrt `cgi-bin/vendo` still denies every signed `member_v2_*` before heartbeat or money mutation. **Nothing clears or spends paid credit as a result of this verifier.**
- PAY-0720 adds NO private-key generator, no signer in customer firmware, no live key material, and no v1 financial migration.

## Production readiness gaps / target evidence

The current `build/build-openwrt-image.sh` package set includes `openssl-util` for x86/SBC image kinds, but **not** the Ruijie small-router image path. No supported target's physical `openssl dgst -sha256 -sign` capability, secure private key storage, secure activation, signer error/rollback semantics or latency is yet verified; an OpenWrt package list is not physical signing evidence. Introducing this verifier does NOT justify enabling a P-256 server ACK issuer until these are demonstrated.

Required before enabling v2 money: durable atomic member+receipt authority and independent monotonic external freshness #43, signed challenge/sequence bound to controller queue, fail-closed clock/key rollover, owner-controlled pinned public-key provisioning and protected rotation, no v1 fallback, physical target fsync and power interruptions, reversible explicit migration, 30+ client/24h and signer identity acceptance #34. Server keys must remain server-only and never be provided to CI or clients.

**Safety:** `VERSION=0.5.3`, `CUSTOMER_INSTALL_AUTHORIZED=0`, `PRODUCTION_v0.6.0_RELEASED=0`.
