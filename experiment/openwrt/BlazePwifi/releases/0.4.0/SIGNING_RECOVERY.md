# BlazeRental signing recovery

The v0.3 production APK was signed by a key generated in GitHub Actions run
`37210720716`. That run produced an encrypted recovery handoff containing:

- the production keystore backup encrypted with AES-256-CBC;
- the AES key encrypted with the BlazeRental RSA transfer public key using OAEP/SHA-256;
- the IV;
- the public certificate and fingerprint.

The current production certificate fingerprint is:

`F6:8F:A0:41:A8:15:2C:C6:9C:77:C9:7A:D2:95:45:E8:25:9F:D0:DD:27:41:2C:58:F9:12:21:7D:D1:C0:B2:B9`

## v0.4 signing paths

The v0.4 signing workflow accepts either:

1. `BLAZERENTAL_KEYSTORE_B64` + `BLAZERENTAL_KEYSTORE_PASSWORD`; or
2. `BLAZERENTAL_TRANSFER_PRIVATE_KEY_PEM`, which allows the workflow to decrypt
   the preserved v0.3 recovery handoff and restore the exact signing identity
   only for the duration of the signing job.

The transfer private key must never be committed to the repository or release
assets. If it is unavailable, the project cannot cryptographically produce an
in-place-update-compatible APK with the v0.3 package identity. A new key would
only be suitable for fresh enrollment/reprovisioning.

The preservation workflow copies the still-live encrypted handoff into a
90-day Actions artifact so the recovery material is not lost while the final
production signing secret is being restored.
