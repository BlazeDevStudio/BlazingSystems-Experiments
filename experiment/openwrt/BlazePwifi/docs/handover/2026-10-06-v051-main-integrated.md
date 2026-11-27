# Handover Log — 2026-10-06 — v0.5.1 Integrated Into Main

## Success

The full published BlazePwifi v0.5.1 implementation is integrated into the repository default branch.

Published release remains:
- tag: `v0.5.1`
- exact candidate: `65f87d775793a1fdc09a9522cf752349f68c3b41`
- build run: `37425063793` — PASS
- release run: `37426030884` — PASS
- release ID: `404404262`

## Main divergence reconciliation

Main had five newer commits containing 19 standalone-rental/release paths that were not present on the v0.5.1 implementation branch.

Those files were preserved byte-for-byte while overlaying the complete v0.5.1 release tree.

Reconciled integration commit:
`e081c6bdfc41d22ac07f918c4cbc62a745bca883`

Integration tree:
`f1c0194f8039577bad88a6e93b02d9b837e228c2`

Integration build run:
`37426701445`

Result: **PASS**

It passed:
- full validation/security/config/integration/stress suite;
- v0.5.1 transactional update/rollback regression;
- v0.5.1 BlazeRental update contracts;
- update-bundle generation;
- BlazeRental normal + rescue APK build;
- Android Device Owner emulator;
- browser simulation;
- ESP8266/ESP32 build + simulation;
- Ruijie build + simulation;
- x86 build + QEMU simulation;
- required Orange Pi builds + simulations;
- final candidate gate.

## Merge

PR #14:
`release: integrate BlazePwifi v0.5.1 into main (reconciled)`

Result: **MERGED**

Main merge commit:
`1aa8926563e6dccb6a512a035e8f6f662b997d57`

The merge tree is exactly the already-green integration tree:
`f1c0194f8039577bad88a6e93b02d9b837e228c2`

Post-merge `main` build run:
`37427339687`

Result: **PASS**, including Android Device Owner emulator, x86 QEMU and final candidate gate.

Superseded PR #13 was closed without merging.

## Release identity

The merge did not move or rewrite `v0.5.1`.

The release still targets:
`65f87d775793a1fdc09a9522cf752349f68c3b41`

It remains a prerelease solely because production BlazeRental signing requires the exact locked v0.4 identity, which is not currently available in GitHub secrets/recovery.

Locked signing run `37425929657` failed safely and refused certificate rotation.

## Next action

When the exact locked v0.4 signer is restored:
1. rerun v0.5.1 locked signing against build run `37425063793` and candidate `65f87d775793a1fdc09a9522cf752349f68c3b41`;
2. verify both normal and rescue APK fingerprints;
3. refresh the existing v0.5.1 release with signed `BlazeRental.apk` and signed rescue;
4. promote v0.5.1 out of prerelease;
5. do not rebuild or retag the application unnecessarily.

## Audit & Reconcile prompt

```text
@GitHub Reconcile BlazePwifi from the v0.5.1 main-integrated state.

1. Read experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md.
2. Read the newest handover log, especially 2026-10-06-v051-release-published.md and 2026-10-06-v051-main-integrated.md.
3. Verify main contains merge commit 1aa8926563e6dccb6a512a035e8f6f662b997d57 or a descendant.
4. Verify the v0.5.1 implementation is present on main and the 19 standalone-rental/release files remain present.
5. Verify integration run 37426701445 passed for reconciled SHA e081c6bdfc41d22ac07f918c4cbc62a745bca883, and post-merge main run 37427339687 passed for merge SHA 1aa8926563e6dccb6a512a035e8f6f662b997d57, including Android Device Owner, x86 QEMU and final candidate gates.
6. Verify GitHub Release v0.5.1 still targets exact published candidate 65f87d775793a1fdc09a9522cf752349f68c3b41 and remains prerelease unless the exact production signer has since been restored.
7. Verify build run 37425063793 and release run 37426030884 remain successful.
8. Preserve transactional no-reflash updates, last-known-good rollback, boot health guard, v0.5.0 bootstrap updater, same-signer Rental APK verification, health promotion and rescue APK architecture.
9. Preserve Android signing fingerprint C7:7E:4D:A2:2E:92:D2:BE:7D:93:B9:D3:DC:7C:3F:77:56:C0:6A:5A:13:0E:C6:90:5A:DC:C2:AD:4E:A3:56:24 and never silently rotate it.
10. If the exact signer becomes available, sign the existing validated v0.5.1 candidate, refresh the release and promote it without unnecessary rebuilds.
11. Update PROJECT_HANDOVER.md and add a dated handover log after every meaningful success/failure with a fresh Audit & Reconcile prompt.
```
