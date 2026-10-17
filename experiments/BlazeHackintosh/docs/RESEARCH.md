# Research checkpoint — 2026-10-18

## OpenCore
The official Acidanthera OpenCorePkg GitHub latest-release endpoint returned **1.0.8**, published 2026-09-27.
Its release includes the Windows macrecovery fix and launch-helper changes.
Source: https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8
Confidence: high for the release metadata at the time checked. New releases require rechecking.

## Guide drift
The Dortania OpenCore Install Guide repository front page still describes its current
supported version as **1.0.6**. It is NOT evidence that all published guide values
are validated for OpenCore 1.0.8. Before generating config.plist, compare official
OpenCore 1.0.8 Configuration.pdf, Sample.plist and Differences.pdf with relevant Dortania
architecture guidance, and run **matching** ocvalidate.
Source: https://github.com/dortania/OpenCore-Install-Guide
Confidence: high for observed version mismatch.

## Hardware constraints
Dortania explicitly warns that CPU support does not establish integrated-GPU support.
Its hardware limitations document calls out a Haswell iGPU ceiling at macOS 12,
while desktop Coffee Lake and Skylake have separate configuration paths.
CPU family alone is insufficient for selecting an installer or promising acceleration.
Sources:
- https://dortania.github.io/OpenCore-Install-Guide/macos-limits.html
- https://dortania.github.io/OpenCore-Install-Guide/config.plist/haswell.html
- https://dortania.github.io/OpenCore-Install-Guide/config.plist/skylake.html
- https://dortania.github.io/OpenCore-Install-Guide/config.plist/coffee-lake.html

## AMD-specific blocking details
AMD Vanilla documents use of ProvideCurrentCpuInfo for supported CPU families and
specific physical core-count replacement requirements. It also documents Zen 4
IOPCIFamily-related changes. This project MUST NOT inject generic AMD patches without
determining CPU family, physical core count and target macOS version.
Source: https://github.com/AMD-OSX/AMD_Vanilla
Confidence: high for source rules, not independent physical hardware verification.

## Third-party graphics
Lucide icon library licensed ISC (copyright Lucide Icons and Contributors);
source SVGs are vendored locally with complete license notice.
Sources: https://lucide.dev/license and https://github.com/lucide-icons/lucide/tree/main/icons
No royalty-based backgrounds, remotely loaded assets or Apple logo artwork are used.

## Legal
Apple software license terms are version-dependent and generally restrict macOS installation
to Apple-branded hardware. No Apple macOS images or modified installers are hosted.
Source: https://www.apple.com/legal/sla/

## Research still required
- Compare detailed OpenCore 1.0.8 Configuration.pdf to Dortania 1.0.6-current text;
- verify precise GPU/PCI support and macOS version rules for each exact SKU;
- verify authoritative kext releases, licenses and dependency hashes;
- design generated-EFI reproducible ocvalidate checks and non-destructive image tests;
- establish appropriately licensed distribution method for dependency packages.
