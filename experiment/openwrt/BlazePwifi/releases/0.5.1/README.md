# BlazePwifi v0.5.1 — Safe Updates & Recovery

BlazePwifi v0.5.1 is a maintenance/reliability release focused on upgrading the running system without reflashing for ordinary feature revisions and on providing a safe rollback path for both BlazePwifi and BlazeRental.

## Highlights

- Transactional BlazePwifi overlay updates.
- No full firmware reflash for normal BlazePwifi feature/revision updates.
- Exact SHA-256 validation before activation.
- Configurable HTTPS update source.
- Last-known-good file snapshot before changes.
- Immediate rollback when apply or health checks fail.
- Boot health guard with automatic rollback after repeated failed health checks.
- Configurable stability grace before a candidate becomes the new stable version.
- Configurable bounded rollback-history retention.
- Manual rollback from **Management Console → Updates & Recovery**.
- One-time no-reflash bootstrap for existing v0.5.0 installations.
- BlazeRental v0.5.1 managed APK updater.
- BlazeRental verifies exact SHA-256, package identity and signing certificate before install.
- Android PackageInstaller provides atomic APK replacement.
- BlazeRental stores previous APK/version metadata and promotes a new build only after a launcher health window.
- Optional rollback-rescue APK uses known-good v0.5.0 application code with a recovery-only higher version code so Android accepts it without allowing arbitrary downgrade.
- Repeated failed boots while a Rental update is pending can trigger rescue installation when a valid rescue package is published.
- Native BlazeRental Admin provides **Check update**, **Install available update**, and **Roll back to last stable rescue**.
- BlazePwifi Rental Devices console includes a central Rental Update Manager.

## Upgrade BlazePwifi v0.5.0 without reflashing

Download these two release assets:

- `BlazePwifi-v0.5.1-update.tar.gz`
- `BlazePwifi-v0.5.1-update-bootstrap.sh`

Also copy the exact SHA-256 shown by the release for the update bundle.

On the BlazePwifi device:

```sh
sh BlazePwifi-v0.5.1-update-bootstrap.sh \
  BlazePwifi-v0.5.1-update.tar.gz \
  <EXACT_UPDATE_BUNDLE_SHA256>
```

The bootstrap verifies the bundle before installing the transactional updater. The currently running files are snapshotted first and retained as the rollback target.

After v0.5.1 is installed, future compatible feature updates can be installed from **Management Console → Updates & Recovery** by supplying the configured HTTPS bundle URL and exact SHA-256.

## Rollback behavior

A newly installed BlazePwifi update begins as **pending**, not stable.

The previous stable files remain preserved while the new version proves healthy. Failed immediate health checks restore the previous version. The boot guard can also restore the previous snapshot after repeated failed boot health checks.

Manual rollback is available in **Updates & Recovery** while a rollback snapshot exists.

Configuration/state files such as customer sessions, vouchers, credentials and operator UCI settings are not blindly replaced by feature-update bundles. New configuration defaults are migrated idempotently.

## When a full firmware flash is still appropriate

The updater intentionally does not pretend every OpenWrt change can be safely delivered as an overlay. A full firmware/sysupgrade may still be required for changes involving:

- kernel or kernel modules;
- bootloader;
- partition layout;
- base OpenWrt ABI;
- filesystem format;
- incompatible platform/target migration.

The console should distinguish these base-system upgrades from ordinary BlazePwifi feature revisions.

## BlazeRental update / recovery

Normal v0.5.1 update build:

- version code `50100`

Rollback rescue:

- known-good v0.5.0 application code;
- recovery version code `50101`;
- version label `0.5.0-rescue-for-0.5.1`.

The rescue version code is intentionally higher than 50100 so Android treats recovery as an upgrade rather than a prohibited downgrade. Future normal BlazeRental versions must use a higher family code, e.g. v0.5.2 should use 50200 or later.

The administrator publishes the normal APK and rescue APK metadata centrally in **Rental Devices → BlazeRental Update Manager**.

A phone will reject an APK when:

- SHA-256 does not match;
- package ID differs from `com.blazesystems.blazerental`;
- signing certificate differs from the installed BlazeRental;
- published version code does not match the APK.

For Device Owner deployments, app data and policy state are preserved across same-package updates.

## Android signing

Production BlazeRental updates and their rollback-rescue APK must be signed using the exact existing locked BlazeRental production identity. The release workflow refuses silent certificate rotation.

When that signer is unavailable, TEST and unsigned APK artifacts may be published for validation, but they are not substitutes for the production `BlazeRental.apk`.

## Security

Update actions remain Management Console admin operations protected by existing authentication, role checks and CSRF validation. The update URL must use HTTPS and match the configured update source. Update size is bounded, archive paths are validated, payload files are allowlisted, and each payload file has a manifest SHA-256.

The public Wi-Fi portal has no update or terminal access.
