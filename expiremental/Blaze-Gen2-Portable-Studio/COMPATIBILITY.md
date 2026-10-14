# Compatibility and limitations

The static assessment has five classification values. **FullyPortableCandidate** means only that current static heuristics found no blocking evidence; it is NOT a guarantee. **PartiallyPortable** signals limited evidence. **RequiresExternalDependencies** signals unresolved PE imports or runtime support. **HighRiskManualConfiguration** flags suspicious driver/anti-cheat indicators. **Unsupported** records an identified limitation. These labels and warnings do not block the builder; users decide whether to continue, and packaging never bypasses OS or vendor policies.

## Roblox and diskless sessions (experimental)

Roblox packages automatically select client-local executable copies, per-client writable state, and APPDATA / LOCALAPPDATA overrides. Data paths include `BLAZE_STATION_ID`; set this to a stable unique value for every diskless seat, or the computer name is used. The launcher has no package-wide lock held while the app is running, so multiple launchers may remain open concurrently.

This is best-effort filesystem and environment separation. It does **not** isolate Windows user registry hives, APIs that resolve Known Folders through Windows, browser profiles, machine services, or Roblox's server-side account sessions. Use a distinct persistent Windows profile and a different Roblox account for each station. Roblox [documents Error 264](https://en.help.roblox.com/hc/en-us/articles/36665660855700-Error-Code-264-Same-account-launched-experience-from-different-devices) when the same account joins an experience from multiple devices. Blaze does not disable or bypass that rule. Two real Roblox clients on separate diskless PCs have not been tested.

## In scope (experimental)
Files copied from one selected application subtree; directly imported DLL names where PE import directory is parseable; opt-in environment variables; relative launch paths; per-user writable data paths; version-directory selection by parseable numeric version folders and presence of executable.

## Out of scope
Services, driver installation, DRM, anti-cheat, machine-bound licenses, hardcoded paths, UWP/MSIX, dynamic runtime dependency discovery, capture/restore of registry changes, Windows Known Folder interception, real filesystem overlay, automatic app-specific update integration, symbolic-link redirection, injection, and executable patching.

Apps using registry, fixed paths, GPU middleware, redistributables, installers or activation may not work.

## Diskless modes

| Mode | Application path | Writable app data | Survives reboot? |
|---|---|---|---|
| PerClientWritable | Package can live on shared read-only drive | Client's LOCALAPPDATA | Only if client's local storage is persistent |
| FullyLocal | Package on local writable storage | Package/Data | Only if package storage persists |
| TemporarySession | Package can be shared | Unique system temporary directory | No; best-effort deletion when target exits |

A server share cannot guarantee read-only enforcement; configure file/share permissions externally. Child processes may outlive the tracked main process. The launcher does not prevent concurrent instances. APPDATA / LOCALAPPDATA overrides are inherited environment values and do not intercept Windows Known Folder APIs.

