# Read-only GPT/ESP image audit (experimental)

This feature is a **regular-file-only** auditor. It must not accept physical block devices, mount images, write disks, or assert macOS boot success.

## Acceptance boundaries

- Require an independently supplied full SHA-256 digest and check the entire regular `.img` file.
- Validate protective MBR, both GPT headers and partition-table CRCs, primary/backup consistency, partition bounds and overlap, and a single EFI System Partition.
- Perform only FAT32 boot-sector plausibility checks; these do **not** establish filesystem integrity, that an EFI loader exists, or that the image can boot.
- Reject symlinks, reparse points, device paths, missing hashes, hybrid MBRs and malformed metadata.
- Emit explicit false values for `physical_readback_verified`, `filesystem_verified`, `boot_verified`, and `safe_to_flash`.

A synthetic in-memory or temporary-file test is **not** an image readback from a real USB device. Actual physical-drive writing, rollback, boot acceptance, component authentication, and production release gates remain blocked pending independent evidence and explicit operator authorization.

Do not claim a passing structural audit authorizes flashing or establishes hardware compatibility.
