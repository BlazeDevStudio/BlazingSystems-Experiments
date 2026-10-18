# BlazeHackintosh — experimental foundation (v0.1.4 experimental Haswell candidate staging)

**Status:** v0.1.0 development foundation, **NOT** a complete Hackintosh installer or EFI generator.

BlazeHackintosh is a hardware-aware OpenCore research and preparation initiative.
This directory is isolated within BlazingSystems-Experiments until a dedicated repository can be created.
No files outside this namespace and its named GitHub Actions workflow are owned by this project.

## What is real now
- Python standard-library **read-only** Windows/Linux/macOS-adjacent hardware scanner; JSON output.
- Expert-only Haswell desktop EFI research candidate staging, requiring supplied kexts/ACPI/HFS/SMBIOS and both structural and official schema validation; see [docs/HASWELL-STAGING.md](docs/HASWELL-STAGING.md).
- User-authorized, SHA-256-pinned OpenCore 1.0.8 ocvalidate validation (requires separately supplied official ZIP, never downloaded or executed implicitly); see [docs/OFFICIAL-OCVALIDATE.md](docs/OFFICIAL-OCVALIDATE.md).
- Read-only OpenCore EFI structural inspection: referenced ACPI, kext, UEFI driver and tool paths, with traversal/duplicate checks (not ocvalidate).
- Windows GPU/network vendor:device PCI IDs, firmware mode, memory and non-sensitive physical storage inventory; analogous best-effort Linux probes.
- Explicit CPU SKU reference lookup with safe **Unknown** fallback.
- 31 Intel/AMD **research-only taxonomy entries** and a validated database structure.
- Offline manual-reference browser UI with scanner JSON import, interactive evaluation and JSON export.
- Automated Python tests and a Windows command-line executable build workflow.
- Locally vendored Lucide ISC SVG icons, with license notice.
- Source documentation, known limitations and handover record.

## What is not implemented
- Universal or hardware-verified OpenCore EFI generation, macOS installer creation, disk flashing or EFI migration. Haswell research staging is available with individually supplied components; no ready-to-boot EFI is shipped.
- CPU/GPU-level boot validation or real hardware acceptance.
- A compiled *graphical* Windows Setup Assistant (the browser UI is a reference preview).
- Offline complete macOS installer, Linux recovery ISO, IMG images, dual-boot manager and GitHub Release.

## Use without installing dependencies

Install Python 3.10+ and execute from this directory:

```powershell
python blazehackintosh.py scan --output hardware-report.json
python blazehackintosh.py evaluate --report hardware-report.json
python blazehackintosh.py catalog --output families.json
python blazehackintosh.py validate-efi --efi "D:\\EFI-folder" --output inspection.json
python -m unittest discover -s Tests -v
```

The optional `--output` only writes to the **file path you choose**; without it output goes to the console.
The scanner does not read user documents, partition disks or execute network requests. PnP instance IDs, MAC addresses, serials and UUIDs are not exported. Reported disk models and sizes are read-only descriptors.
On Windows it queries read-only WMI/CIM properties via PowerShell; Linux uses /proc/cpuinfo and optional lspci.
Unknown values are retained rather than guessed. JSON reports remain local unless you choose to share them.

**Graphical preview:** open `Setup-Assistant/index.html` in a browser with the adjacent `assets` directory. The UI is offline. It cannot scan local hardware from a browser.

**Windows CLI build:** GitHub Actions compiles `BlazeHackintosh-Scanner.exe` on `windows-latest` using a pinned PyInstaller version; inspect the actual workflow result before trusting a build. The executable is a console scanner, not a one-click macOS installer.

## Licensing / legal caution
This project is not affiliated with Apple or Acidanthera. Apple's macOS software licenses restrict installation to Apple-branded computers; see https://www.apple.com/legal/sla/ and the agreement for the desired macOS version. No macOS binaries or modified installers are distributed. Third-party code and icons must retain their notices; see LICENSES.

## Engineering gates
A matched CPU family does not mean the CPU/GPU/chipset/firmware/macOS combination will boot.
No EFI inspector success may be described as successful official ocvalidate or a bootable EFI. No files in this milestone may be described as a validated EFI image, bootable USB image, or physical-hardware success.
Future EFI generation must use a version-matched OpenCore Sample.plist, required kexts and ocvalidate.

See [docs/README.md](docs/README.md), [docs/KNOWN-ISSUES.md](docs/KNOWN-ISSUES.md) and [DEVELOPMENT-HANDOVER.md](DEVELOPMENT-HANDOVER.md).

## Previous verified experimental downloads

- [v0.1.2-alpha.1 Windows toolkit and offline UI](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.2-alpha.1)
- [Latest test run](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39080929664): 25 Python unit tests passed on each Linux and Windows runner; packaged Windows executable smoke-tested.
- `validate-efi` checks only local EFI references, does not use official `ocvalidate`, and never proves physical boot.

All graphical preview assets remain locally bundled and licensed as described in `LICENSES/`.

- [v0.1.3-alpha.1 toolkit — with optional official, digest-pinned OpenCore 1.0.8 ocvalidate](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.3-alpha.1): 36 Linux and 36 Windows tests passed, plus actual upstream-checker rejection of intentionally invalid EFI (both source and Windows EXE); this remains experimental, **not a macOS installer**.

## Latest verified prerelease

- [v0.1.4-alpha.1 Windows toolkit and offline UI](https://github.com/BlazingSystems/BlazingSystems-Experiments/releases/tag/blazehackintosh-toolkit-v0.1.4-alpha.1) — restricted Haswell EFI research candidate staging, optional official 1.0.8 ocvalidate, Windows executable, SHA-256 manifest.
- [Validated GitHub Actions run](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39091108747) — 48 tests on each platform, Windows CLI compiled and smoke-tested, real official OpenCore 1.0.8 validator accepted synthetic reference config generated with fake third-party components.
- **NOT A READY-TO-BOOT EFI**: real component provenance, physical boot and supported macOS installation remain untested.
