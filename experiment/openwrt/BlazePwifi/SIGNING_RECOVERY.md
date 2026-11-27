# BlazeRental Production Signing Recovery

This file is the permanent entry point for BlazeRental Android production signing continuity.

## Active production lineage

Starting with BlazeRental **v0.5.2**, production releases use:

- Lineage name: `BlazeRental-production-lineage2`
- Android package: `com.blazesystems.blazerental`
- First production release: `v0.5.2`
- Frozen application candidate: `bf2992977fe8504d21b107df02826032c31d3a62`
- Validated build run: `37443570618`

The one-time Lineage-2 signing run succeeded. The fingerprint below is now permanent for all future BlazeRental production APKs.

## Recovery architecture

The plaintext production PKCS12 keystore and password are **never committed to Git**.

The v0.5.2 release stores an authenticated encrypted signing backup using:

- payload encryption: AES-256-GCM;
- key wrapping: RSA-OAEP-SHA256;
- two independent owner recovery public keys.

Recovery A public-key SHA-256:

`e6c24a4bc3533170747d99c5debc7522cbf31097a2e08091514f98895ef2159d`

Recovery B public-key SHA-256:

`f15466ab3af75e7174dbb0a7bf7bb30c25540be5fb3da9e291d241146437bfac`

Public keys:

- `.github/blazerental-v052-recovery-A-public.pem`
- `.github/blazerental-v052-recovery-B-public.pem`

Private recovery keys are deliberately outside Git:

- Recovery A: owner-private ChatGPT Library copy under `/BlazePwifi Signing Recovery/`;
- Recovery B: independent owner/offline copy.

Either private recovery key can recover the exact production signing backup.

## Release recovery assets

The signed v0.5.2 release must contain:

- `BlazeRental-v0.5.2-lineage2-signing-backup.enc`
- `BlazeRental-v0.5.2-lineage2-signing-nonce.bin`
- `BlazeRental-v0.5.2-lineage2-key-recovery-A.enc`
- `BlazeRental-v0.5.2-lineage2-key-recovery-B.enc`
- `BlazeRental-RECOVERY-MANIFEST.json`
- `BlazeRental-signing-cert.pem`
- `BlazeRental-signing-fingerprint.txt`
- `unseal-blazerental-lineage2.py`

## Local recovery

Download the encrypted recovery assets from release `v0.5.2`, then use one owner private recovery key:

```bash
python3 -m pip install cryptography
python3 unseal-blazerental-lineage2.py \
  --private-key /secure/path/recovery-private.pem \
  --wrapped-key BlazeRental-v0.5.2-lineage2-key-recovery-A.enc \
  --encrypted-backup BlazeRental-v0.5.2-lineage2-signing-backup.enc \
  --nonce BlazeRental-v0.5.2-lineage2-signing-nonce.bin \
  --manifest BlazeRental-RECOVERY-MANIFEST.json \
  --out BlazeRental-v0.5.2-lineage2-signing-backup.tar.gz
```

If using Recovery B, use the B wrapped-key asset instead.

Extract the recovered archive only on a trusted local machine. It contains the production PKCS12 and its password.

## Mandatory future signing rule

Every production BlazeRental APK after v0.5.2 must verify against the exact Lineage-2 certificate fingerprint recorded below. A workflow must fail closed if a different certificate is presented.

Do not:

- generate a replacement production signer silently;
- commit the plaintext PKCS12 or private recovery keys;
- Base64/rename/split a private key as a substitute for encryption;
- use an online decoder for recovery material;
- sign an ordinary future release with a different certificate.

## Migration boundary

The v0.5.2 Lineage-2 certificate intentionally replaces the abandoned old v0.4 production lineage.

Devices carrying BlazeRental signed by the old v0.4 certificate cannot perform an ordinary in-place APK signature update to Lineage 2. Reprovision/factory reset is required for migration. Once provisioned with v0.5.2 Lineage 2, future releases must keep this Lineage-2 certificate.

## Verified signing creation and recovery

- Signing workflow run: `37448352082` — PASS
- Signing artifact: `11404278200`
- Recovery A end-to-end decrypt/P12 fingerprint drill: PASS
- Recovery B end-to-end decrypt/P12 fingerprint drill: PASS
- Signed BlazeRental SHA-256: `d0ad20bed00ea304db9bff45928542fed574070d416ed65b4fbf3d8ba23d7102`
- Signed rollback-rescue SHA-256: `a1c8d759405842b85879c77e9525b1a6e9c4f6d62eb8bda9b0abc60fb899d513`

## Production certificate fingerprint


`1A:18:D5:8E:1F:95:55:96:89:10:20:71:F5:6C:93:E9:B9:D2:EA:6B:E4:0E:6F:20:70:06:C9:89:62:A1:6A:25`
