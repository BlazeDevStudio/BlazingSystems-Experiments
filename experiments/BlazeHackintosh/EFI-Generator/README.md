# EFI Generator: read-only validation milestone

This directory currently documents the actual `../efi_validator.py` CLI.
It is an **inspector**, not an EFI generator, disk writer, macOS downloader or boot validator.

## Usage

```powershell
python blazehackintosh.py validate-efi --efi "D:\EFI-folder" --output check.json
python efi_validator.py --efi "/path/to/existing/EFI-folder"
```

The directory can be an EFI root containing `EFI/OC`, the `EFI` directory
itself, or an existing `OC` directory. The validator parses `OC/config.plist`,
checks presence of `OpenCore.efi`, examines enabled ACPI, kext, UEFI driver
and tool references, flags duplicates and rejects path traversal and external
symlinks. It can flag absence of `BOOT/BOOTx64.efi` as a warning.

Tests intentionally use dummy files that are not UEFI-executable binaries:
a "structural_checks_passed" result only says the configured references resolve
locally. It does not validate executable integrity, ACPI semantics, GPU support,
SMBIOS suitability, version compatibility, APFS, OpenCore schema or boot success.

**MANDATORY BEFORE EFI ACCEPTANCE:** use `ocvalidate` from the **same OpenCore
release** as the EFI and check its errors. The inspector does not automatically
execute or download unverified ocvalidate binaries. Then run real hardware
tests with documented backup/rollback procedures.

Sources:
- https://github.com/acidanthera/OpenCorePkg/tree/master/Utilities/ocvalidate
- https://github.com/acidanthera/OpenCorePkg/blob/master/Docs/Configuration.tex

The toolkit never writes the inspected EFI directory and never executes its contents.
