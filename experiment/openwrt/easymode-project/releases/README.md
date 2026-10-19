# EasyMode Releases

Versioned release snapshots.

Published version directories are treated as immutable records: new work should create a new version rather than silently replacing an older release. Each release should carry manifests, checksums, release notes, test status and known limitations.

[← EasyMode](../README.md)

- [4.2.1 R281 experiment](v4.2.1-r281-experiment/): tested source snapshot for the existing R281 installation; not a flashable image.

- [4.2.2 installed R281 experiment](v4.2.2-r281-experiment/): current deployed source, independent repeater AP settings and tested shared-login captive compatibility. Firmware/reset validation remains separate.

- [4.2.3 installed R281 experiment](v4.2.3-r281-experiment/): current deployed source, tested signal LED controls, independent repeater AP settings and shared-login captive compatibility. Private firmware candidate passed structural checks; flash/reset validation and USSD remain unfinished.

- [4.2.3 R281 encrypted installer](v4.2.3-r281-installer-encrypted/): complete owner-specific kit protected with AES-256-GCM; recovery key retained offline. Firmware remains unflashed and not reset-tested.

- [10.0.0 R281 application profile](v10.0.0-r281/): copy of the running R281 EasyMode, deployed and checked on Notion R281 / OpenWrt 24.10.8. This is an application archive, not a firmware image; other board profiles and hard-reset persistence are not verified.
