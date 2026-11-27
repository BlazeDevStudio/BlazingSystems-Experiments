# R281 one-click installer — encrypted private package

This contains the **complete owner-specific installer ZIP**, encrypted with AES-256-GCM because the Experiments repository is public. The firmware inside contains saved passwords, SSH/TLS private keys, network settings and private device backups. **The decryption key is deliberately not uploaded.** Keep it separately backed up; the encrypted file cannot be restored without it.

The owner's local key is in the separate `R281-GitHub-Recovery` output folder. Do not commit that folder or key to any public repository.

## Restore the original ZIP

Download this folder's encrypted archive, `MANIFEST.json`, and `decrypt-installer.py`. Use Python with the `cryptography` package and the separately retained key:

```text
python decrypt-installer.py --key /private/path/R281-installer-recovery.key
```

On the prepared laptop, the existing installer's `native/lib` directory can be supplied through `--library-path`, so no package download is needed. The helper checks the encrypted checksum, authenticated encryption tag and original ZIP checksum before writing. It refuses to overwrite an existing output file.

Extract the restored ZIP and open `README.html`. `START-Unlock-and-Install.bat` verifies the pinned device and chooses native upgrade or the supported stock PLDT recovery path. It retrieves fresh modem key records, unlocks only when needed, saves backups, guides any required TFTP power/reset steps, verifies the new immutable root and exports the matching recovery image. Native upgrade requires no manual power/reset action.

## Current status and limits

- Candidate build: `2026.10.05-reset-defaults-4.2.3`; EasyMode source remains [4.2.3](../v4.2.3-r281-experiment/).
- The refreshed image passed 2,331 filesystem-entry checks, original factory-format reconstruction, native image validation and full current-default comparison. Installer guard and transfer tests passed.
- **Not flashed or reset-tested.** The actual installer stopped before writes because the pinned Ethernet adapter was disconnected. This package does not establish reset persistence on the currently running router.
- The TFTP BIN restores AP firmware and baked defaults. It is not a whole-chip clone of the bootloader, calibration and cellular processor. Logical partition backups are separate diagnostic files, not TFTP images.
- Stock migration with this new image remains untested end to end. USSD, fresh physical captive login and sustained cellular reliability remain unfinished.

This remains in **Experiments**. The package is tied to the audited laptop/router and the owner's Windows account. Do not treat it as generic R281 firmware or publish the decrypted contents or key. This upload performs no router flash.
