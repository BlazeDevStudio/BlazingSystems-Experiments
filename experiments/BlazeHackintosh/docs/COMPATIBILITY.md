# Compatibility policy

There are seven intended evidence classes:
- Hardware Verified
- Community Reported
- Structurally Validated Only
- Untested
- Experimental
- Known Incompatible
- Research Only

**Current state:** every one of the 31 CPU-family taxonomy records is **Research Only**.
The reference lookup knows eight exact CPU SKUs for architecture identification alone.
Unmapped or ambiguous CPU strings result in **Unknown**, not a convenient nearby CPU family.

No recommended macOS version, supported GPU, SMBIOS, generated EFI, SSDT, kext bundle,
tested USB image or boot-success claim exists in this initial milestone.

A future selection algorithm must require relevant CPUID/instructions, exact GPU PCI ID,
chipset, UEFI firmware, ACPI requirements, target macOS version, version-matched ocvalidate,
and evidence; if those are absent it must stop short of claiming boot compatibility.
