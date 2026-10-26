# EasyMode 10.2.0 for the R281

This independently authored EasyMode application revision is for the verified Notion R281 on OpenWrt 24.10.8. It keeps the existing SMS, modem, Wi-Fi, repeater, port, access, site-control, client-session and Traffic Intelligence controls.

## Changes

- The watchdog checks two internet targets and HTTPS, then tries a data reconnect, radio re-registration, and a last-resort device reboot. It rechecks before each stage, respects a working backup uplink, requires a valid clock and ten minutes of uptime, and permits at most two reboots in 24 hours with at least 90 minutes between them. The reboot control is visible under Network watchdog.
- Connection quality records two-target loss, average RTT and HTTPS reachability every two minutes. Network events and signal samples are bounded to roughly 24 hours in RAM. Signal history uses the existing modem cache, so it does not add serial-port traffic.
- Small screens show five main destinations directly, with a native section picker and an Other tools menu. Main sections remember their last visited sub-section. Traffic Intelligence 7.0.2 has a mobile view picker and clearer website/app coverage.
- The installer verifies hashes and syntax, pauses the watchdog during installation, marks an update as pending, makes a rollback archive, checks copied files, then restarts services without a network reload or reboot.

## Installation and reset persistence

The application archive is an overlay update. On the verified R281, extract it into a private temporary directory and run `./install.sh --check`, then `./install.sh --apply`. It accepts the 4.2.6, 10.0.0, 10.1.0 and 10.2.0 baselines on the exact board and release. It does not make EasyMode survive a factory reset.

A separate private R281 sysupgrade image has been built with EasyMode and current router defaults inside SquashFS. Its root filesystem was read back file by file and its image passed `sysupgrade -T` on this R281. It has **not been flashed**. It contains private settings and keys, so keep it off public repositories. This router has one root filesystem and no verified automatic rollback; flashing remotely could leave a roof-mounted device unreachable. See [HANDOFF.md](HANDOFF.md).

The credential-free [public R281 candidate](openwrt/R281-EasyMode-v10.2.0-public-tested.bin) is a separate image built from the pinned clean community OpenWrt baseline. SHA-256: `9f346961ebb4d984a480f44fa1bd8af56653a6c34b706c2eb2a7e5df8532fdba`. Its 2,248 filesystem entries passed readback checks and the exact image passed `sysupgrade -T` on the R281. It has **not been boot-tested or flashed**. The clean baseline has no device identities or Wi-Fi setup and has OpenWrt's blank default root password, so it is a candidate for controlled installation, not an unattended roof-mounted-device update. The base provenance and reproducibility limit are documented in [firmware/r281/README.md](../../firmware/r281/README.md).

A separate [LuCI restore archive builder](../../tools/build-r281-luci-restore.py) packages the overlay application without credentials. Restoring the archive requires a reachable router and a reboot; it cannot survive a later factory reset by itself. The owner also has a device-specific full backup in the approved private-file folder.

The six Generic, AP, Router, Cellular, Switch and PC offline bundles are editions of the separate Traffic Intelligence package, not full EasyMode firmware images. They share the mobile navigation, clearer attribution views and checksum-verified installer. Only Cellular was installed and checked on this R281; other hardware remains unverified.

QManager was used as a public feature reference at commit `7bad6f8f48b02241e1767b3a208c2290d7a1dbc9`. Its Commons Clause restricts commercial use of derived software. No QManager source, artwork or styles were copied. [FEATURE-GAP.md](FEATURE-GAP.md) states what is present and what still needs work.
