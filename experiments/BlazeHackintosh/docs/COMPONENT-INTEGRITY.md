# User-supplied component integrity ledger — v0.1.5 experimental

This is a **local SHA-256 consistency gate**, not independent upstream verification.
The toolkit does NOT download, execute or redistribute kext/SSDT/HFS drivers for
you. You must obtain these separately, validate the vendor, release and license,
and preserve their applicable notices. Apple/HfsPlus component licensing may
restrict redistribution. Do not publish private SMBIOS identities or diagnostics.

## Required manifest

Pass `--component-manifest C:\Private\components.json` to
`stage-haswell-efi`. The JSON must contain `schema_version: 1` and a complete
`files` array. Each entry must have exactly a relative `path`, lower-case
64-digit SHA-256 `sha256`, `source_url` (HTTPS), `release` and `license_id`.

Example entry (illustrative only; replace every value and verify directly):

```json
{
  "schema_version": 1,
  "files": [
    {
      "path": "Drivers/HfsPlus.efi",
      "sha256": "REPLACE_WITH_REAL_LOWERCASE_64_DIGIT_SHA256",
      "source_url": "https://example.org/replace-with-upstream",
      "release": "REPLACE",
      "license_id": "REPLACE"
    }
  ]
}
```

The example is **not sufficient**: the complete list must cover EVERY regular
file inside:
- `Kexts/Lilu.kext/` (including executable, Info.plist, resources)
- `Kexts/VirtualSMC.kext/`
- `Kexts/WhateverGreen.kext/`
- `ACPI/SSDT-PLUG.aml` and `ACPI/SSDT-EC.aml`
- `Drivers/HfsPlus.efi`

No extra ACPI payloads are accepted in the current restricted profile.
For each file, compute the SHA-256 locally (e.g. on Windows:
`Get-FileHash -Algorithm SHA256 -LiteralPath "C:\LocalKexts\Lilu.kext\Contents\Info.plist"`).
Record and verify original project/release URLs and exact applicable licenses
against their publishers. Do not use a generic web search result as provenance.

The builder compares every source file with the declared hash, copies dependencies
into a new temporary research output folder, checks EVERY copy against the same
manifest, and runs existing structural and official OpenCore schema tests.
Failures clean temporary output and do not overwrite existing directories.

**Important distinction:** a manifest that hashes to itself and contains
self-declared URLs proves only matching bytes to operator-provided expectations.
It cannot establish that those files came from the claimed vendor, that a license
allows your use, that an SSDT fits your motherboard, or that macOS can boot.
Vendor-signed release verification and physical hardware tests remain mandatory.
