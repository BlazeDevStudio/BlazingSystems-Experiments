# Reconciliation log

2026-10-18:
1. Dedicated repository name was not accessible, so project placed in isolated
   `experiments/BlazeHackintosh/` directory of `BlazingSystems-Experiments`.
2. OpenCore upstream v1.0.8 versus Dortania guide front-page 1.0.6 is treated
   as documentation drift; no blind Sample.plist copy.
3. 31 CPU family entries are taxonomy only; no automatic EFI for unverified hardware.
4. Browser security prevents arbitrary PC scanning; browser UI performs manual reference
   checks, while Python scanner performs local read-only discovery.
5. No destructive disk operations, Apple binary redistribution or unverified IMG files.
6. Lucide SVGs are packaged offline under ISC; original CSS handles backgrounds/buttons.

## 2026-10-19 — upstream OpenCore documentation drift and archive evidence
- Acidanthera's official GitHub OpenCorePkg 1.0.8 release remains listed as latest, published 2026-09-27: https://github.com/acidanthera/OpenCorePkg/releases/tag/1.0.8 ; pinned asset metadata were checked through the GitHub release API. Record SHA-256 and size in docs/TEST-EVIDENCE.md.
- Dortania's publicly visible installation guide continues to advertise **supported version 1.0.6**: https://dortania.github.io/OpenCore-Install-Guide/ ; do not assume guide screenshots, quirks, or sample configurations automatically match pinned 1.0.8 binaries. Use authoritative OpenCorePkg 1.0.8 Configuration.pdf and Sample.plist when building/checking the project.
- Dortania's generated documentation page also cautions that OpenCorePkg's official documents are authoritative: https://dortania.github.io/docs/ .
- Apple software license terms require separate checking for the particular macOS version and restrict permitted installation and redistribution; an OpenCore ZIP archive check does not change Apple license rules: https://www.apple.com/legal/sla/ .
- Real archive CI confirms ZIP bytes and CRC against pinned metadata, not independent supplier identity; provider-key attestation, license notices and per-device EFI acceptance remain OPEN.

## 2026-10-19 — GPT/FAT32 image structure, not physical acceptance
- Microsoft's *Extensible Firmware Initiative FAT32 File System Specification* v1.03, December 6 2000, pp. 21–22 (https://www.cs.fsu.edu/~cop4610t/assignments/project3/spec/fatspec.pdf) puts FSInfo's `FSI_Reserved2` at bytes 496–507 and `FSI_TrailSig` at bytes 508–511 (value 0xAA550000). Audit code checks 508; the earlier local draft that checked 496 was incorrect and must not be integrated.
- Windows can expose differing inode/device IDs between path `lstat` and opened-handle `fstat`; image-auditor source reuses `archive_integrity._same_opened_file` with bounded regular-file, size and reparse checks. Full opened-handle SHA-256 is recomputed after structural reads; no promise of complete TOCTOU race immunity.
- Passing GPT CRC, FAT32 boot metadata samples and hashes verifies a *synthetic disk file* only: no FAT-chain walk, directory tree verification, real EFI files, end-to-end USB restore, publisher identity/license verification or physical boot evidence. Gate classification remains unchanged.
