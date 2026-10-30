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

## CI-tested implementation (2026-10-19)
`image_audit.py` exposes `audit_image(path, expected_sha256)` and a read-only CLI:
```
python image_audit.py --image disposable.img --expected-sha256 <operator-provided-sha256>
```
Exit 0 means bounded ordinary-file hash and structural checks passed **only**. Exit 2 means a failed audit. A passing result is not a bootable installer, filesystem validation or permission to flash.

A disposable, sparse ~40 MiB synthetic GPT/FAT32 fixture is used by `Tests/test_image_audit.py`; it deliberately contains no usable boot payload. Windows-safe pathname/opened-handle identity comparison reuses `archive_integrity._same_opened_file`; it still does not claim to prevent sophisticated Windows symlink races. The FAT32 FSInfo trailing signature is checked at byte **508**, 0xAA550000, per Microsoft's FAT32 Specification v1.03 (Dec 2000), pp. 21–22: https://www.cs.fsu.edu/~cop4610t/assignments/project3/spec/fatspec.pdf .

CI evidence: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222346177 and https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39222341172 (237 Python tests each platform). No image writer, restore or physical disk operation is provided by this module.

## Disposable file roundtrip regression
Two additional `Tests/test_image_audit.py` cases verify copying the synthetic 40 MiB image into a private temporary .img, readback integrity, rejection after simulated corruption, restoration from a temporary backup, and rejection of interrupted copies. Source and destination are ordinary temporary files; `shutil` and `os.replace` are exercised **inside tests only**. This is not the deliverable physical disk writer, migration utility, FAT32 filesystem content validator or rollback proof. CI: https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/39224322821.

## Experimental short-name EFI-file payload readback (draft PR #257; 2026-10-30)
`esp_readback.audit_boot_efi(image_path, expected_image_sha256, expected_boot_file_sha256)` is a separate read-only helper for **ordinary .img files only**. It first requires the existing GPT/ESP/FAT32 metadata audit to pass, then opens the same pinned image bytes read-only and follows the FAT32 directory/FAT chain for exactly `EFI/BOOT/BOOTX64.EFI` using 8.3 short names. It verifies the SHA-256 of the actual file content, including multiple clusters, and rehashes the opened image handle before returning. Any unhandled LFN, oversized directory/file, missing entry, FAT cycle, inconsistent mirrored FAT or mismatched digest fails closed.

It deliberately does **not** support arbitrary file paths, verify every FAT entry, check complete filesystem integrity, validate an EFI executable, or write to a disk. Return flags `physical_readback_verified`, `filesystem_verified`, `boot_verified` and `safe_to_flash` stay false even on success. The synthetic 700-byte payload is not real OpenCore or a deployable loader.

RED CI: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988387682 ; GREEN 245 Linux/245 Windows: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40988558649 .
