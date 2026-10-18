# Expert-only Haswell candidate staging

**Status: v0.1.4 experimental research builder. NOT a ready-to-boot installer.**

The builder produces a *new, isolated folder* `BlazeEFI-*` containing an EFI layout
from the official, **SHA-256 verified** OpenCore 1.0.8 RELEASE ZIP plus supplied
local kexts, SSDTs, HFS driver, and SMBIOS values. A produced research candidate
is only accepted if both in-project structural validation and the real matching
`ocvalidate` pass. This never proves it boots or works on the user's hardware.

Dortania desktop Haswell reference:
https://dortania.github.io/OpenCore-Install-Guide/config.plist/haswell.html

## Profile gate (narrow by design)

- Confirmed UEFI, exact Intel Core i5-4570 or i7-4770 name.
- **One** GPU, exact PCI `8086:0412` (Haswell Intel HD 4600); no discrete GPU.
- Motherboard model must be reported, but motherboard compatibility is **unverified**.
- macOS 12 only for this research profile, not a promise that any installation works.
- Local hardware scan JSON required. Unsupported or ambiguous devices are rejected.
- Generic SMBIOS profile explicitly set to `iMac14,2`; this project does not
  claim that model selection or the supplied identity is valid for every board.

## Required separately sourced local inputs

- Original **OpenCore 1.0.8 RELEASE ZIP**, unmodified and hash matched.
- `--kext-dir` containing `Lilu.kext`, `VirtualSMC.kext`, `WhateverGreen.kext`
  with Info.plist and executable. No unreviewed online downloads or bundled kexts.
- `--acpi-dir` with previously reviewed, target-specific
  `SSDT-PLUG.aml` and `SSDT-EC.aml`.
- `--hfs-driver` pointing to separately obtained `HfsPlus.efi`.
- `--smbios-json` with **locally generated** `SystemProductName`,
  `SystemSerialNumber`, `MLB`, `SystemUUID`, `ROM` (6-byte hex).
  Keep this file private: never commit/upload a real SMBIOS identity.
- Existing parent directory and an **absent** child directory named `BlazeEFI-*`.
  No existing path is overwritten and no disks are partitioned or mounted.

Example:

```powershell
BlazeHackintosh-Toolkit.exe scan --output target-report.json
BlazeHackintosh-Toolkit.exe plan-haswell --report target-report.json --macos 12
BlazeHackintosh-Toolkit.exe stage-haswell-efi --report target-report.json --macos 12 --zip OpenCore-1.0.8-RELEASE.zip --kext-dir C:\LocalKexts --acpi-dir C:\LocalAcpi --hfs-driver C:\LocalDrivers\HfsPlus.efi --smbios-json C:\Private\smbios.json --output-dir C:\Research\BlazeEFI-Haswell --acknowledge-research-only
```

The builder writes a manifest, per-file SHA-256, research-notice marker and
non-boot-certified EFI files only to the new staging directory. If any validation
fails, it deletes the temporary staging files and leaves no candidate output.
It never writes an ESP, partition table, MBR, UEFI boot entry, or internal disk.

**Important limitations:** source kext binaries, SMBIOS identity provenance,
ACPI applicability, DSDT/EC specifics, framebuffer configuration, BIOS quirks,
USB maps, network/audio, power management, NVRAM, installer resources, update
support and real physical boot remain unverified. OpenCore Sample.plist itself
warns not to use it unmodified. Do NOT flash this research candidate blindly.

Unit-test components and Windows CI's staged components are deliberately
**fake and non-bootable**. CI checks generated configuration structural/schema
validity only. Those fake components and identities are not published as EFI.
