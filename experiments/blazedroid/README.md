# BlazeDroid 16 — Android 16 x86-64 foundation

**State: EXPERIMENTAL / NOT INSTALLABLE YET. No BlazeDroid ISO has been built, booted, or released.**

BlazeDroid is separate from the other Blaze Systems products. This source tree is a controlled Android 16 build entrypoint, **not** an operating-system release.

## Verified source selection (2026-10-21)

- [Lineout Core / los-tv-x86 Android 16 manifest](https://github.com/los-tv-x86/lineage_bass_android/tree/lineage-23.2): `default.xml` uses AOSP `android-16.0.0_r4`; manifest commit locked in [foundation.lock.json](foundation.lock.json).
- [x86-64 tablet product](https://github.com/los-tv-x86/android_device_generic_x86_64_tablet/blob/lineage-23.2/AndroidProducts.mk): lunch target `lineage_x86_64_tablet-userdebug`, **not Android TV**, by default (`USE_TV_BUILD=false`).
- [Āropa installer](https://github.com/Bliss-Bass/bootable_aaropa/commit/8c6a69fd8d7728ceeddefd42470a488d9785339f): integrated by upstream as `bootable/aaropa`. Calamares and all installer functionality require boot/installation testing; **Windows dual boot is not certified**.
- BlissOS `typhoon-x86` is **Android 13** (its `default.xml` pins `android-13.0.0_r77`) and is deliberately not used.

Upstream's manifest includes both floating branch dependencies and possible third-party firmware/prebuilts. A checked-out manifest commit alone **is not a bit-for-bit reproducible source lock**. The build exports a resolved `repo manifest -r` snapshot for provenance.

## Build (dedicated Linux build host only)

Do **not** run the full build on standard GitHub-hosted runners. Supply a dedicated Linux x86-64 build machine with ample CPU, RAM and disk (plan at least 32 GiB RAM and 300+ GiB free; these are **build-host planning allowances**, not tested end-user requirements), and install the Android/Lineage dependencies, Android `repo`, `git-lfs`, Python 3, `xorriso`, and `sha256sum`.

```bash
python3 -m unittest discover -s experiments/blazedroid/tests -v
bash experiments/blazedroid/scripts/build-iso.sh "$HOME/blazedroid-source" "$HOME/blazedroid-output"
```

The build command refuses nonempty source directories that lack a `.repo` checkout, verifies the manifest and pinned installer commit, uses the upstream `iso_img` target, and refuses builds whose `build.prop` lacks Android 16 / API 36. It copies an ISO **only if** upstream produced exactly one image, and checks its optical filesystem and EFI boot catalog before writing a SHA-256 checksum. Artifacts are labeled **experimental** pending acceptance.

To run manually in GitHub Actions use the `BlazeDroid 16 foundation` workflow with `full_build=true` **only after** registering a capable runner labeled `blazedroid-aosp`. This workflow does not create GitHub releases and does not certify a bootable product.

## Release blockers (fail closed)

1. Full repo sync + Android 16 compile on a capable builder, with logged manifest and provenance.
2. EFI and BIOS QEMU boot, live boot, launcher and resizable-window checks, Android version verification inside the guest.
3. Āropa graphical installer launch, clean installation, reboot, persistence and error handling.
4. Dual-boot validation with **disposable Windows images**; test UEFI/ESP, BitLocker, hibernation, rollback and boot entry preservation. Never resize users' real Windows disks during development.
5. Physical x86-64 PC checks, Rufus/YUMI checks, network/audio/graphics compatibility and hardware requirements.
6. Google Play requires distribution permission/certification. AOSP-only is the only configured edition; no GApps or Play Integrity bypasses.

Until these pass, do **not** rename a generated experimental ISO to `BlazeDroid-16.0.0-x86_64.iso` or publish a production release.

## Legal and attribution

AOSP, LineageOS, Android-Generic, Āropa/Calamares, Devuan, Linux and respective third-party code retain their upstream copyrights and licenses. Review all resolved dependency licenses and redistribution rights (especially firmware/codecs) **before** distributing an image. No Google proprietary packages are downloaded or included by this repository. The upstream BlissOS licensing guide explicitly distinguishes public personal-use GApps images from authorized commercial distribution.
