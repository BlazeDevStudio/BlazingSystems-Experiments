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
