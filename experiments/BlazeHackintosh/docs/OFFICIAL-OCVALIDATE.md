# Pinned OpenCore ocvalidate — trust model

OpenCore's official \`ocvalidate\` checks \`config.plist\` syntax and schema for a **specific**
OpenCore release, not hardware compatibility. The BlazeHackintosh structural inspector
remains independent and read-only. Combining both results is stronger configuration
inspection, **not proof of a usable EFI or physical boot**.

Source: https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8
Upstream release date: 2026-09-27
Verified official OpenCore 1.0.8 RELEASE ZIP SHA-256:
\`2011e8b7216ecb2645d97ea710df965947edd406846e92050b9bc4190be6d27b\`

Official usage reference:
https://github.com/acidanthera/OpenCorePkg/blob/master/Utilities/ocvalidate/README.md
It explicitly requires a version-matched binary and a single \`config.plist\` argument.

## Offline workflow

Download the **official RELEASE ZIP yourself** from the upstream link. Do not
repackage it or trust an unofficial binary. Verify before execution:

\`\`\`powershell
BlazeHackintosh-Toolkit.exe verify-opencore-package --zip OpenCore-1.0.8-RELEASE.zip
\`\`\`

Then, only when you explicitly approve executing the verified upstream checker:

\`\`\`powershell
BlazeHackintosh-Toolkit.exe validate-efi --efi D:\MyOfflineEFI --ocvalidate-package OpenCore-1.0.8-RELEASE.zip --run-official-ocvalidate --output results.json
\`\`\`

- Requires exact SHA-256 of the full original official archive before extracting a
  single \`Utilities/ocvalidate\` executable into an isolated temporary directory.
- Requires \`ocvalidate --version\` to confirm **1.0.8** before passing \`config.plist\`.
- No automatic networking, binary downloads, unverified execution, EFI mutation,
  formatting, OS boot configuration changes or diagnostic uploads.
- Fails closed for missing/incompatible platforms, versions, invalid ELF/PE,
  unsupported package layouts and unexpected tool errors.
- Refuses symbolic links for \`config.plist\`; emits structured report and no
  boot-success claims. Command output may contain local EFI configuration details,
  so handle exported JSON reports privately.
- This integration currently supports only the pinned **1.0.8 RELEASE** archive.
  Never silently replace an upstream release or auto-select latest versions.
- Physically testing a complete EFI and additional GPU/firmware/macOS compatibility
  evidence are still mandatory before describing any EFI as working.

**Security caution:** running an approved, hash-verified upstream binary still
executes code on your device. Use on trusted systems only, keep backups, and do not
run downloads from unofficial sources. ZIP verification alone performs no execution.
