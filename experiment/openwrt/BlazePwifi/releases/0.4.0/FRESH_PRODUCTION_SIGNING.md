# BlazeRental v0.4 locked production identity

The one-time fresh production signing bootstrap completed successfully.

- Candidate: `1373eaa8ee8e95abbc2d0cbf5565d8ed28d2a750`
- Validated build run: `37268063117`
- Signing run: `37279036434`
- Signed APK SHA-256: `944d0da425fbcd591fa37801ed549db6d5707690d4e6417961eaca392b240fb0`
- Certificate SHA-256: `C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24`

The matching private signing key is stored only inside an encrypted recovery backup. The backup is sealed to the transfer public key whose DER SHA-256 is:

`2a6a19de7b07ad756afd1f60c40a58776aa20f2e2daeb2e8e980219891b54a3e`

The transfer private key is intentionally not committed. It must be retained offline by the owner. Losing it makes the encrypted recovery backup unusable and would prevent future APK updates using this identity.

This identity is for clean/fresh v0.4 provisioning and is not update-compatible with the older v0.3 certificate.
