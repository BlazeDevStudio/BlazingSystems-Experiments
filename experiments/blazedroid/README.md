# BlazeDroid 16 — Android 16 x86-64 PREVIEW

**Release policy: PREVIEW / UNTESTED ON HARDWARE.** Early images can be published without VM or physical-PC testing, at the owner's explicit request. **No successful ISO compile has yet been recorded in this repository.** Do not confuse source-validation CI with a bootable operating system.

BlazeDroid is an independent Android desktop OS project, isolated from all coin-operated Blaze Systems projects. Only a genuine Android 16 image built from this source can be called a BlazeDroid 16 preview.

## Upstream Android 16 foundation

- [los-tv-x86 LineageOS 23.2 manifest](https://github.com/los-tv-x86/lineage_bass_android/tree/lineage-23.2) references AOSP `android-16.0.0_r4`; commit pinned in [foundation.lock.json](foundation.lock.json).
- [x86-64 tablet hardware product](https://github.com/los-tv-x86/android_device_generic_x86_64_tablet/blob/lineage-23.2/AndroidProducts.mk): reused for drivers and platform configuration (not Android TV when `USE_TV_BUILD=false`).
- **BlazeDroid-owned Android product:** `device/blazedroid/x86_64/blazedroid_x86_64.mk` in this tree inherits that x86-64 tablet device. The actual build selects `lunch blazedroid_x86_64-userdebug`, setting `PRODUCT_BRAND=BlazeDroid`, `PRODUCT_MODEL=BlazeDroid 16 Preview`, and system `ro.blazedroid.*` properties. This is source configuration, not yet proof of a successful image build.
- [Bliss-Bass Āropa installer commit](https://github.com/Bliss-Bass/bootable_aaropa/commit/8c6a69fd8d7728ceeddefd42470a488d9785339f): upstream installer base including Calamares. Installer launch has not been verified.
- BlissOS `typhoon-x86` manifest is Android 13, so it is **not** used.

This manifest still includes some floating upstream dependency branches. Every successful build exports `resolved-manifest.xml` with concrete resolved revisions.

## Build and preview publication

A full AOSP compilation needs a **dedicated Linux x86-64 build host**, with preinstalled Android/Lineage build prerequisites, Android `repo`, `git-lfs`, Python3 and `xorriso`. Plan for at least 32 GiB RAM and 300+ GiB of free SSD storage as an unverified build-host allowance. Standard GitHub-hosted runners are not adequate. Register a trusted self-hosted GitHub Actions runner labeled **`blazedroid-aosp`**.

1. The `BlazeDroid 16 preview build` workflow must exist on the repository's **default branch** for the GitHub **Run workflow** UI to work.
2. Select **Actions → BlazeDroid 16 preview build → Run workflow → main**, and set `full_build=true`.
3. Choose `publish_preview=true` only when you want a public preview. Before setting `redistribution_approved=true`, verify that all bundled upstream firmware, binaries, and codecs may lawfully be redistributed. Otherwise an Actions artifact is uploaded **without** a public release.
4. The build checks pinned source/installer commits, stages the BlazeDroid-owned product definition, selects its own `lunch` target, compiles `iso_img`, requires Android 16/API 36 **and** `ro.blazedroid.version=16.0.0` / `ro.blazedroid.channel=preview` in built properties, verifies the ISO optical structure plus EFI catalog, creates SHA256 checksums, and uploads PREVIEW artifacts. Source overlay digests are written to `blazedroid-overlay-SHA256SUMS` during the build.
5. When a release is authorized and the build succeeds, GitHub Releases creates a **prerelease** tagged `blazedroid-v16.0.0-preview.<run_number>`. There is **no VM or physical acceptance test requirement**.

Build locally on a trusted machine:

```bash
python3 -m unittest discover -s experiments/blazedroid/tests -v
bash experiments/blazedroid/scripts/build-iso.sh "$HOME/blazedroid-source" "$HOME/blazedroid-output"
python3 experiments/blazedroid/scripts/prepare_preview.py \
  --iso "$HOME/blazedroid-output/BlazeDroid-16.0.0-x86_64-PREVIEW.iso" \
  --manifest "$HOME/blazedroid-output/resolved-manifest.xml" \
  --output "$HOME/blazedroid-preview-assets"
```

**A branded makefile is not a built ISO, and no real ISO exists just because these scripts pass syntax or unit tests.** Check the *full-build* job logs and actual artifact files.

### ISO download format

For ISOs that fit GitHub Releases' **under-2 GiB per asset** limit, download `BlazeDroid-16.0.0-x86_64-PREVIEW.iso` directly. Larger ISOs are losslessly split into `.part001`, `.part002`, etc., and include a `REASSEMBLE_WINDOWS.cmd` script (Windows) plus `SHA256SUMS`. On Linux, reconstruct with `cat BlazeDroid-16.0.0-x86_64-PREVIEW.iso.part* > BlazeDroid-16.0.0-x86_64-PREVIEW.iso`. Verify the ISO's full SHA-256 before making a bootable USB.

## OWNER-TEST PREVIEW: safety and limitations

**This is untested software. Never perform your first test on a disk containing irreplaceable data or a Windows installation you must preserve.**

- First try live USB on a spare computer, using a disposable or backed-up disk if installing.
- Windows dual boot, BitLocker, UEFI ESP preservation, recovery, bootloader behavior, BIOS support, Rufus/YUMI, and safe installation are all **unverified**.
- Taskbar, resizable windows, graphics, network, audio, RAM requirements and application compatibility are unverified.
- The actual Android 16 version still must be checked on a booted image; source version and `build.prop` alone are not runtime evidence.
- Google Play/GApps are **not included** and no Play certification is claimed. Google proprietary components cannot be redistributed without proper authorization.
- File test evidence or bugs at [BlazeDroid acceptance issue #125](https://github.com/BlazingSystems/BlazingSystems-Experiments/issues/125).

Virtual testing is deferred, **not falsely reported as passed**. Production status requires separately verified installation and compatibility.

## Attribution and legal

Android Open Source Project, LineageOS, Android-Generic, Bliss-Bass Āropa, Calamares, Linux and their contributors retain their upstream copyrights and licenses. Inspect the resolved source manifest and third-party license obligations before publishing an ISO. No proprietary Google packages are automatically downloaded or bundled by BlazeDroid.
