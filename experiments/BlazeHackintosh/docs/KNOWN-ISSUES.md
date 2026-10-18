# Known issues and release blockers

1. **No usable EFI generator**: Sample.plist customization, kext/SSDT selection,
   dependency manifests, GPU probing and matching ocvalidate still unimplemented.
2. **Limited scanner**: PowerShell may be unavailable/blocked; BIOS/UEFI and exact PCI
   properties remain incomplete; Linux lspci is optional. Windows firmware is intentionally Unknown.
3. **Limited CPU SKU map**: only eight identified sample CPU model names; 31 family entries
   cannot be used to claim coverage of all CPUs in these families.
4. **No hardware verification**: zero physical Hackintosh boot-test evidence.
5. **Not a compiled GUI**: Windows Actions produces a console scanner executable only;
   standalone browser UI is a research-preview frontend.
6. **No disk functions**: USB flashing, EFI migration, multi-boot preservation and rollback
   remain blocked pending explicit safety design and virtual-disk destructive tests.
7. **No released IMG/ISO/installer**: none exist; never advertise empty images.
8. **Documentation drift**: Dortania guide version indicator differs from official
   OpenCorePkg release; must reconcile config schema before EFI generation.
9. **License constraints**: respect Apple's macOS restrictions; keep third-party notices.

These are not silently deferred production features. v0.1.0 is experimental only.
10. **Scanner inventory completeness:** Windows CIM and Linux optional utilities may return null; `missing_inventory_evidence` documents gaps and does not imply incompatibility. GPU vendor:device alone does not establish acceleration or kext support.

11. **Read-only EFI inspector is not ocvalidate**: it only checks existence of enabled component references and basic path integrity. It cannot validate OpenCore schema, binary authenticity, version compatibility, actual boot paths or hardware. See EFI-Generator/README.md.
11. **Official validator binary requires consent:** user-supplied version 1.0.8 RELEASE ZIP must match exact pinned SHA-256 before any attempt to execute an extracted binary. A successful ocvalidate verifies a config schema only; real EFI executable signatures, hardware support and physical boot are NOT established. Unavailable layouts/platforms fail closed.
12. **Initial builder is narrow and research-only:** only desktop Haswell i5-4570/i7-4770, sole Intel HD 4600 PCI 8086:0412, UEFI and macOS 12 are permitted for staging. Supplied SSDTs/kexts/SMBIOS/HfsPlus are NOT authenticated by the builder; their applicability must be manually checked. No boot guarantees or IMG/flashing support.
13. **Operator-declared component manifest is not upstream authenticity:** v0.1.5 checks each kext/ACPI/HFS SHA-256 at input and output but cannot independently establish that the source URLs/licenses/releases entered by the operator are truthful, nor prove kext signing or device compatibility. Supplier signatures, trusted known-good release pins, and physical hardware testing remain blockers.
