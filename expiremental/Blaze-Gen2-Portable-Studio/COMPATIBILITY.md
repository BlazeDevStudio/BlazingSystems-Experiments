# Compatibility and limitations

The static assessment has five classification values. **FullyPortableCandidate** means only that current static heuristics found no blocking evidence; it is NOT a guarantee. **PartiallyPortable** signals limited evidence. **RequiresExternalDependencies** signals unresolved PE imports or runtime support. **HighRiskManualConfiguration** flags suspicious driver/anti-cheat indicators and blocks the automated GUI builder. **Unsupported** is reserved for explicit unsupported conditions and can be extended with profiles.

## v1.1 network-session advisory

On diskless clients, this development branch copies executable files into a per-station local cache and redirects child-process APPDATA / LOCALAPPDATA to per-station roots. Roblox is allowed through the builder, with automatic isolation and a warning. This is experimental source behavior; the published v1.1.0 binaries still block Roblox, and synthetic fixtures do not establish real Roblox compatibility.

A deployment must assign each physical PC a unique Windows computer name or `BLAZE_STATION_ID`, and persist its own local Windows profile overlay across reboots. The user profile and HKCU hive must not be shared between PCs. Sign in to a different Roblox account at each station. Roblox documents [Error 264](https://en.help.roblox.com/hc/en-us/articles/36665660855700-Error-Code-264-Same-account-launched-experience-from-different-devices) when the same account joins the same game from multiple devices.

These launcher settings only provide environment-variable redirection and a private client copy. They do not virtualize the Windows registry, intercept every Known Folder API, or guarantee account isolation if the diskless system shares profile state.

## In scope (experimental)
Files copied from one selected application subtree; directly imported DLL names where PE import directory is parseable; opt-in environment variables; relative launch paths; per-user writable data paths; version-directory selection by parseable numeric version folders and presence of executable.

## Out of scope
Services, driver installation, DRM, anti-cheat, machine-bound licenses, hardcoded paths, UWP/MSIX, dynamic runtime dependency discovery, capture/restore of registry changes, AppData Known Folder interception, real filesystem overlay, shared-configuration conflict locks, automatic app-specific update integration, symbolic-link redirection, injection, and executable patching.

Apps using registry, fixed paths, GPU middleware, redistributables, installers or activation may not work.

## Diskless modes

| Mode | Application path | Writable app data | Survives reboot? |
|---|---|---|---|
| PerClientWritable | Package can live on shared read-only drive | Client's LOCALAPPDATA | Only if client's local storage is persistent |
| FullyLocal | Package on local writable storage | Package/Data | Only if package storage persists |
| TemporarySession | Package can be shared | Unique system temporary directory | No; best-effort deletion when target exits |

A server share cannot guarantee read-only enforcement; configure file/share permissions externally. Child processes may outlive the tracked main process. There is no global session exclusion lock in 1.0.0. Changing APPDATA or LOCALAPPDATA is an optional per-child environment operation and does not intercept Known Folder APIs.

Roblox is a **future testing target only**, not an officially supported profile or a proven portable game.

