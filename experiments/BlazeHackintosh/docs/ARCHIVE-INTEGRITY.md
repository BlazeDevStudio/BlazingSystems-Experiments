# Read-only ZIP integrity audit

The Python module archive_integrity.py checks an **operator-supplied local ZIP** against a supplied 64-character lowercase SHA-256 pin and exact byte size. It examines ZIP metadata, streams each member and checks CRC without extraction, downloads, execution or physical disk writes. Failure produces exit code 2.

From experiments/BlazeHackintosh/:

    python archive_integrity.py --archive /path/to/asset.zip --sha256 <sha256> --size <bytes>

This is groundwork for integrating the separately reviewed component-provenance candidate. No downloads are automatic. The operator must independently establish which publisher, signed key, license and release bytes are trustworthy; GitHub API asset digests and GitHub-hosted repository text are **not** independent supplier attestations.

Safeguards: no linked archive, bounded regular file, streamed hash before and after examination, stat/race detection, ZIP CRC, path traversal and Windows names, duplicate/case collisions, symlink/special entries, compression/size/expansion limits. It deliberately rejects some unusually encoded but legitimate ZIPs.

Do not treat a passing scan as permission to extract, run, redistribute or install its contents. A matching SHA-256 does not establish independently authenticated publisher identity. Do not promote any mandatory BlazeHackintosh production gate based on this check alone.

Regression tests: Tests/test_archive_integrity.py uses only disposable synthetic archives. No actual supplier releases, Windows GUI, USB media, real EFI payloads or physical boots are tested.
