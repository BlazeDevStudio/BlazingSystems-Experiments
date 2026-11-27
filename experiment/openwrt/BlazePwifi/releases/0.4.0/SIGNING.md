# BlazeRental v0.4 production signing

BlazeRental v0.4 uses a locked **fresh production certificate** for the final Launcher Edition release.

Production SHA-256 certificate fingerprint:

`C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

Package ID remains `com.blazesystems.blazerental`.

## Upgrade compatibility

This v0.4 production identity is **not** the v0.3 certificate. Android therefore will not accept the v0.4 APK as an in-place update over a v0.3 installation with the same package ID.

For v0.4 deployment, use clean/factory-reset Device Owner provisioning or remove the old v0.3 package before installing v0.4. Existing v0.3 installations that must retain app data require the original v0.3 private key; that recovery path remains separate and is not claimed as completed here.

## Signature schemes

The production APK is required to verify with:

- v1/JAR signing for Android 5.x/6.x compatibility.
- APK Signature Scheme v2.
- APK Signature Scheme v3.

The locked production signer uses RSA-3072.

## Identity lock and recovery

The exact production identity is recorded in `.github/blazerental-v04-production-identity.json`. Future BlazeRental updates must reuse that certificate. Generating another fresh signing identity would break Android update compatibility again.

The private production keystore is not committed. Its recovery copy is encrypted and sealed to the offline transfer public key. The encrypted backup, encrypted AES key, IV, signer certificate, fingerprint and signing manifest are included with the production release. The matching transfer private key must remain offline and private.

The one-time fresh signer workflow is no longer an automatic push workflow after identity lock.
